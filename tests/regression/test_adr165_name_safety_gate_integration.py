"""ADR-165 회귀 — name/reading.py에서 run_safety_gates 자동 호출 + 폴백 검증.

ADR-163·164 패턴을 name 도메인으로 확산. name은 텍스트 입력 단독(Vision X) +
age·metrics 인자 부재. fact_check는 gender만 의미 + alignment + persona +
pii + token_guard 작동.

검증:
  · gender_mismatch 시 deterministic stub 폴백
  · 모순 없으면 원본 응답 유지
  · envelope 3 신규 필드 노출
  · 안전망 예외 → 원본 응답 유지
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_adr165_name_gender_mismatch_triggers_fallback():
    """gender=female인데 LLM이 '사내아이의 이름' → fact_mismatch + stub 폴백."""
    from engine.divination.name import reading as name_reading

    fake_text = (
        "묵향 선생이 살피니, 이 이름은 사내아이의 결이 두텁고 환하니 좋은 결이로다. "
        "이만 자네의 이름을 마치노라."
    )
    with patch.object(name_reading, "_call_llm", return_value=fake_text), \
         patch.object(name_reading, "_load_cache", return_value=None), \
         patch.object(name_reading, "_save_cache"):
        out = name_reading.generate_name_reading(
            fullname_ko="김영희",
            gender="female",
        )

    assert out["safety_gate_fallback_used"] is True
    assert out["safety_gate_verdict"] in ("warn", "critical")
    assert "fact_mismatch" in out["safety_gate_failures"]
    assert "사내아이의 결" not in out["text"]


def test_adr165_name_clean_response_no_fallback():
    """모순 없는 응답 → palace_score_mismatch 또는 fact_mismatch 폴백 X.

    페르소나 톤·길이 미달 등 다른 게이트로 인한 폴백은 본 테스트 범위 밖
    (운영 LLM 실 응답은 충분 길이·페르소나 톤 보장). 본 ADR 핵심은
    fact_mismatch 미발생 검증.
    """
    from engine.divination.name import reading as name_reading

    fake_text = (
        "허허, 묵향 선생이 자네의 이름을 살피니 그 결이 두텁고 환하니 좋은 결이로다. "
        "이름의 음과 양이 고르게 어우러지고, 자획의 흐름이 맑게 이어지니 "
        "맑은 결이라 하겠네. 따님의 이름이 결이 곱고 단정하니, 이 늙은이 "
        "자네의 이름을 짚어보매 정성스러운 결이 묻어 있음이로다. 이름의 결이 "
        "단정하니, 차근차근 가꾸어 가는 자세가 좋은 결을 이루리라. "
        "이만 자네의 이름을 마치노라."
    )
    with patch.object(name_reading, "_call_llm", return_value=fake_text), \
         patch.object(name_reading, "_load_cache", return_value=None), \
         patch.object(name_reading, "_save_cache"):
        out = name_reading.generate_name_reading(
            fullname_ko="김영희",
            gender="female",
        )

    # 핵심 검증: fact_mismatch 미발생 (gender·age 등 단정 환각 부재)
    assert "fact_mismatch" not in out["safety_gate_failures"]


def test_adr165_name_envelope_exposes_safety_gate_fields():
    """envelope에 safety_gate_verdict/failures/fallback_used 노출."""
    from engine.divination.name import reading as name_reading

    fake_text = (
        "묵향 선생이 살피니, 이 이름의 결이 환하니 좋은 결이로다. "
        "이만 자네의 이름을 마치노라."
    )
    with patch.object(name_reading, "_call_llm", return_value=fake_text), \
         patch.object(name_reading, "_load_cache", return_value=None), \
         patch.object(name_reading, "_save_cache"):
        out = name_reading.generate_name_reading(fullname_ko="홍길동")

    assert "safety_gate_verdict" in out
    assert "safety_gate_failures" in out
    assert "safety_gate_fallback_used" in out
    assert isinstance(out["safety_gate_failures"], list)
    assert isinstance(out["safety_gate_fallback_used"], bool)


def test_adr165_name_safety_gate_exception_preserves_original():
    """안전망 예외 시 원본 응답 유지."""
    from engine.divination.name import reading as name_reading

    fake_text = (
        "묵향 선생이 살피니, 이 이름의 결이로다. 이만 자네의 이름을 마치노라."
    )

    def _raise(*a, **kw):
        raise RuntimeError("forced gate failure")

    with patch.object(name_reading, "_call_llm", return_value=fake_text), \
         patch.object(name_reading, "_load_cache", return_value=None), \
         patch.object(name_reading, "_save_cache"), \
         patch("engine.safety.llm.output_safety_gate.run_safety_gates",
               side_effect=_raise):
        out = name_reading.generate_name_reading(fullname_ko="홍길동")

    assert out["safety_gate_fallback_used"] is False
    assert out["safety_gate_verdict"] is None
    assert "이 이름의 결이로다" in out["text"]
