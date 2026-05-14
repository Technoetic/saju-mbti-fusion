"""한방 해몽 — 황제내경 음사발몽 + 동의보감 신문 몽편.

전통 동양 의학의 꿈 해석:
  - 邪氣가 침입한 장부에 따라 꿈 내용이 결정 (黃帝內經)
  - 혼백(魂魄)의 동요와 장부 허실의 신호로 진단 (東醫寶鑑)
"""

from engine.divination.dream_lex.hanbang.eumsabalmong import (
    EUMSA_LABEL,
    EUMSA_ORGAN_DREAMS,
    map_dream_to_organ,
)
from engine.divination.dream_lex.hanbang.donguibogam import (
    DONGUI_LABEL,
    DONGUI_HONBAEK_PATTERNS,
    diagnose_honbaek,
)

__all__ = [
    "EUMSA_LABEL",
    "EUMSA_ORGAN_DREAMS",
    "map_dream_to_organ",
    "DONGUI_LABEL",
    "DONGUI_HONBAEK_PATTERNS",
    "diagnose_honbaek",
]
