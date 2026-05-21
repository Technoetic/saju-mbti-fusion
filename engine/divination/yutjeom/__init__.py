"""ADR-112 — 한국 정통 윷점 64괘 결정론 모듈.

본 모듈은 ADR-002·006·010 정합. 한국 민속학 정통 (국립민속박물관 +
이능화 1927 조선무속고). 78장 카드 점복 시스템과 직교.

영역:
  · 윷점 64괘 (4^3 = 64) 결정론 매핑
  · 도·개·걸·윷 4사위 × 3회 조합
  · 국립민속박물관 PS0100200100109517400000 정통

면책:
  · 의료·법률·금융 단독 근거 X
  · ADR-006 자문 거절 정신
"""

from engine.divination.yutjeom.scoring import (
    YutSide,
    YutHexagram,
    YUT_SIDES,
    SIXTY_FOUR_HEXAGRAMS,
    compute_yut_hexagram,
    hexagram_by_id,
    format_hexagram_for_prompt,
)

__all__ = [
    "YutSide",
    "YutHexagram",
    "YUT_SIDES",
    "SIXTY_FOUR_HEXAGRAMS",
    "compute_yut_hexagram",
    "hexagram_by_id",
    "format_hexagram_for_prompt",
]
