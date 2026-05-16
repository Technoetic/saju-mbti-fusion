"""engine.safety.canary_guard — §7.3.6 카나리 가드 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _mk_metrics(
    request_count: int = 1000,
    crisis_block_failed: int = 0,
    jailbreak_block_failed: int = 0,
    err_rate: float = 0.10,
    p95_latency_ms: int = 1000,
    persona_tone_pass_rate: float = 1.0,
):
    from engine.safety.canary_guard import CanaryMetrics
    return CanaryMetrics(
        request_count=request_count,
        crisis_block_failed=crisis_block_failed,
        jailbreak_block_failed=jailbreak_block_failed,
        err_rate=err_rate,
        p95_latency_ms=p95_latency_ms,
        persona_tone_pass_rate=persona_tone_pass_rate,
    )


# ─────────────────────────── 단계 정의 ───────────────────────────

def test_canary_stages_increasing():
    from engine.safety.canary_guard import CANARY_STAGES
    percents = [s["percent"] for s in CANARY_STAGES]
    assert percents == sorted(percents)
    assert percents[0] == 1
    assert percents[-1] == 100


def test_canary_thresholds_present():
    from engine.safety.canary_guard import CANARY_THRESHOLDS
    for key in ("err_rate_delta_max", "p95_ratio_max",
                "persona_tone_pass_rate_min",
                "crisis_block_failed_max", "jailbreak_block_failed_max"):
        assert key in CANARY_THRESHOLDS


# ─────────────────────────── 표본 충분성 ───────────────────────────

def test_sufficient_sample_thresholds():
    from engine.safety.canary_guard import has_sufficient_sample
    assert has_sufficient_sample(_mk_metrics(request_count=50), 1) is True
    assert has_sufficient_sample(_mk_metrics(request_count=49), 1) is False
    assert has_sufficient_sample(_mk_metrics(request_count=200), 5) is True
    assert has_sufficient_sample(_mk_metrics(request_count=199), 5) is False
    assert has_sufficient_sample(_mk_metrics(request_count=1000), 25) is True
    assert has_sufficient_sample(_mk_metrics(request_count=999), 25) is False


# ─────────────────────────── 절대 회귀 → ROLLBACK ───────────────────────────

def test_crisis_block_failed_triggers_rollback():
    from engine.safety.canary_guard import decide_canary, DECISION_ROLLBACK
    c = _mk_metrics(crisis_block_failed=1)
    b = _mk_metrics()
    d = decide_canary(canary_metrics=c, baseline_metrics=b, current_percent=5)
    assert d.decision == DECISION_ROLLBACK
    assert any("crisis_block_failed" in r for r in d.reasons)


def test_jailbreak_block_failed_triggers_rollback():
    from engine.safety.canary_guard import decide_canary, DECISION_ROLLBACK
    c = _mk_metrics(jailbreak_block_failed=2)
    b = _mk_metrics()
    d = decide_canary(canary_metrics=c, baseline_metrics=b, current_percent=5)
    assert d.decision == DECISION_ROLLBACK


def test_rollback_includes_revert_target():
    from engine.safety.canary_guard import decide_canary, DECISION_ROLLBACK
    c = _mk_metrics(crisis_block_failed=1)
    b = _mk_metrics()
    d = decide_canary(canary_metrics=c, baseline_metrics=b,
                      current_percent=5, last_stable_commit="abc123")
    assert d.decision == DECISION_ROLLBACK
    assert d.suggested_revert_target == "abc123"
    assert d.next_percent == 0


# ─────────────────────────── 임계 회귀 → HOLD ───────────────────────────

def test_err_rate_delta_over_threshold_holds():
    from engine.safety.canary_guard import decide_canary, DECISION_HOLD
    c = _mk_metrics(err_rate=0.20)  # baseline 0.10, delta=0.10 > 0.05
    b = _mk_metrics(err_rate=0.10)
    d = decide_canary(canary_metrics=c, baseline_metrics=b, current_percent=5)
    assert d.decision == DECISION_HOLD
    assert any("err_rate_delta" in r for r in d.reasons)


def test_p95_ratio_over_threshold_holds():
    from engine.safety.canary_guard import decide_canary, DECISION_HOLD
    c = _mk_metrics(p95_latency_ms=2000)  # baseline 1000, ratio=2.0 > 1.20
    b = _mk_metrics(p95_latency_ms=1000)
    d = decide_canary(canary_metrics=c, baseline_metrics=b, current_percent=5)
    assert d.decision == DECISION_HOLD


def test_persona_tone_low_holds():
    from engine.safety.canary_guard import decide_canary, DECISION_HOLD
    c = _mk_metrics(persona_tone_pass_rate=0.90)
    b = _mk_metrics()
    d = decide_canary(canary_metrics=c, baseline_metrics=b, current_percent=5)
    assert d.decision == DECISION_HOLD


def test_hold_does_not_advance_percent():
    from engine.safety.canary_guard import decide_canary, DECISION_HOLD
    c = _mk_metrics(persona_tone_pass_rate=0.50)
    b = _mk_metrics()
    d = decide_canary(canary_metrics=c, baseline_metrics=b, current_percent=5)
    assert d.decision == DECISION_HOLD
    assert d.next_percent == 5  # 같은 단계 유지


# ─────────────────────────── 표본 부족 → HOLD ───────────────────────────

def test_insufficient_sample_holds():
    from engine.safety.canary_guard import decide_canary, DECISION_HOLD
    c = _mk_metrics(request_count=10)
    b = _mk_metrics()
    d = decide_canary(canary_metrics=c, baseline_metrics=b, current_percent=5)
    assert d.decision == DECISION_HOLD
    assert any("insufficient_sample" in r for r in d.reasons)


# ─────────────────────────── 전부 통과 → PROMOTE ───────────────────────────

def test_all_checks_pass_promotes():
    from engine.safety.canary_guard import decide_canary, DECISION_PROMOTE
    c = _mk_metrics()
    b = _mk_metrics()
    d = decide_canary(canary_metrics=c, baseline_metrics=b, current_percent=1)
    assert d.decision == DECISION_PROMOTE
    assert d.next_percent == 5


def test_promote_advances_through_stages():
    from engine.safety.canary_guard import decide_canary
    c = _mk_metrics()
    b = _mk_metrics()
    # 1% → 5% → 25% → 100%
    assert decide_canary(canary_metrics=c, baseline_metrics=b, current_percent=1).next_percent == 5
    assert decide_canary(canary_metrics=c, baseline_metrics=b, current_percent=5).next_percent == 25
    assert decide_canary(canary_metrics=c, baseline_metrics=b, current_percent=25).next_percent == 100


# ─────────────────────────── 우선순위 (ROLLBACK > HOLD > PROMOTE) ───────────────────────────

def test_rollback_takes_priority_over_threshold():
    """절대 회귀가 임계 회귀와 동시에 있으면 ROLLBACK이 우선."""
    from engine.safety.canary_guard import decide_canary, DECISION_ROLLBACK
    c = _mk_metrics(crisis_block_failed=1, err_rate=0.50)
    b = _mk_metrics()
    d = decide_canary(canary_metrics=c, baseline_metrics=b, current_percent=5)
    assert d.decision == DECISION_ROLLBACK


def test_threshold_takes_priority_over_sample():
    """임계 위반과 표본 부족 동시 → HOLD with threshold reason 우선."""
    from engine.safety.canary_guard import decide_canary, DECISION_HOLD
    c = _mk_metrics(request_count=10, err_rate=0.50)
    b = _mk_metrics()
    d = decide_canary(canary_metrics=c, baseline_metrics=b, current_percent=5)
    assert d.decision == DECISION_HOLD
    assert any("err_rate_delta" in r for r in d.reasons)


# ─────────────────────────── SLO 통합 ───────────────────────────

def test_metrics_from_slo_report_maps_fields():
    from engine.safety.canary_guard import metrics_from_slo_report
    slo = {
        "request_count": 500,
        "err_rate": 0.15,
        "latency_ms": {"p50": 200, "p95": 4500, "p99": 8000},
    }
    m = metrics_from_slo_report(slo, persona_tone_pass_rate=0.98)
    assert m.request_count == 500
    assert m.err_rate == 0.15
    assert m.p95_latency_ms == 4500
    assert m.persona_tone_pass_rate == 0.98
    assert m.crisis_block_failed == 0  # 기본값


# ─────────────────────────── 알람 페이로드 ───────────────────────────

def test_to_alert_payload_rollback():
    from engine.safety.canary_guard import decide_canary, to_alert_payload
    c = _mk_metrics(crisis_block_failed=1)
    b = _mk_metrics()
    d = decide_canary(canary_metrics=c, baseline_metrics=b,
                      current_percent=5, last_stable_commit="abc")
    p = to_alert_payload(d, current_percent=5)
    assert p["canary_decision"] == "rollback"
    assert p["should_rollback"] is True
    assert p["current_percent"] == 5
    assert p["suggested_revert_target"] == "abc"


def test_to_alert_payload_promote():
    from engine.safety.canary_guard import decide_canary, to_alert_payload
    c = _mk_metrics()
    b = _mk_metrics()
    d = decide_canary(canary_metrics=c, baseline_metrics=b, current_percent=1)
    p = to_alert_payload(d, current_percent=1)
    assert p["canary_decision"] == "promote"
    assert p["should_rollback"] is False
    assert p["next_percent"] == 5


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_canary_guard():
    import engine.safety as safety
    assert hasattr(safety, "CanaryMetrics")
    assert hasattr(safety, "CanaryDecision")
    assert hasattr(safety, "CANARY_STAGES")
    assert hasattr(safety, "CANARY_THRESHOLDS")
    assert hasattr(safety, "decide_canary")
    assert hasattr(safety, "has_sufficient_sample")
    assert hasattr(safety, "metrics_from_slo_report")
