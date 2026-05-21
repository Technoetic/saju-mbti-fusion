"""ADR-131 회귀 — saju 12신살 풀 결정론 매핑.

학파: 자평진전(沈孝瞻 1734) · 삼명통회(萬民英 1578) 정통 일치 표준.

12 신살: 겁살·재살·천살·지살·년살·월살·망신살·장성살·반안살·역마살·육해살·화개살

본 시스템 정합 검증:
  - 천살은 ADR-122 ancestor 모듈 매핑과 동일
  - 역마는 shensha.py _TRIPLES 매핑과 동일
"""
from __future__ import annotations

import pytest

from engine.saju.twelve_sinsal import (
    SINSAL_FLOW_TONE,
    detect_sinsal_in_pillars,
    get_sinsal_for_year,
)


# 4 삼합 × 12 신살 = 48 핵심 매핑 (자평진전 정통)
EXPECTED_MAPPINGS = {
    # 申子辰 (수국)
    "申": {"겁살": "巳", "재살": "午", "천살": "未", "지살": "申", "년살": "酉",
            "월살": "戌", "망신살": "亥", "장성살": "子", "반안살": "丑",
            "역마살": "寅", "육해살": "卯", "화개살": "辰"},
    # 巳酉丑 (금국)
    "巳": {"겁살": "寅", "재살": "卯", "천살": "辰", "지살": "巳", "년살": "午",
            "월살": "未", "망신살": "申", "장성살": "酉", "반안살": "戌",
            "역마살": "亥", "육해살": "子", "화개살": "丑"},
    # 寅午戌 (화국)
    "寅": {"겁살": "亥", "재살": "子", "천살": "丑", "지살": "寅", "년살": "卯",
            "월살": "辰", "망신살": "巳", "장성살": "午", "반안살": "未",
            "역마살": "申", "육해살": "酉", "화개살": "戌"},
    # 亥卯未 (목국)
    "亥": {"겁살": "申", "재살": "酉", "천살": "戌", "지살": "亥", "년살": "子",
            "월살": "丑", "망신살": "寅", "장성살": "卯", "반안살": "辰",
            "역마살": "巳", "육해살": "午", "화개살": "未"},
}


class TestSinsalMappings:
    """4 삼합 × 12 신살 매핑 결정론."""

    @pytest.mark.parametrize("year_ji", ["申", "子", "辰"])
    def test_suguk_samhap_same_mapping(self, year_ji: str):
        """수국 (申子辰) 3 지지 모두 동일 매핑."""
        result = get_sinsal_for_year(year_ji)
        for sinsal, expected_ji in EXPECTED_MAPPINGS["申"].items():
            assert result[sinsal]["ji"] == expected_ji, (
                f"{year_ji} {sinsal}: 기대 {expected_ji}, 실제 {result[sinsal]['ji']}"
            )

    @pytest.mark.parametrize("year_ji", ["巳", "酉", "丑"])
    def test_geumguk_samhap_same_mapping(self, year_ji: str):
        """금국 (巳酉丑) 3 지지 모두 동일 매핑."""
        result = get_sinsal_for_year(year_ji)
        for sinsal, expected_ji in EXPECTED_MAPPINGS["巳"].items():
            assert result[sinsal]["ji"] == expected_ji

    @pytest.mark.parametrize("year_ji", ["寅", "午", "戌"])
    def test_hwaguk_samhap_same_mapping(self, year_ji: str):
        """화국 (寅午戌) 3 지지 모두 동일 매핑."""
        result = get_sinsal_for_year(year_ji)
        for sinsal, expected_ji in EXPECTED_MAPPINGS["寅"].items():
            assert result[sinsal]["ji"] == expected_ji

    @pytest.mark.parametrize("year_ji", ["亥", "卯", "未"])
    def test_mokguk_samhap_same_mapping(self, year_ji: str):
        """목국 (亥卯未) 3 지지 모두 동일 매핑."""
        result = get_sinsal_for_year(year_ji)
        for sinsal, expected_ji in EXPECTED_MAPPINGS["亥"].items():
            assert result[sinsal]["ji"] == expected_ji


class TestCheonsalConsistencyAcrossAdr:
    """본 시스템 ADR-122 ancestor 천살 매핑과 정합성 검증."""

    def test_cheonsal_matches_adr_122(self):
        """천살이 ADR-122 cheonsal_direction 매핑과 일치."""
        from engine.divination.ancestor.cheonsal import CHEONSAL_DIRECTIONS_BY_YEAR_JI
        for year_ji in ["申", "子", "辰", "巳", "酉", "丑",
                         "寅", "午", "戌", "亥", "卯", "未"]:
            sinsal_result = get_sinsal_for_year(year_ji)
            ancestor_cheonsal = CHEONSAL_DIRECTIONS_BY_YEAR_JI[year_ji]["cheonsal_ji"]
            assert sinsal_result["천살"]["ji"] == ancestor_cheonsal, (
                f"{year_ji}: 12신살 천살={sinsal_result['천살']['ji']}, "
                f"ADR-122 천살={ancestor_cheonsal} 불일치"
            )


