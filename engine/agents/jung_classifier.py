"""A5 융 원형 LLM 분류 에이전트 — 결정론 위에 LLM 라벨링.

기존 jung_archetypes.py가 키워드 매칭으로 원형 후보를 카운트.
본 에이전트는 그 후보 + 등장 인물·서사를 LLM에게 전달해:
  - Shadow/Anima/Animus/Self/Persona/모성 중 가장 적합한 1차 원형 라벨
  - 개성화(individuation) 단계 추정 (대면·통합·초월 등)
  - 단정 금지, 다층 가능성 톤

목표 인간 코더 일치도 κ ≥ 0.6 (문서 §11-C).
LLM 호출 0~1회.
"""

from __future__ import annotations
from typing import Any
import json

from engine.divination.dream_lex.jung_archetypes import lookup_archetypes


JUNG_CLASSIFIER_LABEL = (
    "A5 융 원형 LLM 분류 — 결정론 후보 위에 LLM이 1차 원형 + 개성화 단계 라벨."
)


INDIVIDUATION_STAGES = [
    "confrontation_shadow",  # 그림자 직면
    "integration_anima_animus",  # 아니마/아니무스 통합
    "encounter_old_wise",  # 노현자 만남
    "self_realization",  # 자기실현
    "transcendence",  # 초월
    "early_or_unknown",  # 초기/불명
]


_JUNG_SYSTEM = (
    "당신은 융 분석심리의 원형 분류기입니다.\n"
    "입력으로 꿈 요약과 결정론 매칭 후보가 주어지면, JSON으로만 출력하십시오.\n\n"
    "[엄격 규칙]\n"
    "  • 단정 금지 — '~원형의 가능성' 가능성 톤\n"
    "  • 본문에 명시되지 않은 인물·서사 추측 금지\n"
    "  • 성환원·도덕 판단 금지\n"
    "  • 출력은 valid JSON 1개. 마크다운 금지.\n\n"
    "[출력 스키마]\n"
    "  {\n"
    '    "primary_archetype": "shadow|anima|animus|self|persona|mother|child|sage|trickster",\n'
    '    "secondary_archetype": "...",\n'
    '    "confidence": 0.0-1.0,\n'
    '    "individuation_stage": "confrontation_shadow|integration_anima_animus|encounter_old_wise|self_realization|transcendence|early_or_unknown",\n'
    '    "rationale": "왜 이 원형으로 본 두 줄 (한국어 존댓말)",\n'
    '    "compensation_hypothesis": "융 보상 가설 — 의식의 결핍 가능성 한 줄"\n'
    "  }"
)


def classify_archetype(
    dream_text: str,
    *,
    gender: str | None = None,
) -> dict[str, Any]:
    """결정론 후보 → LLM 1차 분류."""
    from engine.llm_sync import call_llm_sync

    determ = lookup_archetypes(dream_text, gender=gender, limit=8)
    candidate_keywords = ", ".join(
        f"{h['keyword']}({h['archetype']})"
        for h in (determ.get("archetype_hits") or [])[:6]
    )
    dominant = determ.get("dominant_archetype") or "(미감지)"
    liminal = determ.get("liminal_spaces") or []
    liminal_str = ", ".join(k["keyword"] for k in liminal[:3])

    if not dream_text or not dream_text.strip():
        return {
            "agent": "A5",
            "deterministic": determ,
            "llm_classification": None,
            "skip_reason": "꿈 본문 없음",
        }

    user_msg = (
        f"[꿈 본문]\n{dream_text[:1500]}\n\n"
        f"[결정론 매칭 후보]\n"
        f"  · 우세 원형: {dominant}\n"
        f"  · 매칭 키워드: {candidate_keywords or '(없음)'}\n"
        f"  · 임계 공간: {liminal_str or '(없음)'}\n"
        f"  · 성별: {gender or 'unknown'}\n\n"
        f"위 후보를 검토하고, 본문 서사를 함께 보아 1차 원형 + 개성화 단계를 JSON으로 분류."
    )

    try:
        raw = call_llm_sync(user_text=user_msg, system_prompt=_JUNG_SYSTEM)
    except Exception as e:
        return {
            "agent": "A5",
            "deterministic": determ,
            "llm_classification": None,
            "error": f"LLM 호출 실패: {e}",
        }

    cleaned = _strip_codeblock(raw or "")
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return {
            "agent": "A5",
            "deterministic": determ,
            "llm_classification": None,
            "parse_error": str(e),
            "raw": (raw or "")[:200],
        }

    return {
        "agent": "A5",
        "deterministic": determ,
        "llm_classification": _normalize(data),
        "principle": (
            "결정론 매칭이 키워드 후보를 제공하고, LLM이 서사 맥락으로 최종 라벨. "
            "결정론과 LLM이 다른 경우 양쪽 모두 제시."
        ),
    }


def _strip_codeblock(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        lines = t.split("\n")
        if len(lines) > 2:
            t = "\n".join(lines[1:-1])
    first = t.find("{")
    last = t.rfind("}")
    if first >= 0 and last > first:
        t = t[first:last + 1]
    return t


def _normalize(data: dict[str, Any]) -> dict[str, Any]:
    valid_arche = {"shadow", "anima", "animus", "self", "persona",
                    "mother", "child", "sage", "trickster"}
    primary = data.get("primary_archetype")
    if primary not in valid_arche:
        primary = None
    secondary = data.get("secondary_archetype")
    if secondary not in valid_arche:
        secondary = None
    stage = data.get("individuation_stage")
    if stage not in INDIVIDUATION_STAGES:
        stage = "early_or_unknown"
    return {
        "primary_archetype": primary,
        "secondary_archetype": secondary,
        "confidence": min(1.0, max(0.0, float(data.get("confidence", 0.5)))),
        "individuation_stage": stage,
        "rationale": str(data.get("rationale", ""))[:400],
        "compensation_hypothesis": str(data.get("compensation_hypothesis", ""))[:300],
    }


__all__ = [
    "JUNG_CLASSIFIER_LABEL",
    "INDIVIDUATION_STAGES",
    "classify_archetype",
]
