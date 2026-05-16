"""사고 사후 검토 빌더 — 운영표준 §14.8 본문화.

P0 사고 발생 후 작성해야 하는 사후 검토(postmortem) 템플릿을 구조화 형식으로
생성. incident_playbook의 postmortem_required=True 사고는 본 모듈로 작성한
보고서가 분기별 운영 리뷰에 제출된다.

§14.8 구조 (Google SRE postmortem 가이드라인 + KR PIPA §34 사고 보고 통합):
  · 메타데이터: incident_id / severity / detected_at / resolved_at / duration
  · impact: affected_users / data_categories / regulatory_notice_required
  · timeline: detection / mitigation / resolution 시각별 사건
  · root_cause: 5 Whys 분석
  · what_went_well / what_went_wrong / where_we_got_lucky
  · remediation: 단기/장기 액션 + 담당자/기한
  · regulatory_section: GDPR Art.33/34, KR PIPA §34 통지 의무 평가

본 모듈은 템플릿 생성만 — 실제 작성은 incident commander 책임.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


# §14.8 통지 의무 등급
NOTIFICATION_NONE = "none"
NOTIFICATION_INTERNAL = "internal_only"
NOTIFICATION_DPO = "dpo_review"
NOTIFICATION_REGULATOR_72H = "regulator_72h"   # GDPR Art.33 / KR PIPA §34
NOTIFICATION_USERS = "users_required"           # GDPR Art.34


@dataclass(frozen=True)
class TimelineEvent:
    timestamp_iso: str
    actor: str           # "on-call" / "system" / "user" / "auto-rollback"
    event: str
    impact: str = ""


@dataclass(frozen=True)
class RemediationAction:
    title: str
    owner: str           # 담당자 식별값
    due_date_iso: str
    priority: str        # P0/P1/P2
    completion_status: str = "pending"   # pending / in_progress / done


@dataclass(frozen=True)
class PostmortemDraft:
    incident_id: str
    title: str
    severity: str
    detected_at_iso: str
    resolved_at_iso: str
    duration_minutes: int
    affected_users_estimated: int
    data_categories_affected: tuple[str, ...]
    notification_required: str
    timeline: tuple[TimelineEvent, ...]
    five_whys: tuple[str, ...]
    what_went_well: tuple[str, ...]
    what_went_wrong: tuple[str, ...]
    where_we_got_lucky: tuple[str, ...]
    short_term_actions: tuple[RemediationAction, ...]
    long_term_actions: tuple[RemediationAction, ...]
    regulatory_notice_sent: bool = False
    incident_commander: str = ""
    related_playbook_id: str = ""


# ─────────────────────────── 통지 의무 평가 ───────────────────────────

# 데이터 카테고리 → 규제 통지 의무 등급
_NOTIFICATION_BY_DATA_CATEGORY = {
    "photo_image": NOTIFICATION_DPO,
    "photo_hash_only": NOTIFICATION_INTERNAL,
    "phone_number": NOTIFICATION_REGULATOR_72H,
    "email": NOTIFICATION_REGULATOR_72H,
    "kor_ssn": NOTIFICATION_USERS,
    "credit_card": NOTIFICATION_USERS,
    "api_key_internal": NOTIFICATION_INTERNAL,
    "crisis_signal": NOTIFICATION_DPO,
    "biometric_inference": NOTIFICATION_DPO,
    "session_log": NOTIFICATION_INTERNAL,
}


def evaluate_notification_required(
    data_categories: tuple[str, ...] | list[str],
    *,
    affected_users: int,
) -> str:
    """데이터 카테고리 + 영향 사용자 수 → 통지 의무 등급.

    가장 엄격한 카테고리 우선. 영향 사용자 0이면 NONE으로 강등.
    """
    if affected_users <= 0:
        return NOTIFICATION_NONE
    # 가장 엄격한 등급 추출
    priority_order = (
        NOTIFICATION_USERS,
        NOTIFICATION_REGULATOR_72H,
        NOTIFICATION_DPO,
        NOTIFICATION_INTERNAL,
    )
    found_levels: set[str] = set()
    for cat in data_categories:
        lvl = _NOTIFICATION_BY_DATA_CATEGORY.get(cat)
        if lvl:
            found_levels.add(lvl)
    if not found_levels:
        return NOTIFICATION_INTERNAL  # 알 수 없는 카테고리는 보수적으로 internal
    for level in priority_order:
        if level in found_levels:
            return level
    return NOTIFICATION_INTERNAL


# ─────────────────────────── 5 Whys 보조 ───────────────────────────

def build_five_whys_template(
    initial_problem: str,
) -> tuple[str, ...]:
    """5 Whys 분석 빈 템플릿. 각 단계에서 '왜?'를 5번 물어본다."""
    return (
        f"1. 왜 발생했나? — {initial_problem}",
        "2. 왜 1번 원인이 발생했나? — [작성 필요]",
        "3. 왜 2번 원인이 발생했나? — [작성 필요]",
        "4. 왜 3번 원인이 발생했나? — [작성 필요]",
        "5. 왜 4번 원인이 발생했나? — [근본 원인, 작성 필요]",
    )


# ─────────────────────────── 빌더 진입점 ───────────────────────────

def build_draft(
    *,
    incident_id: str,
    title: str,
    severity: str,
    detected_at_iso: str,
    resolved_at_iso: str,
    affected_users_estimated: int = 0,
    data_categories: tuple[str, ...] = (),
    initial_problem: str = "",
    timeline: tuple[TimelineEvent, ...] = (),
    incident_commander: str = "",
    related_playbook_id: str = "",
) -> PostmortemDraft:
    """입력값을 받아 빈 5 Whys + remediation 템플릿이 있는 draft 생성.

    팀이 review에서 채울 placeholder("[작성 필요]")가 명시적으로 보임.
    """
    # duration 계산
    try:
        dt_det = datetime.fromisoformat(detected_at_iso.replace("Z", "+00:00"))
        dt_res = datetime.fromisoformat(resolved_at_iso.replace("Z", "+00:00"))
        duration = int((dt_res - dt_det).total_seconds() / 60)
        if duration < 0:
            duration = 0
    except (ValueError, AttributeError):
        duration = 0

    notif = evaluate_notification_required(
        data_categories,
        affected_users=affected_users_estimated,
    )

    five_whys = build_five_whys_template(initial_problem)

    # 기본 remediation 템플릿
    short_term = (
        RemediationAction(
            title="회귀 테스트로 사고 재현 방지",
            owner="[담당자 작성]",
            due_date_iso="[7일 이내]",
            priority="P0",
        ),
        RemediationAction(
            title="이전 안정 버전 검증",
            owner="[담당자 작성]",
            due_date_iso="[3일 이내]",
            priority="P0",
        ),
    )
    long_term = (
        RemediationAction(
            title="알람 임계 재검토",
            owner="[담당자 작성]",
            due_date_iso="[30일 이내]",
            priority="P1",
        ),
        RemediationAction(
            title="유사 사고 방지 위한 신규 검증 모듈",
            owner="[담당자 작성]",
            due_date_iso="[90일 이내]",
            priority="P2",
        ),
    )

    return PostmortemDraft(
        incident_id=incident_id,
        title=title,
        severity=severity,
        detected_at_iso=detected_at_iso,
        resolved_at_iso=resolved_at_iso,
        duration_minutes=duration,
        affected_users_estimated=affected_users_estimated,
        data_categories_affected=tuple(data_categories),
        notification_required=notif,
        timeline=timeline,
        five_whys=five_whys,
        what_went_well=("[작성 필요]",),
        what_went_wrong=("[작성 필요]",),
        where_we_got_lucky=("[작성 필요]",),
        short_term_actions=short_term,
        long_term_actions=long_term,
        incident_commander=incident_commander,
        related_playbook_id=related_playbook_id,
    )


# ─────────────────────────── 마크다운 / JSON ───────────────────────────

def format_markdown(draft: PostmortemDraft) -> str:
    """팀에 공유할 마크다운 본문 (위키/이슈 트래커에 paste 가능)."""
    lines: list[str] = []
    lines.append(f"# Postmortem: {draft.title}")
    lines.append("")
    lines.append(f"- **Incident ID:** `{draft.incident_id}`")
    lines.append(f"- **Severity:** {draft.severity}")
    lines.append(f"- **Detected:** {draft.detected_at_iso}")
    lines.append(f"- **Resolved:** {draft.resolved_at_iso}")
    lines.append(f"- **Duration:** {draft.duration_minutes} minutes")
    lines.append(f"- **Incident Commander:** {draft.incident_commander or '[작성 필요]'}")
    if draft.related_playbook_id:
        lines.append(f"- **Playbook:** `{draft.related_playbook_id}`")
    lines.append("")

    # Impact
    lines.append("## Impact")
    lines.append(f"- Affected users (estimated): {draft.affected_users_estimated}")
    if draft.data_categories_affected:
        lines.append(f"- Data categories: {', '.join(draft.data_categories_affected)}")
    lines.append(f"- Notification required: **{draft.notification_required}**")
    lines.append("")

    # Timeline
    lines.append("## Timeline")
    if not draft.timeline:
        lines.append("- _작성 필요_")
    else:
        for ev in draft.timeline:
            extra = f" — {ev.impact}" if ev.impact else ""
            lines.append(f"- `{ev.timestamp_iso}` **{ev.actor}**: {ev.event}{extra}")
    lines.append("")

    # 5 Whys
    lines.append("## Root Cause (5 Whys)")
    for w in draft.five_whys:
        lines.append(f"- {w}")
    lines.append("")

    # WWW
    lines.append("## What Went Well")
    for x in draft.what_went_well:
        lines.append(f"- {x}")
    lines.append("")
    lines.append("## What Went Wrong")
    for x in draft.what_went_wrong:
        lines.append(f"- {x}")
    lines.append("")
    lines.append("## Where We Got Lucky")
    for x in draft.where_we_got_lucky:
        lines.append(f"- {x}")
    lines.append("")

    # Remediation
    lines.append("## Short-term Remediation")
    for a in draft.short_term_actions:
        lines.append(f"- [{a.completion_status}] [{a.priority}] **{a.title}** — "
                     f"{a.owner} (due {a.due_date_iso})")
    lines.append("")
    lines.append("## Long-term Remediation")
    for a in draft.long_term_actions:
        lines.append(f"- [{a.completion_status}] [{a.priority}] **{a.title}** — "
                     f"{a.owner} (due {a.due_date_iso})")
    lines.append("")

    # Regulatory
    lines.append("## Regulatory Notification")
    lines.append(f"- Level: **{draft.notification_required}**")
    lines.append(f"- Sent: {draft.regulatory_notice_sent}")
    if draft.notification_required in (NOTIFICATION_REGULATOR_72H,
                                       NOTIFICATION_USERS):
        lines.append("- GDPR Art.33 (72h to supervisory authority) — 검토 필요")
    if draft.notification_required == NOTIFICATION_USERS:
        lines.append("- GDPR Art.34 (users) — 검토 필요")
        lines.append("- KR PIPA §34 (개인정보 유출 통지) — 검토 필요")
    return "\n".join(lines)


def to_json(draft: PostmortemDraft) -> dict[str, Any]:
    """JSON 직렬화 — 외부 시스템 인제스트용."""
    return {
        "incident_id": draft.incident_id,
        "title": draft.title,
        "severity": draft.severity,
        "detected_at_iso": draft.detected_at_iso,
        "resolved_at_iso": draft.resolved_at_iso,
        "duration_minutes": draft.duration_minutes,
        "affected_users_estimated": draft.affected_users_estimated,
        "data_categories_affected": list(draft.data_categories_affected),
        "notification_required": draft.notification_required,
        "regulatory_notice_sent": draft.regulatory_notice_sent,
        "incident_commander": draft.incident_commander,
        "related_playbook_id": draft.related_playbook_id,
        "timeline": [
            {"timestamp_iso": ev.timestamp_iso, "actor": ev.actor,
             "event": ev.event, "impact": ev.impact}
            for ev in draft.timeline
        ],
        "five_whys": list(draft.five_whys),
        "what_went_well": list(draft.what_went_well),
        "what_went_wrong": list(draft.what_went_wrong),
        "where_we_got_lucky": list(draft.where_we_got_lucky),
        "short_term_actions": [
            {"title": a.title, "owner": a.owner, "due_date_iso": a.due_date_iso,
             "priority": a.priority, "completion_status": a.completion_status}
            for a in draft.short_term_actions
        ],
        "long_term_actions": [
            {"title": a.title, "owner": a.owner, "due_date_iso": a.due_date_iso,
             "priority": a.priority, "completion_status": a.completion_status}
            for a in draft.long_term_actions
        ],
    }
