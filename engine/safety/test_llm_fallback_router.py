"""engine.safety.llm_fallback_router — §7.2.11 LLM 폴백 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 지역 가중치 ───────────────────────────

def test_eu_prefers_claude():
    from engine.safety.llm_fallback_router import (
        get_region_preference, BACKEND_CLAUDE, BACKEND_GEMINI,
    )
    for code in ("EU", "DE", "FR", "UK", "GB"):
        primary, secondary = get_region_preference(code)
        assert primary == BACKEND_CLAUDE, f"{code} should prefer Claude"
        assert secondary == BACKEND_GEMINI


def test_kr_jp_cn_prefer_gemini():
    from engine.safety.llm_fallback_router import (
        get_region_preference, BACKEND_GEMINI, BACKEND_CLAUDE,
    )
    for code in ("KR", "JP", "CN"):
        primary, secondary = get_region_preference(code)
        assert primary == BACKEND_GEMINI, f"{code} should prefer Gemini"
        assert secondary == BACKEND_CLAUDE


def test_none_region_default_gemini():
    from engine.safety.llm_fallback_router import get_region_preference, BACKEND_GEMINI
    primary, _ = get_region_preference(None)
    assert primary == BACKEND_GEMINI


def test_unknown_region_default():
    from engine.safety.llm_fallback_router import get_region_preference, BACKEND_GEMINI
    primary, _ = get_region_preference("ZZ-XX")
    assert primary == BACKEND_GEMINI


def test_region_case_insensitive():
    from engine.safety.llm_fallback_router import get_region_preference, BACKEND_CLAUDE
    primary, _ = get_region_preference("de")
    assert primary == BACKEND_CLAUDE


# ─────────────────────────── 실패 분류 ───────────────────────────

def test_classify_network_error():
    from engine.safety.llm_fallback_router import classify_failure, TRIGGER_NETWORK_ERROR
    assert classify_failure(exception=TimeoutError("timeout")) == TRIGGER_NETWORK_ERROR
    assert classify_failure(exception=ConnectionError("conn")) == TRIGGER_NETWORK_ERROR


def test_classify_empty_response():
    from engine.safety.llm_fallback_router import classify_failure, TRIGGER_EMPTY_RESPONSE
    assert classify_failure(response_text="") == TRIGGER_EMPTY_RESPONSE
    assert classify_failure(response_text=None) == TRIGGER_EMPTY_RESPONSE
    assert classify_failure(response_text="   ") == TRIGGER_EMPTY_RESPONSE


def test_classify_token_limit():
    """LLM 응답이 ... 로 끝나면 토큰 한도 의심 → 폴백."""
    from engine.safety.llm_fallback_router import classify_failure, TRIGGER_TOKEN_LIMIT
    assert classify_failure(response_text="허허 그대...") == TRIGGER_TOKEN_LIMIT


def test_classify_persona_failed():
    from engine.safety.llm_fallback_router import classify_failure, TRIGGER_PERSONA_FAILED
    assert classify_failure(
        response_text="허허, 그대",
        persona_passed=False,
    ) == TRIGGER_PERSONA_FAILED


def test_classify_jailbreak_leak():
    from engine.safety.llm_fallback_router import classify_failure, TRIGGER_JAILBREAK_LEAK
    assert classify_failure(
        response_text="허허, 그대",
        jailbreak_categories=["forbidden_advice"],
    ) == TRIGGER_JAILBREAK_LEAK


def test_classify_clean_response_no_trigger():
    from engine.safety.llm_fallback_router import classify_failure, TRIGGER_NONE
    assert classify_failure(
        response_text="허허, 그대, 자네의 결이로구먼.",
        persona_passed=True,
    ) == TRIGGER_NONE


def test_should_fallback_only_for_triggers():
    from engine.safety.llm_fallback_router import (
        should_fallback, TRIGGER_NONE, TRIGGER_NETWORK_ERROR,
    )
    assert should_fallback(TRIGGER_NONE) is False
    assert should_fallback(TRIGGER_NETWORK_ERROR) is True


# ─────────────────────────── 계획 ───────────────────────────

def test_plan_three_steps_default():
    from engine.safety.llm_fallback_router import plan_llm_calls, BACKEND_STUB
    d = plan_llm_calls(region="KR")
    assert len(d.plans) == 3
    assert d.plans[-1].backend == BACKEND_STUB
    assert d.plans[-1].is_last_resort is True


def test_plan_two_steps_without_stub():
    from engine.safety.llm_fallback_router import plan_llm_calls
    d = plan_llm_calls(region="KR", include_stub=False)
    assert len(d.plans) == 2


def test_plan_first_is_primary_for_region():
    from engine.safety.llm_fallback_router import (
        plan_llm_calls, BACKEND_CLAUDE, BACKEND_GEMINI,
    )
    eu = plan_llm_calls(region="DE")
    assert eu.plans[0].backend == BACKEND_CLAUDE
    assert eu.plans[0].is_fallback is False

    kr = plan_llm_calls(region="KR")
    assert kr.plans[0].backend == BACKEND_GEMINI
    assert kr.plans[1].backend == BACKEND_CLAUDE
    assert kr.plans[1].is_fallback is True


def test_plan_timeout_budgets_under_slo():
    """primary + secondary timeout 합계가 p99 SLO(8000ms) 이내."""
    from engine.safety.llm_fallback_router import plan_llm_calls
    d = plan_llm_calls(region="KR", include_stub=False)
    total = sum(p.timeout_ms for p in d.plans)
    assert total <= 8000


# ─────────────────────────── stub 응답 ───────────────────────────

def test_stub_response_4_languages():
    from engine.safety.llm_fallback_router import deterministic_stub_response
    for lang in ("ko", "en", "ja", "zh"):
        r = deterministic_stub_response(lang)
        assert isinstance(r, str)
        assert len(r) > 10


def test_stub_response_ko_passes_persona_eval():
    """stub 응답이 자체적으로 페르소나 회귀 통과해야 함."""
    from engine.safety.llm_fallback_router import deterministic_stub_response
    from engine.safety.persona_self_eval import evaluate_persona_tone
    r = evaluate_persona_tone(deterministic_stub_response("ko"))
    assert r.passed is True


def test_stub_response_unknown_lang_falls_back_to_en():
    from engine.safety.llm_fallback_router import deterministic_stub_response
    assert deterministic_stub_response("fr") == deterministic_stub_response("en")


# ─────────────────────────── 추적 페이로드 ───────────────────────────

def test_trace_event_primary_no_fallback():
    from engine.safety.llm_fallback_router import to_trace_event, BACKEND_GEMINI, TRIGGER_NONE
    e = to_trace_event(backend=BACKEND_GEMINI, trigger=TRIGGER_NONE,
                       attempt_index=0, elapsed_ms=1200)
    assert e["llm_backend"] == BACKEND_GEMINI
    assert e["llm_used_fallback"] is False
    assert e["llm_attempt_index"] == 0


def test_trace_event_fallback_marks_used_fallback():
    from engine.safety.llm_fallback_router import (
        to_trace_event, BACKEND_CLAUDE, TRIGGER_NETWORK_ERROR,
    )
    e = to_trace_event(backend=BACKEND_CLAUDE, trigger=TRIGGER_NETWORK_ERROR,
                       attempt_index=1, elapsed_ms=2500)
    assert e["llm_used_fallback"] is True
    assert e["llm_fallback_trigger"] == TRIGGER_NETWORK_ERROR


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_llm_fallback_router():
    import engine.safety as safety
    assert hasattr(safety, "plan_llm_calls")
    assert hasattr(safety, "classify_failure")
    assert hasattr(safety, "should_fallback")
    assert hasattr(safety, "deterministic_stub_response")
    assert hasattr(safety, "to_trace_event")
    assert hasattr(safety, "LLMCallPlan")
    assert hasattr(safety, "BACKEND_GEMINI")
    assert hasattr(safety, "BACKEND_CLAUDE")
    assert hasattr(safety, "BACKEND_STUB")
