"""임상 척도 모듈 — 한국 표준 우울·불안·수면 척도.

법적 제약:
  - 본 모듈은 자가 모니터링·의뢰 트리거 도구이며 의료 진단이 아니다.
  - cutoff 초과 시 전문의 안내만 수행, 진단명 단정 금지.
"""

from engine.clinical.ces_d import (
    CES_D_ITEMS_KO,
    score_ces_d,
    CES_D_CUTOFF_ADULT,
    CES_D_CUTOFF_SENIOR,
)
from engine.clinical.bdi_k import BDI_K_ITEMS_KO, score_bdi_k, BDI_K_CUTOFF
from engine.clinical.stai_k import (
    STAI_K_STATE_ITEMS_KO,
    score_stai_k_state,
    STAI_K_STATE_CUTOFF,
)
from engine.clinical.psqi import PSQI_COMPONENTS, score_psqi, PSQI_CUTOFF
from engine.clinical.isi import ISI_ITEMS_KO, score_isi
from engine.clinical.risk_router import assess_clinical_risk

__all__ = [
    "CES_D_ITEMS_KO", "score_ces_d", "CES_D_CUTOFF_ADULT", "CES_D_CUTOFF_SENIOR",
    "BDI_K_ITEMS_KO", "score_bdi_k", "BDI_K_CUTOFF",
    "STAI_K_STATE_ITEMS_KO", "score_stai_k_state", "STAI_K_STATE_CUTOFF",
    "PSQI_COMPONENTS", "score_psqi", "PSQI_CUTOFF",
    "ISI_ITEMS_KO", "score_isi",
    "assess_clinical_risk",
]
