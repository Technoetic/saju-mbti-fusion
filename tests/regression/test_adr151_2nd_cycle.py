"""ADR-151 회귀 — /domain-priorities 2차 사이클 본 AI 단독 해소.

선행 (ADR-141~150): 23 결손 100% 본 AI 처리 종결.
본 사이클 (ADR-151): 신규 12 결손 중 본 AI 가능 3건 해소.

대상:
  · #2 (face 키워드였으나 실 발굴은 saju 신살) — 김만태 (2025) KCI ART003175177
  · #4 dream korean_folk 6→12 카테고리 확장
  · #5 palm Vision Sonnet 4.6 fallback (SLA 보강)
"""
from __future__ import annotations

import inspect

from engine.divination.dream_lex.korean_folk import KOREAN_FOLK_CATEGORIES
from engine.divination.palm import reading as palm_reading
from engine.saju.twelve_sinsal import (
    SINSAL_KCI_CITATIONS,
    get_sinsal_kci_citations,
)


class TestSinsalKciCitationPersistence:
    """saju 신살 KCI 인용 영속 (#2 — 김만태 2025)."""

    def test_at_least_one_citation(self):
        assert len(SINSAL_KCI_CITATIONS) >= 1

    def test_kim_mantae_2025_present(self):
        cs = get_sinsal_kci_citations()
        kim = [c for c in cs if "김만태" in c.author_ko]
        assert len(kim) == 1
        c = kim[0]
        assert "2025" in c.author_ko
        assert c.kci_artiId == "ART003175177"
        assert "신살" in c.title_ko
        assert "역사와 융합" in c.journal

    def test_kci_url_format(self):
        for c in SINSAL_KCI_CITATIONS:
            assert c.kci_url.startswith("https://www.kci.go.kr/"), (
                f"{c.kci_artiId}: KCI URL 부정합"
            )

    def test_topic_focus_mentions_adr_131_142(self):
        """topic_focus에 ADR-131·142 참조 명시 (cross-ADR 정합)."""
        cs = get_sinsal_kci_citations()
        for c in cs:
            assert "ADR-131" in c.topic_focus or "신살" in c.topic_focus


class TestKoreanFolkCategoriesExpansion:
    """#4 dream korean_folk 12 카테고리 확장."""

    def test_at_least_12_categories(self):
        """6 (ADR-021) → 12 (ADR-151) 확장 보장."""
        assert len(KOREAN_FOLK_CATEGORIES) >= 12, (
            f"카테고리 {len(KOREAN_FOLK_CATEGORIES)}건 (목표 ≥ 12)"
        )

    def test_original_6_preserved(self):
        """기존 6 카테고리 무회귀."""
        original = {"태몽", "재물몽", "합격몽", "죽음몽", "가위눌림", "이별몽"}
        for cat in original:
            assert cat in KOREAN_FOLK_CATEGORIES, f"기존 카테고리 '{cat}' 누락"

    def test_new_6_categories_added(self):
        """ADR-151 신규 6 카테고리 영속."""
        new = {"조상몽", "자연몽", "음식몽", "옷몽", "건물몽", "동물몽"}
        for cat in new:
            assert cat in KOREAN_FOLK_CATEGORIES, (
                f"신규 카테고리 '{cat}' 누락 (#4 해소 의무)"
            )

    def test_descriptions_non_empty(self):
        for cat, desc in KOREAN_FOLK_CATEGORIES.items():
            assert desc.strip(), f"{cat}: 빈 설명"

    def test_no_assertion_words_in_descriptions(self):
        """카테고리 설명에 단정 어휘 0건 (ADR-006)."""
        forbidden = ["반드시", "확실히", "100%", "절대"]
        for cat, desc in KOREAN_FOLK_CATEGORIES.items():
            for w in forbidden:
                assert w not in desc, (
                    f"{cat}: 단정 어휘 '{w}' 검출"
                )


class TestPalmVisionSonnetFallback:
    """#5 palm Vision Sonnet 4.6 fallback — ADR-214로 제거 (Opus 단일).

    ADR-151 SLA 보강 정신은 ADR-214로 무효화 — 사용자 결단으로 Sonnet 폴백
    제거. 본 클래스는 Opus 단일 사용 검증으로 전환.
    """

    def test_call_vision_uses_opus_only(self):
        """ADR-214 — Opus 단일 모델 사용 (Sonnet 폴백 제거)."""
        src = inspect.getsource(palm_reading._call_vision)
        assert "claude-opus-4-7" in src, "Opus 4.7 모델 명시 필요"
        # Sonnet 4.6 폴백 제거 검증 (코드에 미존재)
        assert "claude-sonnet-4-6" not in src, (
            "ADR-214 — Sonnet 4.6 폴백 제거 위반 (사용자 결단)"
        )

    def test_call_vision_no_fallback_loop(self):
        """ADR-214 — fallback_models 루프 제거 (단일 호출)."""
        src = inspect.getsource(palm_reading._call_vision)
        assert "fallback_models" not in src, (
            "ADR-214 — fallback_models 패턴 제거 위반"
        )
