"""Montague Ullman 그룹 꿈 분석 (Experiential Group Dream Work).

출처:
  - Ullman & Zimmerman (1979) Working with Dreams
  - Ullman (1996) Appreciating Dreams: A Group Approach

핵심:
  - 그룹 구성원이 "이 꿈이 만약 내 꿈이라면(If this were my dream)"이라는
    가정 하에 자신의 상상력·은유를 자유 투사
  - 꿈은 더 이상 개인의 소유가 아니라 집단 지성의 대상
  - 꿈꾼 사람의 방어 기제 자극을 피하면서 다각적 통찰 도출

본 모듈:
  - LLM이 N개의 가상 페르소나(다양한 배경)로 분기하여 각각의 투사 생성
  - 사용자에게 N개 관점을 동시 제공 (선택권은 사용자)
  - 단일 정답 강제 회피 — 해석의 다양성을 적극 노출
"""

from __future__ import annotations
from typing import Any


ULLMAN_LABEL = (
    "Ullman 그룹 꿈 분석 — '이 꿈이 내 꿈이라면' 가정 하의 다각적 투사. "
    "단일 정답이 아닌 N개 관점의 동시 제시."
)


# 가상 페르소나 — 다양한 배경의 '그룹 구성원'을 LLM이 연기
DEFAULT_PERSONAS_KO = [
    {
        "key": "elder_woman",
        "name": "60대 어머니 화자",
        "lens": "삶을 오래 산 어머니의 시각 — 가족·돌봄·세대 전수의 맥락",
    },
    {
        "key": "young_artist",
        "name": "20대 예술가 화자",
        "lens": "상징·미적 직관·창조성의 맥락 — 표현의 자유와 갈망",
    },
    {
        "key": "doctor",
        "name": "40대 의사 화자",
        "lens": "신체·정신 건강 신호의 맥락 — 신체화·수면·스트레스 신호",
    },
    {
        "key": "monk",
        "name": "수행자 화자",
        "lens": "내면·집착·놓아둠의 맥락 — 자아의 환영성·연기 관점",
    },
    {
        "key": "philosopher",
        "name": "철학자 화자",
        "lens": "의미·존재·자유의 맥락 — 실존적 질문으로의 환원",
    },
]


# LLM이 페르소나별 투사 생성 시 사용할 시스템 프롬프트
ULLMAN_SYSTEM_KO = (
    "당신은 Ullman의 그룹 꿈 분석에 참여한 한 구성원입니다.\n\n"
    "[엄격한 규칙 — Ullman 원칙]\n"
    "  1. 결코 '이 꿈은 ~을 의미합니다'라고 단정하지 마십시오.\n"
    "  2. 반드시 '만약 이 꿈이 제 꿈이라면, 저는 ~을 떠올립니다' 라고 1인칭 가정으로 시작.\n"
    "  3. 자신의 페르소나 렌즈를 통한 투사만 말하고, 꿈꾼 이의 정답을 강요하지 말 것.\n"
    "  4. 200~350자, 자연 문장, 마크다운 없이.\n"
    "  5. 의료·법률·투자 자문 금지. 정신건강 단정 금지.\n"
)


def build_ullman_session(
    dream_text: str,
    personas: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Ullman 세션 양식 — 사용자 꿈 + N개 페르소나 + 각 LLM 프롬프트 생성.

    실제 LLM 호출은 web/server.py 엔드포인트에서 비동기로.
    """
    text = (dream_text or "").strip()
    if not text:
        return {
            "error": "꿈 본문이 비어 있습니다.",
            "ready": False,
        }

    use_personas = personas or DEFAULT_PERSONAS_KO

    prompts: list[dict[str, str]] = []
    for p in use_personas:
        user_msg = (
            f"[꿈 본문]\n{text[:1500]}\n\n"
            f"[당신의 페르소나]\n  · {p['name']}\n  · 렌즈: {p['lens']}\n\n"
            f"위 페르소나의 렌즈로, '만약 이 꿈이 제 꿈이라면' 형식으로 "
            f"투사 한 단락을 작성하십시오."
        )
        prompts.append({
            "persona_key": p["key"],
            "persona_name": p["name"],
            "user_message": user_msg,
        })

    return {
        "ready": True,
        "dream_text": text,
        "system_prompt": ULLMAN_SYSTEM_KO,
        "persona_prompts": prompts,
        "persona_count": len(prompts),
        "guidance": (
            "각 페르소나가 독립적으로 투사를 생성합니다. "
            "단일 정답을 찾기보다, 자신과 가장 공명하는 한 두 투사를 선택해 보세요."
        ),
        "ullman_principle": (
            "꿈꾼 사람이 자신의 꿈에 대한 최종 권위자입니다. "
            "타인의 투사는 자료일 뿐, 진실은 본인이 가장 잘 압니다."
        ),
    }


def aggregate_persona_projections(
    projections: list[dict[str, str]],
) -> dict[str, Any]:
    """N개 페르소나 투사 결과 집계 — 공통 모티프·차이점 추출.

    각 projection: {persona_key, persona_name, text}
    """
    if not projections:
        return {"common_themes": [], "divergent_views": [], "note": "투사 없음."}

    # 단순 어휘 기반 공통/차이 추출 (LLM 추가 호출 없이 결정론)
    all_words = []
    per_persona_words: dict[str, set[str]] = {}
    for p in projections:
        text = p.get("text", "")
        # 길이 2 이상 한글 어절 추출
        words = {w.strip(".,!?;:()[]\"'") for w in text.split() if len(w.strip()) >= 2}
        per_persona_words[p.get("persona_key", "?")] = words
        all_words.extend(words)

    from collections import Counter
    counter = Counter(all_words)
    common = [w for w, n in counter.most_common(10) if n >= 2]

    # 페르소나별 고유어 (다른 페르소나에 없는 단어)
    divergent: dict[str, list[str]] = {}
    for key, words in per_persona_words.items():
        others = set()
        for k, w in per_persona_words.items():
            if k != key:
                others |= w
        unique = list(words - others)[:5]
        if unique:
            divergent[key] = unique

    return {
        "projection_count": len(projections),
        "common_themes": common,
        "divergent_views_by_persona": divergent,
        "interpretive_note": (
            f"{len(projections)}개 페르소나가 공통으로 짚은 모티프 {len(common)}개. "
            f"공명하는 관점을 사용자가 선택해 자기 해석으로 통합하십시오."
        ),
    }


__all__ = [
    "ULLMAN_LABEL",
    "DEFAULT_PERSONAS_KO",
    "ULLMAN_SYSTEM_KO",
    "build_ullman_session",
    "aggregate_persona_projections",
]
