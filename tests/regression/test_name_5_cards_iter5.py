"""ADR-135~139 회귀 — name 도메인 8 카드 중 5 결손 영역 본문화.

학술 근거:
  - ADR-026 한자 9,932자 풀
  - ADR-027·125·126·127 KCI 자원오행 학파
  - ADR-129 baleum 운해본 옵션 B
  - 자평진전·삼명통회 정통 사주명리
"""
from __future__ import annotations

from datetime import date

from engine.divination.name.biz_naming import (
    BizNamingResult,
    compute_biz_naming,
)
from engine.divination.name.daily_hanja import (
    DailyHanjaResult,
    get_daily_hanja,
)
from engine.divination.name.newborn import (
    NewbornNamingResult,
    compute_newborn_naming,
)
from engine.divination.name.pen_naming import (
    PenNamingResult,
    compute_pen_naming,
)
from engine.divination.name.rename import (
    RenameDiagnosis,
    compute_rename,
)


# ────────────────── ADR-135 today-hanja ──────────────────


class TestDailyHanjaDeterministic:
    """오늘의 한자 결정론."""

    def test_same_date_same_hanja(self):
        """동일 날짜 → 동일 한자 (결정론)."""
        d = date(2026, 5, 22)
        r1 = get_daily_hanja(d)
        r2 = get_daily_hanja(d)
        assert r1 is not None and r2 is not None
        assert r1.char == r2.char
        assert r1.seed_int == r2.seed_int

    def test_seed_format(self):
        """시드 = YYYYMMDD 8자리 정수."""
        d = date(2026, 5, 22)
        r = get_daily_hanja(d)
        assert r is not None
        assert r.seed_int == 20260522

    def test_different_dates_different_hanja_likely(self):
        """다른 날짜는 다른 한자 가능성 높음 (확률 X 결정론)."""
        chars = set()
        for day in range(1, 11):
            r = get_daily_hanja(date(2026, 5, day))
            if r:
                chars.add(r.char)
        # 10일 중 최소 5종 한자 (KCI 103자 풀 가정)
        assert len(chars) >= 5

    def test_result_has_meta(self):
        """결과 메타 필드 정합."""
        r = get_daily_hanja(date(2026, 5, 22))
        assert r is not None
        assert r.date_iso == "2026-05-22"
        assert len(r.char) == 1
        assert r.hangul  # 한국어 음 본문화
        assert r.kangxi_strokes > 0
        assert "참고용" in r.disclaimer

    def test_no_arg_uses_today(self):
        """인자 없으면 오늘 날짜."""
        r = get_daily_hanja()
        assert r is not None
        assert r.date_iso == date.today().isoformat()


# ────────────────── ADR-136 biz ──────────────────


class TestBizNaming:
    """상호 작명 결정론."""

    def test_cafe_returns_hwa_or_su(self):
        """카페 → 火 또는 水 (음식·음료)."""
        r = compute_biz_naming("카페")
        # 음식·식당 = 火 / 음료 = 水
        assert "화" in r.target_ohaeng_primary or "수" in r.target_ohaeng_primary

    def test_it_returns_geum(self):
        """IT 스타트업 → 金 (정밀·하드웨어)."""
        r = compute_biz_naming("IT 스타트업")
        assert "금" in r.target_ohaeng_primary

    def test_clothing_returns_mok(self):
        """의류 브랜드 → 木 (의류·종이)."""
        r = compute_biz_naming("의류 브랜드")
        assert "목" in r.target_ohaeng_primary

    def test_concept_secondary_ohaeng(self):
        """컨셉 '따뜻한' → 火 보조 매핑."""
        r = compute_biz_naming("의류", concept="따뜻한")
        assert r.target_ohaeng_secondary == "화"

    def test_unmatched_falls_back(self):
        """미매칭 업종 — 5 오행 폴백."""
        r = compute_biz_naming("미지의 사업 분야 XYZ")
        assert len(r.target_ohaeng_primary) == 5
        assert r.notes

    def test_recommended_hanja_pool(self):
        """추천 한자 풀 영속화."""
        r = compute_biz_naming("카페")
        # KCI 매핑 한자 풀 의존 — 최소 1자
        assert len(r.recommended_hanja) >= 1
        for h in r.recommended_hanja[:3]:
            assert "char" in h
            assert "ohaeng" in h
            assert "school" in h

    def test_school_source_isbn(self):
        """학파 출처 ISBN 명시 (ADR-010)."""
        r = compute_biz_naming("카페")
        assert "ISBN" in r.school_source

    def test_disclaimer_present(self):
        """면책 의무."""
        r = compute_biz_naming("카페")
        assert "참고용" in r.disclaimer


