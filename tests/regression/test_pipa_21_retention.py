"""ADR-060 회귀 — PIPA §21 개인정보 파기 의무 자동화 검증.

본 시스템 cache_janitor.py (§7.2.12)가 PIPA §21 "수집 목적 달성 시 지체 없이
파기" 의무를 자동화한다. TTL 24h + 5분 주기 청소.
"""

import time

from engine.safety.input_guards.cache_janitor import (
    DEFAULT_TTL_SEC,
    JanitorReport,
    find_expired_files,
    run_janitor,
    should_alert_disk_full,
)


def test_default_ttl_24h_matches_pipa_principle():
    """기본 TTL = 24시간 — PIPA §21 '지체 없이' 정합 (즉시 파기는 캐시 무효화,
    24h 윈도우는 동일 요청 재현 가능성 위한 운영 최소 시간)."""
    assert DEFAULT_TTL_SEC == 24 * 3600


def test_find_expired_files_24h_threshold(tmp_path):
    """24h 초과 파일만 만료 식별. 23h 파일은 보존."""
    now = time.time()
    fresh = tmp_path / "fresh.json"
    expired = tmp_path / "expired.json"
    fresh.write_text("{}")
    expired.write_text("{}")
    import os
    os.utime(fresh, (now - 23 * 3600, now - 23 * 3600))
    os.utime(expired, (now - 25 * 3600, now - 25 * 3600))

    result = find_expired_files(tmp_path, now=now)
    assert expired in result
    assert fresh not in result


def test_run_janitor_deletes_expired(tmp_path):
    """run_janitor가 만료 파일 실 삭제 + 보고서 생성."""
    now = time.time()
    expired = tmp_path / "old.json"
    fresh = tmp_path / "new.json"
    expired.write_text("{}")
    fresh.write_text("{}")
    import os
    os.utime(expired, (now - 48 * 3600, now - 48 * 3600))

    report = run_janitor(tmp_path, now=now)
    assert isinstance(report, JanitorReport)
    assert report.expired_files == 1
    assert report.deleted_files == 1
    assert not expired.exists()
    assert fresh.exists()


def test_run_janitor_dry_run_no_delete(tmp_path):
    """dry_run=True 시 통계만 수집, 파일 삭제 X."""
    now = time.time()
    expired = tmp_path / "old.json"
    expired.write_text("{}")
    import os
    os.utime(expired, (now - 48 * 3600, now - 48 * 3600))

    report = run_janitor(tmp_path, dry_run=True, now=now)
    assert report.expired_files == 1
    assert report.deleted_files == 0
    assert expired.exists()  # 보존됨 (dry_run)


def test_should_alert_disk_full_threshold():
    """잔여 크기 임계 초과 시 알람 — 청소 미작동 신호."""
    big_report = JanitorReport(
        total_files=1000, expired_files=0, deleted_files=0,
        freed_bytes=0, remaining_bytes=600 * 1024 * 1024,
        oldest_age_sec=0, errors=[],
    )
    assert should_alert_disk_full(big_report) is True

    small_report = JanitorReport(
        total_files=10, expired_files=0, deleted_files=0,
        freed_bytes=0, remaining_bytes=1024,
        oldest_age_sec=0, errors=[],
    )
    assert should_alert_disk_full(small_report) is False


def test_pipa_21_principle_documented():
    """cache_janitor.py docstring에 §7.2.12 + 24h TTL 명시 (PIPA §21 정합)."""
    from engine.safety.input_guards import cache_janitor
    doc = cache_janitor.__doc__ or ""
    assert "§7.2.12" in doc
    assert "24시간" in doc
