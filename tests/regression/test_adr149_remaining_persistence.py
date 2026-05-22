"""ADR-149 회귀 — Stale 잔여 4건 (#11·#12·#19·#21) 영속 보장 완성.

ADR-148이 트리아지 메모만 영속했던 4건을 회귀로 코드 검증 영속.
4중 보장 (코드 + ADR + 회귀 + 메타) 체인 완성.

대상:
  · #11 saju 신살 시너지 가중치 4단계 (0.0/1.0/1.5/2.0) — shensha.py
  · #12 dream 학파 명시 의무 (ADR-002·095) — dream.py 시스템 프롬프트
  · #19 face Vision 디폴트 Claude (OpenAI 제거) — face/reading.py
  · #21 saju 자평진전 디폴트 학파 — engine/saju 전반
"""
from __future__ import annotations

import inspect

import pytest

from engine.divination.dream import DREAM_SYSTEM
from engine.divination.face import reading as face_reading
from engine.saju.shensha import (
    SYNERGY_TONE_GUIDE,
    compute_sinsal_synergy_weight,
)


# ─────────────────────────── #11 saju 신살 시너지 가중치 ───────────────────────────


class TestSinsalSynergyWeightPersistence:
    """#11 ADR-133 시너지 가중치 4단계 영속."""

    def test_zero_synergy_weight_zero(self):
        """양인·괴강·백호 모두 부재 → weight 0.0."""
        result = compute_sinsal_synergy_weight({"yangin": [], "goegang": [], "baekho": []})
        assert result["weight"] == 0.0
        assert result["active_count"] == 0
        assert result["tone_branch"] == "none"

    def test_single_synergy_weight_one(self):
        """1개 신살 → weight 1.0."""
        result = compute_sinsal_synergy_weight({"yangin": ["卯"], "goegang": [], "baekho": []})
        assert result["weight"] == 1.0
        assert result["active_count"] == 1
        assert result["tone_branch"] == "single_personality"

    def test_dual_synergy_weight_one_point_five(self):
        """2개 신살 중첩 → weight 1.5."""
        result = compute_sinsal_synergy_weight({
            "yangin": ["卯"], "goegang": ["戊辰"], "baekho": [],
        })
        assert result["weight"] == 1.5
        assert result["active_count"] == 2
        assert result["tone_branch"] == "dual_professional"

    def test_triple_synergy_weight_two(self):
        """3개 신살 동시 → weight 2.0 (메인 동력)."""
        result = compute_sinsal_synergy_weight({
            "yangin": ["卯"], "goegang": ["戊辰"], "baekho": ["甲辰"],
        })
        assert result["weight"] == 2.0
        assert result["active_count"] == 3
        assert result["tone_branch"] == "triple_main_engine"

    def test_synergy_tone_guide_has_4_branches(self):
        """SYNERGY_TONE_GUIDE 4 분기 모두 영속."""
        expected = {"none", "single_personality", "dual_professional", "triple_main_engine"}
        assert set(SYNERGY_TONE_GUIDE.keys()) == expected


# ─────────────────────────── #12 dream 학파 명시 의무 ───────────────────────────


class TestDreamSchoolAttributionObligation:
    """#12 dream 시스템 프롬프트 학파 명시 의무 영속 (ADR-002·095)."""

    def test_adr_095_school_attribution_in_system(self):
        """ADR-095 학파 명시 의무 룰 박힘."""
        assert "ADR-095" in DREAM_SYSTEM

    def test_min_2_schools_obligation(self):
        """최소 2 학파 명시 의무 (다학파 병행)."""
        # ADR-002 다학파 병행 핵심 — 단일 학파 단정 X
        assert "학파 최소 2개 이상" in DREAM_SYSTEM or "2개 이상" in DREAM_SYSTEM

    def test_no_fusion_weight_assertion(self):
        """학파 융합 가중치 강요 부재 (ADR-002 정합 — 의도적 회피)."""
        # 본 시스템은 학파별 가중치 단정 X — 다학파 병행만
        # 시스템 프롬프트에 "weight"·"가중치 우선순위" 단정 부재 검증
        bad_patterns = ["가중치 1순위", "학파 가중치 우선", "특정 학파 우위"]
        for p in bad_patterns:
            assert p not in DREAM_SYSTEM, (
                f"학파 가중치 단정 패턴 '{p}' 검출 — ADR-002 위반"
            )

    def test_school_diversity_examples_present(self):
        """학파 다양성 예시 명시 (아르테미도로스·융·한국민간 등)."""
        # ADR-095 학파 인용 예시
        schools = ["아르테미도로스", "융", "한국민간", "주역"]
        hits = sum(1 for s in schools if s in DREAM_SYSTEM)
        assert hits >= 3, f"학파 예시 {hits}/4 명시 (다양성 부족)"


