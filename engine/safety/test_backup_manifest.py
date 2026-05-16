"""engine.safety.backup_manifest — §7.3.8 백업·복구 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 매니페스트 ───────────────────────────

def test_face_reading_manifest_has_all_5_resources():
    from engine.safety.backup_manifest import get_face_reading_manifest
    ids = {r.resource_id for r in get_face_reading_manifest()}
    assert ids == {
        "feedback_counts", "slo_logs", "model_card",
        "governance_audit", "cache",
    }


def test_cache_is_volatile_not_backed_up():
    from engine.safety.backup_manifest import (
        get_resource_by_id, BACKUP_KIND_VOLATILE,
    )
    r = get_resource_by_id("cache")
    assert r is not None
    assert r.kind == BACKUP_KIND_VOLATILE


def test_governance_audit_is_p0_long_retention():
    """KR/EU 규제 의무 — 7년 보관."""
    from engine.safety.backup_manifest import get_resource_by_id, RECOVERY_PRIORITY_P0
    r = get_resource_by_id("governance_audit")
    assert r is not None
    assert r.priority == RECOVERY_PRIORITY_P0
    assert r.retention_days >= 2555  # 7년 = 2555일


def test_slo_logs_rpo_under_5min():
    """SLO 측정은 5분 RPO 필수."""
    from engine.safety.backup_manifest import get_resource_by_id
    r = get_resource_by_id("slo_logs")
    assert r is not None
    assert r.rpo_sec <= 300


def test_personal_data_resources_encrypted_at_rest():
    from engine.safety.backup_manifest import get_face_reading_manifest
    for r in get_face_reading_manifest():
        if r.resource_id in ("feedback_counts", "slo_logs", "governance_audit"):
            assert r.encrypt_at_rest is True


# ─────────────────────────── 조회 ───────────────────────────

def test_list_backup_targets_excludes_volatile():
    from engine.safety.backup_manifest import list_backup_targets
    targets = list_backup_targets()
    assert all(r.kind != "volatile" for r in targets)
    assert all(r.resource_id != "cache" for r in targets)
    assert len(targets) == 4  # 5개 중 cache 제외


def test_get_resource_by_id_unknown_returns_none():
    from engine.safety.backup_manifest import get_resource_by_id
    assert get_resource_by_id("not_a_real_resource") is None


def test_list_by_priority():
    from engine.safety.backup_manifest import (
        list_by_priority, RECOVERY_PRIORITY_P0, RECOVERY_PRIORITY_P1,
    )
    p0 = list_by_priority(RECOVERY_PRIORITY_P0)
    p1 = list_by_priority(RECOVERY_PRIORITY_P1)
    assert any(r.resource_id == "governance_audit" for r in p0)
    assert any(r.resource_id == "feedback_counts" for r in p1)


# ─────────────────────────── RPO 검증 ───────────────────────────

def test_is_within_rpo_recent_backup_ok():
    from engine.safety.backup_manifest import (
        get_resource_by_id, is_within_rpo,
    )
    r = get_resource_by_id("slo_logs")
    now = 1_700_000_000.0
    # 1분 전 백업 — 5분 RPO 안
    assert is_within_rpo(r, last_backup_epoch=now - 60, now=now) is True


def test_is_within_rpo_old_backup_fails():
    from engine.safety.backup_manifest import (
        get_resource_by_id, is_within_rpo,
    )
    r = get_resource_by_id("slo_logs")  # RPO 5분
    now = 1_700_000_000.0
    # 10분 전 백업 — RPO 초과
    assert is_within_rpo(r, last_backup_epoch=now - 600, now=now) is False


def test_overdue_backups_no_history_all_overdue():
    """백업 이력 자체가 없으면 모든 자원이 overdue."""
    from engine.safety.backup_manifest import overdue_backups
    overdue = overdue_backups({})
    # cache(volatile) 제외하고 4개
    ids = {r.resource_id for r in overdue}
    assert ids == {"feedback_counts", "slo_logs", "model_card", "governance_audit"}


def test_overdue_backups_recent_history_none_overdue():
    """모든 자원의 마지막 백업이 RPO 안이면 빈 리스트."""
    from engine.safety.backup_manifest import overdue_backups
    now = 1_700_000_000.0
    history = {
        "feedback_counts": now - 60,
        "slo_logs": now - 60,
        "model_card": now - 60,
        "governance_audit": now - 60,
    }
    assert overdue_backups(history, now=now) == []


def test_overdue_backups_excludes_volatile():
    """cache(volatile) 자원은 백업 이력 없어도 overdue 아님."""
    from engine.safety.backup_manifest import overdue_backups
    overdue = overdue_backups({})
    assert all(r.resource_id != "cache" for r in overdue)


# ─────────────────────────── 무결성 ───────────────────────────

def test_sha256_is_64_chars(tmp_path):
    from engine.safety.backup_manifest import compute_sha256
    p = tmp_path / "test.bin"
    p.write_bytes(b"hello world")
    h = compute_sha256(p)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_sha256_deterministic(tmp_path):
    from engine.safety.backup_manifest import compute_sha256
    p = tmp_path / "test.bin"
    p.write_bytes(b"same content")
    assert compute_sha256(p) == compute_sha256(p)


# ─────────────────────────── 백업 기록 검증 ───────────────────────────

def _mk_record(
    resource_id: str = "slo_logs",
    started: float = 1_700_000_000.0,
    finished: float = 1_700_000_010.0,
    bytes_copied: int = 1024,
    sha256: str = "a" * 64,
    ok: bool = True,
    error: str = "",
):
    from engine.safety.backup_manifest import BackupRecord
    return BackupRecord(
        resource_id=resource_id,
        started_at_epoch=started,
        finished_at_epoch=finished,
        bytes_copied=bytes_copied,
        sha256=sha256,
        ok=ok,
        error=error,
    )


def test_verify_backup_record_clean_no_violations():
    from engine.safety.backup_manifest import (
        get_resource_by_id, verify_backup_record,
    )
    r = get_resource_by_id("slo_logs")
    rec = _mk_record(resource_id="slo_logs")
    assert verify_backup_record(rec, r) == []


def test_verify_backup_record_not_ok_caught():
    from engine.safety.backup_manifest import (
        get_resource_by_id, verify_backup_record,
    )
    r = get_resource_by_id("slo_logs")
    rec = _mk_record(ok=False, error="disk_full")
    v = verify_backup_record(rec, r)
    assert any("not_ok" in x for x in v)


def test_verify_backup_record_zero_bytes_caught():
    from engine.safety.backup_manifest import (
        get_resource_by_id, verify_backup_record,
    )
    r = get_resource_by_id("slo_logs")
    rec = _mk_record(bytes_copied=0)
    v = verify_backup_record(rec, r)
    assert "zero_bytes_copied" in v


def test_verify_backup_record_invalid_sha_caught():
    from engine.safety.backup_manifest import (
        get_resource_by_id, verify_backup_record,
    )
    r = get_resource_by_id("slo_logs")
    rec = _mk_record(sha256="short")
    v = verify_backup_record(rec, r)
    assert "invalid_sha256" in v


def test_verify_backup_record_duration_over_rto_caught():
    """slo_logs RTO=3600. 4000초 걸리면 위반."""
    from engine.safety.backup_manifest import (
        get_resource_by_id, verify_backup_record,
    )
    r = get_resource_by_id("slo_logs")
    rec = _mk_record(started=1_700_000_000, finished=1_700_004_000)
    v = verify_backup_record(rec, r)
    assert any("duration_exceeds_rto" in x for x in v)


def test_verify_backup_record_id_mismatch_caught():
    from engine.safety.backup_manifest import (
        get_resource_by_id, verify_backup_record,
    )
    r = get_resource_by_id("slo_logs")
    rec = _mk_record(resource_id="feedback_counts")
    v = verify_backup_record(rec, r)
    assert any("resource_id_mismatch" in x for x in v)


# ─────────────────────────── 알람 ───────────────────────────

def test_alert_payload_p0_overdue_pages_oncall():
    from engine.safety.backup_manifest import (
        get_face_reading_manifest, overdue_backups, to_alert_payload,
    )
    # governance_audit (P0)만 overdue로 만들기
    now = 1_700_000_000.0
    history = {
        "feedback_counts": now - 60,
        "slo_logs": now - 60,
        "model_card": now - 60,
        # governance_audit 누락 → overdue
    }
    overdue = overdue_backups(history, now=now)
    p = to_alert_payload(overdue, now=now)
    assert p["severity"] == "P0"
    assert p["should_page_oncall"] is True
    assert "governance_audit" in p["p0_overdue_ids"]


def test_alert_payload_only_p2_no_paging():
    from engine.safety.backup_manifest import (
        get_face_reading_manifest, overdue_backups, to_alert_payload,
    )
    # model_card(P2)만 overdue
    now = 1_700_000_000.0
    history = {
        "feedback_counts": now - 60,
        "slo_logs": now - 60,
        "governance_audit": now - 60,
        # model_card 누락 → P2 overdue
    }
    overdue = overdue_backups(history, now=now)
    p = to_alert_payload(overdue, now=now)
    assert p["severity"] == "P2"
    assert p["should_page_oncall"] is False


def test_alert_payload_empty_overdue():
    from engine.safety.backup_manifest import to_alert_payload
    p = to_alert_payload([])
    assert p["total_overdue"] == 0
    assert p["should_page_oncall"] is False


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_backup_manifest():
    import engine.safety as safety
    assert hasattr(safety, "BackupResource")
    assert hasattr(safety, "BackupRecord")
    assert hasattr(safety, "get_face_reading_manifest")
    assert hasattr(safety, "list_backup_targets")
    assert hasattr(safety, "overdue_backups")
    assert hasattr(safety, "verify_backup_record")
    assert hasattr(safety, "compute_sha256")
    assert hasattr(safety, "BACKUP_KIND_PERSISTENT")
    assert hasattr(safety, "RECOVERY_PRIORITY_P0")
