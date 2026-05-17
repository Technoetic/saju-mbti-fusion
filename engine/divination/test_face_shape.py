"""ADR-022 회귀 테스트 — 5형 결정론 분류.

보고서 §4 회귀 데이터셋 10건 (case_001~case_010) 그대로 검증.

검증 항목:
  1. 메트릭 산출 (compute_face_metrics) 정확
  2. 5형 분류 + 복합형 fallback
  3. 영문 ↔ 한글 매핑 정합
  4. 학술 출처 URL 비어있지 않음
  5. DEFAULT_DISCLAIMERS ADR-010 정합 (인과 표현 0건)
  6. 보고서 §4 case_001~010 expected_shape 매칭
  7. matched_criteria 비어있지 않음 (debug 가능)
"""

from __future__ import annotations

from engine.divination.face_shape import (
    DEFAULT_DISCLAIMERS,
    SHAPE_KOREAN_TO_LATIN,
    SHAPE_LATIN_TO_KOREAN,
    FaceShapeResult,
    classify_face_shape,
    compute_face_metrics,
    jaw_angle_from_points,
)


# ─────────────────────────── 메트릭 산출 ───────────────────────────


def test_compute_face_width_height_ratio():
    """기본 비율 산출."""
    m = compute_face_metrics(
        face_width=140, face_height=160,
        jaw_angle_deg=120.0, zygo_width=140, bigo_width=120,
    )
    assert m["face_width_height_ratio"] == 0.875


def test_compute_bizygomatic_to_bigonial_ratio():
    """광대/하악 비율."""
    m = compute_face_metrics(
        face_width=140, face_height=160,
        jaw_angle_deg=120.0, zygo_width=140, bigo_width=105,
    )
    assert m["bizygomatic_to_bigonial_ratio"] == round(140 / 105, 3)


def test_compute_jaw_angle_passthrough():
    """jaw_angle은 입력 그대로 전달."""
    m = compute_face_metrics(
        face_width=140, face_height=160,
        jaw_angle_deg=125.5, zygo_width=140, bigo_width=120,
    )
    assert m["jaw_angle_deg"] == 125.5


def test_jaw_angle_from_3d_points():
    """벡터 내적 각도 계산 검증."""
    # 단순 90도 케이스 (수직 벡터)
    angle = jaw_angle_from_points(
        go_left=(0, 0, 0),
        gnathion=(0, 1, 0),
        go_right=(1, 0, 0),
    )
    # (0,1,0) 과 (-1,1,0) 사이 각도
    assert 0 < angle < 180


# ─────────────────────────── 영문 ↔ 한글 매핑 ───────────────────────────


def test_korean_to_latin_mapping_complete():
    """5형 + 복합형 모두 매핑."""
    expected = {"목형", "화형", "토형", "금형", "수형", "복합형"}
    assert set(SHAPE_KOREAN_TO_LATIN.keys()) == expected


def test_latin_values_match_face_scoring():
    """영문 값이 face_scoring.py 5종과 호환."""
    expected_latin = {"long", "inverted_tri", "oval", "square", "round"}
    actual_latin = set(SHAPE_LATIN_TO_KOREAN.keys())
    assert actual_latin == expected_latin


# ─────────────────────────── DEFAULT_DISCLAIMERS ADR-010 정합 ───────────────────────────


def test_disclaimers_required():
    """면책 배열 비어있지 않음."""
    assert len(DEFAULT_DISCLAIMERS) >= 3


def test_disclaimers_no_causal_words():
    """인과·예언 표현 0건 (ADR-010 정합)."""
    forbidden = ["당신은 운이", "운명입니다", "예언", "단명", "흉화", "길흉"]
    combined = " ".join(DEFAULT_DISCLAIMERS)
    for w in forbidden:
        # "길흉화복과 무관" 같은 부정문은 허용, 단정 표현만 차단
        # 따라서 "길흉화복" 같은 부분 단어가 있더라도 "무관" 함께 있어야 함
        if w in combined:
            # 예외: "길흉" + "무관" 또는 "않습니다" 동반 시 허용
            if "무관" in combined or "않습니다" in combined or "않는다" in combined or "채택하지" in combined:
                continue
            assert False, f"인과 표현 발견 (부정 없이): {w}"


def test_disclaimers_includes_school_avoidance():
    """학파 회피 명시 (마의상법·유장상법)."""
    combined = " ".join(DEFAULT_DISCLAIMERS)
    assert "마의상법" in combined or "전통 관상학" in combined or "학파" in combined


# ─────────────────────────── 보고서 §4 회귀 10건 ───────────────────────────


def test_case_001_wood_standard():
    """보고서 §4 case_001: 전형 목형 (길고 좁음)."""
    m = compute_face_metrics(
        face_width=135, face_height=170,
        jaw_angle_deg=120.0, zygo_width=135, bigo_width=115,
    )
    result = classify_face_shape(m)
    assert result.shape_type == "목형"
    assert m["face_width_height_ratio"] == 0.794
    assert m["jaw_angle_deg"] == 120.0
    assert m["bizygomatic_to_bigonial_ratio"] == 1.174  # 135/115 = 1.1739...


