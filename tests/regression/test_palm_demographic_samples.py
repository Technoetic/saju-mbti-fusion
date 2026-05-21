"""ADR-100 회귀 — 손금 다인종·연령 표본 메타 + 의료 단정 검출.

/squeeze-report "손금 보조선 정량 분석 학술 데이터.md" 처리 결과:
- C1·C2·C4·C5·C10 ACCEPT (5 표본 + 의료 차단 강화)
- C3·C7·C9 REJECT (도그마·이혼 단정·빈 약속)
"""

from engine.divination.palm.knowledge import (
    PALM_DEMOGRAPHIC_SAMPLES,
    PalmDemographicSample,
    get_demographic_sample,
    is_medical_assertion_text,
)


# ── ① 표본 풀 정합 (4건) ─────────────────────────────


def test_demographic_samples_count():
    """4 표본 풀 영속화."""
    assert len(PALM_DEMOGRAPHIC_SAMPLES) == 4


def test_korean_sample_park_js_2010():
    """Park JS 2010 한국 표본 N=5196 (C2 표본 N 정정)."""
    s = get_demographic_sample("park-js-2010-korean")
    assert s is not None
    assert s.population == "한국 동아시아"
    assert s.n == 5196
    assert s.publication_year == 2010
    assert "synapse.koreamed.org" in s.primary_source_url


def test_indian_sample_gupta_2022():
    """Gupta Sharma 2022 북인도 N=300 (C4)."""
    s = get_demographic_sample("gupta-sharma-2022-north-india")
    assert s is not None
    assert s.n == 300
    assert s.publication_year == 2022
    assert "PMC9469369" in s.primary_source_url


def test_african_sample_ethiopia_2019():
    """에티오피아 2019 N=318 (C5)."""
    s = get_demographic_sample("ethiopia-2019-addis-ababa")
    assert s is not None
    assert s.n == 318
    assert "에티오피아" in s.population
    assert "PMC6689715" in s.primary_source_url


def test_ieee_1971_origin():
    """IEEE 1971 Oda 출처 (C1) — 운명선 0.85 임계 기원."""
    s = get_demographic_sample("ieee-1971-oda-pattern-recognition")
    assert s is not None
    assert s.publication_year == 1971
    assert "패턴 인식" in s.population  # 운명학 X
    assert "ieeexplore" in s.primary_source_url
    assert s.n == 0  # 표본 N 부적합 (영상 처리 알고리즘 기원)


def test_unknown_sample_returns_none():
    """미등록 표본 → None."""
    assert get_demographic_sample("foreign-unknown") is None


# ── ② 표본 dataclass 구조 ────────────────────────────


def test_sample_dataclass_fields():
    """PalmDemographicSample 8 필드 정합."""
    s = PALM_DEMOGRAPHIC_SAMPLES[0]
    assert isinstance(s, PalmDemographicSample)
    assert hasattr(s, "key")
    assert hasattr(s, "population")
    assert hasattr(s, "n")
    assert hasattr(s, "age_range")
    assert hasattr(s, "publication_year")
    assert hasattr(s, "primary_work")
    assert hasattr(s, "primary_source_url")
    assert hasattr(s, "focus")


def test_all_samples_have_url():
    """모든 표본 출처 URL 명시 (ADR-010 사실성 분리)."""
    for s in PALM_DEMOGRAPHIC_SAMPLES:
        assert s.primary_source_url
        assert s.primary_source_url.startswith("https://")


def test_all_samples_have_focus():
    """모든 표본 본 시스템 활용 영역 명시."""
    for s in PALM_DEMOGRAPHIC_SAMPLES:
        assert s.focus
        assert len(s.focus) > 5


# ── ③ 의료 단정 검출 (C10 ADR-100·ADR-006) ───────────


def test_simian_crease_detected():
    """Simian crease 의료 마커 검출."""
    assert is_medical_assertion_text("이 손금은 Simian crease 패턴입니다") is True
    assert is_medical_assertion_text("원숭이 손금이 보여요") is True


def test_down_syndrome_detected():
    """다운증후군·Trisomy 21 검출."""
    assert is_medical_assertion_text("다운증후군 진단") is True
    assert is_medical_assertion_text("Trisomy 21 마커") is True


def test_psychiatric_prediction_detected():
    """정신질환 예측 검출."""
    assert is_medical_assertion_text("정신질환 예측이 가능합니다") is True
    assert is_medical_assertion_text("schizophrenia diagnostic") is True


def test_normal_palm_text_not_detected():
    """정상 손금 풀이 본문은 의료 단정 X."""
    assert is_medical_assertion_text("운명선이 곧게 뻗어 있습니다") is False
    assert is_medical_assertion_text("태양선이 선명합니다") is False
    assert is_medical_assertion_text("4 보조선 분류 결과") is False


def test_empty_text_not_detected():
    """빈 텍스트 → False."""
    assert is_medical_assertion_text("") is False
    assert is_medical_assertion_text(None) is False  # type: ignore


# ── ④ ADR 정합 명시 ──────────────────────────────────


def test_disclaimer_v2_contains_adr_100():
    """_DISCLAIMER_BASE_V2 본문에 ADR-100 명시 확인 (모듈 본문 검사)."""
    import engine.divination.palm.knowledge as kn_module
    src = kn_module.__file__
    if src:
        from pathlib import Path
        content = Path(src).read_text(encoding="utf-8")
        # 본 ADR-100 disclaimer 영역 정합
        assert "ADR-100" in content
        assert "다운증후군" in content
        assert "Park JS 2010" in content
        assert "Gupta Sharma 2022" in content
        assert "에티오피아 2019" in content
        assert "IEEE 1971" in content


def test_no_fate_mapping_in_samples():
    """표본 메타에 fate_mapping·marriage_outcome·divorce 부재 (ADR-006)."""
    for s in PALM_DEMOGRAPHIC_SAMPLES:
        assert not hasattr(s, "fate_mapping")
        assert not hasattr(s, "marriage_outcome")
        assert not hasattr(s, "divorce_risk")
