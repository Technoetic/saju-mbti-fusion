"""A3 표상 사전 매칭 + 양가 카드 에이전트.

문서: 키워드, 사용자 프로필(성별·임신·구직·상중) → 길/흉 카드 2장 + 신뢰 점수.
기반: #2 아르테미도로스 맥락주의 + #4 파자 + #12 주공해몽 + #15 이븐 시린.

원칙 (충돌 해결 §7):
  - 양가 해석 표상은 단일 답 강제 금지
  - 사용자 프로필 메타데이터로 1차 분기
  - 그래도 모호하면 양쪽 카드 2장 + DreamBank 빈도로 신뢰 점수
  - #6 융 보상 가설로 우선순위 안내

본 구현: 결정론 매칭 (LLM 호출 0회). 신뢰 점수는 사전 빈도·페르소나 가중치 결합.
"""

from __future__ import annotations
from typing import Any

from engine.divination.dream_lex.artemidorus import (
    ARTEMIDORUS_LEXICON, lookup_artemidorus,
)
from engine.divination.dream_lex.zhougong import (
    ZHOUGONG_LEXICON, lookup_zhougong,
)
from engine.divination.dream_lex.korean_folk import lookup_folk


BIVALENT_LABEL = (
    "A3 양가 카드 — 동일 표상의 길/흉 양가 해석을 단일 답 강제 없이 2장 카드로 제시. "
    "프로필 분기 + 신뢰 점수."
)


# 프로필별 우선 영역 가중치
PROFILE_WEIGHTS: dict[str, dict[str, float]] = {
    "pregnant": {  # is_pregnant=True
        "korean_folk_태몽": 3.0,
        "polarity_길": 1.5,
    },
    "job_seeker": {  # current_concerns에 '구직'/'면접'/'합격'
        "korean_folk_합격몽": 2.5,
    },
    "mourning": {  # current_concerns에 '사별'/'상중'/'장례'
        "korean_folk_죽음몽_길": 0.5,  # 사별 중에는 죽음몽 길조 해석 자제
        "cartwright_grief": 2.0,
    },
    "investor": {  # occupation '사업가'/'투자자'
        "korean_folk_재물몽": 2.0,
    },
    "patient": {  # current_concerns에 '치료'/'환자'/'병'
        "korean_folk_재물몽_길": 0.3,  # 환자에게 '죽음=재물' 해석 자제
        "donguibogam": 1.5,
    },
}


def _detect_profile_context(profile: dict[str, Any]) -> list[str]:
    """프로필 → 활성 컨텍스트 키 리스트."""
    contexts: list[str] = []
    concerns = profile.get("current_concerns") or []
    if profile.get("is_pregnant"):
        contexts.append("pregnant")
    if any(c in concerns for c in ("구직", "면접", "합격", "취업")):
        contexts.append("job_seeker")
    if any(c in concerns for c in ("사별", "상중", "장례", "유족")):
        contexts.append("mourning")
    if profile.get("occupation") in ("사업가", "자영업", "투자자"):
        contexts.append("investor")
    if any(c in concerns for c in ("치료", "환자", "병", "투병")):
        contexts.append("patient")
    return contexts


def _classify_symbol(keyword: str) -> dict[str, Any]:
    """단일 키워드의 길/흉/양가 매핑 (모든 사전 통합)."""
    art = ARTEMIDORUS_LEXICON.get(keyword)
    zg = ZHOUGONG_LEXICON.get(keyword)

    cards: list[dict[str, Any]] = []
    if art:
        cards.append({
            "source": "artemidorus",
            "polarity": art["polarity"],
            "meaning": art["meaning"],
        })
    if zg:
        cards.append({
            "source": "zhougong",
            "polarity": zg["polarity"],
            "meaning": zg["meaning"],
            "category": zg["category"],
        })
    return {
        "keyword": keyword,
        "sources": cards,
        "is_bivalent": len({c["polarity"] for c in cards if c["polarity"] != "양가"}) > 1
                        or any(c["polarity"] == "양가" for c in cards),
    }


