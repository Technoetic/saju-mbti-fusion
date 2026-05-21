"""ADR-127 본문화 회귀 — 학파 분기 명시 (詠·心) — ADR-002·015 옵션 병행 정신.

학술 근거: 보고서 §6 school_differences 라인 246~258 본문 명시.
"""
from __future__ import annotations

from engine.divination.name.unihan import school_split


class TestSchoolSplit:
    """학파 분기 본문화 회귀."""

    def test_yeong_split(self):
        """詠 학파 분기 — 정통=화, KCI=수, 사주명리=토."""
        split = school_split("詠")
        assert split is not None
        assert split["primary_ohaeng"] == "화"
        schools = split["schools"]
        assert isinstance(schools, list)
        assert len(schools) == 3
        # 학파별 ohaeng 검증
        school_ohaeng_map = {s["school"]: s["ohaeng"] for s in schools}
        # 정통 학파는 화
        assert any("정통" in s and o == "화" for s, o in school_ohaeng_map.items())
        # KCI 학파는 수
        assert any("KCI" in s and o == "수" for s, o in school_ohaeng_map.items())
        # 사주명리 학파는 토
        assert any("사주" in s and o == "토" for s, o in school_ohaeng_map.items())

    def test_sim_split(self):
        """心 학파 분기 — 정통/AKS=화, KCI=불명확."""
        split = school_split("心")
        assert split is not None
        assert split["primary_ohaeng"] == "화"
        schools = split["schools"]
        assert isinstance(schools, list)
        # 적어도 2 학파는 화
        hwa_count = sum(1 for s in schools if s["ohaeng"] == "화")
        assert hwa_count >= 2
        # KCI 학파는 불명확 명시
        assert any("불명확" in s["ohaeng"] or "주의" in s["ohaeng"] for s in schools)

    def test_split_consensus_note_present(self):
        """학파 분기 한자는 consensus_note 명시 의무 (ADR-010)."""
        for char in ["詠", "心"]:
            split = school_split(char)
            assert split is not None
            note = split.get("consensus_note", "")
            assert len(note) > 20, f"{char} consensus_note 너무 짧음: {note}"

    def test_non_split_hanja_returns_none(self):
        """본문 미명시 한자 None (가짜 확장 차단)."""
        # 본 시스템 단일 학파 매핑 한자
        assert school_split("木") is None
        assert school_split("田") is None
        # 미수록 한자
        assert school_split("") is None
        assert school_split("미수록") is None


class TestSchoolSplitDeterministic:
    """결정론 보장."""

    def test_deterministic_same_input(self):
        """동일 입력 동일 출력."""
        r1 = school_split("詠")
        r2 = school_split("詠")
        assert r1 == r2

    def test_only_two_hanja_in_split(self):
        """보고서 본문 명시 2 한자만 (詠·心) 본문화."""
        # 보고서 §6 본문에는 詠·心 2건만 명시
        assert school_split("詠") is not None
        assert school_split("心") is not None
