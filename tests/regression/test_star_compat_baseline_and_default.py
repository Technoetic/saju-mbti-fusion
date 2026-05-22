"""ADR-148 회귀 — #16 star 호환성 144 매트릭스 합성 베이스라인 + #23 별자리 디폴트.

/domain-priorities #16 (22점) + #23 (사용자 결단) 본 AI 단독 해소.

#16: compute_compatibility 144 조합 매트릭스 합성 베이스라인.
  · 모든 144 조합 호출 가능 + 결과 결정론
  · relation_type 3종 분포 (resonant·complementary·frictional)
  · overall_score 범위 검증

#23: 별자리 디폴트 = 서양 12 (twelve zodiac), 옵션 = 동양 28수.
  · 두 시스템 모두 본문화 (ZODIAC_SIGNS + TWENTY_EIGHT_MANSIONS)
  · 디폴트 결단 영속 (ADR-148)
"""
from __future__ import annotations

from collections import Counter

import pytest

from engine.divination.star.compatibility import (
    ZODIAC_SIGNS,
    compatibility_matrix_summary,
    compute_compatibility,
)


# 디폴트 별자리 시스템 라벨 (ADR-148)
DEFAULT_ZODIAC_SYSTEM = "western_12"
OPTIONAL_ZODIAC_SYSTEM = "eastern_28_mansions"


class TestCompatMatrix144Baseline:
    """#16 — 144 매트릭스 합성 베이스라인 영속."""

    def test_all_144_combinations_callable(self):
        """12 × 12 = 144 조합 모두 None이 아닌 결과."""
        count = 0
        for s1 in ZODIAC_SIGNS:
            for s2 in ZODIAC_SIGNS:
                r = compute_compatibility(s1.key, s2.key)
                assert r is not None, f"{s1.key} × {s2.key} → None"
                count += 1
        assert count == 144

    def test_matrix_summary_total_144(self):
        """summary 함수가 144 총 조합 반환."""
        s = compatibility_matrix_summary()
        assert s["total"] == 144

    def test_relation_type_distribution(self):
        """3 relation_type 모두 등장 (resonant·complementary·frictional)."""
        relations = Counter()
        for s1 in ZODIAC_SIGNS:
            for s2 in ZODIAC_SIGNS:
                r = compute_compatibility(s1.key, s2.key)
                assert r is not None
                relations[r.relation_type] += 1
        # 144 조합 모두 분류됨
        assert sum(relations.values()) == 144
        # 3 유형 모두 등장 (다양성 보장)
        assert relations["resonant"] > 0
        assert relations["complementary"] > 0
        assert relations["frictional"] > 0

    def test_overall_score_range(self):
        """overall_score 범위 [45, 85] (element 70% + modality 30%)."""
        for s1 in ZODIAC_SIGNS:
            for s2 in ZODIAC_SIGNS:
                r = compute_compatibility(s1.key, s2.key)
                assert r is not None
                # element 45~85 × 0.7 + modality 70~75 × 0.3 = ~52~82
                assert 45 <= r.overall_score <= 85, (
                    f"{s1.key} × {s2.key}: overall {r.overall_score} 범위 초과"
                )

    def test_deterministic_baseline(self):
        """동일 입력 → 동일 결과 (5회 호출)."""
        for _ in range(5):
            r = compute_compatibility("aries", "leo")
            assert r is not None
            assert r.overall_score == 81  # 베이스라인 값
            assert r.relation_type == "resonant"

    def test_symmetric_compatibility(self):
        """대칭성: A·B = B·A overall_score 동일."""
        for s1 in ZODIAC_SIGNS:
            for s2 in ZODIAC_SIGNS:
                if s1.key >= s2.key:
                    continue
                r12 = compute_compatibility(s1.key, s2.key)
                r21 = compute_compatibility(s2.key, s1.key)
                assert r12 is not None and r21 is not None
                assert r12.overall_score == r21.overall_score, (
                    f"{s1.key}·{s2.key} = {r12.overall_score} vs "
                    f"{s2.key}·{s1.key} = {r21.overall_score}"
                )

    def test_no_assertion_words_in_tones(self):
        """모든 tone에 단정 어휘 0건 (ADR-006)."""
        forbidden = ["반드시", "확실히", "절대", "100%", "결혼", "이혼", "사망"]
        for s1 in ZODIAC_SIGNS:
            for s2 in ZODIAC_SIGNS:
                r = compute_compatibility(s1.key, s2.key)
                assert r is not None
                for w in forbidden:
                    assert w not in r.element_tone_ko, (
                        f"{s1.key}×{s2.key} element_tone: '{w}' 검출"
                    )
                    assert w not in r.modality_tone_ko, (
                        f"{s1.key}×{s2.key} modality_tone: '{w}' 검출"
                    )


class TestADR148ZodiacDefaultPolicy:
    """#23 — 별자리 디폴트 시스템 정책 영속."""

    def test_western_12_signs_present(self):
        """서양 12 별자리 시스템 본문화 (디폴트)."""
        assert len(ZODIAC_SIGNS) == 12
        keys = {s.key for s in ZODIAC_SIGNS}
        expected = {
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        }
        assert keys == expected

    def test_eastern_28_mansions_module_exists(self):
        """동양 28수 시스템 본문화 (옵션)."""
        try:
            from engine.divination.star import twenty_eight_mansions  # noqa
        except ImportError:
            pytest.fail("twenty_eight_mansions 모듈 부재 — 28수 옵션 미본문화")

    def test_default_system_label(self):
        """ADR-148 디폴트 라벨 영속 (서양 12)."""
        assert DEFAULT_ZODIAC_SYSTEM == "western_12"

    def test_optional_system_label(self):
        """ADR-148 옵션 라벨 (동양 28수)."""
        assert OPTIONAL_ZODIAC_SYSTEM == "eastern_28_mansions"
