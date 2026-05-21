"""ADR-118 — 신년 토정비결 144괘 결정론.

본 모듈은 ADR-002·006·010 정합 — 결정론 매핑만, LLM 작문 분리.

영역:
  · 토정 이지함(1517-1578) 정통 144괘
  · 상괘 (生年 干支 끝자리 1~8) × 중괘 (生月 1~6) × 하괘 (生日 1~3) = 144괘
  · 각 괘의 흐름 톤 (단정 X)

출처 (ADR-010):
  · 토정 이지함(土亭 李之菡, 1517-1578) "토정비결(土亭秘訣)"
  · 한국학중앙연구원 한국민족문화대백과사전 — 토정비결 표제
  · 국립민속박물관 디지털 아카이브
"""

from engine.divination.tojeong.scoring import (
    TojeongHexagram,
    SIXTY_FOUR_TOJEONG,
    compute_tojeong_for_year,
    hexagram_by_id,
    format_hexagram_for_prompt,
)
from engine.divination.tojeong.sanitize import (
    sanitize_tojeong_verse,
    TOJEONG_FORBIDDEN_WORDS,
    TOJEONG_FLOW_TONE_SUBSTITUTIONS,
)

__all__ = [
    "TojeongHexagram",
    "SIXTY_FOUR_TOJEONG",
    "compute_tojeong_for_year",
    "hexagram_by_id",
    "format_hexagram_for_prompt",
    "sanitize_tojeong_verse",
    "TOJEONG_FORBIDDEN_WORDS",
    "TOJEONG_FLOW_TONE_SUBSTITUTIONS",
]
