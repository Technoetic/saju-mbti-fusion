"""ADR-158 — 야선 아씨 속궁합 결정론.

본 시스템 char_key='ya' + content_key='sok-gunghap' 백엔드 결정론.
ADR-006 자문 거절 정신 + ADR-002 학파 회피 정합 — LLM 단독 응답 차단.
"""
from .scoring import (
    SokGunghapResult,
    compute_sok_gunghap,
    format_sok_gunghap_for_prompt,
    sanitize_sok_gunghap_text,
)

__all__ = [
    "SokGunghapResult",
    "compute_sok_gunghap",
    "format_sok_gunghap_for_prompt",
    "sanitize_sok_gunghap_text",
]
