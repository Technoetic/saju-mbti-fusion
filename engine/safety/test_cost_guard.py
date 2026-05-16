"""engine.safety.cost_guard — §7.2.17 비용 가드 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 비용 계산 ───────────────────────────

def test_calculate_cost_gemini():
    from engine.safety.cost_guard import calculate_cost
    # 1M input + 1M output 의 gemini = 0.075 + 0.30 = 0.375
    c = calculate_cost("gemini_vision", input_tokens=1_000_000, output_tokens=1_000_000)
    assert abs(c - 0.375) < 1e-6


def test_calculate_cost_claude_more_expensive():
    from engine.safety.cost_guard import calculate_cost
    g = calculate_cost("gemini_vision", input_tokens=10_000, output_tokens=10_000)
    c = calculate_cost("claude_vision", input_tokens=10_000, output_tokens=10_000)
    assert c > g * 10  # claude는 gemini의 10배 이상


def test_calculate_cost_stub_is_zero():
    from engine.safety.cost_guard import calculate_cost
    assert calculate_cost("deterministic_stub", input_tokens=1000, output_tokens=1000) == 0.0


def test_calculate_cost_unknown_backend_returns_zero():
    from engine.safety.cost_guard import calculate_cost
    assert calculate_cost("xxx", input_tokens=1000, output_tokens=1000) == 0.0


def test_calculate_cost_custom_pricing():
    from engine.safety.cost_guard import calculate_cost
    custom = {"my_backend": {"input": 1.0, "output": 2.0}}
    c = calculate_cost("my_backend", input_tokens=1_000_000, output_tokens=500_000,
                       pricing=custom)
    assert abs(c - (1.0 + 1.0)) < 1e-6


# ─────────────────────────── Tracker — 기본 ───────────────────────────

def _mk_tracker(daily=10.0, monthly=100.0):
    from engine.safety.cost_guard import CostBudget, CostTracker
    return CostTracker(CostBudget(daily_usd=daily, monthly_usd=monthly))


def test_initial_status_is_ok():
    from engine.safety.cost_guard import CostTracker, CostBudget
    t = CostTracker(CostBudget(daily_usd=10.0, monthly_usd=100.0))
    s = t.status(now=1_700_000_000.0)
    assert s.severity == "ok"
    assert s.daily_spent_usd == 0.0
    assert s.should_fallback_to_stub is False


def test_record_accumulates_daily():
    t = _mk_tracker(daily=10.0, monthly=100.0)
    # gemini 100K tokens = 100K/1M * $0.30 = $0.03 (output 기준)
    t.record("gemini_vision", input_tokens=100_000, output_tokens=100_000,
             now=1_700_000_000.0)
    s = t.status(now=1_700_000_000.0)
    assert s.daily_spent_usd > 0
    assert s.monthly_spent_usd > 0


def test_record_returns_record_obj():
    t = _mk_tracker()
    rec = t.record("gemini_vision", input_tokens=1000, output_tokens=1000,
                   now=1_700_000_000.0)
    assert rec.backend == "gemini_vision"
    assert rec.cost_usd > 0


# ─────────────────────────── 임계 등급 ───────────────────────────

def test_warn_severity_at_80pct():
    """claude $3/1M input. daily $3 → 1M input = 100%. 80% = 800k."""
    t = _mk_tracker(daily=3.0, monthly=30.0)
    t.record("claude_vision", input_tokens=820_000, output_tokens=0,
             now=1_700_000_000.0)
    s = t.status(now=1_700_000_000.0)
    assert s.severity == "warn"
    assert s.should_fallback_to_stub is False


def test_critical_severity_at_95pct():
    t = _mk_tracker(daily=3.0, monthly=30.0)
    t.record("claude_vision", input_tokens=960_000, output_tokens=0,
             now=1_700_000_000.0)
    s = t.status(now=1_700_000_000.0)
    assert s.severity == "critical"
    assert s.should_fallback_to_stub is True


def test_exhausted_severity_at_100pct():
    t = _mk_tracker(daily=3.0, monthly=30.0)
    t.record("claude_vision", input_tokens=1_500_000, output_tokens=0,
             now=1_700_000_000.0)
    s = t.status(now=1_700_000_000.0)
    assert s.severity == "exhausted"
    assert s.should_fallback_to_stub is True


# ─────────────────────────── can_afford_llm ───────────────────────────

def test_can_afford_when_ok():
    t = _mk_tracker(daily=10.0, monthly=100.0)
    assert t.can_afford_llm(now=1_700_000_000.0) is True


def test_cannot_afford_when_critical():
    t = _mk_tracker(daily=3.0, monthly=30.0)
    t.record("claude_vision", input_tokens=960_000, output_tokens=0,
             now=1_700_000_000.0)
    assert t.can_afford_llm(now=1_700_000_000.0) is False


# ─────────────────────────── 일/월 분리 ───────────────────────────

def test_daily_resets_next_day():
    t = _mk_tracker(daily=10.0, monthly=100.0)
    today = 1_700_000_000.0
    tomorrow = today + 86400 + 60  # 다음 날
    t.record("claude_vision", input_tokens=1_000_000, output_tokens=0, now=today)
    # 다음 날 status 호출 시 daily는 0
    s = t.status(now=tomorrow)
    assert s.daily_spent_usd == 0.0


def test_monthly_persists_across_days():
    t = _mk_tracker(daily=10.0, monthly=100.0)
    day1 = 1_700_000_000.0  # 2023-11-14
    day2 = day1 + 86400 + 60  # 다음 날
    t.record("gemini_vision", input_tokens=1_000_000, output_tokens=0, now=day1)
    t.record("gemini_vision", input_tokens=1_000_000, output_tokens=0, now=day2)
    s = t.status(now=day2)
    # 같은 달 → 월 누적은 둘 다 포함
    assert s.monthly_spent_usd > 0.10


# ─────────────────────────── 알람 페이로드 ───────────────────────────

def test_alert_payload_ok_is_p3():
    from engine.safety.cost_guard import to_alert_payload
    t = _mk_tracker()
    p = to_alert_payload(t.status(now=1_700_000_000.0))
    assert p["severity"] == "P3"


def test_alert_payload_critical_is_p1():
    from engine.safety.cost_guard import to_alert_payload
    t = _mk_tracker(daily=3.0, monthly=30.0)
    t.record("claude_vision", input_tokens=960_000, output_tokens=0,
             now=1_700_000_000.0)
    p = to_alert_payload(t.status(now=1_700_000_000.0))
    assert p["severity"] == "P1"
    assert p["should_fallback_to_stub"] is True


def test_alert_payload_exhausted_is_p0():
    from engine.safety.cost_guard import to_alert_payload
    t = _mk_tracker(daily=3.0, monthly=30.0)
    t.record("claude_vision", input_tokens=1_500_000, output_tokens=0,
             now=1_700_000_000.0)
    p = to_alert_payload(t.status(now=1_700_000_000.0))
    assert p["severity"] == "P0"


# ─────────────────────────── 리셋 ───────────────────────────

def test_reset_clears_all():
    t = _mk_tracker()
    t.record("gemini_vision", input_tokens=1000, output_tokens=1000,
             now=1_700_000_000.0)
    assert len(t.records()) == 1
    t.reset()
    assert len(t.records()) == 0
    s = t.status(now=1_700_000_000.0)
    assert s.daily_spent_usd == 0.0


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_cost_guard():
    import engine.safety as safety
    assert hasattr(safety, "CostBudget")
    assert hasattr(safety, "CostTracker")
    assert hasattr(safety, "CostRecord")
    assert hasattr(safety, "CostStatus")
    assert hasattr(safety, "calculate_cost")
    assert hasattr(safety, "DEFAULT_PRICING_USD_PER_M")
    assert hasattr(safety, "WARN_PERCENT")
    assert hasattr(safety, "CRITICAL_PERCENT")
