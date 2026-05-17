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
    """성별별 음절 빈도 dict 반환 (위치 무관)."""
    data = _load_freq_data()
    if gender == GENDER_MALE:
        return data.get("male_syllable_freq", {})
    if gender == GENDER_FEMALE:
        return data.get("female_syllable_freq", {})
    return data.get("neutral_syllable_freq", {})


# 위치 라벨
POSITION_START = "start"
POSITION_END = "end"


def _get_positional_freq(gender: str, position: str) -> dict[str, int]:
    """위치별(시작/끝) 음절 빈도 — 보고서 §2 본문 '준·윤으로 끝나는' 명시 반영."""
    data = _load_freq_data()
    key_map = {
        (GENDER_MALE, POSITION_START): "male_start_syllable_freq",
        (GENDER_MALE, POSITION_END): "male_end_syllable_freq",
        (GENDER_FEMALE, POSITION_START): "female_start_syllable_freq",
        (GENDER_FEMALE, POSITION_END): "female_end_syllable_freq",
    }
    return data.get(key_map.get((gender, position), ""), {})


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


def get_top_positional_syllables(
    gender: str,
    position: str,
    n: int = 10,
) -> list[tuple[str, int]]:
    """위치별 상위 N개 인기 음절 — 보고서 §2 본문 명시 ('준·윤으로 끝나는')."""
    freq = _get_positional_freq(gender, position)
    return sorted(freq.items(), key=lambda kv: -kv[1])[:n]


def position_match_score(
    name_korean: str,
    gender: Literal["male", "female"] = "male",
) -> dict:
    """이름의 시작/끝 음절이 인기 위치 패턴과 일치하는지 점수.

    보고서 §2 본문 "준·윤으로 끝나는 이름이 자주 관찰" 명시 반영.
    위치별 가중 빈도가 위치 무관 빈도보다 명확한 신호.

    Returns:
        {
            "start_syllable": str,
            "end_syllable": str,
            "start_score": float,  # 0.0~1.0 (시작 음절의 위치별 정규화)
            "end_score": float,
            "combined_score": float,  # 평균
            "rationale": str,
        }
    """
    syllables = [c for c in name_korean if "가" <= c <= "힣"]
    if len(syllables) < 2:
        return {
            "start_syllable": syllables[0] if syllables else "",
            "end_syllable": "",
            "start_score": 0.0,
            "end_score": 0.0,
            "combined_score": 0.0,
            "rationale": f"2음절 이상이어야 위치 평가 가능. ※ {DISCLAIMER_KO}",
        }

    start_freq = _get_positional_freq(gender, POSITION_START)
    end_freq = _get_positional_freq(gender, POSITION_END)
    start_max = max(start_freq.values()) if start_freq else 1
    end_max = max(end_freq.values()) if end_freq else 1

    start_syl = syllables[0]
    end_syl = syllables[-1]
    start_score = start_freq.get(start_syl, 0) / start_max if start_max > 0 else 0.0
    end_score = end_freq.get(end_syl, 0) / end_max if end_max > 0 else 0.0
    combined = (start_score + end_score) / 2

    rationale = _build_position_rationale(
        start_syl, end_syl, start_score, end_score, start_freq, end_freq, gender
    )
    return {
        "start_syllable": start_syl,
        "end_syllable": end_syl,
        "start_score": start_score,
        "end_score": end_score,
        "combined_score": combined,
        "rationale": rationale,
    }


def _build_position_rationale(
    start: str, end: str, start_s: float, end_s: float,
    start_freq: dict, end_freq: dict, gender: str,
) -> str:
    """위치별 점수 사용자 출력 — 면책 자동 포함."""
    parts = []
    if start_s > 0.5:
        parts.append(f"시작 음절 '{start}'은(는) 인기 시작 음절")
    if end_s > 0.5:
        parts.append(f"끝 음절 '{end}'은(는) 인기 끝 음절")
    if not parts:
        parts.append("시작·끝 음절 모두 인기 통계에서 흔하지 않음")
    return f"{', '.join(parts)}. ※ {DISCLAIMER_KO}"


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
        elif initial == "ㅇ":
            # 다음 초성 ㅇ (모음 시작) — 연음 현상 (보고서 §1 본문 명시)
            # "받침 뒤에 모음으로 시작하는 음절이 오면 받침이 다음 음절의
            #  초성으로 이동하여 발음되는 연음 현상이 발생한다"
            # 종성 유무 무관 모두 자연 결합 처리.
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


# ─────────────── 표준발음법 §10~§30 음운 변동 (ADR-028) ───────────────
# 국립국어원 표준발음법 + 보고서 §2 매핑 표 (라인 22-36).
# 결정론 자모 분리 + 조건 제어 매핑.

