"""ADR-187/188 - 문장 경계 윈도우 + 보수적 어휘 확장 회귀."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ───── ADR-187 부정 컨텍스트 문장 경계 회귀 ─────

def test_adr187_negation_within_same_sentence_blocked():
    """같은 문장 내 부정 마커 → 위반 아님 (이전 ±25자도 작동)."""
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(
        "장수의 결이 보이는 듯하나 그것은 단언할 수 없는 것이라.",
        domain="palm",
    )
    assert r.detected is False


def test_adr187_negation_in_different_sentence_not_applied():
    """다른 문장의 부정 마커는 무시 — 이전 ±25자에서 잘못 매칭하던 케이스."""
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    # 같은 문장에 부정 없음 → 다음 문장의 단언할 수 없는 영향 X
    r = detect_fate_assertions(
        "그대는 장수의 결을 갖추고 있도다. 이는 단언할 수 없는 일반론이 아니다.",
        domain="palm",
    )
    # "장수의 결" 문장에는 부정 없음 → 위반
    assert r.detected is True


def test_adr187_long_sentence_safety_margin():
    """매우 긴 문장에서도 안전 마진(60자) 작동."""
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    # 문장 종결 부호 없는 매우 긴 텍스트 (안전 마진 폴백)
    long_text = "장수의 결이 보이는 듯하나 " + "또한 " * 30 + "단언할 수는 없도다"
    r = detect_fate_assertions(long_text, domain="palm")
    # 60자 마진을 넘어선 부정 마커는 미감지 → 위반으로 판정 (보수적)
    assert r.detected is True


def test_adr187_response_fact_check_sentence_window():
    """ADR-187 response_fact_check도 문장 경계 적용."""
    from engine.safety.llm.response_fact_check import _is_negated
    # 같은 문장 내 부정
    assert _is_negated("따님이 아니라 청년의 결이다.", "따님") is True
    # 다른 문장 부정 → 영향 X
    assert _is_negated("따님의 결이다. 청년이 아니라 노년이다.", "따님") is False


# ───── ADR-188 보수적 어휘 확장 회귀 ─────

def test_adr188_must_be_rich_blocked():
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(
        "이 사주를 보니 반드시 부자가 되리라.", domain="saju",
    )
    assert r.detected is True


def test_adr188_inevitable_success_blocked():
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(
        "그대 틀림없이 성공할 것이로다.", domain="face",
    )
    assert r.detected is True


def test_adr188_predetermined_fate_blocked():
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(
        "운명이 정해진 자라 하겠노라.", domain="dream",
    )
    assert r.detected is True


def test_adr188_inescapable_fate_blocked():
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(
        "이는 피할 수 없는 운명이로다.", domain="hwapae",
    )
    assert r.detected is True


def test_adr188_negated_must_passes():
    """ADR-187 결합 — 보수적 어휘도 같은 문장 부정 컨텍스트에서 통과."""
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(
        "반드시 부자가 된다는 것은 단언할 수 없는 일이로다.",
        domain="saju",
    )
    assert r.detected is False
