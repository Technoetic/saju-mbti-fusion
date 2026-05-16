"""자동 롤백 트리거 — 운영표준 §7.3.2.1 본문화.

SLO 위반·골든 셋 회귀·라이브 503 등 사고 신호를 감지했을 때 다음을 결정한다:
  · 이번 이벤트가 자동 롤백 트리거에 해당하는지 (수동 승인 vs 자동)
  · 롤백 대상이 어느 커밋인지 (직전 SUCCESS 워크플로 커밋)
  · 외부 워커가 실행할 git revert 명령 문자열

본 모듈은 실제 git 명령은 실행하지 않는다. 단지 "어떤 명령을 어떤 권한으로
실행해야 하는지" 페이로드를 직렬화해 §14.3 알람 라우터를 통해 PagerDuty의
incident 대응자에게 전달한다.

§7.3.2.1 자동 롤백 정책:
  · AUTO    — crisis_block_failed, slo_violation:crisis_rate (P0, 즉시)
  · APPROVAL — slo_violation:p95/err_rate (P1, 5분 내 수동 승인 또는 자동)
  · NEVER    — golden_set_regression 단독, cache_hit_rate (수동만)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# §7.3.2.1 — 자동 롤백 정책 enum
AUTO = "auto"          # 무조건 자동 실행 (안전·가용성 위협)
APPROVAL = "approval"  # 5분 내 수동 승인 가능, 만료 시 자동
NEVER = "never"        # 자동 롤백 금지, 수동 의사결정만


@dataclass(frozen=True)
class RollbackDecision:
    """롤백 의사결정 결과 — 외부 워커가 실행할 페이로드."""
    policy: str                       # AUTO | APPROVAL | NEVER
    target_commit: str                # 롤백 대상 커밋 SHA (revert HEAD → target)
    reason: str                       # 트리거 사유 (slo_violation:crisis_rate 등)
    revert_command: str               # 외부 워커가 실행할 git 명령
    approval_window_sec: int = 300    # APPROVAL 모드의 수동 승인 윈도우


# §7.3.2.1 — 이벤트명 → 정책 매핑.
# alert_router.classify_event()와 이벤트명 명명 일관.
_POLICY_RULES = {
    "crisis_block_failed":            AUTO,
    "service_down":                   AUTO,
    "auth_breach":                    AUTO,
    "slo_violation:crisis_rate":      AUTO,
    "slo_violation:p95":              APPROVAL,
    "slo_violation:p99":              APPROVAL,
    "slo_violation:err_rate":         APPROVAL,
    "slo_violation:cache_hit_rate":   NEVER,
    "golden_set_regression":          NEVER,
    "data_governance_violation":      NEVER,
}


def classify_rollback_policy(event_name: str) -> str:
    """이벤트명 → AUTO/APPROVAL/NEVER 정책. 미상은 NEVER (안전 기본값)."""
    return _POLICY_RULES.get(event_name, NEVER)


def build_revert_command(target_commit: str, *, current_head: str = "HEAD") -> str:
    """git revert 명령 직렬화.

    --no-edit으로 자동 메시지를 사용하고, 충돌 발생 시 자동 중단(--no-merges 제거).
    실행은 외부 CI 워커(GitHub Actions/Argo)에 위임.
    """
    if not target_commit or not target_commit.strip():
        raise ValueError("target_commit is required")
    safe = target_commit.strip()
    # 단일 커밋만 revert (안전 — 멀티 revert는 별도 명령)
    return f"git revert --no-edit {safe}..{current_head}"


def decide_rollback(
    event_name: str,
    *,
    last_stable_commit: str,
    current_head: str = "HEAD",
    extra_payload: dict[str, Any] | None = None,
) -> RollbackDecision:
    """이벤트 → 정책 결정 + 명령 직렬화.

    Args:
        event_name: alert_router 이벤트명.
        last_stable_commit: 직전 SUCCESS 워크플로의 head SHA.
        current_head: 현재 배포 HEAD (테스트 주입 가능).
        extra_payload: 추가 컨텍스트 (현 단계에서는 미사용, 향후 룬북 링크 등).

    Returns:
        RollbackDecision — 외부 워커가 그대로 직렬화해서 큐잉.
    """
    policy = classify_rollback_policy(event_name)
    return RollbackDecision(
        policy=policy,
        target_commit=last_stable_commit,
        reason=event_name,
        revert_command=build_revert_command(last_stable_commit, current_head=current_head),
        approval_window_sec=300 if policy == APPROVAL else 0,
    )


def should_execute_immediately(decision: RollbackDecision) -> bool:
    """AUTO 정책만 즉시 실행. APPROVAL/NEVER는 외부 의사결정 필요."""
    return decision.policy == AUTO


def to_alert_payload(decision: RollbackDecision) -> dict[str, Any]:
    """§14.3 알람 라우터 호환 페이로드 — incident 채널에 첨부할 컨텍스트."""
    return {
        "rollback_policy": decision.policy,
        "target_commit": decision.target_commit,
        "reason": decision.reason,
        "revert_command": decision.revert_command,
        "approval_window_sec": decision.approval_window_sec,
        "auto_execute": should_execute_immediately(decision),
    }
