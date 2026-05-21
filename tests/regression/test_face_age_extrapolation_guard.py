"""ADR-110 회귀 — 80세 이상 외삽 차단 + Bae SS 2023 KCI 메타 보강.

영역:
  · age > 79 시 79세 baseline cap (Kwon et al. 2021 표본 상한)
  · 79세까지는 회귀 식 정상 동작
  · Bae SS 2023 KCI 한국 20대 NI 평균 조회
  · ADR-006 면책 자동 포함

출처:
  · Kwon SH et al. (2021) PMID 33911812 — 한국 여성 192명 (20-79세 3분할)
  · Bae SS et al. (2023) JKDHS 23(3) KCI — 한국 20대 100명 NI
"""

from engine.divination.face.feature_classifier import (
    classify_nose_shape,
    get_nose_korean_20s_ni_mean,
)


# ─────────────────────────── ADR-110 80세 외삽 차단 ───────────────────────────

def test_age_79_normal_correction():
    """79세는 회귀 식 정상 동작 (표본 상한)."""
    # NI_obs = 90 (Platyrrhine), age 79: 보정 = 0.0035 × (79-25)² = 10.206
    # NI_eff = 90 - 10.206 = 79.794 → Mesorrhine
    r = classify_nose_shape(45.0, 50.0, age=79)
    assert r is not None
    # 90 - 10.206 ≈ 79.79
    assert 79.5 < r.nasal_index < 80.0


def test_age_80_capped_at_79():
    """80세는 79세 cap 적용 (외삽 차단)."""
    r79 = classify_nose_shape(45.0, 50.0, age=79)
    r80 = classify_nose_shape(45.0, 50.0, age=80)
    assert r79 is not None and r80 is not None
    # 80세는 79세와 동일한 보정 적용 (cap)
    assert r79.nasal_index == r80.nasal_index


def test_age_100_capped_at_79():
    """100세도 79세 cap 적용."""
    r79 = classify_nose_shape(45.0, 50.0, age=79)
    r100 = classify_nose_shape(45.0, 50.0, age=100)
    assert r79 is not None and r100 is not None
    assert r79.nasal_index == r100.nasal_index


def test_age_120_capped_at_79():
    """입력 범위 상한 120세도 79세 cap."""
    r79 = classify_nose_shape(45.0, 50.0, age=79)
    r120 = classify_nose_shape(45.0, 50.0, age=120)
    assert r79 is not None and r120 is not None
    assert r79.nasal_index == r120.nasal_index


def test_age_25_no_correction():
    """25세 (baseline)는 보정 0."""
    r = classify_nose_shape(40.0, 50.0, age=25)
    assert r is not None
    # NI_obs = 40/50*100 = 80, age 25 → 보정 0 → NI_eff = 80
    assert r.nasal_index == 80.0


def test_age_50_normal_correction():
    """50세는 정상 회귀 (외삽 X)."""
    r = classify_nose_shape(40.0, 50.0, age=50)
    assert r is not None
    # NI_obs = 80, age 50: 보정 = 0.0035 × 625 = 2.1875
    # NI_eff = 80 - 2.1875 = 77.8125
    assert 77.5 < r.nasal_index < 78.5


def test_invalid_age_above_120_rejected():
    """age > 120는 None (입력 검증)."""
    r = classify_nose_shape(40.0, 50.0, age=121)
    assert r is None


def test_invalid_age_negative_rejected():
    """음수 age는 None."""
    r = classify_nose_shape(40.0, 50.0, age=-5)
    assert r is None


# ─────────────────────────── Bae SS 2023 KCI NI 메타 ───────────────────────────

def test_korean_20s_ni_mean_male():
    """한국 20대 남성 NI 평균 76.16."""
    r = get_nose_korean_20s_ni_mean("male")
    assert r is not None
    assert r["ni_mean"] == 76.16
    assert r["ni_sd"] == 6.78
    assert r["sample_size"] == 50


def test_korean_20s_ni_mean_female():
    """한국 20대 여성 NI 평균 77.84."""
    r = get_nose_korean_20s_ni_mean("female")
    assert r is not None
    assert r["ni_mean"] == 77.84
    assert r["ni_sd"] == 7.16
    assert r["sample_size"] == 50


def test_korean_20s_ni_mean_invalid_sex():
    """잘못된 sex 입력 → None."""
    assert get_nose_korean_20s_ni_mean("invalid") is None
    assert get_nose_korean_20s_ni_mean("") is None


def test_korean_20s_ni_in_mesorrhine_range():
    """Bae SS 2023 — 한국 20대 NI 평균 모두 Mesorrhine (70~85) 범주."""
    male = get_nose_korean_20s_ni_mean("male")
    female = get_nose_korean_20s_ni_mean("female")
    assert male is not None and female is not None
    assert 70.0 <= male["ni_mean"] <= 85.0
    assert 70.0 <= female["ni_mean"] <= 85.0


# ─────────────────────────── 결정론 ───────────────────────────

def test_deterministic_age_80_cap():
    """동일 입력 → 동일 결과 (결정론)."""
    r1 = classify_nose_shape(45.0, 50.0, age=85)
    r2 = classify_nose_shape(45.0, 50.0, age=85)
    assert r1 is not None and r2 is not None
    assert r1 == r2


# ─────────────────────────── 면책 ───────────────────────────

def test_disclaimer_preserved_on_age_cap():
    """80세 cap 적용 시에도 면책 포함."""
    r = classify_nose_shape(45.0, 50.0, age=85)
    assert r is not None
    assert "운명·길흉" in r.disclaimer
    assert "ADR-006" in r.disclaimer
