"""안전·법적 안전장치 모듈 (ADR-050 자동 노출 통합).

본 패키지는 모든 LLM 응답 전후에 의무적으로 호출되어:
  - 자살/자해/위기 신호 결정론 탐지
  - 법정 면책 고지문 자동 첨부
  - 미성년자 차단
  - 정신건강 데이터 동의 검증
을 수행한다. 우회 금지.

ADR-050: 9 카테고리 모든 public 심볼 자동 노출 (옛 평면 import 호환).
중복 심볼 (to_trace_event·to_alert_payload 등 7개)은 첫 발생 모듈만 노출.
"""

# 9 카테고리 서브패키지
from engine.safety import (
    crisis, gdpr, slo, audit, input_guards,
    incident, llm, photo, misc,
)

# 옛 평면 모듈명 alias (engine.safety.feedback 등)
from engine.safety.crisis import detector as crisis_detector
from engine.safety.crisis import resources as crisis_resources
from engine.safety.crisis import alert_router, emotion_disclosure
from engine.safety.gdpr import (
    dsr_processor, consent_screen, pii, data_governance,
    rights_information, regulation, legal_notice,
)
from engine.safety.slo import (
    slo as slo_module,
    latency_audit, kpi_dashboard, tracing, prompt_cache_telemetry,
)
from engine.safety.audit import (
    changelog_tracker, standard_doc_builder, quarterly_review, model_card,
    manual_index, shadow_eval, dependency_graph, onboarding_checklist,
    postmortem_builder, compliance_report,
)
from engine.safety.input_guards import (
    input_sanitizer, rate_limiter, file_integrity, cache_integrity,
    cache_janitor, cache_key_resolver, idempotency_key, canary_guard, cost_guard,
)
from engine.safety.incident import (
    playbook as incident_playbook,
    rollback_trigger, backup_manifest, llm_fallback_router,
)
from engine.safety.llm import (
    output_sampler as llm_output_sampler,
    output_safety_gate, output_token_guard, persona_self_eval,
    response_alignment, response_consistency, response_envelope,
    response_fact_check, response_pii_leak, jailbreak_defense,
)
from engine.safety.photo import guide as photo_guide, quality as photo_quality
from engine.safety.misc import feedback, language, quick_check, request_pipeline

