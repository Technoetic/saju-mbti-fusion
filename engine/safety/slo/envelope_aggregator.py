"""ADR-185 - envelope 트레이스 → KPI 비율 집계 인프라.

ADR-167/169/171/172/174 envelope 트레이스 필드:
  - safety_gate_fallback_used: bool
  - safety_gate_retry_used: bool
  - safety_gate_failures: list[str]
  - safety_gate_verdict: str
  - critic_passed: bool

집계 함수:
  - aggregate_envelopes(envelopes): 전체 KPI 비율 dict
  - aggregate_by_domain(envs_by_domain): {domain: KPI_dict}
  - envelopes_by_domain_from_logs(logs): 로그 → 도메인별 묶음
"""

from __future__ import annotations

from typing import Any


def aggregate_envelopes(envelopes: list[Any]) -> dict[str, Any]:
    """envelope 리스트 → KPI 비율 dict."""
    n = len(envelopes)
    if n == 0:
        return {
            "sample_size": 0,
            "safety_gate_fallback_rate": 0.0,
            "safety_gate_retry_rate": 0.0,
            "safety_gate_fate_assertion_rate": 0.0,
            "safety_gate_critical_rate": 0.0,
            "critic_safety_disagreement_rate": 0.0,
        }

    fallback_n = 0
    retry_n = 0
    fate_n = 0
    critical_n = 0
    disagreement_n = 0

    for env in envelopes:
        if not isinstance(env, dict):
            continue
        if env.get("safety_gate_fallback_used") is True:
            fallback_n += 1
        if env.get("safety_gate_retry_used") is True:
            retry_n += 1
        failures = env.get("safety_gate_failures") or []
        if isinstance(failures, list) and "fate_assertion_detected" in failures:
            fate_n += 1
        if env.get("safety_gate_verdict") == "critical":
            critical_n += 1
        if (env.get("critic_passed") is True
                and env.get("safety_gate_fallback_used") is True):
            disagreement_n += 1

    return {
        "sample_size": n,
        "safety_gate_fallback_rate": round(fallback_n / n, 4),
        "safety_gate_retry_rate": round(retry_n / n, 4),
        "safety_gate_fate_assertion_rate": round(fate_n / n, 4),
        "safety_gate_critical_rate": round(critical_n / n, 4),
        "critic_safety_disagreement_rate": round(disagreement_n / n, 4),
    }


def aggregate_by_domain(
    envs_by_domain: dict[str, list[Any]],
) -> dict[str, dict[str, Any]]:
    """도메인별 envelope 리스트 → 도메인별 KPI dict."""
    return {
        domain: aggregate_envelopes(envs)
        for domain, envs in envs_by_domain.items()
    }


def envelopes_by_domain_from_logs(
    logs: list[Any],
    domain_key: str = "domain",
) -> dict[str, list[Any]]:
    """로그 리스트 → {domain: envelopes} 묶음."""
    grouped: dict[str, list[Any]] = {}
    for entry in logs:
        if not isinstance(entry, dict):
            continue
        domain = entry.get(domain_key)
        if not isinstance(domain, str) or not domain:
            continue
        grouped.setdefault(domain, []).append(entry)
    return grouped
