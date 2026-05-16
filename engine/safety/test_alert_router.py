"""engine.safety.alert_router — §14.3 알람 라우터 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 심각도 분류 ───────────────────────────

def test_classify_slo_violation_crisis_rate_is_p0():
    from engine.safety.alert_router import classify_slo_violation, P0
    assert classify_slo_violation("crisis_rate=0.080 > 0.05") == P0


def test_classify_slo_violation_p95_is_p1():
    from engine.safety.alert_router import classify_slo_violation, P1
    assert classify_slo_violation("p95=6500ms > 5000ms") == P1


def test_classify_slo_violation_err_rate_is_p1():
    from engine.safety.alert_router import classify_slo_violation, P1
    assert classify_slo_violation("err_rate=0.250 > 0.2") == P1


def test_classify_slo_violation_cache_is_p2():
    from engine.safety.alert_router import classify_slo_violation, P2
    assert classify_slo_violation("cache_hit_rate=0.05 < 0.10") == P2


def test_classify_event_crisis_block_failed_is_p0():
    from engine.safety.alert_router import classify_event, P0
    assert classify_event("crisis_block_failed") == P0
    assert classify_event("service_down") == P0


def test_classify_event_golden_set_regression_severity_by_failures():
    from engine.safety.alert_router import classify_event, P1, P2
    assert classify_event("golden_set_regression", {"failures": 5}) == P1
    assert classify_event("golden_set_regression", {"failures": 1}) == P2
    assert classify_event("golden_set_regression") == P2


def test_classify_event_data_governance_is_p2():
    from engine.safety.alert_router import classify_event, P2
    assert classify_event("data_governance_violation") == P2


def test_classify_event_unknown_falls_to_p3():
    from engine.safety.alert_router import classify_event, P3
    assert classify_event("some_random_thing") == P3


# ─────────────────────────── 디바운스 ───────────────────────────

def test_debouncer_first_send_passes():
    from engine.safety.alert_router import Debouncer
    d = Debouncer(window_sec=300)
    assert d.should_send("key1", now=1000.0) is True


def test_debouncer_same_key_within_window_blocked():
    from engine.safety.alert_router import Debouncer
    d = Debouncer(window_sec=300)
    d.should_send("key1", now=1000.0)
    assert d.should_send("key1", now=1100.0) is False  # 100초 후 — 윈도우 내


def test_debouncer_same_key_after_window_passes():
    from engine.safety.alert_router import Debouncer
    d = Debouncer(window_sec=300)
    d.should_send("key1", now=1000.0)
    assert d.should_send("key1", now=1400.0) is True  # 400초 후 — 윈도우 초과


def test_debouncer_different_keys_independent():
    from engine.safety.alert_router import Debouncer
    d = Debouncer()
    assert d.should_send("a", now=1000.0) is True
    assert d.should_send("b", now=1000.0) is True
    assert d.should_send("a", now=1000.0) is False


def test_debouncer_reset_clears():
    from engine.safety.alert_router import Debouncer
    d = Debouncer()
    d.should_send("k", now=1000.0)
    d.reset()
    assert d.should_send("k", now=1001.0) is True


# ─────────────────────────── route_alert ───────────────────────────

def test_route_alert_p0_uses_pagerduty_and_slack_incidents():
    from engine.safety.alert_router import AlertEvent, route_alert, P0
    e = AlertEvent(name="slo_violation:crisis_rate", severity=P0,
                   title="Crisis rate exceeded")
    r = route_alert(e, pagerduty_routing_key="ROUTING-KEY-123")
    assert r["suppressed"] is False
    assert r["severity"] == "P0"
    assert "pagerduty" in r["channels"]
    assert "slack:incidents" in r["channels"]
    assert r["payloads"]["pagerduty"]["routing_key"] == "ROUTING-KEY-123"
    assert r["payloads"]["pagerduty"]["payload"]["severity"] == "critical"


def test_route_alert_p1_uses_slack_incidents_only():
    from engine.safety.alert_router import AlertEvent, route_alert, P1
    e = AlertEvent(name="slo_violation:p95", severity=P1, title="p95 over threshold")
    r = route_alert(e)
    assert r["channels"] == ["slack:incidents"]


def test_route_alert_p2_uses_ops_daily():
    from engine.safety.alert_router import AlertEvent, route_alert, P2
    e = AlertEvent(name="cache_hit_low", severity=P2, title="Cache hit low")
    r = route_alert(e)
    assert r["channels"] == ["slack:ops-daily"]


def test_route_alert_p3_uses_email():
    from engine.safety.alert_router import AlertEvent, route_alert, P3
    e = AlertEvent(name="weekly_trend", severity=P3, title="Weekly trend")
    r = route_alert(e)
    assert r["channels"] == ["email:weekly-digest"]


def test_route_alert_p0_without_routing_key_skips_pagerduty():
    """pagerduty_routing_key 미주입 시 pagerduty 채널은 스킵, slack은 발송."""
    from engine.safety.alert_router import AlertEvent, route_alert, P0
    e = AlertEvent(name="slo_violation:crisis_rate", severity=P0, title="X")
    r = route_alert(e)  # routing_key 없음
    assert "pagerduty" not in r["channels"]
    assert "slack:incidents" in r["channels"]


def test_route_alert_debounced_returns_suppressed():
    from engine.safety.alert_router import AlertEvent, route_alert, P1, Debouncer
    d = Debouncer(window_sec=300)
    e = AlertEvent(name="slo_violation:p95", severity=P1, title="X")
    r1 = route_alert(e, debouncer=d)
    r2 = route_alert(e, debouncer=d)  # 즉시 두 번째
    assert r1["suppressed"] is False
    assert r2["suppressed"] is True
    assert r2["payloads"] == {}


# ─────────────────────────── 메시지 직렬화 ───────────────────────────

def test_slack_message_has_block_kit_structure():
    from engine.safety.alert_router import AlertEvent, build_slack_message, P0
    e = AlertEvent(name="x", severity=P0, title="Title", body="Body text",
                   metric={"foo": 1.23}, runbook_url="https://runbook.example/x")
    m = build_slack_message(e)
    assert "attachments" in m
    blocks = m["attachments"][0]["blocks"]
    # header + section(fields) + section(body) + actions(runbook)
    assert blocks[0]["type"] == "header"
    assert "[P0]" in blocks[0]["text"]["text"]
    # runbook 버튼 포함
    assert any(b.get("type") == "actions" for b in blocks)


def test_pagerduty_payload_dedup_key_is_stable():
    from engine.safety.alert_router import AlertEvent, build_pagerduty_event, P0
    e = AlertEvent(name="slo_violation:crisis_rate", severity=P0, title="X")
    p1 = build_pagerduty_event(e, routing_key="K")
    p2 = build_pagerduty_event(e, routing_key="K")
    assert p1["dedup_key"] == p2["dedup_key"]
    assert p1["payload"]["severity"] == "critical"


# ─────────────────────────── SLO 보고서 통합 ───────────────────────────

def test_alerts_from_slo_report_creates_events_per_violation():
    from engine.safety.alert_router import alerts_from_slo_report
    slo = {
        "request_count": 100,
        "crisis_rate": 0.08,
        "err_rate": 0.25,
        "latency_ms": {"p50": 200, "p95": 6500, "p99": 8500},
        "slo_violations": [
            "crisis_rate=0.080 > 0.05",
            "p95=6500ms > 5000ms",
            "err_rate=0.250 > 0.2",
        ],
    }
    events = alerts_from_slo_report(slo)
    assert len(events) == 3
    # crisis_rate가 P0
    crisis_event = next(e for e in events if "crisis_rate" in e.name)
    assert crisis_event.severity == 0  # P0


def test_alerts_from_slo_report_empty_violations_returns_empty():
    from engine.safety.alert_router import alerts_from_slo_report
    events = alerts_from_slo_report({"slo_violations": []})
    assert events == []


def test_alerts_from_slo_report_dedup_key_per_metric():
    """같은 메트릭 위반은 동일 dedup_key를 사용해야 (5분 윈도우 디바운스)."""
    from engine.safety.alert_router import alerts_from_slo_report
    slo = {"slo_violations": ["p95=6000ms > 5000ms"]}
    events = alerts_from_slo_report(slo)
    assert events[0].dedup_key == "slo:p95"


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_alert_router():
    import engine.safety as safety
    assert hasattr(safety, "AlertEvent")
    assert hasattr(safety, "Debouncer")
    assert hasattr(safety, "route_alert")
    assert hasattr(safety, "classify_event")
    assert hasattr(safety, "classify_slo_violation")
    assert hasattr(safety, "alerts_from_slo_report")
