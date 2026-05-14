"""A. Revonsuo 위협 시뮬레이션 이론(Threat Simulation Theory).

진화적 가설 — 꿈은 조상 환경의 위협을 시뮬레이션해 회피 기제를 강화한다.
실증: 꿈 보고의 65~80%가 부정적 정서를 포함, 위협 장면은 흔함.

이 모듈의 역할:
  - 위협 요소(추격·낙하·공격·재난) 탐지
  - 회피·대처 행동의 유무 분류
  - 'threat rehearsal' 시그널을 critic에 제공
"""

from __future__ import annotations
from typing import Any


TST_LABEL = (
    "위협 시뮬레이션 — 꿈은 진화적으로 위협 회피를 연습하는 무대일 수 있음. "
    "추격·낙하·공격·재난이 흔한 이유."
)


# 위협 카테고리별 키워드
THREAT_CHASE = ["추격", "쫓김", "쫓아옴", "달아남", "도망", "뒤따라옴", "추적자", "쫓는 자"]
THREAT_FALL = ["떨어짐", "추락", "낙하", "절벽", "빌딩에서 떨어", "다리에서 떨어"]
THREAT_ATTACK = ["공격", "맞음", "구타", "찔림", "총", "칼", "물어뜯김", "습격"]
THREAT_DISASTER = ["지진", "홍수", "쓰나미", "해일", "화재", "산불", "태풍", "허리케인", "토네이도", "폭발", "건물 무너짐"]
THREAT_PURSUIT_ANIMAL = ["맹수", "호랑이 공격", "사자 공격", "곰 공격", "뱀에게 물림", "개에게 물림"]
THREAT_HUMAN = ["강도", "도둑", "괴한", "납치", "감금", "살인자"]
THREAT_HEALTH = ["병에 걸림", "암 진단", "쓰러짐", "기절", "심장마비", "숨막힘"]
THREAT_LOSS = ["가족 잃음", "아이 잃음", "길 잃음", "혼자 남음", "버려짐"]
THREAT_SUPERNATURAL = ["귀신", "악령", "악마", "유령", "저주", "원귀"]

# 대처 행동 마커
COPING_MARKERS = [
    "맞서 싸움", "이겨냄", "탈출", "빠져나옴", "구조됨", "도움 받음",
    "숨음", "피함", "도망쳐 성공", "안전한 곳", "안심", "위험 모면",
]


def detect_threats(text: str) -> dict[str, Any]:
    """위협 시뮬레이션 신호 탐지."""
    t = text or ""

    categories: dict[str, list[str]] = {
        "chase": [k for k in THREAT_CHASE if k in t],
        "fall": [k for k in THREAT_FALL if k in t],
        "attack": [k for k in THREAT_ATTACK if k in t],
        "disaster": [k for k in THREAT_DISASTER if k in t],
        "animal": [k for k in THREAT_PURSUIT_ANIMAL if k in t],
        "human": [k for k in THREAT_HUMAN if k in t],
        "health": [k for k in THREAT_HEALTH if k in t],
        "loss": [k for k in THREAT_LOSS if k in t],
        "supernatural": [k for k in THREAT_SUPERNATURAL if k in t],
    }
    coping = [m for m in COPING_MARKERS if m in t]

    total_threats = sum(len(v) for v in categories.values())
    dominant = max(categories, key=lambda k: len(categories[k])) if total_threats > 0 else None

    if total_threats == 0:
        level = "위협 없음"
        interpretation = "위협 모티프 없음 — TST 적용 비대상."
    elif total_threats <= 2 and coping:
        level = "낮음(대처 성공)"
        interpretation = "위협이 있으나 대처 성공 — 회피 기제 강화 양상."
    elif total_threats <= 2:
        level = "낮음"
        interpretation = "약한 위협 — 일반적 스트레스 반영."
    elif total_threats <= 5 and coping:
        level = "중간(대처 성공)"
        interpretation = "위협 다발이나 대처 성공 — 자기효능감 신호."
    elif total_threats <= 5:
        level = "중간"
        interpretation = "현재 깨어 있는 삶의 미해결 위협 가능. 무엇이 위협인지 점검."
    else:
        level = "높음"
        interpretation = "강한 위협 시뮬레이션 — 누적된 불안. 안전감 회복 우선."

    return {
        "threat_categories": categories,
        "total_threats": total_threats,
        "dominant_threat": dominant,
        "coping_actions": coping,
        "coping_success": len(coping) > 0,
        "tst_level": level,
        "interpretation": interpretation,
    }


__all__ = [
    "TST_LABEL",
    "detect_threats",
]
