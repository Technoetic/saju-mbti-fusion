"""SQLite 연결·스키마·마이그레이션 — Python 표준 sqlite3.

Railway 영구 볼륨 경로 우선, 없으면 step_archive/data/ fallback.
WAL 모드로 동시 읽기 성능 보장.
"""

from __future__ import annotations
import os
import sqlite3
import uuid
from pathlib import Path
from contextlib import contextmanager
from typing import Iterator


# ─────────────────────────── 경로 결정 ───────────────────────────
def _resolve_db_path() -> Path:
    """Railway 환경변수 DB_PATH 우선, 없으면 프로젝트 내 data/ 사용."""
    env_path = os.environ.get("DREAM_APP_DB_PATH")
    if env_path:
        p = Path(env_path)
    else:
        # 프로젝트 루트 기준 data/ (Railway는 볼륨을 마운트해야 함)
        project_root = Path(__file__).resolve().parent.parent.parent
        p = project_root / "data" / "app.db"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


DB_PATH = _resolve_db_path()


# ─────────────────────────── 스키마 정의 ───────────────────────────
_SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id        TEXT PRIMARY KEY,
    created_at_iso TEXT NOT NULL,
    last_seen_iso  TEXT,
    -- 개인 맥락 (선택, 클라이언트에서도 보관)
    gender         TEXT,
    age            INTEGER,
    occupation     TEXT,
    mbti           TEXT,
    -- 사주 맥락
    day_master     TEXT,
    yongsin        TEXT,
    -- 민감정보 동의
    consent_sensitive    INTEGER NOT NULL DEFAULT 0,
    consent_at_iso       TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_created ON users(created_at_iso);

-- ─────────── #22 Schredl Diary 표준 일기 ───────────
CREATE TABLE IF NOT EXISTS dream_diary (
    diary_id        TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    created_at_iso  TEXT NOT NULL,
    wake_time_iso   TEXT,
    sleep_duration_min INTEGER,
    -- Schredl 핵심 척도
    recall_quality  INTEGER NOT NULL CHECK (recall_quality BETWEEN 1 AND 5),
    vividness       INTEGER NOT NULL CHECK (vividness BETWEEN 1 AND 5),
    valence         INTEGER NOT NULL CHECK (valence BETWEEN -3 AND 3),
    lucidity        INTEGER NOT NULL CHECK (lucidity BETWEEN 0 AND 5),
    narrative_text  TEXT NOT NULL,
    -- HvDC 호환 태그 (JSON)
    characters_json TEXT,
    settings_json   TEXT,
    activities_json TEXT,
    emotions_json   TEXT,
    -- 분석 캐시 (선택)
    analysis_summary_json TEXT,
    -- 묘에 호환 필드
    core_image      TEXT,
    felt_meaning    TEXT,
    spiritual_resonance TEXT,
    next_intention  TEXT
);

CREATE INDEX IF NOT EXISTS idx_diary_user_created ON dream_diary(user_id, created_at_iso DESC);

-- ─────────── #23·#26 임상 척도 종단 로그 ───────────
CREATE TABLE IF NOT EXISTS clinical_log (
    log_id          TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    created_at_iso  TEXT NOT NULL,
    instrument      TEXT NOT NULL,  -- 'ces_d' | 'bdi_k' | 'stai_k_state' | 'psqi' | 'isi'
    total_score     INTEGER NOT NULL,
    severity        TEXT,
    cutoff          INTEGER,
    exceeded_cutoff INTEGER NOT NULL DEFAULT 0,
    suicide_alert   INTEGER NOT NULL DEFAULT 0,
    responses_json  TEXT,
    raw_result_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_clinical_user_inst ON clinical_log(user_id, instrument, created_at_iso DESC);

-- ─────────── #24 IRT 6단계 워크플로 ───────────
CREATE TABLE IF NOT EXISTS irt_session (
    session_id      TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    started_at_iso  TEXT NOT NULL,
    completed_at_iso TEXT,
    current_step    INTEGER NOT NULL DEFAULT 1,
    target_nightmare_text TEXT,
    chosen_rescript TEXT,
    baseline_freq_per_week REAL,
    week8_freq_per_week REAL,
    outcome_verdict TEXT,
    state_json      TEXT  -- baseline_nightmares, rehearsal_log 등 JSON
);

CREATE INDEX IF NOT EXISTS idx_irt_user_started ON irt_session(user_id, started_at_iso DESC);

-- ─────────── #16 묘에 장기 일기 (dream_diary 보조 — 묘에 전용 필드만) ───────────
-- 묘에 데이터는 dream_diary의 core_image / felt_meaning 등에 통합 저장

-- ─────────── #19 Stickgold 72h 학습 로그 ───────────
CREATE TABLE IF NOT EXISTS learning_log (
    log_id          TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    activity_text   TEXT NOT NULL,
    domain          TEXT,  -- 'procedural' | 'declarative' | 'social' | 'creative'
    activity_at_iso TEXT NOT NULL,
    logged_at_iso   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_learning_user_activity ON learning_log(user_id, activity_at_iso DESC);
"""


# ─────────────────────────── 초기화 + 연결 ───────────────────────────
_initialized = False


def init_db() -> None:
    """스키마 생성 (idempotent). 앱 시작 시 1회 호출."""
    global _initialized
    if _initialized:
        return
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(_SCHEMA_SQL)
    finally:
        conn.close()
    _initialized = True


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """컨텍스트 매니저 — auto commit/rollback. row_factory = Row."""
    if not _initialized:
        init_db()
    conn = sqlite3.connect(DB_PATH, isolation_level="DEFERRED")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def new_user_id() -> str:
    """익명 사용자 ID 생성."""
    return str(uuid.uuid4())


def new_id() -> str:
    """범용 레코드 ID."""
    return str(uuid.uuid4())


__all__ = [
    "DB_PATH",
    "init_db",
    "get_connection",
    "new_user_id",
    "new_id",
]
