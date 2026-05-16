"""Repository 패턴 — 도메인별 CRUD 캡슐화.

각 Repo는 도메인 의미에 맞는 메서드만 노출. 직접 SQL 사용 금지 (테스트 용이).
"""

from __future__ import annotations
import json
from datetime import datetime, timezone, timedelta
from typing import Any

from engine.storage.db import get_connection, new_id


_KST = timezone(timedelta(hours=9))


def _now_iso() -> str:
    return datetime.now(_KST).isoformat()


def _maybe_json_dumps(v: Any) -> str | None:
    if v is None:
        return None
    return json.dumps(v, ensure_ascii=False)


def _maybe_json_loads(v: str | None) -> Any:
    if not v:
        return None
    try:
        return json.loads(v)
    except json.JSONDecodeError:
        return None


# ─────────────────────────── UserRepo ───────────────────────────
class UserRepo:
    """익명 사용자 관리."""

    @staticmethod
    def get_or_create(user_id: str, **profile: Any) -> dict[str, Any]:
        """존재하면 last_seen 갱신, 없으면 새로 생성. profile은 선택."""
        now = _now_iso()
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE users SET last_seen_iso = ? WHERE user_id = ?",
                    (now, user_id),
                )
            else:
                conn.execute(
                    """INSERT INTO users
                        (user_id, created_at_iso, last_seen_iso,
                         gender, age, occupation, mbti, day_master, yongsin,
                         consent_sensitive, consent_at_iso)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NULL)""",
                    (
                        user_id, now, now,
                        profile.get("gender"),
                        profile.get("age"),
                        profile.get("occupation"),
                        profile.get("mbti"),
                        profile.get("day_master"),
                        profile.get("yongsin"),
                    ),
                )
        # 별도 트랜잭션에서 프로필 갱신 (기존 유저인 경우)
        if profile:
            UserRepo.update_profile(user_id, **profile)
        return UserRepo.get(user_id) or {}

    @staticmethod
    def get(user_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def update_profile(user_id: str, **profile: Any) -> None:
        """프로필 필드 부분 갱신."""
        allowed = {"gender", "age", "occupation", "mbti", "day_master", "yongsin"}
        updates = {k: v for k, v in profile.items() if k in allowed and v is not None}
        if not updates:
            return
        sets = ", ".join(f"{k} = ?" for k in updates)
        params = list(updates.values()) + [user_id]
        with get_connection() as conn:
            conn.execute(f"UPDATE users SET {sets} WHERE user_id = ?", params)

    @staticmethod
    def set_consent(user_id: str, consent: bool) -> None:
        """민감정보 동의 기록."""
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET consent_sensitive = ?, consent_at_iso = ? WHERE user_id = ?",
                (1 if consent else 0, _now_iso() if consent else None, user_id),
            )

    @staticmethod
    def delete(user_id: str) -> dict[str, Any]:
        """사용자 + 모든 종속 데이터 삭제 (개인정보보호법 삭제권)."""
        with get_connection() as conn:
            # FK CASCADE로 모든 관련 데이터 자동 삭제
            cur = conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            return {"deleted": cur.rowcount > 0, "user_id": user_id}


# ─────────────────────────── DreamDiaryRepo ───────────────────────────
class DreamDiaryRepo:
    """Schredl Diary + 묘에 통합 일기."""

    @staticmethod
    def add(
        user_id: str,
        *,
        narrative_text: str,
        recall_quality: int = 3,
        vividness: int = 3,
        valence: int = 0,
        lucidity: int = 0,
        wake_time_iso: str | None = None,
        sleep_duration_min: int | None = None,
        characters: list[Any] | None = None,
        settings: list[str] | None = None,
        activities: list[str] | None = None,
        emotions: dict[str, Any] | None = None,
        analysis_summary: dict[str, Any] | None = None,
        # 묘에 필드
        core_image: str | None = None,
        felt_meaning: str | None = None,
        spiritual_resonance: str | None = None,
        next_intention: str | None = None,
    ) -> str:
        """일기 저장 → diary_id 반환."""
        diary_id = new_id()
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO dream_diary
                    (diary_id, user_id, created_at_iso, wake_time_iso, sleep_duration_min,
                     recall_quality, vividness, valence, lucidity, narrative_text,
                     characters_json, settings_json, activities_json, emotions_json,
                     analysis_summary_json,
                     core_image, felt_meaning, spiritual_resonance, next_intention)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    diary_id, user_id, _now_iso(), wake_time_iso, sleep_duration_min,
                    recall_quality, vividness, valence, lucidity, narrative_text,
                    _maybe_json_dumps(characters),
                    _maybe_json_dumps(settings),
                    _maybe_json_dumps(activities),
                    _maybe_json_dumps(emotions),
                    _maybe_json_dumps(analysis_summary),
                    core_image, felt_meaning, spiritual_resonance, next_intention,
                ),
            )
        return diary_id

    @staticmethod
    def list_recent(user_id: str, days: int = 14, limit: int = 60) -> list[dict[str, Any]]:
        """최근 N일치 일기 (최신순)."""
        cutoff = (datetime.now(_KST) - timedelta(days=days)).isoformat()
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM dream_diary
                   WHERE user_id = ? AND created_at_iso >= ?
                   ORDER BY created_at_iso DESC LIMIT ?""",
                (user_id, cutoff, limit),
            ).fetchall()
            return [_dream_row_to_dict(r) for r in rows]

    @staticmethod
    def list_all(user_id: str, limit: int = 200) -> list[dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM dream_diary WHERE user_id = ?
                   ORDER BY created_at_iso DESC LIMIT ?""",
                (user_id, limit),
            ).fetchall()
            return [_dream_row_to_dict(r) for r in rows]

    @staticmethod
    def get(user_id: str, diary_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM dream_diary WHERE user_id = ? AND diary_id = ?",
                (user_id, diary_id),
            ).fetchone()
            return _dream_row_to_dict(row) if row else None

    @staticmethod
    def delete(user_id: str, diary_id: str) -> bool:
        with get_connection() as conn:
            cur = conn.execute(
                "DELETE FROM dream_diary WHERE user_id = ? AND diary_id = ?",
                (user_id, diary_id),
            )
            return cur.rowcount > 0


