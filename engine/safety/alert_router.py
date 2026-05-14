"""알람 채널 라우터 — 운영표준 §14.3 본문화.

운영표준 §7.3.2.1 SLO 위반·§7.1 위기 차단 누적·§7.3.4 ERR 폭증 등 운영 이벤트
발생 시 외부 채널(Slack/PagerDuty/Email)로 통보할 라우팅 규칙을 표준화한다.

본 모듈은 실제 전송은 외부 워커(Celery/Lambda)에 위임하고, 다음만 책임:
  · 이벤트 → 심각도(severity) 분류 (P0~P3)
  · 심각도 → 채널 선택 (어떤 채널에 어떤 메시지로 보낼지)
  · 메시지 페이로드 직렬화 (Slack Block Kit / PagerDuty Event API v2 호환)
  · 동일 알람 디바운스(쿨다운) 결정 (5분 내 동일 키 중복 차단)

§14.3.1 심각도 분류:
  · P0 — 즉시 호출 (crisis_rate 폭증, 라이브 503, 위기 차단 실패)
  · P1 — 15분 내 응답 (p95 임계 초과, err_rate 임계 초과)
  · P2 — 다음 영업일 (cache_hit_rate 저하, 골든 셋 회귀 1건 실패)
  · P3 — 주간 리포트 (정상 운영 메트릭, 트렌드)

§14.3.2 채널 라우팅:
  · P0 → PagerDuty + Slack #incidents
  · P1 → Slack #incidents
  · P2 → Slack #ops-daily
  · P3 → Email weekly digest
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any


# §14.3.1 — 심각도 enum (정렬 가능한 정수)
P0 = 0  # critical
P1 = 1  # high
P2 = 2  # medium
P3 = 3  # low

SEVERITY_LABELS = {P0: "P0", P1: "P1", P2: "P2", P3: "P3"}

# §14.3.2 — 심각도 → 채널 매핑
CHANNEL_MAP = {
    P0: ("pagerduty", "slack:incidents"),
    P1: ("slack:incidents",),
    P2: ("slack:ops-daily",),
    P3: ("email:weekly-digest",),
}

# §14.3.3 — 디바운스 윈도우 (초)
DEBOUNCE_WINDOW_SEC = 300  # 5분 내 동일 dedup_key 중복 차단


@dataclass
class AlertEvent:
    """알람 이벤트 — 라우터에 입력되는 단일 사건.

    Attributes:
        name: 이벤트 식별자 (예: "slo_violation:p95_latency")
        severity: P0~P3
        title: 한 줄 헤드라인
        body: 상세 설명 (멀티라인 가능)
        metric: 위반 메트릭 값 (예: {"p95_ms": 6500, "threshold": 5000})
        runbook_url: 대응 룬북 URL (없으면 빈 문자열)
        dedup_key: 중복 차단 키 (없으면 name+severity 기반 자동 생성)
        timestamp: epoch sec (None이면 now)
    """
    name: str
    severity: int
    title: str
    body: str = ""
    metric: dict[str, Any] = field(default_factory=dict)
    runbook_url: str = ""
    dedup_key: str = ""
    timestamp: float | None = None


# ─────────────────────────── 분류 규칙 ───────────────────────────

# §14.3.1 — SLO 메트릭별 P 등급 매핑.
# slo.py compute_slo() 결과의 slo_violations 리스트 항목과 매칭.
def classify_slo_violation(violation_text: str) -> int:
    """SLO 위반 텍스트 한 줄을 받아 심각도 반환.

    Args:
        violation_text: 예: "crisis_rate=0.080 > 0.05", "p95=6500ms > 5000ms"

    Returns:
        P0~P3 정수. 매칭 안 되면 P2.
    """
    t = violation_text.lower()
    if t.startswith("crisis_rate"):
        return P0  # 위기 신호 폭증 — 즉시 호출
    if t.startswith("p99"):
        return P1
    if t.startswith("p95"):
        return P1
    if t.startswith("err_rate"):
        return P1
    if t.startswith("cache_hit_rate"):
        return P2
    return P2


def classify_event(event_name: str, payload: dict[str, Any] | None = None) -> int:
    """이벤트 이름 → 심각도. 정밀 매칭 우선, prefix 매칭 후순위."""
    payload = payload or {}
    name = event_name.lower()
    # P0 — 안전·가용성 즉시 위협
    if name in {"crisis_block_failed", "service_down", "auth_breach"}:
        return P0
    if name.startswith("slo_violation:crisis_rate"):
        return P0
    # P1 — 성능·품질 임계 초과
    if name.startswith("slo_violation:p95") or name.startswith("slo_violation:p99"):
        return P1
    if name.startswith("slo_violation:err_rate"):
        return P1
    if name == "golden_set_regression":
        # 회귀 실패 건수에 따라 P1/P2
        failures = int(payload.get("failures", 0))
        return P1 if failures >= 3 else P2
    # P2 — 경고
    if name.startswith("slo_violation:cache_hit_rate"):
        return P2
    if name == "data_governance_violation":
        return P2
    # 기본값
    return P3


# ─────────────────────────── 디바운스 ───────────────────────────

class Debouncer:
    """5분 윈도우 동일 키 알람 차단. in-memory — 다중 워커는 외부 Redis 필요."""

    def __init__(self, window_sec: int = DEBOUNCE_WINDOW_SEC) -> None:
        self._seen: dict[str, float] = {}
        self._window = window_sec

    def should_send(self, dedup_key: str, *, now: float | None = None) -> bool:
        now = now if now is not None else time.time()
        last = self._seen.get(dedup_key)
        if last is None or (now - last) >= self._window:
            self._seen[dedup_key] = now
            return True
        return False

    def reset(self) -> None:
        self._seen.clear()


def _compute_dedup_key(event: AlertEvent) -> str:
    if event.dedup_key:
        return event.dedup_key
    raw = f"{event.name}:{event.severity}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


# ─────────────────────────── 메시지 직렬화 ───────────────────────────

def build_slack_message(event: AlertEvent) -> dict[str, Any]:
    """Slack Block Kit 호환 페이로드. 외부 워커가 그대로 chat.postMessage로 전송."""
    sev_label = SEVERITY_LABELS.get(event.severity, "P?")
    color = {"P0": "#d9534f", "P1": "#f0ad4e", "P2": "#5bc0de", "P3": "#5cb85c"}.get(sev_label, "#777")
    fields = [
        {"type": "mrkdwn", "text": f"*Severity:* {sev_label}"},
        {"type": "mrkdwn", "text": f"*Event:* `{event.name}`"},
    ]
    if event.metric:
        metric_lines = "\n".join(f"• {k} = {v}" for k, v in event.metric.items())
        fields.append({"type": "mrkdwn", "text": f"*Metrics:*\n{metric_lines}"})
    blocks: list[dict[str, Any]] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"[{sev_label}] {event.title}"},
        },
        {"type": "section", "fields": fields[:10]},
    ]
    if event.body:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": event.body}})
    if event.runbook_url:
        blocks.append({
            "type": "actions",
            "elements": [{
                "type": "button",
                "text": {"type": "plain_text", "text": "Runbook"},
                "url": event.runbook_url,
            }],
        })
    return {
        "attachments": [{
            "color": color,
            "blocks": blocks,
        }],
    }


def build_pagerduty_event(event: AlertEvent, *, routing_key: str) -> dict[str, Any]:
    """PagerDuty Events API v2 호환 페이로드. routing_key는 외부 ENV에서 주입."""
    pd_severity = {P0: "critical", P1: "error", P2: "warning", P3: "info"}.get(event.severity, "info")
    return {
        "routing_key": routing_key,
        "event_action": "trigger",
        "dedup_key": _compute_dedup_key(event),
        "payload": {
            "summary": event.title,
            "source": "face_reading",
            "severity": pd_severity,
            "custom_details": {
                "event_name": event.name,
                "body": event.body,
                "metric": event.metric,
                "runbook_url": event.runbook_url,
            },
        },
    }


# ─────────────────────────── 라우팅 진입점 ───────────────────────────

def route_alert(
    event: AlertEvent,
    *,
    debouncer: Debouncer | None = None,
    pagerduty_routing_key: str = "",
) -> dict[str, Any]:
    """이벤트를 받아 발송할 채널 + 페이로드를 결정.

    Returns:
        {
            "suppressed": bool,        # 디바운스 차단 시 True (페이로드 미생성)
            "severity": "P0",
            "channels": ["pagerduty", "slack:incidents"],
            "payloads": {
                "slack:incidents": {...},  # Slack Block Kit
                "pagerduty": {...},        # PagerDuty Events API v2
            },
            "dedup_key": "abc123...",
        }
    """
    dedup_key = _compute_dedup_key(event)
    if debouncer is not None and not debouncer.should_send(dedup_key):
        return {
            "suppressed": True,
            "severity": SEVERITY_LABELS.get(event.severity, "P?"),
            "channels": [],
            "payloads": {},
            "dedup_key": dedup_key,
        }

    channels = CHANNEL_MAP.get(event.severity, ("slack:ops-daily",))
    payloads: dict[str, Any] = {}
    for ch in channels:
        if ch == "pagerduty":
            if not pagerduty_routing_key:
                # routing_key 미주입 시 pagerduty 채널 스킵 (다른 채널은 계속)
                continue
            payloads[ch] = build_pagerduty_event(event, routing_key=pagerduty_routing_key)
        elif ch.startswith("slack:"):
            payloads[ch] = build_slack_message(event)
        elif ch.startswith("email:"):
            # 이메일은 단순 plain text 본문 — 외부 워커가 헤더 설정
            payloads[ch] = {
                "subject": f"[{SEVERITY_LABELS.get(event.severity, 'P?')}] {event.title}",
                "body_text": (event.body or event.title),
            }
    return {
        "suppressed": False,
        "severity": SEVERITY_LABELS.get(event.severity, "P?"),
        "channels": list(payloads.keys()),
        "payloads": payloads,
        "dedup_key": dedup_key,
    }


def alerts_from_slo_report(slo: dict[str, Any]) -> list[AlertEvent]:
    """compute_slo() 결과의 slo_violations 리스트 → AlertEvent 리스트.

    각 위반은 단일 알람으로 분리되며, 심각도는 classify_slo_violation()으로 결정.
    """
    events: list[AlertEvent] = []
    for vline in slo.get("slo_violations", []):
        sev = classify_slo_violation(vline)
        # 위반 메트릭 이름을 dedup_key 접두로 — 같은 메트릭은 5분 윈도우 묶임
        metric_name = vline.split("=", 1)[0].strip() if "=" in vline else vline.split()[0]
        events.append(AlertEvent(
            name=f"slo_violation:{metric_name}",
            severity=sev,
            title=f"SLO violation: {metric_name}",
            body=vline,
            metric={
                "request_count": slo.get("request_count", 0),
                "crisis_rate": slo.get("crisis_rate", 0),
                "err_rate": slo.get("err_rate", 0),
                "p95_ms": slo.get("latency_ms", {}).get("p95"),
                "p99_ms": slo.get("latency_ms", {}).get("p99"),
            },
            dedup_key=f"slo:{metric_name}",
        ))
    return events
