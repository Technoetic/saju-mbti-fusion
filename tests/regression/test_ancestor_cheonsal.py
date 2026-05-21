"""ADR-122 천살(天殺) 방위 결정론 회귀.

학술 근거: 메트로신문 김상회 (2021-12-12) + 한국 사주명리 십이신살 정통.

매핑 검증:
  - 申子辰 (수국) → 未 (남남서, 210도)
  - 巳酉丑 (금국) → 辰 (동남동, 120도)
  - 寅午戌 (화국) → 丑 (북북동, 30도)
  - 亥卯未 (목국) → 戌 (서북서, 300도)
"""
from __future__ import annotations

import pytest

from engine.divination.ancestor.cheonsal import (
    CHEONSAL_DIRECTIONS_BY_YEAR_JI,
    get_cheonsal_direction,
)


class TestCheonsalSugukSamhap:
    """수국 삼합 申子辰 → 未 (남남서)."""

    @pytest.mark.parametrize("year_ji", ["申", "子", "辰"])
    def test_suguk_returns_mi(self, year_ji: str) -> None:
        result = get_cheonsal_direction(year_ji)
        assert result["cheonsal_ji"] == "未"
        assert result["direction_ko"] == "남남서"
        assert result["direction_degree"] == 210
        assert result["samhap"] == "申子辰"


class TestCheonsalGeumgukSamhap:
    """금국 삼합 巳酉丑 → 辰 (동남동)."""

    @pytest.mark.parametrize("year_ji", ["巳", "酉", "丑"])
    def test_geumguk_returns_jin(self, year_ji: str) -> None:
        result = get_cheonsal_direction(year_ji)
        assert result["cheonsal_ji"] == "辰"
        assert result["direction_ko"] == "동남동"
        assert result["direction_degree"] == 120
        assert result["samhap"] == "巳酉丑"


class TestCheonsalHwagukSamhap:
    """화국 삼합 寅午戌 → 丑 (북북동)."""

    @pytest.mark.parametrize("year_ji", ["寅", "午", "戌"])
    def test_hwaguk_returns_chuk(self, year_ji: str) -> None:
        result = get_cheonsal_direction(year_ji)
        assert result["cheonsal_ji"] == "丑"
        assert result["direction_ko"] == "북북동"
        assert result["direction_degree"] == 30
        assert result["samhap"] == "寅午戌"


class TestCheonsalMokgukSamhap:
    """목국 삼합 亥卯未 → 戌 (서북서)."""

    @pytest.mark.parametrize("year_ji", ["亥", "卯", "未"])
    def test_mokguk_returns_sul(self, year_ji: str) -> None:
        result = get_cheonsal_direction(year_ji)
        assert result["cheonsal_ji"] == "戌"
        assert result["direction_ko"] == "서북서"
        assert result["direction_degree"] == 300
        assert result["samhap"] == "亥卯未"


class TestCheonsalDeterministic:
    """결정론 보장 — 동일 입력 동일 출력 + 12 지지 풀 영속화."""

    def test_pool_completeness(self) -> None:
        """12 지지 한자 풀 영속화 — 모든 지지가 매핑됨."""
        expected = {"子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"}
        assert set(CHEONSAL_DIRECTIONS_BY_YEAR_JI.keys()) == expected

    def test_deterministic_same_input(self) -> None:
        """동일 입력 동일 출력."""
        r1 = get_cheonsal_direction("子")
        r2 = get_cheonsal_direction("子")
        assert r1 == r2

    def test_invalid_ji_raises(self) -> None:
        """12 지지 외 입력 시 ValueError."""
        with pytest.raises(ValueError):
            get_cheonsal_direction("X")

    def test_disclaimer_present(self) -> None:
        """모든 출력에 면책 의무 포함 (ADR-006)."""
        result = get_cheonsal_direction("子")
        assert "참고용" in str(result["disclaimer"])
        assert "단독 근거" in str(result["disclaimer"])

    def test_school_present(self) -> None:
        """학파 출처 명시 (ADR-010)."""
        result = get_cheonsal_direction("子")
        assert "사주명리" in str(result["school"])
        assert "십이신살" in str(result["school"])
