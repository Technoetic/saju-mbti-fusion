"""운영 — 에러 로그 영구화 + DB 백업 스냅샷 + 위기 익명 통계.

신규 테이블 3개를 동일 SQLite에 추가 (마이그레이션 idempotent).
"""

from __future__ import annotations
import json
import shutil
import gzip
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from engine.storage.db import get_connection, DB_PATH, new_id


_KST = timezone(timedelta(hours=9))


def _now_iso() -> str:
    return datetime.now(_KST).isoformat()


# ─────────────────────────── 마이그레이션 ───────────────────────────
_OPS_SCHEMA = """
CREATE TABLE IF NOT EXISTS error_log (
    error_id        TEXT PRIMARY KEY,
    created_at_iso  TEXT NOT NULL,
    source          TEXT NOT NULL,  -- 'client' | 'server' | 'llm' | 'db'
    msg             TEXT NOT NULL,
    stack           TEXT,
    url             TEXT,
    user_agent      TEXT,
    user_id         TEXT,  -- 익명 ID, 선택
    severity        TEXT DEFAULT 'error'  -- 'info'|'warn'|'error'|'fatal'
);
CREATE INDEX IF NOT EXISTS idx_error_created ON error_log(created_at_iso DESC);
CREATE INDEX IF NOT EXISTS idx_error_severity ON error_log(severity);

CREATE TABLE IF NOT EXISTS crisis_stats (
    stat_id         TEXT PRIMARY KEY,
    created_at_iso  TEXT NOT NULL,
    severity        TEXT NOT NULL,  -- 'direct'|'indirect'|'planning'
    matched_count   INTEGER NOT NULL,
    -- 익명화: 사용자 ID도, 텍스트도 저장하지 않음. 카운터만.
    endpoint        TEXT NOT NULL  -- 'dream'|'hwapae'|'saju_ask'
);
CREATE INDEX IF NOT EXISTS idx_crisis_created ON crisis_stats(created_at_iso DESC);

CREATE TABLE IF NOT EXISTS rate_limit_log (
    log_id          TEXT PRIMARY KEY,
    created_at_iso  TEXT NOT NULL,
    user_id         TEXT NOT NULL,
    endpoint        TEXT NOT NULL,
    count_in_window INTEGER NOT NULL,
    window_sec      INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ratelimit_user ON rate_limit_log(user_id, created_at_iso DESC);
"""


_ops_initialized = False


def init_ops_tables() -> None:
    global _ops_initialized
    if _ops_initialized:
        return
    import sqlite3
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(_OPS_SCHEMA)
    finally:
        conn.close()
    _ops_initialized = True


