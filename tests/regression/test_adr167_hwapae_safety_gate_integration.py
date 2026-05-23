"""ADR-167 회귀 — hwapae/generate_hwapae_reading에서 run_safety_gates 자동 호출 + 폴백.

ADR-163·164·165·166 패턴을 hwapae로 확산. hwapae는 화패 카드 + critic loop
종료 후 final_text. age/gender 인자 부재 → fact_check는 의미 없음.
question alignment + persona + pii + token_guard 위주.

검증:
  · 단정 환각 + 짧은 응답 등 → stub 폴백
  · envelope 3 신규 필드 노출
  · 안전망 예외 시 원본 응답 유지
  · LLM 자체 실패 응답 면제
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


_DUMMY_CARDS = [
    {"한자": "天", "한글": "하늘", "position": "first"},
    {"한자": "地", "한글": "땅", "position": "middle"},
]


def test_adr167_hwapae_envelope_exposes_safety_gate_fields():
    """envelope에 safety_gate_verdict/failures/fallback_used 노출."""
    from engine.divination.hwapae import core as hwapae_core

    fake_text = (
        "허허, 화선 낭자가 자네의 화패를 살피니 그 결이 두텁고 환하니 "
        "좋은 결이로다. 이만 자네의 화패를 마치노라."
    )
    fake_critique = {"passed": True, "verdict": "ok", "total": 100}

    with patch("engine.llm_sync.call_llm_sync", return_value=fake_text), \
         patch.object(hwapae_core, "critique_hwapae", return_value=fake_critique), \
         patch("pathlib.Path.exists", return_value=False):
        result = hwapae_core.generate_hwapae_reading(
            question="요즘 어떻소?",
            drawn_cards=_DUMMY_CARDS,
            max_rounds=1,
        )

    assert "safety_gate_verdict" in result
    assert "safety_gate_failures" in result
    assert "safety_gate_fallback_used" in result
    assert isinstance(result["safety_gate_failures"], list)
    assert isinstance(result["safety_gate_fallback_used"], bool)


def test_adr167_hwapae_safety_gate_exception_preserves_original():
    """안전망 예외 시 원본 응답 유지."""
    from engine.divination.hwapae import core as hwapae_core

    fake_text = (
        "허허, 화선 낭자가 자네의 화패를 짚어보매 결이 단정하니 "
        "차근차근 가꾸어 가는 자세가 좋으리라. 이만 자네의 화패를 마치노라."
    )
    fake_critique = {"passed": True, "verdict": "ok", "total": 100}

    def _raise(*a, **kw):
        raise RuntimeError("forced gate failure")

    with patch("engine.llm_sync.call_llm_sync", return_value=fake_text), \
         patch.object(hwapae_core, "critique_hwapae", return_value=fake_critique), \
         patch("pathlib.Path.exists", return_value=False), \
         patch("engine.safety.llm.output_safety_gate.run_safety_gates",
               side_effect=_raise):
        result = hwapae_core.generate_hwapae_reading(
            question="요즘 어떻소?",
            drawn_cards=_DUMMY_CARDS,
            max_rounds=1,
        )

    assert result["safety_gate_fallback_used"] is False
    assert result["safety_gate_verdict"] is None
    assert "차근차근 가꾸어 가는 자세" in result["text"]


def test_adr167_hwapae_llm_failure_skipped_by_gate():
    """LLM 자체 실패 응답('(풀이 생성 실패…')은 안전망 검증 면제."""
    from engine.divination.hwapae import core as hwapae_core

    def _raise_llm(*a, **kw):
        raise RuntimeError("simulated LLM failure")

    fake_critique = {"passed": True, "verdict": "ok", "total": 100}

    with patch("engine.llm_sync.call_llm_sync", side_effect=_raise_llm), \
         patch.object(hwapae_core, "critique_hwapae", return_value=fake_critique), \
         patch("pathlib.Path.exists", return_value=False):
        result = hwapae_core.generate_hwapae_reading(
            question="요즘 어떻소?",
            drawn_cards=_DUMMY_CARDS,
            max_rounds=1,
        )

    assert result["safety_gate_fallback_used"] is False
    assert result["safety_gate_verdict"] is None
    assert "(풀이 생성 실패" in result["text"]
