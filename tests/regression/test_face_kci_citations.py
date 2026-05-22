"""ADR-144 회귀 — face KCI 학술 인용 영속화 (/domain-priorities #6 해소).

본 시스템 face/knowledge.py에 KCI 등재 학술 논문 인용 추가:
  · 오근재 (1999) Archives of Design Research 12권 1호 — 눈 관상학
  · 강선희·김효동·이경원 (2008) Archives of Design Research 21권 4호 — 부위 분류

회귀 의무:
  · KCI 등재 인용 2건 이상 영속
  · Archives of Design Research = KCI + SCOPUS 등재 보장
  · format_kci_citations_for_prompt() 출력에 KCI/SCOPUS 표기
  · 운명 단정 어휘 차단 (usage_note 안전성)
"""
from __future__ import annotations

from engine.divination.face.knowledge import (
    FACE_KCI_CITATIONS,
    format_kci_citations_for_prompt,
    get_kci_citation_by_key,
)


class TestKciCitationsExist:
    """KCI 인용 영속화."""

    def test_at_least_two_kci_citations(self):
        """최소 2건 KCI 등재 인용 (/domain-priorities #6 해소 임계)."""
        assert len(FACE_KCI_CITATIONS) >= 2

    def test_all_citations_kci_indexed(self):
        """모든 인용이 KCI 등재 (kci_indexed=True 보장)."""
        for c in FACE_KCI_CITATIONS:
            assert c.kci_indexed is True, (
                f"{c.key}: KCI 미등재 — ADR-144 의무 위반"
            )

    def test_oh_1999_eye_present(self):
        """오근재 (1999) 눈 관상학 논문 인용 영속."""
        c = get_kci_citation_by_key("oh_1999_eye")
        assert c is not None
        assert c.publication_year == 1999
        assert "오근재" in c.authors_ko
        assert "눈" in c.title_ko or "眼" in c.title_ko
        assert c.kci_indexed
        assert c.scopus_indexed

    def test_kang_2008_mbti_face_present(self):
        """강선희 외 (2008) 부위 분류 논문 인용 영속."""
        c = get_kci_citation_by_key("kang_2008_mbti_face")
        assert c is not None
        assert c.publication_year == 2008
        assert "강선희" in c.authors_ko


class TestCitationMetadataCompleteness:
    """인용 메타데이터 완전성."""

    def test_all_have_dbpia_url(self):
        """모든 인용에 DBpia 검증 URL 명시."""
        for c in FACE_KCI_CITATIONS:
            assert c.dbpia_url.startswith("https://www.dbpia.co.kr/"), (
                f"{c.key}: DBpia URL 누락 또는 부정합"
            )

    def test_all_have_publisher_url(self):
        """모든 인용에 학회 공식 URL 명시."""
        for c in FACE_KCI_CITATIONS:
            assert c.publisher_url.startswith("https://"), (
                f"{c.key}: 학회 URL 누락"
            )

    def test_all_have_topic_focus(self):
        """모든 인용에 활용 영역 명시 (topic_focus)."""
        for c in FACE_KCI_CITATIONS:
            assert c.topic_focus and len(c.topic_focus) >= 5

    def test_all_have_usage_note(self):
        """모든 인용에 사용 주의사항 명시 (ADR-006·010 정합)."""
        for c in FACE_KCI_CITATIONS:
            assert c.usage_note and len(c.usage_note) >= 10


class TestPromptFormatting:
    """프롬프트 빌드 포맷."""

    def test_prompt_includes_adr_144_marker(self):
        """프롬프트 헤더에 ADR-144 마커 명시."""
        prompt = format_kci_citations_for_prompt()
        assert "ADR-144" in prompt

    def test_prompt_includes_kci_label(self):
        """프롬프트에 'KCI 등재' 라벨 명시."""
        prompt = format_kci_citations_for_prompt()
        assert "KCI 등재" in prompt

    def test_prompt_includes_scopus_when_applicable(self):
        """SCOPUS 등재 인용은 프롬프트에 SCOPUS 표기."""
        prompt = format_kci_citations_for_prompt()
        # 본 인용 2건 모두 SCOPUS — SCOPUS 라벨 명시 의무
        assert "SCOPUS" in prompt

    def test_prompt_includes_all_citations(self):
        """모든 인용이 프롬프트에 포함."""
        prompt = format_kci_citations_for_prompt()
        for c in FACE_KCI_CITATIONS:
            # 저자 이름 1개라도 등장
            first_author = c.authors_ko.split("·")[0].split(" ")[0]
            assert first_author in prompt

    def test_prompt_includes_disclaimer_keyword(self):
        """프롬프트에 운명 단정 회피 주의 명시 (ADR-006·010 정합)."""
        prompt = format_kci_citations_for_prompt()
        # 단정 X 또는 분류 체계만 같은 안전 표기
        assert "단정 X" in prompt or "분류 체계만" in prompt


class TestADR006Safety:
    """ADR-006 자문 거절 정합 — 인용 메타에 단정 어휘 0건."""

    FORBIDDEN_WORDS = [
        "반드시", "확실히", "100%", "절대 행복", "절대 성공",
        "이혼", "재혼", "사망", "단명",
    ]

    def test_no_forbidden_words_in_titles(self):
        """논문 제목에 단정 어휘 0건 (학술 원문 정합)."""
        for c in FACE_KCI_CITATIONS:
            for w in self.FORBIDDEN_WORDS:
                assert w not in c.title_ko, (
                    f"{c.key}: 단정 어휘 '{w}' 제목 포함"
                )

    def test_no_forbidden_words_in_usage_notes(self):
        """usage_note에 단정 어휘 0건 (본 시스템 가이드 정합)."""
        for c in FACE_KCI_CITATIONS:
            for w in self.FORBIDDEN_WORDS:
                # '이혼' 같은 단어는 "이혼 단정 X" 형태로 포함 가능 — 단정 X 컨텍스트만 허용
                if w in c.usage_note:
                    assert ("단정 X" in c.usage_note or
                            "차단" in c.usage_note or
                            "회피" in c.usage_note), (
                        f"{c.key}: '{w}' 사용 시 단정 회피 컨텍스트 의무"
                    )