# ─────────────────────────── 에러 로그 영구화 ───────────────────────────
class ErrorLogRepo:
    @staticmethod
    def add(
        msg: str,
        source: str = "client",
        *,
        stack: str | None = None,
        url: str | None = None,
        user_agent: str | None = None,
        user_id: str | None = None,
        severity: str = "error",
    ) -> str:
        init_ops_tables()
        eid = new_id()
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO error_log
                    (error_id, created_at_iso, source, msg, stack, url, user_agent, user_id, severity)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (eid, _now_iso(), source, (msg or "")[:1000],
                 (stack or "")[:3000] if stack else None,
                 (url or "")[:500] if url else None,
                 (user_agent or "")[:500] if user_agent else None,
                 user_id, severity),
            )
        return eid

    @staticmethod
    def recent(limit: int = 100, severity: str | None = None) -> list[dict[str, Any]]:
        init_ops_tables()
        with get_connection() as conn:
            if severity:
                rows = conn.execute(
                    "SELECT * FROM error_log WHERE severity = ? ORDER BY created_at_iso DESC LIMIT ?",
                    (severity, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM error_log ORDER BY created_at_iso DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def cleanup_old(days: int = 30) -> int:
        """N일 이전 에러 로그 삭제."""
        init_ops_tables()
        cutoff = (datetime.now(_KST) - timedelta(days=days)).isoformat()
        with get_connection() as conn:
            cur = conn.execute(
                "DELETE FROM error_log WHERE created_at_iso < ?", (cutoff,)
            )
            return cur.rowcount


# ─────────────────────────── 위기 익명 통계 (PRIVACY_POLICY §5) ───────────────────────────
class CrisisStatsRepo:
    """위기 신호 익명 카운터. 사용자 ID·텍스트 저장 X — 통계만."""

    @staticmethod
    def add(severity: str, matched_count: int, endpoint: str) -> None:
        init_ops_tables()
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO crisis_stats
                    (stat_id, created_at_iso, severity, matched_count, endpoint)
                   VALUES (?, ?, ?, ?, ?)""",
                (new_id(), _now_iso(), severity, matched_count, endpoint),
            )

    @staticmethod
    def summary(days: int = 30) -> dict[str, Any]:
        """N일 통계."""
        init_ops_tables()
        cutoff = (datetime.now(_KST) - timedelta(days=days)).isoformat()
        with get_connection() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM crisis_stats WHERE created_at_iso >= ?",
                (cutoff,),
            ).fetchone()[0]
            by_severity = dict(conn.execute(
                """SELECT severity, COUNT(*) FROM crisis_stats
                   WHERE created_at_iso >= ? GROUP BY severity""",
                (cutoff,),
            ).fetchall())
            by_endpoint = dict(conn.execute(
                """SELECT endpoint, COUNT(*) FROM crisis_stats
                   WHERE created_at_iso >= ? GROUP BY endpoint""",
                (cutoff,),
            ).fetchall())
        return {
            "days": days,
            "total": total,
            "by_severity": by_severity,
            "by_endpoint": by_endpoint,
        }

    @staticmethod
    def cleanup_old(days: int = 30) -> int:
        """PRIVACY_POLICY §5: 위기 익명 로그 30일만 보관."""
        init_ops_tables()
        cutoff = (datetime.now(_KST) - timedelta(days=days)).isoformat()
        with get_connection() as conn:
            cur = conn.execute(
                "DELETE FROM crisis_stats WHERE created_at_iso < ?", (cutoff,)
            )
            return cur.rowcount


# ─────────────────────────── Rate Limit 로그 (사용자별 비용 가드) ───────────────────────────
class RateLimitRepo:
    """사용자별 v2 호출 일일 카운터. 비용 폭증 방지."""

    @staticmethod
    def check_and_record(
        user_id: str,
        endpoint: str,
        *,
        daily_limit: int = 20,
        window_sec: int = 86400,
    ) -> dict[str, Any]:
        """N초 윈도 안 user_id 호출 카운트 → 한도 초과 여부 반환."""
        init_ops_tables()
        cutoff = (datetime.now(_KST) - timedelta(seconds=window_sec)).isoformat()
        with get_connection() as conn:
            n = conn.execute(
                """SELECT COUNT(*) FROM rate_limit_log
                   WHERE user_id = ? AND endpoint = ? AND created_at_iso >= ?""",
                (user_id, endpoint, cutoff),
            ).fetchone()[0]
            if n >= daily_limit:
                return {
                    "allowed": False,
                    "count": n,
                    "limit": daily_limit,
                    "reset_after_sec": window_sec,
                    "reason": f"일일 한도 {daily_limit}회 초과 ({n}회 사용)",
                }
            conn.execute(
                """INSERT INTO rate_limit_log
                    (log_id, created_at_iso, user_id, endpoint, count_in_window, window_sec)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (new_id(), _now_iso(), user_id, endpoint, n + 1, window_sec),
            )
            return {"allowed": True, "count": n + 1, "limit": daily_limit}

    @staticmethod
    def cleanup_old(days: int = 7) -> int:
        init_ops_tables()
        cutoff = (datetime.now(_KST) - timedelta(days=days)).isoformat()
        with get_connection() as conn:
            cur = conn.execute(
                "DELETE FROM rate_limit_log WHERE created_at_iso < ?", (cutoff,)
            )
            return cur.rowcount


# ─────────────────────────── DB 백업 ───────────────────────────
def backup_db(*, max_keep: int = 7) -> dict[str, Any]:
    """SQLite 원본을 gzip 압축 → /data/backups/ (최근 7개 보관).

    SQLite의 .backup API는 sqlite3 모듈에 있으나 simple file copy도 OK
    (WAL 모드에서도 일관성 보장 — checkpoint 후 복사).
    """
    src = Path(DB_PATH)
    if not src.exists():
        return {"ok": False, "reason": "DB 파일 없음"}

    backup_dir = src.parent / "backups"
    backup_dir.mkdir(exist_ok=True)

    ts = datetime.now(_KST).strftime("%Y%m%d-%H%M%S")
    dest = backup_dir / f"app-{ts}.db.gz"

    # WAL checkpoint 후 copy
    import sqlite3
    conn = sqlite3.connect(src)
    try:
        conn.execute("PRAGMA wal_checkpoint(FULL);")
    finally:
        conn.close()

    with open(src, "rb") as fin, gzip.open(dest, "wb", compresslevel=6) as fout:
        shutil.copyfileobj(fin, fout)

    # 오래된 백업 정리
    backups = sorted(backup_dir.glob("app-*.db.gz"), reverse=True)
    deleted: list[str] = []
    for old in backups[max_keep:]:
        try:
            old.unlink()
            deleted.append(old.name)
        except Exception:
            pass

    return {
        "ok": True,
        "backup_path": str(dest),
        "size_bytes": dest.stat().st_size,
        "kept": [b.name for b in backups[:max_keep]],
        "deleted": deleted,
    }


__all__ = [
    "init_ops_tables",
    "ErrorLogRepo",
    "CrisisStatsRepo",
    "RateLimitRepo",
    "backup_db",
]
