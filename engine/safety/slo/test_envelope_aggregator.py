"""ADR-185 - envelope KPI 집계 회귀."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_empty_envelopes_zero_kpis():
    from engine.safety.slo.envelope_aggregator import aggregate_envelopes
    r = aggregate_envelopes([])
    assert r["sample_size"] == 0
    assert r["safety_gate_fallback_rate"] == 0.0


def test_all_clean_envelopes_zero_rates():
    from engine.safety.slo.envelope_aggregator import aggregate_envelopes
    envelopes = [
        {"safety_gate_fallback_used": False, "safety_gate_retry_used": False,
         "safety_gate_failures": [], "safety_gate_verdict": "clean"},
    ] * 10
    r = aggregate_envelopes(envelopes)
    assert r["sample_size"] == 10
    assert r["safety_gate_fallback_rate"] == 0.0
    assert r["safety_gate_retry_rate"] == 0.0
    assert r["safety_gate_fate_assertion_rate"] == 0.0


def test_fallback_rate_calculated():
    from engine.safety.slo.envelope_aggregator import aggregate_envelopes
    envelopes = (
        [{"safety_gate_fallback_used": True, "safety_gate_failures": []}] * 3
        + [{"safety_gate_fallback_used": False, "safety_gate_failures": []}] * 7
    )
    r = aggregate_envelopes(envelopes)
    assert r["safety_gate_fallback_rate"] == 0.3


def test_retry_rate_calculated():
    from engine.safety.slo.envelope_aggregator import aggregate_envelopes
    envelopes = (
        [{"safety_gate_retry_used": True, "safety_gate_failures": []}] * 1
        + [{"safety_gate_retry_used": False, "safety_gate_failures": []}] * 9
    )
    r = aggregate_envelopes(envelopes)
    assert r["safety_gate_retry_rate"] == 0.1


def test_fate_assertion_rate_from_failures():
    from engine.safety.slo.envelope_aggregator import aggregate_envelopes
    envelopes = (
        [{"safety_gate_failures": ["fate_assertion_detected"]}] * 2
        + [{"safety_gate_failures": ["persona_failed"]}] * 8
    )
    r = aggregate_envelopes(envelopes)
    assert r["safety_gate_fate_assertion_rate"] == 0.2


def test_critic_safety_disagreement_calculated():
    """critic_passed=True AND fallback_used=True 만 카운트."""
    from engine.safety.slo.envelope_aggregator import aggregate_envelopes
    envelopes = [
        # 4건 disagreement (critic 통과 + 안전망 폴백)
        {"critic_passed": True, "safety_gate_fallback_used": True,
         "safety_gate_failures": []},
        {"critic_passed": True, "safety_gate_fallback_used": True,
         "safety_gate_failures": []},
        {"critic_passed": True, "safety_gate_fallback_used": True,
         "safety_gate_failures": []},
        {"critic_passed": True, "safety_gate_fallback_used": True,
         "safety_gate_failures": []},
        # 6건 agreement
        {"critic_passed": True, "safety_gate_fallback_used": False,
         "safety_gate_failures": []},
    ] + [{"critic_passed": False, "safety_gate_fallback_used": False,
          "safety_gate_failures": []}] * 5
    r = aggregate_envelopes(envelopes)
    assert r["critic_safety_disagreement_rate"] == 0.4


def test_critical_rate_from_verdict():
    from engine.safety.slo.envelope_aggregator import aggregate_envelopes
    envelopes = (
        [{"safety_gate_verdict": "critical", "safety_gate_failures": []}] * 1
        + [{"safety_gate_verdict": "clean", "safety_gate_failures": []}] * 99
    )
    r = aggregate_envelopes(envelopes)
    assert r["safety_gate_critical_rate"] == 0.01


def test_aggregate_by_domain():
    from engine.safety.slo.envelope_aggregator import aggregate_by_domain
    envs_by_domain = {
        "face": [{"safety_gate_fallback_used": True, "safety_gate_failures": []}],
        "palm": [{"safety_gate_fallback_used": False, "safety_gate_failures": []}],
    }
    r = aggregate_by_domain(envs_by_domain)
    assert r["face"]["safety_gate_fallback_rate"] == 1.0
    assert r["palm"]["safety_gate_fallback_rate"] == 0.0


def test_envelopes_by_domain_from_logs():
    from engine.safety.slo.envelope_aggregator import envelopes_by_domain_from_logs
    logs = [
        {"domain": "face", "safety_gate_fallback_used": True},
        {"domain": "palm", "safety_gate_fallback_used": False},
        {"domain": "face", "safety_gate_fallback_used": False},
        {"safety_gate_fallback_used": False},  # 도메인 없음 — 스킵
    ]
    grouped = envelopes_by_domain_from_logs(logs)
    assert len(grouped["face"]) == 2
    assert len(grouped["palm"]) == 1
    assert "unknown" not in grouped


def test_invalid_entries_skipped():
    """dict 아닌 entry는 스킵."""
    from engine.safety.slo.envelope_aggregator import aggregate_envelopes
    envelopes = [
        {"safety_gate_fallback_used": True, "safety_gate_failures": []},
        None,
        "invalid",
        42,
        {"safety_gate_fallback_used": False, "safety_gate_failures": []},
    ]
    r = aggregate_envelopes(envelopes)
    # dict 2개 + non-dict 3개 → sample_size = 5 (전체), fallback 1/5
    assert r["sample_size"] == 5
    assert r["safety_gate_fallback_rate"] == 0.2
