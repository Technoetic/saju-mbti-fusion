"""engine.safety.misc.quick_check — §7.3.5 빠른 점검 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 전체 실행 ───────────────────────────

def test_run_quick_check_returns_top_level_keys():
    from engine.safety.misc.quick_check import run_quick_check
    r = run_quick_check()
    assert "timestamp_epoch" in r
    assert "status" in r
    assert "sections" in r
    assert isinstance(r["sections"], dict)


def test_run_quick_check_status_ok_in_clean_state():
    """기본 상태(이벤트 없음, 캐시 dir 존재)에서는 OK."""
    from engine.safety.misc.quick_check import run_quick_check
    r = run_quick_check()
    # CRITICAL은 절대 안 나와야 함 (안전 모듈 임포트 가능, 라우터 정상)
    assert r["status"] in {"OK", "WARN"}


def test_run_quick_check_all_sections_present():
    from engine.safety.misc.quick_check import run_quick_check
    r = run_quick_check()
    sections = r["sections"]
    for name in ("safety_imports", "cache_dir", "slo_window",
                 "alert_router", "rollback_policy", "emotion_disclosure"):
        assert name in sections, f"{name} section missing"


# ─────────────────────────── safety_imports ───────────────────────────

def test_safety_imports_all_modules_loadable():
    from engine.safety.misc.quick_check import run_quick_check
    r = run_quick_check()
    si = r["sections"]["safety_imports"]
    assert si["ok"] is True
    assert si["missing"] == []
    # 최소 14개 모듈 확인
    assert si["checked"] >= 14


# ─────────────────────────── cache_dir ───────────────────────────

def test_cache_dir_check_nonexistent_returns_not_ok(tmp_path):
    from engine.safety.misc.quick_check import run_quick_check
    fake = tmp_path / "nonexistent"
    r = run_quick_check(cache_dir=fake)
    assert r["sections"]["cache_dir"]["exists"] is False
    assert r["sections"]["cache_dir"]["ok"] is False


def test_cache_dir_check_empty_dir_is_ok(tmp_path):
    from engine.safety.misc.quick_check import run_quick_check
    empty = tmp_path / "empty"
    empty.mkdir()
    r = run_quick_check(cache_dir=empty)
    assert r["sections"]["cache_dir"]["exists"] is True
    assert r["sections"]["cache_dir"]["file_count"] == 0
    assert r["sections"]["cache_dir"]["ok"] is True


def test_cache_dir_check_reports_mtimes(tmp_path):
    from engine.safety.misc.quick_check import run_quick_check
    d = tmp_path / "cache"
    d.mkdir()
    (d / "a.json").write_text("{}")
    (d / "b.json").write_text("{}")
    r = run_quick_check(cache_dir=d)
    cd = r["sections"]["cache_dir"]
    assert cd["file_count"] == 2
    assert "oldest_mtime" in cd
    assert "newest_mtime" in cd


# ─────────────────────────── slo_window ───────────────────────────

def test_slo_window_without_events_only_checks_callable():
    from engine.safety.misc.quick_check import run_quick_check
    r = run_quick_check()
    sw = r["sections"]["slo_window"]
    assert sw["callable"] is True
    assert sw["request_count"] == 0
    assert sw["violations"] == []


def test_slo_window_with_violating_events_reports_them():
    from engine.safety.misc.quick_check import run_quick_check
    events = [
        {"service": "face_reading", "event": "crisis_blocked", "elapsed_ms": 50}
        for _ in range(10)
    ] + [
        {"service": "face_reading", "event": "request_completed", "elapsed_ms": 200}
        for _ in range(50)
    ]
    r = run_quick_check(events=events)
    sw = r["sections"]["slo_window"]
    assert sw["request_count"] == 60
    assert sw["crisis_rate"] > 0.05
    assert any("crisis_rate" in v for v in sw["violations"])


def test_quick_check_warn_when_slo_violations_present():
    from engine.safety.misc.quick_check import run_quick_check
    events = [
        {"service": "face_reading", "event": "request_completed", "elapsed_ms": 9000}
        for _ in range(100)
    ]  # p95 > 5000ms → 위반
    r = run_quick_check(events=events)
    assert r["status"] == "WARN"


# ─────────────────────────── alert_router ───────────────────────────

def test_alert_router_check_no_mismatches_when_intact():
    from engine.safety.misc.quick_check import run_quick_check
    r = run_quick_check()
    ar = r["sections"]["alert_router"]
    assert ar["ok"] is True
    assert ar["mismatches"] == {}


# ─────────────────────────── rollback_policy ───────────────────────────

def test_rollback_policy_check_no_mismatches_when_intact():
    from engine.safety.misc.quick_check import run_quick_check
    r = run_quick_check()
    rp = r["sections"]["rollback_policy"]
    assert rp["ok"] is True
    assert rp["mismatches"] == {}


# ─────────────────────────── emotion_disclosure ───────────────────────────

def test_emotion_disclosure_region_mapping_intact():
    from engine.safety.misc.quick_check import run_quick_check
    r = run_quick_check()
    ed = r["sections"]["emotion_disclosure"]
    assert ed["ok"] is True
    assert ed["failed"] == []


# ─────────────────────────── format ───────────────────────────

def test_format_text_contains_status_line():
    from engine.safety.misc.quick_check import run_quick_check, format_quick_check_text
    r = run_quick_check()
    text = format_quick_check_text(r)
    assert "face_reading quick_check" in text
    assert "STATUS=" in text
    # 각 섹션이 한 번씩 등장
    for name in ("safety_imports", "cache_dir", "slo_window",
                 "alert_router", "rollback_policy"):
        assert f"[{name}]" in text


def test_format_text_truncates_long_values():
    """긴 값은 ...로 잘려야 SSH 한 줄 가독성 유지."""
    from engine.safety.misc.quick_check import format_quick_check_text
    fake_report = {
        "timestamp_epoch": 1234.5,
        "status": "OK",
        "sections": {
            "test_section": {
                "ok": True,
                "huge_value": "X" * 500,
            }
        },
    }
    text = format_quick_check_text(fake_report)
    assert "..." in text  # 500자 X 라인이 잘림


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_quick_check():
    import engine.safety as safety
    assert hasattr(safety, "run_quick_check")
    assert hasattr(safety, "format_quick_check_text")
