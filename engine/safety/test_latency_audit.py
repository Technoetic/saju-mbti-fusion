"""engine.safety.latency_audit — §7.2.24 latency 감사 회귀 테스트."""

from __future__ import annotations

import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 기본 ───────────────────────────

def test_new_sample_sets_started_at():
    from engine.safety.latency_audit import new_sample
    s = new_sample(request_id="req-1")
    assert s.started_at_ms > 0
    assert s.request_id == "req-1"
    assert s.step_durations_ms == {}


def test_record_step_stores_duration():
    from engine.safety.latency_audit import new_sample, record_step, STEP_LLM_CALL
    s = new_sample()
    record_step(s, STEP_LLM_CALL, 1500)
    assert s.step_durations_ms[STEP_LLM_CALL] == 1500


def test_record_step_clamps_negative():
    from engine.safety.latency_audit import new_sample, record_step, STEP_LLM_CALL
    s = new_sample()
    record_step(s, STEP_LLM_CALL, -100)
    assert s.step_durations_ms[STEP_LLM_CALL] == 0


def test_finalize_sets_finished_at():
    from engine.safety.latency_audit import new_sample, finalize
    s = new_sample()
    finalize(s)
    assert s.finished_at_ms >= s.started_at_ms


def test_total_ms_after_finalize():
    from engine.safety.latency_audit import new_sample, finalize
    s = new_sample()
    time.sleep(0.01)
    finalize(s)
    assert s.total_ms >= 0


def test_steps_total_sums_durations():
    from engine.safety.latency_audit import (
        new_sample, record_step, STEP_LLM_CALL, STEP_SAFETY_GATE,
    )
    s = new_sample()
    record_step(s, STEP_LLM_CALL, 1000)
    record_step(s, STEP_SAFETY_GATE, 50)
    assert s.steps_total_ms == 1050


# ─────────────────────────── measure 컨텍스트 ───────────────────────────

def test_measure_records_elapsed():
    from engine.safety.latency_audit import new_sample, measure, STEP_LLM_CALL
    s = new_sample()
    with measure(s, STEP_LLM_CALL):
        time.sleep(0.02)
    assert s.step_durations_ms[STEP_LLM_CALL] >= 10


def test_measure_records_on_exception():
    from engine.safety.latency_audit import new_sample, measure, STEP_LLM_CALL
    s = new_sample()
    try:
        with measure(s, STEP_LLM_CALL):
            time.sleep(0.01)
            raise RuntimeError("X")
    except RuntimeError:
        pass
    assert STEP_LLM_CALL in s.step_durations_ms


# ─────────────────────────── 평가 ───────────────────────────

def test_evaluate_clean_no_violations():
    from engine.safety.latency_audit import (
        new_sample, record_step, finalize, evaluate,
        STEP_PREFLIGHT, STEP_LLM_CALL,
    )
    s = new_sample()
    record_step(s, STEP_PREFLIGHT, 10)
    record_step(s, STEP_LLM_CALL, 1000)
    finalize(s)
    r = evaluate(s)
    assert r.has_violations is False
    assert r.violations == []
    assert r.total_violated is False


def test_evaluate_step_violation():
    from engine.safety.latency_audit import (
        new_sample, record_step, finalize, evaluate, STEP_LLM_CALL,
    )
    s = new_sample()
    record_step(s, STEP_LLM_CALL, 6000)  # 5000 한도 초과
    finalize(s)
    r = evaluate(s)
    assert len(r.violations) == 1
    assert r.violations[0].step == STEP_LLM_CALL
    assert r.violations[0].duration_ms == 6000


def test_evaluate_preflight_budget_50ms():
    from engine.safety.latency_audit import (
        new_sample, record_step, finalize, evaluate, STEP_PREFLIGHT,
    )
    s = new_sample()
    record_step(s, STEP_PREFLIGHT, 100)
    finalize(s)
    r = evaluate(s)
    assert any(v.step == STEP_PREFLIGHT for v in r.violations)


def test_evaluate_custom_budgets():
    from engine.safety.latency_audit import (
        new_sample, record_step, finalize, evaluate, STEP_LLM_CALL,
    )
    s = new_sample()
    record_step(s, STEP_LLM_CALL, 100)
    finalize(s)
    # 더 엄격한 50ms 한도 사용 시 위반
    r = evaluate(s, step_budgets_ms={STEP_LLM_CALL: 50})
    assert len(r.violations) == 1