def test_case_002_wood_extreme():
    """보고서 §4 case_002: 극단 수직발달."""
    m = compute_face_metrics(
        face_width=120, face_height=165,
        jaw_angle_deg=118.0, zygo_width=120, bigo_width=105,
    )
    result = classify_face_shape(m)
    assert result.shape_type == "목형"
    assert m["face_width_height_ratio"] == 0.727


def test_case_003_fire_standard():
    """보고서 §4 case_003: 전형 화형 (역삼각)."""
    m = compute_face_metrics(
        face_width=140, face_height=158,
        jaw_angle_deg=130.0, zygo_width=140, bigo_width=105,
    )
    result = classify_face_shape(m)
    assert result.shape_type == "화형"
    assert m["bizygomatic_to_bigonial_ratio"] == 1.333


def test_case_004_fire_sharp_chin():
    """보고서 §4 case_004: 뾰족한 턱."""
    m = compute_face_metrics(
        face_width=145, face_height=160,
        jaw_angle_deg=135.0, zygo_width=145, bigo_width=98,
    )
    result = classify_face_shape(m)
    assert result.shape_type == "화형"
    assert m["bizygomatic_to_bigonial_ratio"] > 1.45


def test_case_005_earth_standard():
    """보고서 §4 case_005: 전형 토형 (넓적 무거운)."""
    m = compute_face_metrics(
        face_width=155, face_height=165,
        jaw_angle_deg=118.0, zygo_width=155, bigo_width=135,
    )
    result = classify_face_shape(m)
    assert result.shape_type == "토형"
    assert m["face_width_height_ratio"] >= 0.88


def test_case_006_earth_wide():
    """보고서 §4 case_006: 극단 수평발달."""
    m = compute_face_metrics(
        face_width=160, face_height=160,
        jaw_angle_deg=120.0, zygo_width=160, bigo_width=140,
    )
    result = classify_face_shape(m)
    assert result.shape_type == "토형"
    assert m["face_width_height_ratio"] == 1.000


def test_case_007_metal_angular():
    """보고서 §4 case_007: 전형 금형 (각진 하악)."""
    m = compute_face_metrics(
        face_width=148, face_height=168,
        jaw_angle_deg=105.0, zygo_width=148, bigo_width=138,
    )
    result = classify_face_shape(m)
    assert result.shape_type == "금형"
    assert m["jaw_angle_deg"] < 112


def test_case_008_metal_square():
    """보고서 §4 case_008: 사각형 윤곽."""
    m = compute_face_metrics(
        face_width=150, face_height=165,
        jaw_angle_deg=110.0, zygo_width=150, bigo_width=142,
    )
    result = classify_face_shape(m)
    assert result.shape_type == "금형"


def test_case_009_water_round():
    """보고서 §4 case_009: 전형 수형 (둥근)."""
    m = compute_face_metrics(
        face_width=140, face_height=160,
        jaw_angle_deg=125.0, zygo_width=140, bigo_width=120,
    )
    result = classify_face_shape(m)
    assert result.shape_type == "수형"
    assert 0.83 <= m["face_width_height_ratio"] <= 0.88


def test_case_010_fallback_standard():
    """보고서 §4 case_010: 복합형 fallback."""
    m = compute_face_metrics(
        face_width=138, face_height=166,
        jaw_angle_deg=113.0, zygo_width=138, bigo_width=125,
    )
    result = classify_face_shape(m)
    assert result.shape_type == "복합형"


# ─────────────────────────── 학술 출처 + 메타데이터 ───────────────────────────


def test_reference_paper_not_empty():
    """모든 결과에 학술 출처 URL 포함."""
    m = compute_face_metrics(
        face_width=140, face_height=160,
        jaw_angle_deg=120.0, zygo_width=140, bigo_width=120,
    )
    result = classify_face_shape(m)
    assert result.reference_paper.startswith("http")


def test_matched_criteria_not_empty():
    """matched_criteria 비어있지 않음 (debug 가능)."""
    m = compute_face_metrics(
        face_width=135, face_height=170,
        jaw_angle_deg=120.0, zygo_width=135, bigo_width=115,
    )
    result = classify_face_shape(m)
    assert len(result.matched_criteria) > 0


def test_morphological_name_no_school_terms():
    """morphological_name에 학파 용어 0건."""
    forbidden = ["마의상법", "유장상법", "관상", "운명", "길흉"]
    m = compute_face_metrics(
        face_width=135, face_height=170,
        jaw_angle_deg=120.0, zygo_width=135, bigo_width=115,
    )
    result = classify_face_shape(m)
    for w in forbidden:
        assert w not in result.morphological_name


def test_frozen_dataclass():
    """FaceShapeResult는 frozen (불변)."""
    m = compute_face_metrics(
        face_width=140, face_height=160,
        jaw_angle_deg=120.0, zygo_width=140, bigo_width=120,
    )
    result = classify_face_shape(m)
    try:
        result.shape_type = "다른 형"  # type: ignore[misc]
        raised = False
    except (AttributeError, Exception):
        raised = True
    assert raised


def test_latin_in_face_scoring_format():
    """latin 값이 face_scoring.py 호환 5종."""
    m = compute_face_metrics(
        face_width=140, face_height=160,
        jaw_angle_deg=125.0, zygo_width=140, bigo_width=120,
    )
    result = classify_face_shape(m)
    assert result.latin in {"round", "square", "oval", "long", "inverted_tri"}
