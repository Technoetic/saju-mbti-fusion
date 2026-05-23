"""ADR-158 — 야선 아씨 운우지정 결정론.

content_key='unu-jijeong' — 두 사주 + 현재 관계 상황 → 합·충 시기 분석.
대운·세운 합·충 결정론 메타로 시기 흐름 매핑.
"""
from .scoring import (
    UnuJijeongResult,
    compute_unu_jijeong,
    format_unu_jijeong_for_prompt,
    sanitize_unu_jijeong_text,
)

__all__ = [
    "UnuJijeongResult",
    "compute_unu_jijeong",
    "format_unu_jijeong_for_prompt",
    "sanitize_unu_jijeong_text",
]
