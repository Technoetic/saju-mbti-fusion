"""engine.safety.audit.model_card — §7.2.10 모델·데이터 카드 회귀 테스트."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 섹션 키 ───────────────────────────

def test_model_card_sections_count():
    from engine.safety.audit.model_card import MODEL_CARD_SECTIONS
    # Mitchell et al. 2019 표 3 — 9개 섹션
    assert len(MODEL_CARD_SECTIONS) == 9


def test_data_card_sections_count():
    from engine.safety.audit.model_card import DATA_CARD_SECTIONS
    # Gebru et al. 2021 — 7개 섹션
    assert len(DATA_CARD_SECTIONS) == 7


# ─────────────────────────── face_reading 모델 카드 ───────────────────────────

def test_get_face_reading_model_card_basic_fields():
    from engine.safety.audit.model_card import get_face_reading_model_card
    c = get_face_reading_model_card()
    assert c.system_id == "face_reading"
    assert c.version
    assert c.published_at  # ISO 형식
    assert isinstance(c.sections, dict)


def test_model_card_has_all_9_sections():
    from engine.safety.audit.model_card import (
        get_face_reading_model_card,
        MODEL_CARD_SECTIONS,
        validate_model_card,
    )
    c = get_face_reading_model_card()
    assert set(c.sections.keys()) == set(MODEL_CARD_SECTIONS)
    assert validate_model_card(c) == []


def test_model_card_lists_5_vertical_engines():
    from engine.safety.audit.model_card import get_face_reading_model_card
    c = get_face_reading_model_card()
    engines = c.sections["model_details"]["engines"]
    assert len(engines) == 5
    for name in ("bone_structure", "ratios", "complexion", "spirit_gaze", "safety"):
        assert name in engines


def test_model_card_intended_use_excludes_high_risk():
    """의료·법률·고용·EU §5(f)가 모두 out_of_scope에 명시되어야 함."""
    from engine.safety.audit.model_card import get_face_reading_model_card
    c = get_face_reading_model_card()
    out = " ".join(c.sections["intended_use"]["out_of_scope"])
    assert "의료" in out
    assert "법률" in out
    assert "고용" in out
    assert "EU AI Act" in out


def test_model_card_ethical_considerations_lists_mitigations():
    """완화 조치에 emotion_disclosure / crisis_detector / pii 명시."""
    from engine.safety.audit.model_card import get_face_reading_model_card
    c = get_face_reading_model_card()
    mits = " ".join(c.sections["ethical_considerations"]["mitigations"])
    assert "emotion_disclosure" in mits
    assert "crisis_detector" in mits
    assert "pii" in mits


def test_model_card_accepts_external_eval_metrics():
    """외부 워커가 회귀 결과를 주입 가능."""
    from engine.safety.audit.model_card import get_face_reading_model_card
    c = get_face_reading_model_card(eval_metrics={
        "regression_tests_passed": 408,
        "golden_set_mean_score": 0.93,
    })
    runtime = c.sections["metrics"]["runtime"]
    assert runtime["regression_tests_passed"] == 408
    quant = c.sections["quantitative_analyses"]
    assert quant["regression_pass_rate"] == 408
    assert quant["golden_set_mean_score"] == 0.93


# ─────────────────────────── face_reading 데이터 카드 ───────────────────────────

def test_data_card_has_all_7_sections():
    from engine.safety.audit.model_card import (
        get_face_reading_data_card,
        DATA_CARD_SECTIONS,
        validate_data_card,
    )
    c = get_face_reading_data_card()
    assert set(c.sections.keys()) == set(DATA_CARD_SECTIONS)
    assert validate_data_card(c) == []


def test_data_card_collection_sources_match_licit():
    """수집 출처가 모두 data_governance.LICIT_SOURCES에 있어야."""
    from engine.safety.audit.model_card import get_face_reading_data_card
    from engine.safety.gdpr.data_governance import LICIT_SOURCES
    c = get_face_reading_data_card()
    for src in c.sections["collection_process"]["sources"]:
        assert src in LICIT_SOURCES, f"{src} not in LICIT_SOURCES"


def test_data_card_excludes_minor_subjects():
    from engine.safety.audit.model_card import get_face_reading_data_card
    c = get_face_reading_data_card()
    assert c.sections["composition"]["minor_subjects"] == "없음 (만 18세 이상만)"


def test_data_card_retention_within_max():
    """retention_max_days가 MAX_RETENTION_DAYS 한도 안인지."""
    from engine.safety.audit.model_card import get_face_reading_data_card
    c = get_face_reading_data_card()
    assert 0 < c.sections["distribution"]["retention_max_days"] <= 36500


# ─────────────────────────── 검증 ───────────────────────────

def test_validate_model_card_catches_missing_section():
    from engine.safety.audit.model_card import ModelCard, validate_model_card
    bad = ModelCard(system_id="X", version="0.0", published_at="2026-05-15", sections={})
    v = validate_model_card(bad)
    assert len(v) == 9  # 9개 섹션 모두 missing


def test_validate_model_card_catches_empty_section():
    from engine.safety.audit.model_card import ModelCard, validate_model_card, MODEL_CARD_SECTIONS
    sections = {k: {"k": "v"} for k in MODEL_CARD_SECTIONS}
    sections["metrics"] = {}  # 빈 섹션
    c = ModelCard(system_id="X", version="0.0", published_at="2026-05-15", sections=sections)
    v = validate_model_card(c)
    assert any("empty_section:metrics" in x for x in v)


# ─────────────────────────── 직렬화 ───────────────────────────

def test_card_to_dict_model_card_json_serializable():
    from engine.safety.audit.model_card import get_face_reading_model_card, card_to_dict
    d = card_to_dict(get_face_reading_model_card())
    # JSON 직렬화 — 예외 없이 성공
    blob = json.dumps(d, ensure_ascii=False)
    assert '"face_reading"' in blob
    assert d["kind"] == "model_card"


def test_card_to_dict_data_card_has_kind():
    from engine.safety.audit.model_card import get_face_reading_data_card, card_to_dict
    d = card_to_dict(get_face_reading_data_card())
    assert d["kind"] == "data_card"
    assert d["dataset_id"] == "face_reading.golden.v1"


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_model_card():
    import engine.safety as safety
    assert hasattr(safety, "ModelCard")
    assert hasattr(safety, "DataCard")
    assert hasattr(safety, "get_face_reading_model_card")
    assert hasattr(safety, "get_face_reading_data_card")
    assert hasattr(safety, "validate_model_card")
    assert hasattr(safety, "validate_data_card")
    assert hasattr(safety, "card_to_dict")
