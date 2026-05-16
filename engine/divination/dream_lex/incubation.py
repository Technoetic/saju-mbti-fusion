"""꿈 부화(Dream Incubation) — 취침 전 질문·확언·명상 안내.

출처: Edelstein & Edelstein, Asclepius (1945)
고대 그리스 아스클레피오스 신전 수면(엥키미시스, ἐγκοίμησις) 전통의 현대화.

현대 임상에서도 사용됨 — Barrett (1993) "The 'Committee of Sleep'"
취침 전 명확한 질문 + 의도 형성이 꿈 회상률과 문제 해결 꿈 빈도를 높임.
"""

from __future__ import annotations
from typing import Any


INCUBATION_LABEL = (
    "꿈 부화 — 고대 신전 수면 전통의 현대화. 취침 전 질문·확언·이완 절차로 "
    "꿈 회상률과 의미 있는 꿈 빈도를 높임."
)


# 부화 안내 단계
INCUBATION_STEPS = [
    {
        "step": 1,
        "name": "환경 정돈",
        "duration_min": 5,
        "instruction": (
            "침실 조명을 낮추고, 휴대폰 알림을 끄세요. 침대 옆에 종이와 펜을 두세요 — "
            "깨자마자 꿈을 적기 위해서입니다."
        ),
    },
    {
        "step": 2,
        "name": "질문 명확화",
        "duration_min": 3,
        "instruction": (
            "오늘 밤 꿈에서 답을 구하고 싶은 질문 하나를 한 문장으로 적어보세요. "
            "예: '내가 지금 직장을 옮기는 것이 옳은가?' "
            "추상적이지 않게, 구체적으로."
        ),
    },
    {
        "step": 3,
        "name": "확언 형성",
        "duration_min": 2,
        "instruction": (
            "다음 문장을 3번 천천히 마음속으로 반복하십시오: "
            "'나는 오늘 밤 의미 있는 꿈을 꿀 것이며, 깨어났을 때 그 꿈을 기억할 것이다.' "
            "단정이 아닌 의도 형성입니다."
        ),
    },
    {
        "step": 4,
        "name": "이완 호흡",
        "duration_min": 5,
        "instruction": (
            "눈을 감고 4초 들이쉬고, 4초 멈추고, 6초 내쉬는 호흡을 10회 반복하세요. "
            "어깨와 턱의 긴장을 풀어주세요."
        ),
    },
    {
        "step": 5,
        "name": "시각화 안착",
        "duration_min": 5,
        "instruction": (
            "안전하다고 느끼는 장소(어린 시절 집·해변·산 등)를 마음속에 그리며 "
            "그 안에 머무세요. 그 장소에서 자연스럽게 잠으로 이행하도록 두세요."
        ),
    },
]


# 깨어난 직후 회상 안내
RECALL_INSTRUCTION_KO = """[깨어난 직후 — 1분 안에 시도]

  1. 눈을 뜨자마자 자세를 바꾸지 마세요 — 같은 자세에서 꿈이 더 잘 떠오릅니다.
  2. 떠오르는 첫 단어·이미지·감정을 그대로 메모하세요. 문장이 안 돼도 좋습니다.
  3. 핵심 키워드 3개와 정서를 먼저 잡고, 그 다음 줄거리를 채우세요.
  4. "왜?"는 나중에. 지금은 "무엇이 있었나?"만.
"""


# 적합도 — 어떤 사용자에게 꿈 부화를 권할지
INCUBATION_RECOMMEND_PATTERNS = [
    {
        "user_signal": "꿈을 자주 못 꾼다 / 기억 안 난다",
        "reason": "회상률 훈련 — 부화는 회상률을 통계적으로 높임",
    },
    {
        "user_signal": "중요한 결정을 앞두고 있다",
        "reason": "Barrett 1993 'Committee of Sleep' — 수면이 문제 해결에 기여",
    },
    {
        "user_signal": "스트레스 정리·정서 회복이 필요하다",
        "reason": "Cartwright 1991 정서 조절 기능 활용",
    },
    {
        "user_signal": "자각몽 훈련 중",
        "reason": "부화의 의도 형성은 자각몽 MILD 기법의 핵심 요소와 중첩",
    },
]


def recommend_incubation(
    *,
    low_recall: bool = False,
    upcoming_decision: bool = False,
    high_stress: bool = False,
    lucid_dream_practice: bool = False,
) -> dict[str, Any]:
    """사용자 상태에 따라 꿈 부화를 권할지 판단."""
    signals = []
    if low_recall:
        signals.append("회상률 훈련")
    if upcoming_decision:
        signals.append("결정 보조")
    if high_stress:
        signals.append("정서 조절")
    if lucid_dream_practice:
        signals.append("자각몽 보조")

    if not signals:
        return {
            "recommend": False,
            "reasons": [],
            "note": "꿈 부화의 명확한 적응증 없음 — 원하실 때 자유롭게 시도 가능합니다.",
        }

    return {
        "recommend": True,
        "reasons": signals,
        "note": (
            f"다음 이유로 꿈 부화를 권합니다: {', '.join(signals)}. "
            "취침 약 20분 전에 5단계 안내를 따라 보세요."
        ),
        "steps": INCUBATION_STEPS,
        "total_duration_min": sum(s["duration_min"] for s in INCUBATION_STEPS),
    }


def build_incubation_session(question: str) -> dict[str, Any]:
    """사용자 질문 + 5단계 안내 + 회상 가이드를 묶어 반환."""
    q = (question or "").strip() or "(오늘 밤 마음에 떠오르는 것을 받아들이겠습니다)"
    return {
        "user_question": q,
        "affirmation": (
            f"오늘 밤 나는 '{q}'에 대한 의미 있는 꿈을 꿀 것이며, "
            "깨어났을 때 그 꿈을 기억할 것이다."
        ),
        "steps": INCUBATION_STEPS,
        "total_duration_min": sum(s["duration_min"] for s in INCUBATION_STEPS),
        "recall_instruction": RECALL_INSTRUCTION_KO,
        "disclaimer": (
            "꿈 부화는 회상률·의미감을 높이는 자기관찰 도구이며, 의료 치료가 아닙니다. "
            "수면 장애가 의심되면 수면 클리닉 상담을 권합니다."
        ),
    }


__all__ = [
    "INCUBATION_LABEL",
    "INCUBATION_STEPS",
    "RECALL_INSTRUCTION_KO",
    "INCUBATION_RECOMMEND_PATTERNS",
    "recommend_incubation",
    "build_incubation_session",
]
