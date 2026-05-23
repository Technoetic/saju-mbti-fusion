"""ADR-158 — 야선 아씨 욕망 사주 결정론.

content_key='desire-saju' 백엔드 결정론. 십성 5종 (편관/정관/편재/정재/식상) +
도화·홍염 분포 분석. 성적·외도 단정 차단.
"""
from .scoring import (
    DesireSajuResult,
    compute_desire_saju,
    format_desire_saju_for_prompt,
    sanitize_desire_saju_text,
)

__all__ = [
    "DesireSajuResult",
    "compute_desire_saju",
    "format_desire_saju_for_prompt",
    "sanitize_desire_saju_text",
]