# ────────────────── ADR-137 pen ──────────────────


class TestPenNaming:
    """예명 작명 결정론."""

    def test_writer_returns_mok_su(self):
        """작가·시인 → 木 + 水."""
        r = compute_pen_naming("writer")
        assert "목" in r.target_ohaeng
        assert "수" in r.target_ohaeng

    def test_youtube_returns_hwa_geum(self):
        """유튜브 → 火 + 金."""
        r = compute_pen_naming("youtube")
        assert "화" in r.target_ohaeng
        assert "금" in r.target_ohaeng

    def test_music_returns_hwa_su(self):
        """음악·DJ → 火 + 水."""
        r = compute_pen_naming("music")
        assert "화" in r.target_ohaeng
        assert "수" in r.target_ohaeng

    def test_other_fallback(self):
        """기타 → 5 오행 폴백."""
        r = compute_pen_naming("other")
        assert len(r.target_ohaeng) == 5

    def test_unknown_field_to_other(self):
        """미지정 분야 → other 폴백."""
        r = compute_pen_naming("invalid_field")
        assert r.field_code == "invalid_field"
        # other rationale 폴백
        assert len(r.target_ohaeng) == 5

    def test_saju_weak_ohaeng_added(self):
        """사주 부족 오행 합산 (옵션)."""
        r = compute_pen_naming("writer", real_saju_weak_ohaeng=["토"])
        # writer 기본 목·수 + 토 추가
        assert "토" in r.target_ohaeng

    def test_school_source_isbn(self):
        r = compute_pen_naming("writer")
        assert "ISBN" in r.school_source


# ────────────────── ADR-138 newborn ──────────────────


class TestNewbornNaming:
    """신생아 작명 결정론."""

    def test_basic_call(self):
        """기본 호출."""
        r = compute_newborn_naming(
            surname="김",
            baby_birth_iso="2026-05-22",
            baby_hour_branch="午",
            baby_gender="M",
            parent_wish="건강하고 지혜로운 아이로",
        )
        assert r is not None
        assert r.surname == "김"
        assert r.baby_birth_iso == "2026-05-22"
        assert r.baby_hour == "午"
        assert r.baby_gender == "M"

    def test_invalid_birth_returns_none(self):
        """잘못된 birth → None."""
        r = compute_newborn_naming(
            surname="김", baby_birth_iso="invalid"
        )
        assert r is None

    def test_saju_summary_present(self):
        """사주 요약 영속화."""
        r = compute_newborn_naming(surname="김", baby_birth_iso="2026-05-22")
        assert r is not None
        assert "일주" in r.saju_summary
        assert "일간" in r.saju_summary

    def test_recommended_hanja_pool(self):
        r = compute_newborn_naming(surname="김", baby_birth_iso="2026-05-22")
        assert r is not None
        # 사주 부족 오행 있으면 한자 풀 1자+ (KCI 매핑 의존)
        if r.saju_recommended_ohaeng:
            assert isinstance(r.recommended_hanja, list)

    def test_school_source_present(self):
        r = compute_newborn_naming(surname="김", baby_birth_iso="2026-05-22")
        assert r is not None
        assert "정통 사주명리" in r.school_source
        assert "KCI" in r.school_source

    def test_disclaimer_no_assertion(self):
        r = compute_newborn_naming(surname="김", baby_birth_iso="2026-05-22")
        assert r is not None
        # 단정 어휘 부재
        for assertion in ["반드시", "확실히", "100%"]:
            assert assertion not in r.disclaimer


