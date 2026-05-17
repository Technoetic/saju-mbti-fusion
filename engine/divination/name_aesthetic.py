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
  - 음운 결합 규칙 (보고서 §1) 데이터 미완으로 미채택
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
