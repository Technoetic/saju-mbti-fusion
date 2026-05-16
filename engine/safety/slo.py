"""SLO·KPI 측정 — 운영표준 §7.3.2 본문화.

§7.3.4 자동 로깅이 emit한 JSON 라인 시퀀스를 받아 운영 지표 산출.
실시간 모니터링은 외부 도구(Datadog/Grafana)에 위임하고, 본 모듈은
오프라인 분석·테스트·CI 회귀의 기준 측정기 역할.

지표 (운영표준 §7.3.2 본문):
  · request_count          — 총 요청 수
  · crisis_rate            — crisis_blocked / total (위기 차단율)
  · err_rate               — err_rejected / total (사진 불량률)
  · cache_hit_rate         — cached_hit / (cached_hit + request_completed)
  · p50 / p95 / p99 latency — elapsed_ms 백분위
  · error_code_distribution — ERR_*/WARN_* 카운트
  · region_distribution    — region별 카운트
  · language_distribution  — detected_language별 카운트
  · age_bucket_distribution — 나이 버킷별 카운트
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any, Iterable


# 운영표준 §7.3.2 SLO 임계값 (분기별 검토 기준)
SLO_THRESHOLDS = {
    "crisis_rate_max": 0.05,          # 5% 초과 시 §7.3.2.1 알람
    "err_rate_max": 0.20,             # 20% 초과 시 UI/촬영 가이드 개선
    "cache_hit_rate_min": 0.10,       # 10% 미만이면 캐시 전략 점검
    "p95_latency_ms_max": 5000,       # 5초 초과 시 LLM·인프라 점검
    "p99_latency_ms_max": 8000,
}


def _percentile(values: list[int], p: float) -> int:
    """간단한 백분위 — numpy 없이 (운영표준 §7.3.5 빠른 점검 진입점 호환)."""
    if not values:
        return 0
    sorted_v = sorted(values)
    k = max(0, min(len(sorted_v) - 1, int(round((p / 100.0) * (len(sorted_v) - 1)))))
    return sorted_v[k]


def parse_log_line(line: str) -> dict[str, Any] | None:
    """JSON 라인 한 줄을 dict로 — 파싱 실패 시 None."""
    line = line.strip()
    if not line.startswith("{"):
        return None
    try:
        d = json.loads(line)
        return d if isinstance(d, dict) else None
    except json.JSONDecodeError:
        return None


def compute_slo(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """face_reading 이벤트 시퀀스 → SLO 지표.

    Args:
        events: parse_log_line으로 미리 파싱된 dict 목록.

    Returns:
        {
            "request_count": int,
            "crisis_rate": float,
            "err_rate": float,
            "cache_hit_rate": float,
            "latency_ms": {"p50": int, "p95": int, "p99": int},
            "error_code_distribution": {"ERR_FACE_NOT_DETECTED": N, ...},
            "region_distribution": {"KR": N, ...},
            "language_distribution": {"ko": N, ...},
            "age_bucket_distribution": {"20s": N, ...},
            "slo_violations": list[str],  # 임계 위반 항목명
        }
    """
    total = 0
    crisis = 0
    err = 0
    cached = 0
    completed = 0
    latencies: list[int] = []
    error_codes: Counter[str] = Counter()
    regions: Counter[str] = Counter()
    languages: Counter[str] = Counter()
    age_buckets: Counter[str] = Counter()

    for ev in events:
        if not isinstance(ev, dict) or ev.get("service") != "face_reading":
            continue
        total += 1
        event_type = ev.get("event")
        if event_type == "crisis_blocked":
            crisis += 1
        elif event_type == "err_rejected":
            err += 1
            ec = ev.get("error_code")
            if ec:
                error_codes[ec] += 1
        elif event_type == "cached_hit":
            cached += 1
        elif event_type == "request_completed":
            completed += 1
            ec = ev.get("error_code")  # WARN_FACE_*
            if ec:
                error_codes[ec] += 1

        elapsed = ev.get("elapsed_ms")
        if isinstance(elapsed, (int, float)) and elapsed >= 0:
            latencies.append(int(elapsed))

        r = ev.get("region")
        if r:
            regions[r] += 1
        lg = ev.get("detected_language")
        if lg:
            languages[lg] += 1
        ab = ev.get("age_bucket")
        if ab:
            age_buckets[ab] += 1

    crisis_rate = crisis / total if total else 0.0
    err_rate = err / total if total else 0.0
    cache_denom = cached + completed
    cache_hit_rate = cached / cache_denom if cache_denom else 0.0

    p50 = _percentile(latencies, 50)
    p95 = _percentile(latencies, 95)
    p99 = _percentile(latencies, 99)

    violations: list[str] = []
    if crisis_rate > SLO_THRESHOLDS["crisis_rate_max"]:
        violations.append(f"crisis_rate={crisis_rate:.3f} > {SLO_THRESHOLDS['crisis_rate_max']}")
    if err_rate > SLO_THRESHOLDS["err_rate_max"]:
        violations.append(f"err_rate={err_rate:.3f} > {SLO_THRESHOLDS['err_rate_max']}")
    if cache_denom > 0 and cache_hit_rate < SLO_THRESHOLDS["cache_hit_rate_min"]:
        violations.append(f"cache_hit_rate={cache_hit_rate:.3f} < {SLO_THRESHOLDS['cache_hit_rate_min']}")
    if p95 > SLO_THRESHOLDS["p95_latency_ms_max"]:
        violations.append(f"p95={p95}ms > {SLO_THRESHOLDS['p95_latency_ms_max']}ms")
    if p99 > SLO_THRESHOLDS["p99_latency_ms_max"]:
        violations.append(f"p99={p99}ms > {SLO_THRESHOLDS['p99_latency_ms_max']}ms")

    return {
        "request_count": total,
        "crisis_rate": round(crisis_rate, 4),
        "err_rate": round(err_rate, 4),
        "cache_hit_rate": round(cache_hit_rate, 4),
        "latency_ms": {"p50": p50, "p95": p95, "p99": p99},
        "error_code_distribution": dict(error_codes),
        "region_distribution": dict(regions),
        "language_distribution": dict(languages),
        "age_bucket_distribution": dict(age_buckets),
        "slo_violations": violations,
    }


def compute_slo_from_lines(lines: Iterable[str]) -> dict[str, Any]:
    """JSON 라인 문자열 시퀀스 → SLO. 비-JSON 라인은 자동 스킵."""
    parsed = (parse_log_line(line) for line in lines)
    events = (ev for ev in parsed if ev is not None)
    return compute_slo(events)