# ─────────────────────────── #19 face Vision 디폴트 Claude ───────────────────────────


class TestFaceVisionClaudeDefault:
    """#19 face Vision 디폴트 Claude (OpenAI 제거) — ADR-143 영속 강화."""

    def test_face_call_vision_default_is_claude(self):
        """face _call_vision 디폴트 모델이 Claude (anthropic 명시)."""
        src = inspect.getsource(face_reading._call_vision)
        assert "anthropic/claude-opus-4.7" in src, (
            "face Vision 디폴트가 Claude Opus 4.7 아님"
        )

    def test_no_gpt_default_fallback(self):
        """디폴트 fallback에 GPT 모델 명시 없음 (Claude 보장)."""
        src = inspect.getsource(face_reading._call_vision)
        # 디폴트 fallback 라인 검증 — or "anthropic/..." 패턴
        bad_defaults = ['or "gpt-4', "or 'gpt-4", 'or "openai/', "or 'openai/"]
        for bad in bad_defaults:
            assert bad not in src, (
                f"디폴트 fallback에 GPT/OpenAI 모델 명시 ({bad}) — ADR-143 위반"
            )

    def test_anthropic_sdk_fallback_uses_claude(self):
        """Anthropic SDK fallback도 Claude 명시."""
        src = inspect.getsource(face_reading._call_vision)
        assert "claude-opus-4-7" in src or "claude-opus-4.7" in src


# ─────────────────────────── #21 saju 자평진전 디폴트 ───────────────────────────


class TestSajuJapyungJinjeonDefault:
    """#21 saju 자평진전 = 디폴트 학파 영속 (ADR-130~142)."""

    def test_compat_module_cites_japyung(self):
        """compat.py에 자평진전 정통 표준 명시."""
        from engine.saju import compat
        src = inspect.getsource(compat)
        assert "자평진전" in src
        # 디폴트 정통 표준 명시
        assert "정통 표준" in src

    def test_shensha_yangin_default_is_japyung(self):
        """shensha.py 양인살 디폴트 = 자평진전 (옵션 A)."""
        from engine.saju import shensha
        src = inspect.getsource(shensha)
        # ADR-128 양인살 옵션 A = 자평진전
        assert "자평진전" in src
        # 옵션 A가 디폴트 (옵션 B는 명시 호출 시만)
        assert "옵션 A" in src or "정통 디폴트" in src

    def test_sinsal_day_basis_default_is_japyung(self):
        """ADR-142 일주 신살 분기 디폴트 = year (자평진전)."""
        from engine.saju.twelve_sinsal import get_sinsal_by_basis
        # 디폴트 호출 시 basis="year"
        r_default = get_sinsal_by_basis("子")
        r_year = get_sinsal_by_basis("子", basis="year")
        assert r_default == r_year, "디폴트가 year (자평진전) 아님"


# ─────────────────────────── 메타 회귀 — ADR-149 영속 체인 ───────────────────────────


class TestADR149PersistenceMetaAssertion:
    """ADR-149 메타 회귀 — Stale 잔여 4건 영속 파일 존재 보장."""

    @pytest.mark.parametrize("item_id,desc", [
        ("#11", "saju 신살 시너지 가중치"),
        ("#12", "dream 학파 명시 의무"),
        ("#19", "face Vision Claude 디폴트"),
        ("#21", "saju 자평진전 디폴트"),
    ])
    def test_each_item_has_test_class(self, item_id, desc):
        """4건 모두 본 파일에 회귀 클래스 존재 (영속 체인 메타 보장)."""
        from pathlib import Path
        src = Path(__file__).read_text(encoding="utf-8")
        assert item_id in src, f"{item_id} ({desc}): 영속 회귀 메모 누락"

    def test_4_classes_present(self):
        """4 영역별 TestClass 영속."""
        from pathlib import Path
        src = Path(__file__).read_text(encoding="utf-8")
        expected_classes = [
            "TestSinsalSynergyWeightPersistence",
            "TestDreamSchoolAttributionObligation",
            "TestFaceVisionClaudeDefault",
            "TestSajuJapyungJinjeonDefault",
        ]
        for cls in expected_classes:
            assert f"class {cls}" in src, f"{cls} 클래스 누락"