# 모든 public 심볼 자동 노출 (중복은 첫 발생만)
from engine.safety.crisis.detector import (
    EMERGENCY_HOTLINES_KR,
    DIRECT_SUICIDE_KEYWORDS,
    DIRECT_SELFHARM_KEYWORDS,
    INDIRECT_DESPAIR_KEYWORDS,
    PLANNING_KEYWORDS,
    NEGATION_PATTERNS,
    CRISIS_RESPONSE_KO,
    detect_crisis,
)
from engine.safety.crisis.resources import (
    CrisisHotline,
    get_crisis_resources,
    format_hotlines_text,
    list_supported_crisis_regions,
)
from engine.safety.crisis.alert_router import (
    P0,
    P1,
    P2,
    P3,
    SEVERITY_LABELS,
    CHANNEL_MAP,
    DEBOUNCE_WINDOW_SEC,
    AlertEvent,
    classify_slo_violation,
    classify_event,
    Debouncer,
    build_slack_message,
    build_pagerduty_event,
    route_alert,
    alerts_from_slo_report,
)
from engine.safety.crisis.emotion_disclosure import (
    is_emotion_disclosure_required,
    is_emotion_disclosure_recommended,
    build_emotion_disclosure,
    inject_emotion_disclosure,
    get_disclosure_metadata,
)
from engine.safety.gdpr.dsr_processor import (
    DSR_STATUS_PENDING,
    DSR_STATUS_PLANNED,
    DSR_STATUS_EXECUTED,
    DSR_STATUS_REJECTED,
    DSRRequest,
    DSRPlan,
    ingest_dsr,
    plan_dsr,
    execute_dsr,
    build_audit_record,
    process_dsr,
)
from engine.safety.gdpr.consent_screen import (
    CONSENT_FIELDS,
    ConsentItem,
    get_consent_screen,
    validate_consent_payload,
)
from engine.safety.gdpr.pii import (
    mask_pii,
    hash_uid,
    hash_question,
    mask_crisis_keyword,
)
from engine.safety.gdpr.data_governance import (
    LICIT_SOURCES,
    ILLICIT_SOURCES,
    REQUIRED_CONSENT_FIELDS,
    MAX_RETENTION_DAYS,
    DataProvenance,
    validate_provenance,
    is_eligible_for_regression,
    is_expired,
    days_until_expiry,
    audit_dataset,
)
from engine.safety.gdpr.rights_information import (
    RIGHT_KEYS,
    AUTOMATION_AUTO,
    AUTOMATION_MANUAL,
    AUTOMATION_NA,
    RightInfo,
    get_rights_information,
    get_right_by_key,
    list_automatable_rights,
    get_sla_for_region,
)
from engine.safety.gdpr.regulation import (
    RegulationProfile,
    get_regulation_profile,
    is_biometric_inference_restricted,
    list_supported_regions,
)
from engine.safety.gdpr.legal_notice import (
    MEDICAL_DISCLAIMER_KO,
    FORTUNE_DISCLAIMER_KO,
    DATA_NOTICE_KO,
    LEGAL_NOTICE_FOOTER_KO,
    CRISIS_FOOTER_KO,
    build_legal_footer,
)
from engine.safety.slo.slo import (
    SLO_THRESHOLDS,
    parse_log_line,
    compute_slo,
    compute_slo_from_lines,
)
from engine.safety.slo.latency_audit import (
    STEP_PREFLIGHT,
    STEP_CACHE_LOOKUP,
    STEP_LLM_CALL,
    STEP_SAFETY_GATE,
    STEP_CACHE_SAVE,
    STEP_TRACING,
    DEFAULT_STEP_BUDGETS_MS,
    DEFAULT_TOTAL_BUDGET_MS,
    LatencySample,
    BudgetViolation,
    AuditReport,
    new_sample,
    record_step,
    finalize,
    measure,
    evaluate,
    to_trace_event,
    to_alert_payload,
    aggregate_step_p95,
    aggregate_total_p95,
)
from engine.safety.slo.kpi_dashboard import (
    KPI_CRISIS_BLOCK_RATE,
    KPI_JAILBREAK_BLOCK_RATE,
    KPI_PII_LEAK_COUNT,
    KPI_PERSONA_PASS_RATE,
    KPI_SAFETY_GATE_CRITICAL,
    KPI_GOLDEN_SET_PASS,
    KPI_RESPONSE_ALIGNMENT,
    KPI_CONSISTENCY_PASS,
    KPI_P95_LATENCY,
    KPI_P99_LATENCY,
    KPI_CACHE_HIT_RATE,
    KPI_DAILY_COST,
    KPI_MONTHLY_COST_PERCENT,
    STATUS_GOOD,
    STATUS_WARN,
    STATUS_BAD,
    TREND_UP,
    TREND_FLAT,
    TREND_DOWN,
    KPIThreshold,
    KPIMetric,
    DashboardPayload,
    classify_status,
    classify_trend,
    build_kpi,
    build_dashboard,
    to_grafana_json,
    to_datadog_metrics,
    format_dashboard_text,
)
from engine.safety.slo.tracing import (
    emit_face_reading_event,
    FaceReadingTrace,
)
from engine.safety.slo.prompt_cache_telemetry import (
    PromptCacheUsage,
    extract_usage,
    summarize,
)
from engine.safety.audit.changelog_tracker import (
    CHANGE_ADDED,
    CHANGE_MODIFIED,
    CHANGE_DEPRECATED,
    CHANGE_REMOVED,
    CHANGE_REGULATION_ADDED,
    REASON_INCIDENT,
    REASON_REGULATION,
    REASON_IMPROVEMENT,
    REASON_DEPRECATION,
    ChangelogEntry,
    ChangelogStore,
    entry_to_dict,
    to_jsonl_lines,
    format_changelog_text,
    DEFAULT_STORE,
    record_change,
    get_default_store,
)
from engine.safety.audit.standard_doc_builder import (
    build_markdown_report,
    build_json_summary,
    build_json_string,
    build_audit_letter,
)
from engine.safety.audit.quarterly_review import (
    IncidentSummary,
    QuarterlyReview,
    compute_mttr_minutes,
    evaluate_grade,
    derive_next_quarter_focus,
    build_executive_summary,
    build_review,
    format_markdown,
    to_json,
)
from engine.safety.audit.model_card import (
    MODEL_CARD_SECTIONS,
    DATA_CARD_SECTIONS,
    ModelCard,
    DataCard,
    get_face_reading_model_card,
    get_face_reading_data_card,
    validate_model_card,
    validate_data_card,
    card_to_dict,
)
from engine.safety.audit.manual_index import (
    CATEGORY_INPUT_GUARD,
    CATEGORY_OUTPUT_GUARD,
    CATEGORY_RUNTIME,
    CATEGORY_GOVERNANCE,
    CATEGORY_OBSERVABILITY,
    CATEGORY_INCIDENT,
    CATEGORY_DOCS,
    TIMING_PREFLIGHT,
    TIMING_RUNTIME,
    TIMING_POSTFLIGHT,
    TIMING_PERIODIC,
    ManualEntry,
    get_all_entries,
    find_by_category,
    find_by_timing,
    find_by_severity,
    find_by_regulation,
    get_entry_by_module,
    format_index_text,
    to_json_summary,
)
from engine.safety.audit.shadow_eval import (
    CANDIDATE_BETTER,
    CANDIDATE_NEUTRAL,
    CANDIDATE_WORSE,
    ShadowComparison,
    jaccard_overlap,
    compare_pair,
    aggregate_shadow_results,
)
from engine.safety.audit.dependency_graph import (
    HOTSPOT_IN_DEGREE,
    DependencyNode,
    DependencyGraph,
    collect_module_imports,
    build_graph,
    in_degree,
    out_degree,
    has_cycles,
    get_dependents,
    get_dependencies,
    format_graph_text,
)
from engine.safety.audit.onboarding_checklist import (
    PHASE_DAY1,
    PHASE_WEEK1,
    PHASE_MONTH1,
    PHASE_ONGOING,
    STATUS_NOT_STARTED,
    STATUS_IN_PROGRESS,
    STATUS_COMPLETED,
    ChecklistItem,
    get_all_items,
    get_items_by_phase,
    get_item,
    total_estimated_minutes,
    evaluate_progress,
    format_progress_text,
)
from engine.safety.audit.postmortem_builder import (
    NOTIFICATION_NONE,
    NOTIFICATION_INTERNAL,
    NOTIFICATION_DPO,
    NOTIFICATION_REGULATOR_72H,
    NOTIFICATION_USERS,
    TimelineEvent,
    RemediationAction,
    PostmortemDraft,
    evaluate_notification_required,
    build_five_whys_template,
    build_draft,
)
from engine.safety.audit.compliance_report import (
    COMPLIANCE_MANIFEST,
    ItemReport,
    ComplianceReport,
    check_item,
    generate_report,
    format_report_text,
)
from engine.safety.input_guards.input_sanitizer import (
    MAX_QUESTION_CHARS,
    MAX_NAME_CHARS,
    SanitizeResult,
    sanitize_question,
    sanitize_name,
    has_injection_attempt,
)
from engine.safety.input_guards.rate_limiter import (
    WINDOW_MINUTE_SEC,
    WINDOW_HOUR_SEC,
    WINDOW_DAY_SEC,
    DEFAULT_PER_MINUTE,
    DEFAULT_PER_HOUR,
    DEFAULT_PER_DAY,
    RESULT_ALLOWED,
    RESULT_LIMITED,
    RateLimitConfig,
    RateLimitResult,
    RateLimiter,
)
from engine.safety.input_guards.file_integrity import (
    DEFAULT_MAX_BYTES,
    ALLOWED_MIMES,
    IntegrityResult,
    validate_image_bytes,
    validate_image_base64,
)
from engine.safety.input_guards.cache_integrity import (
    INTEGRITY_PARSE_ERROR,
    INTEGRITY_MISSING_KEY,
    INTEGRITY_EMPTY_TEXT,
    INTEGRITY_MISSING_LEGAL,
    INTEGRITY_NOT_DICT,
    INTEGRITY_PROMPT_HASH_MISMATCH,
    IntegrityAuditReport,
    verify_cache_file,
    audit_cache_directory,
    list_corrupt_files,
)
from engine.safety.input_guards.cache_janitor import (
    DEFAULT_TTL_SEC,
    DISK_WARN_BYTES,
    JanitorReport,
    find_expired_files,
    run_janitor,
    should_alert_disk_full,
)
from engine.safety.input_guards.cache_key_resolver import (
    CACHE_KEY_LENGTH,
    CacheKey,
    resolve_cache_key,
    invalidates_on_prompt_change,
)
from engine.safety.input_guards.idempotency_key import (
    DEFAULT_WINDOW_SEC,
    SLOT_PENDING,
    SLOT_RESOLVED,
    SLOT_FAILED,
    IdempotencySlot,
    compute_idempotency_key,
    IdempotencyManager,
)
from engine.safety.input_guards.canary_guard import (
    DECISION_PROMOTE,
    DECISION_HOLD,
    DECISION_ROLLBACK,
    CANARY_STAGES,
    CANARY_THRESHOLDS,
    CanaryMetrics,
    CanaryDecision,
    has_sufficient_sample,
    decide_canary,
    metrics_from_slo_report,
)
from engine.safety.input_guards.cost_guard import (
    DEFAULT_PRICING_USD_PER_M,
    WARN_PERCENT,
    CRITICAL_PERCENT,
    CostBudget,
    CostRecord,
    CostStatus,
    calculate_cost,
    CostTracker,
)
from engine.safety.incident.playbook import (
    INCIDENT_CRISIS_BLOCK_FAILED,
    INCIDENT_SLO_CRISIS_RATE,
    INCIDENT_SLO_P95,
    INCIDENT_SLO_ERR_RATE,
    INCIDENT_PII_LEAK,
    INCIDENT_COST_EXHAUSTED,
    INCIDENT_CACHE_CORRUPTION,
    INCIDENT_BACKUP_OVERDUE,
    INCIDENT_CANARY_ROLLBACK,
    INCIDENT_RATE_ABUSE,
    INCIDENT_JAILBREAK_LEAK,
    PlaybookStep,
    IncidentPlaybook,
    get_all_playbooks,
    get_playbook,
    list_playbooks_by_severity,
    list_p0_playbooks,
    format_playbook_text,
    to_alert_attachment,
)
from engine.safety.incident.rollback_trigger import (
    AUTO,
    APPROVAL,
    NEVER,
    RollbackDecision,
    classify_rollback_policy,
    build_revert_command,
    decide_rollback,
    should_execute_immediately,
)
from engine.safety.incident.backup_manifest import (
    BACKUP_KIND_PERSISTENT,
    BACKUP_KIND_VOLATILE,
    BACKUP_KIND_AUDIT,
    RECOVERY_PRIORITY_P0,
    RECOVERY_PRIORITY_P1,
    RECOVERY_PRIORITY_P2,
    BackupResource,
    BackupRecord,
    get_face_reading_manifest,
    list_backup_targets,
    get_resource_by_id,
    list_by_priority,
    is_within_rpo,
    overdue_backups,
    compute_sha256,
    verify_backup_record,
)
from engine.safety.incident.llm_fallback_router import (
    BACKEND_GEMINI,
    BACKEND_CLAUDE,
    BACKEND_STUB,
    LLMCallPlan,
    FallbackDecision,
    TRIGGER_NETWORK_ERROR,
    TRIGGER_EMPTY_RESPONSE,
    TRIGGER_TOKEN_LIMIT,
    TRIGGER_PERSONA_FAILED,
    TRIGGER_JAILBREAK_LEAK,
    TRIGGER_NONE,
    classify_failure,
    should_fallback,
    get_region_preference,
    plan_llm_calls,
    deterministic_stub_response,
)
from engine.safety.llm.output_sampler import (
    sample_llm_output,
)
from engine.safety.llm.output_safety_gate import (
    VERDICT_CLEAN,
    VERDICT_MINOR,
    VERDICT_WARN,
    VERDICT_CRITICAL,
    SafetyGateResult,
    run_safety_gates,
)
from engine.safety.llm.output_token_guard import (
    ISSUE_TOO_SHORT,
    ISSUE_TOO_LONG,
    ISSUE_TRUNCATED,
    ISSUE_LANGUAGE_DRIFT,
    ISSUE_REPETITION,
    ISSUE_NONE,
    MIN_CHARS,
    MAX_CHARS,
    KO_LANG_MIN,
    REPETITION_PHRASE_LEN,
    REPETITION_MIN,
    TokenGuardResult,
    evaluate_output,
    should_trigger_fallback,
    to_fallback_trigger,
)
from engine.safety.llm.persona_self_eval import (
    PERSONA_ENCOURAGED,
    PERSONA_FORBIDDEN,
    MEDICAL_LEGAL_FORBIDDEN,
    MIN_ENCOURAGED_HITS,
    PersonaEvalResult,
    evaluate_persona_tone,
    to_response_dict,
    aggregate_pass_rate,
)
from engine.safety.llm.response_alignment import (
    ALIGN_TOPIC_MISSING,
    ALIGN_OFF_TOPIC,
    ALIGN_QUESTION_IGNORED,
    AlignmentResult,
    detect_topic,
    check_response_topic,
    evaluate_alignment,
)
from engine.safety.llm.response_consistency import (
    LENGTH_CV_MAX,
    TOPIC_AGREEMENT_MIN,
    MIN_SAMPLES_FOR_EVAL,
    CONSISTENCY_PERSONA_DROP,
    CONSISTENCY_MEDICAL_LEAK,
    CONSISTENCY_FORBIDDEN_INCONSISTENT,
    CONSISTENCY_TOPIC_DRIFT,
    CONSISTENCY_LENGTH_VARIANCE_HIGH,
    ConsistencyReport,
    evaluate_consistency,
)
from engine.safety.llm.response_envelope import (
    ENVELOPE_NORMAL,
    ENVELOPE_CACHED,
    ENVELOPE_CRISIS,
    ENVELOPE_JAILBREAK,
    ENVELOPE_ERROR,
    ENVELOPE_WARN,
    REQUIRED_KEYS,
    detect_branch,
    validate_envelope,
    is_valid,
    normalize_envelope,
    audit_envelopes,
)
from engine.safety.llm.response_fact_check import (
    FACT_AGE,
    FACT_GENDER,
    FACT_FACE_COUNT,
    FACT_REGION,
    FACT_GAZE,
    FactCheckResult,
    check_age_consistency,
    check_gender_consistency,
    check_face_count,
    check_region_consistency,
    check_gaze_consistency,
    check_response,
)
from engine.safety.llm.response_pii_leak import (
    PII_PHONE_KR,
    PII_PHONE_INTL,
    PII_EMAIL,
    PII_KOR_SSN,
    PII_CREDIT_CARD,
    PII_IPV4,
    PII_API_KEY,
    PIILeakResult,
    find_phone_kr,
    find_phone_intl,
    find_email,
    find_kor_ssn,
    find_credit_card,
    find_ipv4,
    find_api_key,
    scan,
    has_leak,
    scan_response_pii,
    has_pii_leak,
)
from engine.safety.llm.jailbreak_defense import (
    CATEGORY_PERSONA_OVERRIDE,
    CATEGORY_PROMPT_EXTRACTION,
    CATEGORY_FORBIDDEN_ADVICE,
    CATEGORY_HARM_INSTRUCTION,
    CATEGORY_RACIAL_GENERALIZATION,
    JailbreakHit,
    detect_jailbreak,
    is_jailbreak_attempt,
    get_rejection_text,
    build_jailbreak_response,
)
from engine.safety.photo.guide import (
    PHOTO_CHECKLIST_KO,
    PHOTO_CHECKLIST_EN,
    PHOTO_CHECKLIST_JA,
    PHOTO_CHECKLIST_ZH,
    get_photo_checklist,
    get_error_hint,
    get_retry_tips,
    build_photo_guidance,
)
from engine.safety.photo.quality import (
    THRESHOLD_PALM,
    THRESHOLD_FACE,
    THRESHOLD_DEFAULT,
    Domain,
    BlurResult,
    compute_blur_score,
    is_acceptable,
)
from engine.safety.misc.feedback import (
    reading_hash,
    record_feedback,
    get_aggregate_stats,
    get_reading_counts,
)
from engine.safety.misc.language import (
    detect_language,
    get_language_advisory,
)
from engine.safety.misc.quick_check import (
    run_quick_check,
    format_quick_check_text,
)
from engine.safety.misc.request_pipeline import (
    BLOCK_RATE_LIMITED,
    BLOCK_COST_EXHAUSTED,
    BLOCK_JAILBREAK,
    BLOCK_INPUT_EMPTY,
    PipelineDecision,
    preflight,
)



