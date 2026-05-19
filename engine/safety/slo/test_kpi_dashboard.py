"""engine.safety.slo.kpi_dashboard — §14.11 회귀 테스트."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 임계 + 상태 ───────────────────────────

def test_classify_status_higher_is_better_good():
    from engine.safety.slo.kpi_dashboard import (
        classify_status, KPIThreshold, STATUS_GOOD,
    )
    th = KPIThreshold(warn_at=0.9, bad_at=0.8, higher_is_better=True)
    assert classify_status(value=0.95, threshold=th) == STATUS_GOOD


def test_classify_status_higher_is_better_warn():
    from engine.safety.slo.kpi_dashboard import (
        classify_status, KPIThreshold, STATUS_WARN,
    )
    th = KPIThreshold(warn_at=0.9, bad_at=0.8, higher_is_better=True)
    assert classify_status(value=0.85, threshold=th) == STATUS_WARN


def test_classify_status_higher_is_better_bad():
    from engine.safety.slo.kpi_dashboard import (
        classify_status, KPIThreshold, STATUS_BAD,
    )
    th = KPIThreshold(warn_at=0.9, bad_at=0.8, higher_is_better=True)
    assert classify_status(value=0.75, threshold=th) == STATUS_BAD


def test_classify_status_lower_is_better_good():
    from engine.safety.slo.kpi_dashboard import (
        classify_status, KPIThreshold, STATUS_GOOD,
    )
    th = KPIThreshold(warn_at=4000, bad_at=5000, higher_is_better=False)
    assert classify_status(value=2000, threshold=th) == STATUS_GOOD


def test_classify_status_lower_is_better_bad():
    from engine.safety.slo.kpi_dashboard import (
        classify_status, KPIThreshold, STATUS_BAD,
    )
    th = KPIThreshold(warn_at=4000, bad_at=5000, higher_is_better=False)
    assert classify_status(value=6000, threshold=th) == STATUS_BAD


# ─────────────────────────── 추세 ───────────────────────────

def test_classify_trend_flat():
    from engine.safety.slo.kpi_dashboard import classify_trend, TREND_FLAT
    # 100 → 101: 1% 변화 → flat
    assert classify_trend(current=101, previous=100,
                          higher_is_better=True) == TREND_FLAT


def test_classify_trend_up():
    from engine.safety.slo.kpi_dashboard import classify_trend, TREND_UP
    assert classify_trend(current=150, previous=100,
                          higher_is_better=True) == TREND_UP


def test_classify_trend_down():
    from engine.safety.slo.kpi_dashboard import classify_trend, TREND_DOWN
    assert classify_trend(current=50, previous=100,
                          higher_is_better=True) == TREND_DOWN


def test_classify_trend_previous_zero_current_zero():
    from engine.safety.slo.kpi_dashboard import classify_trend, TREND_FLAT
    assert classify_trend(current=0, previous=0,
                          higher_is_better=False) == TREND_FLAT


def test_classify_trend_previous_zero_current_positive():
    from engine.safety.slo.kpi_dashboard import classify_trend, TREND_UP
    assert classify_trend(current=10, previous=0,
                          higher_is_better=False) == TREND_UP


# ─────────────────────────── KPI 빌더 ───────────────────────────

def test_build_kpi_known():
    from engine.safety.slo.kpi_dashboard import build_kpi, KPI_P95_LATENCY
    m = build_kpi(KPI_P95_LATENCY, 2000.0)
    assert m.kpi_id == KPI_P95_LATENCY
    assert m.value == 2000.0
    assert m.status == "good"
    assert m.unit == "ms"


def test_build_kpi_unknown_raises():
    from engine.safety.slo.kpi_dashboard import build_kpi
    with pytest.raises(ValueError):
        build_kpi("not_a_real_kpi", 0)


def test_build_kpi_with_previous_value():
    from engine.safety.slo.kpi_dashboard import build_kpi, KPI_P95_LATENCY, TREND_UP
    m = build_kpi(KPI_P95_LATENCY, 3000.0, previous_value=2000.0)
    assert m.trend == TREND_UP


def test_build_kpi_persona_pass_rate_bad():
    from engine.safety.slo.kpi_dashboard import build_kpi, KPI_PERSONA_PASS_RATE
    m = build_kpi(KPI_PERSONA_PASS_RATE, 0.70)
    assert m.status == "bad"
    assert m.higher_is_better is True


def test_build_kpi_pii_leak_warn():
    from engine.safety.slo.kpi_dashboard import build_kpi, KPI_PII_LEAK_COUNT
    m = build_kpi(KPI_PII_LEAK_COUNT, 2)
    assert m.status == "warn"  # warn_at=1, bad_at=3


# ─────────────────────────── 대시보드 페이로드 ───────────────────────────

def test_build_dashboard_all_good():
    from engine.safety.slo.kpi_dashboard import build_dashboard, STATUS_GOOD
    p = build_dashboard(current_values={
        "p95_latency_ms": 2000,
        "p99_latency_ms": 4000,
        "persona_pass_rate": 0.98,
    })
    assert p.overall_status == STATUS_GOOD
    assert len(p.metrics) == 3


def test_build_dashboard_one_bad_makes_overall_bad():
    from engine.safety.slo.kpi_dashboard import build_dashboard, STATUS_BAD
    p = build_dashboard(current_values={
        "p95_latency_ms": 2000,             # good
        "persona_pass_rate": 0.70,           # bad
    })
    assert p.overall_status == STATUS_BAD


def test_build_dashboard_warn_when_only_warn():
    from engine.safety.slo.kpi_dashboard import build_dashboard, STATUS_WARN
    p = build_dashboard(current_values={
        "p95_latency_ms": 4500,              # warn
        "persona_pass_rate": 0.98,           # good
    })
    assert p.overall_status == STATUS_WARN


def test_build_dashboard_unknown_kpi_skipped():
    from engine.safety.slo.kpi_dashboard import build_dashboard
    p = build_dashboard(current_values={
        "p95_latency_ms": 2000,
        "not_real_kpi": 9999,
    })
    assert len(p.metrics) == 1
    assert p.metrics[0].kpi_id == "p95_latency_ms"


def test_build_dashboard_with_previous_calculates_trend():
    from engine.safety.slo.kpi_dashboard import build_dashboard, TREND_UP
    p = build_dashboard(
        current_values={"p95_latency_ms": 3000},
        previous_values={"p95_latency_ms": 2000},
    )
    assert p.metrics[0].trend == TREND_UP


# ─────────────────────────── Grafana / Datadog 직렬화 ───────────────────────────

def test_grafana_json_structure():
    from engine.safety.slo.kpi_dashboard import build_dashboard, to_grafana_json
    p = build_dashboard(current_values={"p95_latency_ms": 2000})
    g = to_grafana_json(p)
    assert isinstance(g, list)
    assert g[0]["target"] == "p95_latency_ms"
    # datapoints는 [[value, ts_ms]] 형식
    assert isinstance(g[0]["datapoints"][0], list)
    assert g[0]["datapoints"][0][0] == 2000


def test_datadog_metrics_structure():
    from engine.safety.slo.kpi_dashboard import (
        build_dashboard, to_datadog_metrics,
    )
    p = build_dashboard(current_values={"p95_latency_ms": 2000})
    d = to_datadog_metrics(p)
    assert d[0]["metric"] == "face_reading.p95_latency_ms"
    assert d[0]["type"] == "gauge"
    assert any("system:face_reading" in t for t in d[0]["tags"])


def test_datadog_tags_include_status():
    from engine.safety.slo.kpi_dashboard import (
        build_dashboard, to_datadog_metrics,
    )
    p = build_dashboard(current_values={"persona_pass_rate": 0.5})
    d = to_datadog_metrics(p)
    assert any("status:bad" in t for t in d[0]["tags"])


def test_dashboard_to_json_serializable():
    from engine.safety.slo.kpi_dashboard import (
        build_dashboard, to_grafana_json, to_datadog_metrics,
    )
    p = build_dashboard(current_values={"p95_latency_ms": 2000})
    json.dumps(to_grafana_json(p))
    json.dumps(to_datadog_metrics(p))


# ─────────────────────────── 텍스트 포맷 ───────────────────────────

def test_format_dashboard_text_contains_kpis():
    from engine.safety.slo.kpi_dashboard import (
        build_dashboard, format_dashboard_text,
    )
    p = build_dashboard(current_values={
        "p95_latency_ms": 2000,
        "persona_pass_rate": 0.98,
    })
    text = format_dashboard_text(p)
    assert "KPI Dashboard" in text
    assert "P95 latency" in text
    assert "페르소나 통과율" in text


def test_format_dashboard_text_status_visible():
    from engine.safety.slo.kpi_dashboard import (
        build_dashboard, format_dashboard_text,
    )
    p = build_dashboard(current_values={"persona_pass_rate": 0.5})
    text = format_dashboard_text(p)
    assert "BAD" in text


# ─────────────────────────── 13 KPI 모두 정의 ───────────────────────────

def test_all_13_kpis_have_thresholds():
    from engine.safety.slo.kpi_dashboard import build_kpi
    kpi_ids = [
        "crisis_block_rate", "jailbreak_block_rate", "pii_leak_count",
        "persona_pass_rate", "safety_gate_critical_rate",
        "golden_set_pass_rate", "response_alignment_rate",
        "consistency_pass_rate",
        "p95_latency_ms", "p99_latency_ms", "cache_hit_rate",
        "daily_cost_usd", "monthly_cost_percent",
    ]
    for k in kpi_ids:
        m = build_kpi(k, 0.0)
        assert m.label  # 한국어 라벨 있음
        assert m.unit


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_kpi_dashboard():
    import engine.safety as safety
    assert hasattr(safety, "build_kpi")
    assert hasattr(safety, "build_dashboard")
    assert hasattr(safety, "to_grafana_json")
    assert hasattr(safety, "to_datadog_metrics")
    assert hasattr(safety, "format_dashboard_text")
    assert hasattr(safety, "classify_status")
    assert hasattr(safety, "classify_trend")
    assert hasattr(safety, "KPIMetric")
    assert hasattr(safety, "DashboardPayload")
    assert hasattr(safety, "KPI_P95_LATENCY")
