"""DreamBank 규범치(norms) — Hall-Van de Castle 코딩의 표준 비교 기준.

DreamBank.net에 축적된 수천 개의 꿈 보고를 코딩해 도출한 비율들.
이 모듈은 핵심 norms만 발췌해, 사용자 꿈의 지표를 일반인 평균과 비교한다.

출처(연구 합의치, 다수 논문에서 일관):
  - 남성 평균 공격성 ~ 47%
  - 여성 평균 공격성 ~ 44%
  - 남성 부정 정서 ~ 80%
  - 여성 부정 정서 ~ 73%
  - 불운(misfortune) ~ 36~38%
"""

from __future__ import annotations
from typing import Any


DREAMBANK_LABEL = (
    "DreamBank 규범치 — 수천 명 표본의 HvDC 코딩 평균. "
    "내 꿈이 일반 분포에서 어디 위치하는지 보여줌."
)


# Hall-Van de Castle norms (백분율)
NORMS = {
    "male": {
        "aggression_pct": 47.0,
        "negative_emotion_pct": 80.0,
        "misfortune_pct": 36.0,
        "failure_pct": 56.0,
        "friendliness_pct": 53.0,
    },
    "female": {
        "aggression_pct": 44.0,
        "negative_emotion_pct": 73.0,
        "misfortune_pct": 38.0,
        "failure_pct": 54.0,
        "friendliness_pct": 56.0,
    },
}


def _classify_deviation(value: float, norm: float, tolerance: float = 10.0) -> str:
    diff = value - norm
    if abs(diff) <= tolerance:
        return "평균 범위"
    if diff > tolerance:
        return "평균보다 높음"
    return "평균보다 낮음"


def compare_to_norms(indices: dict[str, float], gender: str | None) -> dict[str, Any]:
    """사용자 지표를 DreamBank 규범과 비교."""
    norm_key = "male" if gender == "M" else "female" if gender == "F" else "male"
    norm = NORMS[norm_key]

    comparisons: dict[str, dict[str, Any]] = {}
    for metric, user_val in indices.items():
        if metric in norm:
            comparisons[metric] = {
                "user": user_val,
                "norm": norm[metric],
                "deviation": round(user_val - norm[metric], 1),
                "verdict": _classify_deviation(user_val, norm[metric]),
            }

    return {
        "reference_norm_gender": norm_key,
        "comparisons": comparisons,
        "interpretive_note": _build_note(comparisons),
    }


def _build_note(comparisons: dict[str, dict[str, Any]]) -> str:
    notes: list[str] = []
    for metric, info in comparisons.items():
        if info["verdict"] == "평균 범위":
            continue
        label = {
            "aggression_pct": "공격성",
            "negative_emotion_pct": "부정 정서",
            "misfortune_pct": "불운 비율",
            "failure_pct": "실패 비율",
        }.get(metric, metric)
        direction = "↑" if info["deviation"] > 0 else "↓"
        notes.append(f"{label} {direction} (Δ{info['deviation']:+.1f}%)")

    if not notes:
        return "일반 분포 범위 — 특이점 없음."
    return "특이점: " + ", ".join(notes)


__all__ = [
    "DREAMBANK_LABEL",
    "NORMS",
    "compare_to_norms",
]
