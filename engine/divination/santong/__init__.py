"""ADR-120 — 한국 정통 산통점 결정론.

본 모듈은 ADR-002·006·010·112 (yutjeom) 정합 — 결정론 매핑만, LLM 작문 분리.

영역:
  · 산통점 (算筒占) — 8 산가지 × 3회 뽑기 = 8^3 = 512 점괘 변형
  · 본 시스템 단순화: 8 산가지 × 3회 = 512 결정론 매핑
  · 한국 무속 정통 (이능화 1927 조선무속고)

출처 (ADR-010):
  · 이능화(1927) "조선무속고(朝鮮巫俗考)" ISBN 9788936471391
  · 국립민속박물관 디지털 아카이브 산통점 표제
  · 한국학중앙연구원 한국민족문화대백과사전

원칙:
  · 단정 예언 차단 — 길흉 단정 X
  · 한국 정통 단일 학파 (이능화·국립민속박물관)
  · 동일 입력 → 동일 점괘 결정론
"""

from engine.divination.santong.scoring import (
    SantongStick,
    SANTONG_STICKS,
    SantongResult,
    compute_santong_reading,
    format_santong_for_prompt,
)

__all__ = [
    "SantongStick",
    "SANTONG_STICKS",
    "SantongResult",
    "compute_santong_reading",
    "format_santong_for_prompt",
]
