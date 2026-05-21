"""ADR-129 회귀 — baleum 운해본(韻解本) 옵션 B 학파 분기.

학술 근거:
  - 조현아 (2014) 공주대학교 석사학위논문 — DBpia T13373928
    "성명학의 작명원리에 있어서의 오행연구: 훈민정음해례본과 현재 작명법에
    적용되는 한글오행의 비교연구"
  - 작명학 한자 자원오행 매핑 학술 출처 보고서 §4.2 (운해본 명시)

학파 분기:
  - 해례본(옵션 A 디폴트): ㅇ/ㅎ→土, ㅁ/ㅂ/ㅍ→水
  - 운해본(옵션 B): ㅇ/ㅎ→水, ㅁ/ㅂ/ㅍ→土
"""
from __future__ import annotations

import pytest

from engine.divination.name.baleum import (
    SCHOOL_OPTIONS,
    chosung_to_ohaeng,
    jongsung_to_ohaeng,
    syllable_to_ohaeng,
)


class TestHaerebonDefault:
    """옵션 A 디폴트 — 훈민정음 해례본 매핑."""

    @pytest.mark.parametrize("chosung, expected", [
        ("ㄱ", "목"), ("ㅋ", "목"),
        ("ㄴ", "화"), ("ㄷ", "화"), ("ㄹ", "화"), ("ㅌ", "화"),
        ("ㅇ", "토"), ("ㅎ", "토"),  # 해례본 — 목구멍소리=土
        ("ㅅ", "금"), ("ㅈ", "금"), ("ㅊ", "금"),
        ("ㅁ", "수"), ("ㅂ", "수"), ("ㅍ", "수"),  # 해례본 — 입술소리=水
    ])
    def test_haerebon_chosung_mapping(self, chosung: str, expected: str):
        """해례본 매핑 (디폴트)."""
        assert chosung_to_ohaeng(chosung) == expected
        assert chosung_to_ohaeng(chosung, school="haerebon") == expected


class TestUnhaeOption:
    """옵션 B — 운해본 매핑 (土/水 교차)."""

    @pytest.mark.parametrize("chosung, expected", [
        # 동일 매핑 (변경 없음)
        ("ㄱ", "목"), ("ㅋ", "목"),
        ("ㄴ", "화"), ("ㄷ", "화"), ("ㄹ", "화"),
        ("ㅅ", "금"), ("ㅈ", "금"), ("ㅊ", "금"),
        # 학파 분기 (운해본 교차)
        ("ㅇ", "수"), ("ㅎ", "수"),  # 운해본 — 土→水 교차
        ("ㅁ", "토"), ("ㅂ", "토"), ("ㅍ", "토"),  # 운해본 — 水→土 교차
    ])
    def test_unhae_chosung_mapping(self, chosung: str, expected: str):
        """운해본 매핑."""
        assert chosung_to_ohaeng(chosung, school="unhae") == expected

    def test_unhae_crosses_haerebon(self):
        """운해본은 해례본의 ㅇ/ㅎ·ㅁ/ㅂ/ㅍ 학파 분기 — 명시 교차 의무."""
        # 해례본 ㅇ=토, 운해본 ㅇ=수
        assert chosung_to_ohaeng("ㅇ", school="haerebon") == "토"
        assert chosung_to_ohaeng("ㅇ", school="unhae") == "수"
        # 해례본 ㅁ=수, 운해본 ㅁ=토
        assert chosung_to_ohaeng("ㅁ", school="haerebon") == "수"
        assert chosung_to_ohaeng("ㅁ", school="unhae") == "토"


class TestJongsungSchoolOption:
    """종성도 학파 분기 적용."""

    def test_jongsung_haerebon(self):
        """해례본 종성 매핑."""
        assert jongsung_to_ohaeng("ㅇ") == "토"
        assert jongsung_to_ohaeng("ㅁ") == "수"

    def test_jongsung_unhae(self):
        """운해본 종성 매핑."""
        assert jongsung_to_ohaeng("ㅇ", school="unhae") == "수"
        assert jongsung_to_ohaeng("ㅁ", school="unhae") == "토"

    def test_jongsung_empty(self):
        """빈 종성 빈 문자열."""
        assert jongsung_to_ohaeng("") == ""
        assert jongsung_to_ohaeng("", school="unhae") == ""


class TestSyllableSchoolOption:
    """음절 발음오행 학파 분기."""

    def test_syllable_haerebon(self):
        """해례본 음절 매핑."""
        assert syllable_to_ohaeng("가") == "목"  # ㄱ
        assert syllable_to_ohaeng("아") == "토"  # ㅇ
        assert syllable_to_ohaeng("마") == "수"  # ㅁ

    def test_syllable_unhae(self):
        """운해본 음절 매핑 — ㅇ/ㅁ 학파 분기."""
        assert syllable_to_ohaeng("가", school="unhae") == "목"  # 동일
        assert syllable_to_ohaeng("아", school="unhae") == "수"  # 교차
        assert syllable_to_ohaeng("마", school="unhae") == "토"  # 교차


class TestSchoolOptionsMetadata:
    """ADR-015 옵션 병행 정신 — 학파 메타데이터 명시."""

    def test_two_school_options_present(self):
        """2 학파 영속화."""
        assert set(SCHOOL_OPTIONS.keys()) == {"haerebon", "unhae"}

    def test_haerebon_is_default(self):
        """해례본은 디폴트 (옵션 A)."""
        assert SCHOOL_OPTIONS["haerebon"]["default"] is True
        assert SCHOOL_OPTIONS["unhae"]["default"] is False

    def test_all_options_have_citation(self):
        """모든 옵션에 학술 인용 명시 (ADR-010)."""
        for school, meta in SCHOOL_OPTIONS.items():
            citation = meta.get("citation", "")
            assert "조현아" in citation or "DBpia" in citation, (
                f"{school}: 학술 인용 부재"
            )

    def test_invalid_school_falls_back_to_haerebon(self):
        """잘못된 학파 키는 해례본 디폴트로 폴백 (안전망)."""
        # 'invalid' 학파는 unhae가 아니므로 haerebon 디폴트
        assert chosung_to_ohaeng("ㅇ", school="invalid") == "토"
        assert chosung_to_ohaeng("ㅁ", school="invalid") == "수"


class TestBackwardCompatibility:
    """기존 API 하위 호환성 — school 인자 없을 때 해례본 디폴트."""

    def test_chosung_default_is_haerebon(self):
        """기존 호출(인자 없음)은 해례본 디폴트 유지."""
        # 기존 시스템 호출 패턴 — 변경 없이 동작 보장
        assert chosung_to_ohaeng("ㄱ") == "목"
        assert chosung_to_ohaeng("ㅇ") == "토"  # 해례본
        assert chosung_to_ohaeng("ㅁ") == "수"  # 해례본

    def test_syllable_default_is_haerebon(self):
        """기존 syllable_to_ohaeng 호출 변경 없음."""
        assert syllable_to_ohaeng("강") == "목"
        assert syllable_to_ohaeng("영") == "토"
        assert syllable_to_ohaeng("민") == "수"
