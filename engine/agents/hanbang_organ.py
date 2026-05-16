"""A4 한방 장부 매핑 에이전트 — 결정론 보강 + LLM 진단 톤.

기존 hanbang/eumsabalmong.py·donguibogam.py가 키워드 매칭 결과를 dict로 반환.
본 에이전트는 그 결과를 LLM에게 전달해:
  - "한방 관점에서는 ~의 신호가 보입니다" 톤으로 자연 한 단락 생성
  - 한방 진단 단정 금지 (의료법 #27 회피)
  - 한의원 상담 권고 자동 포함

LLM 호출 0~1회 (한방 매칭 0건이면 LLM 호출 생략).
"""

from __future__ import annotations
from typing import Any

from engine.divination.dream_lex.hanbang.eumsabalmong import map_dream_to_organ
from engine.divination.dream_lex.hanbang.donguibogam import diagnose_honbaek


HANBANG_ORGAN_LABEL = (
    "A4 한방 장부 — 음사발몽·동의보감 결정론 결과를 한방 진단 톤(단정 금지)으로 합성."
)


_HANBANG_SYSTEM = (
    "당신은 한방 꿈 해석 보조 진행자입니다.\n\n"
    "[엄격 규칙]\n"
    "  • '~병이 있습니다' / '~를 앓고 있습니다' 단정 절대 금지 (의료법 제27조)\n"
    "  • '한방 관점에서는 ~의 신호로 읽힐 수 있습니다' 가능성 톤\n"
    "  • 신체 증상 동반 시 '한의원·가정의학과 전문의 상담을 권합니다' 자동 부착\n"
    "  • 약물·치료법 추천 금지\n"
    "  • 200~350자, 한국어 존댓말, 마크다운 없이"
)


def run_hanbang_agent(
    dream_text: str,
    *,
    has_physical_symptoms: bool = False,
) -> dict[str, Any]:
    """결정론 매칭 + LLM 진단 톤 합성."""
    from engine.llm_sync import call_llm_sync

    eumsa = map_dream_to_organ(dream_text, limit=8)
    dongui = diagnose_honbaek(dream_text, limit_patterns=3)

    has_signal = bool(eumsa.get("matched")) or bool(dongui.get("patterns_detected"))

    if not has_signal:
        return {
            "agent": "A4",
            "eumsabalmong": eumsa,
            "donguibogam": dongui,
            "llm_synthesis": None,
            "skip_reason": "한방 신호 미감지 — LLM 호출 생략",
        }

    # LLM 합성 — 결정론 결과를 자연 한 단락으로
    matched_organs = ", ".join(
        f"{m['keyword']}→{m['organ']}({m['pattern']})"
        for m in (eumsa.get("matched") or [])[:5]
    )
    primary_pattern = dongui.get("primary_pattern") or "(특정 패턴 미감지)"
    dongui_note = dongui.get("interpretive_note") or ""

    user_msg = (
        f"[음사발몽 매칭]\n  · 우세 장부: {eumsa.get('dominant_organ')} "
        f"({eumsa.get('dominant_wuxing')})\n"
        f"  · 매칭: {matched_organs}\n\n"
        f"[동의보감 혼백]\n  · 주된 패턴: {primary_pattern}\n  · {dongui_note}\n\n"
        f"[신체 증상 동반 여부] {'예' if has_physical_symptoms else '미확인'}\n\n"
        f"위 한방 매칭 결과를 자연스러운 한 단락으로 풀어주십시오. "
        f"단정 금지, 한방 관점 가능성 톤. "
        f"필요 시 한의원·가정의학과 상담 권고를 자연스럽게 포함."
    )

    try:
        text = call_llm_sync(user_text=user_msg, system_prompt=_HANBANG_SYSTEM)
    except Exception as e:
        text = f"(LLM 합성 실패: {e})"

    return {
        "agent": "A4",
        "eumsabalmong": eumsa,
        "donguibogam": dongui,
        "llm_synthesis": (text or "").strip(),
        "principle": (
            "결정론 매칭 위에 LLM 진단 톤만 입힘. 학습된 한방 지식 사용 금지 — "
            "사실 블록의 매칭 결과만 풀이."
        ),
    }


__all__ = [
    "HANBANG_ORGAN_LABEL",
    "run_hanbang_agent",
]
