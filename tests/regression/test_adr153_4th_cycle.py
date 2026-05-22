"""ADR-153 회귀 — /domain-priorities 4차 사이클 본 AI 단독 해소 4건.

대상:
  · #1 tojeong 추가 학술 출처 (김창경 2017 KCI ART002295655)
  · #11 saju 신살 시너지 학파별 분기 옵션 (standard/conservative/emphatic)
  · #16 star 호환성 144 매트릭스 점수 분포 통계
  · #10 학파 토글 UI 컴포넌트 (front/js/ui/school-toggle.js)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from engine.divination.star.compatibility import (
    compatibility_matrix_summary,
    compatibility_score_distribution,
)
from engine.divination.tojeong.scoring import (
    TOJEONG_ACADEMIC_CITATIONS,
    get_tojeong_academic_citations,
)
from engine.saju.shensha import compute_sinsal_synergy_weight


# ─────────────────────────── #1 tojeong 추가 학술 ───────────────────────────


class TestTojeongAdditionalCitation:
    """#1 — 김창경 (2017) 토정 도학사상 KCI 인용 영속."""

    def test_at_least_two_citations_now(self):
        """김수년 (2016) + 김창경 (2017) = 최소 2건."""
        assert len(TOJEONG_ACADEMIC_CITATIONS) >= 2

    def test_kim_chang_gyeong_2017_present(self):
        """김창경 (2017) KCI ART002295655 영속."""
        cs = get_tojeong_academic_citations()
        match = [c for c in cs if "김창경" in c.author_ko]
        assert len(match) == 1
        c = match[0]
        assert c.publication_year == 2017
        assert c.riss_control_no == "ART002295655"
        assert "도학사상" in c.title_ko or "이지함" in c.title_ko


# ─────────────────────────── #11 saju 시너지 학파 ───────────────────────────


class TestSinsalSynergySchoolOption:
    """#11 — 신살 시너지 학파 분기 (ADR-153 신규)."""

    def test_standard_default_no_regression(self):
        """디폴트 호출 = standard 학파 (ADR-133 호환)."""
        r = compute_sinsal_synergy_weight({"yangin": ["卯"]})
        assert r["weight"] == 1.0  # standard
        assert r["school"] == "standard"

    def test_conservative_school_weights(self):
        """보수 학파 — 0.8/1.4/1.8."""
        r1 = compute_sinsal_synergy_weight({"yangin": ["卯"]}, school="conservative")
        assert r1["weight"] == 0.8
        r2 = compute_sinsal_synergy_weight(
            {"yangin": ["卯"], "goegang": ["戊辰"]}, school="conservative"
        )
        assert r2["weight"] == 1.4
        r3 = compute_sinsal_synergy_weight(
            {"yangin": ["卯"], "goegang": ["戊辰"], "baekho": ["甲辰"]},
            school="conservative",
        )
        assert r3["weight"] == 1.8

    def test_emphatic_school_weights(self):
        """강조 학파 — 1.2/1.8/2.5."""
        r1 = compute_sinsal_synergy_weight({"yangin": ["卯"]}, school="emphatic")
        assert r1["weight"] == 1.2
        r3 = compute_sinsal_synergy_weight(
            {"yangin": ["卯"], "goegang": ["戊辰"], "baekho": ["甲辰"]},
            school="emphatic",
        )
        assert r3["weight"] == 2.5

    def test_invalid_school_fallback_to_standard(self):
        """잘못된 school → standard 디폴트 fallback (안전)."""
        r = compute_sinsal_synergy_weight({"yangin": ["卯"]}, school="invalid")
        assert r["weight"] == 1.0
        assert r["school"] == "standard"

    def test_school_field_in_result(self):
        """모든 결과에 school 필드 명시."""
        r = compute_sinsal_synergy_weight({"yangin": ["卯"]})
        assert "school" in r


# ─────────────────────────── #16 star 통계 영속 ───────────────────────────


