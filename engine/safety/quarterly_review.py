"""분기별 운영 점검 보고서 — 운영표준 §14.9 본문화.

compliance(자체점검) + SLO(운영지표) + 사고 통계 + 비용을 종합해 경영진에
제출할 1페이지 분기 리뷰를 생성. compliance_report가 정적 점검이라면 본
모듈은 분기 운영 결과를 종합 평가.

§14.9 구조:
  · header: 분기 / 시스템 / 작성일
  · executive_summary: 5문장 요약 (coverage / SLO / 사고 / 비용 / 다음 분기)
  · compliance_section: 자체 점검 coverage + 미구현 항목
  · slo_section: 분기 누적 P95/P99/crisis_rate/err_rate
  · incident_section: 분기 사고 수 (P0/P1/P2/P3) + MTTR
  · cost_section: 분기 LLM 비용 + 한도 대비
  · next_quarter_focus: 운영팀이 다음 분기 우선순위로 다룰 항목

§14.9 외부 입력 (호출자가 주입):
  · slo_summary: dict (compute_slo의 윈도우 누적 결과)
  · incidents: List[dict] (각 사고의 severity + duration_minutes)
  · cost_status: cost_guard.status 결과

본 모듈은 외부 입력을 결정론 정형화 — 점수 계산이나 추정은 안 한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class IncidentSummary:
    incident_id: str
    severity: str           # P0/P1/P2/P3
    duration_minutes: int   # 사고 지속 시간
    postmortem_done: bool = False


@dataclass(frozen=True)
class QuarterlyReview:
    quarter_label: str            # "2026Q2" 등
    generated_at_iso: str
    system_id: str
    # compliance
    compliance_coverage_percent: float
    missing_items: tuple[str, ...]
    # slo
    slo_request_count: int
    slo_p95_ms: int
    slo_p99_ms: int
    slo_crisis_rate: float
    slo_err_rate: float
    slo_cache_hit_rate: float
    slo_violations: tuple[str, ...]
    # incidents
    incident_total: int
    incident_p0: int
    incident_p1: int
    incident_p2: int
    incident_p3: int
    mttr_minutes: int             # mean time to resolution
    # cost
    monthly_spent_usd: float
    monthly_budget_usd: float
    cost_severity: str            # ok/warn/critical/exhausted
    # next quarter
    next_quarter_focus: tuple[str, ...]
    # 전체 등급
    overall_grade: str            # A/B/C/D (S 없음 — 절대 만족 금지)
    executive_summary: tuple[str, ...] = field(default_factory=tuple)


# ─────────────────────────── MTTR 계산 ───────────────────────────

def compute_mttr_minutes(incidents: list[IncidentSummary]) -> int:
    """전체 사고의 평균 해결 시간(분). 빈 리스트면 0."""
    if not incidents:
        return 0
    total = sum(i.duration_minutes for i in incidents if i.duration_minutes > 0)
    n = sum(1 for i in incidents if i.duration_minutes > 0)
    return int(total / n) if n > 0 else 0


# ─────────────────────────── 등급 평가 ───────────────────────────

def evaluate_grade(
    *,
    compliance_coverage: float,
    p0_incidents: int,
    p1_incidents: int,
    slo_violations: int,
    cost_severity: str,
) -> str:
    """전체 운영 등급 — 절대 만족 금지(S 없음).

    A: 정상 운영. P0=0, P1≤1, coverage≥95%, cost 정상
    B: 경미 회귀. P0=0, P1≤3, coverage≥90%
    C: 운영 보강 필요. P0 ≤1, P1 자유, 또는 coverage <90%
    D: 즉시 조치. P0 ≥2 또는 cost exhausted
    """
    if p0_incidents >= 2 or cost_severity == "exhausted":
        return "D"
    if p0_incidents >= 1 or compliance_coverage < 90.0:
        return "C"
    if p1_incidents > 3 or compliance_coverage < 95.0 or slo_violations > 3:
        return "B"
    if p1_incidents <= 1 and compliance_coverage >= 95.0:
        return "A"
    return "B"


# ─────────────────────────── 다음 분기 우선순위 ───────────────────────────

def derive_next_quarter_focus(
    *,
    missing_items: tuple[str, ...],
    p0_incidents: int,
    slo_violations: list[str],
    cost_severity: str,
) -> tuple[str, ...]:
    """현재 분기 결과로부터 다음 분기 우선순위 자동 추출 (최대 5개)."""
    focuses: list[str] = []
    # 1순위: P0 사고
    if p0_incidents > 0:
        focuses.append(f"P0 사고 {p0_incidents}건 재발 방지 모듈 보강")
    # 2순위: 미구현 항목
    if missing_items:
        focuses.append(f"미구현 운영표준 {len(missing_items)}건 본문화 "
                       f"({', '.join(missing_items[:3])}...)")
    # 3순위: SLO
    if slo_violations:
        focuses.append(f"SLO 위반 {len(slo_violations)}건 — "
                       f"{slo_violations[0]} 우선")
    # 4순위: cost
    if cost_severity in ("critical", "exhausted"):
        focuses.append("LLM 비용 한도 재검토 및 cost_guard 임계 조정")
    if cost_severity == "warn":
        focuses.append("LLM 비용 추세 분석 + 캐시 적중률 개선")
    # 5순위: 정기 점검 (항상 포함)
    focuses.append("compliance_report 분기 자체 점검 정기 실행")
    return tuple(focuses[:5])


# ─────────────────────────── executive summary ───────────────────────────

def build_executive_summary(review: QuarterlyReview) -> tuple[str, ...]:
    """5문장 요약 — 경영진용 (격식체)."""
    lines: list[str] = []
    # 1: compliance
    if review.compliance_coverage_percent >= 100.0:
        lines.append("운영표준 자체 점검 모든 항목 구현 완료.")
    else:
        lines.append(f"운영표준 자체 점검 {review.compliance_coverage_percent}% "
                     f"({len(review.missing_items)}개 미구현).")
    # 2: SLO
    if review.slo_violations:
        lines.append(f"SLO {len(review.slo_violations)}건 위반 발생.")
    else:
        lines.append("분기 SLO 임계 위반 없음.")
    # 3: 사고
    if review.incident_p0 > 0:
        lines.append(f"P0 사고 {review.incident_p0}건 발생 (MTTR {review.mttr_minutes}분).")
    elif review.incident_total > 0:
        lines.append(f"사고 총 {review.incident_total}건 "
                     f"(P1 {review.incident_p1} / P2 {review.incident_p2}).")
    else:
        lines.append("분기 사고 0건.")
    # 4: 비용
    pct = (review.monthly_spent_usd / review.monthly_budget_usd * 100
           if review.monthly_budget_usd > 0 else 0)
    lines.append(f"LLM 월 비용 ${review.monthly_spent_usd:.2f} "
                 f"({pct:.1f}% of 한도, severity={review.cost_severity}).")
    # 5: 등급 + 다음 분기
    lines.append(f"분기 등급 {review.overall_grade}. "
                 f"다음 분기 최우선: {review.next_quarter_focus[0] if review.next_quarter_focus else '없음'}.")
    return tuple(lines)


# ─────────────────────────── 빌더 진입점 ───────────────────────────

def build_review(
    *,
    quarter_label: str,
    system_id: str = "face_reading",
    compliance_coverage_percent: float,
    missing_items: tuple[str, ...] = (),
    slo_summary: dict[str, Any] | None = None,
    incidents: list[IncidentSummary] | None = None,
    monthly_spent_usd: float = 0.0,
    monthly_budget_usd: float = 100.0,
    cost_severity: str = "ok",
) -> QuarterlyReview:
    """입력값을 받아 QuarterlyReview 생성."""
    slo = slo_summary or {}
    inc = incidents or []

    p0 = sum(1 for i in inc if i.severity == "P0")
    p1 = sum(1 for i in inc if i.severity == "P1")
    p2 = sum(1 for i in inc if i.severity == "P2")
    p3 = sum(1 for i in inc if i.severity == "P3")
    mttr = compute_mttr_minutes(inc)

    violations = tuple(slo.get("slo_violations", []) or [])

    grade = evaluate_grade(
        compliance_coverage=compliance_coverage_percent,
        p0_incidents=p0,
        p1_incidents=p1,
        slo_violations=len(violations),
        cost_severity=cost_severity,
    )

    next_focus = derive_next_quarter_focus(
        missing_items=missing_items,
        p0_incidents=p0,
        slo_violations=list(violations),
        cost_severity=cost_severity,
    )

    review = QuarterlyReview(
        quarter_label=quarter_label,
        generated_at_iso=datetime.now(timezone.utc).isoformat(),
        system_id=system_id,
        compliance_coverage_percent=compliance_coverage_percent,
        missing_items=missing_items,
        slo_request_count=int(slo.get("request_count", 0)),
        slo_p95_ms=int(slo.get("latency_ms", {}).get("p95", 0)),
        slo_p99_ms=int(slo.get("latency_ms", {}).get("p99", 0)),
        slo_crisis_rate=float(slo.get("crisis_rate", 0.0)),
        slo_err_rate=float(slo.get("err_rate", 0.0)),
        slo_cache_hit_rate=float(slo.get("cache_hit_rate", 0.0)),
        slo_violations=violations,
        incident_total=len(inc),
        incident_p0=p0,
        incident_p1=p1,
        incident_p2=p2,
        incident_p3=p3,
        mttr_minutes=mttr,
        monthly_spent_usd=round(monthly_spent_usd, 4),
        monthly_budget_usd=round(monthly_budget_usd, 4),
        cost_severity=cost_severity,
        next_quarter_focus=next_focus,
        overall_grade=grade,
    )
    # executive_summary는 review 자체를 기반으로 계산 — frozen이므로 새 인스턴스
    summary = build_executive_summary(review)
    return QuarterlyReview(
        quarter_label=review.quarter_label,
        generated_at_iso=review.generated_at_iso,
        system_id=review.system_id,
        compliance_coverage_percent=review.compliance_coverage_percent,
        missing_items=review.missing_items,
        slo_request_count=review.slo_request_count,
        slo_p95_ms=review.slo_p95_ms,
        slo_p99_ms=review.slo_p99_ms,
        slo_crisis_rate=review.slo_crisis_rate,
        slo_err_rate=review.slo_err_rate,
        slo_cache_hit_rate=review.slo_cache_hit_rate,
        slo_violations=review.slo_violations,
        incident_total=review.incident_total,
        incident_p0=review.incident_p0,
        incident_p1=review.incident_p1,
        incident_p2=review.incident_p2,
        incident_p3=review.incident_p3,
        mttr_minutes=review.mttr_minutes,
        monthly_spent_usd=review.monthly_spent_usd,
        monthly_budget_usd=review.monthly_budget_usd,
        cost_severity=review.cost_severity,
        next_quarter_focus=review.next_quarter_focus,
        overall_grade=review.overall_grade,
        executive_summary=summary,
    )


# ─────────────────────────── 마크다운 ───────────────────────────

def format_markdown(review: QuarterlyReview) -> str:
    """경영진용 1페이지 마크다운."""
    lines: list[str] = []
    lines.append(f"# {review.quarter_label} 운영 점검 보고서 — {review.system_id}")
    lines.append(f"_Generated: {review.generated_at_iso}_")
    lines.append("")
    lines.append(f"**Overall Grade: {review.overall_grade}**")
    lines.append("")
    lines.append("## Executive Summary")
    for s in review.executive_summary:
        lines.append(f"- {s}")
    lines.append("")
    lines.append("## Compliance")
    lines.append(f"- Coverage: **{review.compliance_coverage_percent}%**")
    if review.missing_items:
        lines.append(f"- Missing: {', '.join(review.missing_items)}")
    lines.append("")
    lines.append("## SLO")
    lines.append(f"- Requests: {review.slo_request_count}")
    lines.append(f"- P95 latency: {review.slo_p95_ms}ms")
    lines.append(f"- P99 latency: {review.slo_p99_ms}ms")
    lines.append(f"- Crisis rate: {review.slo_crisis_rate:.4f}")
    lines.append(f"- Err rate: {review.slo_err_rate:.4f}")
    lines.append(f"- Cache hit rate: {review.slo_cache_hit_rate:.4f}")
    if review.slo_violations:
        lines.append(f"- Violations: {', '.join(review.slo_violations)}")
    lines.append("")
    lines.append("## Incidents")
    lines.append(f"- Total: {review.incident_total} "
                 f"(P0={review.incident_p0} / P1={review.incident_p1} / "
                 f"P2={review.incident_p2} / P3={review.incident_p3})")
    lines.append(f"- MTTR: {review.mttr_minutes} minutes")
    lines.append("")
    lines.append("## Cost")
    pct = (review.monthly_spent_usd / review.monthly_budget_usd * 100
           if review.monthly_budget_usd > 0 else 0)
    lines.append(f"- Monthly spent: ${review.monthly_spent_usd:.2f} / "
                 f"${review.monthly_budget_usd:.2f} ({pct:.1f}%)")
    lines.append(f"- Severity: **{review.cost_severity}**")
    lines.append("")
    lines.append("## Next Quarter Focus")
    for f in review.next_quarter_focus:
        lines.append(f"- {f}")
    return "\n".join(lines)


def to_json(review: QuarterlyReview) -> dict[str, Any]:
    """외부 인제스트용 JSON."""
    return {
        "quarter_label": review.quarter_label,
        "generated_at_iso": review.generated_at_iso,
        "system_id": review.system_id,
        "overall_grade": review.overall_grade,
        "executive_summary": list(review.executive_summary),
        "compliance": {
            "coverage_percent": review.compliance_coverage_percent,
            "missing_items": list(review.missing_items),
        },
        "slo": {
            "request_count": review.slo_request_count,
            "p95_ms": review.slo_p95_ms,
            "p99_ms": review.slo_p99_ms,
            "crisis_rate": review.slo_crisis_rate,
            "err_rate": review.slo_err_rate,
            "cache_hit_rate": review.slo_cache_hit_rate,
            "violations": list(review.slo_violations),
        },
        "incidents": {
            "total": review.incident_total,
            "p0": review.incident_p0,
            "p1": review.incident_p1,
            "p2": review.incident_p2,
            "p3": review.incident_p3,
            "mttr_minutes": review.mttr_minutes,
        },
        "cost": {
            "monthly_spent_usd": review.monthly_spent_usd,
            "monthly_budget_usd": review.monthly_budget_usd,
            "severity": review.cost_severity,
        },
        "next_quarter_focus": list(review.next_quarter_focus),
    }
