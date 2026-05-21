"""ADR-132·133 회귀 — saju 양인 옵션 B (삼명통회 음간 확장) + 신살 강도 가중치.

학술 근거:
  - 자평진전(沈孝瞻 1734) ISBN 9791196084417 — 옵션 A 양간 5종 디폴트
  - 삼명통회(萬民英 1578) ISBN 9791139035261·9791137216822 — 옵션 B 음간 5종 확장
  - 보고서 「사주 신살 학파별 분류 표준 조사」 §2.4 + §6.3
"""
from __future__ import annotations

import pytest

from engine.saju.shensha import (
    SYNERGY_TONE_GUIDE,
    compute_shensha,
    compute_sinsal_synergy_weight,
    is_yangin,
    render_synergy_tone_guide,
)


# ──────────── ADR-132 양인 옵션 B (삼명통회 음간 5종 확장) ────────────


class TestYanginOptionA:
    """옵션 A 디폴트 — 자평진전 양간 5종 (기존 ADR-128)."""

    @pytest.mark.parametrize("day_gan, yangin_ji", [
        ("甲", "卯"), ("丙", "午"), ("戊", "午"), ("庚", "酉"), ("壬", "子"),
    ])
    def test_yang_gan_default(self, day_gan: str, yangin_ji: str):
        """양간 5종 디폴트 (옵션 A)."""
        assert is_yangin(day_gan, yangin_ji) is True
        assert is_yangin(day_gan, yangin_ji, school="jappyeong") is True

    @pytest.mark.parametrize("day_gan", ["乙", "丁", "己", "辛", "癸"])
    def test_eum_gan_no_yangin_default(self, day_gan: str):
        """옵션 A 디폴트에서 음간 양인 부재 (자평진전 정통)."""
        for ji in ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]:
            assert is_yangin(day_gan, ji) is False
            assert is_yangin(day_gan, ji, school="jappyeong") is False


class TestYanginOptionB:
    """옵션 B 명시 채택 — 삼명통회 음간 5종 확장."""

    @pytest.mark.parametrize("day_gan, yangin_ji", [
        ("乙", "辰"),
        ("丁", "未"),
        ("己", "未"),
        ("辛", "戌"),
        ("癸", "丑"),
    ])
    def test_eum_gan_option_b(self, day_gan: str, yangin_ji: str):
        """음간 5종 옵션 B 양인 매핑 (삼명통회 확장)."""
        # 옵션 A에서는 False (자평진전 비채택)
        assert is_yangin(day_gan, yangin_ji, school="jappyeong") is False
        # 옵션 B에서는 True (삼명통회 채택)
        assert is_yangin(day_gan, yangin_ji, school="samyeong") is True

    def test_yang_gan_in_option_b_still_works(self):
        """옵션 B에서도 양간 5종은 그대로 양인."""
        assert is_yangin("甲", "卯", school="samyeong") is True
        assert is_yangin("丙", "午", school="samyeong") is True

    def test_eum_gan_wrong_ji_option_b_false(self):
        """음간이라도 매핑 외 지지는 False (옵션 B)."""
        # 乙은 옵션 B에서 양인이 辰 — 다른 지지는 False
        assert is_yangin("乙", "子", school="samyeong") is False
        assert is_yangin("癸", "辰", school="samyeong") is False


class TestComputeShenshaOptionB:
    """compute_shensha의 yangin_school 인자 통합."""

    def _make_pillars(self, day_gan, day_ji, year_ji="子"):
        return {
            "year_pillar": {"gan_han": "甲", "ji_han": year_ji, "gan": "", "ji": ""},
            "month_pillar": {"gan_han": "丙", "ji_han": "寅", "gan": "", "ji": ""},
            "day_pillar": {"gan_han": day_gan, "ji_han": day_ji, "gan": "", "ji": ""},
            "hour_pillar": {"gan_han": "乙", "ji_han": "亥", "gan": "", "ji": ""},
        }

    def test_eum_gan_no_yangin_default(self):
        """乙 일주 + 辰 자체 일지 — 옵션 A에서는 양인 부재."""
        pillars = self._make_pillars("乙", "辰")
        result = compute_shensha(pillars)
        assert "辰" not in result["yangin"]

    def test_eum_gan_yangin_option_b(self):
        """乙 일주 + 辰 자체 일지 — 옵션 B에서는 양인 (음인) 매핑."""
        pillars = self._make_pillars("乙", "辰")
        result = compute_shensha(pillars, yangin_school="samyeong")
        assert "辰" in result["yangin"]

    def test_yang_gan_unchanged_between_options(self):
        """양간 사주는 옵션 A·B 동일 결과."""
        pillars = self._make_pillars("甲", "卯")
        r_a = compute_shensha(pillars)
        r_b = compute_shensha(pillars, yangin_school="samyeong")
        assert r_a["yangin"] == r_b["yangin"]


