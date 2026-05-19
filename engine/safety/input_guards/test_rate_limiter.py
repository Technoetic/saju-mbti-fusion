"""engine.safety.input_guards.rate_limiter — §7.2.19 rate limiter 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _mk(per_minute=10, per_hour=100, per_day=500):
    from engine.safety.input_guards.rate_limiter import RateLimiter, RateLimitConfig
    return RateLimiter(RateLimitConfig(
        per_minute=per_minute, per_hour=per_hour, per_day=per_day,
    ))


# ─────────────────────────── 기본 ───────────────────────────

def test_initial_acquire_allowed():
    from engine.safety.input_guards.rate_limiter import RESULT_ALLOWED
    lim = _mk()
    r = lim.acquire("uid1", now=1_700_000_000.0)
    assert r.status == RESULT_ALLOWED
    assert r.minute_count == 1
    assert r.day_count == 1


def test_check_does_not_increment():
    from engine.safety.input_guards.rate_limiter import RESULT_ALLOWED
    lim = _mk()
    lim.check("uid1", now=1_700_000_000.0)
    lim.check("uid1", now=1_700_000_000.0)
    # check만으로는 카운트 증가 안 함
    r = lim.acquire("uid1", now=1_700_000_000.0)
    assert r.status == RESULT_ALLOWED
    assert r.minute_count == 1  # acquire 한 번만 등록됨


# ─────────────────────────── 분 한도 ───────────────────────────

def test_minute_limit_blocks_11th_call():
    from engine.safety.input_guards.rate_limiter import RESULT_ALLOWED, RESULT_LIMITED
    lim = _mk(per_minute=10)
    now = 1_700_000_000.0
    for i in range(10):
        r = lim.acquire("uid1", now=now + i)
        assert r.status == RESULT_ALLOWED
    r = lim.acquire("uid1", now=now + 11)
    assert r.status == RESULT_LIMITED
    assert r.breached_window == "minute"


def test_minute_window_slides_after_60s():
    from engine.safety.input_guards.rate_limiter import RESULT_ALLOWED
    lim = _mk(per_minute=2)
    now = 1_700_000_000.0
    lim.acquire("uid1", now=now)
    lim.acquire("uid1", now=now + 1)
    # 1분+1초 뒤 첫 호출이 윈도우 밖으로 빠짐
    r = lim.acquire("uid1", now=now + 61)
    assert r.status == RESULT_ALLOWED


def test_retry_after_sec_reasonable():
    from engine.safety.input_guards.rate_limiter import RESULT_LIMITED
    lim = _mk(per_minute=2)
    now = 1_700_000_000.0
    lim.acquire("uid1", now=now)
    lim.acquire("uid1", now=now + 5)
    r = lim.acquire("uid1", now=now + 10)
    assert r.status == RESULT_LIMITED
    # 첫 호출이 60s 뒤 풀림 → 60-10=50s 정도
    assert 40 < r.retry_after_sec <= 60


# ─────────────────────────── 시간 한도 ───────────────────────────

def test_hour_limit_blocks():
    from engine.safety.input_guards.rate_limiter import RESULT_LIMITED
    lim = _mk(per_minute=100, per_hour=10, per_day=500)
    now = 1_700_000_000.0
    # 10건을 70초 간격으로 (분 한도는 안 닿음)
    for i in range(10):
        lim.acquire("uid1", now=now + i * 70)
    r = lim.acquire("uid1", now=now + 700)
    assert r.status == RESULT_LIMITED
    assert r.breached_window == "hour"


# ─────────────────────────── 일 한도 ───────────────────────────

def test_day_limit_blocks():
    from engine.safety.input_guards.rate_limiter import RESULT_LIMITED
    lim = _mk(per_minute=1000, per_hour=1000, per_day=5)
    now = 1_700_000_000.0
    for i in range(5):
        lim.acquire("uid1", now=now + i * 3600)
    # 6번째 — 분/시 안에서도 안 막힘. 일 한도 도달.
    r = lim.acquire("uid1", now=now + 5 * 3600)
    assert r.status == RESULT_LIMITED
    assert r.breached_window == "day"


# ─────────────────────────── 우선순위 ───────────────────────────

def test_minute_breach_takes_priority_over_hour():
    from engine.safety.input_guards.rate_limiter import RESULT_LIMITED
    lim = _mk(per_minute=2, per_hour=2)
    now = 1_700_000_000.0
    lim.acquire("uid1", now=now)
    lim.acquire("uid1", now=now + 1)
    r = lim.acquire("uid1", now=now + 2)
    # 분 한도도 도달, 시간 한도도 도달 — minute이 우선
    assert r.status == RESULT_LIMITED
    assert r.breached_window == "minute"


# ─────────────────────────── 키 독립 ───────────────────────────

def test_different_keys_independent():
    from engine.safety.input_guards.rate_limiter import RESULT_ALLOWED
    lim = _mk(per_minute=2)
    now = 1_700_000_000.0
    lim.acquire("uid1", now=now)
    lim.acquire("uid1", now=now + 1)
    # uid1은 한도 도달이지만 uid2는 새로운 키
    r = lim.acquire("uid2", now=now + 2)
    assert r.status == RESULT_ALLOWED


# ─────────────────────────── 트림 / day-old 청소 ───────────────────────────

def test_day_old_timestamps_trimmed():
    """86400초 전 timestamp는 자동 제거."""
    lim = _mk(per_minute=1000, per_hour=1000, per_day=1000)
    now = 1_700_000_000.0
    lim.acquire("uid1", now=now - 100000)  # 100k초 전 (>24h)
    lim.acquire("uid1", now=now)
    # check는 trim을 트리거
    r = lim.check("uid1", now=now)
    assert r.day_count == 1  # 100k초 전 항목 제거됨


# ─────────────────────────── 리셋 ───────────────────────────

def test_reset_single_key():
    from engine.safety.input_guards.rate_limiter import RESULT_ALLOWED, RESULT_LIMITED
    lim = _mk(per_minute=1)
    now = 1_700_000_000.0
    lim.acquire("uid1", now=now)
    assert lim.acquire("uid1", now=now + 1).status == RESULT_LIMITED
    lim.reset("uid1")
    assert lim.acquire("uid1", now=now + 1).status == RESULT_ALLOWED


def test_reset_all_keys():
    lim = _mk()
    lim.acquire("uid1", now=1_700_000_000.0)
    lim.acquire("uid2", now=1_700_000_000.0)
    assert lim.size() == 2
    lim.reset()
    assert lim.size() == 0


# ─────────────────────────── 알람 페이로드 ───────────────────────────

def test_alert_allowed_is_p3():
    from engine.safety.input_guards.rate_limiter import to_alert_payload, RESULT_ALLOWED, RateLimitResult
    r = RateLimitResult(status=RESULT_ALLOWED, minute_count=1)
    p = to_alert_payload(r)
    assert p["severity"] == "P3"


def test_alert_limited_is_p2():
    from engine.safety.input_guards.rate_limiter import to_alert_payload, RESULT_LIMITED, RateLimitResult
    r = RateLimitResult(status=RESULT_LIMITED, breached_window="minute",
                        retry_after_sec=30.0)
    p = to_alert_payload(r, key="userhash12345")
    assert p["severity"] == "P2"
    assert p["breached_window"] == "minute"
    assert p["key_hash_prefix"] == "userhash"  # 처음 8자만


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_rate_limiter():
    import engine.safety as safety
    assert hasattr(safety, "RateLimiter")
    assert hasattr(safety, "RateLimitConfig")
    assert hasattr(safety, "RateLimitResult")
    assert hasattr(safety, "RESULT_ALLOWED")
    assert hasattr(safety, "RESULT_LIMITED")
    assert hasattr(safety, "DEFAULT_PER_MINUTE")
    assert hasattr(safety, "DEFAULT_PER_HOUR")
    assert hasattr(safety, "DEFAULT_PER_DAY")
