"""AI 에이전트 오케스트레이션 — 14 핵심 + 6 보조 = 20개.

문서 §해몽_앱_AI_에이전트_목록.md 명세 기반.

핵심 14:
  A1 text_cleaner            (Schredl/HvDC 자동 추출)
  A2 hvdc_llm                (별도 — dream_lex/hvdc_llm.py)
  A3 bivalent_cards          (표상 양가 카드)
  A4 hanbang_organ           (한방 장부 LLM 보강)
  A5 jung_classifier         (융 원형 LLM 분류)
  A6 IRT 재각본              (clinical/irt.py::generate_rescripted_endings)
  A7 위기 탐지               (safety/crisis_detector.py)
  A8 freud (v2)              (TODO)
  A9 lakoff_topology         ⭐ 차별화 핵심
  A10 cathartic_llm          (감정 아크 미세 분류)
  A11 biomarker              (디지털 바이오마커)
  A12 Hill (v3)              (clara_hill.py + post_hill_step)
  A13 social_unconscious (v3) (TODO — DB 클러스터링)
  A14 Dormio (v3)            (dormio.py)

보조 6:
  B1 rag_gate
  B2 locale_router
  B3 persona_router
  B4 weight_learner
  B5 윤리 가드              (safety/legal_notice.py)
  B6 DreamNet (v4)          (TODO)

orchestrator.interpret_dream_v2 가 모든 에이전트 조율.
"""

from engine.agents.orchestrator import (
    interpret_dream_v2,
    ORCHESTRATOR_LABEL,
)
from engine.agents.persona_router import (
    classify_persona, PERSONAS, PersonaClassification,
)
from engine.agents.locale_router import route_locale, LocaleRouting
from engine.agents.text_cleaner import run_text_cleaner, deterministic_clean
from engine.agents.bivalent_cards import generate_bivalent_cards
from engine.agents.lakoff_topology import extract_topology
from engine.agents.hanbang_organ import run_hanbang_agent
from engine.agents.jung_classifier import classify_archetype
from engine.agents.cathartic_llm import classify_arc_llm
from engine.agents.biomarker import compute_biomarker_signals
from engine.agents.weight_learner import (
    record_feedback,
    get_personalized_weights,
    get_user_feedback_summary,
    reset_user_feedback,
)
from engine.agents.rag_gate import evaluate_rag_compliance
from engine.agents.freud_persona import map_latent_dream, FREUD_PERSONA_LABEL
from engine.agents.social_unconscious import (
    aggregate_social_unconscious, SOCIAL_UNCONSCIOUS_LABEL,
)
from engine.agents.dreamnet_multimodal import (
    BiosignalReport, boost_text_analysis_with_biosignals, DREAMNET_LABEL,
)

__all__ = [
    "interpret_dream_v2",
    "ORCHESTRATOR_LABEL",
    "classify_persona", "PERSONAS", "PersonaClassification",
    "route_locale", "LocaleRouting",
    "run_text_cleaner", "deterministic_clean",
    "generate_bivalent_cards",
    "extract_topology",
    "run_hanbang_agent",
    "classify_archetype",
    "classify_arc_llm",
    "compute_biomarker_signals",
    "record_feedback", "get_personalized_weights",
    "get_user_feedback_summary", "reset_user_feedback",
    "evaluate_rag_compliance",
    "map_latent_dream", "FREUD_PERSONA_LABEL",
    "aggregate_social_unconscious", "SOCIAL_UNCONSCIOUS_LABEL",
    "BiosignalReport", "boost_text_analysis_with_biosignals", "DREAMNET_LABEL",
]
