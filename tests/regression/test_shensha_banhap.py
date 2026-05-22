"""ADR-140 회귀 — saju 지지 반합(半合) 약합 매칭.

학파: 자평진전(沈孝瞻 1734) · 삼명통회(萬民英 1578) 정통 표준 일치 (학파 분쟁 없음).

반합 8쌍 (왕지 子午卯酉 포함 2지지 약합):
  - 火局 (寅午戌): 寅午 · 午戌
  - 木局 (亥卯未): 亥卯 · 卯未
  - 水局 (申子辰): 申子 · 子辰
  - 金局 (巳酉丑): 巳酉 · 酉丑

ADR-130 detect_samhap()(완전 3지지 strength=1.0)와 의도적 분리.
半合 strength=0.5 (약합).

출처:
  - 자평진전 ISBN 9791196084417 (범진 직역, 박영창·김미석 2018)
  - 삼명통회 ISBN 9791139035261·9791137216822
  - 외부 보고서 「월하몽 도메인 지식 보강 가이드 v7」 §1.2
"""
from __future__ import annotations

from engine.saju.shensha import detect_banhap, is_banhap_pair


class TestBanhapHwaguk:
    """火局 반합 (寅午戌)."""

    def test_inoh_banhap(self):
        """寅午 반합."""
        result = detect_banhap(["寅", "午", "卯", "丑"])
        assert len(result) == 1
        assert result[0]["label"] == "寅午"
        assert result[0]["ohaeng"] == "화"
        assert result[0]["guk_full"] == "寅午戌"
        assert result[0]["strength"] == 0.5

    def test_ohsul_banhap(self):
        """午戌 반합."""
        result = detect_banhap(["午", "戌", "卯", "丑"])
        assert len(result) == 1
        assert result[0]["label"] == "午戌"
        assert result[0]["ohaeng"] == "화"
        assert result[0]["strength"] == 0.5


class TestBanhapMokguk:
    """木局 반합 (亥卯未)."""

    def test_haemyo_banhap(self):
        """亥卯 반합."""
        result = detect_banhap(["亥", "卯", "子", "丑"])
        assert len(result) == 1
        assert result[0]["label"] == "亥卯"
        assert result[0]["ohaeng"] == "목"

    def test_myomi_banhap(self):
        """卯未 반합."""
        result = detect_banhap(["卯", "未", "子", "丑"])
        assert len(result) == 1
        assert result[0]["label"] == "卯未"
        assert result[0]["ohaeng"] == "목"


class TestBanhapSuguk:
    """水局 반합 (申子辰)."""

    def test_shinja_banhap(self):
        """申子 반합."""
        result = detect_banhap(["申", "子", "寅", "丑"])
        assert len(result) == 1
        assert result[0]["label"] == "申子"
        assert result[0]["ohaeng"] == "수"

    def test_jajin_banhap(self):
        """子辰 반합."""
        result = detect_banhap(["子", "辰", "寅", "丑"])
        assert len(result) == 1
        assert result[0]["label"] == "子辰"
        assert result[0]["ohaeng"] == "수"


class TestBanhapGeumguk:
    """金局 반합 (巳酉丑)."""

    def test_sayou_banhap(self):
        """巳酉 반합."""
        result = detect_banhap(["巳", "酉", "卯", "寅"])
        assert len(result) == 1
        assert result[0]["label"] == "巳酉"
        assert result[0]["ohaeng"] == "금"

    def test_youchuk_banhap(self):
        """酉丑 반합."""
        result = detect_banhap(["酉", "丑", "卯", "寅"])
        assert len(result) == 1
        assert result[0]["label"] == "酉丑"
        assert result[0]["ohaeng"] == "금"


class TestBanhapEdgeCases:
    """경계 케이스."""

    def test_no_banhap(self):
        """반합 0건."""
        result = detect_banhap(["子", "丑", "寅", "卯"])
        # 子辰·寅午·亥卯·巳酉 모두 미성립
        # 子丑·寅卯는 6합·방합 영역
        assert result == []

    def test_multiple_banhap(self):
        """4지지에 반합 2쌍 동시 매칭 (申子 + 寅午)."""
        result = detect_banhap(["申", "子", "寅", "午"])
        assert len(result) == 2
        labels = {r["label"] for r in result}
        assert labels == {"申子", "寅午"}

    def test_order_invariance(self):
        """지지 순서 무관."""
        result_a = detect_banhap(["寅", "午", "亥", "丑"])
        result_b = detect_banhap(["午", "丑", "寅", "亥"])
        assert len(result_a) == len(result_b) == 1
        assert result_a[0]["label"] == result_b[0]["label"] == "寅午"

    def test_three_branches_only(self):
        """3지지만 (4주 아닌 경우) 반합 검출."""
        result = detect_banhap(["亥", "卯", "巳"])
        assert len(result) == 1
        assert result[0]["label"] == "亥卯"

    def test_strength_always_half(self):
        """반합 강도는 항상 0.5 (ADR-140 정의)."""
        for branches in (
            ["寅", "午", "丑", "子"],
            ["亥", "卯", "申", "酉"],
            ["申", "子", "寅", "卯"],
            ["巳", "酉", "亥", "戌"],
        ):
            result = detect_banhap(branches)
            for r in result:
                assert r["strength"] == 0.5


class TestIsBanhapPair:
    """is_banhap_pair() 헬퍼 API."""

    def test_all_eight_pairs_true(self):
        """반합 8쌍 모두 True."""
        pairs = [
            ("寅", "午"), ("午", "戌"),
            ("亥", "卯"), ("卯", "未"),
            ("申", "子"), ("子", "辰"),
            ("巳", "酉"), ("酉", "丑"),
        ]
        for ji1, ji2 in pairs:
            assert is_banhap_pair(ji1, ji2), f"{ji1}{ji2} 반합 미검출"
            assert is_banhap_pair(ji2, ji1), f"{ji2}{ji1} 순서 변경 미검출"

    def test_non_banhap_false(self):
        """반합 아닌 쌍 False."""
        # 6합·방합·기타
        non_pairs = [
            ("子", "丑"),  # 子丑 6합 (土)
            ("寅", "卯"),  # 방합 木 일부
            ("申", "酉"),  # 방합 金 일부
            ("子", "午"),  # 子午 6충
            ("辰", "戌"),  # 辰戌 6충
        ]
        for ji1, ji2 in non_pairs:
            assert not is_banhap_pair(ji1, ji2), f"{ji1}{ji2} 반합 오검출"

    def test_samhap_full_three_not_pair(self):
        """완전 삼합 3지지는 pair API 영역 외."""
        # 申子辰 완전 삼합은 detect_samhap() (ADR-130) 담당
        # 但 申子·子辰 각각은 半合 쌍이므로 True
        assert is_banhap_pair("申", "子")
        assert is_banhap_pair("子", "辰")
        # 申辰은 半合 X (왕지 子 부재)
        assert not is_banhap_pair("申", "辰")
