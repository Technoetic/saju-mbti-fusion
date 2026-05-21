"""ADR-102 회귀 — 외안각 기울기(PFI) + 의료 차단 가드레일 + 쌍꺼풀 시그니처.

본 ADR은 ADR-101 보강. 봉안(鳳眼) 학파 라벨 거부 (ADR-006 정신).

출처 (Phase 1 라이브 검증):
- Park DH (2002) Archives of Craniofacial Surgery — 한국 996명 PFI 8.65°±2.0°
- Jung HB (2020) Archives of Aesthetic Plastic Surgery — N=240 쌍꺼풀 분리

ADR 정합:
- ADR-006 ★ 학파 라벨 거부 (인체계측 용어만)
- ADR-010 학술 출처 라이브 검증
- ADR-015 옵션 B (age=None, has_crease=None 디폴트)
"""

from engine.divination.face.feature_classifier import (
    EYE_CANTHAL_UPSLANT,
    EYE_CANTHAL_NORMAL,
    EYE_CANTHAL_DOWNSLANT,
    classify_eye_canthal_tilt,
    classify_eye_size,
    is_eye_measurement_pathological,
)


# ─────────────────────────────────────────────────────────────
# ① classify_eye_canthal_tilt — PFI 3분류 + 학파 라벨 거부
# ─────────────────────────────────────────────────────────────


def test_canthal_baseline_normal():
    """Park DH baseline 8.65° → 보통 외안각."""
    r = classify_eye_canthal_tilt(8.65)
    assert r is not None
    assert r.tilt_type == EYE_CANTHAL_NORMAL


def test_canthal_upslant_above_10_65():
    """PFI > 10.65° (baseline + 1SD) → 외안각 상행형."""
    r = classify_eye_canthal_tilt(12.0)
    assert r is not None
    assert r.tilt_type == EYE_CANTHAL_UPSLANT


def test_canthal_downslant_below_6_65():
    """PFI < 6.65° (baseline - 1SD) → 외안각 하행형."""
    r = classify_eye_canthal_tilt(5.0)
    assert r is not None
    assert r.tilt_type == EYE_CANTHAL_DOWNSLANT


def test_canthal_label_no_school_terms():
    """★ 봉안(鳳眼)·삼백안·도화안 등 학파 라벨 거부 (ADR-006)."""
    assert "봉안" not in EYE_CANTHAL_UPSLANT
    assert "삼백안" not in EYE_CANTHAL_UPSLANT
    assert "도화안" not in EYE_CANTHAL_UPSLANT
    assert EYE_CANTHAL_UPSLANT == "외안각 상행형"  # 인체계측 용어
    assert EYE_CANTHAL_NORMAL == "보통 외안각"
    assert EYE_CANTHAL_DOWNSLANT == "외안각 하행형"


def test_canthal_disclaimer_adr_006():
    """면책 자동 — 운명 매핑 X + 학파 라벨 거부 명시."""
    r = classify_eye_canthal_tilt(8.65)
    assert r is not None
    assert "운명" in r.disclaimer
    assert "ADR-006" in r.disclaimer
    assert "봉안" in r.disclaimer  # "봉안 인용 X" 명시 필수
    assert "ADR-102" in r.disclaimer


def test_canthal_extreme_returns_none():
    """극단치 → None (의료 진단 영역 차단)."""
    assert classify_eye_canthal_tilt(45.0) is None  # > 30°
    assert classify_eye_canthal_tilt(-45.0) is None  # < -30°


def test_canthal_invalid_input_returns_none():
    """음수·문자열 입력 → None."""
    assert classify_eye_canthal_tilt("abc") is None  # type: ignore[arg-type]
    assert classify_eye_canthal_tilt(10.0, age=-5) is None


def test_canthal_age_optional_default_none():
    """ADR-015 옵션 A — age 디폴트 None 가능."""
    r = classify_eye_canthal_tilt(8.65)
    assert r is not None
    assert r.age is None


