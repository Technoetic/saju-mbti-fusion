"""Lakoff & Johnson 개념적 은유 이론 (Conceptual Metaphor Theory).

출처:
  - Lakoff & Johnson (1980) Metaphors We Live By
  - Lakoff (1997) "How unconscious metaphorical thought shapes dreams"

핵심:
  - 은유 = 시적 수사가 아니라 인간 인지의 본원적 구조
  - 근원 영역(source) → 목표 영역(target) 매핑
  - 보편 은유 (예: LOVE IS A JOURNEY) 가 꿈의 시나리오 구성

본 모듈의 역할:
  - 꿈 텍스트에서 근원 영역(공간/물리/신체) 추출
  - 사용자의 목표 영역(연애/일/건강/돈)으로 교차 매핑
  - 단순 키워드 직역 회피
"""

from __future__ import annotations
from typing import Any


LAKOFF_CMT_LABEL = (
    "Lakoff & Johnson CMT — 은유는 인지의 본원적 구조. 근원(신체·공간)→목표(추상) 매핑. "
    "꿈은 무의식의 은유 언어 (Lakoff 1997)."
)


# 보편 은유 — 근원 영역의 흔적 → 추정되는 목표 영역
UNIVERSAL_METAPHORS: dict[str, dict[str, Any]] = {
    "LOVE_IS_A_JOURNEY": {
        "label": "사랑은 여정",
        "source_markers": ["갈림길", "길을 잃", "길이 막힘", "막다른 골목",
                           "차가 고장", "다리가 끊", "터널 끝", "함께 걸",
                           "함께 운전", "헤어진 길"],
        "target": "연애·관계",
        "interpretation_hint": "관계의 진행·정체·전환점을 점검하라는 신호",
    },
    "LIFE_IS_A_JOURNEY": {
        "label": "인생은 여정",
        "source_markers": ["오르막", "내리막", "산 정상", "꼭대기",
                           "도착", "출발", "여행", "이정표"],
        "target": "삶의 방향·진로",
        "interpretation_hint": "현재의 인생 단계·방향 점검",
    },
    "ARGUMENT_IS_WAR": {
        "label": "논쟁은 전쟁",
        "source_markers": ["싸움", "전투", "방어", "공격", "이겼",
                           "졌다", "포위", "후퇴", "무기"],
        "target": "갈등·논쟁·의견 대립",
        "interpretation_hint": "현실의 갈등 상황의 야간 시뮬레이션",
    },
    "EMOTIONS_ARE_LIQUIDS": {
        "label": "감정은 액체",
        "source_markers": ["넘쳐", "흘러", "쏟아", "잠겼",
                           "범람", "차올라", "휩쓸려", "익사"],
        "target": "감정의 압도·통제 불능",
        "interpretation_hint": "감당하기 어려운 감정의 시각화",
    },
    "GOOD_IS_UP": {
        "label": "좋음은 위",
        "source_markers": ["올라갔", "하늘로", "공중에 떠", "상승",
                           "정상", "꼭대기에"],
        "target": "성취·기쁨·우월감",
        "interpretation_hint": "긍정적 정서·성취 욕구의 발현",
    },
    "BAD_IS_DOWN": {
        "label": "나쁨은 아래",
        "source_markers": ["떨어졌", "추락", "지하", "바닥",
                           "가라앉", "내려갔"],
        "target": "좌절·우울·실패",
        "interpretation_hint": "통제 상실 또는 침체된 정서",
    },
    "IDEAS_ARE_PLANTS": {
        "label": "생각은 식물",
        "source_markers": ["싹이", "꽃이 피", "열매", "자라났",
                           "뿌리", "시들", "썩었"],
        "target": "아이디어·계획·재능",
        "interpretation_hint": "생각의 성장·결실·정체 점검",
    },
    "SELF_IS_A_CONTAINER": {
        "label": "자아는 그릇",
        "source_markers": ["가득 찼", "비어 있", "넘쳤", "깨졌",
                           "안쪽", "바깥쪽", "구멍"],
        "target": "자아·정체성·정서 그릇",
        "interpretation_hint": "자기 충만·결핍·정체성 균열 신호",
    },
    "TIME_IS_MOVING_OBJECT": {
        "label": "시간은 움직이는 대상",
        "source_markers": ["다가오", "지나갔", "흘러", "쫓아오",
                           "앞당겨", "느려졌"],
        "target": "시간 압박·마감",
        "interpretation_hint": "기한·압박감의 은유",
    },
    "PURPOSES_ARE_DESTINATIONS": {
        "label": "목적은 목적지",
        "source_markers": ["도착하지 못", "헤매", "길을 잃", "도달",
                           "다 왔다", "거의 다"],
        "target": "목표 달성·진로",
        "interpretation_hint": "목표 달성 진행도의 시각화",
    },
    "POWER_IS_PHYSICAL_FORCE": {
        "label": "권력은 물리적 힘",
        "source_markers": ["눌렸", "짓밟", "내리쳤", "휘둘렀",
                           "강압", "압박"],
        "target": "권력 관계·지배·복종",
        "interpretation_hint": "권력 역학의 야간 처리",
    },
    "RELATIONSHIPS_ARE_BONDS": {
        "label": "관계는 결속",
        "source_markers": ["끊어졌", "묶였", "연결", "매듭",
                           "단절", "이어진", "사슬"],
        "target": "인간 관계의 유지·단절",
        "interpretation_hint": "관계의 연결도 점검",
    },
}


def map_metaphors(
    text: str,
    user_target_domain: str | None = None,
) -> dict[str, Any]:
    """꿈 텍스트에서 보편 은유의 근원 영역 신호 추출 + 목표 영역 교차 매핑.

    Args:
        text: 꿈 본문
        user_target_domain: 사용자의 현재 고민 도메인 (예: '연애', '일', '건강')
                            → 매칭 은유 가중치 조정
    """
    t = text or ""

    found_metaphors: list[dict[str, Any]] = []
    for key, meta in UNIVERSAL_METAPHORS.items():
        hits = [m for m in meta["source_markers"] if m in t]
        if hits:
            relevance = 1.0
            # 사용자 목표 도메인과 매칭하면 가중치 ↑
            if user_target_domain and user_target_domain in meta["target"]:
                relevance = 2.0
            found_metaphors.append({
                "metaphor_key": key,
                "label": meta["label"],
                "source_hits": hits,
                "target_domain": meta["target"],
                "interpretation_hint": meta["interpretation_hint"],
                "relevance": relevance,
            })

    # relevance 순 정렬
    found_metaphors.sort(key=lambda m: m["relevance"], reverse=True)

    return {
        "metaphors_detected": found_metaphors,
        "metaphor_count": len(found_metaphors),
        "user_target_domain": user_target_domain,
        "interpretive_note": (
            f"보편 은유 {len(found_metaphors)}개 매핑: "
            f"{', '.join(m['label'] for m in found_metaphors[:3])}. "
            "Lakoff 관점: 꿈의 시나리오는 근원 영역(신체·공간)을 추상 목표로 매핑한 결과."
            if found_metaphors
            else "보편 은유 신호 미감지 — 직접 서사적·일상적 꿈에 가까움."
        ),
        "guidance": (
            "LLM 해석 시: 표면 키워드를 단순 길흉으로 직역하지 말 것. "
            "위 매핑된 근원→목표 구조에 따라 추상 의미를 추출."
        ),
    }


__all__ = [
    "LAKOFF_CMT_LABEL",
    "UNIVERSAL_METAPHORS",
    "map_metaphors",
]
