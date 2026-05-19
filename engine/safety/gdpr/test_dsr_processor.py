"""engine.safety.gdpr.dsr_processor — §10 DSR 처리 회귀 테스트."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _mk(
    right_key: str = "erase",
    subject_id: str = "user-abc",
    authenticated: bool = True,
    lang: str = "ko",
    region: str = "KR",
    request_id: str = "req-001",
):
    from engine.safety.gdpr.dsr_processor import DSRRequest
    return DSRRequest(
        right_key=right_key,
        subject_id=subject_id,
        authenticated=authenticated,
        lang=lang,
        region=region,
        request_id=request_id,
        timestamp_epoch=1234567890.0,
    )


def _setup_cache(tmp_path: Path, subject_id: str) -> Path:
    """캐시 파일 두 개 생성 — 하나는 subject 매칭, 하나는 무관."""
    from engine.safety.gdpr.dsr_processor import _subject_hash
    cache = tmp_path / "cache"
    cache.mkdir()
    short = _subject_hash(subject_id)
    # 매칭 파일
    (cache / f"{short}_payload.json").write_text(json.dumps({"text": "허허"}))
    # 무관 파일 — 다른 subject
    other_short = _subject_hash("other-user")
    (cache / f"{other_short}_payload.json").write_text(json.dumps({"text": "X"}))
    return cache


# ─────────────────────────── ingest ───────────────────────────

def test_ingest_valid_request_ok():
    from engine.safety.gdpr.dsr_processor import ingest_dsr
    ok, reason = ingest_dsr(_mk())
    assert ok is True
    assert reason == ""


def test_ingest_unknown_right_key_rejected():
    from engine.safety.gdpr.dsr_processor import ingest_dsr
    ok, reason = ingest_dsr(_mk(right_key="not_a_right"))
    assert ok is False
    assert "unknown_right_key" in reason


def test_ingest_missing_subject_id_rejected():
    from engine.safety.gdpr.dsr_processor import ingest_dsr
    ok, reason = ingest_dsr(_mk(subject_id=""))
    assert ok is False
    assert "subject_id" in reason


def test_ingest_unauthenticated_rejected():
    from engine.safety.gdpr.dsr_processor import ingest_dsr
    ok, reason = ingest_dsr(_mk(authenticated=False))
    assert ok is False
    assert "authentication_required" in reason


# ─────────────────────────── plan ───────────────────────────

def test_plan_erase_includes_delete_actions(tmp_path):
    from engine.safety.gdpr.dsr_processor import plan_dsr, DSR_STATUS_PLANNED
    cache = _setup_cache(tmp_path, "user-abc")
    p = plan_dsr(_mk(right_key="erase"), cache_dir=cache)
    assert p.status == DSR_STATUS_PLANNED
    assert "delete_cache" in p.actions
    assert "delete_feedback_counts" in p.actions


def test_plan_access_uses_list_action(tmp_path):
    from engine.safety.gdpr.dsr_processor import plan_dsr
    cache = _setup_cache(tmp_path, "user-abc")
    p = plan_dsr(_mk(right_key="access"), cache_dir=cache)
    assert "list_cache" in p.actions


def test_plan_portability_uses_export(tmp_path):
    from engine.safety.gdpr.dsr_processor import plan_dsr
    cache = _setup_cache(tmp_path, "user-abc")
    p = plan_dsr(_mk(right_key="portability"), cache_dir=cache)
    assert "export_json" in p.actions


def test_plan_object_blocks_future(tmp_path):
    from engine.safety.gdpr.dsr_processor import plan_dsr
    cache = _setup_cache(tmp_path, "user-abc")
    p = plan_dsr(_mk(right_key="object"), cache_dir=cache)
    assert "mark_objected" in p.actions
    assert "block_future_requests" in p.actions


def test_plan_withdraw_consent_full_purge(tmp_path):
    from engine.safety.gdpr.dsr_processor import plan_dsr
    cache = _setup_cache(tmp_path, "user-abc")
    p = plan_dsr(_mk(right_key="withdraw_consent"), cache_dir=cache)
    assert "delete_cache" in p.actions
    assert "mark_consent_withdrawn" in p.actions


def test_plan_invalid_request_returns_rejected(tmp_path):
    from engine.safety.gdpr.dsr_processor import plan_dsr, DSR_STATUS_REJECTED
    p = plan_dsr(_mk(authenticated=False))
    assert p.status == DSR_STATUS_REJECTED
    assert p.reject_reason == "authentication_required"
    assert p.actions == []


def test_plan_finds_only_matching_cache_files(tmp_path):
    from engine.safety.gdpr.dsr_processor import plan_dsr
    cache = _setup_cache(tmp_path, "user-abc")
    p = plan_dsr(_mk(right_key="erase", subject_id="user-abc"), cache_dir=cache)
    assert len(p.affected_cache_files) == 1
    assert "other-user" not in str(p.affected_cache_files)


def test_plan_sla_reflects_region(tmp_path):
    """KR=10일, EU=30일."""
    from engine.safety.gdpr.dsr_processor import plan_dsr
    cache = _setup_cache(tmp_path, "user-abc")
    p_kr = plan_dsr(_mk(right_key="erase", region="KR"), cache_dir=cache)
    p_eu = plan_dsr(_mk(right_key="erase", region="DE"), cache_dir=cache)
    assert p_kr.sla_business_days == 10
    assert p_eu.sla_business_days == 30


# ─────────────────────────── execute ───────────────────────────

def test_execute_erase_deletes_only_matching_files(tmp_path):
    from engine.safety.gdpr.dsr_processor import plan_dsr, execute_dsr
    cache = _setup_cache(tmp_path, "user-abc")
    p = plan_dsr(_mk(right_key="erase"), cache_dir=cache)
    r = execute_dsr(p, cache_dir=cache)
    assert r["status"] == "executed"
    assert r["files_deleted"] == 1
    # 무관 파일은 보존
    remaining = [x.name for x in cache.iterdir()]
    assert len(remaining) == 1


def test_execute_access_exports_metadata_only(tmp_path):
    from engine.safety.gdpr.dsr_processor import plan_dsr, execute_dsr
    cache = _setup_cache(tmp_path, "user-abc")
    p = plan_dsr(_mk(right_key="access"), cache_dir=cache)
    r = execute_dsr(p, cache_dir=cache)
    assert "list_cache" in r["actions_executed"]
    assert "cache_files" in r["exports"]
    assert len(r["exports"]["cache_files"]) == 1
    # 파일은 그대로 보존 (access는 읽기만)
    assert cache.exists() and len(list(cache.iterdir())) == 2


def test_execute_portability_exports_full_body(tmp_path):
    from engine.safety.gdpr.dsr_processor import plan_dsr, execute_dsr
    cache = _setup_cache(tmp_path, "user-abc")
    p = plan_dsr(_mk(right_key="portability"), cache_dir=cache)
    r = execute_dsr(p, cache_dir=cache)
    assert "portable_records" in r["exports"]
    assert len(r["exports"]["portable_records"]) == 1
    body = r["exports"]["portable_records"][0]["body"]
    assert body["text"] == "허허"


def test_execute_rejected_plan_returns_rejected(tmp_path):
    from engine.safety.gdpr.dsr_processor import plan_dsr, execute_dsr
    p = plan_dsr(_mk(authenticated=False))
    r = execute_dsr(p)
    assert r["status"] == "rejected"
    assert "reject_reason" in r


def test_execute_mark_actions_are_noop_but_recorded(tmp_path):
    """mark_* 액션은 외부 IAM 처리. 결과에 기록만 됨."""
    from engine.safety.gdpr.dsr_processor import plan_dsr, execute_dsr
    cache = _setup_cache(tmp_path, "user-abc")
    p = plan_dsr(_mk(right_key="object"), cache_dir=cache)
    r = execute_dsr(p, cache_dir=cache)
    assert "mark_objected" in r["actions_executed"]
    assert "block_future_requests" in r["actions_executed"]


# ─────────────────────────── audit ───────────────────────────

def test_audit_record_has_no_raw_subject_id(tmp_path):
    """감사 로그에 subject_id 원본은 들어가면 안 됨 (해시만)."""
    from engine.safety.gdpr.dsr_processor import plan_dsr, execute_dsr, build_audit_record
    cache = _setup_cache(tmp_path, "user-abc")
    p = plan_dsr(_mk(right_key="erase", subject_id="user-abc-PII"), cache_dir=cache)
    r = execute_dsr(p, cache_dir=cache)
    audit = build_audit_record(p, r)
    blob = json.dumps(audit)
    assert "user-abc-PII" not in blob
    assert "subject_hash" in audit


def test_audit_record_has_required_fields(tmp_path):
    from engine.safety.gdpr.dsr_processor import plan_dsr, execute_dsr, build_audit_record
    cache = _setup_cache(tmp_path, "user-abc")
    p = plan_dsr(_mk(right_key="erase"), cache_dir=cache)
    r = execute_dsr(p, cache_dir=cache)
    audit = build_audit_record(p, r)
    for k in ("service", "event", "right_key", "subject_hash", "region",
              "status", "actions_executed", "files_deleted",
              "sla_business_days", "request_id"):
        assert k in audit


# ─────────────────────────── process_dsr 통합 ───────────────────────────

def test_process_dsr_full_flow_erase(tmp_path):
    from engine.safety.gdpr.dsr_processor import process_dsr
    cache = _setup_cache(tmp_path, "user-abc")
    out = process_dsr(_mk(right_key="erase"), cache_dir=cache)
    assert out["plan_status"] == "planned"
    assert out["execution_status"] == "executed"
    assert out["files_deleted"] == 1
    assert "audit_record" in out
    assert out["reject_reason"] == ""


def test_process_dsr_rejected_unauthenticated(tmp_path):
    from engine.safety.gdpr.dsr_processor import process_dsr
    out = process_dsr(_mk(authenticated=False))
    assert out["plan_status"] == "rejected"
    assert out["reject_reason"] == "authentication_required"
    assert out["files_deleted"] == 0


def test_process_dsr_idempotent_for_already_purged(tmp_path):
    """한 번 erase 처리 후 재요청해도 에러 없이 0건 삭제."""
    from engine.safety.gdpr.dsr_processor import process_dsr
    cache = _setup_cache(tmp_path, "user-abc")
    process_dsr(_mk(right_key="erase"), cache_dir=cache)
    out = process_dsr(_mk(right_key="erase"), cache_dir=cache)
    assert out["execution_status"] == "executed"
    assert out["files_deleted"] == 0  # 이미 비어있음


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_dsr_processor():
    import engine.safety as safety
    assert hasattr(safety, "DSRRequest")
    assert hasattr(safety, "DSRPlan")
    assert hasattr(safety, "ingest_dsr")
    assert hasattr(safety, "plan_dsr")
    assert hasattr(safety, "execute_dsr")
    assert hasattr(safety, "process_dsr")
    assert hasattr(safety, "build_audit_record")
