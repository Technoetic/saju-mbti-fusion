"""engine.safety.llm.response_pii_leak — §7.2.18 PII 누출 검출 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 빈 입력 ───────────────────────────

def test_empty_text_clean():
    from engine.safety.llm.response_pii_leak import scan
    r = scan("")
    assert r.clean is True
    assert r.leaks == []


def test_none_safe():
    from engine.safety.llm.response_pii_leak import scan
    r = scan(None)
    assert r.clean is True


def test_clean_text_no_pii():
    from engine.safety.llm.response_pii_leak import scan
    r = scan("허허, 그대의 상을 살피니 이 늙은이의 결이로구먼.")
    assert r.clean is True


# ─────────────────────────── 전화번호 ───────────────────────────

def test_phone_kr_010_detected():
    from engine.safety.llm.response_pii_leak import scan, PII_PHONE_KR
    r = scan("연락처는 010-1234-5678 입니다.")
    assert PII_PHONE_KR in r.leaks


def test_phone_kr_no_dash_detected():
    from engine.safety.llm.response_pii_leak import scan, PII_PHONE_KR
    r = scan("연락 01098765432")
    assert PII_PHONE_KR in r.leaks


def test_phone_intl_detected():
    from engine.safety.llm.response_pii_leak import scan, PII_PHONE_INTL
    r = scan("call +1-555-123-4567")
    assert PII_PHONE_INTL in r.leaks


def test_crisis_hotline_not_leaked():
    """1393/1577-0199 등 위기 핫라인은 PII 아님."""
    from engine.safety.llm.response_pii_leak import scan
    r = scan("자살예방상담전화 1393, 정신건강 1577-0199")
    # 화이트리스트로 phone_kr leak이 없어야
    assert "phone_kr" not in r.leaks


def test_emergency_119_112_not_leaked():
    from engine.safety.llm.response_pii_leak import scan
    r = scan("응급 119, 경찰 112")
    assert "phone_kr" not in r.leaks


# ─────────────────────────── 이메일 ───────────────────────────

def test_email_detected():
    from engine.safety.llm.response_pii_leak import scan, PII_EMAIL
    r = scan("연락은 user@example.com 으로 주십시오.")
    assert PII_EMAIL in r.leaks
    assert "user@example.com" in r.matched_samples


def test_multiple_emails_detected():
    from engine.safety.llm.response_pii_leak import scan
    r = scan("a@b.com 또는 c@d.org")
    assert r.matched_samples.count("a@b.com") + r.matched_samples.count("c@d.org") == 2


# ─────────────────────────── 한국 주민번호 ───────────────────────────

def test_kor_ssn_dashed_detected():
    from engine.safety.llm.response_pii_leak import scan, PII_KOR_SSN
    r = scan("주민번호는 880101-1234567 입니다.")
    assert PII_KOR_SSN in r.leaks


def test_kor_ssn_no_dash_detected():
    from engine.safety.llm.response_pii_leak import scan, PII_KOR_SSN
    r = scan("8801011234567")
    assert PII_KOR_SSN in r.leaks


# ─────────────────────────── 신용카드 ───────────────────────────

def test_credit_card_detected():
    from engine.safety.llm.response_pii_leak import scan, PII_CREDIT_CARD
    r = scan("카드 4111-1111-1111-1111 입력")
    assert PII_CREDIT_CARD in r.leaks


def test_credit_card_spaces_detected():
    from engine.safety.llm.response_pii_leak import scan, PII_CREDIT_CARD
    r = scan("4111 1111 1111 1111")
    assert PII_CREDIT_CARD in r.leaks


# ─────────────────────────── IPv4 ───────────────────────────

def test_ipv4_detected():
    from engine.safety.llm.response_pii_leak import scan, PII_IPV4
    r = scan("서버 IP는 192.168.10.5 입니다.")
    assert PII_IPV4 in r.leaks


def test_loopback_ip_not_leaked():
    """127.0.0.1 / 0.0.0.0 / 1.1.1.1 / 8.8.8.8 같은 공익 IP는 PII 아님."""
    from engine.safety.llm.response_pii_leak import scan
    r = scan("localhost 127.0.0.1, public 8.8.8.8")
    assert "ipv4" not in r.leaks


# ─────────────────────────── API 키 ───────────────────────────

def test_anthropic_api_key_detected():
    from engine.safety.llm.response_pii_leak import scan, PII_API_KEY
    r = scan("key=sk-ant-abcdef1234567890abcdef")
    assert PII_API_KEY in r.leaks


def test_openai_api_key_detected():
    from engine.safety.llm.response_pii_leak import scan, PII_API_KEY
    r = scan("key=sk-abc1234567890ABCDEFGHIJKL")
    assert PII_API_KEY in r.leaks


def test_aws_access_key_detected():
    from engine.safety.llm.response_pii_leak import scan, PII_API_KEY
    r = scan("AWS AKIAIOSFODNN7EXAMPLE")
    assert PII_API_KEY in r.leaks


def test_github_token_detected():
    from engine.safety.llm.response_pii_leak import scan, PII_API_KEY
    r = scan("ghp_" + "a" * 36)
    assert PII_API_KEY in r.leaks


def test_google_api_key_detected():
    from engine.safety.llm.response_pii_leak import scan, PII_API_KEY
    r = scan("google AIzaSyBexample1234567890abcdefghij1234567")
    assert PII_API_KEY in r.leaks


# ─────────────────────────── 통합 ───────────────────────────

def test_multiple_pii_types_aggregated():
    from engine.safety.llm.response_pii_leak import scan
    r = scan("user@ex.com 010-1234-5678 880101-1234567")
    assert "email" in r.leaks
    assert "phone_kr" in r.leaks
    assert "kor_ssn" in r.leaks
    assert len(r.matched_samples) >= 3


def test_has_leak_quick_gate():
    from engine.safety.llm.response_pii_leak import has_leak
    assert has_leak("010-1234-5678") is True
    assert has_leak("정상 응답입니다") is False
    assert has_leak(None) is False


# ─────────────────────────── 폴백 트리거 ───────────────────────────

def test_fallback_trigger_leak_maps_to_persona_failed():
    from engine.safety.llm.response_pii_leak import scan, to_fallback_trigger
    r = scan("user@x.com")
    assert to_fallback_trigger(r) == "persona_failed"


def test_fallback_trigger_clean_returns_empty():
    from engine.safety.llm.response_pii_leak import scan, to_fallback_trigger
    r = scan("허허, 그대.")
    assert to_fallback_trigger(r) == ""


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_response_pii_leak():
    import engine.safety as safety
    assert hasattr(safety, "scan_response_pii")
    assert hasattr(safety, "has_pii_leak")
    assert hasattr(safety, "PIILeakResult")
    assert hasattr(safety, "PII_PHONE_KR")
    assert hasattr(safety, "PII_EMAIL")
    assert hasattr(safety, "PII_KOR_SSN")
    assert hasattr(safety, "PII_API_KEY")
