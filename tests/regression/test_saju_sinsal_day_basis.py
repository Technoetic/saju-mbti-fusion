"""ADR-142 회귀 — saju 12 신살 일주 지지 기준 학파 분기.

ADR-131 한계 절 line 105 해소:
> 본 매핑은 출생 연도 지지 기준 — 일주 지지 기준 분기는 학파 분기 영역 (DEFER)

본 회귀는 명리정종 학파 (일주 기준) 옵션 B를 자평진전 학파 (연주 기준)
옵션 A와 병행 검증한다. 매핑 룰은 동일 — 기준 지지만 다름.

/domain-priorities #5 (45점) 결손 해소.
"""
from __future__ import annotations

import pytest

from engine.saju.twelve_sinsal import (
    detect_sinsal_in_pillars,
    get_sinsal_by_basis,
    get_sinsal_for_day,
    get_sinsal_for_year,
)


# 4 삼합 대표 지지 (수국·금국·화국·목국)
SAMHAP_REPRESENTATIVES = ["子", "酉", "午", "卯"]


class TestDayBasisAPI:
    """일주 기준 신규 API 동작."""

    def test_get_sinsal_for_day_callable(self):
        """get_sinsal_for_day 호출 가능."""
        result = get_sinsal_for_day("子")
        assert isinstance(result, dict)
        assert len(result) == 12

    def test_get_sinsal_for_day_returns_12_sinsals(self):
        """12 신살 모두 반환."""
        result = get_sinsal_for_day("子")
        expected = {
            "겁살", "재살", "천살", "지살", "년살", "월살",
            "망신살", "장성살", "반안살", "역마살", "육해살", "화개살",
        }
        assert set(result.keys()) == expected

    def test_get_sinsal_for_day_invalid_input(self):
        """잘못된 입력 → 빈 dict."""
        assert get_sinsal_for_day("") == {}
        assert get_sinsal_for_day("X") == {}


class TestBasisOptionEquivalence:
    """매핑 룰 동일성 — basis="year" / "day" 결과 일치 (룰 동일)."""

    @pytest.mark.parametrize("branch", SAMHAP_REPRESENTATIVES)
    def test_year_day_mapping_identical(self, branch):
        """동일 기준 지지 → 동일 12 신살 매핑."""
        year_result = get_sinsal_for_year(branch)
        day_result = get_sinsal_for_day(branch)
        assert year_result == day_result, (
            f"{branch}: 학파 분기 룰 일치 의무 깨짐"
        )

    @pytest.mark.parametrize("branch", SAMHAP_REPRESENTATIVES)
    def test_get_sinsal_by_basis_year(self, branch):
        """get_sinsal_by_basis(basis='year') = get_sinsal_for_year."""
        assert get_sinsal_by_basis(branch, basis="year") == get_sinsal_for_year(branch)

    @pytest.mark.parametrize("branch", SAMHAP_REPRESENTATIVES)
    def test_get_sinsal_by_basis_day(self, branch):
        """get_sinsal_by_basis(basis='day') = get_sinsal_for_day."""
        assert get_sinsal_by_basis(branch, basis="day") == get_sinsal_for_day(branch)

    def test_get_sinsal_by_basis_invalid(self):
        """잘못된 basis → 빈 dict."""
        assert get_sinsal_by_basis("子", basis="invalid") == {}
        assert get_sinsal_by_basis("子", basis="") == {}


class TestDetectInPillarsBasisOption:
    """detect_sinsal_in_pillars의 basis 옵션."""

    def test_default_basis_is_year(self):
        """basis 미지정 → year (ADR-131 디폴트 무회귀)."""
        default = detect_sinsal_in_pillars("子", ["子", "亥", "辰", "未"])
        explicit_year = detect_sinsal_in_pillars(
            "子", ["子", "亥", "辰", "未"], basis="year"
        )
        assert default == explicit_year

    def test_day_basis_returns_same_mapping(self):
        """basis='day' → year와 동일 매핑 (룰 동일)."""
        year_result = detect_sinsal_in_pillars(
            "子", ["子", "亥", "辰", "未"], basis="year"
        )
        day_result = detect_sinsal_in_pillars(
            "子", ["子", "亥", "辰", "未"], basis="day"
        )
        assert year_result == day_result

    def test_invalid_basis_returns_empty_lists(self):
        """잘못된 basis → 12 신살 모두 빈 리스트."""
        result = detect_sinsal_in_pillars("子", ["子"], basis="invalid")
        assert len(result) == 12
        assert all(v == [] for v in result.values())


class TestADRComplianceDayBasis:
    """ADR 정합 — 일주 기준 학파 분기."""

    def test_day_basis_yields_jangseong_correctly(self):
        """일주 子 → 장성살 = 子 (자평진전·명리정종 학파 모두 동일 룰)."""
        result = get_sinsal_for_day("子")
        assert result["장성살"]["ji"] == "子"

    def test_day_basis_yields_cheonsal_correctly(self):
        """일주 子 → 천살 = 未 (학파 동일 룰)."""
        result = get_sinsal_for_day("子")
        assert result["천살"]["ji"] == "未"

    def test_day_basis_yields_yeokma_correctly(self):
        """일주 子 → 역마살 = 寅 (학파 동일 룰)."""
        result = get_sinsal_for_day("子")
        assert result["역마살"]["ji"] == "寅"


class TestSafetyAndDeterminism:
    """결정론 + 안전성."""

    def test_deterministic(self):
        """동일 입력 → 동일 결과 (10회 반복)."""
        for _ in range(10):
            r = get_sinsal_for_day("子")
            assert r["겁살"]["ji"] == "巳"

    def test_year_day_call_independent(self):
        """get_sinsal_for_year와 get_sinsal_for_day 독립 호출 부작용 X."""
        y1 = get_sinsal_for_year("子")
        _ = get_sinsal_for_day("酉")  # 다른 삼합 — 격리 검증용 호출
        y2 = get_sinsal_for_year("子")
        assert y1 == y2, "다른 호출이 결과 변경 — 부작용 의심"

    def test_no_assertion_words_in_sinsal_han(self):
        """신살 한자 라벨에 단정 어휘 X (ADR-006 정합)."""
        forbidden = ["반드시", "확실히", "100%", "절대"]
        result = get_sinsal_for_day("子")
        for sinsal_name, data in result.items():
            for w in forbidden:
                assert w not in data["han"], (
                    f"단정 어휘 검출: {sinsal_name} {data['han']}"
                )