# ADR-051 호환 alias — 옛 test의 긴 이름 → 현 짧은 이름 노출
# 각 alias 개별 try/except로 일부 실패가 나머지 영향 안 끼치게 격리
try:
    from engine.safety.audit.changelog_tracker import record_change as record_change_log
except ImportError:
    pass
try:
    from engine.safety.audit.changelog_tracker import get_default_store as get_changelog_store
except ImportError:
    pass
try:
    from engine.safety.slo.latency_audit import new_sample as new_latency_sample
except ImportError:
    pass
try:
    from engine.safety.slo.latency_audit import record_step as record_latency_step
except ImportError:
    pass
try:
    from engine.safety.slo.latency_audit import finalize as finalize_latency_sample
except ImportError:
    pass
try:
    from engine.safety.slo.latency_audit import evaluate as evaluate_latency
except ImportError:
    pass
try:
    from engine.safety.audit.dependency_graph import build_graph as build_dependency_graph
except ImportError:
    pass
try:
    from engine.safety.audit.dependency_graph import in_degree as in_degree_of
except ImportError:
    pass
try:
    from engine.safety.audit.dependency_graph import out_degree as out_degree_of
except ImportError:
    pass
try:
    from engine.safety.audit.dependency_graph import has_cycles as has_dependency_cycles
