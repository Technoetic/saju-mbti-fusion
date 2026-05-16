"""engine.safety.quarterly_review — §14.9 회귀 테스트."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── MTTR ───────────────────────────

def test_compute_mttr_empty():
    from engine.safety.quarterly_review import compute_mttr_minutes
    assert compute_mttr_minutes([]) == 0


def test_compute_mttr_basic():
    from engine.safety.quarterly_review import (
        compute_mttr_minutes, IncidentSummary,
    )
    incidents = [
        IncidentSummary(incident_id="a", severity="P0", duration_minutes=30),
        IncidentSummary(incident_id="b", severity="P1", duration_minutes=60),
    ]
    assert compute_mttr_minutes(incidents) == 45


def test_compute_mttr_skips_zero_duration():
    from engine.safety.quarterly_review import (
        compute_mttr_minutes, IncidentSummary,
    )
    incidents = [
        IncidentSummary(incident_id="a", severity="P0", duration_minutes=30),
        IncidentSummary(incident_id="b", severity="P1", duration_minutes=0),
    ]
    assert compute_mttr_minutes(incidents) == 30


# ─────────────────────────── 등급 ───────────────────────────

def test_grade_a_clean_quarter():
    from engine.safety.quarterly_review import evaluate_grade
    g = evaluate_grade(
        compliance_coverage=100.0, p0_incidents=0, p1_incidents=0,
        slo_violations=0, cost_severity="ok",
    )
    assert g == "A"


def test_grade_d_for_2_p0_incidents():
    from engine.safety.quarterly_review import evaluate_grade
    g = evaluate_grade(
        compliance_coverage=100.0, p0_incidents=2, p1_incidents=0,
        slo_violations=0, cost_severity="ok",
    )
    assert g == "D"


def test_grade_d_for_exhausted_cost():
    from engine.safety.quarterly_review import evaluate_grade
    g = evaluate_grade(
        compliance_coverage=100.0, p0_incidents=0, p1_incidents=0,
        slo_violations=0, cost_severity="exhausted",
    )
    assert g == "D"


def test_grade_c_for_single_p0():
    from engine.safety.quarterly_review import evaluate_grade
    g = evaluate_grade(
        compliance_coverage=100.0, p0_incidents=1, p1_incidents=0,
        slo_violations=0, cost_severity="ok",
    )
    assert g == "C"


def test_grade_c_for_low_coverage():
    from engine.safety.quarterly_review import evaluate_grade
    g = evaluate_grade(
        compliance_coverage=85.0, p0_incidents=0, p1_incidents=0,
        slo_violations=0, cost_severity="ok",
    )
    assert g == "C"


def test_grade_b_for_many_p1():
    from engine.safety.quarterly_review import evaluate_grade
    g = evaluate_grade(
        compliance_coverage=100.0, p0_incidents=0, p1_incidents=5,
        slo_violations=0, cost_severity="ok",
    )
    assert g == "B"


def test_grade_no_s_level_exists():
    """절대 S 등급 없음 (만족 금지 원칙)."""
    from engine.safety.quarterly_review import evaluate_grade
    # 모든 게 완벽해도 A 최대
    g = evaluate_grade(
        compliance_coverage=100.0, p0_incidents=0, p1_incidents=0,
        slo_violations=0, cost_severity="ok",
    )
    assert g != "S"
    assert g in ("A", "B", "C", "D")


# ─────────────────────────── 다음 분기 우선순위 ───────────────────────────

def test_next_quarter_focus_includes_p0_first():
    from engine.safety.quarterly_review import derive_next_quarter_focus
    focuses = derive_next_quarter_focus(
        missing_items=(), p0_incidents=2, slo_violations=[],
        cost_severity="ok",
    )
    assert "P0 사고" in focuses[0]


def test_next_quarter_focus_missing_items():
    from engine.safety.quarterly_review import derive_next_quarter_focus
    focuses = derive_next_quarter_focus(
        missing_items=("7.2.30_new", "7.2.31_other"), p0_incidents=0,
        slo_violations=[], cost_severity="ok",
    )
    assert any("미구현" in f for f in focuses)


def test_next_quarter_focus_always_includes_compliance_check():
    """compliance 정기 점검은 항상 포함."""
    from engine.safety.quarterly_review import derive_next_quarter_focus
    focuses = derive_next_quarter_focus(
        missing_items=(), p0_incidents=0, slo_violations=[],
        cost_severity="ok",
    )
    assert any("compliance" in f.lower() or "자체 점검" in f for f in focuses)


def test_next_quarter_focus_max_5():
    from engine.safety.quarterly_review import derive_next_quarter_focus
    focuses = derive_next_quarter_focus(
        missing_items=("a", "b", "c"), p0_incidents=3,
        slo_violations=["p95=6000ms"], cost_severity="critical",
    )
    assert len(focuses) <= 5


# ─────────────────────────── build_review ───────────────────────────

def test_build_review_clean_quarter_grade_a():
    from engine.safety.quarterly_review import build_review
    r = build_review(
        quarter_label="2026Q2",
        compliance_coverage_percent=100.0,
        slo_summary={
            "request_count": 10000,
            "latency_ms": {"p95": 2000, "p99": 4000},
            "crisis_rate": 0.001, "err_rate": 0.05, "cache_hit_rate": 0.3,
            "slo_violations": [],
        },
        incidents=[],
        monthly_spent_usd=50.0, monthly_budget_usd=100.0,
        cost_severity="ok",
    )
    assert r.overall_grade == "A"
    assert r.incident_total == 0
    assert r.slo_request_count == 10000


def test_build_review_d_grade_for_p0():
    from engine.safety.quarterly_review import build_review, IncidentSummary
    r = build_review(
        quarter_label="2026Q2",
        compliance_coverage_percent=100.0,
        incidents=[
            IncidentSummary("a", "P0", 60),
            IncidentSummary("b", "P0", 30),
        ],
    )
    assert r.overall_grade == "D"
    assert r.incident_p0 == 2


def test_build_review_executive_summary_5_lines():
    from engine.safety.quarterly_review import build_review
    r = build_review(
        quarter_label="2026Q2",
        compliance_coverage_percent=100.0,
    )
    assert len(r.executive_summary) == 5


def test_build_review_mttr_calculated():
    from engine.safety.quarterly_review import build_review, IncidentSummary
    r = build_review(
        quarter_label="2026Q2",
        compliance_coverage_percent=100.0,
        incidents=[
            IncidentSummary("a", "P1", 20),
            IncidentSummary("b", "P2", 40),
        ],
    )
    assert r.mttr_minutes == 30


# ─────────────────────────── 마크다운 ───────────────────────────

def test_markdown_includes_all_sections():
    from engine.safety.quarterly_review import build_review, format_markdown
    r = build_review(
        quarter_label="2026Q2",
        compliance_coverage_percent=100.0,
    )
    md = format_markdown(r)
    for section in ("# 2026Q2", "Overall Grade", "## Executive Summary",
                    "## Compliance", "## SLO", "## Incidents",
                    "## Cost", "## Next Quarter Focus"):
        assert section in md, f"missing {section}"


def test_markdown_grade_visible():
    from engine.safety.quarterly_review import build_review, format_markdown
    r = build_review(
        quarter_label="2026Q2", compliance_coverage_percent=100.0,
    )
    md = format_markdown(r)
    assert "**Overall Grade: A**" in md


# ─────────────────────────── JSON ───────────────────────────

def test_to_json_serializable():
    from engine.safety.quarterly_review import build_review, to_json
    r = build_review(quarter_label="2026Q2", compliance_coverage_percent=100.0)
    j = to_json(r)
    s = json.dumps(j, ensure_ascii=False)
    parsed = json.loads(s)
    assert parsed["quarter_label"] == "2026Q2"


def test_to_json_has_nested_structures():
    from engine.safety.quarterly_review import build_review, to_json
    r = build_review(quarter_label="2026Q2", compliance_coverage_percent=100.0)
    j = to_json(r)
    for k in ("compliance", "slo", "incidents", "cost"):
        assert k in j
    assert "coverage_percent" in j["compliance"]
    assert "p0" in j["incidents"]


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_quarterly_review():
    import engine.safety as safety
    assert hasattr(safety, "build_quarterly_review")
    assert hasattr(safety, "format_quarterly_review_markdown")
    assert hasattr(safety, "quarterly_review_to_json")
    assert hasattr(safety, "compute_mttr_minutes")
    assert hasattr(safety, "evaluate_quarterly_grade")
    assert hasattr(safety, "derive_next_quarter_focus")
    assert hasattr(safety, "QuarterlyReview")
    assert hasattr(safety, "IncidentSummary")
