"""ADR-066 회귀 — 손금 학파 메타 + 4 보조선 결정론 분류 검증.

출처: Cheiro 1900·Benham 1901·Saint-Germain 1897 (Archive.org public domain)
원칙: 운명·재물·결혼·이혼 단정 매핑 차단 (ADR-006 최고 보안)
"""

from engine.divination.palm.knowledge import (
    PALM_SCHOOLS,
    FATE_LINE_LINEARITY_THRESHOLD,
    SUN_LINE_INTENSITY_MIN_PCT,
    MERCURY_LINE_LINEARITY_THRESHOLD,
    FATE_LINE_STRAIGHT, FATE_LINE_CURVED, FATE_LINE_ABSENT,
    SUN_LINE_CLEAR, SUN_LINE_FAINT, SUN_LINE_ABSENT,
    MERCURY_LINE_CONTINUOUS, MERCURY_LINE_FRAGMENTED,
    MARRIAGE_LINE_SINGLE_CLEAR, MARRIAGE_LINE_MULTIPLE,
    MARRIAGE_LINE_FORKED, MARRIAGE_LINE_ABSENT,
    FateLineResult, SunLineResult, MercuryLineResult, MarriageLineResult,
    classify_fate_line, classify_sun_line, classify_mercury_line, classify_marriage_line,
    get_school_by_key, format_schools_metadata_for_prompt,
)


# ─────────────────────────── 학파 메타 ───────────────────────────

def test_six_schools_present():
    """6 학파 메타 영속 (서양 4 + 동양 2)."""
    assert len(PALM_SCHOOLS) == 6
    keys = {s.key for s in PALM_SCHOOLS}
    expected = {"cheiro", "benham", "saint-germain", "hutchinson", "mauisangbeop", "donguibogam"}
    assert keys == expected


def test_traditions_split_western_eastern():
    """서양 4 + 동양 2 옵션 병행 (ADR-015)."""
    western = [s for s in PALM_SCHOOLS if s.tradition == "western"]
    eastern = [s for s in PALM_SCHOOLS if s.tradition == "eastern"]
    assert len(western) == 4
    assert len(eastern) == 2


def test_all_schools_have_verified_urls():
    """모든 학파 1차 출처 URL Archive.org / mediclassics / encykorea."""
    for s in PALM_SCHOOLS:
        assert s.primary_source_url.startswith("http")
        assert s.primary_source_url


def test_adr_002_notes_required():
    """ADR-002 학파 차이 명시 의무."""
    for s in PALM_SCHOOLS:
        assert s.adr_002_note


def test_get_school_by_key():
    """학파 조회."""
    benham = get_school_by_key("benham")
    assert benham is not None
    assert benham.name_short == "Benham"
    assert get_school_by_key("nonexistent") is None


def test_prompt_metadata_has_safety_clause():
    """Stage 2 프롬프트 텍스트에 ADR-006 안전 절 자동 포함."""
    text = format_schools_metadata_for_prompt()
    assert "ADR-006" in text
    assert "운명" in text
    assert "이혼" in text
    assert "사상체질" in text


# ─────────────────────────── 운명선 (Benham 1901) ───────────────────────────

def test_fate_line_straight_threshold():
    """linearity >= 0.85 → 곧은 운명선."""
    r = classify_fate_line(0.90)
    assert r is not None
    assert r.shape_type == FATE_LINE_STRAIGHT
    assert r.source_school == "benham"


def test_fate_line_curved_below_threshold():
    """linearity < 0.85 → 굽은 운명선."""
    r = classify_fate_line(0.70)
    assert r is not None
    assert r.shape_type == FATE_LINE_CURVED


def test_fate_line_boundary_exact():
    """linearity = 0.85 → straight (≥ 포함)."""
    r = classify_fate_line(0.85)
    assert r is not None
    assert r.shape_type == FATE_LINE_STRAIGHT


def test_fate_line_absent_on_none():
    """None 입력 → 운명선 부재."""
    r = classify_fate_line(None)
    assert r is not None
    assert r.shape_type == FATE_LINE_ABSENT


def test_fate_line_no_fate_mapping_field():
    """★ FateLineResult에 fate_mapping 필드 부재 (ADR-006 운명 단정 차단)."""
    r = classify_fate_line(0.90)
    assert r is not None
    assert hasattr(r, "shape_type")
    assert not hasattr(r, "fate_mapping")
    assert not hasattr(r, "career_outcome")


# ─────────────────────────── 태양선 (Cheiro 1900) ───────────────────────────