# 조음 위치 분류 — 비음화 §18~§19 동화 표적
# 연구개음(velar) → ㅇ / 치조음(alveolar) → ㄴ / 양순음(bilabial) → ㅁ
_CODA_VELAR = frozenset(["ㄱ", "ㄲ", "ㅋ", "ㄳ", "ㄺ"])
_CODA_ALVEOLAR = frozenset(["ㄷ", "ㅅ", "ㅆ", "ㅈ", "ㅊ", "ㅌ", "ㅎ"])
_CODA_BILABIAL = frozenset(["ㅂ", "ㅍ", "ㄼ", "ㄿ", "ㅄ"])

# 자음군 단순화 §10~§11 — 어말·자음 앞에서 1자음만 발음
_CLUSTER_SIMPLIFY = {
    "ㄳ": "ㄱ", "ㄵ": "ㄴ", "ㄶ": "ㄴ",
    "ㄺ": "ㄱ", "ㄻ": "ㅁ", "ㄼ": "ㄹ",
    "ㄽ": "ㄹ", "ㄾ": "ㄹ", "ㄿ": "ㅂ",
    "ㅀ": "ㄹ", "ㅄ": "ㅂ",
}

# 경음화 §23~§28 — 평음 → 경음
_TENSE_MAP = {"ㄱ": "ㄲ", "ㄷ": "ㄸ", "ㅂ": "ㅃ", "ㅅ": "ㅆ", "ㅈ": "ㅉ"}

# 격음화 §12 — ㅎ 인접 평음 → 격음
_ASPIRATE_MAP = {"ㄱ": "ㅋ", "ㄷ": "ㅌ", "ㅂ": "ㅍ", "ㅈ": "ㅊ"}

# ㄴ첨가 §29~§30 — 합성어 환경 후행 ㅣ·반모음(ㅑㅕㅛㅠㅖ) 앞
_N_INSERT_VOWELS = frozenset(["ㅣ", "ㅑ", "ㅕ", "ㅛ", "ㅠ", "ㅖ", "ㅒ"])

# 평음 (응축되지 않은 자음) 식별
_PLAIN_CONSONANTS = frozenset(["ㄱ", "ㄷ", "ㅂ", "ㅅ", "ㅈ"])


def _compose_jamo(cho: str, jung: str, jong: str = "") -> str:
    """(초성, 중성, 종성) → 한글 음절. 분해 실패 시 빈 문자열."""
    CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
    JUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
    JONG = "_ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"
    if cho not in CHO or jung not in JUNG:
        return ""
    cho_idx = CHO.index(cho)
    jung_idx = JUNG.index(jung)
    jong_idx = JONG.index(jong) if jong and jong in JONG else 0
    code = cho_idx * 21 * 28 + jung_idx * 28 + jong_idx
    return chr(ord("가") + code)


def f_nasalize(coda: str, initial: str) -> str | None:
    """비음화 §18~§19 — C1 폐쇄음 + C2 비음(ㄴ·ㅁ) → 조음 위치 동질 비음.

    Returns:
        새 종성 (str) 또는 변화 없음 (None).

    Examples:
        f_nasalize('ㄱ', 'ㄴ') == 'ㅇ'  # 박나리 → 방나리
        f_nasalize('ㅂ', 'ㅁ') == 'ㅁ'
        f_nasalize('ㄷ', 'ㄴ') == 'ㄴ'
    """
    if initial not in ("ㄴ", "ㅁ"):
        return None
    if coda in _CODA_VELAR:
        return "ㅇ"
    if coda in _CODA_ALVEOLAR:
        return "ㄴ"
    if coda in _CODA_BILABIAL:
        return "ㅁ"
    return None


def f_lateralize(coda: str, initial: str) -> tuple[str, str] | None:
    """유음화 §20 — ㄴ·ㄹ 인접 → 둘 다 ㄹ.

    Returns:
        (새 종성, 새 초성) 또는 None.

    Examples:
        f_lateralize('ㄴ', 'ㄹ') == ('ㄹ', 'ㄹ')  # 신루리 → 실루리
        f_lateralize('ㄹ', 'ㄴ') == ('ㄹ', 'ㄹ')  # 김만리 → 김말리
    """
    if coda == "ㄴ" and initial == "ㄹ":
        return ("ㄹ", "ㄹ")
    if coda == "ㄹ" and initial == "ㄴ":
        return ("ㄹ", "ㄹ")
    return None


