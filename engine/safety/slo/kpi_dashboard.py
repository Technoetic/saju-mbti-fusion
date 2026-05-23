"""KPI 대시보드 페이로드 — 운영표준 §14.11 본문화.

운영팀이 Grafana/Datadog에 띄울 KPI를 정규화된 메트릭으로 직렬화한다.
quarterly_review가 분기 종합 보고서라면, 본 모듈은 실시간 대시보드용
시계열 메트릭 페이로드를 만든다.

§14.11 KPI 13종:
  안전 (5):
    · crisis_block_rate / jailbreak_block_rate / pii_leak_count /
      persona_pass_rate / safety_gate_critical_rate
  품질 (3):
    · golden_set_pass_rate / response_alignment_rate / consistency_pass_rate
  성능 (3):
    · p95_latency_ms / p99_latency_ms / cache_hit_rate
  비용 (2):
    · daily_cost_usd / monthly_cost_percent

각 KPI에 (현재값, 임계, 단위, status, 추세) 메타 첨부. dashboard 자동 색상화에
바로 쓸 수 있는 형식.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


# §14.11 KPI 식별자
KPI_CRISIS_BLOCK_RATE = "crisis_block_rate"
KPI_JAILBREAK_BLOCK_RATE = "jailbreak_block_rate"
KPI_PII_LEAK_COUNT = "pii_leak_count"
KPI_PERSONA_PASS_RATE = "persona_pass_rate"
KPI_SAFETY_GATE_CRITICAL = "safety_gate_critical_rate"
KPI_GOLDEN_SET_PASS = "golden_set_pass_rate"
KPI_RESPONSE_ALIGNMENT = "response_alignment_rate"
KPI_CONSISTENCY_PASS = "consistency_pass_rate"
KPI_P95_LATENCY = "p95_latency_ms"
KPI_P99_LATENCY = "p99_latency_ms"
KPI_CACHE_HIT_RATE = "cache_hit_rate"
KPI_DAILY_COST = "daily_cost_usd"
KPI_MONTHLY_COST_PERCENT = "monthly_cost_percent"

# ADR-172 — 안전망 운영 관측 KPI 신설
KPI_SAFETY_GATE_FALLBACK_RATE = "safety_gate_fallback_rate"  # WARN/CRITICAL stub 폴백 비율
KPI_SAFETY_GATE_RETRY_RATE = "safety_gate_retry_rate"        # ADR-169 MINOR 재호출 비율
KPI_SAFETY_GATE_FATE_RATE = "safety_gate_fate_assertion_rate"  # ADR-171 단정 검출 비율
KPI_CRITIC_SAFETY_DISAGREEMENT = "critic_safety_disagreement_rate"  # ADR-174 critic↔safety 불일치 비율


# §14.11 KPI 상태
STATUS_GOOD = "good"
STATUS_WARN = "warn"
STATUS_BAD = "bad"

# §14.11 추세
TREND_UP = "up"
TREND_FLAT = "flat"
TREND_DOWN = "down"


@dataclass(frozen=True)
class KPIThreshold:
    """KPI 임계 정의. value 형식에 따라 비교 방향이 다름."""
    warn_at: float
    bad_at: float
    higher_is_better: bool       # True면 값이 클수록 좋음 (예: cache_hit)
    unit: str = ""               # "%", "ms", "USD", "count"
    label: str = ""              # 한국어 라벨


@dataclass(frozen=True)
class KPIMetric:
    """단일 KPI 측정값 + 상태.

    ADR-173: dimension 옵션 인자로 도메인별 분리 측정 지원.
    """
    kpi_id: str
    label: str
    value: float
    unit: str
    status: str                  # good/warn/bad
    trend: str                   # up/flat/down
    warn_at: float
    bad_at: float
    higher_is_better: bool
    dimension: str | None = None  # ADR-173 — 'face'|'palm'|'name'|'dream'|'hwapae'|None


@dataclass(frozen=True)
class DashboardPayload:
    generated_at_iso: str
    system_id: str
    metrics: tuple[KPIMetric, ...]
    overall_status: str          # 가장 나쁜 KPI 상태로 결정


# §14.11 — KPI별 임계 정의
_THRESHOLDS: dict[str, KPIThreshold] = {
    KPI_CRISIS_BLOCK_RATE: KPIThreshold(
        warn_at=0.05, bad_at=0.10, higher_is_better=False,
        unit="rate", label="위기 차단율",
    ),
    KPI_JAILBREAK_BLOCK_RATE: KPIThreshold(
        warn_at=0.05, bad_at=0.10, higher_is_better=False,
        unit="rate", label="jailbreak 차단율",
    ),
    KPI_PII_LEAK_COUNT: KPIThreshold(
        warn_at=1, bad_at=3, higher_is_better=False,
        unit="count", label="PII 누출 누적",
    ),
    KPI_PERSONA_PASS_RATE: KPIThreshold(
        warn_at=0.90, bad_at=0.80, higher_is_better=True,
        unit="rate", label="페르소나 통과율",
    ),
    KPI_SAFETY_GATE_CRITICAL: KPIThreshold(
        warn_at=0.01, bad_at=0.05, higher_is_better=False,
        unit="rate", label="output_safety_gate critical 비율",
    ),
    KPI_GOLDEN_SET_PASS: KPIThreshold(
        warn_at=0.95, bad_at=0.90, higher_is_better=True,
        unit="rate", label="골든 셋 통과율",
    ),
    KPI_RESPONSE_ALIGNMENT: KPIThreshold(
        warn_at=0.90, bad_at=0.80, higher_is_better=True,
        unit="rate", label="응답 주제 정렬율",
    ),
    KPI_CONSISTENCY_PASS: KPIThreshold(
        warn_at=0.95, bad_at=0.85, higher_is_better=True,
        unit="rate", label="응답 일관성 통과율",
    ),
    KPI_P95_LATENCY: KPIThreshold(
        warn_at=4000, bad_at=5000, higher_is_better=False,
        unit="ms", label="P95 latency",
    ),
    KPI_P99_LATENCY: KPIThreshold(
        warn_at=7000, bad_at=8000, higher_is_better=False,
        unit="ms", label="P99 latency",
    ),
    KPI_CACHE_HIT_RATE: KPIThreshold(
        warn_at=0.15, bad_at=0.10, higher_is_better=True,
        unit="rate", label="캐시 적중률",
    ),
    KPI_DAILY_COST: KPIThreshold(
        warn_at=80.0, bad_at=95.0, higher_is_better=False,
        unit="USD", label="일 LLM 비용",
    ),
    KPI_MONTHLY_COST_PERCENT: KPIThreshold(
        warn_at=80.0, bad_at=95.0, higher_is_better=False,
        unit="%", label="월 비용 한도 대비",
    ),
    # ADR-172 — 안전망 운영 관측 KPI
    KPI_SAFETY_GATE_FALLBACK_RATE: KPIThreshold(
        warn_at=0.05, bad_at=0.15, higher_is_better=False,
        unit="rate", label="WARN/CRITICAL stub 폴백 비율 (ADR-167)",
    ),
    KPI_SAFETY_GATE_RETRY_RATE: KPIThreshold(
        warn_at=0.10, bad_at=0.25, higher_is_better=False,
        unit="rate", label="MINOR 재호출 비율 (ADR-169)",
    ),
    KPI_SAFETY_GATE_FATE_RATE: KPIThreshold(
        warn_at=0.02, bad_at=0.08, higher_is_better=False,
        unit="rate", label="운명·길흉 단정 검출 비율 (ADR-171)",
    ),
    # ADR-174 — critic loop 통과했으나 안전망 폴백된 비율
    # 높을수록 critic 사전 검증 효과 ↓ — critic 룰셋 강화 신호
    KPI_CRITIC_SAFETY_DISAGREEMENT: KPIThreshold(
        warn_at=0.03, bad_at=0.10, higher_is_better=False,
        unit="rate", label="critic 통과 + 안전망 폴백 불일치 비율 (ADR-174)",
    ),
}


# ─────────────────────────── 상태 평가 ───────────────────────────

def classify_status(
    *,
    value: float,
    threshold: KPIThreshold,
) -> str:
    """KPI 임계 비교 → status (good/warn/bad)."""
    if threshold.higher_is_better:
        # 큰 값이 좋음 — bad_at 미만이면 bad
        if value < threshold.bad_at:
            return STATUS_BAD
        if value < threshold.warn_at:
            return STATUS_WARN
        return STATUS_GOOD
    # 작은 값이 좋음
    if value >= threshold.bad_at:
        return STATUS_BAD
    if value >= threshold.warn_at:
        return STATUS_WARN
    return STATUS_GOOD


def classify_trend(
    *,
    current: float,
    previous: float,
    higher_is_better: bool,
    flat_threshold_ratio: float = 0.05,
) -> str:
    """이전 값 대비 추세 → up/flat/down. flat는 ±5% 안."""
    if previous == 0:
        return TREND_FLAT if current == 0 else TREND_UP
    delta_ratio = (current - previous) / abs(previous)
    if abs(delta_ratio) < flat_threshold_ratio:
        return TREND_FLAT
    return TREND_UP if delta_ratio > 0 else TREND_DOWN


# ─────────────────────────── KPI 빌더 ───────────────────────────

_VALID_DIMENSIONS: frozenset[str] = frozenset({"face", "palm", "name", "dream", "hwapae"})


def build_kpi(
    kpi_id: str,
    value: float,
    *,
    previous_value: float | None = None,
    dimension: str | None = None,
) -> KPIMetric:
    """단일 KPI metric 생성.

    ADR-173: dimension 인자로 도메인별 분리 측정 지원.

    Args:
        dimension: 'face'|'palm'|'name'|'dream'|'hwapae'|None.
            None이면 시스템 전체. 알 수 없는 도메인은 None으로 정규화.
    """
    threshold = _THRESHOLDS.get(kpi_id)
    if threshold is None:
        raise ValueError(f"unknown kpi_id: {kpi_id}")
    status = classify_status(value=value, threshold=threshold)
    if previous_value is None:
        trend = TREND_FLAT
    else:
        trend = classify_trend(
            current=value, previous=previous_value,
            higher_is_better=threshold.higher_is_better,
        )
    # dimension 정규화: 알려진 값만 유지
    dim_norm = dimension if dimension in _VALID_DIMENSIONS else None
    # 라벨에 도메인 표시 (있을 때만)
    label = threshold.label
    if dim_norm:
        label = f"[{dim_norm}] {label}"
    return KPIMetric(
        kpi_id=kpi_id,
        label=label,
        value=round(value, 4),
        unit=threshold.unit,
        status=status,
        trend=trend,
        warn_at=threshold.warn_at,
        bad_at=threshold.bad_at,
        higher_is_better=threshold.higher_is_better,
        dimension=dim_norm,
    )


# ─────────────────────────── 대시보드 페이로드 ───────────────────────────

def build_dashboard(
    *,
    system_id: str = "face_reading",
    current_values: dict[Any, float] | None = None,
    previous_values: dict[Any, float] | None = None,
) -> DashboardPayload:
    """현재값 dict + (선택) 이전값 dict → DashboardPayload.

    Args:
        current_values: {kpi_id: value} 또는 {(kpi_id, dimension): value}.
            - 단순 키(str): 시스템 전체 KPI
            - 튜플 키(kpi_id, dim): ADR-186 도메인별 KPI
            비어있는 키는 제외.
        previous_values: 이전 윈도우 값 (같은 키 형식, 추세 계산용).

    ADR-186: current_values 키가 (kpi_id, dim) 튜플이면 dimension 분리 측정.
    """
    current_values = current_values or {}
    previous_values = previous_values or {}
    metrics: list[KPIMetric] = []
    for key, value in current_values.items():
        # ADR-186 — 튜플 키 (kpi_id, dim) 지원
        if isinstance(key, tuple) and len(key) == 2:
            kpi_id, dim = key
        else:
            kpi_id, dim = key, None
        if kpi_id not in _THRESHOLDS:
            continue
        prev = previous_values.get(key)
        metrics.append(build_kpi(kpi_id, value, previous_value=prev, dimension=dim))

    # 전체 상태 — 가장 나쁜 KPI 기준
    if any(m.status == STATUS_BAD for m in metrics):
        overall = STATUS_BAD
    elif any(m.status == STATUS_WARN for m in metrics):
        overall = STATUS_WARN
    else:
        overall = STATUS_GOOD

    return DashboardPayload(
        generated_at_iso=datetime.now(timezone.utc).isoformat(),
        system_id=system_id,
        metrics=tuple(metrics),
        overall_status=overall,
    )


# ─────────────────────────── 직렬화 ───────────────────────────

def to_grafana_json(payload: DashboardPayload) -> list[dict[str, Any]]:
    """Grafana simple JSON datasource 호환 페이로드 — datapoints 1건씩.

    ADR-173: dimension 있으면 target에 도메인 접미사 추가 (kpi_id{dim=face}).
    """
    out: list[dict[str, Any]] = []
    ts_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    for m in payload.metrics:
        target = m.kpi_id
        if m.dimension:
            target = f"{m.kpi_id}{{dim={m.dimension}}}"
        out.append({
            "target": target,
            "datapoints": [[m.value, ts_ms]],
        })
    return out


def to_datadog_metrics(payload: DashboardPayload) -> list[dict[str, Any]]:
    """Datadog metrics API v1 호환 페이로드.

    ADR-173: dimension 있으면 'dim:<domain>' 태그 추가.
    """
    ts = int(datetime.now(timezone.utc).timestamp())
    out: list[dict[str, Any]] = []
    for m in payload.metrics:
        tags = [
            f"system:{payload.system_id}",
            f"status:{m.status}",
            f"unit:{m.unit}",
        ]
        if m.dimension:
            tags.append(f"dim:{m.dimension}")
        out.append({
            "metric": f"face_reading.{m.kpi_id}",
            "points": [[ts, m.value]],
            "type": "gauge",
            "tags": tags,
        })
    return out


def format_dashboard_text(payload: DashboardPayload) -> str:
    """터미널 출력용 사람-읽기 텍스트."""
    lines: list[str] = []
    sym = {"good": "OK", "warn": "WARN", "bad": "BAD"}.get(
        payload.overall_status, "?")
    lines.append(f"[KPI Dashboard: {payload.system_id}] STATUS={sym} "
                 f"@ {payload.generated_at_iso}")
    for m in payload.metrics:
        trend_sym = {"up": "↑", "flat": "→", "down": "↓"}.get(m.trend, "?")
        status_sym = {"good": "OK", "warn": "WARN", "bad": "BAD"}.get(
            m.status, "?")
        lines.append(f"  [{status_sym}] {m.label:30s} = {m.value} {m.unit} "
                     f"{trend_sym} (warn>{m.warn_at} bad>{m.bad_at})")
    return "\n".join(lines)
