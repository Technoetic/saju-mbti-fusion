"""ADR-126 본문화 회귀 — 214 부수 디폴트 자원오행 (이재승 2024 KCI).

학술 근거: 이재승 (2024) 인명 한자 214 부수의 자원에 의한 성명학적 오행 배속
KCI DSpace ID 2187321.
"""
from __future__ import annotations

from engine.divination.name.unihan import radical_default_ohaeng


# 보고서 §6 radical_mapping_214 라인 217~244 본문 명시 7 부수
EXPECTED_RADICAL_DEFAULTS = {
    75: "목",   # 木 (나무 목)
    85: "수",   # 水 (물 수 — 氵 동일)
    86: "화",   # 火 (불 화 — 灬 동일)
    32: "토",   # 土 (흙 토)
    167: "금",  # 金 (쇠 금)
    140: "목",  # 艸 (풀 초)
    18: "금",   # 刀 (칼 도)
}


class TestRadicalDefaultMapping:
    """본문 명시 7 부수 디폴트 매핑 영속화."""

    def test_all_7_radicals_mapped(self):
        """7 부수 모두 디폴트 자원오행 명시."""
        for radical_num, expected in EXPECTED_RADICAL_DEFAULTS.items():
            actual = radical_default_ohaeng(radical_num)
            assert actual == expected, (
                f"부수 {radical_num}: 기대 {expected}, 실제 {actual}"
            )

    def test_unmapped_radical_returns_none(self):
        """본문 미명시 부수 None (가짜 확장 차단 — ADR-010)."""
        # 부수 102 (田) — 본문에 부수로 매핑되지 않음 (田 한자만 매핑됨)
        assert radical_default_ohaeng(102) is None
        # 부수 1 (一) — 본문 미명시
        assert radical_default_ohaeng(1) is None
        # 부수 214 — 본문 미명시
        assert radical_default_ohaeng(214) is None

    def test_invalid_input_returns_none(self):
        """잘못된 입력 None 반환."""
        assert radical_default_ohaeng(0) is None
        assert radical_default_ohaeng(215) is None
        assert radical_default_ohaeng(-1) is None


class TestRadicalDeterministic:
    """결정론 보장."""

    def test_deterministic_same_input(self):
        """동일 입력 동일 출력."""
        for radical_num in EXPECTED_RADICAL_DEFAULTS.keys():
            r1 = radical_default_ohaeng(radical_num)
            r2 = radical_default_ohaeng(radical_num)
            assert r1 == r2

    def test_no_extension_beyond_report(self):
        """보고서 본문 명시 외 부수는 매핑 없음 (가짜 확장 차단)."""
        # 본문에 명시되지 않은 부수 풀에서 5건 sample 점검
        for radical_num in [9, 10, 60, 100, 200]:
            assert radical_default_ohaeng(radical_num) is None
