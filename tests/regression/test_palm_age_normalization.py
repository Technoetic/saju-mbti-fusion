"""ADR-104 회귀 — 손금 운명선·수성선 연령 정규화.

출처 (Phase 1 라이브 검증):
- Park JS 2010 KCI synapse (한국 5,196명) — 운명선 회귀 R²=0.74
- PCNN 영상 처리 논문 — 수성선 픽셀 갭 R²=0.81

ADR 정합:
- ADR-006: fate_mapping·marriage_outcome 부재 유지
- ADR-010: Park JS·PCNN 라이브 검증
- ADR-015: age=None 디폴트 (역호환) + age 입력 시 보정
- ADR-066: 4 보조선 baseline 임계값 정합
- ADR-100: 의료 차단 정합
"""

from engine.divination.palm.knowledge import (
    FATE_LINE_LINEARITY_THRESHOLD,
    FATE_LINE_STRAIGHT,
    FATE_LINE_CURVED,
    FATE_LINE_ABSENT,
    MERCURY_LINE_CONTINUOUS,
    MERCURY_LINE_FRAGMENTED,
    classify_fate_line,
    classify_mercury_line,
)


# ─────────────────────────────────────────────────────────────
# ① classify_fate_line — age 옵션 (ADR-104)
# ─────────────────────────────────────────────────────────────


def test_fate_age_none_baseline_adr_066_compatible():
    """age=None → 0.85 baseline (ADR-066 역호환)."""
    r = classify_fate_line(0.85)
    assert r is not None
    assert r.shape_type == FATE_LINE_STRAIGHT
    assert FATE_LINE_LINEARITY_THRESHOLD == 0.85


def test_fate_age_20_park_js_baseline():
    """age=20 (Park JS 2010 baseline) → threshold 0.88 - 0.05 - 0.02 = 0.81."""
    # linearity 0.81 → boundary (>= 0.81)
    r = classify_fate_line(0.81, age=20)
    assert r is not None
    assert r.shape_type == FATE_LINE_STRAIGHT


def test_fate_age_40_threshold_lowered():
    """age=40 → threshold ≈ 0.70 (float 0.7000000000000001).

    0.71 >= 0.70 → 곧은, 0.69 < 0.70 → 굽은.
    부동소수점 정밀도상 0.70 정확 비교는 회피.
    """
    r = classify_fate_line(0.71, age=40)
    assert r is not None
    assert r.shape_type == FATE_LINE_STRAIGHT
    r2 = classify_fate_line(0.69, age=40)
    assert r2 is not None
    assert r2.shape_type == FATE_LINE_CURVED


def test_fate_age_60_significant_correction():
    """age=60 → threshold ~0.55 → 노화 보정 효과 큼."""
    r = classify_fate_line(0.60, age=60)
    assert r is not None
    # 0.88 - 0.15 - 0.18 = 0.55 → 0.60 >= 0.55 → 곧은
    assert r.shape_type == FATE_LINE_STRAIGHT


def test_fate_age_invalid_returns_none():
    """age 부정합 → None."""
    assert classify_fate_line(0.85, age=-1) is None
    assert classify_fate_line(0.85, age=130) is None


def test_fate_linearity_none_age_absent():
    """linearity=None → 검출 실패 (age 무관)."""
    r = classify_fate_line(None)
    assert r is not None
    assert r.shape_type == FATE_LINE_ABSENT
    r2 = classify_fate_line(None, age=50)
    assert r2 is not None
    assert r2.shape_type == FATE_LINE_ABSENT


def test_fate_no_fate_mapping_in_result():
    """★ ADR-006 — fate_mapping 필드 부재 (운명 단정 차단)."""
    r = classify_fate_line(0.85, age=40)
    assert r is not None
    # FateLineResult dataclass에 fate_mapping 필드 부재 검증
    assert not hasattr(r, "fate_mapping")
    assert not hasattr(r, "destiny_outcome")


# ─────────────────────────────────────────────────────────────
# ② classify_mercury_line — age 옵션 (ADR-104)
# ─────────────────────────────────────────────────────────────


def test_mercury_age_none_baseline():
    """age=None → max_interruptions=1 (ADR-066 역호환)."""
    r = classify_mercury_line(0.85, 1)
    assert r is not None
    assert r.shape_type == MERCURY_LINE_CONTINUOUS


def test_mercury_age_20_baseline():
    """age=20 → 10px / 10 = 1 (baseline 정합)."""
    r = classify_mercury_line(0.85, 1, age=20)
    assert r is not None
    assert r.shape_type == MERCURY_LINE_CONTINUOUS


def test_mercury_age_40_increased_tolerance():
    """age=40 → 10 + 0.45×20 = 19px → 약 2 단절 허용."""
    r = classify_mercury_line(0.85, 2, age=40)
    assert r is not None
    assert r.shape_type == MERCURY_LINE_CONTINUOUS  # 노화 잔주름 보정


def test_mercury_age_60_more_tolerance():
    """age=60 → 10 + 0.45×40 = 28px → 약 3 단절 허용."""
    r = classify_mercury_line(0.85, 3, age=60)
    assert r is not None
    assert r.shape_type == MERCURY_LINE_CONTINUOUS


def test_mercury_age_none_strict_baseline():
    """age=None + 2 단절 → fragmented (ADR-066 baseline 정합)."""
    r = classify_mercury_line(0.85, 2)
    assert r is not None
    assert r.shape_type == MERCURY_LINE_FRAGMENTED


def test_mercury_age_invalid_returns_none():
    """age 부정합 → None."""
    assert classify_mercury_line(0.85, 1, age=-5) is None
    assert classify_mercury_line(0.85, 1, age=130) is None


def test_mercury_no_wealth_mapping_in_result():
    """★ ADR-006 — wealth_mapping 필드 부재 (재물 단정 차단)."""
    r = classify_mercury_line(0.85, 1, age=40)
    assert r is not None
    assert not hasattr(r, "wealth_mapping")
    assert not hasattr(r, "financial_destiny")


# ─────────────────────────────────────────────────────────────
# ③ ADR-066 역호환 회귀 (기존 호출 패턴 영향 없음)
# ─────────────────────────────────────────────────────────────


def test_fate_legacy_signature_compatibility():
    """기존 코드가 age 인자 없이 호출해도 동작 (역호환)."""
    r1 = classify_fate_line(0.85)
    r2 = classify_fate_line(0.85, None)
    assert r1 is not None and r2 is not None
    assert r1.shape_type == r2.shape_type


def test_mercury_legacy_signature_compatibility():
    """기존 코드가 age 인자 없이 호출해도 동작 (역호환)."""
    r1 = classify_mercury_line(0.85, 1)
    r2 = classify_mercury_line(0.85, 1, None)
    assert r1 is not None and r2 is not None
    assert r1.shape_type == r2.shape_type


# ─────────────────────────────────────────────────────────────
# ④ ADR-010 사실성 분리 — 면책 자동 검증
# ─────────────────────────────────────────────────────────────


def test_fate_disclaimer_no_destiny_mapping():
    """운명 매핑 차단 명시."""
    r = classify_fate_line(0.85, age=40)
    assert r is not None
    assert "운명" in r.disclaimer


def test_mercury_disclaimer_no_destiny_mapping():
    """재물·운명 매핑 차단 명시."""
    r = classify_mercury_line(0.85, 1, age=40)
    assert r is not None
    assert "운명" in r.disclaimer
