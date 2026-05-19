"""신규 입사자 온보딩 체크리스트 — 운영표준 §14.6 본문화.

운영자가 face_reading 안전 모듈을 학습할 순서를 단계별로 정의. compliance
audit과 달리 "지금 시스템이 무엇을 가지고 있는가"가 아니라 "운영자가 그것을
어떻게 배워야 하는가"의 학습 경로.

§14.6 4단계:
  · Day 1 — 기본기 (페르소나 / 위기 / PII / 면책)
  · Week 1 — 실 운영 (SLO / alert / canary / 롤백)
  · Month 1 — 규제 (GDPR / EU AI Act / KR PIPA / DSR)
  · Ongoing — 정기 점검 (compliance / shadow / 회귀)

각 단계는 (학습 항목, 추천 모듈, 실습 명령) 묶음. 진행 상황을 외부에서
persist하기 쉽도록 상태(NOT_STARTED/IN_PROGRESS/COMPLETED)를 외부 인자로
받아 처리.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# §14.6 단계 식별자
PHASE_DAY1 = "day1"
PHASE_WEEK1 = "week1"
PHASE_MONTH1 = "month1"
PHASE_ONGOING = "ongoing"

# §14.6 학습 항목 상태
STATUS_NOT_STARTED = "not_started"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"


@dataclass(frozen=True)
class ChecklistItem:
    item_id: str
    phase: str
    title: str
    summary: str
    modules: tuple[str, ...]
    practice_command: str = ""    # 실습 명령 (railway ssh / pytest 등)
    estimated_minutes: int = 0
    references: tuple[str, ...] = field(default_factory=tuple)


# §14.6 학습 항목 매니페스트 — 4단계 × N개 항목
_CHECKLIST: tuple[ChecklistItem, ...] = (
    # ── Day 1 ──
    ChecklistItem(
        item_id="d1_persona",
        phase=PHASE_DAY1,
        title="운학 도사 페르소나 이해",
        summary=(
            "face_reading의 시스템 프롬프트가 정의하는 사극풍 캐릭터를 학습하고, "
            "응답 톤이 회귀하지 않도록 persona_self_eval로 측정한다."
        ),
        modules=("engine.divination.face.reading._FACE_SYSTEM",
                 "engine.safety.llm.persona_self_eval"),
        practice_command=(
            "python -c 'from engine.safety import evaluate_persona_tone; "
            "print(evaluate_persona_tone(\"허허, 그대, 자네의 결이로구먼.\"))'"
        ),
        estimated_minutes=30,
        references=("§5.2.5",),
    ),
    ChecklistItem(
        item_id="d1_crisis",
        phase=PHASE_DAY1,
        title="위기 신호 결정론 차단",
        summary=(
            "ko/en/ja/zh 4언어 위기 키워드 사전이 어떤 표현을 차단하는지 익히고, "
            "false positive(꿈/3인칭) 회피 패턴을 확인한다."
        ),
        modules=("engine.safety.crisis.detector",
                 "engine.safety.crisis.resources"),
        practice_command=(
            "python -c 'from engine.safety import detect_crisis; "
            "print(detect_crisis(\"자살하고 싶다\"))'"
        ),
        estimated_minutes=45,
        references=("§5.2.7", "Character.AI 2024 precedent"),
    ),
    ChecklistItem(
        item_id="d1_pii",
        phase=PHASE_DAY1,
        title="PII 마스킹과 응답 누출 검출",
        summary=(
            "입력의 PII는 mask_pii로 마스킹하고, 응답에 PII가 들어오면 "
            "scan_response_pii로 검출해 폐기한다."
        ),
        modules=("engine.safety.gdpr.pii", "engine.safety.llm.response_pii_leak"),
        practice_command=(
            "python -c 'from engine.safety import scan_response_pii; "
            "print(scan_response_pii(\"010-1234-5678\").leaks)'"
        ),
        estimated_minutes=30,
        references=("§7.2.5", "§7.2.18", "GDPR Art.32"),
    ),
    ChecklistItem(
        item_id="d1_legal",
        phase=PHASE_DAY1,
        title="법정 면책 자동 첨부",
        summary=(
            "ko/en/ja/zh 4언어 면책 텍스트가 모든 응답에 자동 첨부되는지 확인. "
            "위기 응답에는 별도 위기 면책이 더해진다."
        ),
        modules=("engine.safety.gdpr.legal_notice",),
        practice_command=(
            "python -c 'from engine.safety import build_legal_footer; "
            "print(build_legal_footer(is_crisis=False, lang=\"ko\")[:50])'"
        ),
        estimated_minutes=15,
        references=("§7.1", "의료법 §27", "변호사법 §109"),
    ),

    # ── Week 1 ──
    ChecklistItem(
        item_id="w1_slo",
        phase=PHASE_WEEK1,
        title="SLO 측정과 quick_check",
        summary=(
            "운영 윈도우의 P95/P99 latency와 crisis_rate를 산출하고, SSH로 "
            "quick_check를 호출해 시스템 헬스를 한 화면으로 확인한다."
        ),
        modules=("engine.safety.slo.slo", "engine.safety.misc.quick_check",
                 "engine.safety.slo.latency_audit"),
        practice_command="railway ssh \"python -c 'from engine.safety import run_quick_check; print(run_quick_check())'\"",
        estimated_minutes=60,
        references=("§7.3.2", "§7.3.5", "§7.2.24"),
    ),
    ChecklistItem(
        item_id="w1_alerts",
        phase=PHASE_WEEK1,
        title="알람 라우터 P0~P3",
        summary=(
            "SLO 위반 / 비용 초과 / 백업 실패 등의 이벤트가 P0~P3 어느 채널로 "
            "라우팅되는지 학습. Slack/PagerDuty 페이로드 형식 확인."
        ),
        modules=("engine.safety.crisis.alert_router",),
        practice_command=(
            "python -c 'from engine.safety import classify_event; "
            "print(classify_event(\"crisis_block_failed\"))'"
        ),
        estimated_minutes=45,
        references=("§14.3",),
    ),
    ChecklistItem(
        item_id="w1_canary_rollback",
        phase=PHASE_WEEK1,
        title="카나리 배포와 자동 롤백",
        summary=(
            "1%→5%→25%→100% 카나리 단계와 PROMOTE/HOLD/ROLLBACK 결정, "
            "rollback_trigger의 AUTO/APPROVAL/NEVER 정책을 학습."
        ),
        modules=("engine.safety.input_guards.canary_guard", "engine.safety.incident.rollback_trigger"),
        practice_command="pytest engine/safety/test_canary_guard.py -v",
        estimated_minutes=60,
        references=("§7.3.6", "§7.3.2.1"),
    ),
    ChecklistItem(
        item_id="w1_cost",
        phase=PHASE_WEEK1,
        title="LLM 비용 가드와 rate limiter",
        summary=(
            "Gemini/Claude 가격, 일/월 한도, exhausted 시 stub 폴백을 학습. "
            "uid별 분당/시간당 한도와 sliding window 알고리즘 이해."
        ),
        modules=("engine.safety.input_guards.cost_guard", "engine.safety.input_guards.rate_limiter"),
        practice_command="pytest engine/safety/test_cost_guard.py -q",
        estimated_minutes=45,
        references=("§7.2.17", "§7.2.19"),
    ),

    # ── Month 1 ──
    ChecklistItem(
        item_id="m1_gdpr_dsr",
        phase=PHASE_MONTH1,
        title="GDPR / KR PIPA / DSR 처리",
        summary=(
            "데이터 주체 요청(DSR) 7권리(access/rectify/erase/restrict/portability/"
            "object/withdraw_consent)와 지역별 SLA(KR 10일 / EU 30일)를 학습."
        ),
        modules=("engine.safety.gdpr.rights_information",
                 "engine.safety.gdpr.dsr_processor"),
        practice_command=(
            "python -c 'from engine.safety import DSRRequest, process_dsr; "
            "print(process_dsr(DSRRequest(right_key=\"access\", subject_id=\"u\", "
            "authenticated=True, region=\"KR\")))'"
        ),
        estimated_minutes=120,
        references=("§10", "§14.2", "GDPR Art.15-22", "KR PIPA §35-37"),
    ),
    ChecklistItem(
        item_id="m1_eu_ai_act",
        phase=PHASE_MONTH1,
        title="EU AI Act §50(3) 감정 추론 명시 고지",
        summary=(
            "EU 27개 회원국 + 'EU' 코드 지역의 사용자에게는 감정 추론이 포함되어 "
            "있다는 명시 고지가 응답에 자동 첨부되는지 확인."
        ),
        modules=("engine.safety.crisis.emotion_disclosure",),
        practice_command=(
            "python -c 'from engine.safety import inject_emotion_disclosure; "
            "print(inject_emotion_disclosure(\"허허\", region=\"DE\", lang=\"en\"))'"
        ),
        estimated_minutes=60,
        references=("EU AI Act Art.50(3)", "EU AI Act §5(f)"),
    ),
    ChecklistItem(
        item_id="m1_governance",
        phase=PHASE_MONTH1,
        title="데이터 거버넌스와 백업",
        summary=(
            "골든 셋·평가셋의 출처/동의/라이선스 검증, 백업 RPO/RTO 매트릭스, "
            "감사 7년 보관(KR §21/EU AI Act §12)을 학습."
        ),
        modules=("engine.safety.gdpr.data_governance",
                 "engine.safety.incident.backup_manifest"),
        practice_command=(
            "python -c 'from engine.safety import audit_dataset; "
            "print(audit_dataset([]))'"
        ),
        estimated_minutes=90,
        references=("§7.3.3", "§7.3.8", "GDPR Art.7"),
    ),
    ChecklistItem(
        item_id="m1_consent",
        phase=PHASE_MONTH1,
        title="동의 화면과 권리 정보",
        summary=(
            "processing/storage/training/third_party_sharing 4개 동의 항목, "
            "필수 vs 선택, 4언어 텍스트를 학습."
        ),
        modules=("engine.safety.gdpr.consent_screen",
                 "engine.safety.gdpr.rights_information"),
        practice_command=(
            "python -c 'from engine.safety import get_consent_screen; "
            "print(get_consent_screen(\"ko\")[\"items\"])'"
        ),
        estimated_minutes=60,
        references=("§14.1", "§14.2"),
    ),

    # ── Ongoing ──
    ChecklistItem(
        item_id="ong_compliance",
        phase=PHASE_ONGOING,
        title="분기별 운영표준 점검",
        summary=(
            "compliance_report로 41개 항목 자체 점검. coverage 100% 미만이면 "
            "alert_router를 통해 P2 알람 발송."
        ),
        modules=("engine.safety.audit.compliance_report",
                 "engine.safety.audit.standard_doc_builder"),
        practice_command=(
            "python -c 'from engine.safety import generate_compliance_report; "
            "r = generate_compliance_report(); print(r.coverage_percent)'"
        ),
        estimated_minutes=30,
        references=("§14.4", "§14.5"),
    ),
    ChecklistItem(
        item_id="ong_shadow",
        phase=PHASE_ONGOING,
        title="새 시스템 프롬프트의 셰도우 평가",
        summary=(
            "새 프롬프트나 LLM 백엔드 교체는 control vs candidate 페어 평가를 "
            "거쳐 promote_recommended=True일 때만 카나리 진입."
        ),
        modules=("engine.safety.audit.shadow_eval",),
        practice_command="pytest engine/safety/test_shadow_eval.py -q",
        estimated_minutes=45,
        references=("§7.3.9",),
    ),
    ChecklistItem(
        item_id="ong_regression",
        phase=PHASE_ONGOING,
        title="회귀 테스트 분기별 풀 실행",
        summary=(
            "engine/ 전체 회귀(972건)를 분기별로 실행. "
            "golden set 21건 + persona judge + 통합 envelope 모두 통과 확인."
        ),
        # ADR-051: 옛 test 파일 (engine.divination.test_*) 5회차 git rm 후 자머.
        # 현 회귀 테스트는 tests/regression/ + tests/smoke/ + tests/e2e/ (ADR-046·047)
        modules=("engine.divination.face.reading",
                 "engine.divination.name.reading",
                 "engine.divination.palm.reading"),
        practice_command="pytest engine/ -q",
        estimated_minutes=30,
        references=("§5.1", "§5.2",),
    ),
)


# ─────────────────────────── Public API ───────────────────────────

def get_all_items() -> tuple[ChecklistItem, ...]:
    return _CHECKLIST


def get_items_by_phase(phase: str) -> list[ChecklistItem]:
    return [it for it in _CHECKLIST if it.phase == phase]


def get_item(item_id: str) -> ChecklistItem | None:
    for it in _CHECKLIST:
        if it.item_id == item_id:
            return it
    return None


def total_estimated_minutes(*, phase: str | None = None) -> int:
    """선택 단계 또는 전체의 총 예상 학습 시간(분)."""
    items = get_items_by_phase(phase) if phase else list(_CHECKLIST)
    return sum(it.estimated_minutes for it in items)


def evaluate_progress(
    statuses: dict[str, str],
) -> dict[str, Any]:
    """외부에서 받은 항목별 상태를 집계해 진행률 산출.

    Args:
        statuses: {item_id: STATUS_*}.

    Returns:
        {
            "total": N,
            "completed": int,
            "in_progress": int,
            "not_started": int,
            "completed_percent": float,
            "next_phase": str,         # 다음에 학습할 phase (가장 뒤처진)
        }
    """
    total = len(_CHECKLIST)
    completed = 0
    in_progress = 0
    not_started = 0
    phase_done: dict[str, int] = {}
    phase_total: dict[str, int] = {}

    for it in _CHECKLIST:
        status = statuses.get(it.item_id, STATUS_NOT_STARTED)
        if status == STATUS_COMPLETED:
            completed += 1
            phase_done[it.phase] = phase_done.get(it.phase, 0) + 1
        elif status == STATUS_IN_PROGRESS:
            in_progress += 1
        else:
            not_started += 1
        phase_total[it.phase] = phase_total.get(it.phase, 0) + 1

    # 다음 학습할 phase — 완료율이 가장 낮은 단계 (Day1→Week1→Month1→Ongoing 순)
    phase_order = (PHASE_DAY1, PHASE_WEEK1, PHASE_MONTH1, PHASE_ONGOING)
    next_phase = PHASE_ONGOING  # 기본값
    for p in phase_order:
        done = phase_done.get(p, 0)
        tot = phase_total.get(p, 0)
        if tot > 0 and done < tot:
            next_phase = p
            break

    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "not_started": not_started,
        "completed_percent": round((completed / total) * 100, 2) if total else 0.0,
        "next_phase": next_phase,
    }


def format_progress_text(progress: dict[str, Any]) -> str:
    """CLI 표시용 한 줄 요약."""
    return (
        f"[Onboarding] {progress['completed']}/{progress['total']} "
        f"({progress['completed_percent']}%) — next: {progress['next_phase']}"
    )