def _dream_row_to_dict(row: Any) -> dict[str, Any]:
    if not row:
        return {}
    d = dict(row)
    d["characters"] = _maybe_json_loads(d.pop("characters_json", None))
    d["settings"] = _maybe_json_loads(d.pop("settings_json", None))
    d["activities"] = _maybe_json_loads(d.pop("activities_json", None))
    d["emotions"] = _maybe_json_loads(d.pop("emotions_json", None))
    d["analysis_summary"] = _maybe_json_loads(d.pop("analysis_summary_json", None))
    return d


# ─────────────────────────── ClinicalLogRepo ───────────────────────────
class ClinicalLogRepo:
    """임상 척도 채점 종단 로그."""

    @staticmethod
    def add(
        user_id: str,
        instrument: str,
        result: dict[str, Any],
        responses: Any | None = None,
    ) -> str:
        log_id = new_id()
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO clinical_log
                    (log_id, user_id, created_at_iso, instrument,
                     total_score, severity, cutoff, exceeded_cutoff,
                     suicide_alert, responses_json, raw_result_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    log_id, user_id, _now_iso(), instrument,
                    int(result.get("total_score", 0)),
                    result.get("severity"),
                    result.get("cutoff"),
                    1 if result.get("exceeded_cutoff") else 0,
                    1 if result.get("suicide_alert") else 0,
                    _maybe_json_dumps(responses),
                    _maybe_json_dumps(result),
                ),
            )
        return log_id

    @staticmethod
    def history(
        user_id: str,
        instrument: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        with get_connection() as conn:
            if instrument:
                rows = conn.execute(
                    """SELECT * FROM clinical_log
                       WHERE user_id = ? AND instrument = ?
                       ORDER BY created_at_iso DESC LIMIT ?""",
                    (user_id, instrument, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM clinical_log
                       WHERE user_id = ?
                       ORDER BY created_at_iso DESC LIMIT ?""",
                    (user_id, limit),
                ).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["responses"] = _maybe_json_loads(d.pop("responses_json", None))
                d["raw_result"] = _maybe_json_loads(d.pop("raw_result_json", None))
                results.append(d)
            return results

    @staticmethod
    def trend(user_id: str, instrument: str) -> dict[str, Any]:
        """척도 점수 추세 — 첫 측정 vs 최근."""
        hist = ClinicalLogRepo.history(user_id, instrument=instrument, limit=50)
        if not hist:
            return {"trend": "no_data", "count": 0}
        # 시간순 오름차순
        hist.sort(key=lambda x: x["created_at_iso"])
        first = hist[0]
        last = hist[-1]
        delta = last["total_score"] - first["total_score"]
        return {
            "count": len(hist),
            "first_score": first["total_score"],
            "first_date": first["created_at_iso"],
            "latest_score": last["total_score"],
            "latest_date": last["created_at_iso"],
            "delta": delta,
            "trend": (
                "개선" if delta < -2 else
                "악화" if delta > 2 else
                "안정"
            ),
            "all_scores": [(h["created_at_iso"], h["total_score"]) for h in hist],
        }


# ─────────────────────────── IRTSessionRepo ───────────────────────────
class IRTSessionRepo:
    """IRT 6단계 세션 영구 보관."""

    @staticmethod
    def create(user_id: str) -> str:
        sid = new_id()
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO irt_session
                    (session_id, user_id, started_at_iso, current_step, state_json)
                   VALUES (?, ?, ?, 1, '{}')""",
                (sid, user_id, _now_iso()),
            )
        return sid

    @staticmethod
    def get(user_id: str, session_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            row = conn.execute(
                """SELECT * FROM irt_session
                   WHERE user_id = ? AND session_id = ?""",
                (user_id, session_id),
            ).fetchone()
            if not row:
                return None
            d = dict(row)
            d["state"] = _maybe_json_loads(d.pop("state_json", None)) or {}
            return d

    @staticmethod
    def update(
        user_id: str,
        session_id: str,
        *,
        current_step: int | None = None,
        target_nightmare_text: str | None = None,
        chosen_rescript: str | None = None,
        baseline_freq_per_week: float | None = None,
        week8_freq_per_week: float | None = None,
        outcome_verdict: str | None = None,
        completed: bool = False,
        state_patch: dict[str, Any] | None = None,
    ) -> None:
        current = IRTSessionRepo.get(user_id, session_id)
        if not current:
            return
        state = current["state"]
        if state_patch:
            state.update(state_patch)
        new_step = current_step if current_step is not None else current["current_step"]
        new_target = target_nightmare_text if target_nightmare_text is not None else current["target_nightmare_text"]
        new_rescript = chosen_rescript if chosen_rescript is not None else current["chosen_rescript"]
        new_baseline = baseline_freq_per_week if baseline_freq_per_week is not None else current["baseline_freq_per_week"]
        new_week8 = week8_freq_per_week if week8_freq_per_week is not None else current["week8_freq_per_week"]
        new_verdict = outcome_verdict if outcome_verdict is not None else current["outcome_verdict"]
        completed_at = _now_iso() if completed else current["completed_at_iso"]

        with get_connection() as conn:
            conn.execute(
                """UPDATE irt_session SET
                    current_step = ?, target_nightmare_text = ?, chosen_rescript = ?,
                    baseline_freq_per_week = ?, week8_freq_per_week = ?,
                    outcome_verdict = ?, completed_at_iso = ?, state_json = ?
                   WHERE user_id = ? AND session_id = ?""",
                (
                    new_step, new_target, new_rescript,
                    new_baseline, new_week8, new_verdict,
                    completed_at, _maybe_json_dumps(state),
                    user_id, session_id,
                ),
            )

    @staticmethod
    def list_user(user_id: str) -> list[dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM irt_session WHERE user_id = ? ORDER BY started_at_iso DESC",
                (user_id,),
            ).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["state"] = _maybe_json_loads(d.pop("state_json", None)) or {}
                results.append(d)
            return results


# ─────────────────────────── MyoeDiaryRepo (DreamDiary 위의 헬퍼) ───────────────────────────
class MyoeDiaryRepo:
    """묘에 장기 일기 — DreamDiary의 묘에 필드만 쿼리."""

    @staticmethod
    def list_for_analysis(user_id: str, days: int = 30, limit: int = 60) -> list[dict[str, Any]]:
        diaries = DreamDiaryRepo.list_recent(user_id, days=days, limit=limit)
        # 묘에 분석에 필요한 최소 필드만 추출
        return [
            {
                "date_iso": d["created_at_iso"],
                "narrative_text": d["narrative_text"],
                "core_image": d.get("core_image"),
                "valence": d["valence"],
                "felt_meaning": d.get("felt_meaning"),
            }
            for d in diaries
        ]


# ─────────────────────────── LearningLogRepo (Stickgold 72h) ───────────────────────────
class LearningLogRepo:
    """학습/작업 로그 — Stickgold dream lag 매칭."""

    @staticmethod
    def add(
        user_id: str,
        activity_text: str,
        domain: str | None = None,
        activity_at_iso: str | None = None,
    ) -> str:
        log_id = new_id()
        activity_time = activity_at_iso or _now_iso()
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO learning_log
                    (log_id, user_id, activity_text, domain, activity_at_iso, logged_at_iso)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (log_id, user_id, activity_text, domain, activity_time, _now_iso()),
            )
        return log_id

    @staticmethod
    def list_recent_72h(user_id: str) -> list[dict[str, Any]]:
        """72시간 이내 학습 활동 — Stickgold dream lag window."""
        cutoff = (datetime.now(_KST) - timedelta(hours=72)).isoformat()
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM learning_log
                   WHERE user_id = ? AND activity_at_iso >= ?
                   ORDER BY activity_at_iso DESC""",
                (user_id, cutoff),
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def list_with_ages(user_id: str, hours_back: int = 168) -> tuple[list[str], list[int]]:
        """detect_memory_consolidation에 전달할 형식: (activities, ages_hours)."""
        cutoff = (datetime.now(_KST) - timedelta(hours=hours_back)).isoformat()
        now = datetime.now(_KST)
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT activity_text, activity_at_iso FROM learning_log
                   WHERE user_id = ? AND activity_at_iso >= ?
                   ORDER BY activity_at_iso DESC""",
                (user_id, cutoff),
            ).fetchall()
        activities: list[str] = []
        ages: list[int] = []
        for r in rows:
            activities.append(r["activity_text"])
            try:
                t = datetime.fromisoformat(r["activity_at_iso"])
                age_h = int((now - t).total_seconds() // 3600)
            except (ValueError, TypeError):
                age_h = 999
            ages.append(age_h)
        return activities, ages


__all__ = [
    "UserRepo",
    "DreamDiaryRepo",
    "ClinicalLogRepo",
    "IRTSessionRepo",
    "MyoeDiaryRepo",
    "LearningLogRepo",
]
