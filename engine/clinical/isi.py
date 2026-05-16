"""ISI (Insomnia Severity Index) — 불면증 심각도.

출처: Bastien et al. (2001) Sleep Medicine 2(4)
한국판: 조용원 외 (2014) 대한신경정신의학회지

구조:
  - 7문항, 0~4점 척도
  - 총점 0~28점
  - cutoff: ≥ 8 경도 불면, ≥ 15 임상적 불면, ≥ 22 중증 불면
"""

from __future__ import annotations
from typing import Any


ISI_RESPONSE_OPTIONS_DIFFICULTY = {
    0: "전혀 없음",
    1: "약간",
    2: "보통",
    3: "심함",
    4: "매우 심함",
}

ISI_RESPONSE_OPTIONS_SATISFACTION = {
    0: "매우 만족",
    1: "만족",
    2: "보통",
    3: "불만족",
    4: "매우 불만족",
}


ISI_ITEMS_KO: list[dict[str, Any]] = [
    {"no": 1, "text": "잠들기 어려움", "options": ISI_RESPONSE_OPTIONS_DIFFICULTY},
    {"no": 2, "text": "수면 유지 어려움 (자다 깸)", "options": ISI_RESPONSE_OPTIONS_DIFFICULTY},
    {"no": 3, "text": "너무 일찍 잠에서 깸", "options": ISI_RESPONSE_OPTIONS_DIFFICULTY},
    {"no": 4, "text": "현재 수면 양상에 대한 만족도", "options": ISI_RESPONSE_OPTIONS_SATISFACTION},
    {"no": 5, "text": "수면 문제가 일상 기능에 미치는 영향이 다른 사람에게 보이는 정도",
     "options": {0: "전혀 안 보임", 1: "약간 보임", 2: "어느 정도", 3: "많이", 4: "매우 많이"}},
    {"no": 6, "text": "현재 수면 문제로 인한 걱정·고통의 정도", "options": ISI_RESPONSE_OPTIONS_DIFFICULTY},
    {"no": 7, "text": "수면 문제가 낮 생활(피로·집중·기분·기억 등)에 영향을 주는 정도",
     "options": ISI_RESPONSE_OPTIONS_DIFFICULTY},
]


def score_isi(responses: list[int]) -> dict[str, Any]:
    """ISI 채점."""
    if len(responses) != 7:
        raise ValueError(f"ISI는 7개 응답 필요 (받음: {len(responses)})")
    for i, r in enumerate(responses):
        if r not in (0, 1, 2, 3, 4):
            raise ValueError(f"응답은 0~4 정수 (item {i + 1}: {r})")

    total = sum(responses)
    if total < 8:
        severity = "임상적 의미 없음"
        referral = False
    elif total < 15:
        severity = "경도 불면증"
        referral = True
    elif total < 22:
        severity = "중등도 불면증"
        referral = True
    else:
        severity = "중증 불면증"
        referral = True

    return {
        "total_score": total,
        "severity": severity,
        "referral_recommended": referral,
        "interpretive_note": (
            "불면 증상이 임상적 수준 — 수면 클리닉 또는 정신건강의학과 상담을 권합니다."
            if total >= 15
            else "경도 불면 가능성 — 수면 위생 점검 권장."
            if total >= 8
            else "임상적 불면 의심 수준 미만."
        ),
        "instrument": "ISI (Bastien 2001)",
    }


__all__ = [
    "ISI_ITEMS_KO",
    "score_isi",
]
