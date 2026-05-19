"""engine.safety.audit.postmortem_builder — §14.8 회귀 테스트."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 통지 의무 평가 ───────────────────────────

def test_notification_none_when_no_affected_users():
    from engine.safety.audit.postmortem_builder import (
        evaluate_notification_required, NOTIFICATION_NONE,
    )
    r = evaluate_notification_required(("kor_ssn",), affected_users=0)
    assert r == NOTIFICATION_NONE


def test_notification_users_for_ssn():
    from engine.safety.audit.postmortem_builder import (
        evaluate_notification_required, NOTIFICATION_USERS,
    )
    r = evaluate_notification_required(("kor_ssn",), affected_users=1)
    assert r == NOTIFICATION_USERS


def test_notification_users_for_credit_card():
    from engine.safety.audit.postmortem_builder import (
        evaluate_notification_required, NOTIFICATION_USERS,
    )
    r = evaluate_notification_required(("credit_card",), affected_users=1)
    assert r == NOTIFICATION_USERS


def test_notification_regulator_for_phone_email():
    from engine.safety.audit.postmortem_builder import (
        evaluate_notification_required, NOTIFICATION_REGULATOR_72H,
    )
    r = evaluate_notification_required(("phone_number", "email"),
                                       affected_users=5)
    assert r == NOTIFICATION_REGULATOR_72H


def test_notification_dpo_for_biometric():
    from engine.safety.audit.postmortem_builder import (
        evaluate_notification_required, NOTIFICATION_DPO,
    )
    r = evaluate_notification_required(("biometric_inference",),
                                       affected_users=10)
    assert r == NOTIFICATION_DPO


def test_notification_picks_most_strict_category():
    """ssn(USERS) + session_log(INTERNAL) → USERS 우선."""
    from engine.safety.audit.postmortem_builder import (
        evaluate_notification_required, NOTIFICATION_USERS,
    )
    r = evaluate_notification_required(("session_log", "kor_ssn"),
                                       affected_users=1)
    assert r == NOTIFICATION_USERS


def test_notification_unknown_category_internal():
    from engine.safety.audit.postmortem_builder import (
        evaluate_notification_required, NOTIFICATION_INTERNAL,
    )
    r = evaluate_notification_required(("unknown_cat",), affected_users=1)
    assert r == NOTIFICATION_INTERNAL


# ─────────────────────────── 5 Whys ───────────────────────────

def test_five_whys_template_returns_5_items():
    from engine.safety.audit.postmortem_builder import build_five_whys_template
    whys = build_five_whys_template("응답이 PII를 누출했다")
    assert len(whys) == 5
    assert "응답이 PII를 누출했다" in whys[0]


def test_five_whys_has_placeholders():
    from engine.safety.audit.postmortem_builder import build_five_whys_template
    whys = build_five_whys_template("X")
    # 2~5번은 모두 작성 필요 placeholder
    for w in whys[1:]:
        assert "작성 필요" in w


# ─────────────────────────── build_draft ───────────────────────────

def test_build_draft_basic():
    from engine.safety.audit.postmortem_builder import build_draft
    d = build_draft(
        incident_id="crisis_block_failed",
        title="위기 신호 차단 실패",
        severity="P0",
        detected_at_iso="2026-05-15T10:00:00+00:00",
        resolved_at_iso="2026-05-15T10:30:00+00:00",
    )
    assert d.incident_id == "crisis_block_failed"
    assert d.severity == "P0"
    assert d.duration_minutes == 30


def test_build_draft_duration_for_invalid_dates():
    from engine.safety.audit.postmortem_builder import build_draft
    d = build_draft(
        incident_id="x", title="X", severity="P1",
        detected_at_iso="invalid", resolved_at_iso="bad",
    )
    assert d.duration_minutes == 0


def test_build_draft_negative_duration_clamped():
    """resolved < detected → 0으로 클램프."""
    from engine.safety.audit.postmortem_builder import build_draft
    d = build_draft(
        incident_id="x", title="X", severity="P1",
        detected_at_iso="2026-05-15T11:00:00+00:00",
        resolved_at_iso="2026-05-15T10:00:00+00:00",
    )
    assert d.duration_minutes == 0


def test_build_draft_notification_evaluated():
    from engine.safety.audit.postmortem_builder import (
        build_draft, NOTIFICATION_USERS,
    )
    d = build_draft(
        incident_id="pii_leak", title="X", severity="P0",
        detected_at_iso="2026-05-15T10:00:00+00:00",
        resolved_at_iso="2026-05-15T10:30:00+00:00",
        affected_users_estimated=10,
        data_categories=("kor_ssn",),
    )
    assert d.notification_required == NOTIFICATION_USERS


def test_build_draft_includes_five_whys():
    from engine.safety.audit.postmortem_builder import build_draft
    d = build_draft(
        incident_id="x", title="X", severity="P0",
        detected_at_iso="2026-05-15T10:00:00+00:00",
        resolved_at_iso="2026-05-15T10:30:00+00:00",
        initial_problem="응답에 PII 누출",
    )
    assert len(d.five_whys) == 5
    assert "응답에 PII 누출" in d.five_whys[0]


def test_build_draft_default_remediation_present():
    from engine.safety.audit.postmortem_builder import build_draft
    d = build_draft(
        incident_id="x", title="X", severity="P0",
        detected_at_iso="2026-05-15T10:00:00+00:00",
        resolved_at_iso="2026-05-15T10:30:00+00:00",
    )
    assert len(d.short_term_actions) >= 1
    assert len(d.long_term_actions) >= 1
    # 모든 action은 owner placeholder 가짐
    for a in d.short_term_actions + d.long_term_actions:
        assert a.owner  # 비어있지 않음


# ─────────────────────────── timeline ───────────────────────────

def test_build_draft_accepts_timeline():
    from engine.safety.audit.postmortem_builder import build_draft, TimelineEvent
    timeline = (
        TimelineEvent(
            timestamp_iso="2026-05-15T10:00:00+00:00",
            actor="system", event="alert fired",
        ),
        TimelineEvent(
            timestamp_iso="2026-05-15T10:05:00+00:00",
            actor="on-call", event="paged, started investigation",
        ),
    )
    d = build_draft(
        incident_id="x", title="X", severity="P0",
        detected_at_iso="2026-05-15T10:00:00+00:00",
        resolved_at_iso="2026-05-15T10:30:00+00:00",
        timeline=timeline,
    )
    assert len(d.timeline) == 2
    assert d.timeline[0].actor == "system"


# ─────────────────────────── 마크다운 출력 ───────────────────────────

def test_markdown_includes_all_sections():
    from engine.safety.audit.postmortem_builder import build_draft, format_markdown
    d = build_draft(
        incident_id="x", title="테스트 사고", severity="P0",
        detected_at_iso="2026-05-15T10:00:00+00:00",
        resolved_at_iso="2026-05-15T10:30:00+00:00",
        affected_users_estimated=5,
        data_categories=("email",),
    )
    md = format_markdown(d)
    for section in ("# Postmortem", "## Impact", "## Timeline",
                    "## Root Cause", "## What Went Well",
                    "## What Went Wrong", "## Where We Got Lucky",
                    "## Short-term Remediation", "## Long-term Remediation",
                    "## Regulatory Notification"):
        assert section in md, f"missing {section}"


def test_markdown_mentions_gdpr_for_user_notification():
    from engine.safety.audit.postmortem_builder import build_draft, format_markdown
    d = build_draft(
        incident_id="x", title="X", severity="P0",
        detected_at_iso="2026-05-15T10:00:00+00:00",
        resolved_at_iso="2026-05-15T10:30:00+00:00",
        affected_users_estimated=10,
        data_categories=("kor_ssn",),
    )
    md = format_markdown(d)
    assert "GDPR Art.34" in md
    assert "KR PIPA §34" in md


def test_markdown_omits_gdpr_when_internal_only():
    from engine.safety.audit.postmortem_builder import build_draft, format_markdown
    d = build_draft(
        incident_id="x", title="X", severity="P2",
        detected_at_iso="2026-05-15T10:00:00+00:00",
        resolved_at_iso="2026-05-15T10:30:00+00:00",
        affected_users_estimated=1,
        data_categories=("session_log",),
    )
    md = format_markdown(d)
    # internal_only 등급 → Art.33/34 안내 안 함
    assert "GDPR Art.33" not in md
    assert "GDPR Art.34" not in md


# ─────────────────────────── JSON ───────────────────────────

def test_to_json_valid_serializable():
    from engine.safety.audit.postmortem_builder import build_draft, to_json
    d = build_draft(
        incident_id="x", title="X", severity="P0",
        detected_at_iso="2026-05-15T10:00:00+00:00",
        resolved_at_iso="2026-05-15T10:30:00+00:00",
    )
    j = to_json(d)
    # JSON 직렬화 가능
    s = json.dumps(j, ensure_ascii=False)
    assert "x" in s
    parsed = json.loads(s)
    assert parsed["incident_id"] == "x"


def test_to_json_has_all_required_fields():
    from engine.safety.audit.postmortem_builder import build_draft, to_json
    d = build_draft(
        incident_id="x", title="X", severity="P0",
        detected_at_iso="2026-05-15T10:00:00+00:00",
        resolved_at_iso="2026-05-15T10:30:00+00:00",
    )
    j = to_json(d)
    for k in ("incident_id", "title", "severity", "duration_minutes",
              "notification_required", "five_whys",
              "short_term_actions", "long_term_actions"):
        assert k in j


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_postmortem_builder():
    import engine.safety as safety
    assert hasattr(safety, "build_postmortem_draft")
    assert hasattr(safety, "format_postmortem_markdown")
    assert hasattr(safety, "postmortem_to_json")
    assert hasattr(safety, "evaluate_notification_required")
    assert hasattr(safety, "build_five_whys_template")
    assert hasattr(safety, "PostmortemDraft")
    assert hasattr(safety, "TimelineEvent")
    assert hasattr(safety, "RemediationAction")
    assert hasattr(safety, "NOTIFICATION_NONE")
    assert hasattr(safety, "NOTIFICATION_USERS")
