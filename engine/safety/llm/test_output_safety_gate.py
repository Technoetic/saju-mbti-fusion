"""engine.safety.llm.output_safety_gate — §7.2.21 통합 안전망 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# 합격 가능한 사극풍 응답 (80자+, 종결, 한글)
GOOD = ("허허, 그대의 처첩궁이 환하니, 이 늙은이가 짚는 결은 자네에게 인연이 따르는 결이로구먼. "
        "삼정이 고르고 명궁이 환하니 마음의 결이 맑도다. 어미가 매끈하니 부부 화목이 따르겠도다. 그대로 가시게.")


# ─────────────────────────── 빈/None ───────────────────────────

def test_empty_response_critical():
    from engine.safety.llm.output_safety_gate import run_safety_gates, VERDICT_CRITICAL
    r = run_safety_gates("")
    assert r.verdict == VERDICT_CRITICAL
    assert "empty_response" in r.failures


def test_none_response_critical():
    from engine.safety.llm.output_safety_gate import run_safety_gates, VERDICT_CRITICAL
    r = run_safety_gates(None)
    assert r.verdict == VERDICT_CRITICAL


# ─────────────────────────── CLEAN ───────────────────────────

def test_clean_response_all_gates_pass():
    from engine.safety.llm.output_safety_gate import run_safety_gates, VERDICT_CLEAN
    r = run_safety_gates(
        GOOD,
        question="결혼운이 어떤가요?",
        age=30,
        gender="male",
        region="KR",
        lang="ko",
    )
    assert r.verdict == VERDICT_CLEAN
    assert r.failures == []
    assert r.is_clean is True
    assert r.fallback_trigger == ""


def test_clean_no_question_provided():
    """question=None이면 alignment 검증 건너뜀."""
    from engine.safety.llm.output_safety_gate import run_safety_gates, VERDICT_CLEAN
    r = run_safety_gates(GOOD, lang="ko")
    assert r.verdict == VERDICT_CLEAN


# ─────────────────────────── CRITICAL — PII ───────────────────────────

def test_pii_leak_critical():
    from engine.safety.llm.output_safety_gate import run_safety_gates, VERDICT_CRITICAL
    bad = GOOD + " 010-1234-5678"
    r = run_safety_gates(bad, lang="ko")
    assert r.verdict == VERDICT_CRITICAL
    assert "pii_leak" in r.failures


def test_email_leak_critical():
    from engine.safety.llm.output_safety_gate import run_safety_gates, VERDICT_CRITICAL
    bad = GOOD + " 문의는 user@example.com 으로."
    r = run_safety_gates(bad, lang="ko")
    assert r.verdict == VERDICT_CRITICAL


def test_api_key_leak_critical():
    from engine.safety.llm.output_safety_gate import run_safety_gates, VERDICT_CRITICAL
    bad = GOOD + " key=sk-ant-abcdef1234567890abcdef"
    r = run_safety_gates(bad, lang="ko")
    assert r.verdict == VERDICT_CRITICAL


# ─────────────────────────── WARN — persona/alignment/fact ───────────────────────────

def test_persona_violation_warn():
    from engine.safety.llm.output_safety_gate import run_safety_gates, VERDICT_WARN
    bad = "안녕하세요 회원님, 분석 결과를 알려드립니다. 행운이 따를 것입니다. 좋은 하루 되세요."
    r = run_safety_gates(bad, lang="ko")
    assert r.verdict == VERDICT_WARN
    assert "persona_failed" in r.failures


def test_alignment_violation_warn():
    """결혼운 화두인데 응답은 건강만 다룸."""
    from engine.safety.llm.output_safety_gate import run_safety_gates, VERDICT_WARN
    health_only = ("허허, 그대의 산근이 곧으니 건강과 수명이 길겠구먼. "
                   "기색이 맑으니 마음의 결도 환하구먼. 그대로 가시게.")
    r = run_safety_gates(
        health_only,
        question="결혼운이 어떤가요?",
        lang="ko",
    )
    assert r.verdict == VERDICT_WARN
    assert "alignment_failed" in r.failures


def test_fact_mismatch_warn():
    """남성 입력인데 응답은 '따님' 언급."""
    from engine.safety.llm.output_safety_gate import run_safety_gates, VERDICT_WARN
    bad = ("허허, 따님의 상을 짚으니 처첩궁이 환하구먼. "
           "삼정이 고르고 명궁이 환하니 마음의 결이 맑도다.")
    r = run_safety_gates(bad, gender="male", lang="ko")
    assert r.verdict == VERDICT_WARN
    assert "fact_mismatch" in r.failures


# ─────────────────────────── MINOR — token_guard만 ───────────────────────────

def test_too_short_minor():
    """페르소나 어휘는 충분하지만 길이만 짧은 응답 → minor."""
    from engine.safety.llm.output_safety_gate import run_safety_gates, VERDICT_MINOR
    # 권장 어휘 3개 이상 + 종결, 단 80자 미만
    short_but_persona_ok = "허허, 그대, 자네의 결이로구먼."
    r = run_safety_gates(short_but_persona_ok, lang="ko")
    assert r.verdict == VERDICT_MINOR
    assert r.fallback_trigger == "empty_response"


def test_truncated_minor_with_token_limit_trigger():
    from engine.safety.llm.output_safety_gate import run_safety_gates, VERDICT_MINOR
    truncated = ("허허, 그대의 처첩궁이 환하니, 이 늙은이가 짚는 결은 자네에게 인연이 따르는 결이로구먼. "
                 "삼정이 고르고 명궁이 환하니 마음의 결이 맑도다. 코끝이 환하고 이마가 넓으니 초년에 학문이 깊을 결이고 중년에는 자리가 든든할 듯")  # 종결 없음 + 80자+
    r = run_safety_gates(truncated, lang="ko")
    assert r.verdict == VERDICT_MINOR
    assert r.fallback_trigger == "token_limit"


# ─────────────────────────── 우선순위 ───────────────────────────

def test_pii_trumps_persona():
    """PII + 페르소나 위반 동시 → critical 우선."""
    from engine.safety.llm.output_safety_gate import run_safety_gates, VERDICT_CRITICAL
    bad = "안녕하세요 회원님, user@example.com 으로 연락주세요. 분석 결과 행운이 따를 것입니다."
    r = run_safety_gates(bad, lang="ko")
    assert r.verdict == VERDICT_CRITICAL


def test_warn_trumps_minor():
    """페르소나 위반 + truncated → warn 우선."""
    from engine.safety.llm.output_safety_gate import run_safety_gates, VERDICT_WARN
    bad = ("안녕하세요 회원님, 분석 결과를 알려드립니다. 좋은 하루 되시고 행운을 빕니다. "
           "오늘은 정말 멋진 날이 될 것이로구")  # persona+truncated
    r = run_safety_gates(bad, lang="ko")
    assert r.verdict == VERDICT_WARN


# ─────────────────────────── details 구조 ───────────────────────────

def test_details_contains_all_gate_sections():
    from engine.safety.llm.output_safety_gate import run_safety_gates
    r = run_safety_gates(GOOD, question="결혼운?", lang="ko")
    for section in ("token_guard", "pii_leak", "persona", "fact_check", "alignment"):
        assert section in r.details


def test_details_persona_section_has_score():
    from engine.safety.llm.output_safety_gate import run_safety_gates
    r = run_safety_gates(GOOD, lang="ko")
    assert "score" in r.details["persona"]


# ─────────────────────────── 폴백 트리거 / 알람 ───────────────────────────

def test_should_fallback_clean_is_false():
    from engine.safety.llm.output_safety_gate import run_safety_gates, should_fallback
    r = run_safety_gates(GOOD, lang="ko")
    assert should_fallback(r) is False


def test_should_fallback_critical_is_true():
    from engine.safety.llm.output_safety_gate import run_safety_gates, should_fallback
    r = run_safety_gates(GOOD + " 010-1234-5678", lang="ko")
    assert should_fallback(r) is True


def test_trace_event_fields():
    from engine.safety.llm.output_safety_gate import run_safety_gates, to_trace_event
    r = run_safety_gates(GOOD, lang="ko")
    e = to_trace_event(r)
    for k in ("safety_gate_verdict", "safety_gate_failures",
              "safety_gate_failure_count", "safety_gate_fallback_trigger"):
        assert k in e
    assert e["safety_gate_verdict"] == "clean"


def test_alert_payload_critical_is_p0():
    from engine.safety.llm.output_safety_gate import run_safety_gates, to_alert_payload
    r = run_safety_gates(GOOD + " 010-1234-5678", lang="ko")
    p = to_alert_payload(r)
    assert p["severity"] == "P0"


def test_alert_payload_clean_is_p3():
    from engine.safety.llm.output_safety_gate import run_safety_gates, to_alert_payload
    r = run_safety_gates(GOOD, lang="ko")
    p = to_alert_payload(r)
    assert p["severity"] == "P3"


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_output_safety_gate():
    import engine.safety as safety
    assert hasattr(safety, "run_safety_gates")
    assert hasattr(safety, "should_fallback")
    assert hasattr(safety, "SafetyGateResult")
    assert hasattr(safety, "VERDICT_CLEAN")
    assert hasattr(safety, "VERDICT_MINOR")
    assert hasattr(safety, "VERDICT_WARN")
    assert hasattr(safety, "VERDICT_CRITICAL")
