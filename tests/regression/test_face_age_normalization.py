"""ADR-101 회귀 — 안면 인체계측 연령별 정규화 (눈 PFW/PFH/MRD1 + 코 age 보정).

본 ADR은 ADR-064(코)·ADR-099(턱) 동일 정신.
운명 매핑 X (ADR-006). 의료 진단 영역 차단.
ADR-015 옵션 B: age=None 디폴트 + age 입력 시 보정.

출처 (Phase 1 라이브 검증 100%):
- KoreaMed 2119636 (Song 1999, n=498) — 한국 20대 PFW 27.0±1.8 mm
- PMC6786987 (2019, n=7569) — KDC+Ansan-Ansung 연령별 PFW/PFH, R²=0.807
- PMC6976759 (2020, n=320 EEA) — 회귀 R²=0.807
- Synapse KoreaMed 1098729 — 한국 380안 MRD1 3.23/3.33/2.42 mm, R²=0.850
- Kwon et al. 3D 사진측량 (보고서 §4 Table 3) — 코 NI 75.5→81.7, R²=0.720
- PMC9191628 — 한국 235명 CBCT, 하악각 age-invariant R²=0.0
"""

import pytest

from engine.divination.face.feature_classifier import (
    EYE_SMALL,
    EYE_MEDIUM,
    EYE_LARGE,
    NOSE_MESORRHINE,
    NOSE_PLATYRRHINE,
    classify_eye_size,
    classify_nose_shape,
    mrd1_normalize,
)


# ─────────────────────────────────────────────────────────────
# ① classify_eye_size — PFW 분류 + age 옵션 디폴트
# ─────────────────────────────────────────────────────────────


def test_eye_baseline_20s_medium():
    """한국 20대 baseline PFW 27.0 → 보통 눈 (KoreaMed 2119636)."""
    r = classify_eye_size(27.0, 9.0)
    assert r is not None
    assert r.size_type == EYE_MEDIUM
    assert r.pfw_mm == 27.0
    assert r.age is None
    assert r.pfw_age_corrected is None  # age=None → 보정 X


def test_eye_small_below_25_2():
    """PFW < 25.2 (baseline-1SD) → 작은 눈."""
    r = classify_eye_size(24.0, 8.0)
    assert r is not None
    assert r.size_type == EYE_SMALL


def test_eye_large_above_28_8():
    """PFW > 28.8 (baseline+1SD) → 큰 눈."""
    r = classify_eye_size(29.5, 10.0)
    assert r is not None
    assert r.size_type == EYE_LARGE


def test_eye_age_50_pfh_correction():
    """50대 사용자 PFH 8.4 → age=50 보정 후 baseline 9.0 복원 (PMC6786987)."""
    r = classify_eye_size(27.0, 8.4, age=50)
    assert r is not None
    assert r.age == 50
    # age 50 - 40 = 10년 × 0.06 mm/yr = 0.6 mm 가산 → 9.0
    assert r.pfh_age_corrected == pytest.approx(9.0, abs=0.01)


def test_eye_age_below_40_no_correction():
    """age < 40 → PFH 보정 0 (baseline 정합)."""
    r = classify_eye_size(27.0, 9.0, age=30)
    assert r is not None
    assert r.pfh_age_corrected == pytest.approx(9.0, abs=0.01)


def test_eye_invalid_input_returns_none():
    """음수·0 입력 → None (ADR-099 정합)."""
    assert classify_eye_size(0, 9.0) is None
    assert classify_eye_size(27.0, -1) is None
    assert classify_eye_size(27.0, 9.0, age=-5) is None
    assert classify_eye_size(27.0, 9.0, age=130) is None


def test_eye_result_dataclass_frozen():
    """EyeSizeResult frozen — 결정론 보장."""
    r = classify_eye_size(27.0, 9.0)
    assert r is not None
    with pytest.raises(Exception):
        r.size_type = "변조"  # type: ignore


def test_eye_disclaimer_adr_006():
    """면책 자동 — 운명 매핑 X 명시 (ADR-006)."""
    r = classify_eye_size(27.0, 9.0)
    assert r is not None
    assert "운명" in r.disclaimer
    assert "ADR-006" in r.disclaimer
    assert "ADR-101" in r.disclaimer


# ─────────────────────────────────────────────────────────────
# ② mrd1_normalize — 계단형 비선형 보정
# ─────────────────────────────────────────────────────────────


def test_mrd1_baseline_age_none_pass_through():
    """age=None → 보정 0 (ADR-015 옵션 A 디폴트)."""
    assert mrd1_normalize(3.33) == pytest.approx(3.33, abs=0.001)


def test_mrd1_age_40_no_correction():
    """20-40세 baseline → 보정 0 (Synapse KoreaMed 1098729: 3.23 mm)."""
    assert mrd1_normalize(3.23, age=40) == pytest.approx(3.23, abs=0.001)


