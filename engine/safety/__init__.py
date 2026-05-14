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
]
