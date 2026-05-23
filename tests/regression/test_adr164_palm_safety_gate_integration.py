"""ADR-164 회귀 — palm/reading.py에서 run_safety_gates 자동 호출 + 폴백 검증.

ADR-163 의 face 패턴을 palm 도메인으로 확산. palm은 결정론 점수가 reading
본문에 산출되지 않으므로 palace_scores=None — fact_check 5 차원(age·gender·
face_count·region·gaze) + alignment + persona + pii + token_guard만 작동.

검증:
  · gender_mismatch 시 deterministic stub 폴백
  · 모순 없으면 원본 응답 유지
  · envelope 3 신규 필드 노출
  · 안전망 자체 예외 → 원본 응답 유지 (회귀 보호)
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


_DUMMY_IMAGE_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7w"
    "AAAABJRU5ErkJggg=="
)


def test_adr164_palm_gender_mismatch_triggers_fallback():
    """gender=male인데 LLM이 '따님의 손금' → fact_mismatch + stub 폴백."""
    from engine.divination.palm import reading as palm_reading

    fake_text = (
        "허허, 그대 따님의 손금이 두텁고 결이 환하니 좋은 결이로다. "
        "이 늙은이 이만 자네의 손을 마치노라."
    )
    with patch.object(palm_reading, "_call_vision", return_value=fake_text), \
         patch.object(palm_reading, "_load_cache", return_value=None), \
         patch.object(palm_reading, "_save_cache"):
        out = palm_reading.generate_palm_reading(
            image_b64=_DUMMY_IMAGE_B64,
            age=30,
            gender="male",
            hand="right",
        )

    assert out["safety_gate_fallback_used"] is True
    assert out["safety_gate_verdict"] in ("warn", "critical")
    assert "fact_mismatch" in out["safety_gate_failures"]
    assert "따님의 손금" not in out["text"]


def test_adr164_palm_clean_response_no_fallback():
    """모순 없는 응답 → 폴백 X."""
    from engine.divination.palm import reading as palm_reading

    fake_text = (
        "허허, 그대 청년의 손금이 두텁고 결이 환하니 좋은 결이로다. "
        "이 늙은이 이만 자네의 손을 마치노라."
    )
    with patch.object(palm_reading, "_call_vision", return_value=fake_text), \
         patch.object(palm_reading, "_load_cache", return_value=None), \
         patch.object(palm_reading, "_save_cache"):
        out = palm_reading.generate_palm_reading(
            image_b64=_DUMMY_IMAGE_B64,
            age=30,
            gender="male",
            hand="right",
        )

    assert out["safety_gate_fallback_used"] is False
    assert "청년의 손금" in out["text"]


def test_adr164_palm_envelope_exposes_safety_gate_fields():
    """envelope에 safety_gate_verdict/failures/fallback_used 노출."""
    from engine.divination.palm import reading as palm_reading

    fake_text = (
        "허허, 그대 청년의 손금이 환하니 좋은 결이로다. "
        "이 늙은이 이만 자네의 손을 마치노라."
    )
    with patch.object(palm_reading, "_call_vision", return_value=fake_text), \
         patch.object(palm_reading, "_load_cache", return_value=None), \
         patch.object(palm_reading, "_save_cache"):
        out = palm_reading.generate_palm_reading(
            image_b64=_DUMMY_IMAGE_B64,
            age=30,
            gender="male",
        )

    assert "safety_gate_verdict" in out
    assert "safety_gate_failures" in out
    assert "safety_gate_fallback_used" in out
    assert isinstance(out["safety_gate_failures"], list)
    assert isinstance(out["safety_gate_fallback_used"], bool)


def test_adr164_palm_safety_gate_exception_preserves_original():
    """안전망 예외 시 원본 응답 유지."""
    from engine.divination.palm import reading as palm_reading

    fake_text = (
        "허허, 청년의 손금이로다. 이 늙은이 이만 자네의 손을 마치노라."
    )

    def _raise(*a, **kw):
        raise RuntimeError("forced gate failure")

    with patch.object(palm_reading, "_call_vision", return_value=fake_text), \
         patch.object(palm_reading, "_load_cache", return_value=None), \
         patch.object(palm_reading, "_save_cache"), \
         patch("engine.safety.llm.output_safety_gate.run_safety_gates",
               side_effect=_raise):
        out = palm_reading.generate_palm_reading(
            image_b64=_DUMMY_IMAGE_B64,
            age=30,
        )

    assert out["safety_gate_fallback_used"] is False
    assert out["safety_gate_verdict"] is None
    assert "청년의 손금이로다" in out["text"]
