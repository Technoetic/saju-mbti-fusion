"""engine.safety.input_guards.cache_integrity — §7.2.16 캐시 무결성 회귀 테스트."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _good_envelope():
    return {
        "text": "허허, 그대의 결이로구먼.",
        "cached": True,
        "crisis_alert": None,
        "legal_notice": "[법정 면책] ...",
        "detected_language": "ko",
        "language_advisory": None,
    }


def _write(tmp_path: Path, name: str, body) -> Path:
    p = tmp_path / name
    if isinstance(body, (dict, list)):
        p.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
    else:
        p.write_text(str(body), encoding="utf-8")
    return p


# ─────────────────────────── 단일 파일 ───────────────────────────

def test_verify_clean_cache_file_passes(tmp_path):
    from engine.safety.input_guards.cache_integrity import verify_cache_file
    p = _write(tmp_path, "ok.json", _good_envelope())
    r = verify_cache_file(p)
    assert r.ok is True
    assert r.issues == []


def test_verify_parse_error(tmp_path):
    from engine.safety.input_guards.cache_integrity import (
        verify_cache_file, INTEGRITY_PARSE_ERROR,
    )
    p = _write(tmp_path, "broken.json", "not json {{")
    r = verify_cache_file(p)
    assert INTEGRITY_PARSE_ERROR in r.issues


def test_verify_array_not_dict(tmp_path):
    from engine.safety.input_guards.cache_integrity import (
        verify_cache_file, INTEGRITY_NOT_DICT,
    )
    p = _write(tmp_path, "array.json", ["x", "y"])
    r = verify_cache_file(p)
    assert INTEGRITY_NOT_DICT in r.issues


def test_verify_missing_required_keys(tmp_path):
    from engine.safety.input_guards.cache_integrity import verify_cache_file
    p = _write(tmp_path, "incomplete.json", {"text": "허허"})
    r = verify_cache_file(p)
    assert any("missing_key:cached" in x for x in r.issues)
    assert any("missing_key:legal_notice" in x for x in r.issues)


def test_verify_empty_text(tmp_path):
    from engine.safety.input_guards.cache_integrity import (
        verify_cache_file, INTEGRITY_EMPTY_TEXT,
    )
    env = _good_envelope()
    env["text"] = ""
    p = _write(tmp_path, "empty.json", env)
    r = verify_cache_file(p)
    assert INTEGRITY_EMPTY_TEXT in r.issues


def test_verify_missing_legal_notice(tmp_path):
    from engine.safety.input_guards.cache_integrity import (
        verify_cache_file, INTEGRITY_MISSING_LEGAL,
    )
    env = _good_envelope()
    env["legal_notice"] = None
    p = _write(tmp_path, "nolegal.json", env)
    r = verify_cache_file(p)
    assert INTEGRITY_MISSING_LEGAL in r.issues


def test_verify_crisis_envelope_legal_optional(tmp_path):
    """위기 응답(crisis_alert!=None)은 legal_notice 누락 허용."""
    from engine.safety.input_guards.cache_integrity import (
        verify_cache_file, INTEGRITY_MISSING_LEGAL,
    )
    env = _good_envelope()
    env["legal_notice"] = None
    env["crisis_alert"] = {"severity": "high"}
    p = _write(tmp_path, "crisis.json", env)
    r = verify_cache_file(p)
    assert INTEGRITY_MISSING_LEGAL not in r.issues


def test_verify_prompt_hash_match(tmp_path):
    from engine.safety.input_guards.cache_integrity import verify_cache_file
    env = _good_envelope()
    env["system_prompt_hash"] = "abc123"
    p = _write(tmp_path, "hashed.json", env)
    r = verify_cache_file(p, expected_prompt_hash="abc123")
    assert r.ok is True


def test_verify_prompt_hash_mismatch(tmp_path):
    from engine.safety.input_guards.cache_integrity import (
        verify_cache_file, INTEGRITY_PROMPT_HASH_MISMATCH,
    )
    env = _good_envelope()
    env["system_prompt_hash"] = "old_hash"
    p = _write(tmp_path, "stale.json", env)
    r = verify_cache_file(p, expected_prompt_hash="new_hash")
    assert any(INTEGRITY_PROMPT_HASH_MISMATCH in x for x in r.issues)


def test_verify_nonexistent_file_reports_parse_error(tmp_path):
    from engine.safety.input_guards.cache_integrity import (
        verify_cache_file, INTEGRITY_PARSE_ERROR,
    )
    r = verify_cache_file(tmp_path / "missing.json")
    assert INTEGRITY_PARSE_ERROR in r.issues


# ─────────────────────────── 일괄 감사 ───────────────────────────

def test_audit_empty_directory(tmp_path):
    from engine.safety.input_guards.cache_integrity import audit_cache_directory
    cache = tmp_path / "empty"
    cache.mkdir()
    r = audit_cache_directory(cache)
    assert r.total == 0
    assert r.valid == 0
    assert r.invalid == 0


def test_audit_nonexistent_directory(tmp_path):
    from engine.safety.input_guards.cache_integrity import audit_cache_directory
    r = audit_cache_directory(tmp_path / "missing")
    assert r.total == 0


def test_audit_mixed_files(tmp_path):
    from engine.safety.input_guards.cache_integrity import audit_cache_directory
    cache = tmp_path / "cache"
    cache.mkdir()
    _write(cache, "ok1.json", _good_envelope())
    _write(cache, "ok2.json", _good_envelope())
    _write(cache, "broken.json", "not json")
    bad = _good_envelope()
    bad["text"] = ""
    _write(cache, "empty.json", bad)
    r = audit_cache_directory(cache)
    assert r.total == 4
    assert r.valid == 2
    assert r.invalid == 2
    assert "broken.json" in r.issues_by_file
    assert "empty.json" in r.issues_by_file
    assert r.total_size_bytes > 0


def test_list_corrupt_files_returns_only_invalid(tmp_path):
    from engine.safety.input_guards.cache_integrity import list_corrupt_files
    cache = tmp_path / "cache"
    cache.mkdir()
    _write(cache, "ok.json", _good_envelope())
    _write(cache, "bad.json", "garbage")
    corrupt = list_corrupt_files(cache)
    assert len(corrupt) == 1
    assert corrupt[0].name == "bad.json"


def test_audit_with_prompt_hash_filters_stale(tmp_path):
    from engine.safety.input_guards.cache_integrity import audit_cache_directory
    cache = tmp_path / "cache"
    cache.mkdir()
    fresh = _good_envelope()
    fresh["system_prompt_hash"] = "v2"
    _write(cache, "fresh.json", fresh)
    stale = _good_envelope()
    stale["system_prompt_hash"] = "v1"
    _write(cache, "stale.json", stale)
    r = audit_cache_directory(cache, expected_prompt_hash="v2")
    assert r.valid == 1
    assert r.invalid == 1
    assert "stale.json" in r.issues_by_file


# ─────────────────────────── 알람 ───────────────────────────

def test_alert_clean_is_p3():
    from engine.safety.input_guards.cache_integrity import (
        IntegrityAuditReport, to_alert_payload,
    )
    r = IntegrityAuditReport(total=100, valid=100, invalid=0)
    p = to_alert_payload(r)
    assert p["severity"] == "P3"
    assert p["corruption_rate"] == 0.0


def test_alert_low_corruption_is_p2():
    from engine.safety.input_guards.cache_integrity import (
        IntegrityAuditReport, to_alert_payload,
    )
    r = IntegrityAuditReport(
        total=100, valid=97, invalid=3,
        issues_by_file={"x.json": ["parse_error"]},
    )
    p = to_alert_payload(r)
    assert p["severity"] == "P2"


def test_alert_high_corruption_is_p1():
    from engine.safety.input_guards.cache_integrity import (
        IntegrityAuditReport, to_alert_payload,
    )
    r = IntegrityAuditReport(total=100, valid=80, invalid=20)
    p = to_alert_payload(r)
    assert p["severity"] == "P1"


def test_alert_payload_includes_sample_files():
    from engine.safety.input_guards.cache_integrity import (
        IntegrityAuditReport, to_alert_payload,
    )
    issues = {f"f{i}.json": ["empty_text"] for i in range(10)}
    r = IntegrityAuditReport(total=10, valid=0, invalid=10, issues_by_file=issues)
    p = to_alert_payload(r)
    assert len(p["sample_corrupt_files"]) == 5  # 상위 5개만


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_cache_integrity():
    import engine.safety as safety
    assert hasattr(safety, "verify_cache_file")
    assert hasattr(safety, "audit_cache_directory")
    assert hasattr(safety, "list_corrupt_files")
    assert hasattr(safety, "IntegrityResult")
    assert hasattr(safety, "IntegrityAuditReport")
    assert hasattr(safety, "INTEGRITY_PARSE_ERROR")