except ImportError:
    pass
try:
    from engine.safety.audit.dependency_graph import format_graph as format_dependency_graph
except ImportError:
    pass
try:
    from engine.safety.audit.dependency_graph import graph_to_json as dependency_graph_to_json
except ImportError:
    pass
try:
    from engine.safety.audit.quarterly_review import format_markdown as format_quarterly_review_markdown
except ImportError:
    pass
try:
    from engine.safety.audit.quarterly_review import to_json as quarterly_review_to_json
except ImportError:
    pass
try:
    from engine.safety.audit.quarterly_review import build_review as build_quarterly_review
except ImportError:
    pass
try:
    from engine.safety.audit.quarterly_review import evaluate_grade as evaluate_quarterly_grade
except ImportError:
    pass
try:
    from engine.safety.audit.postmortem_builder import format_postmortem as format_postmortem_markdown
except ImportError:
    pass
try:
    from engine.safety.audit.postmortem_builder import to_json as postmortem_to_json
except ImportError:
    pass
try:
    from engine.safety.audit.postmortem_builder import build_draft as build_postmortem_draft
except ImportError:
    pass
try:
    from engine.safety.audit.compliance_report import generate_report as generate_compliance_report
except ImportError:
    pass
try:
    from engine.safety.audit.compliance_report import check_item as check_compliance_item
