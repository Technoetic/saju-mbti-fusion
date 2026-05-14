"""안전·법적 안전장치 모듈.

본 패키지는 모든 LLM 응답 전후에 의무적으로 호출되어:
  - 자살/자해/위기 신호 결정론 탐지
  - 법정 면책 고지문 자동 첨부
  - 미성년자 차단
  - 정신건강 데이터 동의 검증
을 수행한다. 우회 금지.
"""

from engine.safety.crisis_detector import (
    detect_crisis,
    CRISIS_RESPONSE_KO,
    EMERGENCY_HOTLINES_KR,
)
from engine.safety.legal_notice import (
    MEDICAL_DISCLAIMER_KO,
    FORTUNE_DISCLAIMER_KO,
    LEGAL_NOTICE_FOOTER_KO,
    build_legal_footer,
)
from engine.safety.pii import (
    mask_pii,
    hash_uid,
    hash_question,
    mask_crisis_keyword,
)
from engine.safety.feedback import (
    record_feedback,
    get_aggregate_stats,
    get_reading_counts,
    reading_hash,
)
from engine.safety.regulation import (
    RegulationProfile,
    get_regulation_profile,
    is_biometric_inference_restricted,
    list_supported_regions,
)
from engine.safety.crisis_resources import (
    CrisisHotline,
    get_crisis_resources,
    format_hotlines_text,
    list_supported_crisis_regions,
)
from engine.safety.language import (
    detect_language,
    get_language_advisory,
)
from engine.safety.tracing import (
    FaceReadingTrace,
    emit_face_reading_event,
)
from engine.safety.slo import (
    SLO_THRESHOLDS,
    parse_log_line,
    compute_slo,
    compute_slo_from_lines,
)
from engine.safety.photo_guide import (
    get_photo_checklist,
    get_error_hint,
    get_retry_tips,
    build_photo_guidance,
)
from engine.safety.data_governance import (
    DataProvenance,
    LICIT_SOURCES,
    ILLICIT_SOURCES,
    REQUIRED_CONSENT_FIELDS,
    MAX_RETENTION_DAYS,
    validate_provenance,
    is_eligible_for_regression,
    is_expired,
    days_until_expiry,
    audit_dataset,
)
from engine.safety.consent_screen import (
    CONSENT_FIELDS,
    ConsentItem,
    get_consent_screen,
    validate_consent_payload,
)
from engine.safety.alert_router import (
    AlertEvent,
    Debouncer,
    classify_event,
    classify_slo_violation,
    route_alert,
    build_slack_message,
    build_pagerduty_event,
    alerts_from_slo_report,
)
from engine.safety.emotion_disclosure import (
    is_emotion_disclosure_required,
    is_emotion_disclosure_recommended,
    build_emotion_disclosure,
    inject_emotion_disclosure,
    get_disclosure_metadata,
)

__all__ = [
    "detect_crisis",
    "CRISIS_RESPONSE_KO",
    "EMERGENCY_HOTLINES_KR",
    "MEDICAL_DISCLAIMER_KO",
    "FORTUNE_DISCLAIMER_KO",
    "LEGAL_NOTICE_FOOTER_KO",
    "build_legal_footer",
    "mask_pii",
    "hash_uid",
    "hash_question",
    "mask_crisis_keyword",
    "record_feedback",
    "get_aggregate_stats",
    "get_reading_counts",
    "reading_hash",
    "RegulationProfile",
    "get_regulation_profile",
    "is_biometric_inference_restricted",
    "list_supported_regions",
    "CrisisHotline",
    "get_crisis_resources",
    "format_hotlines_text",
    "list_supported_crisis_regions",
    "detect_language",
    "get_language_advisory",
    "FaceReadingTrace",
    "emit_face_reading_event",
    "SLO_THRESHOLDS",
    "parse_log_line",
    "compute_slo",
    "compute_slo_from_lines",
    "get_photo_checklist",
    "get_error_hint",
    "get_retry_tips",
    "build_photo_guidance",
    "DataProvenance",
    "LICIT_SOURCES",
    "ILLICIT_SOURCES",
    "REQUIRED_CONSENT_FIELDS",
    "MAX_RETENTION_DAYS",
    "validate_provenance",
    "is_eligible_for_regression",
    "is_expired",
    "days_until_expiry",
    "audit_dataset",
    "CONSENT_FIELDS",
    "ConsentItem",
    "get_consent_screen",
    "validate_consent_payload",
    "AlertEvent",
    "Debouncer",
    "classify_event",
    "classify_slo_violation",
    "route_alert",
    "build_slack_message",
    "build_pagerduty_event",
    "alerts_from_slo_report",
    "is_emotion_disclosure_required",
    "is_emotion_disclosure_recommended",
    "build_emotion_disclosure",
    "inject_emotion_disclosure",
    "get_disclosure_metadata",
]
