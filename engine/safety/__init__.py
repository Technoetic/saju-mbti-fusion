"""안전·법적 안전장치 모듈.

본 패키지는 모든 LLM 응답 전후에 의무적으로 호출되어:
  - 자살/자해/위기 신호 결정론 탐지
  - 법정 면책 고지문 자동 첨부
  - 미성년자 차단
  - 정신건강 데이터 동의 검증
을 수행한다. 우회 금지.
"""

from engine.safety.crisis.detector import (
    detect_crisis,
    CRISIS_RESPONSE_KO,
    EMERGENCY_HOTLINES_KR,
)
from engine.safety.gdpr.legal_notice import (
    MEDICAL_DISCLAIMER_KO,
    FORTUNE_DISCLAIMER_KO,
    LEGAL_NOTICE_FOOTER_KO,
    build_legal_footer,
)

# ADR-048: 9 카테고리 서브패키지 + 평면 모듈명 alias (옛 import 호환)
# 옛 test_*.py가 'from engine.safety import X' 또는 'engine.safety.X' 접근하던 패턴 보존.
from engine.safety import (
    crisis,
    gdpr,
    slo,
    audit,
    input_guards,
    incident,
    llm,
    photo,
    misc,
)

# 옛 평면 모듈명 alias (engine.safety.feedback → engine.safety.misc.feedback 등)
from engine.safety.misc import feedback, language, quick_check, request_pipeline
from engine.safety.crisis import detector as crisis_detector
from engine.safety.crisis import resources as crisis_resources
from engine.safety.crisis import alert_router, emotion_disclosure
from engine.safety.gdpr import (
    dsr_processor,
    consent_screen,
    pii,
    data_governance,
    rights_information,
    regulation,
    legal_notice,
)
from engine.safety.slo import (
    slo as slo_module,
    latency_audit,
    kpi_dashboard,
    tracing,
    prompt_cache_telemetry,
)
from engine.safety.audit import (
    changelog_tracker,
    standard_doc_builder,
    quarterly_review,
    model_card,
    manual_index,
    shadow_eval,
    dependency_graph,
    onboarding_checklist,
    postmortem_builder,
    compliance_report,
)
from engine.safety.input_guards import (
    input_sanitizer,
    rate_limiter,
    file_integrity,
    cache_integrity,
    cache_janitor,
    cache_key_resolver,
    idempotency_key,
    canary_guard,
    cost_guard,
)
from engine.safety.incident import (
    playbook as incident_playbook,
    rollback_trigger,
    backup_manifest,
    llm_fallback_router,
)
from engine.safety.llm import (
    output_sampler as llm_output_sampler,
    output_safety_gate,
    output_token_guard,
    persona_self_eval,
    response_alignment,
    response_consistency,
    response_envelope,
    response_fact_check,
    response_pii_leak,
    jailbreak_defense,
)
from engine.safety.photo import guide as photo_guide, quality as photo_quality

# 자주 사용되는 함수·class 직접 re-export (옛 test의 hasattr 검증 대상)
from engine.safety.audit.changelog_tracker import (
    ChangelogEntry, ChangelogStore,
    CHANGE_ADDED, CHANGE_MODIFIED, CHANGE_REMOVED,
)

__all__ = [
    # 기존 핵심 함수
    "detect_crisis", "CRISIS_RESPONSE_KO", "EMERGENCY_HOTLINES_KR",
    "MEDICAL_DISCLAIMER_KO", "FORTUNE_DISCLAIMER_KO",
    "LEGAL_NOTICE_FOOTER_KO", "build_legal_footer",
    # 9 카테고리
    "crisis", "gdpr", "slo", "audit", "input_guards",
    "incident", "llm", "photo", "misc",
    # 옛 평면 alias
    "feedback", "language", "quick_check", "request_pipeline",
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
    # 자주 사용
    "ChangelogEntry", "ChangelogStore",
    "CHANGE_ADDED", "CHANGE_MODIFIED", "CHANGE_REMOVED",
]