except ImportError:
    pass
try:
    from engine.safety.audit.manual_index import to_json_summary as manual_index_to_json
except ImportError:
    pass
try:
    from engine.safety.audit.manual_index import format_index_text as format_manual_index
except ImportError:
    pass
try:
    from engine.safety.audit.manual_index import get_all_entries as get_manual_entries
except ImportError:
    pass
try:
    from engine.safety.audit.manual_index import find_by_category as find_manual_by_category
except ImportError:
    pass
try:
    from engine.safety.audit.manual_index import find_by_timing as find_manual_by_timing
except ImportError:
    pass
try:
    from engine.safety.audit.manual_index import find_by_severity as find_manual_by_severity
except ImportError:
    pass
try:
    from engine.safety.audit.manual_index import find_by_regulation as find_manual_by_regulation
except ImportError:
    pass
try:
    from engine.safety.audit.postmortem_builder import format_markdown as format_postmortem_markdown
except ImportError:
    pass
try:
    from engine.safety.audit.dependency_graph import format_graph_text as format_dependency_graph
except ImportError:
    pass
try:
    from engine.safety.audit.dependency_graph import to_json as dependency_graph_to_json
except ImportError:
    pass
try:
    from engine.safety.audit.onboarding_checklist import evaluate_progress as evaluate_onboarding_progress
except ImportError:
    pass
try:
    from engine.safety.audit.onboarding_checklist import get_all_items as get_onboarding_items
except ImportError:
    pass
try:
    from engine.safety.audit.onboarding_checklist import get_items_by_phase as get_onboarding_items_by_phase
except ImportError:
    pass