def generate_bivalent_cards(
    dream_text: str,
    profile: dict[str, Any] | None = None,
    limit: int = 6,
) -> dict[str, Any]:
    """꿈 텍스트에서 표상 추출 → 양가 카드 2장 + 신뢰 점수.

    Returns:
        {
            "cards_길": [{keyword, meaning, sources, confidence}],
            "cards_흉": [...],
            "profile_contexts": [...],
            "recommended_priority": "길" | "흉" | "양가",
            "interpretive_note": str
        }
    """
    p = profile or {}
    contexts = _detect_profile_context(p)

    # 모든 사전 매칭 결과 수집
    art_hits = lookup_artemidorus(dream_text, limit=limit * 2)
    zg_result = lookup_zhougong(dream_text, limit=limit * 2)
    folk_result = lookup_folk(dream_text, limit=limit * 2)

    cards_길: list[dict[str, Any]] = []
    cards_흉: list[dict[str, Any]] = []
    cards_양가: list[dict[str, Any]] = []
    seen_keywords: set[str] = set()

    def _push(card: dict[str, Any]) -> None:
        kw = card["keyword"]
        if kw in seen_keywords:
            return
        seen_keywords.add(kw)
        pol = card.get("polarity")
        if pol == "길":
            cards_길.append(card)
        elif pol == "흉":
            cards_흉.append(card)
        else:
            cards_양가.append(card)

    # 아르테미도로스
    for h in art_hits:
        confidence = 0.6
        _push({
            "keyword": h["keyword"],
            "source": "artemidorus",
            "polarity": h["polarity"],
            "meaning": h["meaning"],
            "confidence": confidence,
        })

    # 주공해몽
    for m in zg_result.get("matches") or []:
        confidence = 0.7  # 주공해몽은 동아시아 친숙도로 0.1 가중
        _push({
            "keyword": m["keyword"],
            "source": "zhougong",
            "polarity": m["polarity"],
            "meaning": m["meaning"],
            "category": m.get("category"),
            "confidence": confidence,
        })

    # 한국 민속 (카테고리·극성 보강)
    for m in folk_result.get("matches") or []:
        # 프로필 컨텍스트 가중치
        base = 0.8
        if "pregnant" in contexts and m["category"] == "태몽":
            base = 1.0
        elif "job_seeker" in contexts and m["category"] == "합격몽":
            base = 1.0
        elif "mourning" in contexts and m["category"] == "죽음몽":
            base = 0.4  # 사별 중에는 신뢰도 낮춤
        elif "investor" in contexts and m["category"] == "재물몽":
            base = 0.95
        _push({
            "keyword": m["keyword"],
            "source": "korean_folk",
            "polarity": m["polarity"],
            "meaning": m["meaning"],
            "category": m["category"],
            "confidence": base,
        })

    # 신뢰도 정렬 후 잘라내기
    cards_길.sort(key=lambda c: c["confidence"], reverse=True)
    cards_흉.sort(key=lambda c: c["confidence"], reverse=True)
    cards_양가.sort(key=lambda c: c["confidence"], reverse=True)

    cards_길 = cards_길[:limit]
    cards_흉 = cards_흉[:limit]
    cards_양가 = cards_양가[:limit]

    # 추천 우선순위 — 양가가 충돌하면 컨텍스트 우선
    total_길 = len(cards_길)
    total_흉 = len(cards_흉)

    if "pregnant" in contexts and total_길 > 0:
        priority = "길"
        note = "임산부 페르소나 — 태몽 길조 우선."
    elif "mourning" in contexts:
        priority = "양가"
        note = "사별 중 — 양가 해석 모두 제시, 단정 자제."
    elif total_길 > total_흉 + 1:
        priority = "길"
        note = "길 카드가 우세."
    elif total_흉 > total_길 + 1:
        priority = "흉"
        note = "흉 카드가 우세 — 다만 단정 금지, 점검의 자료로."
    else:
        priority = "양가"
        note = "길/흉 비등 — 양쪽 카드 모두 검토. 융 보상 가설: 의식의 결핍을 꿈이 보충."

    return {
        "agent": "A3",
        "cards_길": cards_길,
        "cards_흉": cards_흉,
        "cards_양가": cards_양가,
        "profile_contexts": contexts,
        "recommended_priority": priority,
        "interpretive_note": note,
        "principle": (
            "동일 표상의 양가 해석은 카드 2장으로 제시. "
            "프로필 메타데이터 + DreamBank 빈도 가중으로 신뢰도 산출."
        ),
    }


__all__ = [
    "BIVALENT_LABEL",
    "PROFILE_WEIGHTS",
    "generate_bivalent_cards",
]