def test_mrd1_age_50_no_correction():
    """40-60세 정체기 → 보정 0 (3.33 mm 그대로)."""
    assert mrd1_normalize(3.33, age=50) == pytest.approx(3.33, abs=0.001)


def test_mrd1_age_60_full_correction():
    """60+세 → +0.90 mm 가산 (노인성 안검하수 보상, 2.42→3.32 mm baseline 복원)."""
    assert mrd1_normalize(2.42, age=65) == pytest.approx(3.32, abs=0.01)


def test_mrd1_age_57_linear_interpolation():
    """55-60 선형 보간 (age=57 → 2/5 × 0.90 = +0.36)."""
    result = mrd1_normalize(3.0, age=57)
    assert result == pytest.approx(3.36, abs=0.01)


def test_mrd1_age_55_boundary():
    """age=55 → 보간 시작점 (0 가산)."""
    assert mrd1_normalize(3.0, age=55) == pytest.approx(3.0, abs=0.001)


def test_mrd1_age_60_boundary():
    """age=60 → 풀 보정 (+0.90)."""
    assert mrd1_normalize(2.42, age=60) == pytest.approx(3.32, abs=0.01)


# ─────────────────────────────────────────────────────────────
# ③ classify_nose_shape — age 옵션 추가 (ADR-064 + ADR-101)
# ─────────────────────────────────────────────────────────────


def test_nose_age_none_baseline_adr_064_compatible():
    """ADR-064 정합 — age=None이면 NI 그대로 분류 (역호환)."""
    r = classify_nose_shape(38.0, 50.0)  # NI=76
    assert r is not None
    assert r.shape_type == NOSE_MESORRHINE
    assert r.nasal_index == 76.0


def test_nose_age_25_baseline_no_correction():
    """age=25 (baseline) → 보정 0 (ADR-101 baseline)."""
    r = classify_nose_shape(38.0, 50.0, age=25)
    assert r is not None
    assert r.nasal_index == 76.0  # 보정 없음
    assert r.shape_type == NOSE_MESORRHINE


def test_nose_age_50_quadratic_correction():
    """age=50 → 2차 함수 보정 (NI 90 → 90 - 0.0035×625 = 87.81).

    원본 NI 90 → 보정 후 87.81 → 여전히 Platyrrhine (>85)
    Kwon et al. R²=0.720 회귀식 검증.
    """
    r = classify_nose_shape(45.0, 50.0, age=50)  # NI_obs=90
    assert r is not None
    # 90 - 0.0035 × (50-25)^2 = 90 - 2.1875 = 87.8125
    assert r.nasal_index == pytest.approx(87.81, abs=0.05)
    assert r.shape_type == NOSE_PLATYRRHINE  # 여전히 >85


def test_nose_age_60_significant_correction():
    """age=60 → 2차 함수 큰 보정 (NI 86 → 86 - 4.2875 = 81.7).

    보고서 §4 Table 3: 60대+ NI 81.7 정합 검증.
    """
    r = classify_nose_shape(42.0, 48.84, age=60)  # NI_obs~86
    assert r is not None
    # NI_obs ≈ 85.99
    # 보정 = 0.0035 × (60-25)^2 = 0.0035 × 1225 = 4.2875
    # NI_norm ≈ 81.7 → Mesorrhine (≤85)
    assert r.shape_type == NOSE_MESORRHINE


def test_nose_age_below_baseline_no_correction():
    """age < 25 → 보정 0 (baseline)."""
    r1 = classify_nose_shape(38.0, 50.0, age=20)
    r2 = classify_nose_shape(38.0, 50.0, age=25)
    assert r1 is not None and r2 is not None
    assert r1.nasal_index == r2.nasal_index


def test_nose_invalid_age_returns_none():
    """age 부정합 → None (의료 진단 영역 차단)."""
    assert classify_nose_shape(38.0, 50.0, age=-1) is None
    assert classify_nose_shape(38.0, 50.0, age=130) is None


def test_nose_age_optional_default_none_adr_015():
    """ADR-015 옵션 A 디폴트 — age 미지정 호출 가능 (역호환)."""
    r = classify_nose_shape(38.0, 50.0)  # age 미지정
    assert r is not None


# ─────────────────────────────────────────────────────────────
# ④ ADR-006 면책 자동 검증 (사용자 출력 의무)
# ─────────────────────────────────────────────────────────────


def test_nose_disclaimer_no_fate_mapping():
    """코 결과 면책 — 운명·관운 매핑 차단."""
    r = classify_nose_shape(38.0, 50.0, age=50)
    assert r is not None
    assert "운명" in r.disclaimer
    assert "ADR-006" in r.disclaimer


def test_eye_disclaimer_no_medical_diagnosis():
    """눈 결과 면책 — 안검하수 등 의료 진단 차단."""
    r = classify_eye_size(27.0, 9.0, age=60)
    assert r is not None
    assert "의료 진단" in r.disclaimer
    assert "안검하수" in r.disclaimer
