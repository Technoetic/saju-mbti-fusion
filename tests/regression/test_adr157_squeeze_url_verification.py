"""ADR-157 회귀 — /squeeze-report 월하몽_도메인지식_URL_검증목록.md 본 AI 단독 4 채택.

대상:
  · C4 pillars.py YAJASI_KCI_CITATIONS (ART001867073)
  · C5 saju_school.py QUANTIFICATION_KCI_CITATIONS (ART002423988)
  · C6 ten_gods.py SIPSUNG_KCI_CITATIONS (ART002438633·002596247)
  · C2 dream_lex/korean_folk.py DREAM_KCI_CITATIONS 확장 (2→4건, ART002716260·001206120)
"""
from __future__ import annotations


class TestPillarsYajasiKci:
    """C4 — pillars.py 야자시 KCI 영속."""

    def test_citation_present(self):
        from engine.saju.pillars import get_yajasi_kci_citations
        cs = get_yajasi_kci_citations()
        assert len(cs) >= 1
        assert cs[0].identifier == "ART001867073"
        assert cs[0].kci_indexed is True

    def test_topic_yajasi_separate(self):
        from engine.saju.pillars import get_yajasi_kci_citations
        c = get_yajasi_kci_citations()[0]
        assert "야자시" in c.topic_focus or "정자시" in c.topic_focus


class TestSajuSchoolQuantificationKci:
    """C5 — saju_school.py 사주오행 계량화 KCI 영속."""

    def test_citation_present(self):
        from engine.divination.name.saju_school import get_quantification_kci_citations
        cs = get_quantification_kci_citations()
        assert len(cs) >= 1
        assert cs[0].identifier == "ART002423988"

    def test_topic_quantification(self):
        from engine.divination.name.saju_school import get_quantification_kci_citations
        c = get_quantification_kci_citations()[0]
        assert "계량" in c.topic_focus
        assert "일간" in c.topic_focus


class TestTenGodsSipsungKci:
    """C6 — ten_gods.py 십성·격국 KCI 영속 (2건)."""

    def test_two_citations(self):
        from engine.saju.ten_gods import get_sipsung_kci_citations
        cs = get_sipsung_kci_citations()
        assert len(cs) == 2

    def test_identifiers(self):
        from engine.saju.ten_gods import get_sipsung_kci_citations
        ids = {c.identifier for c in get_sipsung_kci_citations()}
        assert "ART002438633" in ids
        assert "ART002596247" in ids

    def test_all_kci_indexed(self):
        from engine.saju.ten_gods import get_sipsung_kci_citations
        for c in get_sipsung_kci_citations():
            assert c.kci_indexed is True


class TestDreamKciExpansion:
    """C2 — dream_lex/korean_folk.py KCI 2→4 확장."""

    def test_four_citations_now(self):
        from engine.divination.dream_lex.korean_folk import get_dream_kci_citations
        cs = get_dream_kci_citations()
        assert len(cs) == 4

    def test_v7_citations_present(self):
        from engine.divination.dream_lex.korean_folk import get_dream_kci_citations
        ids = {c.identifier for c in get_dream_kci_citations()}
        assert "ART002716260" in ids
        assert "ART001206120" in ids

    def test_adr152_baseline_preserved(self):
        """ADR-152 기존 2건 (김재희·조규문) 영속."""
        from engine.divination.dream_lex.korean_folk import get_dream_kci_citations
        ids = {c.identifier for c in get_dream_kci_citations()}
        assert "DIKO0014402351" in ids  # 김재희 박사논문
        assert any("Sundo Culture" in i for i in ids)  # 조규문 2020
