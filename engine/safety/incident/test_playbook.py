"""engine.safety.incident.playbook — §14.7 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 매니페스트 ───────────────────────────

def test_all_playbooks_have_required_fields():
    from engine.safety.incident.playbook import get_all_playbooks
    for p in get_all_playbooks():
        assert p.incident_id
        assert p.title
        assert p.severity in ("P0", "P1", "P2", "P3")
        assert p.summary
        assert len(p.steps) >= 1
        assert p.verify
        # 모든 step에 title + detail 필수
        for step in p.steps:
            assert step.title
            assert step.detail


def test_at_least_one_p0_playbook_exists():
    from engine.safety.incident.playbook import list_p0_playbooks
    p0 = list_p0_playbooks()
    assert len(p0) >= 1
    # 모두 SLA 0분 (즉시 호출)
    for p in p0:
        assert p.sla_minutes == 0


def test_crisis_block_failed_is_p0():
    from engine.safety.incident.playbook import (
        get_playbook, INCIDENT_CRISIS_BLOCK_FAILED,
    )
    p = get_playbook(INCIDENT_CRISIS_BLOCK_FAILED)
    assert p is not None
    assert p.severity == "P0"
    assert p.postmortem_required is True


def test_pii_leak_is_p0():
    from engine.safety.incident.playbook import (
        get_playbook, INCIDENT_PII_LEAK,
    )
    p = get_playbook(INCIDENT_PII_LEAK)
    assert p is not None
    assert p.severity == "P0"


def test_slo_p95_is_p1_with_15min_sla():
    from engine.safety.incident.playbook import (
        get_playbook, INCIDENT_SLO_P95,
    )
    p = get_playbook(INCIDENT_SLO_P95)
    assert p is not None
    assert p.severity == "P1"
    assert p.sla_minutes == 15


def test_get_playbook_unknown_returns_none():
    from engine.safety.incident.playbook import get_playbook
    assert get_playbook("not_a_real_incident") is None


# ─────────────────────────── 필터 ───────────────────────────

def test_list_by_severity_p0():
    from engine.safety.incident.playbook import list_playbooks_by_severity
    p0 = list_playbooks_by_severity("P0")
    assert all(p.severity == "P0" for p in p0)


def test_list_by_severity_p2():
    from engine.safety.incident.playbook import list_playbooks_by_severity
    p2 = list_playbooks_by_severity("P2")
    assert all(p.severity == "P2" for p in p2)


# ─────────────────────────── 포맷 ───────────────────────────

def test_format_text_includes_severity_and_steps():
    from engine.safety.incident.playbook import (
        get_playbook, format_playbook_text, INCIDENT_CRISIS_BLOCK_FAILED,
    )
    p = get_playbook(INCIDENT_CRISIS_BLOCK_FAILED)
    text = format_playbook_text(p)
    assert "[P0]" in text
    assert "대응 절차" in text
    assert "해결 확인" in text
    # 첫 step title이 본문에 등장
    assert p.steps[0].title in text


def test_format_text_lists_related_modules():
    from engine.safety.incident.playbook import (
        get_playbook, format_playbook_text, INCIDENT_CRISIS_BLOCK_FAILED,
    )
    p = get_playbook(INCIDENT_CRISIS_BLOCK_FAILED)
    text = format_playbook_text(p)
    if p.related_modules:
        assert "관련 모듈" in text
        # 첫 모듈이 포함됨
        assert p.related_modules[0] in text


# ─────────────────────────── alert_router 첨부 ───────────────────────────

def test_to_alert_attachment_has_required_fields():
    from engine.safety.incident.playbook import (
        get_playbook, to_alert_attachment, INCIDENT_SLO_P95,
    )
    p = get_playbook(INCIDENT_SLO_P95)
    a = to_alert_attachment(p)
    for k in ("playbook_id", "playbook_title", "severity", "sla_minutes",
              "first_step", "total_steps", "postmortem_required"):
        assert k in a
    assert a["severity"] == "P1"


def test_to_alert_attachment_first_step_matches():
    from engine.safety.incident.playbook import (
        get_playbook, to_alert_attachment, INCIDENT_CRISIS_BLOCK_FAILED,
    )
    p = get_playbook(INCIDENT_CRISIS_BLOCK_FAILED)
    a = to_alert_attachment(p)
    assert a["first_step"] == p.steps[0].title


# ─────────────────────────── 일관성 ───────────────────────────

def test_p0_playbooks_require_postmortem():
    """P0 사고는 사후 검토 필수."""
    from engine.safety.incident.playbook import list_p0_playbooks
    for p in list_p0_playbooks():
        assert p.postmortem_required is True, f"{p.incident_id} P0 should require postmortem"


def test_sla_minutes_monotonic_with_severity():
    """심각도가 높을수록(P0→P3) SLA가 짧아야 한다."""
    from engine.safety.incident.playbook import get_all_playbooks
    severity_max_sla = {"P0": 0, "P1": 60, "P2": 480, "P3": 1440}
    for p in get_all_playbooks():
        max_sla = severity_max_sla[p.severity]
        assert p.sla_minutes <= max_sla, \
            f"{p.incident_id} severity={p.severity} sla={p.sla_minutes} > {max_sla}"


def test_related_modules_are_engine_safety():
    """플레이북이 참조하는 모듈은 engine.safety 또는 engine.divination 안에 있어야."""
    from engine.safety.incident.playbook import get_all_playbooks
    for p in get_all_playbooks():
        for m in p.related_modules:
            assert m.startswith("engine."), f"{p.incident_id} bad module: {m}"


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_incident_playbook():
    import engine.safety as safety
    assert hasattr(safety, "get_all_playbooks")
    assert hasattr(safety, "get_playbook")
    assert hasattr(safety, "list_playbooks_by_severity")
    assert hasattr(safety, "format_playbook_text")
    assert hasattr(safety, "IncidentPlaybook")
    assert hasattr(safety, "PlaybookStep")
    assert hasattr(safety, "INCIDENT_CRISIS_BLOCK_FAILED")
    assert hasattr(safety, "INCIDENT_PII_LEAK")
