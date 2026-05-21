"""ADR-119 — 한국 12지신 띠별 운세 + 12×12 띠 궁합 매트릭스.

본 모듈은 ADR-002·006·010 정합 — 결정론 매핑만, LLM 작문 분리.

영역:
  · 12지신 (子丑寅卯辰巳午未申酉戌亥) 메타 (동물·오행·계절·시각)
  · 12×12 = 144 띠 궁합 매트릭스 (삼합·육해·원진살 정통)
  · 매해 12지 띠 운세 (점치는 해 干支 × 본인 띠 매트릭스)

출처 (ADR-010):
  · 한국학중앙연구원 한국민족문화대백과사전 — 12지신 표제
  · 정통 12지 궁합 (삼합三合·육합六合·육해六害·원진살元辰煞)
"""

from engine.divination.zodiac_ko.scoring import (
    ZodiacAnimal,
    ZODIAC_ANIMALS,
    ZodiacCompatibility,
    animal_by_year,
    animal_by_key,
    compute_animal_compatibility,
    compute_year_fortune,
    format_animal_for_prompt,
)

__all__ = [
    "ZodiacAnimal",
    "ZODIAC_ANIMALS",
    "ZodiacCompatibility",
    "animal_by_year",
    "animal_by_key",
    "compute_animal_compatibility",
    "compute_year_fortune",
    "format_animal_for_prompt",
]
