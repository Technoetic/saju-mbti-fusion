"""동의보감 신문(神門) 몽편 — 혼백 동요·장부 허실 진단.

출처: 許浚 『東醫寶鑑』 內景篇 卷一 神門 (夢條), 1613

핵심 원리:
  - 心藏神 / 肝藏魂 / 肺藏魄 / 脾藏意 / 腎藏志
  - 꿈은 혼백의 동요 → 어느 장부가 허·실인지 판단

음사발몽이 邪氣 침입 결과라면, 동의보감은 본기(本氣)의 허실 — 보다 만성적·체질적.
"""

from __future__ import annotations
from typing import Any


DONGUI_LABEL = (
    "동의보감 신문 몽편 — 꿈은 혼백(魂魄)의 동요와 장부 허실의 신호. "
    "급성 邪氣(음사발몽)와 달리 만성·체질적 신호 위주."
)


# 혼백 매핑
HONBAEK_MAPPING = {
    "心": {"shin": "神 (정신)", "imbalance": "심신불안", "symptom": "꿈이 잦고 잘 잊음"},
    "肝": {"shin": "魂 (혼)", "imbalance": "혼불수사", "symptom": "악몽·놀라는 꿈"},
    "肺": {"shin": "魄 (백)", "imbalance": "백불안", "symptom": "비통하고 우는 꿈"},
    "脾": {"shin": "意 (의)", "imbalance": "비기허", "symptom": "잡몽·기억 흐림"},
    "腎": {"shin": "志 (지)", "imbalance": "신정부족", "symptom": "공포·물·낙하의 꿈"},
}


# 혼백 동요 패턴 — 다중 키워드로 패턴 매칭
DONGUI_HONBAEK_PATTERNS: dict[str, dict[str, Any]] = {
    "혼불수사": {
        "korean": "혼이 자리를 못 지킴 — 간허·혼불안",
        "organ": "肝",
        "shin": "魂",
        "triggers": ["악몽", "가위눌림", "놀라 깸", "비명", "쫓김", "쫓김 꿈"],
        "note": "간혈허(肝血虛)에 잘 동반. 충분한 휴식·녹색 채소·신맛 보충.",
    },
    "심신불안": {
        "korean": "심신이 불안 — 심기허·신지불안",
        "organ": "心",
        "shin": "神",
        "triggers": ["꿈이 많", "잡몽", "잘 잊", "건망", "심장 두근", "가슴 두근"],
        "note": "심혈허(心血虛)에 잘 동반. 대추·용안육·연자육 등 안신 식품.",
    },
    "백불안": {
        "korean": "백이 불안 — 폐기허·금기 부족",
        "organ": "肺",
        "shin": "魄",
        "triggers": ["우는 꿈", "비통한 꿈", "한숨", "기침", "숨막힘", "흰 옷"],
        "note": "폐기허에 잘 동반. 맥문동·도라지·배 등 윤폐 식품.",
    },
    "비기허": {
        "korean": "비기 허약 — 잡몽·기억 흐림",
        "organ": "脾",
        "shin": "意",
        "triggers": ["꿈 기억 안", "잡몽", "몸 무거움", "식욕 없", "소화 안 됨"],
        "note": "비위허에 잘 동반. 마·인삼·대추 등 보비 식품.",
    },
    "신정부족": {
        "korean": "신정 부족 — 공포·수액 동요",
        "organ": "腎",
        "shin": "志",
        "triggers": ["물에 빠짐", "익사", "추락", "공포", "허리 시림", "다리 시림", "이빨 빠짐"],
        "note": "신음·신양 양허에 동반. 흑임자·구기자·검은콩 등 보신 식품.",
    },
}


def diagnose_honbaek(text: str, limit_patterns: int = 3) -> dict[str, Any]:
    """꿈 텍스트에서 혼백 동요 패턴 진단."""
    t = text or ""
    matches: list[dict[str, Any]] = []

    for pattern_name, data in DONGUI_HONBAEK_PATTERNS.items():
        hits = [k for k in data["triggers"] if k in t]
        if hits:
            matches.append({
                "pattern": pattern_name,
                "korean": data["korean"],
                "organ": data["organ"],
                "shin": data["shin"],
                "matched_triggers": hits,
                "trigger_count": len(hits),
                "note": data["note"],
            })

    matches.sort(key=lambda x: x["trigger_count"], reverse=True)
    matches = matches[:limit_patterns]

    primary = matches[0] if matches else None

    return {
        "patterns_detected": matches,
        "primary_pattern": primary["pattern"] if primary else None,
        "primary_organ": primary["organ"] if primary else None,
        "primary_shin": primary["shin"] if primary else None,
        "interpretive_note": (
            f"동의보감 관점: 주된 동요는 '{primary['korean']}' — "
            f"{primary['organ']}({primary['shin']}). {primary['note']}"
            if primary
            else "특정 혼백 동요 패턴 미감지."
        ),
        "disclaimer": (
            "본 진단은 전통 한방 문헌의 패턴 매칭이며 의학적 진단이 아닙니다. "
            "신체 증상이 동반된다면 한의원 또는 가정의학과 상담을 권합니다."
        ),
    }


__all__ = [
    "DONGUI_LABEL",
    "HONBAEK_MAPPING",
    "DONGUI_HONBAEK_PATTERNS",
    "diagnose_honbaek",
]
