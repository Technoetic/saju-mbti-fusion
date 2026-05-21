"""ADR-099 회귀 — 턱 하악각 4분류 결정론 (PMC4738126·PMC11417696·KCI 차인호).

본 ADR은 ADR-064 코 분류 동일 정신.
운명 매핑 X (ADR-006). 의료 진단 영역 차단 (정상 범위 100~150° 밖).
"""

import pytest

from engine.divination.face.feature_classifier import (
    classify_jaw_shape,
    get_jaw_korean_mean,
    JAW_SQUARE,
    JAW_OVAL,
    JAW_POINTED,
    JAW_ROUND,
    JawShapeResult,
)


# ── ① 4 카테고리 라벨 상수 ────────────────────────────────────


def test_jaw_category_labels_exist():
    """4 카테고리 라벨 한국어 명시."""
    assert JAW_SQUARE == "사각형 턱"
    assert JAW_OVAL == "계란형 턱"
    assert JAW_POINTED == "뾰족형 턱"
    assert JAW_ROUND == "둥근형 턱"


# ── ② 경계값 정합 ─────────────────────────────────────────


def test_square_below_124():
    """사각형 < 124° (PMC11417696 사각턱 환자군 124.1±5.67° 정합)."""
    r = classify_jaw_shape(120.0)
    assert r is not None
    assert r.shape_type == JAW_SQUARE


def test_square_at_124_boundary():
    """경계값 124° = 사각형."""
    r = classify_jaw_shape(124.0)
    assert r is not None
    assert r.shape_type == JAW_SQUARE


def test_oval_125_to_132():
    """계란형 125~132° (KCI 차인호 정상교합 128.71±3.87° 정중심)."""
    for angle in [125.0, 128.0, 128.71, 130.0, 132.0]:
        r = classify_jaw_shape(angle)
        assert r is not None
        assert r.shape_type == JAW_OVAL, f"angle={angle} 계란형 기대"


def test_pointed_above_133():
    """뾰족형 >= 133°."""
    for angle in [133.0, 135.0, 140.0]:
        r = classify_jaw_shape(angle)
        assert r is not None
        assert r.shape_type == JAW_POINTED, f"angle={angle} 뾰족형 기대"


# ── ③ 정상 범위 외 차단 (의료 진단 영역 ADR-006) ──────────


def test_below_normal_range_returns_none():
    """100° 미만 = 측정 오류 또는 병리 → None (의료 영역 차단)."""
    assert classify_jaw_shape(95.0) is None
    assert classify_jaw_shape(99.9) is None


def test_above_normal_range_returns_none():
    """150° 초과 = 측정 오류 또는 병리 → None."""
    assert classify_jaw_shape(150.1) is None
    assert classify_jaw_shape(155.0) is None


# ── ④ 입력 타입 검증 ──────────────────────────────────────


def test_invalid_type_returns_none():
    """비숫자 입력 → None."""
    assert classify_jaw_shape("128") is None  # type: ignore
    assert classify_jaw_shape(None) is None  # type: ignore


# ── ⑤ Result dataclass 구조 ──────────────────────────────


def test_result_dataclass_fields():
    """JawShapeResult 6 필드 정합."""
    r = classify_jaw_shape(128.0)
    assert r is not None
    assert isinstance(r, JawShapeResult)
    assert r.shape_type == JAW_OVAL
    assert r.gonial_angle_deg == 128.0
    assert r.gonial_angle_side == "avg"  # default
    assert r.confidence == "HIGH"
    assert isinstance(r.source_urls, tuple)
    assert len(r.source_urls) >= 2  # PMC4738126 + PMC11417696
    assert "PMC4738126" in r.source_urls[0]


def test_side_parameter():
    """side 파라미터 (right·left·avg)."""
    r_right = classify_jaw_shape(128.0, side="right")
    assert r_right is not None
    assert r_right.gonial_angle_side == "right"

    r_left = classify_jaw_shape(128.0, side="left")
    assert r_left is not None
    assert r_left.gonial_angle_side == "left"


def test_invalid_side_defaults_to_avg():
    """잘못된 side → avg fallback."""
    r = classify_jaw_shape(128.0, side="invalid")
    assert r is not None
    assert r.gonial_angle_side == "avg"


# ── ⑥ ADR-006 fate_mapping 차단 검증 ─────────────────────


def test_disclaimer_contains_adr_006():
    """면책 문구에 ADR-006 정신 명시."""
    r = classify_jaw_shape(128.0)
    assert r is not None
    assert "운명" in r.disclaimer
    assert "매핑 X" in r.disclaimer
    assert "ADR-006" in r.disclaimer


def test_disclaimer_blocks_medical():
    """면책 문구에 의료 진단 영역 차단 명시."""
    r = classify_jaw_shape(128.0)
    assert r is not None
    assert "의료 진단 영역 X" in r.disclaimer
    # KBG·SRD5A2·MBTPS1·CDKN2A 유전자 마커 명시
    for marker in ["KBG", "SRD5A2", "MBTPS1", "CDKN2A"]:
        assert marker in r.disclaimer


def test_no_fate_mapping_field():
    """JawShapeResult에 fate_mapping 필드 부재 (ADR-006 정합)."""
    r = classify_jaw_shape(128.0)
    assert r is not None
    assert not hasattr(r, "fate_mapping")
    assert not hasattr(r, "fortune")
    assert not hasattr(r, "destiny")


# ── ⑦ 한국 표본 평균 조회 ────────────────────────────────


def test_korean_normal_mean():
    """KCI 차인호 한국 117명 정상교합 평균."""
    m = get_jaw_korean_mean("normal_korean")
    assert m is not None
    assert m["mean"] == 128.71
    assert m["sd"] == 3.87
    assert m["n"] == 117


def test_korean_patient_3d_cbct():
    """PMC4738126 한국 106명 3D CBCT 환자군 평균."""
    m = get_jaw_korean_mean("patient_3d_cbct")
    assert m is not None
    assert m["right_mean"] == 134.37
    assert m["left_mean"] == 131.54
    assert m["n"] == 106


def test_unknown_sample_returns_none():
    """미등록 표본 → None."""
    assert get_jaw_korean_mean("foreign") is None


# ── ⑧ 출처 URL 라이브 가능성 ─────────────────────────────


def test_source_urls_use_pmc():
    """출처 URL에 PMC ID 명시 (라이브 검증 가능)."""
    r = classify_jaw_shape(128.0)
    assert r is not None
    assert any("ncbi.nlm.nih.gov" in url for url in r.source_urls)
    assert any("PMC4738126" in url or "PMC11417696" in url for url in r.source_urls)


# ── ⑨ 입력 round trip ────────────────────────────────────


def test_angle_rounded_to_2_decimals():
    """gonial_angle_deg 소수 2자리 반올림."""
    r = classify_jaw_shape(128.7126)
    assert r is not None
    assert r.gonial_angle_deg == 128.71
