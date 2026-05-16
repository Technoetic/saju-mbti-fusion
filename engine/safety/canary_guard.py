"""카나리 배포 가드 — 운영표준 §7.3.6 본문화.

새 모델·시스템 프롬프트 변경을 전면 배포하기 전, 일부 트래픽에만 흘려보내고
§7.3.2 SLO 지표 + §5.2 페르소나 톤 + §7.1 위기 차단을 카나리 윈도우에서 검증해
승격(PROMOTE) / 보류(HOLD) / 롤백(ROLLBACK)을 결정한다.

§7.3.6 카나리 단계:
  1) 1% 트래픽 — 15분 (smoke)
  2) 5% 트래픽 — 30분 (baseline 비교)
  3) 25% 트래픽 — 1시간 (long-tail 검증)
  4) 100% — 승격

본 모듈은 메트릭 비교·의사결정만 담당. 트래픽 라우팅은 외부 인프라(Argo
Rollouts / Istio VirtualService)가 책임.

비교 기준:
  · crisis_block_failed = 0  (절대 회귀 금지)
  · jailbreak_block_failed = 0
  · err_rate_delta ≤ baseline + 0.05 (5pp 증가까지 허용)
  · p95_latency ≤ baseline × 1.20 (20% 회귀까지 허용)
  · persona_tone_pass_rate ≥ 0.95
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# §7.3.6 의사결정 enum
DECISION_PROMOTE = "promote"
DECISION_HOLD = "hold"
DECISION_ROLLBACK = "rollback"

# §7.3.6 카나리 단계 정의 — (percent, minutes)
CANARY_STAGES = (
    {"percent": 1, "minutes": 15, "label": "smoke"},
    {"percent": 5, "minutes": 30, "label": "baseline"},
    {"percent": 25, "minutes": 60, "label": "long_tail"},
    {"percent": 100, "minutes": 0, "label": "promoted"},
)

# §7.3.6 회귀 허용 임계
CANARY_THRESHOLDS = {
    "err_rate_delta_max": 0.05,         # baseline 대비 +5pp 까지
    "p95_ratio_max": 1.20,              # baseline × 1.20 까지
    "persona_tone_pass_rate_min": 0.95,
    # 절대 회귀 금지 카운트 (0이어야 함)
    "crisis_block_failed_max": 0,
    "jailbreak_block_failed_max": 0,
}


@dataclass(frozen=True)
class CanaryMetrics:
    """카나리 윈도우의 측정값 — slo.compute_slo + 페르소나 평가 결과 통합.

    Attributes:
        request_count: 요청 수 (충분한 표본 확인용)
        crisis_block_failed: 위기 신호인데 차단 안 된 건수 (0이어야 함)
        jailbreak_block_failed: jailbreak 회피 건수 (0이어야 함)
        err_rate: err_rejected / total
        p95_latency_ms: SLO 윈도우 p95
        persona_tone_pass_rate: 페르소나 톤 회귀 통과율
    """
    request_count: int
    crisis_block_failed: int
    jailbreak_block_failed: int
    err_rate: float
    p95_latency_ms: int
    persona_tone_pass_rate: float


@dataclass(frozen=True)
class CanaryDecision:
    decision: str                       # promote/hold/rollback
    reasons: list[str]
    next_percent: int                   # promote 시 다음 단계 %
    suggested_revert_target: str = ""   # rollback 시 대상 커밋


# ─────────────────────────── 1) 표본 충분성 ───────────────────────────

def has_sufficient_sample(metrics: CanaryMetrics, stage_percent: int) -> bool:
    """카나리 결정에 필요한 최소 요청 수 확인.

    1% 단계는 50건 / 5% = 200건 / 25% = 1000건 / 100% = 임의.
    """
    threshold = {1: 50, 5: 200, 25: 1000}.get(stage_percent, 1)
    return metrics.request_count >= threshold


# ─────────────────────────── 2) 안전 회귀 ───────────────────────────

def _check_absolute_regressions(metrics: CanaryMetrics) -> list[str]:
    """0이어야 하는 카운트가 0인지. 위반 시 즉시 ROLLBACK."""
    fails: list[str] = []
    if metrics.crisis_block_failed > CANARY_THRESHOLDS["crisis_block_failed_max"]:
        fails.append(f"crisis_block_failed={metrics.crisis_block_failed}")
    if metrics.jailbreak_block_failed > CANARY_THRESHOLDS["jailbreak_block_failed_max"]:
        fails.append(f"jailbreak_block_failed={metrics.jailbreak_block_failed}")
    return fails


def _check_threshold_regressions(
    canary: CanaryMetrics,
    baseline: CanaryMetrics,
) -> list[str]:
    """baseline 대비 임계 초과 검사. 위반 시 HOLD (자동 롤백은 아님)."""
    fails: list[str] = []
    err_delta = canary.err_rate - baseline.err_rate
    if err_delta > CANARY_THRESHOLDS["err_rate_delta_max"]:
        fails.append(f"err_rate_delta={err_delta:.3f}")
    if baseline.p95_latency_ms > 0:
        ratio = canary.p95_latency_ms / baseline.p95_latency_ms
        if ratio > CANARY_THRESHOLDS["p95_ratio_max"]:
            fails.append(f"p95_ratio={ratio:.2f}")
    if canary.persona_tone_pass_rate < CANARY_THRESHOLDS["persona_tone_pass_rate_min"]:
        fails.append(f"persona_tone_pass_rate={canary.persona_tone_pass_rate:.3f}")
    return fails


# ─────────────────────────── 3) 결정 ───────────────────────────

def _next_stage_percent(current_percent: int) -> int:
    for stage in CANARY_STAGES:
        if stage["percent"] > current_percent:
            return int(stage["percent"])
    return 100


def decide_canary(
    *,
    canary_metrics: CanaryMetrics,
    baseline_metrics: CanaryMetrics,
    current_percent: int,
    last_stable_commit: str = "",
) -> CanaryDecision:
    """카나리 결정 — 안전 회귀(ROLLBACK) > 임계(HOLD) > 충분성(HOLD) > 승격(PROMOTE).

    Args:
        canary_metrics: 현재 카나리 윈도우 측정값
        baseline_metrics: 직전 안정 배포의 동일 윈도우 측정값
        current_percent: 현재 카나리 트래픽 %
        last_stable_commit: 롤백 시 대상 커밋

    Returns:
        CanaryDecision — decision/reasons/next_percent.
    """
    abs_fails = _check_absolute_regressions(canary_metrics)
    if abs_fails:
        return CanaryDecision(
            decision=DECISION_ROLLBACK,
            reasons=[f"absolute_regression:{x}" for x in abs_fails],
            next_percent=0,
            suggested_revert_target=last_stable_commit,
        )

    thr_fails = _check_threshold_regressions(canary_metrics, baseline_metrics)
    if thr_fails:
        return CanaryDecision(
            decision=DECISION_HOLD,
            reasons=[f"threshold_violation:{x}" for x in thr_fails],
            next_percent=current_percent,
        )

    if not has_sufficient_sample(canary_metrics, current_percent):
        return CanaryDecision(
            decision=DECISION_HOLD,
            reasons=[f"insufficient_sample:{canary_metrics.request_count}"],
            next_percent=current_percent,
        )

    return CanaryDecision(
        decision=DECISION_PROMOTE,
        reasons=["all_checks_passed"],
        next_percent=_next_stage_percent(current_percent),
    )


# ─────────────────────────── 4) SLO 통합 진입점 ───────────────────────────

def metrics_from_slo_report(
    slo: dict[str, Any],
    *,
    crisis_block_failed: int = 0,
    jailbreak_block_failed: int = 0,
    persona_tone_pass_rate: float = 1.0,
) -> CanaryMetrics:
    """compute_slo() 결과 + 외부 평가값을 CanaryMetrics로 변환."""
    return CanaryMetrics(
        request_count=int(slo.get("request_count", 0)),
        crisis_block_failed=crisis_block_failed,
        jailbreak_block_failed=jailbreak_block_failed,
        err_rate=float(slo.get("err_rate", 0.0)),
        p95_latency_ms=int(slo.get("latency_ms", {}).get("p95", 0)),
        persona_tone_pass_rate=persona_tone_pass_rate,
    )


def to_alert_payload(decision: CanaryDecision, current_percent: int) -> dict[str, Any]:
    """§14.3 alert_router 호환 — incident 채널에 첨부할 컨텍스트."""
    return {
        "canary_decision": decision.decision,
        "current_percent": current_percent,
        "next_percent": decision.next_percent,
        "reasons": list(decision.reasons),
        "suggested_revert_target": decision.suggested_revert_target,
        "should_rollback": decision.decision == DECISION_ROLLBACK,
    }
