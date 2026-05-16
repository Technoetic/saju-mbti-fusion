"""engine.safety.slo — §7.3.2 SLO 측정 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _make_event(event_type: str, **kw):
    base = {
        "service": "face_reading",
        "event": event_type,
        "elapsed_ms": kw.pop("elapsed_ms", 100),
    }
    base.update(kw)
    return base


# ─────────────────────────── parse_log_line ───────────────────────────

def test_parse_log_line_valid():
    from engine.safety.slo import parse_log_line
    line = '{"service":"face_reading","event":"request_completed","elapsed_ms":200}'
    d = parse_log_line(line)
    assert d["event"] == "request_completed"


def test_parse_log_line_invalid():
    from engine.safety.slo import parse_log_line
    assert parse_log_line("not json") is None
    assert parse_log_line("") is None
    assert parse_log_line("INFO: server started") is None


def test_parse_log_line_array_returns_none():
    from engine.safety.slo import parse_log_line
    assert parse_log_line('["array"]') is None


# ─────────────────────────── compute_slo ───────────────────────────

def test_compute_slo_empty():
    from engine.safety.slo import compute_slo
    s = compute_slo([])
    assert s["request_count"] == 0
    assert s["crisis_rate"] == 0.0
    assert s["err_rate"] == 0.0
    assert s["cache_hit_rate"] == 0.0


def test_compute_slo_basic_counts():
    from engine.safety.slo import compute_slo
    events = [
        _make_event("request_completed", elapsed_ms=100),
        _make_event("request_completed", elapsed_ms=200),
        _make_event("err_rejected", error_code="ERR_FACE_NOT_DETECTED"),
        _make_event("crisis_blocked"),
        _make_event("cached_hit", elapsed_ms=10),
    ]
    s = compute_slo(events)
    assert s["request_count"] == 5
    assert s["crisis_rate"] == 0.2  # 1/5
    assert s["err_rate"] == 0.2     # 1/5


def test_compute_slo_cache_hit_rate():
    """cache_hit_rate = cached / (cached + completed)."""
    from engine.safety.slo import compute_slo
    events = [
        _make_event("cached_hit"),
        _make_event("cached_hit"),
        _make_event("request_completed"),
        _make_event("err_rejected", error_code="X"),  # 분모에 포함 안 됨
    ]
    s = compute_slo(events)
    assert s["cache_hit_rate"] == round(2 / 3, 4)


def test_compute_slo_latency_percentiles():
    from engine.safety.slo import compute_slo
    events = [_make_event("request_completed", elapsed_ms=i * 100) for i in range(1, 101)]
    s = compute_slo(events)
    # 100개 샘플, 값 100~10000. 단순 백분위 (round(p/100·(n-1))).
    assert 4900 <= s["latency_ms"]["p50"] <= 5200
    assert s["latency_ms"]["p95"] >= 9000
    assert s["latency_ms"]["p99"] >= 9800


def test_compute_slo_error_code_distribution():
    from engine.safety.slo import compute_slo
    events = [
        _make_event("err_rejected", error_code="ERR_FACE_NOT_DETECTED"),
        _make_event("err_rejected", error_code="ERR_FACE_NOT_DETECTED"),
        _make_event("err_rejected", error_code="ERR_FACE_MULTIPLE"),
        _make_event("request_completed", error_code="WARN_FACE_FLAT"),
    ]
    s = compute_slo(events)
    assert s["error_code_distribution"]["ERR_FACE_NOT_DETECTED"] == 2
    assert s["error_code_distribution"]["ERR_FACE_MULTIPLE"] == 1
    assert s["error_code_distribution"]["WARN_FACE_FLAT"] == 1


def test_compute_slo_region_distribution():
    from engine.safety.slo import compute_slo
    events = [
        _make_event("request_completed", region="KR"),
        _make_event("request_completed", region="KR"),
        _make_event("request_completed", region="US-CA"),
    ]
    s = compute_slo(events)
    assert s["region_distribution"] == {"KR": 2, "US-CA": 1}


def test_compute_slo_language_age_distribution():
    from engine.safety.slo import compute_slo
    events = [
        _make_event("request_completed", detected_language="ko", age_bucket="20s"),
        _make_event("request_completed", detected_language="en", age_bucket="30s"),
        _make_event("request_completed", detected_language="ko", age_bucket="30s"),
    ]
    s = compute_slo(events)
    assert s["language_distribution"] == {"ko": 2, "en": 1}
    assert s["age_bucket_distribution"] == {"20s": 1, "30s": 2}


def test_compute_slo_ignores_non_face_reading():
    """service 필드가 다르면 무시."""
    from engine.safety.slo import compute_slo
    events = [
        _make_event("request_completed"),
        {"service": "saju", "event": "request_completed"},  # 무시
    ]
    s = compute_slo(events)
    assert s["request_count"] == 1


# ─────────────────────────── SLO 위반 감지 ───────────────────────────

def test_slo_violation_crisis_rate():
    """crisis_rate > 0.05 → 위반 감지."""
    from engine.safety.slo import compute_slo
    events = [_make_event("crisis_blocked") for _ in range(10)] + \
             [_make_event("request_completed") for _ in range(50)]
    s = compute_slo(events)
    assert any("crisis_rate" in v for v in s["slo_violations"])


def test_slo_violation_p95_latency():
    """p95 > 5000ms → 위반."""
    from engine.safety.slo import compute_slo
    events = [_make_event("request_completed", elapsed_ms=10000) for _ in range(100)]
    s = compute_slo(events)
    assert any("p95" in v for v in s["slo_violations"])


def test_slo_no_violation_when_healthy():
    """정상 트래픽 — 위반 없음."""
    from engine.safety.slo import compute_slo
    events = [
        _make_event("request_completed", elapsed_ms=200),
        _make_event("request_completed", elapsed_ms=500),
        _make_event("cached_hit", elapsed_ms=20),
    ]
    s = compute_slo(events)
    assert s["slo_violations"] == []


# ─────────────────────────── compute_slo_from_lines (라인 파싱) ───────────────────────────

def test_compute_slo_from_lines_skips_non_json():
    """JSON 아닌 라인은 자동 스킵."""
    from engine.safety.slo import compute_slo_from_lines
    lines = [
        "INFO: Started server",
        '{"service":"face_reading","event":"request_completed","elapsed_ms":100}',
        "Mounting volume...",
        '{"service":"face_reading","event":"crisis_blocked","elapsed_ms":50}',
        "",
    ]
    s = compute_slo_from_lines(lines)
    assert s["request_count"] == 2
    assert s["crisis_rate"] == 0.5


def test_engine_safety_exports_slo():
    import engine.safety as safety
    assert hasattr(safety, "compute_slo")
    assert hasattr(safety, "parse_log_line")
    assert hasattr(safety, "SLO_THRESHOLDS")
    assert hasattr(safety, "compute_slo_from_lines")
