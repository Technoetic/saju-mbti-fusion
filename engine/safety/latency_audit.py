"""단계별 latency 감사 — 운영표준 §7.2.24 본문화.

face_reading 호출 단위 시간 추적. slo.py가 윈도우 전체 P50/P95/P99 집계라면,
본 모듈은 단일 호출의 단계별 분해(LLM call / 후처리 / cache lookup / safety gate)를
기록하고 SLO 임계 초과 단계를 즉시 식별한다.

§7.2.24 단계 분류:
  · preflight      — request_pipeline.preflight (rate/cost/sanitize/jailbreak)
  · cache_lookup   — _load_cache 디스크 IO
  · llm_call       — Gemini/Claude vision 호출
  · safety_gate    — output_safety_gate.run_safety_gates
  · cache_save     — _save_cache 디스크 IO
  · tracing        — emit_face_reading_event

§7.2.24 SLO 단계별 임계 (ms):
  · preflight      < 50
  · cache_lookup   < 30
  · llm_call       < 5000  (slo.py p95 와 일관)
  · safety_gate    < 100
  · cache_save     < 50
  · tracing        < 10

본 모듈은 측정만 — 차단·롤백 결정은 외부에 위임 (alert_router에 페이로드 전달).
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator


# §7.2.24 단계 식별자
STEP_PREFLIGHT = "preflight"
STEP_CACHE_LOOKUP = "cache_lookup"
STEP_LLM_CALL = "llm_call"
STEP_SAFETY_GATE = "safety_gate"
STEP_CACHE_SAVE = "cache_save"
STEP_TRACING = "tracing"


# §7.2.24 단계별 SLO 임계 (ms)
DEFAULT_STEP_BUDGETS_MS = {
    STEP_PREFLIGHT: 50,
    STEP_CACHE_LOOKUP: 30,
    STEP_LLM_CALL: 5000,
    STEP_SAFETY_GATE: 100,
    STEP_CACHE_SAVE: 50,
    STEP_TRACING: 10,
}

# §7.2.24 전체 호출 임계 (모든 단계 합)
DEFAULT_TOTAL_BUDGET_MS = 8000


@dataclass
class LatencySample:
    """단일 호출의 단계별 latency 기록."""
    step_durations_ms: dict[str, int] = field(default_factory=dict)
    started_at_ms: int = 0
    finished_at_ms: int = 0
    request_id: str = ""

    @property
    def total_ms(self) -> int:
        return self.finished_at_ms - self.started_at_ms

    @property
    def steps_total_ms(self) -> int:
        """기록된 단계 합 (병렬 단계는 없으므로 ≤ total_ms)."""
        return sum(self.step_durations_ms.values())


@dataclass(frozen=True)
class BudgetViolation:
    step: str
    duration_ms: int
    budget_ms: int


@dataclass(frozen=True)
class AuditReport:
    sample: LatencySample
    violations: list[BudgetViolation]
    total_violated: bool

    @property
    def has_violations(self) -> bool:
        return bool(self.violations) or self.total_violated


# ─────────────────────────── 측정 ───────────────────────────

def _now_ms() -> int:
    return int(time.time() * 1000)


def new_sample(request_id: str = "") -> LatencySample:
    """새 latency 샘플 생성. 호출 시점을 started_at_ms로."""
    return LatencySample(
        started_at_ms=_now_ms(),
        request_id=request_id,
    )


def record_step(
    sample: LatencySample,
    step: str,
    duration_ms: int,
) -> None:
    """이미 측정된 단계 시간을 등록 (외부 measure 후 호출)."""
    if duration_ms < 0:
        duration_ms = 0
    sample.step_durations_ms[step] = duration_ms


def finalize(sample: LatencySample) -> LatencySample:
    """모든 단계 기록 완료 후 finished_at_ms 설정."""
    sample.finished_at_ms = _now_ms()
    return sample


@contextmanager
def measure(sample: LatencySample, step: str) -> Iterator[None]:
    """with 블록 안의 elapsed를 자동으로 step에 기록."""
    start = _now_ms()
    try:
        yield
    finally:
        record_step(sample, step, _now_ms() - start)


# ─────────────────────────── 평가 ───────────────────────────

def evaluate(
    sample: LatencySample,
    *,
    step_budgets_ms: dict[str, int] | None = None,
    total_budget_ms: int | None = None,
) -> AuditReport:
    """샘플을 임계와 비교 → AuditReport."""
    budgets = step_budgets_ms or DEFAULT_STEP_BUDGETS_MS
    total = total_budget_ms if total_budget_ms is not None else DEFAULT_TOTAL_BUDGET_MS

    violations: list[BudgetViolation] = []
    for step, dur in sample.step_durations_ms.items():
        b = budgets.get(step)
        if b is not None and dur > b:
            violations.append(BudgetViolation(
                step=step, duration_ms=dur, budget_ms=b,
            ))

    total_violated = (
        sample.finished_at_ms > sample.started_at_ms
        and sample.total_ms > total
    )

    return AuditReport(
        sample=sample,
        violations=violations,
        total_violated=total_violated,
    )


# ─────────────────────────── 트레이싱·알람 ───────────────────────────

def to_trace_event(sample: LatencySample) -> dict[str, Any]:
    """§7.3.4 tracing extra 호환 — 단계별 latency 평면화."""
    out: dict[str, Any] = {
        "latency_total_ms": sample.total_ms,
        "latency_steps_total_ms": sample.steps_total_ms,
    }
    for step, dur in sample.step_durations_ms.items():
        out[f"latency_{step}_ms"] = dur
    return out


def to_alert_payload(report: AuditReport) -> dict[str, Any]:
    """§14.3 alert_router 호환.

    severity 매핑:
      · ok        — 위반 없음 P3
      · llm_call 단독 — P2
      · 2개 이상 또는 total_violated — P1
    """
    if not report.has_violations:
        sev = "P3"
    elif report.total_violated or len(report.violations) >= 2:
        sev = "P1"
    else:
        sev = "P2"
    return {
        "service": "latency_audit",
        "severity": sev,
        "total_ms": report.sample.total_ms,
        "total_violated": report.total_violated,
        "violations": [
            {"step": v.step, "duration_ms": v.duration_ms, "budget_ms": v.budget_ms}
            for v in report.violations
        ],
        "request_id": report.sample.request_id,
    }


# ─────────────────────────── 윈도우 집계 ───────────────────────────

def aggregate_step_p95(
    samples: list[LatencySample],
    step: str,
) -> int:
    """N개 샘플에서 특정 step의 P95. 빈 리스트면 0."""
    durations = [s.step_durations_ms.get(step, 0) for s in samples
                 if step in s.step_durations_ms]
    if not durations:
        return 0
    durations.sort()
    idx = int(round(0.95 * (len(durations) - 1)))
    return durations[idx]


def aggregate_total_p95(samples: list[LatencySample]) -> int:
    if not samples:
        return 0
    totals = sorted(s.total_ms for s in samples if s.total_ms > 0)
    if not totals:
        return 0
    idx = int(round(0.95 * (len(totals) - 1)))
    return totals[idx]
