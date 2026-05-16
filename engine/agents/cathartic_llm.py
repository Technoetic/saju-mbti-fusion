"""A10 카타르시스 꿈 LLM 미세 분류 — 결정론 위에 LLM 정밀화.

기존 cathartic.py가 3등분 텍스트의 부정/긍정 마커 카운트로 6 카테고리 분류.
본 에이전트는 그 결과 + 본문을 LLM에 보내 더 정밀한 감정 아크 + 임상 신호.

목표: 인간 평가자 일치도 87~100% (Bertolini 2024 카타르시스 연구 수준).
LLM 호출 0~1회 (결정론에서 'unknown'이면 LLM 호출).
"""

from __future__ import annotations
from typing import Any
import json

from engine.divination.dream_lex.cathartic import classify_cathartic_arc


CATHARTIC_LLM_LABEL = (
    "A10 카타르시스 LLM 미세 분류 — 감정 아크 정밀화 + 임상 신호 추출."
)


_CATHARTIC_SYSTEM = (
    "당신은 꿈의 감정 아크(emotional arc) 분류기입니다.\n"
    "본문을 시간순으로 따라가며 감정 변화를 추적하고 JSON으로만 출력하십시오.\n\n"
    "[엄격 규칙]\n"
    "  • 추측 금지 — 본문에 실제 나타난 감정만\n"
    "  • 5 카테고리 중 정확히 하나 선택\n"
    "  • 단정적 임상 진단 금지\n"
    "  • 출력은 valid JSON 1개\n\n"
    "[감정 아크 카테고리]\n"
    "  cathartic         — 초중반 부정 → 결말 긍정/해소 (능동적 처리)\n"
    "  nightmare         — 부정 시작 → 폭력/미해결 결말\n"
    "  unresolved_anxiety— 부정만 지속, 해소 없음\n"
    "  positive          — 전반 긍정\n"
    "  neutral_or_mixed  — 명확한 아크 없음\n\n"
    "[출력 스키마]\n"
    "  {\n"
    '    "arc_type": "cathartic|nightmare|unresolved_anxiety|positive|neutral_or_mixed",\n'
    '    "arc_intensity": 1-5,\n'
    '    "turning_point": "결말 반전이 일어난 지점 본문 인용 (없으면 빈 문자열)",\n'
    '    "dominant_negative_emotion": "fear|sadness|anger|confusion|none",\n'
    '    "dominant_positive_emotion": "relief|joy|peace|none",\n'
    '    "is_cathartic": true|false,\n'
    '    "clinical_signal": "정서 처리·악몽·미해결·정상 등 한 줄 (단정 금지)"\n'
    "  }"
)


def classify_arc_llm(dream_text: str) -> dict[str, Any]:
    """결정론 분류 + LLM 정밀 분류 통합."""
    from engine.llm_sync import call_llm_sync

    determ = classify_cathartic_arc(dream_text)
    determ_arc = determ.get("arc_type")

    # 결정론이 명확하면 LLM 호출 생략
    if determ_arc in ("cathartic", "positive") and (
        not dream_text or len(dream_text.strip()) < 80
    ):
        return {
            "agent": "A10",
            "deterministic": determ,
            "llm_classification": None,
            "final_arc": determ_arc,
            "skip_reason": "결정론 분류가 명확 — LLM 호출 생략",
        }

    if not dream_text or not dream_text.strip():
        return {
            "agent": "A10",
            "deterministic": determ,
            "llm_classification": None,
            "final_arc": "unknown",
        }

    user_msg = (
        f"[꿈 본문]\n{dream_text[:2000]}\n\n"
        f"[결정론 1차 분류] {determ_arc} ({determ.get('arc_label', '?')})\n\n"
        f"위 본문의 감정 아크를 JSON으로 정밀 분류."
    )

    try:
        raw = call_llm_sync(user_text=user_msg, system_prompt=_CATHARTIC_SYSTEM)
    except Exception as e:
        return {
            "agent": "A10",
            "deterministic": determ,
            "llm_classification": None,
            "final_arc": determ_arc,
            "error": f"LLM 호출 실패: {e}",
        }

    cleaned = _strip_codeblock(raw or "")
    try:
        data = json.loads(cleaned)
        llm_class = _normalize(data)
        final_arc = llm_class["arc_type"] or determ_arc
    except json.JSONDecodeError as e:
        llm_class = None
        final_arc = determ_arc

    return {
        "agent": "A10",
        "deterministic": determ,
        "llm_classification": llm_class,
        "final_arc": final_arc,
        "is_cathartic": (llm_class or {}).get("is_cathartic") or determ.get("is_cathartic"),
        "principle": (
            "결정론 분류가 명확하면 LLM 호출 생략. 모호하거나 본문이 길면 LLM 정밀화. "
            "최종 라벨은 LLM 우선, 실패 시 결정론 fallback."
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
    valid_arcs = {"cathartic", "nightmare", "unresolved_anxiety", "positive", "neutral_or_mixed"}
    arc = data.get("arc_type")
    if arc not in valid_arcs:
        arc = "neutral_or_mixed"
    return {
        "arc_type": arc,
        "arc_intensity": min(5, max(1, int(data.get("arc_intensity", 3)))),
        "turning_point": str(data.get("turning_point", ""))[:200],
        "dominant_negative_emotion": str(data.get("dominant_negative_emotion", "none"))[:20],
        "dominant_positive_emotion": str(data.get("dominant_positive_emotion", "none"))[:20],
        "is_cathartic": bool(data.get("is_cathartic")),
        "clinical_signal": str(data.get("clinical_signal", ""))[:200],
    }


__all__ = [
    "CATHARTIC_LLM_LABEL",
    "classify_arc_llm",
]