def test_sun_line_clear():
    """intensity ≥ 15% + length ≥ 1cm → 선명한 태양선."""
    r = classify_sun_line(20.0, 2.0)
    assert r is not None
    assert r.shape_type == SUN_LINE_CLEAR


def test_sun_line_faint_low_intensity():
    """intensity < 15% → 옅은 태양선."""
    r = classify_sun_line(10.0, 2.0)
    assert r is not None
    assert r.shape_type == SUN_LINE_FAINT


def test_sun_line_faint_short_length():
    """length < 1cm → 옅은 태양선."""
    r = classify_sun_line(20.0, 0.5)
    assert r is not None
    assert r.shape_type == SUN_LINE_FAINT


def test_sun_line_absent_on_none():
    """None 입력 → 태양선 부재."""
    r = classify_sun_line(None, None)
    assert r is not None
    assert r.shape_type == SUN_LINE_ABSENT


# ─────────────────────────── 수성선 (Benham 1901) ───────────────────────────

def test_mercury_line_continuous():
    """linearity ≥ 0.80 + interrupt ≤ 1 → 이어진 수성선."""
    r = classify_mercury_line(0.85, 1)
    assert r is not None
    assert r.shape_type == MERCURY_LINE_CONTINUOUS


def test_mercury_line_fragmented_low_linearity():
    """linearity < 0.80 → 끊긴 수성선."""
    r = classify_mercury_line(0.70, 0)
    assert r is not None
    assert r.shape_type == MERCURY_LINE_FRAGMENTED


def test_mercury_line_fragmented_many_interrupts():
    """interrupt ≥ 2 → 끊긴 수성선."""
    r = classify_mercury_line(0.90, 3)
    assert r is not None
    assert r.shape_type == MERCURY_LINE_FRAGMENTED


def test_mercury_line_no_wealth_mapping():
    """★ MercuryLineResult에 wealth_mapping·재물복 필드 부재 (ADR-006)."""
    r = classify_mercury_line(0.85, 1)
    assert r is not None
    assert not hasattr(r, "wealth_mapping")
    assert not hasattr(r, "money_outcome")


# ─────────────────────────── 결혼선 (Saint-Germain 1897) ★ 최고 보안 ───────────────────────────

def test_marriage_line_single_clear():
    """1개 + 길이 ≥ 0.5cm → 한 줄 결혼선."""
    r = classify_marriage_line(1, 1.0)
    assert r is not None
    assert r.shape_type == MARRIAGE_LINE_SINGLE_CLEAR


def test_marriage_line_multiple():
    """≥ 2개 → 여러 줄 결혼선."""
    r = classify_marriage_line(3, 1.0)
    assert r is not None
    assert r.shape_type == MARRIAGE_LINE_MULTIPLE


def test_marriage_line_forked_priority():
    """forking 있으면 multiple보다 우선."""
    r = classify_marriage_line(2, 1.0, has_forking=True)
    assert r is not None
    assert r.shape_type == MARRIAGE_LINE_FORKED


def test_marriage_line_absent_on_zero():
    """count=0 → 결혼선 부재."""
    r = classify_marriage_line(0, 0.0)
    assert r is not None
    assert r.shape_type == MARRIAGE_LINE_ABSENT


def test_marriage_line_no_divorce_mapping():
    """★★ MarriageLineResult에 marriage_outcome·divorce·affair 매핑 부재 (ADR-006 최고 보안)."""
    r = classify_marriage_line(2, 1.0, has_forking=True)
    assert r is not None
    assert not hasattr(r, "marriage_outcome_mapping")
    assert not hasattr(r, "divorce_risk")
    assert not hasattr(r, "affair_indicator")


# ─────────────────────────── 면책 + 사상체질 차단 ───────────────────────────

def test_all_results_have_disclaimer():
    """모든 분류 결과에 ADR-006 면책 자동 첨부."""
    results = [
        classify_fate_line(0.90),
        classify_sun_line(20.0, 2.0),
        classify_mercury_line(0.85, 1),
        classify_marriage_line(1, 1.0),
    ]
    for r in results:
        assert r is not None
        assert "운명" in r.disclaimer
        assert "사상체질" in r.disclaimer


def test_threshold_constants_documented():
    """임계값 상수 출처 명시 — Benham 0.85 / Cheiro 15% / Mercury 0.80."""
    assert FATE_LINE_LINEARITY_THRESHOLD == 0.85
    assert SUN_LINE_INTENSITY_MIN_PCT == 15.0
    assert MERCURY_LINE_LINEARITY_THRESHOLD == 0.80
