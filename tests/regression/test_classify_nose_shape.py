"""ADR-064 회귀 — 코 비지수 결정론 분류 (Phase 2).

출처: PMC11431719 Lee & Park (2024) 한국 20대 100명 CBCT
임계값: NI < 70 (Leptorrhine), 70 ≤ NI ≤ 85 (Mesorrhine), NI > 85 (Platyrrhine)
"""

import pytest

from engine.divination.face.feature_classifier import (
    NOSE_LEPTORRHINE,
    NOSE_MESORRHINE,
    NOSE_PLATYRRHINE,
    NoseShapeResult,
    classify_nose_shape,
    get_nose_korean_20s_mean,
)


def test_korean_male_average_is_mesorrhine():
    """한국 20대 남성 평균 (39.33/51.91 = 75.77) → 보통 코 (Mesorrhine)."""
    result = classify_nose_shape(39.33, 51.91)
    assert result is not None
    assert result.shape_type == NOSE_MESORRHINE
    assert 70.0 <= result.nasal_index <= 85.0


def test_korean_female_average_is_mesorrhine():
    """한국 20대 여성 평균 (36.70/47.74 = 76.87) → 보통 코 (Mesorrhine)."""
    result = classify_nose_shape(36.70, 47.74)
    assert result is not None
    assert result.shape_type == NOSE_MESORRHINE


def test_narrow_nose_leptorrhine():
    """좁은 코 (NI < 70)."""
    # 30mm 너비 + 50mm 길이 = 60 → Leptorrhine
    result = classify_nose_shape(30.0, 50.0)
    assert result is not None
    assert result.shape_type == NOSE_LEPTORRHINE
    assert result.nasal_index == 60.0


def test_wide_nose_platyrrhine():
    """넓은 코 (NI > 85)."""
    # 45mm 너비 + 48mm 길이 = 93.75 → Platyrrhine
    result = classify_nose_shape(45.0, 48.0)
    assert result is not None
    assert result.shape_type == NOSE_PLATYRRHINE
    assert result.nasal_index == 93.75


def test_boundary_leptorrhine_mesorrhine():
    """경계값 NI = 70 → Mesorrhine (≥ 70 포함)."""
    # 35.0/50.0 = 70.0 정확
    result = classify_nose_shape(35.0, 50.0)
    assert result is not None
    assert result.shape_type == NOSE_MESORRHINE


def test_boundary_mesorrhine_platyrrhine():
    """경계값 NI = 85 → Mesorrhine (≤ 85 포함)."""
    # 42.5/50.0 = 85.0 정확
    result = classify_nose_shape(42.5, 50.0)
    assert result is not None
    assert result.shape_type == NOSE_MESORRHINE


def test_invalid_inputs():
    """음수·0·None·문자열 거부."""
    assert classify_nose_shape(0, 50.0) is None
    assert classify_nose_shape(40.0, 0) is None
    assert classify_nose_shape(-10.0, 50.0) is None
    assert classify_nose_shape("40", 50.0) is None  # type: ignore[arg-type]


def test_source_url_pmc():
    """모든 결과에 PMC11431719 URL 명시."""
    result = classify_nose_shape(40.0, 50.0)
    assert result is not None
    assert "pmc.ncbi.nlm.nih.gov" in result.source_url
    assert "PMC11431719" in result.source_url


def test_disclaimer_adr_006_compliance():
    """면책에 ADR-006 정신 명시 (운명·관운 매핑 X)."""
    result = classify_nose_shape(40.0, 50.0)
    assert result is not None
    assert "운명" in result.disclaimer
    assert "관운" in result.disclaimer or "매핑 X" in result.disclaimer


def test_disclaimer_sasang_excluded():
    """면책에 사상체질 인용 X 명시 (ADR-006 강화)."""
    result = classify_nose_shape(40.0, 50.0)
    assert result is not None
    assert "사상체질" in result.disclaimer
    assert "X" in result.disclaimer


def test_dataclass_immutable():
    """NoseShapeResult frozen dataclass."""
    result = classify_nose_shape(40.0, 50.0)
    assert result is not None
    with pytest.raises(Exception):
        result.shape_type = "변경"  # type: ignore[misc]


def test_korean_20s_male_metadata():
    """한국 20대 남성 평균 데이터 조회."""
    data = get_nose_korean_20s_mean("male")
    assert data is not None
    assert data["nasal_width_mm"] == 39.33
    assert data["nasal_width_std"] == 2.43
    assert data["nasal_height_mm"] == 51.91
    assert data["sample_size"] == 50


def test_korean_20s_female_metadata():
    """한국 20대 여성 평균 데이터."""
    data = get_nose_korean_20s_mean("female")
    assert data is not None
    assert data["nasal_width_mm"] == 36.70
    assert data["sample_size"] == 50


def test_korean_20s_invalid_sex():
    """잘못된 sex 입력 → None."""
    assert get_nose_korean_20s_mean("other") is None
    assert get_nose_korean_20s_mean("") is None


def test_confidence_high_default():
    """기본 confidence HIGH."""
    result = classify_nose_shape(40.0, 50.0)
    assert result is not None
    assert result.confidence == "HIGH"


def test_confidence_medium_explicit():
    """confidence MEDIUM 명시 가능."""
    result = classify_nose_shape(40.0, 50.0, confidence="MEDIUM")
    assert result is not None
    assert result.confidence == "MEDIUM"


def test_nasal_index_calculation():
    """비지수 계산 정확도 (소수 2자리 반올림)."""
    # 40/50 = 80.0
    result = classify_nose_shape(40.0, 50.0)
    assert result is not None
    assert result.nasal_index == 80.0

    # 39.33/51.91 = 75.7657... → 75.77
    result = classify_nose_shape(39.33, 51.91)
    assert result is not None
    assert result.nasal_index == 75.77
