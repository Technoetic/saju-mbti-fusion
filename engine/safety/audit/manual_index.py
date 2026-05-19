"""운영 매뉴얼 인덱스 — 운영표준 §14.10 본문화.

안전 모듈 45개를 카테고리/사용 시점/심각도/관련 모듈로 검색 가능한 인덱스.
운영자가 "지금 이 상황에 쓸 모듈" 즉시 찾기 위함.

§14.10 4종 인덱싱:
  · BY_CATEGORY  — input_guard / output_guard / runtime / governance / docs
  · BY_TIMING    — preflight / runtime / postflight / periodic
  · BY_SEVERITY  — P0_response / P1_response / P2_response / general
  · BY_REGULATION — GDPR / EU_AI_ACT / KR_PIPA / OWASP_LLM / SRE

각 모듈에 use_when (1줄), key_apis, related_modules를 명시. 자연어 검색은
하지 않고 정확 분류만 — 운영자가 매뉴얼 형태로 빠르게 훑을 수 있게.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# §14.10 카테고리 분류
CATEGORY_INPUT_GUARD = "input_guard"          # 입력 검증·정제
CATEGORY_OUTPUT_GUARD = "output_guard"        # 응답 검증
CATEGORY_RUNTIME = "runtime"                  # 실시간 운영 (limit/cost/cache)
CATEGORY_GOVERNANCE = "governance"            # 규제·동의·권리
CATEGORY_OBSERVABILITY = "observability"      # SLO/trace/quick_check
CATEGORY_INCIDENT = "incident"                # 사고 대응·플레이북
CATEGORY_DOCS = "docs"                        # 보고서·문서 생성

# §14.10 사용 시점
TIMING_PREFLIGHT = "preflight"                # LLM 호출 전
TIMING_RUNTIME = "runtime"                    # LLM 호출 중
TIMING_POSTFLIGHT = "postflight"              # LLM 호출 후
TIMING_PERIODIC = "periodic"                  # 분기/정기


@dataclass(frozen=True)
class ManualEntry:
    module: str                               # engine.safety.xxx
    standard_ref: str                         # §7.2.18 등
    title: str
    category: str
    timing: tuple[str, ...]
    use_when: str                             # 1줄 사용 시점
    key_apis: tuple[str, ...]                 # 주요 진입 함수
    severity_relevance: tuple[str, ...] = field(default_factory=tuple)
    regulations: tuple[str, ...] = field(default_factory=tuple)
    related: tuple[str, ...] = field(default_factory=tuple)


# §14.10 매니페스트 — 45개 모듈
_MANUAL: tuple[ManualEntry, ...] = (
    # ── input guard ──
    ManualEntry(
        module="engine.safety.input_guards.input_sanitizer", standard_ref="§7.2.15",
        title="입력 정제기",
        category=CATEGORY_INPUT_GUARD, timing=(TIMING_PREFLIGHT,),
        use_when="LLM 호출 전 화두 본문의 제어 문자·injection 마커 제거",
        key_apis=("sanitize_question", "has_injection_attempt"),
        regulations=("OWASP_LLM01",),
        related=("jailbreak_defense",),
    ),
    ManualEntry(
        module="engine.safety.llm.jailbreak_defense", standard_ref="§5.2.4",
        title="적대적 프롬프트 방어",
        category=CATEGORY_INPUT_GUARD, timing=(TIMING_PREFLIGHT,),
        use_when="화두 본문에서 페르소나 우회·금지 자문 유도 탐지",
        key_apis=("detect_jailbreak", "build_jailbreak_response"),
        regulations=("OWASP_LLM01",),
        related=("input_sanitizer", "request_pipeline"),
    ),
    ManualEntry(
        module="engine.safety.crisis.detector", standard_ref="§5.2.7",
        title="위기 신호 결정론 차단",
        category=CATEGORY_INPUT_GUARD, timing=(TIMING_PREFLIGHT,),
        use_when="자살·자해·자살계획 표현 4언어 탐지",
        key_apis=("detect_crisis",),
        severity_relevance=("P0",),
        regulations=("KR_PIPA",),
        related=("crisis_resources",),
    ),
    ManualEntry(
        module="engine.safety.gdpr.pii", standard_ref="§7.2.5",
        title="입력 PII 마스킹",
        category=CATEGORY_INPUT_GUARD, timing=(TIMING_PREFLIGHT,),
        use_when="화두에 포함된 PII를 LLM 전송 전 마스킹",
        key_apis=("mask_pii", "hash_uid"),
        regulations=("GDPR", "KR_PIPA"),
        related=("response_pii_leak",),
    ),
    ManualEntry(
        module="engine.safety.misc.request_pipeline", standard_ref="§7.2.22",
        title="통합 사전 점검 파이프라인",
        category=CATEGORY_INPUT_GUARD, timing=(TIMING_PREFLIGHT,),
        use_when="rate/cost/sanitize/jailbreak/idempotency 5단계 통합 점검",
        key_apis=("preflight",),
        related=("rate_limiter", "cost_guard", "jailbreak_defense"),
    ),

    # ── output guard ──
    ManualEntry(
        module="engine.safety.llm.persona_self_eval", standard_ref="§5.2.5",
        title="페르소나 톤 자체 평가",
        category=CATEGORY_OUTPUT_GUARD, timing=(TIMING_POSTFLIGHT,),
        use_when="LLM 응답이 사극풍·금지어 회귀하지 않는지 평가",
        key_apis=("evaluate_persona_tone",),
        related=("response_alignment", "response_consistency"),
    ),
    ManualEntry(
        module="engine.safety.llm.output_token_guard", standard_ref="§5.2.6",
        title="출력 토큰 가드",
        category=CATEGORY_OUTPUT_GUARD, timing=(TIMING_POSTFLIGHT,),
        use_when="너무 짧음·절단·언어 drift·반복 검출",
        key_apis=("evaluate_output", "to_fallback_trigger"),
        related=("llm_fallback_router",),
    ),
    ManualEntry(
        module="engine.safety.llm.response_fact_check", standard_ref="§5.2.8",
        title="응답 사실 검증",
        category=CATEGORY_OUTPUT_GUARD, timing=(TIMING_POSTFLIGHT,),
        use_when="응답이 입력 age/gender/metrics와 모순되는지",
        key_apis=("check_response",),
        related=("face_reading",),
    ),
    ManualEntry(
        module="engine.safety.llm.response_pii_leak", standard_ref="§7.2.18",
        title="응답 PII 누출 검출",
        category=CATEGORY_OUTPUT_GUARD, timing=(TIMING_POSTFLIGHT,),
        use_when="LLM 응답에 전화·이메일·SSN·API 키 포함되는지 검출",
        key_apis=("scan_response_pii", "has_pii_leak"),
        severity_relevance=("P0",),
        regulations=("GDPR", "KR_PIPA"),
    ),
    ManualEntry(
        module="engine.safety.llm.response_alignment", standard_ref="§7.2.20",
        title="응답 주제 정렬 검증",
        category=CATEGORY_OUTPUT_GUARD, timing=(TIMING_POSTFLIGHT,),
        use_when="응답이 화두 주제(결혼/재물/건강 등)와 정렬되는지",
        key_apis=("evaluate_alignment", "detect_topic"),
    ),
    ManualEntry(
        module="engine.safety.llm.response_consistency", standard_ref="§5.2.9",
        title="N개 응답 일관성 검증",
        category=CATEGORY_OUTPUT_GUARD, timing=(TIMING_POSTFLIGHT,),
        use_when="같은 입력의 N개 응답이 페르소나·주제·길이에서 일관되는지",
        key_apis=("evaluate_consistency",),
    ),
    ManualEntry(
        module="engine.safety.llm.output_safety_gate", standard_ref="§7.2.21",
        title="통합 출력 안전망",
        category=CATEGORY_OUTPUT_GUARD, timing=(TIMING_POSTFLIGHT,),
        use_when="5개 후처리 검증을 한 호출로",
        key_apis=("run_safety_gates",),
        related=("persona_self_eval", "response_pii_leak",
                 "response_fact_check", "response_alignment"),
    ),
    ManualEntry(
        module="engine.safety.llm.response_envelope", standard_ref="§7.2.13",
        title="응답 envelope 표준 검증",
        category=CATEGORY_OUTPUT_GUARD, timing=(TIMING_POSTFLIGHT,),
        use_when="응답 6개 분기가 공통 필수 키를 유지하는지",
        key_apis=("validate_envelope", "detect_branch"),
    ),
    ManualEntry(
        module="engine.safety.gdpr.legal_notice", standard_ref="§7.1",
        title="법정 면책 자동 첨부",
        category=CATEGORY_OUTPUT_GUARD, timing=(TIMING_POSTFLIGHT,),
        use_when="모든 응답에 의료·법률·금융 자문 아님 명시",
        key_apis=("build_legal_footer",),
        regulations=("의료법§27", "변호사법§109"),
    ),
    ManualEntry(
        module="engine.safety.crisis.emotion_disclosure", standard_ref="EU AI Act §50(3)",
        title="EU 감정 추론 명시 고지",
        category=CATEGORY_OUTPUT_GUARD, timing=(TIMING_POSTFLIGHT,),
        use_when="EU/UK 지역 응답에 감정 추론 포함 명시 고지 자동 첨부",
        key_apis=("inject_emotion_disclosure", "get_disclosure_metadata"),
        regulations=("EU_AI_ACT",),
    ),

    # ── runtime ──
    ManualEntry(
        module="engine.safety.input_guards.rate_limiter", standard_ref="§7.2.19",
        title="Rate limiter (분/시/일)",
        category=CATEGORY_RUNTIME, timing=(TIMING_PREFLIGHT,),
        use_when="uid별 분당/시간당/일당 호출 횟수 제한",
        key_apis=("RateLimiter.acquire",),
        regulations=("OWASP_LLM04",),
    ),
    ManualEntry(
        module="engine.safety.input_guards.cost_guard", standard_ref="§7.2.17",
        title="LLM 비용 한도 가드",
        category=CATEGORY_RUNTIME, timing=(TIMING_PREFLIGHT, TIMING_PERIODIC),
        use_when="일/월 LLM 비용 한도 + warn/critical/exhausted 분류",
        key_apis=("CostTracker.status", "CostTracker.record"),
    ),
    ManualEntry(
        module="engine.safety.input_guards.idempotency_key", standard_ref="§7.2.14",
        title="멱등 키 관리자",
        category=CATEGORY_RUNTIME, timing=(TIMING_PREFLIGHT,),
        use_when="동시 in-flight 같은 입력 중복 호출 방지",
        key_apis=("IdempotencyManager.claim", "compute_idempotency_key"),
    ),
    ManualEntry(
        module="engine.safety.input_guards.cache_key_resolver", standard_ref="§7.2.23",
        title="캐시 키 결정기",
        category=CATEGORY_RUNTIME, timing=(TIMING_RUNTIME,),
        use_when="결정론 캐시 키 생성 + 시스템 프롬프트 변경 무효화",
        key_apis=("resolve_cache_key", "invalidates_on_prompt_change"),
    ),
    ManualEntry(
        module="engine.safety.input_guards.cache_integrity", standard_ref="§7.2.16",
        title="캐시 무결성 검증",
        category=CATEGORY_RUNTIME, timing=(TIMING_PERIODIC,),
        use_when="디스크 캐시 손상·외부 변조·프롬프트 해시 mismatch 검출",
        key_apis=("verify_cache_file", "audit_cache_directory"),
    ),
    ManualEntry(
        module="engine.safety.input_guards.cache_janitor", standard_ref="§7.2.12",
        title="캐시 TTL 청소",
        category=CATEGORY_RUNTIME, timing=(TIMING_PERIODIC,),
        use_when="24h TTL 만료 캐시 정기 정리 + 디스크 가득 알람",
        key_apis=("run_janitor", "find_expired_files"),
    ),
    ManualEntry(
        module="engine.safety.incident.llm_fallback_router", standard_ref="§7.2.11",
        title="LLM 폴백 라우터",
        category=CATEGORY_RUNTIME, timing=(TIMING_RUNTIME, TIMING_POSTFLIGHT),
        use_when="Primary 실패 시 Secondary·Stub으로 폴백",
        key_apis=("plan_llm_calls", "classify_failure",
                  "deterministic_stub_response"),
    ),
    ManualEntry(
        module="engine.safety.photo.guide", standard_ref="§7.2.9",
        title="사진 촬영 가이드 (4언어)",
        category=CATEGORY_RUNTIME, timing=(TIMING_POSTFLIGHT,),
        use_when="ERR_FACE_*/WARN_FACE_* 응답에 사용자 가이드 첨부",
        key_apis=("build_photo_guidance", "get_retry_tips"),
    ),

    # ── governance ──
    ManualEntry(
        module="engine.safety.gdpr.consent_screen", standard_ref="§14.1",
        title="동의 화면 (4언어)",
        category=CATEGORY_GOVERNANCE, timing=(TIMING_PREFLIGHT,),
        use_when="사용자 동의 항목 4종 + 필수/선택 텍스트 표시",
        key_apis=("get_consent_screen", "validate_consent_payload"),
        regulations=("GDPR_Art7", "KR_PIPA_§22"),
    ),
    ManualEntry(
        module="engine.safety.gdpr.data_governance", standard_ref="§7.3.3",
        title="데이터 거버넌스 (골든셋·평가셋)",
        category=CATEGORY_GOVERNANCE, timing=(TIMING_PERIODIC,),
        use_when="골든 셋 출처·동의·라이선스·보존기한 일괄 감사",
        key_apis=("audit_dataset", "validate_provenance"),
        regulations=("GDPR_Art7", "EU_AI_ACT_§10", "KR_PIPA_§15"),
    ),
    ManualEntry(
        module="engine.safety.gdpr.rights_information", standard_ref="§14.2",
        title="권리 행사 안내 (7권리·4언어)",
        category=CATEGORY_GOVERNANCE, timing=(TIMING_PREFLIGHT,),
        use_when="GDPR/PIPA/CCPA 권리와 지역별 SLA 안내",
        key_apis=("get_rights_information", "get_sla_for_region"),
        regulations=("GDPR_Art15-22", "KR_PIPA_§35-37", "CCPA"),
    ),
    ManualEntry(
        module="engine.safety.gdpr.dsr_processor", standard_ref="§10",
        title="DSR 처리 (4단계)",
        category=CATEGORY_GOVERNANCE, timing=(TIMING_RUNTIME,),
        use_when="권리 행사 요청 ingest→plan→execute→audit",
        key_apis=("process_dsr", "DSRRequest"),
        regulations=("GDPR_Art15-22", "KR_PIPA_§35-37"),
    ),
    ManualEntry(
        module="engine.safety.gdpr.regulation", standard_ref="§14",
        title="지역별 규제 프로파일",
        category=CATEGORY_GOVERNANCE, timing=(TIMING_PREFLIGHT,),
        use_when="지역(KR/EU/UK/US-CA/US-IL/JP/CN)별 규제 매핑",
        key_apis=("get_regulation_profile", "is_biometric_inference_restricted"),
        regulations=("EU_AI_ACT", "KR_PIPA", "CCPA", "BIPA"),
    ),
    ManualEntry(
        module="engine.safety.incident.backup_manifest", standard_ref="§7.3.8",
        title="백업·복구 매니페스트",
        category=CATEGORY_GOVERNANCE, timing=(TIMING_PERIODIC,),
        use_when="5종 자원의 RPO/RTO 매트릭스 + overdue 감지",
        key_apis=("get_face_reading_manifest", "overdue_backups"),
        regulations=("KR_PIPA_§21", "EU_AI_ACT_§12"),
    ),

    # ── observability ──
    ManualEntry(
        module="engine.safety.slo.slo.tracing", standard_ref="§7.3.4",
        title="요청 트레이싱 (JSON line)",
        category=CATEGORY_OBSERVABILITY, timing=(TIMING_RUNTIME,),
        use_when="모든 face_reading 호출에 트레이스 이벤트 emit",
        key_apis=("emit_face_reading_event", "FaceReadingTrace"),
    ),
    ManualEntry(
        module="engine.safety.slo.slo", standard_ref="§7.3.2",
        title="SLO·KPI 측정",
        category=CATEGORY_OBSERVABILITY, timing=(TIMING_PERIODIC,),
        use_when="윈도우 P50/P95/P99 + crisis/err/cache_hit rate 산출",
        key_apis=("compute_slo", "parse_log_line"),
    ),
    ManualEntry(
        module="engine.safety.slo.slo.latency_audit", standard_ref="§7.2.24",
        title="단계별 latency 감사",
        category=CATEGORY_OBSERVABILITY, timing=(TIMING_RUNTIME,),
        use_when="6개 단계별 latency 측정 + 임계 위반 감지",
        key_apis=("new_latency_sample", "measure_latency", "evaluate_latency"),
    ),
    ManualEntry(
        module="engine.safety.misc.quick_check", standard_ref="§7.3.5",
        title="빠른 점검 진입점",
        category=CATEGORY_OBSERVABILITY, timing=(TIMING_PERIODIC,),
        use_when="SSH 한 줄로 시스템 6개 섹션 헬스 확인",
        key_apis=("run_quick_check", "format_quick_check_text"),
    ),
    ManualEntry(
        module="engine.safety.input_guards.canary_guard", standard_ref="§7.3.6",
        title="카나리 배포 가드",
        category=CATEGORY_OBSERVABILITY, timing=(TIMING_PERIODIC,),
        use_when="1%→5%→25%→100% 단계 PROMOTE/HOLD/ROLLBACK 결정",
        key_apis=("decide_canary", "metrics_from_slo_report"),
    ),
    ManualEntry(
        module="engine.safety.audit.shadow_eval", standard_ref="§7.3.9",
        title="셰도우 페어 평가",
        category=CATEGORY_OBSERVABILITY, timing=(TIMING_PERIODIC,),
        use_when="새 프롬프트 control vs candidate 비교",
        key_apis=("compare_pair", "aggregate_shadow_results"),
    ),
    ManualEntry(
        module="engine.safety.misc.feedback", standard_ref="§7.2.7",
        title="익명 피드백 카운트",
        category=CATEGORY_OBSERVABILITY, timing=(TIMING_POSTFLIGHT,),
        use_when="익명 thumbs up/down 카운트 누적",
        key_apis=("record_feedback", "get_aggregate_stats"),
    ),
    ManualEntry(
        module="engine.safety.misc.language", standard_ref="§7.2.3",
        title="언어 감지 + 외국어 안내",
        category=CATEGORY_OBSERVABILITY, timing=(TIMING_PREFLIGHT,),
        use_when="화두 언어 자동 감지 + 한국어 외 안내",
        key_apis=("detect_language", "get_language_advisory"),
    ),

    # ── incident ──
    ManualEntry(
        module="engine.safety.crisis.alert_router", standard_ref="§14.3",
        title="알람 채널 라우터 (P0~P3)",
        category=CATEGORY_INCIDENT, timing=(TIMING_RUNTIME,),
        use_when="이벤트→심각도→Slack/PagerDuty 채널 라우팅",
        key_apis=("route_alert", "AlertEvent", "Debouncer"),
        severity_relevance=("P0", "P1", "P2", "P3"),
    ),
    ManualEntry(
        module="engine.safety.incident.rollback_trigger", standard_ref="§7.3.2.1",
        title="자동 롤백 정책",
        category=CATEGORY_INCIDENT, timing=(TIMING_RUNTIME,),
        use_when="이벤트→AUTO/APPROVAL/NEVER 결정 + git revert 명령",
        key_apis=("decide_rollback", "classify_rollback_policy"),
        severity_relevance=("P0", "P1"),
    ),
    ManualEntry(
        module="engine.safety.crisis.resources", standard_ref="§7.2.12",
        title="다국가 위기 핫라인",
        category=CATEGORY_INCIDENT, timing=(TIMING_RUNTIME,),
        use_when="위기 감지 시 지역별 핫라인 텍스트 자동 부착",
        key_apis=("get_crisis_resources", "format_hotlines_text"),
        severity_relevance=("P0",),
    ),
    ManualEntry(
        module="engine.safety.incident.playbook", standard_ref="§14.7",
        title="사고 대응 플레이북",
        category=CATEGORY_INCIDENT, timing=(TIMING_RUNTIME,),
        use_when="P0~P2 사고 단계별 대응 절차 (8개 playbook)",
        key_apis=("get_playbook", "list_p0_playbooks", "format_playbook_text"),
        severity_relevance=("P0", "P1", "P2"),
    ),
    ManualEntry(
        module="engine.safety.audit.postmortem_builder", standard_ref="§14.8",
        title="사후 검토 빌더",
        category=CATEGORY_INCIDENT, timing=(TIMING_PERIODIC,),
        use_when="P0 사고 후 5 Whys + 통지 의무 + remediation 템플릿",
        key_apis=("build_postmortem_draft", "evaluate_notification_required"),
        regulations=("GDPR_Art33_34", "KR_PIPA_§34"),
    ),

    # ── docs ──
    ManualEntry(
        module="engine.safety.audit.compliance_report", standard_ref="§14.4",
        title="운영표준 자체 점검",
        category=CATEGORY_DOCS, timing=(TIMING_PERIODIC,),
        use_when="41개 항목 일괄 정적 점검 + coverage 산출",
        key_apis=("generate_compliance_report", "check_compliance_item"),
    ),
    ManualEntry(
        module="engine.safety.audit.model_card", standard_ref="§7.2.10",
        title="Model Card + Data Card",
        category=CATEGORY_DOCS, timing=(TIMING_PERIODIC,),
        use_when="Mitchell 2019 + Gebru 2021 양식 자동 생성",
        key_apis=("get_face_reading_model_card", "get_face_reading_data_card"),
        regulations=("EU_AI_ACT_AnnexIV", "NIST_AI_RMF"),
    ),
    ManualEntry(
        module="engine.safety.audit.standard_doc_builder", standard_ref="§14.5",
        title="운영표준 문서 빌더",
        category=CATEGORY_DOCS, timing=(TIMING_PERIODIC,),
        use_when="감사용 마크다운/JSON/한국어 letter 자동 생성",
        key_apis=("build_markdown_report", "build_audit_letter"),
    ),
    ManualEntry(
        module="engine.safety.audit.onboarding_checklist", standard_ref="§14.6",
        title="신규 입사자 온보딩",
        category=CATEGORY_DOCS, timing=(TIMING_PERIODIC,),
        use_when="4단계(Day1/Week1/Month1/Ongoing) 학습 경로",
        key_apis=("get_onboarding_items", "evaluate_onboarding_progress"),
    ),
    ManualEntry(
        module="engine.safety.audit.quarterly_review", standard_ref="§14.9",
        title="분기별 운영 리뷰",
        category=CATEGORY_DOCS, timing=(TIMING_PERIODIC,),
        use_when="경영진용 1페이지 (compliance/SLO/incidents/cost)",
        key_apis=("build_quarterly_review", "evaluate_quarterly_grade"),
    ),
)


# ─────────────────────────── Public API ───────────────────────────

def get_all_entries() -> tuple[ManualEntry, ...]:
    return _MANUAL


def find_by_category(category: str) -> list[ManualEntry]:
    return [e for e in _MANUAL if e.category == category]


def find_by_timing(timing: str) -> list[ManualEntry]:
    return [e for e in _MANUAL if timing in e.timing]


def find_by_severity(severity: str) -> list[ManualEntry]:
    return [e for e in _MANUAL if severity in e.severity_relevance]


def find_by_regulation(regulation_prefix: str) -> list[ManualEntry]:
    """규제 코드 prefix 매칭 (예: 'GDPR' → 'GDPR_Art7', 'GDPR_Art15-22' 모두)."""
    return [e for e in _MANUAL
            if any(r.startswith(regulation_prefix) for r in e.regulations)]


def get_entry_by_module(module: str) -> ManualEntry | None:
    for e in _MANUAL:
        if e.module == module:
            return e
    return None


def format_index_text(entries: list[ManualEntry] | None = None) -> str:
    """카테고리별로 그룹화된 사람-읽기 가능 인덱스."""
    items = entries if entries is not None else list(_MANUAL)
    by_cat: dict[str, list[ManualEntry]] = {}
    for e in items:
        by_cat.setdefault(e.category, []).append(e)
    lines: list[str] = []
    lines.append(f"# 운영 매뉴얼 인덱스 ({len(items)}개 모듈)")
    lines.append("")
    for cat in sorted(by_cat.keys()):
        lines.append(f"## {cat}")
        for e in by_cat[cat]:
            lines.append(f"- `{e.module}` [{e.standard_ref}] — {e.title}")
            lines.append(f"  · 사용 시점: {e.use_when}")
            lines.append(f"  · 주요 API: {', '.join(e.key_apis)}")
        lines.append("")
    return "\n".join(lines)


def to_json_summary() -> dict[str, Any]:
    """외부 인제스트용 JSON."""
    return {
        "total_entries": len(_MANUAL),
        "by_category": {
            cat: len(find_by_category(cat))
            for cat in (CATEGORY_INPUT_GUARD, CATEGORY_OUTPUT_GUARD,
                        CATEGORY_RUNTIME, CATEGORY_GOVERNANCE,
                        CATEGORY_OBSERVABILITY, CATEGORY_INCIDENT,
                        CATEGORY_DOCS)
        },
        "entries": [
            {
                "module": e.module, "standard_ref": e.standard_ref,
                "title": e.title, "category": e.category,
                "timing": list(e.timing), "use_when": e.use_when,
                "key_apis": list(e.key_apis),
                "severity_relevance": list(e.severity_relevance),
                "regulations": list(e.regulations),
                "related": list(e.related),
            }
            for e in _MANUAL
        ],
    }
