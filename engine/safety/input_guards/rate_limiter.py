"""Rate limiter — 운영표준 §7.2.19 본문화.

uid·IP·키별 분당/시간당 호출 횟수를 제한해 abuse·DDoS·비용 폭발을 차단.
sliding window log 알고리즘 (정확하지만 메모리 O(N), 단일 프로세스용).

§7.2.19 기본 한도 (외부에서 override 가능):
  · 분당 10건 / 시간당 100건 / 일당 500건

§7.2.19 응답:
  · ALLOWED — 호출 허용 + 카운터 증가
  · LIMITED — 가장 가까운 윈도우 초과 → 거부
    · retry_after_sec — 다음 슬롯이 열리는 시각까지 남은 초
    · breached_window — minute/hour/day 어느 윈도우에서 막혔는지

다중 워커 분산은 외부 Redis ZADD/ZREMRANGEBYSCORE 필요. 본 모듈 비대상.
"""

from __future__ import annotations

import bisect
import threading
import time
from dataclasses import dataclass


# §7.2.19 윈도우 (초)
WINDOW_MINUTE_SEC = 60
WINDOW_HOUR_SEC = 3600
WINDOW_DAY_SEC = 86400

# §7.2.19 기본 한도 (외부 override 가능)
DEFAULT_PER_MINUTE = 10
DEFAULT_PER_HOUR = 100
DEFAULT_PER_DAY = 500

# 결과 enum
RESULT_ALLOWED = "allowed"
RESULT_LIMITED = "limited"


@dataclass(frozen=True)
class RateLimitConfig:
    per_minute: int
    per_hour: int
    per_day: int


@dataclass(frozen=True)
class RateLimitResult:
    status: str                       # ALLOWED | LIMITED
    breached_window: str = ""         # minute/hour/day
    retry_after_sec: float = 0.0
    minute_count: int = 0
    hour_count: int = 0
    day_count: int = 0


# ─────────────────────────── Limiter ───────────────────────────

class RateLimiter:
    """sliding window log 기반 단일 프로세스 limiter.

    키별로 timestamp 정렬 리스트를 유지. 호출 시 day-old 항목 청소 + 카운트.
    """

    def __init__(
        self,
        config: RateLimitConfig | None = None,
    ) -> None:
        self.config = config or RateLimitConfig(
            per_minute=DEFAULT_PER_MINUTE,
            per_hour=DEFAULT_PER_HOUR,
            per_day=DEFAULT_PER_DAY,
        )
        self._lock = threading.RLock()
        self._timestamps: dict[str, list[float]] = {}

    def _now(self) -> float:
        return time.time()

    def _trim(self, key: str, *, now: float) -> None:
        """day window 밖 timestamp 제거. 카운트 함수 호출 전에 실행."""
        ts = self._timestamps.get(key)
        if not ts:
            return
        cutoff = now - WINDOW_DAY_SEC
        # 정렬되어 있으므로 bisect로 빠르게 잘라냄
        idx = bisect.bisect_left(ts, cutoff)
        if idx > 0:
            del ts[:idx]

    def _count_in_window(self, ts: list[float], *, now: float, window: float) -> int:
        cutoff = now - window
        idx = bisect.bisect_left(ts, cutoff)
        return len(ts) - idx

    def check(self, key: str, *, now: float | None = None) -> RateLimitResult:
        """카운트만 확인 (dry-run). 호출 등록 안 함."""
        now = now if now is not None else self._now()
        with self._lock:
            self._trim(key, now=now)
            ts = self._timestamps.get(key, [])
            m = self._count_in_window(ts, now=now, window=WINDOW_MINUTE_SEC)
            h = self._count_in_window(ts, now=now, window=WINDOW_HOUR_SEC)
            d = len(ts)
        return self._evaluate(m=m, h=h, d=d, ts=ts, now=now)

    def acquire(self, key: str, *, now: float | None = None) -> RateLimitResult:
        """호출 시도 — 허용되면 카운터 증가, 한도 초과면 LIMITED 반환."""
        now = now if now is not None else self._now()
        with self._lock:
            self._trim(key, now=now)
            ts = self._timestamps.setdefault(key, [])
            m = self._count_in_window(ts, now=now, window=WINDOW_MINUTE_SEC)
            h = self._count_in_window(ts, now=now, window=WINDOW_HOUR_SEC)
            d = len(ts)
            result = self._evaluate(m=m, h=h, d=d, ts=ts, now=now)
            if result.status == RESULT_ALLOWED:
                ts.append(now)
                # 새 카운터 반영한 새 결과 반환
                return RateLimitResult(
                    status=RESULT_ALLOWED,
                    minute_count=m + 1,
                    hour_count=h + 1,
                    day_count=d + 1,
                )
            return result

    def _evaluate(
        self,
        *,
        m: int,
        h: int,
        d: int,
        ts: list[float],
        now: float,
    ) -> RateLimitResult:
        """현 카운트 → 결과 매핑."""
        cfg = self.config
        # 가장 빠르게 막히는 윈도우 우선 (minute > hour > day)
        if m >= cfg.per_minute:
            retry = WINDOW_MINUTE_SEC - (now - ts[-cfg.per_minute]) if ts else 0.0
            return RateLimitResult(
                status=RESULT_LIMITED,
                breached_window="minute",
                retry_after_sec=max(0.0, retry),
                minute_count=m, hour_count=h, day_count=d,
            )
        if h >= cfg.per_hour:
            retry = WINDOW_HOUR_SEC - (now - ts[-cfg.per_hour]) if ts else 0.0
            return RateLimitResult(
                status=RESULT_LIMITED,
                breached_window="hour",
                retry_after_sec=max(0.0, retry),
                minute_count=m, hour_count=h, day_count=d,
            )
        if d >= cfg.per_day:
            retry = WINDOW_DAY_SEC - (now - ts[-cfg.per_day]) if ts else 0.0
            return RateLimitResult(
                status=RESULT_LIMITED,
                breached_window="day",
                retry_after_sec=max(0.0, retry),
                minute_count=m, hour_count=h, day_count=d,
            )
        return RateLimitResult(
            status=RESULT_ALLOWED,
            minute_count=m, hour_count=h, day_count=d,
        )

    def reset(self, key: str | None = None) -> None:
        """단일 키 또는 전체 초기화 (테스트용)."""
        with self._lock:
            if key is None:
                self._timestamps.clear()
            elif key in self._timestamps:
                del self._timestamps[key]

    def size(self) -> int:
        with self._lock:
            return sum(len(v) for v in self._timestamps.values())


# ─────────────────────────── 알람 ───────────────────────────

def to_alert_payload(result: RateLimitResult, *, key: str = "") -> dict[str, object]:
    """§14.3 alert_router 호환 — 한도 초과 시 P3 알람."""
    return {
        "service": "rate_limiter",
        "severity": "P3" if result.status == RESULT_ALLOWED else "P2",
        "status": result.status,
        "breached_window": result.breached_window,
        "retry_after_sec": result.retry_after_sec,
        "minute_count": result.minute_count,
        "hour_count": result.hour_count,
        "day_count": result.day_count,
        "key_hash_prefix": key[:8] if key else "",
    }
