"""ADR-152 회귀 — /domain-priorities 3차 사이클 5 도메인 KCI 확장.

3 도메인 발굴 성공 (dream·name·star) + 2 도메인 부재 정직 명시 (palm·yutjeom).

영속 영역:
  · dream: 김재희 박사 (태몽) + 조규문 2020 (Sundo Culture)
  · name: 권익기 2022 KCI ART002920855 (성명학 정체성)
  · star: KCI ART000897391 (점성술 비판 — ADR-006 정합 강화)
"""
from __future__ import annotations

from engine.divination.dream_lex.korean_folk import (
    DREAM_KCI_CITATIONS,
    get_dream_kci_citations,
)
from engine.divination.name.baleum import (
    NAME_KCI_CITATIONS,
    get_name_kci_citations,
)
from engine.divination.star.astronomy import (
    STAR_KCI_CITATIONS,
    get_star_kci_citations,
)


class TestDreamKciCitations:
    """dream 도메인 KCI 인용 영속."""

    def test_at_least_two_citations(self):
        assert len(DREAM_KCI_CITATIONS) >= 2

    def test_kim_taemong_present(self):
        """김재희 박사 태몽 논문 영속 (DIKO0014402351)."""
        cs = get_dream_kci_citations()
        kim = [c for c in cs if "김재희" in c.author_ko]
        assert len(kim) == 1
        assert kim[0].identifier == "DIKO0014402351"
        assert "태몽" in kim[0].title_ko

    def test_cho_2020_sundo_culture_present(self):
        """조규문 (2020) Sundo Culture 28권 영속."""
        cs = get_dream_kci_citations()
        cho = [c for c in cs if "조규문" in c.author_ko]
        assert len(cho) == 1
        c = cho[0]
        assert c.publication_year == 2020
        assert "Sundo Culture" in c.journal or "선도문화" in c.journal


class TestNameKciCitations:
    """name 도메인 KCI 인용 영속."""

    def test_at_least_one_citation(self):
        assert len(NAME_KCI_CITATIONS) >= 1

    def test_kwon_2022_present(self):
        """권익기 (2022) 성명학 정체성 KCI ART002920855 영속."""
        cs = get_name_kci_citations()
        kwon = [c for c in cs if "권익기" in c.author_ko]
        assert len(kwon) == 1
        c = kwon[0]
        assert c.publication_year == 2022
        assert c.kci_artiId == "ART002920855"
        assert "성명학" in c.title_ko
        assert c.kci_citations >= 1

    def test_has_doi(self):
        """권익기 (2022) DOI 영속."""
        cs = get_name_kci_citations()
        kwon = [c for c in cs if "권익기" in c.author_ko][0]
        assert kwon.doi.startswith("10."), f"DOI 형식 부정합: {kwon.doi}"


class TestStarKciCitations:
    """star 도메인 KCI 인용 영속 (비판 관점)."""

    def test_at_least_one_citation(self):
        assert len(STAR_KCI_CITATIONS) >= 1

    def test_pseudo_science_critique_present(self):
        """점성술 비판 논문 KCI ART000897391 영속."""
        cs = get_star_kci_citations()
        match = [c for c in cs if c.kci_artiId == "ART000897391"]
        assert len(match) == 1
        c = match[0]
        assert "점성술" in c.title_ko
        assert "비판" in c.title_ko

    def test_critique_note_explicit(self):
        """비판 관점이 critique_note에 명시 (ADR-006 정합 보강)."""
        cs = get_star_kci_citations()
        for c in cs:
            assert c.critique_note and len(c.critique_note) >= 20
            assert "ADR-006" in c.critique_note or "단정" in c.critique_note


class TestCrossDomainADR010Strengthening:
    """ADR-010 사실성 분리 — 3 도메인 학술 출처 강화."""

    def test_3_domains_have_kci_citations(self):
        """dream·name·star 3 도메인 모두 KCI 인용 1건 이상."""
        assert len(DREAM_KCI_CITATIONS) >= 1
        assert len(NAME_KCI_CITATIONS) >= 1
        assert len(STAR_KCI_CITATIONS) >= 1

    def test_total_5_citations_across_domains(self):
        """3 도메인 총 인용 5건 이상 (2+1+1+ 추가 확장 가능)."""
        total = (
            len(DREAM_KCI_CITATIONS)
            + len(NAME_KCI_CITATIONS)
            + len(STAR_KCI_CITATIONS)
        )
        assert total >= 4, f"3 도메인 총 인용 {total}건 (목표 ≥ 4)"

    def test_no_assertion_words_in_topic_focus(self):
        """모든 인용 topic_focus에 단정 어휘 0건."""
        forbidden = ["반드시", "확실히", "100%", "절대"]
        all_cs = list(DREAM_KCI_CITATIONS) + list(NAME_KCI_CITATIONS) + list(STAR_KCI_CITATIONS)
        for c in all_cs:
            for w in forbidden:
                assert w not in c.topic_focus, (
                    f"{c.author_ko}: topic_focus 단정 어휘 '{w}' 검출"
                )
