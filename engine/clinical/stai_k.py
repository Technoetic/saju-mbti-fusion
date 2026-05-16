"""STAI 한국판 (State-Trait Anxiety Inventory) — 상태 불안 척도.

출처: 한덕웅·이장호·전겸구 (1996) "한국판 STAI 표준화", 한국심리학회지: 임상 15(1)
원판: Spielberger (1970) Manual for the State-Trait Anxiety Inventory

구조:
  - 상태 불안(State) 20문항, 4점 척도 (1~4)
  - 총점 20~80점
  - cutoff: 상태 불안 ≥ 52점 (고불안, 한덕웅 1996)
  - 역채점: 1, 2, 5, 8, 10, 11, 15, 16, 19, 20번
"""

from __future__ import annotations
from typing import Any


STAI_K_STATE_CUTOFF = 52  # 한덕웅 외 1996 고불안 임계


STAI_K_STATE_RESPONSE_OPTIONS = {
    1: "전혀 그렇지 않다",
    2: "약간 그렇다",
    3: "상당히 그렇다",
    4: "매우 그렇다",
}


# 상태 불안 20문항 — "지금 이 순간" 기준
STAI_K_STATE_ITEMS_KO: list[dict[str, Any]] = [
    {"no": 1, "text": "나는 마음이 차분하다", "reversed": True},
    {"no": 2, "text": "나는 마음이 든든하다", "reversed": True},
    {"no": 3, "text": "나는 긴장되어 있다", "reversed": False},
    {"no": 4, "text": "나는 후회스럽고 서운하다", "reversed": False},
    {"no": 5, "text": "나는 마음이 편하다", "reversed": True},
    {"no": 6, "text": "나는 당황해서 어찌할 바를 모르겠다", "reversed": False},
    {"no": 7, "text": "나는 앞으로 불행이 있을까봐 걱정하고 있다", "reversed": False},
    {"no": 8, "text": "나는 마음을 놓고 있다", "reversed": True},
    {"no": 9, "text": "나는 불안하다", "reversed": False},
    {"no": 10, "text": "나는 편안하게 느낀다", "reversed": True},
    {"no": 11, "text": "나는 자신감이 있다", "reversed": True},
    {"no": 12, "text": "나는 짜증스럽다", "reversed": False},
    {"no": 13, "text": "나는 마음이 조마조마하다", "reversed": False},
    {"no": 14, "text": "나는 극도로 긴장되어 있다", "reversed": False},
    {"no": 15, "text": "내 마음은 긴장이 풀려 푸근하다", "reversed": True},
    {"no": 16, "text": "나는 만족스럽다", "reversed": True},
    {"no": 17, "text": "나는 걱정하고 있다", "reversed": False},
    {"no": 18, "text": "나는 흥분되어 어쩔 줄을 모르겠다", "reversed": False},
    {"no": 19, "text": "나는 즐겁다", "reversed": True},
    {"no": 20, "text": "나는 기분이 좋다", "reversed": True},
]


def score_stai_k_state(responses: list[int]) -> dict[str, Any]:
    """STAI 상태 불안 채점."""
    if len(responses) != 20:
        raise ValueError(f"STAI 상태는 20개 응답 필요 (받음: {len(responses)})")
    for i, r in enumerate(responses):
        if r not in (1, 2, 3, 4):
            raise ValueError(f"응답은 1~4 정수여야 함 (item {i + 1}: {r})")

    total = 0
    for idx, raw in enumerate(responses):
        item = STAI_K_STATE_ITEMS_KO[idx]
        score = (5 - raw) if item["reversed"] else raw
        total += score

    exceeded = total >= STAI_K_STATE_CUTOFF
    if total < 40:
        severity = "낮은 불안"
    elif total < 52:
        severity = "보통 불안"
    elif total < 60:
        severity = "높은 불안"
    else:
        severity = "매우 높은 불안"

    return {
        "total_score": total,
        "cutoff": STAI_K_STATE_CUTOFF,
        "exceeded_cutoff": exceeded,
        "severity": severity,
        "interpretive_note": (
            "고불안 임계 초과 — 지속될 경우 전문가 상담을 권합니다."
            if exceeded
            else "현 시점 불안 수준은 임계 미만. 자가보고는 그날의 상태에 영향."
        ),
        "referral_recommended": exceeded,
        "instrument": "STAI 상태 한국판 (한덕웅·이장호·전겸구 1996)",
    }


__all__ = [
    "STAI_K_STATE_CUTOFF",
    "STAI_K_STATE_RESPONSE_OPTIONS",
    "STAI_K_STATE_ITEMS_KO",
    "score_stai_k_state",
]
