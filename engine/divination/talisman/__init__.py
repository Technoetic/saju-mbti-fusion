"""ADR-121 — 한국 정통 부적 4 표준 결정론 메타.

본 모듈은 ADR-002·006·010 정합 — 결정론 메타만, 이미지 생성 옵션 분리.

영역:
  · 합격부 (合格符) — 학업·시험 합격 기원 부적
  · 재물부 (財物符) — 재물 안정 기원 부적
  · 연애부 (戀愛符) — 인연·관계 기원 부적
  · 건강부 (健康符) — 건강·치병 기원 부적

출처 (ADR-010):
  · 한국학중앙연구원 한국민족문화대백과사전 — 부적 표제
  · 국립민속박물관 디지털 아카이브 — 부적 4 표준 (조선시대 무속)
  · 한국민속박물관 부적 자료집

원칙 (ADR-006):
  · 부적이 "재물·합격·연애·건강 단정" X — 기원 의식의 결정론 메타
  · "이것을 가지면 반드시" 표현 절대 금지 — 흐름 톤
  · 이미지 생성 옵션은 사용자 결단 (Stable Diffusion·Imagen API 호출 비용)
"""

from engine.divination.talisman.scoring import (
    TalismanType,
    TALISMAN_TYPES,
    TalismanReading,
    talisman_by_key,
    compute_talisman_reading,
    format_talisman_for_prompt,
)

__all__ = [
    "TalismanType",
    "TALISMAN_TYPES",
    "TalismanReading",
    "talisman_by_key",
    "compute_talisman_reading",
    "format_talisman_for_prompt",
]