__all__ = [
    # 9 카테고리
    "crisis", "gdpr", "slo", "audit", "input_guards",
    "incident", "llm", "photo", "misc",
    # 평면 alias
    "crisis_detector", "crisis_resources", "alert_router", "emotion_disclosure",
    "dsr_processor", "consent_screen", "pii", "data_governance",
    "rights_information", "regulation", "legal_notice",
    "slo_module", "latency_audit", "kpi_dashboard", "tracing", "prompt_cache_telemetry",
    "changelog_tracker", "standard_doc_builder", "quarterly_review", "model_card",
    "manual_index", "shadow_eval", "dependency_graph", "onboarding_checklist",
    "postmortem_builder", "compliance_report",
    "input_sanitizer", "rate_limiter", "file_integrity", "cache_integrity",
    "cache_janitor", "cache_key_resolver", "idempotency_key", "canary_guard", "cost_guard",
    "incident_playbook", "rollback_trigger", "backup_manifest", "llm_fallback_router",
    "llm_output_sampler", "output_safety_gate", "output_token_guard", "persona_self_eval",
    "response_alignment", "response_consistency", "response_envelope",
    "response_fact_check", "response_pii_leak", "jailbreak_defense",
    "photo_guide", "photo_quality",
    "feedback", "language", "quick_check", "request_pipeline",
    # 모든 public 심볼
    "EMERGENCY_HOTLINES_KR",
    "DIRECT_SUICIDE_KEYWORDS",
    "DIRECT_SELFHARM_KEYWORDS",
    "INDIRECT_DESPAIR_KEYWORDS",
    "PLANNING_KEYWORDS",
    "NEGATION_PATTERNS",
    "CRISIS_RESPONSE_KO",
    "detect_crisis",
    "CrisisHotline",
    "get_crisis_resources",
    "format_hotlines_text",
    "list_supported_crisis_regions",
    "P0",
    "P1",
    "P2",
    "P3",
    "SEVERITY_LABELS",
    "CHANNEL_MAP",
    "DEBOUNCE_WINDOW_SEC",
    "AlertEvent",
    "classify_slo_violation",
    "classify_event",
    "Debouncer",
    "build_slack_message",
    "build_pagerduty_event",
    "route_alert",
    "alerts_from_slo_report",
    "is_emotion_disclosure_required",
    "is_emotion_disclosure_recommended",
    "build_emotion_disclosure",
    "inject_emotion_disclosure",
    "get_disclosure_metadata",
    "DSR_STATUS_PENDING",
    "DSR_STATUS_PLANNED",
    "DSR_STATUS_EXECUTED",
    "DSR_STATUS_REJECTED",
    "DSRRequest",
    "DSRPlan",
    "ingest_dsr",
    "plan_dsr",
    "execute_dsr",
    "build_audit_record",
    "process_dsr",
    "CONSENT_FIELDS",
    "ConsentItem",
    "get_consent_screen",
    "validate_consent_payload",
    "mask_pii",
    "hash_uid",
    "hash_question",
    "mask_crisis_keyword",
    "LICIT_SOURCES",
    "ILLICIT_SOURCES",
    "REQUIRED_CONSENT_FIELDS",
    "MAX_RETENTION_DAYS",
    "DataProvenance",
    "validate_provenance",
    "is_eligible_for_regression",
    "is_expired",
    "days_until_expiry",
    "audit_dataset",
    "RIGHT_KEYS",
    "AUTOMATION_AUTO",
    "AUTOMATION_MANUAL",
    "AUTOMATION_NA",
    "RightInfo",
    "get_rights_information",
    "get_right_by_key",
    "list_automatable_rights",
    "get_sla_for_region",
    "RegulationProfile",
    "get_regulation_profile",
    "is_biometric_inference_restricted",
    "list_supported_regions",
    "MEDICAL_DISCLAIMER_KO",
    "FORTUNE_DISCLAIMER_KO",
    "DATA_NOTICE_KO",
    "LEGAL_NOTICE_FOOTER_KO",
    "CRISIS_FOOTER_KO",
    "build_legal_footer",
    "SLO_THRESHOLDS",
    "parse_log_line",
    "compute_slo",
    "compute_slo_from_lines",
    "STEP_PREFLIGHT",
    "STEP_CACHE_LOOKUP",
    "STEP_LLM_CALL",
    "STEP_SAFETY_GATE",
    "STEP_CACHE_SAVE",
    "STEP_TRACING",
    "DEFAULT_STEP_BUDGETS_MS",
    "DEFAULT_TOTAL_BUDGET_MS",
    "LatencySample",
    "BudgetViolation",
    "AuditReport",
    "new_sample",
    "record_step",
    "finalize",
    "measure",
    "evaluate",
    "to_trace_event",
    "to_alert_payload",
    "aggregate_step_p95",
    "aggregate_total_p95",
    "KPI_CRISIS_BLOCK_RATE",
    "KPI_JAILBREAK_BLOCK_RATE",
    "KPI_PII_LEAK_COUNT",
    "KPI_PERSONA_PASS_RATE",
    "KPI_SAFETY_GATE_CRITICAL",
    "KPI_GOLDEN_SET_PASS",
    "KPI_RESPONSE_ALIGNMENT",
    "KPI_CONSISTENCY_PASS",
    "KPI_P95_LATENCY",
    "KPI_P99_LATENCY",
    "KPI_CACHE_HIT_RATE",
    "KPI_DAILY_COST",
    "KPI_MONTHLY_COST_PERCENT",
    "STATUS_GOOD",
    "STATUS_WARN",
    "STATUS_BAD",
    "TREND_UP",
    "TREND_FLAT",
    "TREND_DOWN",
    "KPIThreshold",
    "KPIMetric",
    "DashboardPayload",
    "classify_status",
    "classify_trend",
    "build_kpi",
    "build_dashboard",
    "to_grafana_json",
    "to_datadog_metrics",
    "format_dashboard_text",
    "emit_face_reading_event",
    "FaceReadingTrace",
    "PromptCacheUsage",
    "extract_usage",
    "summarize",
    "CHANGE_ADDED",
    "CHANGE_MODIFIED",
    "CHANGE_DEPRECATED",
    "CHANGE_REMOVED",
    "CHANGE_REGULATION_ADDED",
    "REASON_INCIDENT",
    "REASON_REGULATION",
    "REASON_IMPROVEMENT",
    "REASON_DEPRECATION",
    "ChangelogEntry",
    "ChangelogStore",
    "entry_to_dict",
    "to_jsonl_lines",
    "format_changelog_text",
    "DEFAULT_STORE",
    "record_change",
    "get_default_store",
    "build_markdown_report",
    "build_json_summary",
    "build_json_string",
    "build_audit_letter",
    "IncidentSummary",
    "QuarterlyReview",
    "compute_mttr_minutes",
    "evaluate_grade",
    "derive_next_quarter_focus",
    "build_executive_summary",
    "build_review",
    "format_markdown",
    "to_json",
    "MODEL_CARD_SECTIONS",
    "DATA_CARD_SECTIONS",
    "ModelCard",
    "DataCard",
    "get_face_reading_model_card",
    "get_face_reading_data_card",
    "validate_model_card",
    "validate_data_card",
    "card_to_dict",
    "CATEGORY_INPUT_GUARD",
    "CATEGORY_OUTPUT_GUARD",
    "CATEGORY_RUNTIME",
    "CATEGORY_GOVERNANCE",
    "CATEGORY_OBSERVABILITY",
    "CATEGORY_INCIDENT",
    "CATEGORY_DOCS",
    "TIMING_PREFLIGHT",
    "TIMING_RUNTIME",
    "TIMING_POSTFLIGHT",
    "TIMING_PERIODIC",
    "ManualEntry",
    "get_all_entries",
    "find_by_category",
    "find_by_timing",
    "find_by_severity",
    "find_by_regulation",
    "get_entry_by_module",
    "format_index_text",
    "to_json_summary",
    "CANDIDATE_BETTER",
    "CANDIDATE_NEUTRAL",
    "CANDIDATE_WORSE",
    "ShadowComparison",
    "jaccard_overlap",
    "compare_pair",
    "aggregate_shadow_results",
    "HOTSPOT_IN_DEGREE",
    "DependencyNode",
    "DependencyGraph",
    "collect_module_imports",
    "build_graph",
    "in_degree",
    "out_degree",
    "has_cycles",
    "get_dependents",
    "get_dependencies",
    "format_graph_text",
    "PHASE_DAY1",
    "PHASE_WEEK1",
    "PHASE_MONTH1",
    "PHASE_ONGOING",
    "STATUS_NOT_STARTED",
    "STATUS_IN_PROGRESS",
    "STATUS_COMPLETED",
    "ChecklistItem",
    "get_all_items",
    "get_items_by_phase",
    "get_item",
    "total_estimated_minutes",
    "evaluate_progress",
    "format_progress_text",
    "NOTIFICATION_NONE",
    "NOTIFICATION_INTERNAL",
    "NOTIFICATION_DPO",
    "NOTIFICATION_REGULATOR_72H",
    "NOTIFICATION_USERS",
    "TimelineEvent",
    "RemediationAction",
    "PostmortemDraft",
    "evaluate_notification_required",
    "build_five_whys_template",
    "build_draft",
    "COMPLIANCE_MANIFEST",
    "ItemReport",
    "ComplianceReport",
    "check_item",
    "generate_report",
    "format_report_text",
    "MAX_QUESTION_CHARS",
    "MAX_NAME_CHARS",
    "SanitizeResult",
    "sanitize_question",
    "sanitize_name",
    "has_injection_attempt",
    "WINDOW_MINUTE_SEC",
    "WINDOW_HOUR_SEC",
    "WINDOW_DAY_SEC",
    "DEFAULT_PER_MINUTE",
    "DEFAULT_PER_HOUR",
    "DEFAULT_PER_DAY",
    "RESULT_ALLOWED",
    "RESULT_LIMITED",
    "RateLimitConfig",
    "RateLimitResult",
    "RateLimiter",
    "DEFAULT_MAX_BYTES",
    "ALLOWED_MIMES",
    "IntegrityResult",
    "validate_image_bytes",
    "validate_image_base64",
    "INTEGRITY_PARSE_ERROR",
    "INTEGRITY_MISSING_KEY",
    "INTEGRITY_EMPTY_TEXT",
    "INTEGRITY_MISSING_LEGAL",
    "INTEGRITY_NOT_DICT",
    "INTEGRITY_PROMPT_HASH_MISMATCH",
    "IntegrityAuditReport",
    "verify_cache_file",
    "audit_cache_directory",
    "list_corrupt_files",
    "DEFAULT_TTL_SEC",
    "DISK_WARN_BYTES",
    "JanitorReport",
    "find_expired_files",
    "run_janitor",
    "should_alert_disk_full",
    "CACHE_KEY_LENGTH",
    "CacheKey",
    "resolve_cache_key",
    "invalidates_on_prompt_change",
    "DEFAULT_WINDOW_SEC",
    "SLOT_PENDING",
    "SLOT_RESOLVED",
    "SLOT_FAILED",
    "IdempotencySlot",
    "compute_idempotency_key",
    "IdempotencyManager",
    "DECISION_PROMOTE",
    "DECISION_HOLD",
    "DECISION_ROLLBACK",
    "CANARY_STAGES",
    "CANARY_THRESHOLDS",
    "CanaryMetrics",
    "CanaryDecision",
    "has_sufficient_sample",
    "decide_canary",
    "metrics_from_slo_report",
    "DEFAULT_PRICING_USD_PER_M",
    "WARN_PERCENT",
    "CRITICAL_PERCENT",
    "CostBudget",
    "CostRecord",
    "CostStatus",
    "calculate_cost",
    "CostTracker",
    "INCIDENT_CRISIS_BLOCK_FAILED",
    "INCIDENT_SLO_CRISIS_RATE",
    "INCIDENT_SLO_P95",
    "INCIDENT_SLO_ERR_RATE",
    "INCIDENT_PII_LEAK",
    "INCIDENT_COST_EXHAUSTED",
    "INCIDENT_CACHE_CORRUPTION",
    "INCIDENT_BACKUP_OVERDUE",
    "INCIDENT_CANARY_ROLLBACK",
    "INCIDENT_RATE_ABUSE",
    "INCIDENT_JAILBREAK_LEAK",
    "PlaybookStep",
    "IncidentPlaybook",
    "get_all_playbooks",
    "get_playbook",
    "list_playbooks_by_severity",
    "list_p0_playbooks",
    "format_playbook_text",
    "to_alert_attachment",
    "AUTO",
    "APPROVAL",
    "NEVER",
    "RollbackDecision",
    "classify_rollback_policy",
    "build_revert_command",
    "decide_rollback",
    "should_execute_immediately",
    "BACKUP_KIND_PERSISTENT",
    "BACKUP_KIND_VOLATILE",
    "BACKUP_KIND_AUDIT",
    "RECOVERY_PRIORITY_P0",
    "RECOVERY_PRIORITY_P1",
    "RECOVERY_PRIORITY_P2",
    "BackupResource",
    "BackupRecord",
    "get_face_reading_manifest",
    "list_backup_targets",
    "get_resource_by_id",
    "list_by_priority",
    "is_within_rpo",
    "overdue_backups",
    "compute_sha256",
    "verify_backup_record",
    "BACKEND_GEMINI",
    "BACKEND_CLAUDE",
    "BACKEND_STUB",
    "LLMCallPlan",
    "FallbackDecision",
    "TRIGGER_NETWORK_ERROR",
    "TRIGGER_EMPTY_RESPONSE",
    "TRIGGER_TOKEN_LIMIT",
    "TRIGGER_PERSONA_FAILED",
    "TRIGGER_JAILBREAK_LEAK",
    "TRIGGER_NONE",
    "classify_failure",
    "should_fallback",
    "get_region_preference",
    "plan_llm_calls",
    "deterministic_stub_response",
    "sample_llm_output",
    "VERDICT_CLEAN",
    "VERDICT_MINOR",
    "VERDICT_WARN",
    "VERDICT_CRITICAL",
    "SafetyGateResult",
    "run_safety_gates",
    "ISSUE_TOO_SHORT",
    "ISSUE_TOO_LONG",
    "ISSUE_TRUNCATED",
    "ISSUE_LANGUAGE_DRIFT",
    "ISSUE_REPETITION",
    "ISSUE_NONE",
    "MIN_CHARS",
    "MAX_CHARS",
    "KO_LANG_MIN",
    "REPETITION_PHRASE_LEN",
    "REPETITION_MIN",
    "TokenGuardResult",
    "evaluate_output",
    "should_trigger_fallback",
    "to_fallback_trigger",
    "PERSONA_ENCOURAGED",
    "PERSONA_FORBIDDEN",
    "MEDICAL_LEGAL_FORBIDDEN",
    "MIN_ENCOURAGED_HITS",
    "PersonaEvalResult",
    "evaluate_persona_tone",
    "to_response_dict",
    "aggregate_pass_rate",
    "ALIGN_TOPIC_MISSING",
    "ALIGN_OFF_TOPIC",
    "ALIGN_QUESTION_IGNORED",
    "AlignmentResult",
    "detect_topic",
    "check_response_topic",
    "evaluate_alignment",
    "LENGTH_CV_MAX",
    "TOPIC_AGREEMENT_MIN",
    "MIN_SAMPLES_FOR_EVAL",
    "CONSISTENCY_PERSONA_DROP",
    "CONSISTENCY_MEDICAL_LEAK",
    "CONSISTENCY_FORBIDDEN_INCONSISTENT",
    "CONSISTENCY_TOPIC_DRIFT",
    "CONSISTENCY_LENGTH_VARIANCE_HIGH",
    "ConsistencyReport",
    "evaluate_consistency",
    "ENVELOPE_NORMAL",
    "ENVELOPE_CACHED",
    "ENVELOPE_CRISIS",
    "ENVELOPE_JAILBREAK",
    "ENVELOPE_ERROR",
    "ENVELOPE_WARN",
    "REQUIRED_KEYS",
    "detect_branch",
    "validate_envelope",
    "is_valid",
    "normalize_envelope",
    "audit_envelopes",
    "FACT_AGE",
    "FACT_GENDER",
    "FACT_FACE_COUNT",
    "FACT_REGION",
    "FACT_GAZE",
    "FactCheckResult",
    "check_age_consistency",
    "check_gender_consistency",
    "check_face_count",
    "check_region_consistency",
    "check_gaze_consistency",
    "check_response",
    "PII_PHONE_KR",
    "PII_PHONE_INTL",
    "PII_EMAIL",
    "PII_KOR_SSN",
    "PII_CREDIT_CARD",
    "PII_IPV4",
    "PII_API_KEY",
    "PIILeakResult",
    "find_phone_kr",
    "find_phone_intl",
    "find_email",
    "find_kor_ssn",
    "find_credit_card",
    "find_ipv4",
    "find_api_key",
    "scan",
    "has_leak",
    "scan_response_pii",
    "has_pii_leak",
    "CATEGORY_PERSONA_OVERRIDE",
    "CATEGORY_PROMPT_EXTRACTION",
    "CATEGORY_FORBIDDEN_ADVICE",
    "CATEGORY_HARM_INSTRUCTION",
    "CATEGORY_RACIAL_GENERALIZATION",
    "JailbreakHit",
    "detect_jailbreak",
    "is_jailbreak_attempt",
    "get_rejection_text",
    "build_jailbreak_response",
    "PHOTO_CHECKLIST_KO",
    "PHOTO_CHECKLIST_EN",
    "PHOTO_CHECKLIST_JA",
    "PHOTO_CHECKLIST_ZH",
    "get_photo_checklist",
    "get_error_hint",
    "get_retry_tips",
    "build_photo_guidance",
    "THRESHOLD_PALM",
    "THRESHOLD_FACE",
    "THRESHOLD_DEFAULT",
    "Domain",
    "BlurResult",
    "compute_blur_score",
    "is_acceptable",
    "reading_hash",
    "record_feedback",
    "get_aggregate_stats",
    "get_reading_counts",
    "detect_language",
    "get_language_advisory",
    "run_quick_check",
    "format_quick_check_text",
    "BLOCK_RATE_LIMITED",
    "BLOCK_COST_EXHAUSTED",
    "BLOCK_JAILBREAK",
    "BLOCK_INPUT_EMPTY",
    "PipelineDecision",
    "preflight",
]