class TestStarScoreDistribution:
    """#16 — 144 매트릭스 점수 분포 통계."""

    def test_distribution_keys(self):
        """필수 필드: min·max·mean·median·stdev·p25·p75."""
        d = compatibility_score_distribution()
        for key in ("min", "max", "mean", "median", "stdev", "p25", "p75"):
            assert key in d, f"필드 '{key}' 누락"

    def test_score_range_within_45_to_85(self):
        """점수 범위 [45, 85] (ADR-148 베이스라인)."""
        d = compatibility_score_distribution()
        assert d["min"] >= 45.0
        assert d["max"] <= 85.0

    def test_mean_median_reasonable(self):
        """평균·중앙값 [55, 75] 범위 (정합 분포)."""
        d = compatibility_score_distribution()
        assert 55 <= d["mean"] <= 75
        assert 55 <= d["median"] <= 75

    def test_stdev_positive(self):
        """표준편차 > 0 (다양성 보장)."""
        d = compatibility_score_distribution()
        assert d["stdev"] > 0

    def test_p25_p75_ordered(self):
        """p25 ≤ p75 (사분위 정렬)."""
        d = compatibility_score_distribution()
        assert d["p25"] <= d["p75"]

    def test_total_matches_144(self):
        """기존 summary total = 144 무회귀."""
        s = compatibility_matrix_summary()
        assert s["total"] == 144


# ─────────────────────────── #10 학파 토글 UI ───────────────────────────


class TestSchoolToggleUI:
    """#10 — 학파 토글 UI 컴포넌트 영속."""

    @pytest.fixture
    def school_toggle_path(self):
        return Path("front/js/ui/school-toggle.js")

    @pytest.fixture
    def school_toggle_css_path(self):
        return Path("front/styles/school-toggle.css")

    def test_school_toggle_module_exists(self, school_toggle_path):
        """front/js/ui/school-toggle.js 신규 모듈 영속."""
        assert school_toggle_path.exists()

    def test_school_toggle_css_exists(self, school_toggle_css_path):
        """front/styles/school-toggle.css 영속."""
        assert school_toggle_css_path.exists()

    def test_render_function_exported(self, school_toggle_path):
        """renderSchoolToggle export."""
        src = school_toggle_path.read_text(encoding="utf-8")
        assert "export function renderSchoolToggle" in src

    def test_4_preset_options_exported(self, school_toggle_path):
        """4 학파 옵션 풀 export."""
        src = school_toggle_path.read_text(encoding="utf-8")
        expected = [
            "SAJU_GUK_STRENGTH_OPTIONS",
            "SAJU_SINSAL_BASIS_OPTIONS",
            "YUTJEOM_SCHOOL_OPTIONS",
            "SAJU_SYNERGY_SCHOOL_OPTIONS",
        ]
        for opt in expected:
            assert f"export const {opt}" in src, f"'{opt}' export 누락"

    def test_default_marker_in_options(self, school_toggle_path):
        """옵션에 isDefault: true 마커 명시."""
        src = school_toggle_path.read_text(encoding="utf-8")
        assert "isDefault: true" in src
        assert "isDefault: false" in src

    def test_disclaimer_in_module(self, school_toggle_path):
        """모듈에 면책 텍스트 자동 포함 (ADR-006)."""
        src = school_toggle_path.read_text(encoding="utf-8")
        assert "단정 X" in src or "참고용" in src
        assert "ADR-006" in src

    def test_no_assertion_words_in_descriptions(self, school_toggle_path):
        """옵션 description에 단정 어휘 0건 (description 라인만)."""
        src = school_toggle_path.read_text(encoding="utf-8")
        # description 라인 추출
        desc_lines = [
            ln for ln in src.split("\n")
            if "description:" in ln
        ]
        desc_text = "\n".join(desc_lines)
        forbidden = ["반드시", "확실히", "100%", "절대"]
        for w in forbidden:
            assert w not in desc_text, (
                f"description에 단정 어휘 '{w}' 검출 — ADR-006 위반"
            )

    def test_css_school_toggle_class_present(self, school_toggle_css_path):
        """CSS에 .school-toggle 핵심 클래스 영속."""
        src = school_toggle_css_path.read_text(encoding="utf-8")
        assert ".school-toggle " in src or ".school-toggle{" in src
        assert ".school-toggle-btn" in src
        assert ".school-toggle-btn-active" in src
