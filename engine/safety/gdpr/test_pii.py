"""engine.safety.gdpr.pii — §7.3.4.1 PII 마스킹기 단위 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── mask_pii ───────────────────────────

def test_mask_pii_email_basic():
    from engine.safety.gdpr.pii import mask_pii
    assert mask_pii("문의 hello@example.com") == "문의 [EMAIL]"


def test_mask_pii_email_dots_plus_dash():
    from engine.safety.gdpr.pii import mask_pii
    assert mask_pii("user.name+tag@sub-domain.co.kr") == "[EMAIL]"


def test_mask_pii_phone_dash():
    from engine.safety.gdpr.pii import mask_pii
    assert mask_pii("010-1234-5678로 연락") == "[PHONE]로 연락"


def test_mask_pii_phone_no_dash():
    from engine.safety.gdpr.pii import mask_pii
    assert mask_pii("01012345678") == "[PHONE]"


def test_mask_pii_phone_landline():
    from engine.safety.gdpr.pii import mask_pii
    assert mask_pii("02-123-4567") == "[PHONE]"
    assert mask_pii("031-1234-5678") == "[PHONE]"


def test_mask_pii_rrn():
    from engine.safety.gdpr.pii import mask_pii
    assert mask_pii("주민 900101-1234567 확인") == "주민 [RRN] 확인"


def test_mask_pii_combined():
    from engine.safety.gdpr.pii import mask_pii
    raw = "고객 hello@x.com / 010-1111-2222 / 900101-1234567"
    out = mask_pii(raw)
    assert out == "고객 [EMAIL] / [PHONE] / [RRN]"


def test_mask_pii_empty_and_none():
    from engine.safety.gdpr.pii import mask_pii
    assert mask_pii("") == ""
    assert mask_pii(None) == ""  # type: ignore[arg-type]


def test_mask_pii_no_match_passthrough():
    """일반 텍스트는 그대로 (과탐 방지)."""
    from engine.safety.gdpr.pii import mask_pii
    assert mask_pii("그대의 상이 잘 잡혀 있구먼.") == "그대의 상이 잘 잡혀 있구먼."


def test_mask_pii_no_overmatch_digits():
    """이어붙은 숫자열은 전화로 인식하지 말 것."""
    from engine.safety.gdpr.pii import mask_pii
    # 010 + 더 긴 숫자 → 전화 매칭 안 됨 (자릿수 초과)
    assert mask_pii("010123456789012") != "[PHONE]"


# ─────────────────────────── hash_uid ───────────────────────────

def test_hash_uid_deterministic():
    from engine.safety.gdpr.pii import hash_uid
    assert hash_uid("user-123") == hash_uid("user-123")
    assert len(hash_uid("user-123")) == 8


def test_hash_uid_different_inputs_different_outputs():
    from engine.safety.gdpr.pii import hash_uid
    assert hash_uid("user-A") != hash_uid("user-B")


def test_hash_uid_custom_length():
    from engine.safety.gdpr.pii import hash_uid
    assert len(hash_uid("user", length=16)) == 16
    assert len(hash_uid("user", length=4)) == 4


def test_hash_uid_empty():
    from engine.safety.gdpr.pii import hash_uid
    assert hash_uid("") == ""
    assert hash_uid(None) == ""  # type: ignore[arg-type]


# ─────────────────────────── hash_question ───────────────────────────

def test_hash_question_deterministic():
    from engine.safety.gdpr.pii import hash_question
    h1 = hash_question("올해 운이 어떨까요")
    h2 = hash_question("올해 운이 어떨까요")
    assert h1 == h2 and len(h1) == 8


def test_hash_question_different_inputs():
    from engine.safety.gdpr.pii import hash_question
    assert hash_question("질문 A") != hash_question("질문 B")


def test_hash_question_empty():
    from engine.safety.gdpr.pii import hash_question
    assert hash_question("") == ""
    assert hash_question(None) == ""  # type: ignore[arg-type]


# ─────────────────────────── mask_crisis_keyword ───────────────────────────

def test_mask_crisis_keyword_long():
    """긴 키워드는 앞 4자 + [...]"""
    from engine.safety.gdpr.pii import mask_crisis_keyword
    assert mask_crisis_keyword("자살하고싶어") == "자살하고[...]"


def test_mask_crisis_keyword_short():
    """4자 이하면 전체 + [...]"""
    from engine.safety.gdpr.pii import mask_crisis_keyword
    assert mask_crisis_keyword("죽다") == "죽다[...]"


def test_mask_crisis_keyword_empty():
    from engine.safety.gdpr.pii import mask_crisis_keyword
    assert mask_crisis_keyword("") == ""


def test_mask_crisis_keyword_custom_prefix():
    from engine.safety.gdpr.pii import mask_crisis_keyword
    assert mask_crisis_keyword("자살하고싶어", prefix_len=2) == "자살[...]"


# ─────────────────────────── 패키지 노출 확인 ───────────────────────────

def test_engine_safety_exports_pii():
    """engine.safety 패키지에서 PII 함수가 노출되는지 (운영표준 §7.3.4.1)."""
    import engine.safety as safety
    assert hasattr(safety, "mask_pii")
    assert hasattr(safety, "hash_uid")
    assert hasattr(safety, "hash_question")
    assert hasattr(safety, "mask_crisis_keyword")
