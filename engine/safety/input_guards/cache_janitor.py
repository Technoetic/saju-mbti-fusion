"""캐시 만료 청소 — 운영표준 §7.2.12 본문화.

face_reading 캐시는 24시간 TTL이지만, face_reading.py의 _load_cache는 호출
시점에만 만료 확인을 하므로, 만료된 파일이 디스크에 남아 누적될 수 있다.
본 모듈은:
  1) 만료 파일 결정론 식별
  2) 안전 삭제 (dry-run 옵션)
  3) 통계 리포트 (older_than_24h / total / freed_bytes)
  4) §14.3 alert_router 호환 P2 알람 페이로드

§7.2.12는 단순히 청소만이 아니라, 디스크 가득참(p99 회귀의 흔한 원인)을
사전 차단하는 운영 보호막이다. 운영 워커(cron / k8s CronJob)가 5분 주기로
run_janitor()를 호출하도록 설계.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# §7.2.12 — 기본 TTL. face_reading._TTL_SEC와 동일.
DEFAULT_TTL_SEC = 24 * 3600

# §7.2.12 — 디스크 가득 알람 임계. 캐시 크기가 이 한도를 넘으면 P2 알람.
DISK_WARN_BYTES = 500 * 1024 * 1024  # 500MB


@dataclass(frozen=True)
class JanitorReport:
    """단일 실행 보고서.

    Attributes:
        total_files: 검사한 파일 수
        expired_files: 만료된 파일 수
        deleted_files: 실제 삭제된 수 (dry_run=False일 때)
        freed_bytes: 회수한 디스크 (바이트)
        remaining_bytes: 청소 후 디렉터리 총 크기
        oldest_age_sec: 가장 오래된 파일의 나이 (초)
        errors: 삭제 실패 사유 리스트
    """
    total_files: int
    expired_files: int
    deleted_files: int
    freed_bytes: int
    remaining_bytes: int
    oldest_age_sec: int
    errors: list[str]


# ─────────────────────────── 핵심 ───────────────────────────

def _iter_cache_files(cache_dir: Path) -> list[Path]:
    if not cache_dir.exists():
        return []
    return [p for p in cache_dir.iterdir() if p.is_file()]


def find_expired_files(
    cache_dir: Path,
    *,
    ttl_sec: int = DEFAULT_TTL_SEC,
    now: float | None = None,
) -> list[Path]:
    """TTL 초과 파일 목록 — 결정론. 부수효과 없음."""
    now = now if now is not None else time.time()
    cutoff = now - ttl_sec
    expired: list[Path] = []
    for p in _iter_cache_files(cache_dir):
        try:
            if p.stat().st_mtime < cutoff:
                expired.append(p)
        except OSError:
            # stat 실패는 다음 회차에 재시도
            continue
    return expired


def run_janitor(
    cache_dir: Path,
    *,
    ttl_sec: int = DEFAULT_TTL_SEC,
    dry_run: bool = False,
    now: float | None = None,
) -> JanitorReport:
    """캐시 디렉터리 청소.

    Args:
        cache_dir: 점검할 캐시 경로
        ttl_sec: 이보다 오래된 파일 삭제
        dry_run: True면 통계만 수집, 실제 삭제 X
        now: 시간 주입 (테스트용)
    """
    now = now if now is not None else time.time()
    all_files = _iter_cache_files(cache_dir)
    total_files = len(all_files)
    expired = find_expired_files(cache_dir, ttl_sec=ttl_sec, now=now)

    freed = 0
    deleted = 0
    errors: list[str] = []
    for p in expired:
        try:
            size = p.stat().st_size
            if not dry_run:
                p.unlink()
                deleted += 1
            freed += size
        except OSError as e:
            errors.append(f"{p.name}:{type(e).__name__}")

    # 청소 후 남은 크기 계산
    remaining = 0
    oldest_age = 0
    for p in _iter_cache_files(cache_dir):
        try:
            st = p.stat()
            remaining += st.st_size
            age = int(now - st.st_mtime)
            if age > oldest_age:
                oldest_age = age
        except OSError:
            continue

    return JanitorReport(
        total_files=total_files,
        expired_files=len(expired),
        deleted_files=deleted,
        freed_bytes=freed,
        remaining_bytes=remaining,
        oldest_age_sec=oldest_age,
        errors=errors,
    )


# ─────────────────────────── 알람 ───────────────────────────

def should_alert_disk_full(
    report: JanitorReport,
    *,
    warn_bytes: int = DISK_WARN_BYTES,
) -> bool:
    """청소 후에도 잔여 크기가 임계를 초과하면 알람."""
    return report.remaining_bytes >= warn_bytes


def to_alert_payload(
    report: JanitorReport,
    *,
    warn_bytes: int = DISK_WARN_BYTES,
) -> dict[str, Any]:
    """§14.3 alert_router 호환 페이로드 — P2 알람."""
    return {
        "service": "cache_janitor",
        "total_files": report.total_files,
        "expired_files": report.expired_files,
        "deleted_files": report.deleted_files,
        "freed_bytes": report.freed_bytes,
        "remaining_bytes": report.remaining_bytes,
        "oldest_age_sec": report.oldest_age_sec,
        "disk_warn_triggered": should_alert_disk_full(report, warn_bytes=warn_bytes),
        "error_count": len(report.errors),
    }


def to_trace_event(report: JanitorReport) -> dict[str, Any]:
    """§7.3.4 tracing 호환 페이로드 — emit_face_reading_event(extra=...)로 전달."""
    return {
        "cache_janitor_run": True,
        "cache_total_files": report.total_files,
        "cache_expired_files": report.expired_files,
        "cache_deleted_files": report.deleted_files,
        "cache_freed_bytes": report.freed_bytes,
        "cache_remaining_bytes": report.remaining_bytes,
    }