# ────────────────── ADR-139 rename ──────────────────


class TestRename:
    """개명 진단 결정론."""

    def test_basic_call(self):
        """기본 호출."""
        r = compute_rename(
            current_name="김철수",
            birth_iso="1990-05-15",
            hour_branch="午",
        )
        assert r is not None
        assert r.current_name == "김철수"

    def test_invalid_birth_returns_none(self):
        """잘못된 birth → None."""
        r = compute_rename(current_name="김철수", birth_iso="invalid")
        assert r is None

    def test_conflict_diagnosis_present(self):
        """충돌 진단 boolean + 상세."""
        r = compute_rename(current_name="김철수", birth_iso="1990-05-15")
        assert r is not None
        assert isinstance(r.ohaeng_conflict, bool)
        assert r.conflict_detail  # 상세 한 줄 영속화

    def test_recommended_hanja_pool(self):
        r = compute_rename(current_name="김철수", birth_iso="1990-05-15")
        assert r is not None
        assert isinstance(r.recommended_hanja, list)

    def test_user_reason_preserved(self):
        """사용자 이유 텍스트 LLM 전달용 보존."""
        r = compute_rename(
            current_name="김철수",
            birth_iso="1990-05-15",
            user_reason="일이 잘 풀리지 않아",
        )
        assert r is not None
        assert r.user_reason == "일이 잘 풀리지 않아"

    def test_school_source_present(self):
        r = compute_rename(current_name="김철수", birth_iso="1990-05-15")
        assert r is not None
        assert "정통 사주명리" in r.school_source
        assert "KCI" in r.school_source

    def test_baleum_grade_present(self):
        """발음오행 등급 영속화."""
        r = compute_rename(current_name="김철수", birth_iso="1990-05-15")
        assert r is not None
        # baleum_grade는 빈 문자열 가능 (등급 미산출 시) — 필드 존재만 검증
        assert hasattr(r, "baleum_grade")

    def test_no_negative_assertion(self):
        """진단 텍스트에 단정 어휘 부재 (ADR-006)."""
        r = compute_rename(
            current_name="김철수",
            birth_iso="1990-05-15",
            user_reason="운이 안 좋아",
        )
        assert r is not None
        # 시스템 출력 (conflict_detail·disclaimer)에 단정 어휘 부재
        for assertion in ["반드시", "확실히", "100%", "운이 나쁘다"]:
            assert assertion not in r.conflict_detail
            assert assertion not in r.disclaimer


# ────────────────── 통합 안전성 ──────────────────


class TestIntegratedSafety:
    """5 카드 통합 ADR-006·010 정합."""

    def test_all_5_modules_have_disclaimer(self):
        """5 모듈 모두 면책 의무."""
        # today-hanja
        r1 = get_daily_hanja(date(2026, 5, 22))
        assert r1 and "참고용" in r1.disclaimer
        # biz
        r2 = compute_biz_naming("카페")
        assert "참고용" in r2.disclaimer
        # pen
        r3 = compute_pen_naming("writer")
        assert "참고용" in r3.disclaimer
        # newborn
        r4 = compute_newborn_naming(surname="김", baby_birth_iso="2026-05-22")
        assert r4 and "참고용" in r4.disclaimer
        # rename
        r5 = compute_rename(current_name="김철수", birth_iso="1990-05-15")
        assert r5 and "참고용" in r5.disclaimer

    def test_all_5_modules_have_school_source(self):
        """5 모듈 모두 학파 출처 명시 (ADR-010)."""
        r2 = compute_biz_naming("카페")
        assert r2.school_source
        r3 = compute_pen_naming("writer")
        assert r3.school_source
        r4 = compute_newborn_naming(surname="김", baby_birth_iso="2026-05-22")
        assert r4 and r4.school_source
        r5 = compute_rename(current_name="김철수", birth_iso="1990-05-15")
        assert r5 and r5.school_source
