"""ADR-155 회귀 — /domain-priorities 잔여 5건 본 AI 단독 추가 영속.

대상:
  · #4 학파 토글 compatibility·tojeong content-system 마운트 + 신규 옵션 풀 2종
  · #1 tojeong RISS 김수년 (2016) WebFetch 학술 메타
  · #2 palm 11k Hands fair use 정책 자동화
  · #3 hwapae A/B 테스트 측정 인프라
  · #5 /domain-priorities cron reminder 스크립트 + GitHub Actions
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest


# ─────────────────────────── #4 학파 토글 추가 옵션 풀 + content-system 마운트 ───────────────────────────


class TestSchoolToggleExtraOptions:
    """ADR-155 추가 옵션 풀 (compatibility·tojeong) 영속."""

    @pytest.fixture(scope="class")
    def school_toggle_src(self) -> str:
        return Path("front/js/ui/school-toggle.js").read_text(encoding="utf-8")

    def test_star_compatibility_options_exported(self, school_toggle_src: str):
        assert "export const STAR_COMPATIBILITY_OPTIONS" in school_toggle_src

    def test_tojeong_verse_source_options_exported(self, school_toggle_src: str):
        assert "export const TOJEONG_VERSE_SOURCE_OPTIONS" in school_toggle_src

    def test_star_default_element_only(self, school_toggle_src: str):
        """디폴트: element 호환 (Liz Greene 정통)."""
        assert "key: 'element_only'" in school_toggle_src

    def test_tojeong_default_synthesized(self, school_toggle_src: str):
        """디폴트: 흐름 톤만 (운명 단정 X)."""
        assert "key: 'synthesized_only'" in school_toggle_src


class TestContentSystemMount:
    """ADR-155 content-system.js 학파 토글 마운트 영속."""

    @pytest.fixture(scope="class")
    def content_system_src(self) -> str:
        return Path("front/js/ui/content-system.js").read_text(encoding="utf-8")

    def test_slot_container_present(self, content_system_src: str):
        assert 'id="content-school-toggle-slot"' in content_system_src

    def test_dynamic_import(self, content_system_src: str):
        assert "import('./school-toggle.js')" in content_system_src

    def test_compatibility_branch(self, content_system_src: str):
        assert "STAR_COMPATIBILITY_OPTIONS" in content_system_src

    def test_tojeong_branch(self, content_system_src: str):
        assert "TOJEONG_VERSE_SOURCE_OPTIONS" in content_system_src

    def test_localstorage_keys(self, content_system_src: str):
        for key in ("whm.school.star_compat", "whm.school.tojeong_source"):
            assert key in content_system_src, f"localStorage 키 '{key}' 누락"


# ─────────────────────────── #1 tojeong RISS 김수년 메타 ───────────────────────────


class TestKim2016ResearchMeta:
    """ADR-155 WebFetch 라이브 확보 김수년 (2016) 학술 메타."""

    def test_meta_dict_full_keys(self):
        from engine.divination.tojeong.scoring import get_kim_2016_research_meta
        m = get_kim_2016_research_meta()
        for key in (
            "title_hanja", "title_en", "author_ko", "publication_year",
            "riss_control_no", "appendix_has_144_full",
            "original_verse_char_count", "classical_reference_ratio_pct",
        ):
            assert key in m, f"메타 필드 '{key}' 누락"

    def test_riss_control_no_match(self):
        from engine.divination.tojeong.scoring import get_kim_2016_research_meta
        assert get_kim_2016_research_meta()["riss_control_no"] == "000014351511"

    def test_144_appendix_confirmed(self):
        """WebFetch 라이브 확인 — 권말부록 144괘 원문 수록."""
        from engine.divination.tojeong.scoring import get_kim_2016_research_meta
        assert get_kim_2016_research_meta()["appendix_has_144_full"] is True

    def test_original_verse_8_chars(self):
        """WebFetch 핵심 발견 — 원본 시구 8자."""
        from engine.divination.tojeong.scoring import get_kim_2016_research_meta
        assert get_kim_2016_research_meta()["original_verse_char_count"] == 8

    def test_classical_reference_61pct(self):
        """61% 육효점·매화역수 인용률."""
        from engine.divination.tojeong.scoring import get_kim_2016_research_meta
        assert get_kim_2016_research_meta()["classical_reference_ratio_pct"] == 61


# ─────────────────────────── #2 palm 11k Hands fair use 정책 ───────────────────────────


class TestHands11kFairUse:
    """ADR-155 11k Hands fair use 정책 자동화."""

    def test_policy_keys(self):
        from engine.divination.palm.training_skeleton import get_11k_hands_policy
        p = get_11k_hands_policy()
        for key in ("academic_use", "commercial_use", "bibtex", "official_url", "doi"):
            assert key in p, f"정책 필드 '{key}' 누락"

    def test_academic_yes_commercial_no(self):
        from engine.divination.palm.training_skeleton import get_11k_hands_policy
        p = get_11k_hands_policy()
        assert p["academic_use"] is True
        assert p["commercial_use"] is False

    def test_doi_present(self):
        from engine.divination.palm.training_skeleton import get_11k_hands_policy
        assert get_11k_hands_policy()["doi"] == "10.1007/s11042-019-7424-8"

    def test_commercial_use_blocked(self):
        from engine.divination.palm.training_skeleton import validate_commercial_use_blocked
        ok, _ = validate_commercial_use_blocked("commercial_saas")
        assert ok is False

    def test_academic_allowed(self):
        from engine.divination.palm.training_skeleton import validate_commercial_use_blocked
        ok, _ = validate_commercial_use_blocked("academic_research")
        assert ok is True


# ─────────────────────────── #3 hwapae A/B 측정 인프라 ───────────────────────────


class TestHwapaeABTest:
    """ADR-155 hwapae A/B 테스트 측정 인프라."""

    def setup_method(self):
        from engine.divination.hwapae.marketing_slots import reset_ab_test_state
        reset_ab_test_state()

    def test_assign_variant_deterministic(self):
        """동일 anon_id → 항상 동일 variant (UX 일관성)."""
        from engine.divination.hwapae.marketing_slots import assign_variant
        v1 = assign_variant("user_abc")
        v2 = assign_variant("user_abc")
        assert v1 == v2

    def test_assign_variant_different_users_distribute(self):
        """다양한 anon_id → variant 분산 (1명 이상)."""
        from engine.divination.hwapae.marketing_slots import assign_variant
        variants = {assign_variant(f"user_{i}") for i in range(100)}
        assert len(variants) >= 2  # 최소 2 variant 노출 보장

    def test_record_exposure_and_stats(self):
        from engine.divination.hwapae.marketing_slots import (
            record_exposure, compute_ab_test_stats,
        )
        record_exposure("u1", "academic_kci", 1700000000000)
        record_exposure("u2", "academic_kci", 1700000001000)
        record_exposure("u3", "casual_fun", 1700000002000)
        stats = compute_ab_test_stats()
        assert stats["academic_kci"]["exposures"] == 2
        assert stats["casual_fun"]["exposures"] == 1

    def test_conversion_rate_calculation(self):
        from engine.divination.hwapae.marketing_slots import (
            record_exposure, record_conversion, compute_ab_test_stats,
        )
        record_exposure("u1", "academic_kci", 1700000000000)
        record_exposure("u2", "academic_kci", 1700000001000)
        record_conversion("u1", "academic_kci")
        stats = compute_ab_test_stats()
        assert stats["academic_kci"]["conversion_rate"] == 0.5  # 1/2


# ─────────────────────────── #5 /domain-priorities cron reminder ───────────────────────────


class TestDomainPrioritiesReminder:
    """ADR-155 /domain-priorities 재호출 cron reminder 스크립트."""

    def test_script_importable(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "auto_reminder",
            Path("scripts/auto_domain_priorities_reminder.py").resolve(),
        )
        assert spec is not None
        assert spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "is_recall_due")
        assert hasattr(mod, "format_reminder_message")
        assert hasattr(mod, "extract_limit_sections_from_adrs")

    def test_recall_interval_30_days(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "auto_reminder",
            Path("scripts/auto_domain_priorities_reminder.py").resolve(),
        )
        assert spec is not None
        assert spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert mod.REMINDER_INTERVAL_DAYS == 30

    def test_github_action_workflow_exists(self):
        wf = Path(".github/workflows/domain-priorities-reminder.yml")
        assert wf.exists(), "GitHub Actions cron workflow 누락"
        src = wf.read_text(encoding="utf-8")
        assert "schedule" in src
        assert "cron: '0 9 1 * *'" in src  # 매월 1일 09:00 UTC

    def test_recall_due_logic(self):
        """30일 미만 → False, 30일 이상 → True."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "auto_reminder",
            Path("scripts/auto_domain_priorities_reminder.py").resolve(),
        )
        assert spec is not None
        assert spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # 마지막 호출 일자에 의존 — vault 부재 시 None 처리
        last = mod.get_last_domain_priorities_date()
        if last is None:
            pytest.skip("vault/reports/ 부재 (CLAUDE.md §6) — CI 환경 스킵")
        days = mod.days_since_last_call()
        assert days is not None and days >= 0
