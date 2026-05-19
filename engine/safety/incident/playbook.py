"""응급 사고 대응 플레이북 — 운영표준 §14.7 본문화.

운영 사고 발생 시 단계별 대응 절차를 구조화. on-call 운영자가 알람을 받았을
때 "지금 무엇을 해야 하는가"를 즉시 알 수 있다.

§14.7 구조:
  · 사고 유형별 (incident_id) → severity / steps / verify / postmortem
  · severity: P0 (즉시) / P1 (15분) / P2 (4시간) / P3 (다음 영업일)
  · steps: 번호별 행동 (CLI 명령, 확인할 모듈, 의사결정 분기)
  · verify: 사고 해결 확인 방법
  · postmortem_required: 사후 검토 작성 필요 여부

본 모듈은 정적 플레이북만 — 실행은 외부 on-call 운영자에 위임.
alert_router.AlertEvent와 incident_id가 1:1 매핑되도록 설계.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# §14.7 사고 식별자 (alert_router 이벤트명과 일관)
INCIDENT_CRISIS_BLOCK_FAILED = "crisis_block_failed"
INCIDENT_SLO_CRISIS_RATE = "slo_violation:crisis_rate"
INCIDENT_SLO_P95 = "slo_violation:p95"
INCIDENT_SLO_ERR_RATE = "slo_violation:err_rate"
INCIDENT_PII_LEAK = "pii_leak_detected"
INCIDENT_COST_EXHAUSTED = "cost_exhausted"
INCIDENT_CACHE_CORRUPTION = "cache_corruption"
INCIDENT_BACKUP_OVERDUE = "backup_overdue"
INCIDENT_CANARY_ROLLBACK = "canary_rollback"
INCIDENT_RATE_ABUSE = "rate_abuse"
INCIDENT_JAILBREAK_LEAK = "jailbreak_leak"


@dataclass(frozen=True)
class PlaybookStep:
    """단일 행동 단계."""
    order: int
    title: str
    detail: str
    command: str = ""               # 실행할 CLI/Python (선택)
    decision_branch: str = ""       # if/then 분기 설명 (선택)
    expected_seconds: int = 0       # 예상 소요 시간


@dataclass(frozen=True)
class IncidentPlaybook:
    incident_id: str
    title: str
    severity: str                   # P0/P1/P2/P3
    sla_minutes: int                # 응답 SLA
    summary: str
    steps: tuple[PlaybookStep, ...]
    verify: str                     # 사고 해결 확인 방법
    postmortem_required: bool
    related_modules: tuple[str, ...] = field(default_factory=tuple)


# ─────────────────────────── 플레이북 매니페스트 ───────────────────────────

_PLAYBOOKS: tuple[IncidentPlaybook, ...] = (
    # ── P0: 위기 차단 실패 ──
    IncidentPlaybook(
        incident_id=INCIDENT_CRISIS_BLOCK_FAILED,
        title="위기 신호 차단 실패",
        severity="P0",
        sla_minutes=0,
        summary=(
            "crisis_detector가 위기 신호를 잡았어야 하는데 LLM 호출까지 진행됨. "
            "법적 책임(Character.AI 선례)와 사용자 안전 직접 위협."
        ),
        steps=(
            PlaybookStep(
                order=1,
                title="라이브 트래픽 100% rate limit 적용",
                detail="신규 요청을 즉시 차단하여 추가 사고 방지.",
                command="railway 환경변수 RATE_LIMIT_PER_MIN=0 으로 설정",
                expected_seconds=60,
            ),
            PlaybookStep(
                order=2,
                title="rollback_trigger 자동 실행 확인",
                detail="AUTO 정책 — 직전 안정 커밋으로 자동 revert 진행 중인지.",
                command="gh run list --limit 1",
                decision_branch="진행 중이면 대기, 누락이면 수동 git revert",
                expected_seconds=120,
            ),
            PlaybookStep(
                order=3,
                title="누락된 위기 키워드 식별",
                detail="이번 사고의 화두 본문이 어떤 표현이었는지 트레이싱에서 추출.",
                command="railway logs --tail 200 | grep crisis",
                expected_seconds=180,
            ),
            PlaybookStep(
                order=4,
                title="crisis_detector 키워드 사전 보강",
                detail="DIRECT_SUICIDE_KEYWORDS / INDIRECT_DESPAIR_KEYWORDS 추가.",
                command="engine/safety/crisis_detector.py 편집",
                expected_seconds=300,
            ),
            PlaybookStep(
                order=5,
                title="회귀 테스트 + 재배포",
                detail="test_crisis_multilingual.py 통과 후 main에 푸시.",
                command="pytest engine/safety/test_crisis_multilingual.py -v && git push",
                expected_seconds=600,
            ),
            PlaybookStep(
                order=6,
                title="법무팀·DPO 통보",
                detail="사고 보고 + 영향 사용자 식별 + 72시간 내 통지 의무 검토 (GDPR Art.33).",
                expected_seconds=900,
            ),
        ),
        verify=(
            "test_crisis_multilingual.py 통과 + 라이브 트래픽에서 같은 표현 차단 확인 + "
            "alert_router에서 crisis_block_failed 미발생 24시간"
        ),
        postmortem_required=True,
        related_modules=("engine.safety.crisis.detector",
                         "engine.safety.crisis.resources",
                         "engine.safety.incident.rollback_trigger"),
    ),
    # ── P0: PII 누출 ──
    IncidentPlaybook(
        incident_id=INCIDENT_PII_LEAK,
        title="응답에 PII 누출",
        severity="P0",
        sla_minutes=0,
        summary=(
            "scan_response_pii가 응답에서 전화번호/이메일/주민번호/API 키 검출. "
            "GDPR Art.34 통지 의무 가능."
        ),
        steps=(
            PlaybookStep(
                order=1,
                title="해당 응답 캐시 즉시 삭제",
                detail="cache_integrity.list_corrupt_files로 PII 포함 캐시 식별 후 unlink.",
                command="railway ssh 'python -c \"from engine.safety import list_corrupt_files; ...\"'",
                expected_seconds=120,
            ),
            PlaybookStep(
                order=2,
                title="LLM 백엔드 임시 stub 폴백",
                detail="llm_fallback_router를 통해 deterministic_stub 응답으로 강제.",
                command="환경변수 FORCE_STUB_FALLBACK=true",
                expected_seconds=60,
            ),
            PlaybookStep(
                order=3,
                title="영향 사용자 식별",
                detail="tracing 로그에서 cached_hit + pii_leak 동시 발생 uid_hash 추출.",
                command="railway logs --tail 1000 | grep pii_leak",
                expected_seconds=600,
            ),
            PlaybookStep(
                order=4,
                title="DPO 통보 + GDPR Art.34 통지 평가",
                detail="중대성 평가 후 72시간 내 사용자·감독기관 통지 결정.",
                expected_seconds=3600,
            ),
        ),
        verify="라이브 N개 응답 샘플링 + scan_response_pii 0건",
        postmortem_required=True,
        related_modules=("engine.safety.llm.response_pii_leak",
                         "engine.safety.input_guards.cache_integrity",
                         "engine.safety.incident.llm_fallback_router"),
    ),
    # ── P1: SLO p95 latency ──
    IncidentPlaybook(
        incident_id=INCIDENT_SLO_P95,
        title="응답 p95 latency 초과",
        severity="P1",
        sla_minutes=15,
        summary=(
            "compute_slo가 p95 > 5000ms 위반 감지. 사용자 경험·전환 영향."
        ),
        steps=(
            PlaybookStep(
                order=1,
                title="latency_audit으로 단계별 분해",
                detail="어느 단계(LLM call / safety_gate / cache)가 느린지 확인.",
                command="railway ssh 'python -c \"from engine.safety import run_quick_check; ...\"'",
                expected_seconds=120,
            ),
            PlaybookStep(
                order=2,
                title="LLM 백엔드 polling",
                detail="Gemini/Claude 상태 페이지 확인. 둘 다 장애면 stub fallback 평가.",
                expected_seconds=180,
            ),
            PlaybookStep(
                order=3,
                title="canary_guard 결정 검토",
                detail="새 배포가 회귀 일으켰는지. HOLD/ROLLBACK 권고 시 즉시 실행.",
                expected_seconds=300,
            ),
            PlaybookStep(
                order=4,
                title="필요 시 git revert",
                detail="canary_guard.suggested_revert_target으로 직전 안정 커밋.",
                expected_seconds=600,
            ),
        ),
        verify="5분 윈도우 compute_slo가 p95 < 5000ms 복귀",
        postmortem_required=False,
        related_modules=("engine.safety.slo.slo",
                         "engine.safety.slo.latency_audit",
                         "engine.safety.input_guards.canary_guard",
                         "engine.safety.incident.rollback_trigger"),
    ),
    # ── P1: jailbreak 누출 ──
    IncidentPlaybook(
        incident_id=INCIDENT_JAILBREAK_LEAK,
        title="응답에 jailbreak 카테고리 누출",
        severity="P1",
        sla_minutes=15,
        summary=(
            "jailbreak_defense를 통과했지만 LLM 응답에 시스템 프롬프트 노출, "
            "의료/법률 단정, 인종 일반화 같은 카테고리 검출."
        ),
        steps=(
            PlaybookStep(
                order=1,
                title="누락된 jailbreak 패턴 식별",
                detail="입력 화두에서 detect_jailbreak가 빈 결과 반환한 케이스 추출.",
                command="railway logs --tail 500 | grep jailbreak",
                expected_seconds=300,
            ),
            PlaybookStep(
                order=2,
                title="jailbreak_defense 패턴 보강",
                detail="_PERSONA_OVERRIDE_PATTERNS 또는 _FORBIDDEN_ADVICE_PATTERNS 추가.",
                command="engine/safety/jailbreak_defense.py 편집",
                expected_seconds=300,
            ),
            PlaybookStep(
                order=3,
                title="회귀 + 셰도우 평가",
                detail="새 패턴이 false positive 늘리지 않는지 shadow_eval로 확인.",
                command="pytest engine/safety/test_jailbreak_defense.py -v",
                expected_seconds=300,
            ),
        ),
        verify="라이브 trace에서 jailbreak_blocked 적절히 증가, 응답 누출 0건",
        postmortem_required=False,
        related_modules=("engine.safety.llm.jailbreak_defense",
                         "engine.safety.llm.output_safety_gate"),
    ),
    # ── P1: 비용 한도 도달 ──
    IncidentPlaybook(
        incident_id=INCIDENT_COST_EXHAUSTED,
        title="LLM 비용 한도 도달",
        severity="P1",
        sla_minutes=15,
        summary=(
            "cost_guard.status가 exhausted. 신규 호출은 stub fallback으로 진행 중. "
            "비용 폭발 방지 + 한도 조정 결정 필요."
        ),
        steps=(
            PlaybookStep(
                order=1,
                title="비용 누적 원인 분석",
                detail="claude_vision 호출 비율, 토큰 평균, rate_limiter 우회 여부 확인.",
                expected_seconds=300,
            ),
            PlaybookStep(
                order=2,
                title="rate_limiter 한도 임시 강화",
                detail="abuse 의심이면 per_minute 5건으로 축소.",
                command="환경변수 RATE_LIMIT_PER_MIN=5",
                expected_seconds=60,
            ),
            PlaybookStep(
                order=3,
                title="한도 조정 또는 회계팀 보고",
                detail="정상 트래픽이면 한도 증액 결재 요청, abuse면 차단.",
                expected_seconds=1200,
            ),
        ),
        verify="cost_guard.status가 ok/warn으로 복귀, 24시간 stub fallback 사용률 감소",
        postmortem_required=False,
        related_modules=("engine.safety.input_guards.cost_guard", "engine.safety.input_guards.rate_limiter"),
    ),
    # ── P2: 캐시 무결성 위반 ──
    IncidentPlaybook(
        incident_id=INCIDENT_CACHE_CORRUPTION,
        title="캐시 손상 비율 임계 초과",
        severity="P2",
        sla_minutes=240,
        summary=(
            "audit_cache_directory가 손상율 > 5% 보고. JSON 파싱 실패·필수 키 누락·"
            "PII 누출 등."
        ),
        steps=(
            PlaybookStep(
                order=1,
                title="list_corrupt_files로 손상 파일 식별",
                detail="cache_integrity.list_corrupt_files로 손상 캐시 경로 목록 추출.",
                command="from engine.safety import list_corrupt_files",
                expected_seconds=60,
            ),
            PlaybookStep(
                order=2,
                title="손상 파일 일괄 삭제",
                detail="cache_janitor.run_janitor를 강제 TTL=0으로 호출.",
                expected_seconds=120,
            ),
            PlaybookStep(
                order=3,
                title="시스템 프롬프트 해시 mismatch 여부 확인",
                detail="배포 직후라면 정상 — 새 캐시가 생성될 때까지 대기.",
                expected_seconds=300,
            ),
        ),
        verify="audit_cache_directory 손상율 < 1%",
        postmortem_required=False,
        related_modules=("engine.safety.input_guards.cache_integrity",
                         "engine.safety.input_guards.cache_janitor"),
    ),
    # ── P2: 백업 RPO 초과 ──
    IncidentPlaybook(
        incident_id=INCIDENT_BACKUP_OVERDUE,
        title="백업 RPO 초과",
        severity="P2",
        sla_minutes=240,
        summary=(
            "overdue_backups가 자원 1개 이상 보고. governance_audit(P0 자원)은 7년 보관."
        ),
        steps=(
            PlaybookStep(
                order=1,
                title="외부 백업 워커 상태 확인",
                detail="rsync/restic/S3-sync 워커가 동작 중인지.",
                expected_seconds=300,
            ),
            PlaybookStep(
                order=2,
                title="수동 백업 실행",
                detail="자동 워커 복구 전까지 수동 실행으로 RPO 회복.",
                expected_seconds=900,
            ),
            PlaybookStep(
                order=3,
                title="verify_backup_record로 무결성 확인",
                detail="bytes/sha256/duration 검증 통과해야 백업 인정.",
                expected_seconds=120,
            ),
        ),
        verify="overdue_backups 빈 리스트, 모든 자원 RPO 내",
        postmortem_required=False,
        related_modules=("engine.safety.incident.backup_manifest",),
    ),
    # ── P2: rate abuse ──
    IncidentPlaybook(
        incident_id=INCIDENT_RATE_ABUSE,
        title="단일 사용자 rate 한도 반복 초과",
        severity="P2",
        sla_minutes=240,
        summary=(
            "특정 uid가 분당 한도를 반복 초과. 자동화 의심 + 비용 영향."
        ),
        steps=(
            PlaybookStep(
                order=1,
                title="abuse uid 식별 + 임시 차단",
                detail="rate_limiter에서 일정 시간 reset 없이 유지 + IAM 측 차단.",
                expected_seconds=300,
            ),
            PlaybookStep(
                order=2,
                title="과거 트래픽 패턴 분석",
                detail="해당 uid가 jailbreak 시도/PII 입력 패턴 있었는지.",
                expected_seconds=600,
            ),
        ),
        verify="해당 uid 24시간 rate_limit 미발생, 정상 트래픽만",
        postmortem_required=False,
        related_modules=("engine.safety.input_guards.rate_limiter",),
    ),
)


# ─────────────────────────── Public API ───────────────────────────

def get_all_playbooks() -> tuple[IncidentPlaybook, ...]:
    return _PLAYBOOKS


def get_playbook(incident_id: str) -> IncidentPlaybook | None:
    for p in _PLAYBOOKS:
        if p.incident_id == incident_id:
            return p
    return None


def list_playbooks_by_severity(severity: str) -> list[IncidentPlaybook]:
    return [p for p in _PLAYBOOKS if p.severity == severity]


def list_p0_playbooks() -> list[IncidentPlaybook]:
    """P0 즉시 호출 대상만."""
    return list_playbooks_by_severity("P0")


def format_playbook_text(playbook: IncidentPlaybook) -> str:
    """on-call 운영자가 보기 좋은 사람-읽기 텍스트."""
    lines: list[str] = []
    lines.append(f"# [{playbook.severity}] {playbook.title}")
    lines.append(f"_SLA: {playbook.sla_minutes}분 / "
                 f"Postmortem: {'필수' if playbook.postmortem_required else '선택'}_")
    lines.append("")
    lines.append(playbook.summary)
    lines.append("")
    lines.append("## 대응 절차")
    for step in playbook.steps:
        lines.append(f"### {step.order}. {step.title}")
        lines.append(step.detail)
        if step.command:
            lines.append(f"  · 명령: `{step.command}`")
        if step.decision_branch:
            lines.append(f"  · 분기: {step.decision_branch}")
        if step.expected_seconds:
            lines.append(f"  · 예상: {step.expected_seconds}초")
        lines.append("")
    lines.append("## 해결 확인")
    lines.append(playbook.verify)
    if playbook.related_modules:
        lines.append("")
        lines.append("## 관련 모듈")
        for m in playbook.related_modules:
            lines.append(f"- `{m}`")
    return "\n".join(lines)


def to_alert_attachment(playbook: IncidentPlaybook) -> dict[str, Any]:
    """alert_router 알람에 첨부할 요약 페이로드."""
    return {
        "playbook_id": playbook.incident_id,
        "playbook_title": playbook.title,
        "severity": playbook.severity,
        "sla_minutes": playbook.sla_minutes,
        "first_step": playbook.steps[0].title if playbook.steps else "",
        "total_steps": len(playbook.steps),
        "postmortem_required": playbook.postmortem_required,
    }
