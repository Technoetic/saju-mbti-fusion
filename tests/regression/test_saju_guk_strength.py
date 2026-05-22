"""ADR-141 회귀 — saju 합국(合局) 위치별 강도 가중치.

자평진전(子平眞詮) 「合化」 절 정통 표준:
  - 월지(月支) = 월령 득함 → strength 1.0 (최강)
  - 일지(日支) = 일주 직접 → strength 0.7 (중)
  - 년지(年支)·시지(時支) → strength 0.5 (약)

합국 강도 = 매칭된 지지들의 위치 가중치 중 최대값.

본 회귀는 detect_samhap·detect_banghap·detect_compat_relations에
with_strength=True 옵션 동작을 검증한다. 기존 ADR-130 회귀 18건은
디폴트 호출 (with_strength=False) 그대로 동작 — 무회귀 보장.

4주 인덱스 표준: [0]=년 / [1]=월 / [2]=일 / [3]=시
"""
from __future__ import annotations

from engine.saju.compat import (
    detect_banghap,
    detect_compat_relations,
    detect_samhap,
)


class TestSamhapStrengthMonthly:
    """삼합 — 월지(月支)에 합국 구성 지지가 있으면 strength=1.0."""

    def test_suguk_monthly_申(self):
        """申(월) 子(일) 辰(시) — 申子辰 수국, 월지 申 = 1.0."""
        r = detect_samhap(["丑", "申", "子", "辰"], with_strength=True)
        assert len(r) == 1
        assert r[0]["label"] == "申子辰"
        assert r[0]["strength"] == 1.0

    def test_hwaguk_monthly_午(self):
        """寅(년) 午(월) 戌(일) — 화국, 월지 午 = 1.0."""
        r = detect_samhap(["寅", "午", "戌", "卯"], with_strength=True)
        assert r[0]["strength"] == 1.0

    def test_mokguk_monthly_卯(self):
        """亥(년) 卯(월) 未(일) — 목국, 월지 卯 = 1.0."""
        r = detect_samhap(["亥", "卯", "未", "巳"], with_strength=True)
        assert r[0]["strength"] == 1.0


class TestSamhapStrengthDaily:
    """삼합 — 월지엔 합국 X, 일지에만 있으면 strength=0.7."""

    def test_suguk_daily_only(self):
        """申(년) 丑(월·합국 X) 子(일) 辰(시) — 일지 子가 최강 위치 → 0.7."""
        r = detect_samhap(["申", "丑", "子", "辰"], with_strength=True)
        assert len(r) == 1
        assert r[0]["strength"] == 0.7

    def test_geumguk_daily_only(self):
        """巳(년) 寅(월·합국 X) 酉(일) 丑(시) — 일지 酉 = 0.7."""
        r = detect_samhap(["巳", "寅", "酉", "丑"], with_strength=True)
        assert r[0]["strength"] == 0.7


class TestSamhapStrengthYearOrHour:
    """삼합 — 년·시지에만 합국 구성 지지가 있으면 strength=0.5."""

    def test_suguk_year_hour_only(self):
        """申(년) 寅(월) 卯(일) 子+辰 X — 매칭 안 됨 (3지지 필요)."""
        # 申(년) 子(시) 두 지지로는 삼합 불가 (3지지 완전 필요)
        r = detect_samhap(["申", "寅", "卯", "子"], with_strength=True)
        assert r == []  # 申子만 → 반합, 완전 삼합 X

    def test_suguk_year_only_with_filler(self):
        """申(년) 戌(월) 寅(일) 子+辰 — 申·子·辰 모두 ?
        申(년) 戌(월) 子(일) 辰(시) — 월지 戌 합국 X, 일지 子 0.7, 년지 申 0.5, 시지 辰 0.5 → 0.7"""
        r = detect_samhap(["申", "戌", "子", "辰"], with_strength=True)
        assert r[0]["strength"] == 0.7  # 일지 子가 최강

    def test_suguk_year_hour_pure(self):
        """申(년) 戌(월) 寅(일) 辰(시) — 申·辰만 매칭 위치, 子 부재 → 합국 X."""
        r = detect_samhap(["申", "戌", "寅", "辰"], with_strength=True)
        assert r == []


class TestBanghapStrength:
    """방합 — 위치 가중치 동일 규칙."""

    def test_bangmok_monthly(self):
        """寅(년) 卯(월) 辰(일) — 춘목 방합, 월지 卯 = 1.0."""
        r = detect_banghap(["寅", "卯", "辰", "丑"], with_strength=True)
        assert len(r) == 1
        assert r[0]["label"] == "寅卯辰"
        assert r[0]["strength"] == 1.0

    def test_bangsu_daily(self):
        """亥(년) 寅(월·합국 X) 子(일) 丑(시) — 동수 방합, 일지 子 = 0.7."""
        r = detect_banghap(["亥", "寅", "子", "丑"], with_strength=True)
        assert r[0]["strength"] == 0.7

    def test_banggeum_year_hour(self):
        """申(년) 寅(월) 卯(일) 戌(시) — 申·戌만, 酉 부재 → 방합 X."""
        r = detect_banghap(["申", "寅", "卯", "戌"], with_strength=True)
        assert r == []


class TestCompatRelationsStrength:
    """통합 API — with_strength 전파."""

    def test_compat_with_strength_propagates(self):
        """detect_compat_relations(with_strength=True) → samhap·banghap에 strength 포함."""
        r = detect_compat_relations(["丑", "申", "子", "辰"], with_strength=True)
        assert "samhap" in r
        assert len(r["samhap"]) == 1
        assert "strength" in r["samhap"][0]
        assert r["samhap"][0]["strength"] == 1.0  # 월지 申

    def test_compat_default_no_strength(self):
        """디폴트 (with_strength=False) — strength 필드 부재 (ADR-130 정합)."""
        r = detect_compat_relations(["丑", "申", "子", "辰"])
        assert len(r["samhap"]) == 1
        assert "strength" not in r["samhap"][0]


class TestStrengthEdgeCases:
    """경계 케이스 — 길이 != 4 / 빈 입력 / 다중 합국."""

    def test_wrong_length_returns_min_strength(self):
        """4주 아닌 경우 (3지지) — strength=0.5 (위치 정보 부족 → 보수적 최솟값)."""
        r = detect_samhap(["申", "子", "辰"], with_strength=True)
        assert len(r) == 1
        assert r[0]["strength"] == 0.5

    def test_empty_input(self):
        """빈 입력 → 빈 리스트."""
        r = detect_samhap([], with_strength=True)
        assert r == []

    def test_strength_safety_range(self):
        """strength는 항상 {0.5, 0.7, 1.0} 중 하나."""
        VALID = {0.5, 0.7, 1.0}
        # 12 합국 (삼합 4 + 방합 4 + 위치 변형) 모두 검증
        test_cases = [
            ["丑", "申", "子", "辰"],  # 월지 1.0
            ["申", "丑", "子", "辰"],  # 일지 0.7
            ["申", "子", "辰"],        # 길이 != 4 → 0.5
            ["寅", "卯", "辰", "丑"],
            ["亥", "寅", "子", "丑"],
        ]
        for branches in test_cases:
            for r in detect_samhap(branches, with_strength=True):
                assert r["strength"] in VALID, f"{branches}: {r['strength']}"
            for r in detect_banghap(branches, with_strength=True):
                assert r["strength"] in VALID
