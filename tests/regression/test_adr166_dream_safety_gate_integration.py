"""ADR-166 회귀 — dream/interpret_dream에서 run_safety_gates 자동 호출 + 폴백.

ADR-163·164·165 패턴을 dream 도메인으로 확산. dream은 멀티에이전트 14+6
critic loop 종료 후 final_text 단일 응답. PersonalContext.gender 'M'/'F' →
fact_check 인식 'male'/'female' 정규화.

검증:
  · gender_mismatch 시 deterministic stub 폴백
  · 모순 없으면 fact_mismatch 미발생
  · envelope 3 신규 필드 노출
  · 안전망 예외 시 원본 응답 유지
  · LLM 실패 응답("(풀이 생성 실패…")은 안전망 검증 면제 — 원본 보존
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_adr166_dream_gender_mismatch_triggers_fallback():
    """gender='M'인데 LLM이 '따님의 꿈' → fact_mismatch + stub 폴백."""
    from engine.divination import dream as dream_mod
    from engine.divination.dream_lex.personal_context import PersonalContext

    fake_text = (
        "허허, 그대 따님의 꿈을 살피니 결이 두텁고 맑은 결이로다. "
        "이만 자네의 꿈을 마치노라."
    )
    # critic 통과로 첫 라운드 종료
    fake_critique = {"passed": True, "verdict": "ok", "total": 100}

    ctx = PersonalContext(gender="M", age=30)
    with patch("engine.llm_sync.call_llm_sync", return_value=fake_text), \
         patch.object(dream_mod, "critique_dream", return_value=fake_critique), \
         patch("pathlib.Path.exists", return_value=False):
        result = dream_mod.interpret_dream(
            dream_text="용을 타고 하늘을 날았다.",
            personal_context=ctx,
            max_rounds=1,
        )

    assert result["safety_gate_fallback_used"] is True
    assert result["safety_gate_verdict"] in ("warn", "critical")
    assert "fact_mismatch" in result["safety_gate_failures"]
    assert "따님의 꿈" not in result["text"]


def test_adr166_dream_clean_response_no_fact_mismatch():
    """모순 없는 응답 → fact_mismatch 미발생."""
    from engine.divination import dream as dream_mod
    from engine.divination.dream_lex.personal_context import PersonalContext

    fake_text = (
        "허허, 그대 청년의 꿈이 결이 두텁고 환하니 좋은 결이로다. "
        "용을 타고 하늘을 날아오르는 결은 자네의 기상이 펼쳐지는 모습이라. "
        "이 늙은이 자네의 꿈을 짚어보매 흐름이 맑고 단정하니, 차근차근 "
        "자네의 결을 가꾸어 가는 자세가 좋은 결을 이루리라. 꿈의 결이 "
        "두텁고 환하니, 이만 자네의 꿈을 마치노라."
    )
    fake_critique = {"passed": True, "verdict": "ok", "total": 100}

    ctx = PersonalContext(gender="M", age=25)
    with patch("engine.llm_sync.call_llm_sync", return_value=fake_text), \
         patch.object(dream_mod, "critique_dream", return_value=fake_critique), \
         patch("pathlib.Path.exists", return_value=False):
        result = dream_mod.interpret_dream(
            dream_text="용을 타고 하늘을 날았다.",
            personal_context=ctx,
            max_rounds=1,
        )

    assert "fact_mismatch" not in result["safety_gate_failures"]


def test_adr166_dream_envelope_exposes_safety_gate_fields():
    """envelope에 safety_gate_verdict/failures/fallback_used 노출."""
    from engine.divination import dream as dream_mod
    from engine.divination.dream_lex.personal_context import PersonalContext

    fake_text = (
        "허허, 그대 청년의 꿈이 환하니 좋은 결이로다. "
        "이만 자네의 꿈을 마치노라."
    )
    fake_critique = {"passed": True, "verdict": "ok", "total": 100}

    ctx = PersonalContext(gender="M", age=25)
    with patch("engine.llm_sync.call_llm_sync", return_value=fake_text), \
         patch.object(dream_mod, "critique_dream", return_value=fake_critique), \
         patch("pathlib.Path.exists", return_value=False):
        result = dream_mod.interpret_dream(
            dream_text="용을 봤다.",
            personal_context=ctx,
            max_rounds=1,
        )

    assert "safety_gate_verdict" in result
    assert "safety_gate_failures" in result
    assert "safety_gate_fallback_used" in result
    assert isinstance(result["safety_gate_failures"], list)
    assert isinstance(result["safety_gate_fallback_used"], bool)


def test_adr166_dream_safety_gate_exception_preserves_original():
    """안전망 예외 시 원본 응답 유지."""
    from engine.divination import dream as dream_mod
    from engine.divination.dream_lex.personal_context import PersonalContext

    fake_text = "허허, 청년의 꿈이로다. 이만 자네의 꿈을 마치노라."
    fake_critique = {"passed": True, "verdict": "ok", "total": 100}

    def _raise(*a, **kw):
        raise RuntimeError("forced gate failure")

    ctx = PersonalContext(gender="M", age=25)
    with patch("engine.llm_sync.call_llm_sync", return_value=fake_text), \
         patch.object(dream_mod, "critique_dream", return_value=fake_critique), \
         patch("pathlib.Path.exists", return_value=False), \
         patch("engine.safety.llm.output_safety_gate.run_safety_gates",
               side_effect=_raise):
        result = dream_mod.interpret_dream(
            dream_text="용을 봤다.",
            personal_context=ctx,
            max_rounds=1,
        )

    assert result["safety_gate_fallback_used"] is False
    assert result["safety_gate_verdict"] is None
    assert "청년의 꿈이로다" in result["text"]


def test_adr166_dream_llm_failure_skipped_by_gate():
    """LLM 자체 실패 응답('(풀이 생성 실패…')은 안전망 검증 면제."""
    from engine.divination import dream as dream_mod
    from engine.divination.dream_lex.personal_context import PersonalContext

    # call_llm_sync가 예외 → final_text = "(풀이 생성 실패: …)"
    def _raise_llm(*a, **kw):
        raise RuntimeError("simulated LLM failure")

    fake_critique = {"passed": True, "verdict": "ok", "total": 100}

    ctx = PersonalContext(gender="M", age=25)
    with patch("engine.llm_sync.call_llm_sync", side_effect=_raise_llm), \
         patch.object(dream_mod, "critique_dream", return_value=fake_critique), \
         patch("pathlib.Path.exists", return_value=False):
        result = dream_mod.interpret_dream(
            dream_text="용을 봤다.",
            personal_context=ctx,
            max_rounds=1,
        )

    # LLM 실패 메시지는 안전망 검증 X (verdict None) — 원본 그대로 노출
    assert result["safety_gate_fallback_used"] is False
    assert result["safety_gate_verdict"] is None
    assert "(풀이 생성 실패" in result["text"]