class TestYeokmaConsistencyAcrossAdr:
    """본 시스템 shensha.py 역마 매핑과 정합성 검증."""

    def test_yeokma_matches_shensha(self):
        """역마살이 shensha.py _TRIPLES 매핑과 일치."""
        # _TRIPLES 매핑 (year_ji → yeokma):
        # 申子辰 → 寅, 巳酉丑 → 亥, 寅午戌 → 申, 亥卯未 → 巳
        expected = {
            "申": "寅", "子": "寅", "辰": "寅",
            "巳": "亥", "酉": "亥", "丑": "亥",
            "寅": "申", "午": "申", "戌": "申",
            "亥": "巳", "卯": "巳", "未": "巳",
        }
        for year_ji, expected_yeokma in expected.items():
            result = get_sinsal_for_year(year_ji)
            assert result["역마살"]["ji"] == expected_yeokma, (
                f"{year_ji}: 12신살 역마={result['역마살']['ji']}, "
                f"shensha 역마={expected_yeokma} 불일치"
            )


class TestSinsalDetectionInPillars:
    """4주 지지 매칭."""

    def test_detect_full_pillars(self):
        """4주 모두 매칭 사례 — 申子辰 + 4주 {子, 亥, 辰, 未}."""
        result = detect_sinsal_in_pillars("子", ["子", "亥", "辰", "未"])
        # 子 = 장성살
        assert "子" in result["장성살"]
        # 亥 = 망신살
        assert "亥" in result["망신살"]
        # 辰 = 화개살
        assert "辰" in result["화개살"]
        # 未 = 천살
        assert "未" in result["천살"]

    def test_no_match_empty_lists(self):
        """매칭 없는 신살은 빈 리스트."""
        result = detect_sinsal_in_pillars("子", ["子"])
        # 子만 있으면 장성살만 매칭, 나머지 11종 빈 리스트
        assert result["장성살"] == ["子"]
        assert result["겁살"] == []
        assert result["천살"] == []

    def test_invalid_year_ji_returns_empty_lists(self):
        """잘못된 year_ji는 모든 신살 빈 리스트."""
        result = detect_sinsal_in_pillars("X", ["子", "亥"])
        for sinsal_name in result.keys():
            assert result[sinsal_name] == []


class TestSinsalSafety:
    """ADR-006 자문 거절 정신 정합."""

    def test_invalid_year_ji_returns_empty_dict(self):
        """잘못된 입력 빈 dict."""
        assert get_sinsal_for_year("X") == {}
        assert get_sinsal_for_year("") == {}

    def test_deterministic_same_input(self):
        """결정론 — 동일 입력 동일 출력."""
        r1 = get_sinsal_for_year("子")
        r2 = get_sinsal_for_year("子")
        assert r1 == r2

    def test_flow_tone_12_sinsal_present(self):
        """SINSAL_FLOW_TONE 12 신살 영속화."""
        for sinsal in ["겁살", "재살", "천살", "지살", "년살", "월살",
                       "망신살", "장성살", "반안살", "역마살", "육해살", "화개살"]:
            assert sinsal in SINSAL_FLOW_TONE
            assert "label" in SINSAL_FLOW_TONE[sinsal]
            assert "summary" in SINSAL_FLOW_TONE[sinsal]

    def test_flow_tone_no_assertion_words(self):
        """모든 흐름 톤에 단정 어휘 부재."""
        for sinsal, info in SINSAL_FLOW_TONE.items():
            summary = info["summary"]
            for assertion in ["이혼", "사망", "단명", "재산 탕진", "사고사", "혈광지사"]:
                assert assertion not in summary, (
                    f"{sinsal} summary에 단정 어휘 '{assertion}' 포함: {summary}"
                )

    def test_all_12_sinsal_returned(self):
        """get_sinsal_for_year는 12 신살 모두 반환."""
        result = get_sinsal_for_year("子")
        assert set(result.keys()) == {
            "겁살", "재살", "천살", "지살", "년살", "월살",
            "망신살", "장성살", "반안살", "역마살", "육해살", "화개살",
        }

    def test_each_sinsal_has_han(self):
        """각 신살에 한자 명시."""
        result = get_sinsal_for_year("子")
        for sinsal, info in result.items():
            assert "han" in info
            assert "ji" in info
            assert info["han"].endswith("殺"), f"{sinsal} 한자에 殺 결손: {info['han']}"