# ─────────────────────────────────────────────────────────────
# ② is_eye_measurement_pathological — 의료 차단 가드레일
# ─────────────────────────────────────────────────────────────


def test_pathological_mrd1_below_2():
    """MRD1 < 2mm → 안검하수 의심 (True 반환)."""
    is_path, reason = is_eye_measurement_pathological(mrd1_mm=1.5)
    assert is_path is True
    assert reason is not None
    assert "MRD1" in reason
    assert "안검하수" in reason
    assert "ADR-006" in reason


def test_pathological_pfw_below_18():
    """PFW < 18mm → 선천성 검열협착증 의심."""
    is_path, reason = is_eye_measurement_pathological(pfw_mm=15.0)
    assert is_path is True
    assert reason is not None
    assert "PFW" in reason
    assert "검열협착증" in reason


def test_pathological_pfw_above_32():
    """PFW > 32mm → 극단치 (안검외반 의심)."""
    is_path, reason = is_eye_measurement_pathological(pfw_mm=35.0)
    assert is_path is True
    assert reason is not None
    assert "PFW" in reason


def test_pathological_pfh_below_5():
    """PFH < 5mm → 측정 오류 또는 안검열 폐쇄."""
    is_path, reason = is_eye_measurement_pathological(pfh_mm=3.0)
    assert is_path is True
    assert reason is not None
    assert "PFH" in reason


def test_pathological_normal_range_pass():
    """정상 범위 → (False, None)."""
    is_path, reason = is_eye_measurement_pathological(pfw_mm=27.0, pfh_mm=9.0, mrd1_mm=3.3)
    assert is_path is False
    assert reason is None


def test_pathological_all_none_pass():
    """모두 미지정 → (False, None) — 옵션 안전."""
    is_path, reason = is_eye_measurement_pathological()
    assert is_path is False
    assert reason is None


def test_pathological_mrd1_priority():
    """MRD1 우선 점검 — 다중 위반 시 첫 사유 반환."""
    is_path, reason = is_eye_measurement_pathological(pfw_mm=15.0, mrd1_mm=1.5)
    assert is_path is True
    # MRD1 우선 (안검하수가 검열협착증보다 임상 우선순위 높음)
    assert reason is not None
    assert "MRD1" in reason


# ─────────────────────────────────────────────────────────────
# ③ classify_eye_size has_crease 시그니처 확장 (ADR-102)
# ─────────────────────────────────────────────────────────────


def test_eye_size_has_crease_none_default():
    """has_crease=None 디폴트 (ADR-101 통합 baseline 정합, 역호환)."""
    r = classify_eye_size(27.0, 9.0)  # 미지정
    assert r is not None
    assert r.has_crease is None


def test_eye_size_has_crease_true_propagated():
    """has_crease=True (쌍꺼풀) → 필드 보존."""
    r = classify_eye_size(27.0, 9.9, has_crease=True)
    assert r is not None
    assert r.has_crease is True


def test_eye_size_has_crease_false_propagated():
    """has_crease=False (단안검) → 필드 보존."""
    r = classify_eye_size(27.0, 8.0, has_crease=False)
    assert r is not None
    assert r.has_crease is False


def test_eye_size_has_crease_invalid_returns_none():
    """has_crease 부정합 → None (타입 안정성)."""
    # bool 아닌 값
    assert classify_eye_size(27.0, 9.0, has_crease="yes") is None  # type: ignore[arg-type]
    assert classify_eye_size(27.0, 9.0, has_crease=1) is None  # type: ignore[arg-type]


def test_eye_size_adr_101_regression_compatibility():
    """ADR-101 역호환 — has_crease 추가가 기존 분류 로직 영향 X."""
    r1 = classify_eye_size(27.0, 9.0)
    r2 = classify_eye_size(27.0, 9.0, has_crease=True)
    r3 = classify_eye_size(27.0, 9.0, has_crease=False)
    assert r1 is not None and r2 is not None and r3 is not None
    # PFW 기준 분류 동일
    assert r1.size_type == r2.size_type == r3.size_type
