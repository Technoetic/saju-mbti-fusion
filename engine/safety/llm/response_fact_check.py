"""응답 사실 검증 — 운영표준 §5.2.8 본문화.

LLM이 입력 메트릭·보조정보(나이·성별·face_count 등)와 모순되는 응답을 내는
경우를 결정론 후처리로 감지. 모순 시 폴백 트리거.

§5.2.8 검증 차원:
  · age_mismatch       — "고희를 넘기신" 같은 노년 언급인데 입력 나이가 청년
  · gender_mismatch    — 입력 성별과 명백히 다른 성별 언급
  · face_count_mismatch — face_count=1인데 "두 사람의 상" 언급
  · region_mismatch    — region=KR인데 "유럽인의" 언급
  · gaze_mismatch      — gaze_locked=False인데 "맑게 정면을 보시는"
  · palace_score_mismatch — LLM 단정 어휘("재물복 풍성")가 결정론 점수와 충돌
                            (ADR-010 사실성 분리 — Phase 3 본문화)

본 모듈은 응답을 수정하지 않는다 — 검증만. 호출자는 위반 시 llm_fallback_router
폴백 트리거(persona_failed)로 매핑.

§5.2.8 보수적 접근:
  · 매칭이 모호하면 위반으로 표시 안 함 (false positive 최소화)
  · 부정문맥("~이 아니다") 안에 있으면 위반 아님
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# §5.2.8 위반 코드
FACT_AGE = "age_mismatch"
FACT_GENDER = "gender_mismatch"
FACT_FACE_COUNT = "face_count_mismatch"
FACT_REGION = "region_mismatch"
FACT_GAZE = "gaze_mismatch"
FACT_PALACE_SCORE = "palace_score_mismatch"  # ADR-004 Phase 3 — 결정론 점수 vs LLM 단정


# ─────────────────────────── 어휘 사전 ───────────────────────────

# 연령대 키워드 — 응답 본문에 등장 시 입력 나이와 비교
_AGE_BUCKETS = {
    "elderly": ("고희", "팔순", "구순", "백수(白壽)", "노년", "노인",
                "어르신", "이순", "환갑을 넘기"),
    "middle": ("중년", "사십대", "오십대", "마흔", "쉰"),
    "young": ("청년", "이십대", "삼십대", "스물", "서른"),
}

# 성별 키워드 — 응답에 등장 시 입력 gender와 비교
_GENDER_TERMS = {
    "male": ("아드님", "사내아이", "남편 되시는", "총각", "사내의 상이로"),
    "female": ("따님", "여식", "처녀의 상이로", "아내 되시는", "처자"),
}

# face_count 모순
_MULTI_FACE_PATTERNS = (
    r"두\s*분의\s*상", r"여러\s*분의\s*상", r"세\s*분의\s*상",
    r"두\s*사람", r"세\s*사람",
)

# 인종/지역 키워드 — region과 비교
_REGION_TERMS = {
    "kr": ("한국인의 상", "조선 사람의 상", "동방의 사람"),
    "eu": ("유럽인의 상", "서양인의 상", "백인의 상"),
    "jp": ("일본인의 상", "왜인의 상"),
    "cn": ("중국인의 상", "한족의 상"),
}

# 부정 컨텍스트 — 위반 키워드 주변에 이 표현이 있으면 무시
_NEGATION_MARKERS = (
    "아니라", "아니로", "아닌", "않으",
    "처럼 보이지", "같지 않",
)


# ───── ADR-004 Phase 3 — 12궁 단정 어휘 ↔ palace_score 매핑 ─────
#
# 각 궁(palace key)별로, LLM이 사용했을 때 "그 궁이 강함을 단정"하는
# 단정형 어휘 묶음. 결정론 점수가 약함(< _PALACE_STRONG_THRESHOLD)인데
# 단정 어휘가 등장하면 사실성 분리(ADR-010) 위반 → 폴백.
#
# 부정 어휘(약함 단정)도 마찬가지 — 점수가 강한데 "재물이 빈약" 같이 적으면 위반.
#
# 어휘는 본 시스템 시스템 프롬프트 통설 어휘 + knowledge.py 학파 출처와 정합.
# "운명·길흉" 매핑이 아니라 "결정론 점수 ↔ LLM 어휘" 정합 검증임.

_PALACE_STRONG_THRESHOLD = 0.30  # 이 미만이면 "약/옅"
_PALACE_WEAK_THRESHOLD = 0.75    # 이 초과면 "강/환"

_PALACE_STRONG_ASSERTIONS: dict[str, tuple[str, ...]] = {
    "jaebaek": ("재물복이 풍성", "재물복이 두텁", "재백궁이 환하",
                "재물이 넉넉", "재백궁이 두드러", "재백궁이 빛나"),
    "gwanrok": ("관록궁이 환하", "관운이 두텁", "벼슬길이 트이",
                "관록궁이 빛나", "벼슬이 높"),
    "myeong": ("명궁이 환하", "명궁이 빛나", "명궁이 두드러"),
    "cheocheop": ("처첩궁이 환하", "처첩궁이 두텁", "혼인 자리가 두텁"),
    "janyeo": ("자녀궁이 환하", "자손이 넉넉", "자녀 자리가 두드러"),
    "jilek": ("질액궁이 환하", "건강이 두텁", "산근이 빛나"),
    "hyeongje": ("형제궁이 환하", "형제 자리가 두텁"),
    "jeontaek": ("전택궁이 환하", "전택 자리가 두텁"),
    "nobok": ("노복궁이 환하", "노복 자리가 두텁"),
    "cheoni": ("천이궁이 환하", "이동 자리가 두텁"),
    "bokdeok": ("복덕궁이 환하", "복덕 자리가 두텁"),
    "bumo": ("부모궁이 환하", "부모 자리가 두텁"),
}

_PALACE_WEAK_ASSERTIONS: dict[str, tuple[str, ...]] = {
    "jaebaek": ("재물이 빈약", "재백궁이 흐리", "재물복이 옅",
                "재백궁이 약하"),
    "gwanrok": ("관록궁이 흐리", "관운이 약하", "벼슬이 트이지 않"),
    "myeong": ("명궁이 흐리", "명궁이 옅"),
    "cheocheop": ("처첩궁이 흐리", "혼인 자리가 옅"),
    "janyeo": ("자녀궁이 흐리", "자녀 자리가 옅"),
    "jilek": ("질액궁이 흐리", "산근이 흐리"),
    "hyeongje": ("형제궁이 흐리",),
    "jeontaek": ("전택궁이 흐리",),
    "nobok": ("노복궁이 흐리",),
    "cheoni": ("천이궁이 흐리",),
    "bokdeok": ("복덕궁이 흐리",),
    "bumo": ("부모궁이 흐리",),
}


@dataclass(frozen=True)
class FactCheckResult:
    violations: list[str] = field(default_factory=list)
    matched_terms: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.violations


# ─────────────────────────── 헬퍼 ───────────────────────────

_SENTENCE_BOUNDARIES = (".", "!", "?", "\n", "。", "!", "?")


def _is_negated(text: str, term: str) -> bool:
    """ADR-187 — 문장 경계 기반 부정 컨텍스트 검출 (이전 ±25자 → 문장 단위)."""
    idx = text.find(term)
    if idx < 0:
        return False
    # 좌측 — 직전 문장 종결 부호까지 (최대 60자 폴백)
    start = idx
    while start > 0 and text[start - 1] not in _SENTENCE_BOUNDARIES:
        start -= 1
        if idx - start > 60:
            break
    # 우측 — 다음 문장 종결 부호까지
    end = idx + len(term)
    while end < len(text) and text[end] not in _SENTENCE_BOUNDARIES:
        end += 1
        if end - (idx + len(term)) > 60:
            break
    window = text[start:end]
    return any(neg in window for neg in _NEGATION_MARKERS)


def _age_bucket(age: int | None) -> str:
    """입력 나이 → bucket 식별. age 모르면 'unknown'."""
    if age is None or not isinstance(age, int) or age < 0:
        return "unknown"
    if age >= 60:
        return "elderly"
    if age >= 40:
        return "middle"
    return "young"


# ─────────────────────────── 검증 함수 ───────────────────────────

def check_age_consistency(text: str, age: int | None) -> tuple[bool, list[str]]:
    """입력 나이와 응답 어휘가 호환되는지. 반환: (ok, matched_terms)."""
    if age is None or not text:
        return True, []
    bucket = _age_bucket(age)
    if bucket == "unknown":
        return True, []
    # 다른 bucket의 어휘가 등장하면 위반
    other_buckets = {k: v for k, v in _AGE_BUCKETS.items() if k != bucket}
    matched: list[str] = []
    for _other, terms in other_buckets.items():
        for t in terms:
            if t in text and not _is_negated(text, t):
                matched.append(t)
    return (not matched), matched


def check_gender_consistency(text: str, gender: str | None) -> tuple[bool, list[str]]:
    """입력 성별과 응답 어휘 비교."""
    if not gender or not text:
        return True, []
    g = gender.lower().strip()
    if g not in ("male", "female", "m", "f", "남", "여"):
        return True, []
    # 정규화
    if g in ("m", "남"):
        g = "male"
    elif g in ("f", "여"):
        g = "female"
    # 반대 성별 어휘 검색
    opposite = "female" if g == "male" else "male"
    opposite_terms = _GENDER_TERMS.get(opposite, ())
    matched = [t for t in opposite_terms if t in text and not _is_negated(text, t)]
    return (not matched), matched


def check_face_count(text: str, face_count: int | None) -> tuple[bool, list[str]]:
    """face_count=1이면 다중 얼굴 언급 금지."""
    if not text or face_count is None or face_count != 1:
        return True, []
    matched: list[str] = []
    for pattern in _MULTI_FACE_PATTERNS:
        m = re.search(pattern, text)
        if m and not _is_negated(text, m.group(0)):
            matched.append(m.group(0))
    return (not matched), matched


def check_region_consistency(text: str, region: str | None) -> tuple[bool, list[str]]:
    """region과 무관한 인종/지역 언급 검출."""
    if not region or not text:
        return True, []
    region_key = (region or "").upper()
    # KR 정규화
    if region_key == "KR":
        rk = "kr"
    elif region_key in ("EU", "DE", "FR", "UK", "GB"):
        rk = "eu"
    elif region_key == "JP":
        rk = "jp"
    elif region_key == "CN":
        rk = "cn"
    else:
        return True, []
    others = {k: v for k, v in _REGION_TERMS.items() if k != rk}
    matched: list[str] = []
    for _k, terms in others.items():
        for t in terms:
            if t in text and not _is_negated(text, t):
                matched.append(t)
    return (not matched), matched


def check_gaze_consistency(text: str, gaze_locked: bool | None) -> tuple[bool, list[str]]:
    """gaze_locked=False인데 '맑게 정면을' 같은 응시 강한 표현이 있으면 위반."""
    if gaze_locked is None or gaze_locked is True or not text:
        return True, []
    gaze_terms = ("맑게 정면을 보시", "또렷이 응시", "흔들림 없이 마주")
    matched = [t for t in gaze_terms if t in text and not _is_negated(text, t)]
    return (not matched), matched


def check_palace_score_consistency(
    text: str,
    palace_scores: dict[str, float] | None,
) -> tuple[bool, list[str]]:
    """ADR-004 Phase 3 — LLM 단정 어휘 vs 결정론 점수 정합.

    palace_scores 예: {"jaebaek": 0.18, "gwanrok": 0.82, ...}
      → "재백궁이 환하" 어휘가 본문에 있는데 점수 0.18이면 위반 (단정 환각)
      → "재물이 빈약" 어휘가 본문에 있는데 점수 0.82이면 위반 (단정 환각)

    palace_scores가 None이면 검증 면제(역호환). 부정 컨텍스트("재백궁이
    환한 것은 아니로")는 위반 아님.

    Args:
        text: LLM 응답 본문.
        palace_scores: scoring.PalaceScore.score 모음 — {궁key: float}.

    Returns:
        (ok, matched_terms) — ok=False면 단정 환각 검출.
    """
    if not text or not palace_scores:
        return True, []
    matched: list[str] = []
    for palace_key, score in palace_scores.items():
        if not isinstance(score, (int, float)):
            continue
        # 약한 점수 + 강한 단정 어휘 → 위반
        if score < _PALACE_STRONG_THRESHOLD:
            for term in _PALACE_STRONG_ASSERTIONS.get(palace_key, ()):
                if term in text and not _is_negated(text, term):
                    matched.append(f"{palace_key}:strong:{term}")
        # 강한 점수 + 약한 단정 어휘 → 위반
        elif score > _PALACE_WEAK_THRESHOLD:
            for term in _PALACE_WEAK_ASSERTIONS.get(palace_key, ()):
                if term in text and not _is_negated(text, term):
                    matched.append(f"{palace_key}:weak:{term}")
    return (not matched), matched


# ─────────────────────────── 통합 진입점 ───────────────────────────

def check_response(
    text: str | None,
    *,
    age: int | None = None,
    gender: str | None = None,
    metrics: dict[str, Any] | None = None,
    region: str | None = None,
    palace_scores: dict[str, float] | None = None,
) -> FactCheckResult:
    """모든 차원 일괄 검증.

    Args:
        text: LLM 응답 본문 (legal footer 등 첨부 전이면 더 정확).
        age/gender/region: 입력 보조정보.
        metrics: face_count, gaze_locked 등.
        palace_scores: ADR-004 Phase 3 — 결정론 12궁 점수 dict.
            전달되면 LLM 단정 어휘가 점수와 충돌하는지 검증.
            None이면 검증 면제(역호환).
    """
    if not text:
        return FactCheckResult()
    metrics = metrics or {}

    all_violations: list[str] = []
    all_matched: list[str] = []

    ok, matched = check_age_consistency(text, age)
    if not ok:
        all_violations.append(FACT_AGE)
        all_matched.extend(matched)

    ok, matched = check_gender_consistency(text, gender)
    if not ok:
        all_violations.append(FACT_GENDER)
        all_matched.extend(matched)

    ok, matched = check_face_count(text, metrics.get("face_count"))
    if not ok:
        all_violations.append(FACT_FACE_COUNT)
        all_matched.extend(matched)

    ok, matched = check_region_consistency(text, region)
    if not ok:
        all_violations.append(FACT_REGION)
        all_matched.extend(matched)

    ok, matched = check_gaze_consistency(text, metrics.get("gaze_locked"))
    if not ok:
        all_violations.append(FACT_GAZE)
        all_matched.extend(matched)

    ok, matched = check_palace_score_consistency(text, palace_scores)
    if not ok:
        all_violations.append(FACT_PALACE_SCORE)
        all_matched.extend(matched)

    return FactCheckResult(
        violations=all_violations,
        matched_terms=all_matched,
    )


def to_fallback_trigger(result: FactCheckResult) -> str:
    """llm_fallback_router 호환 — 위반 1건이라도 있으면 persona_failed."""
    return "persona_failed" if result.violations else ""
