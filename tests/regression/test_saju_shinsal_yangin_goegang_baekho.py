"""ADR-128 회귀 — saju 신살 3종 (양인·괴강·백호).

학파: 자평진전(沈孝瞻 1734) + 삼명통회(萬民英 1578) 정통 일치.

학술 출처 ISBN:
  - 자평진전: 이담북스 (2011, 김정혜·서소옥·안명순 역, "원전 현토 완역")
  - 자평진전: 푸른길 (2023, 이명재 역)
  - 삼명통회: 문원북 (2017-2019, 김정안 역) · 부크크 (2023, 완역)

KCI 직접 인용 부재 (DBpia 검색 0 건) — 정통 사주명리 원전 본 학파 명시 의무.
"""
from __future__ import annotations

import pytest

from engine.saju.shensha import (
    SHENSHA_MEANINGS,
    compute_shensha,
    is_baekho,
    is_goegang,
    is_yangin,
)


# ────────────────── 양인살 (양간 5종, 자평진전 옵션 A 디폴트) ──────────────────


class TestYanginDeterministic:
    """양인살 5 양간 결정론 매핑."""

    @pytest.mark.parametrize("day_gan, yangin_ji", [
        ("甲", "卯"),
        ("丙", "午"),
        ("戊", "午"),
        ("庚", "酉"),
        ("壬", "子"),
    ])
    def test_5_yang_gan_yangin(self, day_gan: str, yangin_ji: str):
        """양간 5종 양인 매핑 (자평진전 정통)."""
        assert is_yangin(day_gan, yangin_ji) is True

    @pytest.mark.parametrize("day_gan", ["乙", "丁", "己", "辛", "癸"])
    def test_5_eum_gan_not_yangin(self, day_gan: str):
        """음간 5종 양인 비매핑 (자평진전 옵션 A 정합)."""
        # 모든 12 지지에 대해 음간은 양인 매핑 부재
        for ji in ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]:
            assert is_yangin(day_gan, ji) is False

    def test_yangin_wrong_ji_returns_false(self):
        """양간이라도 양인 지지가 아니면 False."""
        # 甲의 양인은 卯, 다른 지지는 False
        assert is_yangin("甲", "子") is False
        assert is_yangin("甲", "卯") is True

    def test_yangin_invalid_input(self):
        """잘못된 입력 False."""
        assert is_yangin("", "卯") is False
        assert is_yangin("甲", "") is False
        assert is_yangin("X", "卯") is False


# ────────────────── 괴강살 (4 일주 정통 표준) ──────────────────


class TestGoegangDeterministic:
    """괴강살 4 일주 결정론 매핑."""

    @pytest.mark.parametrize("day_pillar", ["庚辰", "庚戌", "壬辰", "戊戌"])
    def test_4_goegang_pillars(self, day_pillar: str):
        """정통 4 괴강 일주 (자평진전·삼명통회 일치)."""
        assert is_goegang(day_pillar) is True

    @pytest.mark.parametrize("day_pillar", [
        "甲子", "乙丑", "丙寅", "丁卯",  # 임의 4 일주
        "庚寅",  # 庚 + 다른 지지 (괴강 X)
        "戊辰",  # 戊 + 다른 지지 (괴강 X, 백호 O)
        "壬戌",  # 壬 + 다른 지지 (괴강 X, 백호 O)
    ])
    def test_non_goegang_pillars(self, day_pillar: str):
        """비-괴강 일주."""
        assert is_goegang(day_pillar) is False

    def test_goegang_invalid_input(self):
        """잘못된 입력 False."""
        assert is_goegang("") is False
        assert is_goegang("XX") is False
        assert is_goegang("X") is False


# ────────────────── 백호살 (7 일주 정통 표준) ──────────────────


class TestBaekhoDeterministic:
    """백호살 7 일주 결정론 매핑."""

    @pytest.mark.parametrize("day_pillar", [
        "甲辰", "乙未", "丙戌", "丁丑", "戊辰", "壬戌", "癸丑"
    ])
    def test_7_baekho_pillars(self, day_pillar: str):
        """정통 7 백호 일주 (자평진전·삼명통회 일치)."""
        assert is_baekho(day_pillar) is True

    @pytest.mark.parametrize("day_pillar", [
        "甲子", "乙丑", "庚辰", "庚戌", "壬辰", "戊戌"  # 괴강 4 일주는 백호 X
    ])
    def test_non_baekho_pillars(self, day_pillar: str):
        """비-백호 일주."""
        assert is_baekho(day_pillar) is False

    def test_baekho_invalid_input(self):
        """잘못된 입력 False."""
        assert is_baekho("") is False
        assert is_baekho("XX") is False