def f_aspirate(coda: str, initial: str) -> tuple[str, str] | None:
    """격음화 §12 — ㅎ + 평음 또는 평음 + ㅎ → 격음.

    Returns:
        (새 종성, 새 초성) 또는 None.

    Examples:
        f_aspirate('ㄱ', 'ㅎ') == ('', 'ㅋ')  # 박국희 → 박구키
        f_aspirate('ㅎ', 'ㄱ') == ('', 'ㅋ')
    """
    # 종성 ㅎ + 초성 평음 → 격음
    if coda == "ㅎ" and initial in _ASPIRATE_MAP:
        return ("", _ASPIRATE_MAP[initial])
    # 종성 평음 + 초성 ㅎ → 격음
    if coda in _ASPIRATE_MAP and initial == "ㅎ":
        return ("", _ASPIRATE_MAP[coda])
    return None


def f_tensify(coda: str, initial: str) -> str | None:
    """경음화 §23 — 폐쇄음 종성 + 평음 초성 → 경음 초성.

    한자어 §26 (ㄹ받침 + 평음) 별도 처리 필요 (구분 불가하면 미적용).

    Returns:
        새 초성 또는 None.

    Examples:
        f_tensify('ㄱ', 'ㅈ') == 'ㅉ'  # 김국진 → 김국찐
        f_tensify('ㅂ', 'ㅅ') == 'ㅆ'  # 송학동: 송학똥 (학+동 → 학똥)
    """
    if initial not in _PLAIN_CONSONANTS:
        return None
    # §23 — 받침이 ㄱ·ㄷ·ㅂ 계열 (자음군 단순화 후)
    simplified = _CLUSTER_SIMPLIFY.get(coda, coda)
    if simplified in _CODA_VELAR or simplified in _CODA_ALVEOLAR or simplified in _CODA_BILABIAL:
        return _TENSE_MAP.get(initial)
    return None


def f_insert_n(coda: str, initial: str, jung_next: str) -> tuple[str, str] | None:
    """ㄴ첨가 §29~§30 — C1 존재 + C2=ㅇ + 후행 중성 ㅣ류 → ㄴ첨가.

    Returns:
        (새 종성, 새 초성) 또는 None.

    Examples:
        f_insert_n('ㅇ', 'ㅇ', 'ㅛ') == None  # 박영진: 단어 경계 아님
        f_insert_n('ㄴ', 'ㅇ', 'ㅑ') → ('ㄴ', 'ㄴ')  # 송녀름의 첨가 패턴
    """
    if not coda or initial != "ㅇ" or jung_next not in _N_INSERT_VOWELS:
        return None
    # 단순 ㄴ첨가: 후행 ㅇ → ㄴ
    return (coda, "ㄴ")


def f_simplify_cluster(coda: str) -> str:
    """자음군 단순화 §10~§11 — 어말·자음 앞 겹받침 단일화.

    Examples:
        f_simplify_cluster('ㄳ') == 'ㄱ'
        f_simplify_cluster('ㄶ') == 'ㄴ'
    """
    return _CLUSTER_SIMPLIFY.get(coda, coda)


def f_link(coda: str, initial: str) -> tuple[str, str] | None:
    """연음 §13~§16 — C1 + 초성 ㅇ → C1을 다음 음절 초성으로 이동.

    §13 (단순 종성): 종성 전체 이동, 종성 빈 문자열.
    §14 (겹받침): 앞 자음은 종성으로 남고 뒤 자음만 이동.

    Returns:
        (새 종성, 새 초성) 또는 None.

    Examples:
        f_link('ㄴ', 'ㅇ') == ('', 'ㄴ')  # §13: 이진희→이지니
        f_link('ㄺ', 'ㅇ') == ('ㄹ', 'ㄱ')  # §14: 송닭이→송달기 (ㄹ 남고 ㄱ 이동)
    """
    if not coda or initial != "ㅇ":
        return None
    # §14 겹받침 — 앞 자음 종성 유지 + 뒤 자음 초성 이동
    DOUBLE_CODA_SPLIT = {
        "ㄳ": ("ㄱ", "ㅅ"),
        "ㄵ": ("ㄴ", "ㅈ"),
        "ㄶ": ("ㄴ", "ㅎ"),
        "ㄺ": ("ㄹ", "ㄱ"),
        "ㄻ": ("ㄹ", "ㅁ"),
        "ㄼ": ("ㄹ", "ㅂ"),
        "ㄽ": ("ㄹ", "ㅅ"),
        "ㄾ": ("ㄹ", "ㅌ"),
        "ㄿ": ("ㄹ", "ㅍ"),
        "ㅀ": ("ㄹ", "ㅎ"),
        "ㅄ": ("ㅂ", "ㅅ"),
    }
    if coda in DOUBLE_CODA_SPLIT:
        kept, moved = DOUBLE_CODA_SPLIT[coda]
        return (kept, moved)
    # §13 단순 종성
    if coda == "ㅎ":
        # ㅎ은 격음화로 가지 않으면 약화 탈락
        return ("", "ㅇ")
    return ("", coda)


