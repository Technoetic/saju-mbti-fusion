"""engine.safety.incident.rollback_trigger — §7.3.2.1 자동 롤백 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 정책 분류 ───────────────────────────

def test_auto_policy_for_critical_events():
    from engine.safety.incident.rollback_trigger import classify_rollback_policy, AUTO
    for ev in ("crisis_block_failed", "service_down", "auth_breach",
               "slo_violation:crisis_rate"):
        assert classify_rollback_policy(ev) == AUTO, f"{ev} should be AUTO"


def test_approval_policy_for_performance_events():
    from engine.safety.incident.rollback_trigger import classify_rollback_policy, APPROVAL
    for ev in ("slo_violation:p95", "slo_violation:p99", "slo_violation:err_rate"):
        assert classify_rollback_policy(ev) == APPROVAL, f"{ev} should be APPROVAL"


def test_never_policy_for_quality_events():
    from engine.safety.incident.rollback_trigger import classify_rollback_policy, NEVER
    for ev in ("slo_violation:cache_hit_rate", "golden_set_regression",
               "data_governance_violation"):
        assert classify_rollback_policy(ev) == NEVER, f"{ev} should be NEVER"


def test_unknown_event_defaults_to_never():
    """미상 이벤트는 안전 기본값으로 자동 롤백 금지."""
    from engine.safety.incident.rollback_trigger import classify_rollback_policy, NEVER
    assert classify_rollback_policy("some_unknown_event") == NEVER


# ─────────────────────────── revert 명령 ───────────────────────────

def test_revert_command_format():
    from engine.safety.incident.rollback_trigger import build_revert_command
    cmd = build_revert_command("abc1234")
    assert cmd.startswith("git revert --no-edit ")
    assert "abc1234..HEAD" in cmd


def test_revert_command_with_explicit_head():
    from engine.safety.incident.rollback_trigger import build_revert_command
    cmd = build_revert_command("abc1234", current_head="def5678")
    assert "abc1234..def5678" in cmd


def test_revert_command_strips_whitespace():
    from engine.safety.incident.rollback_trigger import build_revert_command
    cmd = build_revert_command("  abc1234  ")
    assert "abc1234..HEAD" in cmd
    assert "  abc1234  " not in cmd


def test_revert_command_empty_target_raises():
    from engine.safety.incident.rollback_trigger import build_revert_command
    with pytest.raises(ValueError):
        build_revert_command("")
    with pytest.raises(ValueError):
        build_revert_command("   ")


# ─────────────────────────── decide_rollback ───────────────────────────

def test_decide_rollback_auto_event():
    from engine.safety.incident.rollback_trigger import decide_rollback, AUTO
    d = decide_rollback("slo_violation:crisis_rate", last_stable_commit="stable123")
    assert d.policy == AUTO
    assert d.target_commit == "stable123"
    assert d.reason == "slo_violation:crisis_rate"
    assert "stable123..HEAD" in d.revert_command
    assert d.approval_window_sec == 0  # AUTO는 윈도우 없음


def test_decide_rollback_approval_event_has_window():
    from engine.safety.incident.rollback_trigger import decide_rollback, APPROVAL
    d = decide_rollback("slo_violation:p95", last_stable_commit="stable123")
    assert d.policy == APPROVAL
    assert d.approval_window_sec == 300


def test_decide_rollback_never_event_still_returns_command():
    """NEVER도 명령은 생성 — 수동 운영자가 참고. 자동 실행만 차단."""
    from engine.safety.incident.rollback_trigger import decide_rollback, NEVER
    d = decide_rollback("golden_set_regression", last_stable_commit="stable123")
    assert d.policy == NEVER
    assert d.revert_command  # 명령 자체는 생성됨


# ─────────────────────────── should_execute_immediately ───────────────────────────

def test_should_execute_immediately_auto_only():
    from engine.safety.incident.rollback_trigger import (
        decide_rollback,
        should_execute_immediately,
    )
    auto = decide_rollback("crisis_block_failed", last_stable_commit="x")
    approval = decide_rollback("slo_violation:p95", last_stable_commit="x")
    never = decide_rollback("golden_set_regression", last_stable_commit="x")
    assert should_execute_immediately(auto) is True
    assert should_execute_immediately(approval) is False
    assert should_execute_immediately(never) is False


# ─────────────────────────── 알람 페이로드 ───────────────────────────

def test_to_alert_payload_has_required_fields():
    from engine.safety.incident.rollback_trigger import decide_rollback, to_alert_payload
    d = decide_rollback("slo_violation:crisis_rate", last_stable_commit="abc")
    p = to_alert_payload(d)
    assert p["rollback_policy"] == "auto"
    assert p["target_commit"] == "abc"
    assert p["reason"] == "slo_violation:crisis_rate"
    assert "abc..HEAD" in p["revert_command"]
    assert p["auto_execute"] is True
    assert p["approval_window_sec"] == 0


def test_to_alert_payload_approval_auto_execute_false():
    from engine.safety.incident.rollback_trigger import decide_rollback, to_alert_payload
    d = decide_rollback("slo_violation:p95", last_stable_commit="abc")
    p = to_alert_payload(d)
    assert p["auto_execute"] is False
    assert p["approval_window_sec"] == 300


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_rollback_trigger():
    import engine.safety as safety
    assert hasattr(safety, "AUTO")
    assert hasattr(safety, "APPROVAL")
    assert hasattr(safety, "NEVER")
    assert hasattr(safety, "RollbackDecision")
    assert hasattr(safety, "classify_rollback_policy")
    assert hasattr(safety, "decide_rollback")
    assert hasattr(safety, "should_execute_immediately")
    assert hasattr(safety, "to_alert_payload")
