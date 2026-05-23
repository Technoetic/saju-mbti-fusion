"""ADR-158 — 야선 아씨 정인 사주 결정론.

content_key='jeongin-saju' — 일지·정관·정인 분석으로 배우자 결정론.
배우자 외모·직업·만나는 시기 단정 차단.
"""
from .scoring import (
    JeonginSajuResult,
    compute_jeongin_saju,
    format_jeongin_saju_for_prompt,
    sanitize_jeongin_saju_text,
)

__all__ = [
    "JeonginSajuResult",
    "compute_jeongin_saju",
    "format_jeongin_saju_for_prompt",
    "sanitize_jeongin_saju_text",
]