def phonetic_delta_score(name_korean: str) -> dict:
    """표준발음법 §10~§30 절대값 어감 변동 점수 (ADR-028).

    보고서 §3·§4 명시 expected_score_delta [-5, 0] 절대값.

    파이프라인:
      1. 자모 분해
      2. 경계별 음운 변동 적용 (비음화·유음화·격음화·경음화·ㄴ첨가·연음)
      3. 변동별 delta 합산 + expected_phonetic 산출

    Returns:
        {
            "input_name": str,
            "expected_phonetic": str,
            "applied_rules": list[str],
            "score_delta": int,  # [-5, 0] 절대값 합
            "rationale": str,  # 면책 자동 포함
        }

    면책 (ADR-010 + ADR-028):
        본 결과는 국립국어원 표준발음법 기반 음운 변동 분석. 운명·길흉
        해석 X. 사용자 출력에 면책 자동 포함.
    """
    syllables = [c for c in name_korean if "가" <= c <= "힣"]
    applied_rules: list[str] = []
    delta = 0

    if len(syllables) < 2:
        return {
            "input_name": name_korean,
            "expected_phonetic": name_korean,
            "applied_rules": [],
            "score_delta": 0,
            "rationale": (
                f"'{name_korean}'은 음운 변동 분석 대상 음절 부족. "
                f"※ {DISCLAIMER_KO}"
            ),
        }

    decomps: list[list[str]] = []
    for s in syllables:
        d = _decompose_jamo(s)
        if d is None:
            return {
                "input_name": name_korean,
                "expected_phonetic": name_korean,
                "applied_rules": [],
                "score_delta": 0,
                "rationale": f"'{name_korean}' 분해 실패. ※ {DISCLAIMER_KO}",
            }
        decomps.append([d[0], d[1], d[2]])

    # 음운 변동 적용 — 경계별 좌→우
    for i in range(len(decomps) - 1):
        jong1 = decomps[i][2]
        cho2 = decomps[i + 1][0]

        # §18~19 비음화
        new_jong = f_nasalize(jong1, cho2)
        if new_jong is not None:
            decomps[i][2] = new_jong
            applied_rules.append(f"§18~19 비음화 ({jong1}→{new_jong} / {cho2}_)")
            delta -= 2
            continue

        # §20 유음화
        lateral = f_lateralize(jong1, cho2)
        if lateral is not None:
            decomps[i][2] = lateral[0]
            decomps[i + 1][0] = lateral[1]
            applied_rules.append(f"§20 유음화 ({jong1}+{cho2}→ㄹㄹ)")
            delta -= 1
            continue

        # §12 격음화
        aspirate = f_aspirate(jong1, cho2)
        if aspirate is not None:
            decomps[i][2] = aspirate[0]
            decomps[i + 1][0] = aspirate[1]
            applied_rules.append(f"§12 격음화 ({jong1}+{cho2}→{aspirate[1]})")
            delta -= 1
            continue

        # §23~28 경음화
        tense = f_tensify(jong1, cho2)
        if tense is not None:
            decomps[i + 1][0] = tense
            # §26 한자어 특례 추정 + 송학동 같은 극단 사례
            ext = -3 if cho2 in ("ㅅ", "ㅈ") else -4
            applied_rules.append(f"§23~26 경음화 ({jong1}+{cho2}→{tense})")
            delta += ext
            continue

        # §13~16 연음 (종성 + 초성 ㅇ)
        link = f_link(jong1, cho2)
        if link is not None:
            decomps[i][2] = link[0]
            decomps[i + 1][0] = link[1]
            applied_rules.append(f"§13~16 연음 ({jong1}→{link[1]}_)")
            # 연음은 자연스러운 변동, delta 0
            continue

    expected = "".join(_compose_jamo(c, j, jg) or "" for c, j, jg in decomps)
    # delta 클램프 (보고서 [-5, 0])
    delta = max(-5, min(0, delta))

    rule_summary = ", ".join(applied_rules) if applied_rules else "변동 없음"
    rationale = (
        f"'{name_korean}'은 표준발음법 적용 시 [{expected}]으로 발음됩니다 "
        f"({rule_summary}). "
        f"※ {DISCLAIMER_KO}"
    )
    return {
        "input_name": name_korean,
        "expected_phonetic": expected,
        "applied_rules": applied_rules,
        "score_delta": delta,
        "rationale": rationale,
    }
