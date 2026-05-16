"""LLM 비용 가드 — 운영표준 §7.2.17 본문화.

LLM 호출 비용을 일/월 한도로 추적하고 한도 초과 시 다음 동작 결정:
  · 80% 도달 → P2 알람 (운영팀 통보)
  · 95% 도달 → P1 알람 + 신규 호출 stub 폴백 권고
  · 100% 도달 → 신규 호출 차단 (deterministic_stub_response만 응답)

§7.2.17 가격 모델 (USD, 2026년 기준 추정 — 외부 운영자가 주입 가능):
  · gemini_vision: input $0.075 / 1K tokens, output $0.30 / 1K tokens
  · claude_vision: input $3.00 / 1K tokens, output $15.00 / 1K tokens
  · stub: $0

본 모듈은 in-memory 카운터 — 다중 워커는 외부 Redis HINCRBY 필요.
저장은 일간/월간 키별로 분리.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


# §7.2.17 — 백엔드별 가격표 (USD per 1M tokens). 외부에서 override 가능.
DEFAULT_PRICING_USD_PER_M = {
    "gemini_vision": {"input": 0.075, "output": 0.30},
    "claude_vision": {"input": 3.00, "output": 15.00},
    "deterministic_stub": {"input": 0.0, "output": 0.0},
}

# §7.2.17 — 한도 임계
WARN_PERCENT = 0.80
CRITICAL_PERCENT = 0.95


@dataclass
class CostBudget:
    """일/월 한도 정의.

    Attributes:
        daily_usd: 일 한도
        monthly_usd: 월 한도
    """
    daily_usd: float
    monthly_usd: float


@dataclass(frozen=True)
class CostRecord:
    """단일 LLM 호출 비용 기록."""
    backend: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp_epoch: float


@dataclass(frozen=True)
class CostStatus:
    """현재 누적 + 한도 대비 상태."""
    day_key: str          # "2026-05-15"
    month_key: str        # "2026-05"
    daily_spent_usd: float
    monthly_spent_usd: float
    daily_budget_usd: float
    monthly_budget_usd: float
    daily_percent: float
    monthly_percent: float
    severity: str         # "ok" / "warn" / "critical" / "exhausted"
    should_fallback_to_stub: bool


# ─────────────────────────── 비용 계산 ───────────────────────────

def calculate_cost(
    backend: str,
    *,
    input_tokens: int,
    output_tokens: int,
    pricing: dict[str, dict[str, float]] | None = None,
) -> float:
    """단일 호출 비용 (USD)."""
    pricing = pricing or DEFAULT_PRICING_USD_PER_M
    table = pricing.get(backend)
    if table is None:
        return 0.0  # 알 수 없는 백엔드는 0으로 처리 (보수적)
    return (
        (input_tokens / 1_000_000.0) * table.get("input", 0.0)
        + (output_tokens / 1_000_000.0) * table.get("output", 0.0)
    )


# ─────────────────────────── Tracker ───────────────────────────

def _day_key(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%d")


def _month_key(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m")


class CostTracker:
    """일/월 누적 추적기. 단일 프로세스, RLock으로 thread-safe."""

    def __init__(
        self,
        budget: CostBudget,
        *,
        pricing: dict[str, dict[str, float]] | None = None,
    ) -> None:
        self.budget = budget
        self.pricing = pricing or DEFAULT_PRICING_USD_PER_M
        self._lock = threading.RLock()
        self._daily: dict[str, float] = {}
        self._monthly: dict[str, float] = {}
        self._records: list[CostRecord] = []

    def record(
        self,
        backend: str,
        *,
        input_tokens: int,
        output_tokens: int,
        now: float | None = None,
    ) -> CostRecord:
        """LLM 호출 직후 등록. 비용 자동 계산 + 일/월 누적."""
        import time as _time
        now = now if now is not None else _time.time()
        cost = calculate_cost(
            backend,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            pricing=self.pricing,
        )
        rec = CostRecord(
            backend=backend,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            timestamp_epoch=now,
        )
        with self._lock:
            self._records.append(rec)
            dk = _day_key(now)
            mk = _month_key(now)
            self._daily[dk] = self._daily.get(dk, 0.0) + cost
            self._monthly[mk] = self._monthly.get(mk, 0.0) + cost
        return rec

    def status(self, *, now: float | None = None) -> CostStatus:
        """현재 일/월 누적 상태 + 알람 등급."""
        import time as _time
        now = now if now is not None else _time.time()
        with self._lock:
            dk = _day_key(now)
            mk = _month_key(now)
            ds = self._daily.get(dk, 0.0)
            ms = self._monthly.get(mk, 0.0)
        d_pct = ds / self.budget.daily_usd if self.budget.daily_usd > 0 else 0.0
        m_pct = ms / self.budget.monthly_usd if self.budget.monthly_usd > 0 else 0.0
        worst = max(d_pct, m_pct)
        if worst >= 1.0:
            severity = "exhausted"
        elif worst >= CRITICAL_PERCENT:
            severity = "critical"
        elif worst >= WARN_PERCENT:
            severity = "warn"
        else:
            severity = "ok"
        should_stub = worst >= CRITICAL_PERCENT
        return CostStatus(
            day_key=dk,
            month_key=mk,
            daily_spent_usd=round(ds, 6),
            monthly_spent_usd=round(ms, 6),
            daily_budget_usd=self.budget.daily_usd,
            monthly_budget_usd=self.budget.monthly_usd,
            daily_percent=round(d_pct, 4),
            monthly_percent=round(m_pct, 4),
            severity=severity,
            should_fallback_to_stub=should_stub,
        )

    def can_afford_llm(self, *, now: float | None = None) -> bool:
        """신규 LLM 호출이 가능한지 — exhausted/critical이면 False."""
        return not self.status(now=now).should_fallback_to_stub

    def reset(self) -> None:
        """테스트용 일괄 초기화."""
        with self._lock:
            self._daily.clear()
            self._monthly.clear()
            self._records.clear()

    def records(self) -> list[CostRecord]:
        with self._lock:
            return list(self._records)


# ─────────────────────────── 알람 ───────────────────────────

def to_alert_payload(status: CostStatus) -> dict[str, Any]:
    """§14.3 alert_router 호환 페이로드.

    severity 매핑:
      · ok        → P3
      · warn      → P2
      · critical  → P1
      · exhausted → P0 (서비스 가용성 위협)
    """
    sev_map = {"ok": "P3", "warn": "P2", "critical": "P1", "exhausted": "P0"}
    return {
        "service": "cost_guard",
        "severity": sev_map.get(status.severity, "P3"),
        "day_key": status.day_key,
        "month_key": status.month_key,
        "daily_spent_usd": status.daily_spent_usd,
        "monthly_spent_usd": status.monthly_spent_usd,
        "daily_percent": status.daily_percent,
        "monthly_percent": status.monthly_percent,
        "should_fallback_to_stub": status.should_fallback_to_stub,
    }
