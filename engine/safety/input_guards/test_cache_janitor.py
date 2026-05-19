"""engine.safety.input_guards.cache_janitor — §7.2.12 캐시 청소 회귀 테스트."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _mk_cache(tmp_path: Path, n_fresh: int = 2, n_expired: int = 3,
              ttl_sec: int = 24 * 3600) -> tuple[Path, float]:
    """fresh n + expired n 파일을 생성. (cache_dir, now) 반환."""
    cache = tmp_path / "cache"
    cache.mkdir()
    now = 1_700_000_000.0
    fresh_mtime = now - 60  # 1분 전
    expired_mtime = now - ttl_sec - 3600  # TTL + 1시간 전
    for i in range(n_fresh):
        p = cache / f"fresh_{i}.json"
        p.write_text(f'{{"i":{i}}}', encoding="utf-8")
        os.utime(p, (fresh_mtime, fresh_mtime))
    for i in range(n_expired):
        p = cache / f"expired_{i}.json"
        p.write_text(f'{{"i":{i}}}', encoding="utf-8")
        os.utime(p, (expired_mtime, expired_mtime))
    return cache, now


# ─────────────────────────── find_expired_files ───────────────────────────

def test_find_expired_files_separates_fresh_and_expired(tmp_path):
    from engine.safety.input_guards.cache_janitor import find_expired_files
    cache, now = _mk_cache(tmp_path)
    expired = find_expired_files(cache, now=now)
    assert len(expired) == 3
    names = [p.name for p in expired]
    assert all(n.startswith("expired_") for n in names)


def test_find_expired_no_files(tmp_path):
    from engine.safety.input_guards.cache_janitor import find_expired_files
    cache = tmp_path / "empty"
    cache.mkdir()
    assert find_expired_files(cache) == []


def test_find_expired_nonexistent_dir_returns_empty(tmp_path):
    from engine.safety.input_guards.cache_janitor import find_expired_files
    assert find_expired_files(tmp_path / "missing") == []


def test_find_expired_respects_custom_ttl(tmp_path):
    """TTL 0 은 모든 파일을 만료 처리해야 함."""
    from engine.safety.input_guards.cache_janitor import find_expired_files
    cache, now = _mk_cache(tmp_path, n_fresh=2, n_expired=2)
    expired = find_expired_files(cache, ttl_sec=0, now=now + 1)
    assert len(expired) == 4  # 모두 만료


# ─────────────────────────── run_janitor ───────────────────────────

def test_run_janitor_deletes_expired_keeps_fresh(tmp_path):
    from engine.safety.input_guards.cache_janitor import run_janitor
    cache, now = _mk_cache(tmp_path, n_fresh=2, n_expired=3)
    r = run_janitor(cache, now=now)
    assert r.total_files == 5
    assert r.expired_files == 3
    assert r.deleted_files == 3
    assert r.freed_bytes > 0
    # 디스크에 fresh 2개만 남음
    remaining = [p.name for p in cache.iterdir()]
    assert len(remaining) == 2
    assert all(n.startswith("fresh_") for n in remaining)


def test_run_janitor_dry_run_does_not_delete(tmp_path):
    from engine.safety.input_guards.cache_janitor import run_janitor
    cache, now = _mk_cache(tmp_path, n_fresh=1, n_expired=2)
    r = run_janitor(cache, dry_run=True, now=now)
    assert r.expired_files == 2
    assert r.deleted_files == 0
    # 파일 그대로 남아있음
    assert len(list(cache.iterdir())) == 3


def test_run_janitor_freed_bytes_accurate(tmp_path):
    from engine.safety.input_guards.cache_janitor import run_janitor
    cache = tmp_path / "cache"
    cache.mkdir()
    now = 1_700_000_000.0
    # 정확히 100바이트 파일 생성, 만료 처리
    p = cache / "expired.json"
    p.write_text("x" * 100, encoding="utf-8")
    os.utime(p, (now - 2 * 24 * 3600, now - 2 * 24 * 3600))
    r = run_janitor(cache, now=now)
    assert r.freed_bytes == 100


def test_run_janitor_empty_dir(tmp_path):
    from engine.safety.input_guards.cache_janitor import run_janitor
    cache = tmp_path / "empty"
    cache.mkdir()
    r = run_janitor(cache)
    assert r.total_files == 0
    assert r.expired_files == 0
    assert r.deleted_files == 0
    assert r.freed_bytes == 0


def test_run_janitor_reports_oldest_age(tmp_path):
    from engine.safety.input_guards.cache_janitor import run_janitor
    cache = tmp_path / "cache"
    cache.mkdir()
    now = 1_700_000_000.0
    p1 = cache / "a.json"
    p1.write_text("1")
    os.utime(p1, (now - 100, now - 100))  # 100초 전
    p2 = cache / "b.json"
    p2.write_text("2")
    os.utime(p2, (now - 5000, now - 5000))  # 5000초 전
    r = run_janitor(cache, now=now)
    assert r.expired_files == 0  # TTL 86400 미만
    assert r.oldest_age_sec >= 5000


def test_run_janitor_remaining_bytes_after_cleanup(tmp_path):
    from engine.safety.input_guards.cache_janitor import run_janitor
    cache, now = _mk_cache(tmp_path, n_fresh=2, n_expired=3)
    r = run_janitor(cache, now=now)
    # fresh 2개의 합과 remaining_bytes 일치
    remaining_actual = sum(p.stat().st_size for p in cache.iterdir())
    assert r.remaining_bytes == remaining_actual


# ─────────────────────────── 알람 ───────────────────────────

def test_should_alert_disk_full_below_threshold():
    from engine.safety.input_guards.cache_janitor import (
        JanitorReport, should_alert_disk_full, DISK_WARN_BYTES,
    )
    small = JanitorReport(
        total_files=10, expired_files=5, deleted_files=5,
        freed_bytes=1000, remaining_bytes=100_000_000,
        oldest_age_sec=3600, errors=[],
    )
    assert should_alert_disk_full(small) is False


def test_should_alert_disk_full_over_threshold():
    from engine.safety.input_guards.cache_janitor import (
        JanitorReport, should_alert_disk_full, DISK_WARN_BYTES,
    )
    huge = JanitorReport(
        total_files=10, expired_files=0, deleted_files=0,
        freed_bytes=0, remaining_bytes=DISK_WARN_BYTES + 1,
        oldest_age_sec=0, errors=[],
    )
    assert should_alert_disk_full(huge) is True


def test_alert_payload_fields():
    from engine.safety.input_guards.cache_janitor import (
        run_janitor, to_alert_payload,
    )
    cache_path = Path("/tmp") / "test_cache_janitor_alert"
    cache_path.mkdir(exist_ok=True)
    try:
        r = run_janitor(cache_path)
        p = to_alert_payload(r)
        for k in ("service", "total_files", "expired_files", "deleted_files",
                  "freed_bytes", "remaining_bytes", "oldest_age_sec",
                  "disk_warn_triggered", "error_count"):
            assert k in p
        assert p["service"] == "cache_janitor"
    finally:
        # 정리
        for f in cache_path.iterdir():
            f.unlink()
        cache_path.rmdir()


def test_trace_event_fields(tmp_path):
    from engine.safety.input_guards.cache_janitor import run_janitor, to_trace_event
    cache, now = _mk_cache(tmp_path, n_fresh=1, n_expired=1)
    r = run_janitor(cache, now=now)
    t = to_trace_event(r)
    assert t["cache_janitor_run"] is True
    assert t["cache_deleted_files"] == 1
    assert t["cache_total_files"] == 2


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_cache_janitor():
    import engine.safety as safety
    assert hasattr(safety, "run_janitor")
    assert hasattr(safety, "find_expired_files")
    assert hasattr(safety, "JanitorReport")
    assert hasattr(safety, "should_alert_disk_full")
    assert hasattr(safety, "DEFAULT_TTL_SEC")
    assert hasattr(safety, "DISK_WARN_BYTES")
