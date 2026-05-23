"""ADR-171 — domain_assertion_dict 회귀."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_empty_text_returns_not_detected():
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions("", domain="palm")
    assert r.detected is False
    assert r.matched_terms == []


def test_none_text_safe():
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(None, domain="palm")
    assert r.detected is False


def test_common_assertion_detected_in_face():
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions("그대 장수의 결이 보입니다.", domain="face")
    assert r.detected is True
    assert "장수의 결" in r.matched_terms


def test_palm_specific_assertion_detected():
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(
        "긴 생명선이라 장수하리라.", domain="palm",
    )
    assert r.detected is True


def test_name_specific_assertion_detected():
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(
        "이 이름은 부귀의 결을 갖추고 있도다.", domain="name",
    )
    assert r.detected is True
    assert "이 이름은 부귀의 결" in r.matched_terms


def test_dream_specific_assertion_detected():
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(
        "이 꿈은 길몽이라 큰 재물이 들어오리.", domain="dream",
    )
    assert r.detected is True


def test_hwapae_specific_assertion_detected():
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(
        "이 화패는 큰 재물의 결이 또렷합니다.", domain="hwapae",
    )
    assert r.detected is True


def test_palm_specific_not_in_face_domain():
    """palm 전용 어휘는 face 도메인에서 검출 X."""
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(
        "긴 생명선이라 장수.", domain="face",
    )
    # face 도메인이므로 palm 전용 어휘 사전 X — 공통 어휘만 매칭 가능
    # "장수의 결"·"장수하리"는 공통이므로 본 문장은 검출 X
    palm_specific_matched = [t for t in r.matched_terms
                             if "긴 생명선" in t]
    assert palm_specific_matched == []


def test_negated_assertion_ignored():
    """부정 컨텍스트에 있는 단정은 검출 X."""
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(
        "장수의 결이 보이는 듯하나 그것은 단언할 수 없는 것이라.",
        domain="palm",
    )
    assert r.detected is False


def test_clean_response_passes():
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(
        "허허, 그대 청년의 손금이 두텁고 결이 환하니 좋은 결이로다. "
        "차근차근 가꾸어 가는 자세가 좋은 결을 이루리라.",
        domain="palm",
    )
    assert r.detected is False


def test_domain_none_uses_common_vocab():
    """domain=None이어도 공통 어휘는 검출."""
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(
        "장수의 결이 보입니다.", domain=None,
    )
    assert r.detected is True


def test_unknown_domain_falls_back_to_common():
    """알 수 없는 domain도 공통 어휘 사용."""
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(
        "장수의 결이 보입니다.", domain="some_other",
    )
    assert r.detected is True


# ───── ADR-175 saju 도메인 회귀 ─────

def test_adr175_saju_specific_assertion_detected():
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(
        "이 사주는 대운이 들어오리라.", domain="saju",
    )
    assert r.detected is True


def test_adr175_saju_marriage_timing_assertion_detected():
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(
        "올해 결혼할 사주가 또렷합니다.", domain="saju",
    )
    assert r.detected is True


def test_adr175_saju_clean_passes():
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(
        "사주를 풀어보매 흐름이 단정하고 결이 맑으니 차근차근 가꾸어 가는 자세가 좋으리라.",
        domain="saju",
    )
    assert r.detected is False


def test_adr175_saju_specific_not_in_face():
    """saju 전용 어휘는 face 도메인에서 검출 X."""
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(
        "이 사주는 대운이 들어오리라.", domain="face",
    )
    saju_specific_matched = [t for t in r.matched_terms if "사주" in t]
    assert saju_specific_matched == []


def test_safety_gate_includes_fate_assertion_domain_kwarg():
    """run_safety_gates(domain=...)가 fate_assertion 게이트 활성화."""
    from engine.safety.llm.output_safety_gate import run_safety_gates
    # 페르소나 톤·길이 등 다른 게이트 통과 위해 충분한 응답
    text = (
        "허허, 그대의 상을 짚어보매 이 늙은이가 살피니 긴 생명선이라 "
        "장수하리라 하는 결이 또렷이 보이는도다. 자네의 결이 단정하고 "
        "흐름이 맑으니 차근차근 가꾸어 가는 자세가 좋으리라. 이만 자네의 "
        "손을 마치노라."
    )
    r = run_safety_gates(text, lang="ko", domain="palm")
    assert "fate_assertion_detected" in r.failures


def test_safety_gate_without_domain_skips_fate_check():
    """domain 미전달 시 fate_assertion 게이트 비활성."""
    from engine.safety.llm.output_safety_gate import run_safety_gates
    text = (
        "허허, 그대의 상을 짚어보매 이 늙은이가 살피니 긴 생명선이라 "
        "장수하리라 하는 결이 또렷이 보이는도다. 자네의 결이 단정하고 "
        "흐름이 맑으니 차근차근 가꾸어 가는 자세가 좋으리라. 이만 자네의 "
        "손을 마치노라."
    )
    r = run_safety_gates(text, lang="ko")  # domain 미전달
    assert "fate_assertion_detected" not in r.failures
