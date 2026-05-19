"""운영표준 자체 점검 보고서 — §14.4 본문화.

운영표준 §1~§14의 각 항목이 실제로 모듈로 구현되어 있는지 일괄 점검하고
구조화된 보고서를 생성한다. 규제 감사·정기 점검·신규 입사자 온보딩에 사용.

§14.4 보고서 구조:
  · sections: 각 운영표준 항목 (예: "5.2.4", "7.2.9", "14.1")
    · implemented: bool — 모듈/함수 존재 여부
    · module: 구현 모듈 경로
    · evidence: 발견된 심볼 목록 (Class/함수)
    · regulatory_anchors: 규제 매핑 (GDPR/EU AI Act/KR PIPA 등)
  · summary:
    · total_items, implemented_count, missing
    · coverage_percent

본 모듈은 정적 점검만 — 모듈 import 성공 + 핵심 심볼 hasattr 검사.
실제 동작 검증은 quick_check.py에 위임.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Any


# §14.4 — 운영표준 항목 → 모듈 매핑 매니페스트.
# 각 항목은 (module_path, required_symbols, regulatory_anchors) 튜플.
COMPLIANCE_MANIFEST: dict[str, dict[str, Any]] = {
    # ── §5 LLM 안전 ──
    "5.2.4_jailbreak_defense": {
        "module": "engine.safety.jailbreak_defense",
        "symbols": ("detect_jailbreak", "build_jailbreak_response"),
        "anchors": ("OWASP LLM01", "NIST AI RMF Map-1"),
    },
    "5.2.5_persona_self_eval": {
        "module": "engine.safety.persona_self_eval",
        "symbols": ("evaluate_persona_tone", "PersonaEvalResult"),
        "anchors": ("internal_quality_gate",),
    },
    "5.2.6_output_token_guard": {
        "module": "engine.safety.output_token_guard",
        "symbols": ("evaluate_output", "TokenGuardResult"),
        "anchors": ("OWASP LLM04",),
    },
    "5.2.7_crisis_multilingual": {
        "module": "engine.safety.crisis_detector",
        "symbols": ("detect_crisis", "DIRECT_SUICIDE_KEYWORDS_ZH"),
        "anchors": ("KR PIPA §22-2", "Character.AI 2024 precedent"),
    },
    "5.2.8_response_fact_check": {
        "module": "engine.safety.response_fact_check",
        "symbols": ("check_response", "FACT_AGE", "FACT_GENDER"),
        "anchors": ("OWASP LLM09",),
    },
    # ── §7.1 법정 면책 ──
    "7.1_legal_notice": {
        "module": "engine.safety.legal_notice",
        "symbols": ("build_legal_footer", "MEDICAL_DISCLAIMER_KO"),
        "anchors": ("의료법 §27", "변호사법 §109"),
    },
    # ── §7.2 응답 가드 ──
    "7.2.1_photo_quality": {
        "module": "engine.divination.face.reading",
        "symbols": ("classify_metric_issue", "ERR_FACE_NOT_DETECTED"),
        "anchors": ("internal_quality_gate",),
    },
    "7.2.3_language_detection": {
        "module": "engine.safety.language",
        "symbols": ("detect_language", "get_language_advisory"),
        "anchors": ("internal_i18n",),
    },
    "7.2.5_pii": {
        "module": "engine.safety.pii",
        "symbols": ("mask_pii", "hash_uid"),
        "anchors": ("KR PIPA §29", "GDPR Art.32"),
    },
    "7.2.6_a11y": {
        "module": "engine.divination.face.reading",
        "symbols": ("_extract_a11y_metadata",),
        "anchors": ("WCAG 2.1 AA", "KR §16-3"),
    },
    "7.2.9_photo_guide": {
        "module": "engine.safety.photo_guide",
        "symbols": ("build_photo_guidance", "get_photo_checklist"),
        "anchors": ("internal_quality_gate",),
    },
    "7.2.10_model_card": {
        "module": "engine.safety.model_card",
        "symbols": ("get_face_reading_model_card", "validate_model_card"),
        "anchors": ("EU AI Act Annex IV", "NIST AI RMF Govern-1.1"),
    },
    "7.2.11_llm_fallback": {
        "module": "engine.safety.llm_fallback_router",
        "symbols": ("plan_llm_calls", "deterministic_stub_response"),
        "anchors": ("internal_resilience",),
    },
    "7.2.12_cache_janitor": {
        "module": "engine.safety.cache_janitor",
        "symbols": ("run_janitor", "find_expired_files"),
        "anchors": ("KR PIPA §21",),
    },
    "7.2.13_response_envelope": {
        "module": "engine.safety.response_envelope",
        "symbols": ("validate_envelope", "detect_branch"),
        "anchors": ("internal_api_contract",),
    },
    "7.2.14_idempotency": {
        "module": "engine.safety.idempotency_key",
        "symbols": ("IdempotencyManager", "compute_idempotency_key"),
        "anchors": ("internal_resilience",),
    },
    "7.2.15_input_sanitizer": {
        "module": "engine.safety.input_sanitizer",
        "symbols": ("sanitize_question", "has_injection_attempt"),
        "anchors": ("OWASP LLM01",),
    },
    "7.2.16_cache_integrity": {
        "module": "engine.safety.cache_integrity",
        "symbols": ("verify_cache_file", "audit_cache_directory"),
        "anchors": ("internal_data_quality",),
    },
    "7.2.17_cost_guard": {
        "module": "engine.safety.cost_guard",
        "symbols": ("CostTracker", "CostBudget"),
        "anchors": ("internal_cost_control",),
    },
    "7.2.18_response_pii_leak": {
        "module": "engine.safety.response_pii_leak",
        "symbols": ("scan_response_pii", "has_pii_leak"),
        "anchors": ("OWASP LLM06", "GDPR Art.32"),
    },
    "7.2.19_rate_limiter": {
        "module": "engine.safety.rate_limiter",
        "symbols": ("RateLimiter", "RateLimitConfig"),
        "anchors": ("OWASP LLM04",),
    },
    "7.2.20_response_alignment": {
        "module": "engine.safety.response_alignment",
        "symbols": ("evaluate_alignment", "detect_topic"),
        "anchors": ("internal_quality_gate",),
    },
    "7.2.21_output_safety_gate": {
        "module": "engine.safety.output_safety_gate",
        "symbols": ("run_safety_gates", "SafetyGateResult"),
        "anchors": ("internal_quality_gate",),
    },
    "7.2.22_request_pipeline": {
        "module": "engine.safety.request_pipeline",
        "symbols": ("preflight", "PipelineDecision"),
        "anchors": ("internal_quality_gate",),
    },
    "7.2.23_cache_key_resolver": {
        "module": "engine.safety.cache_key_resolver",
        "symbols": ("resolve_cache_key", "invalidates_on_prompt_change"),
        "anchors": ("internal_data_quality",),
    },
    # ── §7.3 운영 ──
    "7.3.2_slo": {
        "module": "engine.safety.slo",
        "symbols": ("compute_slo", "SLO_THRESHOLDS"),
        "anchors": ("Google SRE SLO",),
    },
    "7.3.2.1_rollback_trigger": {
        "module": "engine.safety.rollback_trigger",
        "symbols": ("decide_rollback", "classify_rollback_policy"),
        "anchors": ("internal_resilience",),
    },
    "7.3.3_data_governance": {
        "module": "engine.safety.data_governance",
        "symbols": ("audit_dataset", "DataProvenance"),
        "anchors": ("GDPR Art.7", "EU AI Act §10(5)", "KR PIPA §15"),
    },
    "7.3.4_tracing": {
        "module": "engine.safety.tracing",
        "symbols": ("emit_face_reading_event", "FaceReadingTrace"),
        "anchors": ("internal_observability",),
    },
    "7.3.5_quick_check": {
        "module": "engine.safety.quick_check",
        "symbols": ("run_quick_check", "format_quick_check_text"),
        "anchors": ("internal_observability",),
    },
    "7.3.6_canary_guard": {
        "module": "engine.safety.canary_guard",
        "symbols": ("decide_canary", "CanaryMetrics"),
        "anchors": ("Google SRE canary",),
    },
    "7.3.8_backup_manifest": {
        "module": "engine.safety.backup_manifest",
        "symbols": ("get_face_reading_manifest", "overdue_backups"),
        "anchors": ("KR PIPA §21", "EU AI Act §12"),
    },
    "7.3.9_shadow_eval": {
        "module": "engine.safety.shadow_eval",
        "symbols": ("compare_pair", "aggregate_shadow_results"),
        "anchors": ("Google SRE shadow",),
    },
    # ── §10 DSR ──
    "10_dsr_processor": {
        "module": "engine.safety.dsr_processor",
        "symbols": ("process_dsr", "DSRRequest"),
        "anchors": ("GDPR Art.15-22", "KR PIPA §35-37", "CCPA §1798"),
    },
    # ── §14 동의/권리/알람 ──
    "14.1_consent_screen": {
        "module": "engine.safety.consent_screen",
        "symbols": ("get_consent_screen", "validate_consent_payload"),
        "anchors": ("GDPR Art.7", "KR PIPA §22"),
    },
    "14.2_rights_information": {
        "module": "engine.safety.rights_information",
        "symbols": ("get_rights_information", "list_automatable_rights"),
        "anchors": ("GDPR Art.15-22", "KR PIPA §35-37"),
    },
    "14.3_alert_router": {
        "module": "engine.safety.alert_router",
        "symbols": ("route_alert", "AlertEvent"),
        "anchors": ("internal_incident_response",),
    },
    # ── 별도 규제 ──
    "EU_AI_Act_Art50_3": {
        "module": "engine.safety.emotion_disclosure",
        "symbols": ("is_emotion_disclosure_required", "build_emotion_disclosure"),
        "anchors": ("EU AI Act Art.50(3)", "EU AI Act §5(f)"),
    },
    "crisis_resources_multimarket": {
        "module": "engine.safety.crisis_resources",
        "symbols": ("get_crisis_resources", "format_hotlines_text"),
        "anchors": ("KR §1393", "US §988", "EU §116-111"),
    },
    "regulation_profile": {
        "module": "engine.safety.regulation",
        "symbols": ("get_regulation_profile", "is_biometric_inference_restricted"),
        "anchors": ("EU AI Act §5", "KR PIPA", "US-CA CCPA", "US-IL BIPA"),
    },
    "feedback_anonymous": {
        "module": "engine.safety.feedback",
        "symbols": ("record_feedback", "get_aggregate_stats"),
        "anchors": ("internal_quality_gate",),
    },
}


@dataclass(frozen=True)
class ItemReport:
    item_id: str
    implemented: bool
    module: str
    evidence: list[str] = field(default_factory=list)
    missing_symbols: list[str] = field(default_factory=list)
    regulatory_anchors: list[str] = field(default_factory=list)
    error: str = ""


@dataclass(frozen=True)
class ComplianceReport:
    items: list[ItemReport]
    total_items: int
    implemented_count: int
    missing_items: list[str]
    coverage_percent: float
    anchors_covered: list[str]


# ─────────────────────────── 점검 ───────────────────────────

def check_item(item_id: str, *, manifest: dict[str, Any] | None = None) -> ItemReport:
    """단일 항목 점검 — 모듈 import + 심볼 hasattr."""
    manifest = manifest or COMPLIANCE_MANIFEST
    spec = manifest.get(item_id)
    if spec is None:
        return ItemReport(
            item_id=item_id, implemented=False, module="",
            error=f"unknown_item:{item_id}",
        )
    module_path = spec["module"]
    symbols = list(spec.get("symbols", ()))
    anchors = list(spec.get("anchors", ()))

    try:
        mod = importlib.import_module(module_path)
    except Exception as e:  # noqa: BLE001
        return ItemReport(
            item_id=item_id, implemented=False, module=module_path,
            missing_symbols=symbols,
            regulatory_anchors=anchors,
            error=f"import_failed:{type(e).__name__}",
        )

    evidence: list[str] = []
    missing: list[str] = []
    for s in symbols:
        if hasattr(mod, s):
            evidence.append(s)
        else:
            missing.append(s)

    return ItemReport(
        item_id=item_id,
        implemented=not missing,
        module=module_path,
        evidence=evidence,
        missing_symbols=missing,
        regulatory_anchors=anchors,
    )


def generate_report(*, manifest: dict[str, Any] | None = None) -> ComplianceReport:
    """전체 매니페스트 점검 → ComplianceReport."""
    manifest = manifest or COMPLIANCE_MANIFEST
    items = [check_item(k, manifest=manifest) for k in sorted(manifest.keys())]
    implemented = [it for it in items if it.implemented]
    missing = [it.item_id for it in items if not it.implemented]
    total = len(items)
    pct = (len(implemented) / total) if total > 0 else 0.0

    anchors: set[str] = set()
    for it in items:
        if it.implemented:
            anchors.update(it.regulatory_anchors)

    return ComplianceReport(
        items=items,
        total_items=total,
        implemented_count=len(implemented),
        missing_items=missing,
        coverage_percent=round(pct * 100, 2),
        anchors_covered=sorted(anchors),
    )


def format_report_text(report: ComplianceReport) -> str:
    """CLI 표시용 사람-읽기 가능 텍스트."""
    lines: list[str] = []
    lines.append(f"[Compliance Report] coverage={report.coverage_percent}% "
                 f"({report.implemented_count}/{report.total_items})")
    if report.missing_items:
        lines.append(f"  MISSING ({len(report.missing_items)}): "
                     f"{', '.join(report.missing_items[:10])}")
    else:
        lines.append("  All items implemented.")
    lines.append(f"  Regulatory anchors covered ({len(report.anchors_covered)}):")
    for a in report.anchors_covered[:20]:
        lines.append(f"    - {a}")
    return "\n".join(lines)