def test_evaluate_unknown_step_no_violation():
    """매니페스트에 없는 step은 검사 안 함."""
    from engine.safety.latency_audit import (
        new_sample, record_step, finalize, evaluate,
    )
    s = new_sample()
    record_step(s, "custom_step", 99999)
    finalize(s)
    r = evaluate(s)
    assert r.has_violations is False


# ─────────────────────────── 트레이싱 ───────────────────────────

def test_to_trace_event_includes_all_steps():
    from engine.safety.latency_audit import (
        new_sample, record_step, finalize, to_trace_event,
        STEP_LLM_CALL, STEP_SAFETY_GATE,
    )
    s = new_sample()
    record_step(s, STEP_LLM_CALL, 1000)
    record_step(s, STEP_SAFETY_GATE, 50)
    finalize(s)
    e = to_trace_event(s)
    assert e["latency_llm_call_ms"] == 1000
    assert e["latency_safety_gate_ms"] == 50
    assert "latency_total_ms" in e
    assert "latency_steps_total_ms" in e


# ─────────────────────────── 알람 ───────────────────────────

def test_alert_clean_is_p3():
    from engine.safety.latency_audit import (
        new_sample, finalize, evaluate, to_alert_payload,
    )
    s = new_sample()
    finalize(s)
    p = to_alert_payload(evaluate(s))
    assert p["severity"] == "P3"


def test_alert_single_step_violation_is_p2():
    from engine.safety.latency_audit import (
        new_sample, record_step, finalize, evaluate, to_alert_payload,
        STEP_LLM_CALL,
    )
    s = new_sample()
    record_step(s, STEP_LLM_CALL, 6000)
    finalize(s)
    p = to_alert_payload(evaluate(s))
    assert p["severity"] == "P2"


def test_alert_multiple_violations_is_p1():
    from engine.safety.latency_audit import (
        new_sample, record_step, finalize, evaluate, to_alert_payload,
        STEP_LLM_CALL, STEP_PREFLIGHT,
    )
    s = new_sample()
    record_step(s, STEP_LLM_CALL, 6000)
    record_step(s, STEP_PREFLIGHT, 200)
    finalize(s)
    p = to_alert_payload(evaluate(s))
    assert p["severity"] == "P1"
    assert len(p["violations"]) == 2


# ─────────────────────────── 윈도우 집계 ───────────────────────────

def test_aggregate_step_p95_basic():
    from engine.safety.latency_audit import (
        new_sample, record_step, finalize, aggregate_step_p95,
        STEP_LLM_CALL,
    )
    samples = []
    for i in range(100):
        s = new_sample()
        record_step(s, STEP_LLM_CALL, (i + 1) * 10)  # 10~1000ms
        finalize(s)
        samples.append(s)
    p95 = aggregate_step_p95(samples, STEP_LLM_CALL)
    # 95번째 = idx 94 = 950ms
    assert 940 <= p95 <= 960


def test_aggregate_step_p95_empty():
    from engine.safety.latency_audit import aggregate_step_p95, STEP_LLM_CALL
    assert aggregate_step_p95([], STEP_LLM_CALL) == 0


def test_aggregate_total_p95_basic():
    from engine.safety.latency_audit import (
        new_sample, finalize, aggregate_total_p95,
    )
    samples = []
    base = 1_000_000
    for i in range(100):
        s = new_sample()
        s.started_at_ms = base
        s.finished_at_ms = base + (i + 1) * 10
        samples.append(s)
    p95 = aggregate_total_p95(samples)
    assert 940 <= p95 <= 960


def test_aggregate_total_p95_empty():
    from engine.safety.latency_audit import aggregate_total_p95
    assert aggregate_total_p95([]) == 0


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_latency_audit():
    import engine.safety as safety
    assert hasattr(safety, "LatencySample")
    assert hasattr(safety, "AuditReport")
    assert hasattr(safety, "new_latency_sample")
    assert hasattr(safety, "record_latency_step")
    assert hasattr(safety, "finalize_latency_sample")
    assert hasattr(safety, "evaluate_latency")
    assert hasattr(safety, "STEP_LLM_CALL")
    assert hasattr(safety, "DEFAULT_STEP_BUDGETS_MS")
