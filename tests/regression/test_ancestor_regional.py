"""ADR-124 4 권역 위령 의례 메타 회귀.

학술 근거: 한국학중앙연구원·국립민속박물관 정통.
"""
from __future__ import annotations

from engine.divination.ancestor.regional_rites import (
    REGIONAL_RITES,
    get_regional_rite,
    list_all_regions,
)


def test_four_regions_present():
    """4 권역 영속화 — 수도권·경상도·전라도·북부."""
    assert set(REGIONAL_RITES.keys()) == {"수도권", "경상도", "전라도", "북부"}


def test_sudokwon_has_jinogi_saenam():
    """수도권 → 진오기굿·새남굿."""
    rite = get_regional_rite("수도권")
    assert rite is not None
    rites = rite["rites"]
    assert isinstance(rites, list)
    assert "진오기굿" in rites
    assert "새남굿" in rites


def test_jeolla_has_ssitgimgut():
    """전라도 → 씻김굿."""
    rite = get_regional_rite("전라도")
    assert rite is not None
    rites = rite["rites"]
    assert isinstance(rites, list)
    assert "씻김굿" in rites


def test_north_has_mangmuk():
    """북부 → 망묵이굿·다리굿."""
    rite = get_regional_rite("북부")
    assert rite is not None
    rites = rite["rites"]
    assert isinstance(rites, list)
    assert "망묵이굿" in rites
    assert "다리굿" in rites


def test_gyeongsang_has_ogugut():
    """경상도 → 오구굿."""
    rite = get_regional_rite("경상도")
    assert rite is not None
    rites = rite["rites"]
    assert isinstance(rites, list)
    assert "오구굿" in rites


def test_invalid_region_returns_none():
    """4 권역 외 → None."""
    assert get_regional_rite("미지") is None


def test_all_regions_have_school():
    """모든 권역에 학파 출처 명시 (ADR-010)."""
    for region in list_all_regions():
        rite = get_regional_rite(region)
        assert rite is not None
        assert "한국학중앙연구원" in str(rite["school"])
        assert "국립민속박물관" in str(rite["school"])


def test_all_regions_have_disclaimer():
    """모든 권역에 면책 의무 (ADR-006)."""
    for region in list_all_regions():
        rite = get_regional_rite(region)
        assert rite is not None
        assert "점술적 단정" in str(rite["disclaimer"])


def test_all_regions_have_source_urls():
    """모든 권역에 학술 출처 URL (ADR-010 검증 가능)."""
    for region in list_all_regions():
        rite = get_regional_rite(region)
        assert rite is not None
        urls = rite["source_urls"]
        assert isinstance(urls, list)
        assert len(urls) >= 1
        # folkency.nfm.go.kr 또는 encykorea.aks.ac.kr 출처
        for url in urls:
            assert url.startswith("https://"), f"비-https URL: {url}"
