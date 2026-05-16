"""CES-D 한국판 (Center for Epidemiologic Studies Depression Scale).

출처: 전겸구·이민규 (1992) "한국판 CES-D 개발", 한국심리학회지: 임상 11(1)
원판: Radloff (1977) Applied Psychological Measurement 1(3)

구조:
  - 20문항, 0~3점 척도
  - 총점 0~60점
  - cutoff: 일반인 16점 / 노인 21점 (전겸구 외 1999)
  - 역채점 문항: 4, 8, 12, 16번 (0번 인덱스 기준: 3, 7, 11, 15)
  - 항목 16(0-idx 15)은 자살 사고 관련 — 위기 분기 트리거
"""

from __future__ import annotations
from typing import Any


CES_D_CUTOFF_ADULT = 16  # 일반 성인
CES_D_CUTOFF_SENIOR = 21  # 만 65세 이상 (전겸구 외 1999)

CES_D_RESPONSE_OPTIONS = {
    0: "거의 드물게 (1일 미만)",
    1: "때로 (1~2일)",
    2: "상당히 (3~4일)",
    3: "대부분 (5~7일)",
}

# 한국판 20문항 (전겸구·이민규 1992)
CES_D_ITEMS_KO: list[dict[str, Any]] = [
    {"no": 1, "text": "평소 아무렇지도 않던 일들이 귀찮게 느껴졌다", "reversed": False},
    {"no": 2, "text": "먹고 싶지 않았다 — 입맛이 없었다", "reversed": False},
    {"no": 3, "text": "가족이나 친구가 도와주어도 울적한 기분을 떨쳐버릴 수 없었다", "reversed": False},
    {"no": 4, "text": "다른 사람들만큼 능력이 있다고 느꼈다", "reversed": True},
    {"no": 5, "text": "내가 하는 일에 마음을 집중하기가 어려웠다", "reversed": False},
    {"no": 6, "text": "우울했다", "reversed": False},
    {"no": 7, "text": "하는 일마다 힘들게 느껴졌다", "reversed": False},
    {"no": 8, "text": "미래에 대해 희망적으로 느꼈다", "reversed": True},
    {"no": 9, "text": "내 인생은 실패작이라는 생각이 들었다", "reversed": False},
    {"no": 10, "text": "두려움을 느꼈다", "reversed": False},
    {"no": 11, "text": "잠을 편히 자지 못했다", "reversed": False},
    {"no": 12, "text": "행복했다", "reversed": True},
    {"no": 13, "text": "평소보다 말을 적게 했다", "reversed": False},
    {"no": 14, "text": "외로움을 느꼈다", "reversed": False},
    {"no": 15, "text": "사람들이 나에게 불친절하다고 느꼈다", "reversed": False},
    {"no": 16, "text": "생활을 즐겁게 보냈다", "reversed": True},
    {"no": 17, "text": "갑자기 울음이 나왔다", "reversed": False},
    {"no": 18, "text": "슬픔을 느꼈다", "reversed": False},
    {"no": 19, "text": "사람들이 나를 싫어한다는 느낌이 들었다", "reversed": False},
    {"no": 20, "text": "도무지 무엇을 시작할 기력이 없었다", "reversed": False},
]


def score_ces_d(responses: list[int], age: int | None = None) -> dict[str, Any]:
    """CES-D 채점.

    Args:
        responses: 20개 응답 (0~3). 길이 검증.
        age: 나이 (cutoff 분기용)

    Returns:
        {
            "total_score": int,
            "cutoff": int,
            "exceeded_cutoff": bool,
            "severity": str,  # "정상" | "경증 우울 의심" | "중증도" | "중증"
            "interpretive_note": str,
            "referral_recommended": bool,
        }
    """
    if len(responses) != 20:
        raise ValueError(f"CES-D는 20개 응답 필요 (받음: {len(responses)})")
    for i, r in enumerate(responses):
        if r not in (0, 1, 2, 3):
            raise ValueError(f"응답은 0~3 정수여야 함 (item {i + 1}: {r})")

    total = 0
    for idx, raw in enumerate(responses):
        item = CES_D_ITEMS_KO[idx]
        score = (3 - raw) if item["reversed"] else raw
        total += score

    cutoff = CES_D_CUTOFF_SENIOR if (age and age >= 65) else CES_D_CUTOFF_ADULT
    exceeded = total >= cutoff

    if total < cutoff:
        severity = "정상 범위"
        note = "현 시점 우울 의심 수준 미만. 다만 자가보고는 시점·심신 컨디션에 영향을 받으니 참고 자료로만."
    elif total < 21:
        severity = "경증 우울 의심"
        note = "cutoff 초과 — 지속될 경우 정신건강의학과 또는 가정의학과 상담 권장."
    elif total < 25:
        severity = "중등도 우울 의심"
        note = "전문가 상담을 적극 권합니다."
    else:
        severity = "중증 우울 의심"
        note = "가급적 빠른 시일 내 정신건강의학과 진료를 권합니다."

    return {
        "total_score": total,
        "cutoff": cutoff,
        "exceeded_cutoff": exceeded,
        "severity": severity,
        "interpretive_note": note,
        "referral_recommended": exceeded,
        "instrument": "CES-D 한국판 (전겸구·이민규 1992)",
    }


__all__ = [
    "CES_D_CUTOFF_ADULT",
    "CES_D_CUTOFF_SENIOR",
    "CES_D_RESPONSE_OPTIONS",
    "CES_D_ITEMS_KO",
    "score_ces_d",
]
