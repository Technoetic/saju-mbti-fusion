"""Joe Griffin 기대 충족 이론 (Expectation Fulfillment Theory).

출처: Griffin & Tyrrell, Human Givens Institute

핵심:
  - 낮 동안 형성된 감정적 '기대'(예: 분노·욕망)가 사회적 억압으로 미실행
  - 미해결된 각성(arousal)은 자율신경계에 누적
  - REM 꿈에서 PGO 파가 이 미결 기대를 가상으로 실행 → 방전(discharge)
  - 은유 형태인 이유: 실제 사건으로 기록되면 거짓 기억(false memory) 위험
  - PTSD = 각성은 촉발되나 방전되지 못한 상태

본 모듈의 역할:
  - 낮의 '미실행 기대'(억제된 분노·욕망·욕동) 입력 받기
  - 꿈에서 그것이 은유적으로 방전되었는지 매칭
  - PTSD 위험 신호 (반복되는 미방전) 탐지
"""

from __future__ import annotations
from typing import Any


GRIFFIN_EFT_LABEL = (
    "Griffin EFT — 낮의 미실행 감정 기대가 REM 꿈에서 은유적으로 방전됨. "
    "은유는 거짓 기억을 피하기 위한 진화적 코딩 (Human Givens)."
)


# 미실행 기대(억제된 욕동)의 일반적 카테고리
EXPECTATION_CATEGORIES = {
    "anger": {
        "korean": "분노 방전",
        "daily_triggers": ["짜증", "화났", "참았", "억누른", "성가", "당했"],
        "dream_discharge_patterns": [
            "싸웠", "이겼", "때렸", "복수했", "내가 이겼",
            "괴물을 죽였", "지배자가 됐", "권력을 잡았",
        ],
    },
    "desire": {
        "korean": "욕망·매력 방전",
        "daily_triggers": ["호감", "끌렸", "매력", "원했", "보고 싶",
                           "갖고 싶", "함께하고 싶"],
        "dream_discharge_patterns": [
            "키스했", "만났", "함께 있었", "포옹", "결혼했",
            "얻었", "가졌", "획득",
        ],
    },
    "fear_escape": {
        "korean": "공포 회피·탈출 방전",
        "daily_triggers": ["불안", "걱정", "겁났", "두려", "피하고 싶",
                           "도망가고 싶"],
        "dream_discharge_patterns": [
            "도망쳤", "탈출", "벗어났", "안전한 곳", "숨었",
            "쫓겼다가 살았", "달아나 성공",
        ],
    },
    "achievement": {
        "korean": "성취·인정 방전",
        "daily_triggers": ["인정 못 받", "무시당", "공로", "노력 헛",
                           "보여주고 싶"],
        "dream_discharge_patterns": [
            "박수 받았", "1등", "수상", "왕관", "트로피", "메달",
            "유명해졌", "주목 받",
        ],
    },
    "loss_grief": {
        "korean": "상실·애도 방전",
        "daily_triggers": ["잃었", "헤어진", "떠난", "죽은", "사별",
                           "끝났"],
        "dream_discharge_patterns": [
            "다시 만났", "돌아왔", "함께 있었", "재회",
            "용서받았", "사과했",
        ],
    },
}


def detect_expectation_discharge(
    text: str,
    *,
    daytime_context: str | None = None,
) -> dict[str, Any]:
    """미실행 기대의 야간 방전 탐지.

    Args:
        text: 꿈 본문
        daytime_context: (선택) 사용자가 보고한 낮의 미해결 감정
    """
    t = text or ""
    daytime = daytime_context or ""

    results: list[dict[str, Any]] = []
    total_daytime_triggers = 0
    total_dream_discharge = 0

    for cat_key, cat in EXPECTATION_CATEGORIES.items():
        daytime_hits = (
            [m for m in cat["daily_triggers"] if m in daytime]
            if daytime else []
        )
        dream_hits = [m for m in cat["dream_discharge_patterns"] if m in t]

        if daytime_hits or dream_hits:
            results.append({
                "category": cat_key,
                "korean": cat["korean"],
                "daytime_triggers_matched": daytime_hits,
                "dream_discharge_matched": dream_hits,
                "fully_discharged": bool(daytime_hits) and bool(dream_hits),
                "unresolved_arousal": bool(daytime_hits) and not bool(dream_hits),
            })
        total_daytime_triggers += len(daytime_hits)
        total_dream_discharge += len(dream_hits)

    # PTSD 위험 신호 — 미방전 패턴
    ptsd_risk_indicators = [
        "또 그 일", "다시 그 사람", "여전히 무서", "벗어나지 못",
        "쫓겨도 살아남지 못", "결국 잡혔", "도망 실패",
    ]
    ptsd_hits = [m for m in ptsd_risk_indicators if m in t]

    # 종합 판정
    if ptsd_hits:
        verdict = "미방전 패턴 (주의)"
        note = (
            "각성이 촉발되었으나 방전되지 못한 패턴. 6개월 이상 지속되면 "
            "PTSD 가능성을 고려해 전문가 상담을 권합니다."
        )
    elif total_dream_discharge >= 2:
        verdict = "활발한 은유적 방전"
        note = (
            "낮의 미실행 감정이 꿈에서 은유적으로 잘 방전되었습니다. "
            "아침에 그 감정이 가벼워진 느낌이 있다면 EFT의 정상 작동."
        )
    elif total_daytime_triggers > 0 and total_dream_discharge == 0:
        verdict = "방전 부족"
        note = (
            "낮의 각성에 비해 꿈의 방전 신호가 부족. "
            "수면 질 점검 또는 IRT(악몽 재각본) 권장."
        )
    elif total_dream_discharge >= 1:
        verdict = "부분 방전"
        note = "일부 카테고리에서 방전 진행 중."
    else:
        verdict = "신호 미감지"
        note = "EFT 관점의 명확한 방전 신호가 없습니다."

    return {
        "category_matches": results,
        "total_daytime_triggers": total_daytime_triggers,
        "total_dream_discharge": total_dream_discharge,
        "ptsd_risk_indicators": ptsd_hits,
        "verdict": verdict,
        "interpretive_note": note,
        "griffin_principle": (
            "꿈이 은유 형태인 이유: 실제 사건으로 기록되면 거짓 기억 위험. "
            "은유는 감정적 각성만 정확히 방전하고 본문은 잊히게 설계된 진화적 코딩."
        ),
    }


__all__ = [
    "GRIFFIN_EFT_LABEL",
    "EXPECTATION_CATEGORIES",
    "detect_expectation_discharge",
]