# ────────────────── compute_shensha 통합 ──────────────────


def _make_pillars(year, month, day, hour) -> dict:
    """간단한 4주 fixture — 4 한자 쌍 (gan+ji) 입력."""
    return {
        "year_pillar": {"gan_han": year[0], "ji_han": year[1], "gan": "", "ji": ""},
        "month_pillar": {"gan_han": month[0], "ji_han": month[1], "gan": "", "ji": ""},
        "day_pillar": {"gan_han": day[0], "ji_han": day[1], "gan": "", "ji": ""},
        "hour_pillar": {"gan_han": hour[0], "ji_han": hour[1], "gan": "", "ji": ""},
    }


class TestComputeShenshaIntegration:
    """compute_shensha 8종 통합 (기존 5 + 신규 3) 회귀."""

    def test_all_8_keys_present(self):
        """8 신살 키 모두 반환."""
        pillars = _make_pillars(("甲", "子"), ("丙", "寅"), ("甲", "卯"), ("乙", "亥"))
        result = compute_shensha(pillars)
        assert set(result.keys()) == {
            "cheoneul", "munchang", "yeokma", "dohwa", "kongmang",
            "yangin", "goegang", "baekho",
        }

    def test_yangin_detection_in_pillars(self):
        """일간 甲 + 卯 일지 → yangin에 卯 등재."""
        pillars = _make_pillars(("甲", "子"), ("丙", "寅"), ("甲", "卯"), ("乙", "亥"))
        result = compute_shensha(pillars)
        assert "卯" in result["yangin"]

    def test_goegang_detection_in_pillars(self):
        """일주 庚辰 → goegang에 '庚辰' 등재."""
        pillars = _make_pillars(("甲", "子"), ("丙", "寅"), ("庚", "辰"), ("乙", "亥"))
        result = compute_shensha(pillars)
        assert result["goegang"] == ["庚辰"]

    def test_baekho_detection_in_pillars(self):
        """일주 甲辰 → baekho에 '甲辰' 등재."""
        pillars = _make_pillars(("甲", "子"), ("丙", "寅"), ("甲", "辰"), ("乙", "亥"))
        result = compute_shensha(pillars)
        assert result["baekho"] == ["甲辰"]

    def test_non_match_empty_lists(self):
        """매칭 없으면 빈 리스트."""
        pillars = _make_pillars(("甲", "子"), ("丙", "寅"), ("乙", "丑"), ("丁", "卯"))
        result = compute_shensha(pillars)
        # 乙은 음간 — 양인 비매핑
        assert result["yangin"] == []
        # 乙丑은 괴강 X·백호 X
        assert result["goegang"] == []
        assert result["baekho"] == []


# ────────────────── 흐름 톤 (ADR-006 단정 어휘 차단 정합) ──────────────────


class TestShenshaFlowTone:
    """3 신살 흐름 톤 단정 어휘 차단 (ADR-006)."""

    def test_yangin_meaning_no_assertion(self):
        """양인 풀이에 '이혼·사망·단명' 단정 어휘 없음."""
        meaning = SHENSHA_MEANINGS["yangin"]["summary"]
        for assertion in ["이혼", "사망", "단명", "재산 탕진"]:
            assert assertion not in meaning

    def test_goegang_meaning_no_assertion(self):
        """괴강 풀이에 '과부·이혼·혈광지사' 단정 어휘 없음."""
        meaning = SHENSHA_MEANINGS["goegang"]["summary"]
        for assertion in ["과부", "이혼", "혈광지사", "사고사"]:
            assert assertion not in meaning

    def test_baekho_meaning_no_assertion(self):
        """백호 풀이에 '혈광지사·사고사·단명' 단정 어휘 없음."""
        meaning = SHENSHA_MEANINGS["baekho"]["summary"]
        for assertion in ["혈광지사", "사고사", "단명"]:
            assert assertion not in meaning

    def test_three_new_shinsal_in_meanings(self):
        """3 신살 모두 SHENSHA_MEANINGS 풀에 등재."""
        for key in ["yangin", "goegang", "baekho"]:
            assert key in SHENSHA_MEANINGS
            assert "label" in SHENSHA_MEANINGS[key]
            assert "summary" in SHENSHA_MEANINGS[key]
