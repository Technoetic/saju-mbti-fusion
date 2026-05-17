"""한국어 작명 어감·선호도 점수 — ADR-016 부분 채택.

본 모듈은 추천 작명 후보 정렬용 **가점**만 산출. 길흉 예언 X.

데이터 출처:
  - data/name_aesthetic_syllable_freq.json
  - 보고서 §2.1·§2.2 (전자가족관계등록시스템 기반 2015-2024 인기 이름 70건)

⚠️ 사용 정책 (ADR-016):
  · "어감이 좋다/나쁘다" 단정 금지 — 추천 정렬 가점만
  · 인과적 길흉 예언 금지 (ADR-006·010)
  · 사용자 출력 시 면책 의무
  · 본 데이터는 **추세**일 뿐 절대 기준 아님

본 모듈은 ADR-010 사실성 분리 부분 적용:
  - 검증된 데이터 (전자가족관계 통계) 채택
  - 학술 인용 (보고서 §4의 김진욱·정희원) 검증 실패라 미채택
  - 음운 결합 규칙 (보고서 §1) JSON 표는 미완이나 본문 명시 4개 규칙은 채택
    (국립국어원 표준발음법 — 한국어 음운론 표준 사실)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal


# 데이터 파일 경로
_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "name_aesthetic_syllable_freq.json"


# 성별 라벨
GENDER_MALE = "male"
GENDER_FEMALE = "female"
GENDER_NEUTRAL = "neutral"


@dataclass(frozen=True)
class AestheticResult:
    """어감 점수 결과.

    Attributes:
        name: 입력 이름 (한글).
        score: 0.0~1.0 정규화된 점수.
        gender: "male" / "female" / "neutral".
        syllable_scores: 각 음절의 원시 빈도값.
        max_freq: 데이터셋의 최고 빈도 (정규화 기준).
        rationale: 사용자 노출용 한국어 사유 (면책 포함).
    """
    name: str
    score: float
    gender: str
    syllable_scores: dict[str, int]
    max_freq: int
    rationale: str


@lru_cache(maxsize=1)
def _load_freq_data() -> dict:
    return json.loads(_DATA_PATH.read_text(encoding="utf-8"))


def _get_freq_dict(gender: str) -> dict[str, int]:
    """성별별 음절 빈도 dict 반환."""
    data = _load_freq_data()
    if gender == GENDER_MALE:
        return data.get("male_syllable_freq", {})
    if gender == GENDER_FEMALE:
        return data.get("female_syllable_freq", {})
    return data.get("neutral_syllable_freq", {})


DISCLAIMER_KO = (
    "본 점수는 최근 10년 인기 이름 통계(전자가족관계등록시스템 기반) 기반 "
    "추천 정렬 가점이며, 이름의 길흉이나 어감 절대 기준이 아닙니다."
)


def aesthetic_score(
    name_korean: str,
    gender: Literal["male", "female", "neutral"] = "neutral",
) -> AestheticResult:
    """이름의 음절 인기도 기반 어감 가점 산출.

    Args:
        name_korean: 한글 이름 (성씨 제외, 이름만). 예: "준서".
        gender: "male" / "female" / "neutral".

    Returns:
        AestheticResult — score 0.0~1.0 (정규화), 각 음절 원시 빈도 포함.

    면책 (ADR-016):
        본 점수는 추천 정렬 가점일 뿐. "어감이 좋다" 단정 금지.
        반환된 rationale에 면책 자동 포함.
    """
    freq = _get_freq_dict(gender)
    max_freq = max(freq.values()) if freq else 1

    syllable_scores: dict[str, int] = {}
    total = 0
    for ch in name_korean:
        if "가" <= ch <= "힣":
            score = freq.get(ch, 0)
            syllable_scores[ch] = score
            total += score

    syllable_count = len([c for c in name_korean if "가" <= c <= "힣"])
    if syllable_count == 0 or max_freq == 0:
        normalized = 0.0
    else:
        # 정규화: 평균 음절 빈도 / 최대 빈도
        normalized = (total / syllable_count) / max_freq
        normalized = max(0.0, min(1.0, normalized))

    rationale = _build_rationale(name_korean, gender, normalized, syllable_scores)

    return AestheticResult(
        name=name_korean,
        score=normalized,
        gender=gender,
        syllable_scores=syllable_scores,
        max_freq=max_freq,
        rationale=rationale,
    )


def _build_rationale(
    name: str,
    gender: str,
    score: float,
    syllable_scores: dict[str, int],
) -> str:
    """사용자 노출 사유 — 면책 자동 포함."""
    if not syllable_scores or all(v == 0 for v in syllable_scores.values()):
        return (
            f"'{name}'의 음절은 최근 10년 인기 이름 통계에서 흔하지 않은 음절입니다. "
            f"※ {DISCLAIMER_KO}"
        )

    top_syl = max(syllable_scores.items(), key=lambda kv: kv[1])
    intensity = (
        "매우 자주" if score >= 0.5
        else "자주" if score >= 0.25
        else "다소"
    )
    return (
        f"'{name}'은(는) 최근 10년 인기 이름에서 {intensity} 쓰이는 음절을 포함합니다 "
        f"(특히 '{top_syl[0]}' 음절 빈도 {top_syl[1]}). "
        f"※ {DISCLAIMER_KO}"
    )


def total_syllables(gender: str = GENDER_NEUTRAL) -> int:
    """라이브 점검용 — 데이터셋 음절 수."""
    return len(_get_freq_dict(gender))


def get_top_syllables(gender: str = GENDER_NEUTRAL, n: int = 10) -> list[tuple[str, int]]:
    """상위 N개 인기 음절 (디버깅·관리용)."""
    freq = _get_freq_dict(gender)
    return sorted(freq.items(), key=lambda kv: -kv[1])[:n]


# ─────────────────────────── 음운 결합 자연스러움 (보고서 §1) ───────────────────────────
# 국립국어원 표준발음법 기반 — 한국어 음운론 표준 사실.
# 보고서 §1 JSON 표는 빈 약속이나, 본문에 명시된 4개 규칙은 채택.


# 표준 종성 7자음 (표준발음법 제8항)
_VALID_CODA = frozenset("ㄱㄴㄷㄹㅁㅂㅇ")

# 자음군 회피 — 받침 + 다음 초성 어색 조합 (보고서 §1 명시)
# 격음(ㅋㅌㅍㅊ) + 평음 종성, 또는 발음 충돌 조합
_AWKWARD_BATCHIM_INITIAL = frozenset([
    ("ㄱ", "ㅍ"),  # 보고서 명시 예시
    ("ㄱ", "ㅌ"),
    ("ㄱ", "ㅋ"),
    ("ㅂ", "ㅍ"),
    ("ㅂ", "ㅋ"),
    ("ㅂ", "ㅌ"),
    ("ㄷ", "ㅌ"),
    ("ㄷ", "ㅍ"),
])

# 자연 결합 — 받침 + 다음 초성 부드러운 조합 (보고서 §1 명시)
# ㄴ 받침 + ㅇ/ㅎ (연음 + 약화), 모음 시작 (연음)
_SMOOTH_BATCHIM_INITIAL = frozenset([
    ("ㄴ", "ㅇ"),  # 보고서 명시 예시
    ("ㄴ", "ㅎ"),
    ("ㄴ", "ㄴ"),  # 동일 자음 연결 자연
    ("ㄹ", "ㄹ"),  # 유음화 자연
    ("ㅇ", "ㅇ"),
    ("ㅁ", "ㅇ"),
    ("ㅁ", "ㅎ"),
])


def _decompose_jamo(syllable: str) -> tuple[str, str, str] | None:
    """한글 음절 → (초성, 중성, 종성) 분해. 종성 없으면 빈 문자열."""
    if not ("가" <= syllable <= "힣"):
        return None
    code = ord(syllable) - ord("가")
    cho_idx = code // (21 * 28)
    jung_idx = (code % (21 * 28)) // 28
    jong_idx = code % 28
    CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
    JUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
    JONG = "_ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"
    cho = CHO[cho_idx]
    jung = JUNG[jung_idx]
    jong = JONG[jong_idx] if jong_idx > 0 else ""
    return (cho, jung, jong)


def _normalize_coda(coda: str) -> str:
    """복합 종성을 표준 7자음 중 하나로 정규화 (표준발음법 제8항)."""
    if not coda:
        return ""
    # 표준 7자음 매핑 (대표 변환만 — 정확성 위해 보수적)
    mapping = {
        "ㄲ": "ㄱ", "ㅋ": "ㄱ", "ㄳ": "ㄱ", "ㄺ": "ㄱ",
        "ㄵ": "ㄴ", "ㄶ": "ㄴ",
        "ㅅ": "ㄷ", "ㅆ": "ㄷ", "ㅈ": "ㄷ", "ㅊ": "ㄷ", "ㅌ": "ㄷ", "ㅎ": "ㄷ",
        "ㄻ": "ㅁ", "ㄼ": "ㅂ", "ㄽ": "ㄹ", "ㄾ": "ㄹ", "ㄿ": "ㅂ", "ㅀ": "ㄹ",
        "ㅄ": "ㅂ", "ㅍ": "ㅂ",
    }
    return mapping.get(coda, coda if coda in _VALID_CODA else "")


def phonetic_combination_score(name_korean: str) -> dict:
    """음절 결합 자연스러움 점수 — 보고서 §1 기반.

    분석:
      - 음절 N개 사이 N-1 결합 페어 검사
      - 자연 결합 (smooth) → +1
      - 어색 결합 (awkward) → -1
      - 일반 결합 → 0

    Returns:
        {
            "score": float,  # 정규화 [-1.0, 1.0]
            "pairs": list[dict],  # 각 결합 페어 평가
            "awkward_count": int,
            "smooth_count": int,
            "rationale": str,  # 면책 포함
        }

    면책 (ADR-016):
        본 점수는 한국어 음운론 표준 기반 추세. 절대 평가 X.
    """
    syllables = [c for c in name_korean if "가" <= c <= "힣"]
    if len(syllables) < 2:
        return {
            "score": 0.0,
            "pairs": [],
            "awkward_count": 0,
            "smooth_count": 0,
            "rationale": (
                "음절 2개 이상이어야 결합 평가 가능합니다. "
                f"※ {DISCLAIMER_KO}"
            ),
        }

    pairs: list[dict] = []
    awkward_count = 0
    smooth_count = 0

    for i in range(len(syllables) - 1):
        s1 = syllables[i]
        s2 = syllables[i + 1]
        decomp1 = _decompose_jamo(s1)
        decomp2 = _decompose_jamo(s2)
        if not decomp1 or not decomp2:
            continue
        coda = _normalize_coda(decomp1[2])
        initial = decomp2[0]
        verdict = "normal"
        if (coda, initial) in _AWKWARD_BATCHIM_INITIAL:
            verdict = "awkward"
            awkward_count += 1
        elif (coda, initial) in _SMOOTH_BATCHIM_INITIAL:
            verdict = "smooth"
            smooth_count += 1
        elif not coda and initial == "ㅇ":
            # 종성 없고 다음 초성 ㅇ — 연음 자연
            verdict = "smooth"
            smooth_count += 1
        pairs.append({
            "pair": f"{s1}{s2}",
            "coda": coda or "(없음)",
            "initial": initial,
            "verdict": verdict,
        })

    n_pairs = len(pairs)
    if n_pairs == 0:
        score = 0.0
    else:
        score = (smooth_count - awkward_count) / n_pairs
        score = max(-1.0, min(1.0, score))

    rationale = _build_phonetic_rationale(name_korean, score, smooth_count, awkward_count)
    return {
        "score": score,
        "pairs": pairs,
        "awkward_count": awkward_count,
        "smooth_count": smooth_count,
        "rationale": rationale,
    }


def _build_phonetic_rationale(name: str, score: float, smooth: int, awkward: int) -> str:
    """음운 결합 사용자 출력 — 면책 자동 포함."""
    if score > 0.3:
        intensity = "자연스러운"
    elif score < -0.3:
        intensity = "다소 어색한"
    else:
        intensity = "보통의"
    return (
        f"'{name}'의 음절 결합은 {intensity} 발음 흐름을 보입니다 "
        f"(자연 결합 {smooth}건, 어색 결합 {awkward}건). "
        f"※ {DISCLAIMER_KO}"
    )