# ──────────── ADR-133 신살 강도 가중치 (Synergy Effect) ────────────


class TestSynergyWeight:
    """양인·괴강·백호 중첩 가중치 산출."""

    def test_zero_active_returns_0(self):
        """3 신살 모두 부재 → 0.0."""
        result = compute_sinsal_synergy_weight({
            "yangin": [], "goegang": [], "baekho": [],
            "cheoneul": ["丑"], "munchang": [], "yeokma": [], "dohwa": [], "kongmang": [],
        })
        assert result["active_count"] == 0
        assert result["weight"] == 0.0
        assert result["tone_branch"] == "none"

    def test_single_active_returns_1_0(self):
        """1 신살 발현 → 1.0 (성격적 톤)."""
        result = compute_sinsal_synergy_weight({
            "yangin": ["卯"], "goegang": [], "baekho": [],
            "cheoneul": [], "munchang": [], "yeokma": [], "dohwa": [], "kongmang": [],
        })
        assert result["active_count"] == 1
        assert result["weight"] == 1.0
        assert result["tone_branch"] == "single_personality"
        assert result["active_sinsals"] == ["yangin"]

    def test_dual_active_returns_1_5(self):
        """2 신살 중첩 → 1.5 (직업적 톤)."""
        result = compute_sinsal_synergy_weight({
            "yangin": ["卯"], "goegang": ["庚辰"], "baekho": [],
            "cheoneul": [], "munchang": [], "yeokma": [], "dohwa": [], "kongmang": [],
        })
        assert result["active_count"] == 2
        assert result["weight"] == 1.5
        assert result["tone_branch"] == "dual_professional"

    def test_triple_active_returns_2_0(self):
        """3 신살 모두 발현 → 2.0 (메인 동력 톤)."""
        result = compute_sinsal_synergy_weight({
            "yangin": ["卯"], "goegang": ["庚辰"], "baekho": ["甲辰"],
            "cheoneul": [], "munchang": [], "yeokma": [], "dohwa": [], "kongmang": [],
        })
        assert result["active_count"] == 3
        assert result["weight"] == 2.0
        assert result["tone_branch"] == "triple_main_engine"
        assert set(result["active_sinsals"]) == {"yangin", "goegang", "baekho"}  # type: ignore[arg-type]


class TestSynergyToneGuide:
    """SYNERGY_TONE_GUIDE 4 분기 텍스트."""

    def test_all_4_branches_present(self):
        """4 분기 키 영속화."""
        assert set(SYNERGY_TONE_GUIDE.keys()) == {
            "none", "single_personality", "dual_professional", "triple_main_engine",
        }

    def test_none_returns_empty(self):
        """none 분기 빈 문자열."""
        assert SYNERGY_TONE_GUIDE["none"] == ""

    def test_render_no_assertion_words(self):
        """모든 톤 가이드에 단정 어휘 부재 (ADR-006)."""
        for branch, text in SYNERGY_TONE_GUIDE.items():
            for assertion in ["이혼", "사망", "단명", "객사", "혈광지사", "사고사", "과부", "파산"]:
                assert assertion not in text, (
                    f"{branch}에 단정 어휘 '{assertion}' 포함: {text}"
                )

    def test_render_function_integration(self):
        """render_synergy_tone_guide 통합."""
        # 3 신살 모두 → triple_main_engine 톤
        result = render_synergy_tone_guide({
            "yangin": ["卯"], "goegang": ["庚辰"], "baekho": ["甲辰"],
            "cheoneul": [], "munchang": [], "yeokma": [], "dohwa": [], "kongmang": [],
        })
        assert "메인 동력" in result or "Main Engine" in result

    def test_render_function_empty_when_no_intense(self):
        """3 신살 모두 부재 → 빈 텍스트."""
        result = render_synergy_tone_guide({
            "yangin": [], "goegang": [], "baekho": [],
            "cheoneul": ["丑"], "munchang": [], "yeokma": [], "dohwa": [], "kongmang": [],
        })
        assert result == ""


class TestSynergyDeterministic:
    """결정론 보장."""

    def test_deterministic_same_input(self):
        """동일 입력 동일 출력."""
        sh = {
            "yangin": ["卯"], "goegang": ["庚辰"], "baekho": [],
            "cheoneul": [], "munchang": [], "yeokma": [], "dohwa": [], "kongmang": [],
        }
        r1 = compute_sinsal_synergy_weight(sh)
        r2 = compute_sinsal_synergy_weight(sh)
        assert r1 == r2
