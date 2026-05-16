"""Social Simulation Theory (SST) — Revonsuo·Tuominen·Valli 사회 시뮬레이션.

출처:
  - Revonsuo, Tuominen, Valli (2015) "The Avatars in the Machine — Dreaming as
    a Simulation of Social Reality", Open MIND

핵심:
  - TST(위협 시뮬레이션)의 후속 — 꿈은 위협뿐 아니라 사회적 상호작용을 시뮬레이션
  - 동맹·결속·유대·갈등을 가상 훈련해 사회 인지 강화
  - 등장인물 종류·관계·상호작용이 핵심 분석 단위

본 모듈의 역할:
  - 등장인물 종류(가족/연인/낯선이/유명인) 분류
  - 상호작용 양식(우호/공격/성/대화) 분석
  - TST와의 분기 (위협 동반 → TST 우선, 평화 → SST)
"""

from __future__ import annotations
from typing import Any


SST_LABEL = (
    "사회 시뮬레이션 (SST) — 꿈은 사회적 상호작용·동맹·결속을 시뮬레이션해 "
    "사회 인지 강화. TST의 후속(Revonsuo 2015)."
)


# 등장인물 카테고리 (HvDC 호환 + 한국 확장)
CHARACTER_CATEGORIES = {
    "self": ["내가", "나는", "스스로"],
    "family": [
        "엄마", "어머니", "아빠", "아버지", "할머니", "할아버지",
        "형", "오빠", "누나", "언니", "동생", "자녀", "아들", "딸",
        "삼촌", "이모", "고모", "사촌", "조카", "가족",
    ],
    "romantic": [
        "남편", "아내", "연인", "남친", "여친", "애인", "남자친구", "여자친구",
        "배우자", "약혼자",
    ],
    "friend": ["친구", "베프", "단짝", "동창", "지인", "선배", "후배"],
    "colleague": ["동료", "상사", "팀장", "부장", "사장", "팀원", "거래처"],
    "stranger": ["낯선 사람", "처음 본", "모르는 사람", "지나가던", "행인", "낯선이"],
    "famous": ["연예인", "스타", "가수", "배우", "유명인", "대통령", "운동선수"],
    "imaginary": ["천사", "악마", "귀신", "신", "유령", "정령", "도깨비", "용", "괴물"],
    "ancestor_deceased": ["조상", "돌아가신", "고인", "할아버지(돌아가심)", "할머니(돌아가심)"],
}


# 상호작용 양식 (HvDC enum 호환)
INTERACTION_TYPES = {
    "friendly": ["대화", "도와줌", "안아줌", "포옹", "키스", "선물", "축하", "함께"],
    "aggressive": ["다툼", "싸움", "공격", "때림", "욕설", "비난", "협박"],
    "sexual": ["성관계", "애무", "유혹", "키스(긴)"],
    "neutral_present": ["옆에 있었", "지나갔", "쳐다봤", "마주쳤"],
    "alliance": ["함께 싸웠", "협력", "동맹", "도움 받음", "구조됨", "보호해줬"],
    "betrayal": ["배신", "거짓말", "속였", "버렸", "배반"],
}


def analyze_social_simulation(
    text: str,
    threat_detected: bool = False,
) -> dict[str, Any]:
    """등장인물·상호작용 추출 + SST 해석.

    Args:
        text: 꿈 본문
        threat_detected: TST 결과로 위협이 감지되었다면 True (분기 안내용)
    """
    t = text or ""

    # 인물 카테고리별 매칭
    chars_by_category: dict[str, list[str]] = {}
    for category, kws in CHARACTER_CATEGORIES.items():
        if category == "self":
            continue
        hits = [k for k in kws if k in t]
        if hits:
            chars_by_category[category] = hits

    # 상호작용
    interactions_by_type: dict[str, list[str]] = {}
    for itype, kws in INTERACTION_TYPES.items():
        hits = [k for k in kws if k in t]
        if hits:
            interactions_by_type[itype] = hits

    total_chars = sum(len(v) for v in chars_by_category.values())
    n_categories = len(chars_by_category)
    has_friendly = bool(interactions_by_type.get("friendly")) or bool(interactions_by_type.get("alliance"))
    has_aggressive = bool(interactions_by_type.get("aggressive")) or bool(interactions_by_type.get("betrayal"))

    # SST vs TST 분기 (Revonsuo 2015 명시)
    if threat_detected and has_aggressive:
        primary = "TST (위협 우선)"
        note = "위협·공격 행위 동반 → 위협 시뮬레이션 가설(TST)이 우선 해석."
    elif has_friendly and not has_aggressive:
        primary = "SST (평화로운 사회 시뮬레이션)"
        note = "평화로운 상호작용·동맹 — 사회적 결속 강화의 야간 리허설."
    elif has_friendly and has_aggressive:
        primary = "SST (혼합 사회 시뮬레이션)"
        note = "갈등과 화해가 공존 — 복잡한 관계 동학의 야간 처리."
    elif total_chars > 0:
        primary = "SST (인물 등장 — 양식 모호)"
        note = "인물은 등장하나 상호작용 양식이 모호. 깨어 있는 삶의 관계 인식 점검."
    else:
        primary = "사회 시뮬레이션 신호 미감지"
        note = "꿈에 인물 등장 거의 없음 — 자기 안의 일과 직면 중일 가능성."

    return {
        "characters_by_category": chars_by_category,
        "total_characters": total_chars,
        "category_diversity": n_categories,
        "interactions": interactions_by_type,
        "has_friendly": has_friendly,
        "has_aggressive": has_aggressive,
        "primary_theory": primary,
        "interpretive_note": note,
        "social_richness_score": min(total_chars + n_categories, 10),
        "revonsuo_principle": (
            "SST는 위협·공격이 없을 때 적용 — 결속·동맹·유대를 사회 인지 강화로 시뮬레이션. "
            "TST(위협)와 SST(사회)는 같은 진화적 적응 가설의 두 갈래."
        ),
    }


__all__ = [
    "SST_LABEL",
    "CHARACTER_CATEGORIES",
    "INTERACTION_TYPES",
    "analyze_social_simulation",
]
