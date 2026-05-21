"""ADR-130 회귀 — saju 삼합(三合)·방합(方合) 결정론 매칭.

학파: 자평진전(沈孝瞻 1734) · 삼명통회(萬民英 1578) 정통 표준 일치.

삼합 4국:
  - 申子辰 → 水局
  - 巳酉丑 → 金局
  - 寅午戌 → 火局
  - 亥卯未 → 木局

방합 4국:
  - 寅卯辰 → 春木 (동방)
  - 巳午未 → 夏火 (남방)
  - 申酉戌 → 秋金 (서방)
  - 亥子丑 → 冬水 (북방)
"""
from __future__ import annotations

from engine.saju.compat import (
    detect_banghap,
    detect_compat_relations,
    detect_samhap,
)


class TestSamhapDetection:
    """삼합 4국 결정론 매칭."""

    def test_suguk_samhap(self):
        """수국 申子辰."""
        result = detect_samhap(["申", "子", "辰", "卯"])
        assert len(result) == 1
        assert result[0]["label"] == "申子辰"
        assert result[0]["guk"] == "水局"
        assert result[0]["ohaeng"] == "수"

    def test_geumguk_samhap(self):
        """금국 巳酉丑."""
        result = detect_samhap(["巳", "酉", "丑", "卯"])
        assert len(result) == 1
        assert result[0]["label"] == "巳酉丑"
        assert result[0]["ohaeng"] == "금"

    def test_hwaguk_samhap(self):
        """화국 寅午戌."""
        result = detect_samhap(["寅", "午", "戌", "卯"])
        assert len(result) == 1
        assert result[0]["ohaeng"] == "화"

    def test_mokguk_samhap(self):
        """목국 亥卯未."""
        result = detect_samhap(["亥", "卯", "未", "辰"])
        assert len(result) == 1
        assert result[0]["ohaeng"] == "목"

    def test_partial_samhap_no_match(self):
        """반합(2지지만 일치) — 매칭 X (완전 3지지만 매칭)."""
        # 申子만 있고 辰 없음
        assert detect_samhap(["申", "子", "卯", "巳"]) == []
        # 寅午만 있고 戌 없음
        assert detect_samhap(["寅", "午", "亥", "辰"]) == []

    def test_empty_input(self):
        """빈 입력 빈 리스트."""
        assert detect_samhap([]) == []


class TestBanghapDetection:
    """방합 4국 결정론 매칭."""

    def test_chunmokguk_banghap(self):
        """춘목국 寅卯辰 (동방)."""
        result = detect_banghap(["寅", "卯", "辰", "子"])
        assert len(result) == 1
        assert result[0]["label"] == "寅卯辰"
        assert result[0]["guk"] == "春木"
        assert result[0]["ohaeng"] == "목"
        assert result[0]["direction"] == "동방"

    def test_hahwaguk_banghap(self):
        """하화국 巳午未 (남방)."""
        result = detect_banghap(["巳", "午", "未", "子"])
        assert len(result) == 1
        assert result[0]["ohaeng"] == "화"
        assert result[0]["direction"] == "남방"

    def test_chugeumguk_banghap(self):
        """추금국 申酉戌 (서방)."""
        result = detect_banghap(["申", "酉", "戌", "子"])
        assert len(result) == 1
        assert result[0]["ohaeng"] == "금"
        assert result[0]["direction"] == "서방"

    def test_dongsuguk_banghap(self):
        """동수국 亥子丑 (북방)."""
        result = detect_banghap(["亥", "子", "丑", "卯"])
        assert len(result) == 1
        assert result[0]["ohaeng"] == "수"
        assert result[0]["direction"] == "북방"

    def test_partial_banghap_no_match(self):
        """부분 방합 매칭 X."""
        assert detect_banghap(["寅", "卯", "子", "辰"]) != []  # 寅卯辰 매칭됨
        # 寅卯만 (辰 없음) + 子 (방합 다른 국)
        assert detect_banghap(["寅", "卯", "子", "酉"]) == []


class TestCompatRelationsIntegration:
    """detect_compat_relations 통합."""

    def test_returns_all_4_keys(self):
        """4 키 반환."""
        result = detect_compat_relations(["申", "子", "辰", "卯"])
        assert set(result.keys()) == {"samhap", "banghap", "yukhap_pairs", "yukchong_pairs"}

    def test_samhap_and_yukhap_simultaneously(self):
        """삼합 + 6합 동시 매칭."""
        # 申子辰 (삼합) + 子丑合 (6합)
        result = detect_compat_relations(["申", "子", "辰", "丑"])
        assert len(result["samhap"]) == 1  # 申子辰
        # 6합: 子丑合
        assert any("子丑" in p for p in result["yukhap_pairs"])

    def test_yukchong_detection(self):
        """6충 매칭."""
        # 子午沖
        result = detect_compat_relations(["子", "午", "卯", "未"])
        assert any("子午" in p for p in result["yukchong_pairs"])

    def test_empty_branches(self):
        """빈 입력."""
        result = detect_compat_relations([])
        assert result["samhap"] == []
        assert result["banghap"] == []
        assert result["yukhap_pairs"] == []
        assert result["yukchong_pairs"] == []


class TestDeterministicSafety:
    """ADR-006 정합 — 단정 어휘 X (결정론 매칭만)."""

    def test_samhap_result_no_assertion_words(self):
        """삼합 결과에 '결혼·이혼·사망' 단정 어휘 부재."""
        result = detect_samhap(["申", "子", "辰", "卯"])
        for r in result:
            joined = " ".join(str(v) for v in r.values())
            for assertion in ["결혼", "이혼", "사망", "단명"]:
                assert assertion not in joined

    def test_deterministic_same_input(self):
        """결정론 — 동일 입력 동일 출력."""
        r1 = detect_samhap(["申", "子", "辰", "卯"])
        r2 = detect_samhap(["申", "子", "辰", "卯"])
        assert r1 == r2

    def test_order_independence(self):
        """지지 순서 무관 (frozenset 매칭 패턴)."""
        r1 = detect_samhap(["申", "子", "辰", "卯"])
        r2 = detect_samhap(["卯", "辰", "子", "申"])
        assert r1 == r2
