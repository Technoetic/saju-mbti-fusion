"""ADR-154 회귀 — /domain-priorities 잔여 5건 본 AI 단독 부분 해소.

대상:
  · #1 tojeong 144괘 본문화 진행도 영속 (tojeong_verse_coverage_stats)
  · #2 palm ML 학습 파이프라인 스켈레톤 (training_skeleton.py)
  · #3 hwapae 마케팅 메시지 채택 슬롯 (marketing_slots.py)
  · #4 학파 토글 실 페이지 마운트 (saju-ui.js renderResult)
"""
from __future__ import annotations

from pathlib import Path

import pytest

INDEX_HTML = Path("front/index.html")
SAJU_UI_JS = Path("front/js/core/saju-ui.js")


@pytest.fixture(scope="module")
def index_html_src() -> str:
    return INDEX_HTML.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def saju_ui_src() -> str:
    return SAJU_UI_JS.read_text(encoding="utf-8")


class TestIndexHtmlSchoolToggleCss:
    """front/index.html school-toggle.css 로드 영속."""

    def test_css_link_present(self, index_html_src: str):
        assert 'href="styles/school-toggle.css"' in index_html_src


class TestSajuUiMount:
    """front/js/core/saju-ui.js 학파 토글 3종 마운트 영속."""

    def test_three_container_slots_present(self, saju_ui_src: str):
        """3 컨테이너 div 영속."""
        for cid in (
            "saju-school-toggle-guk",
            "saju-school-toggle-sinsal",
            "saju-school-toggle-synergy",
        ):
            assert f'id="{cid}"' in saju_ui_src, f"컨테이너 '{cid}' 누락"

    def test_dynamic_import_pattern(self, saju_ui_src: str):
        """동적 import 패턴 (../ui/school-toggle.js)."""
        assert "import('../ui/school-toggle.js')" in saju_ui_src

    def test_three_options_pools_referenced(self, saju_ui_src: str):
        """3 옵션 풀 (GUK · SINSAL_BASIS · SYNERGY) 참조."""
        for opt in (
            "SAJU_GUK_STRENGTH_OPTIONS",
            "SAJU_SINSAL_BASIS_OPTIONS",
            "SAJU_SYNERGY_SCHOOL_OPTIONS",
        ):
            assert opt in saju_ui_src, f"옵션 풀 '{opt}' 참조 누락"

    def test_localstorage_persistence(self, saju_ui_src: str):
        """localStorage 학파 선택 영속 (다음 호출 시 디폴트)."""
        for key in (
            "whm.school.guk",
            "whm.school.sinsal_basis",
            "whm.school.synergy",
        ):
            assert key in saju_ui_src, f"localStorage 키 '{key}' 누락"

    def test_adr_refs_in_mount(self, saju_ui_src: str):
        """3 마운트에 ADR 참조 (141·142·153) 명시."""
        for adr in ("ADR-141", "ADR-142", "ADR-153"):
            assert adr in saju_ui_src, f"마운트 ADR 참조 '{adr}' 누락"


# ─────────────────────────── #1 tojeong 144괘 본문화 진행도 ───────────────────────────


class TestTojeongVerseCoverage:
    """#1 tojeong 144괘 원문 본문화 진행도 영속 정직 메타."""

    def test_coverage_stats_full_keys(self):
        from engine.divination.tojeong.scoring import tojeong_verse_coverage_stats
        s = tojeong_verse_coverage_stats()
        for k in ("total", "with_original_verse", "synthesized_only", "coverage_pct",
                  "confidence_breakdown", "by_source_school"):
            assert k in s, f"진행도 필드 '{k}' 누락"

    def test_total_144(self):
        from engine.divination.tojeong.scoring import tojeong_verse_coverage_stats
        assert tojeong_verse_coverage_stats()["total"] == 144

    def test_adr134_11_hexagrams_with_verse(self):
        """ADR-134 11괘 본문화 영속."""
        from engine.divination.tojeong.scoring import tojeong_verse_coverage_stats
        assert tojeong_verse_coverage_stats()["with_original_verse"] == 11

    def test_get_verse_source_status_original(self):
        from engine.divination.tojeong.scoring import get_verse_source_status
        # hex_id=0은 ADR-134 본문화된 괘
        s = get_verse_source_status(0)
        assert s["status"] == "original"
        assert s["confidence"] == "HIGH"

    def test_get_verse_source_status_synthesized(self):
        from engine.divination.tojeong.scoring import get_verse_source_status
        # hex_id=10은 본문화 X (133괘 중 하나)
        s = get_verse_source_status(10)
        assert s["status"] == "synthesized"
        assert "김수년" in s["note"]  # RISS 출처 정직 명시

    def test_get_verse_source_status_invalid(self):
        from engine.divination.tojeong.scoring import get_verse_source_status
        s = get_verse_source_status(999)
        assert s["status"] == "invalid"


# ─────────────────────────── #2 palm 학습 파이프라인 스켈레톤 ───────────────────────────


class TestPalmTrainingSkeleton:
    """#2 palm ML 학습 파이프라인 스켈레톤 영속."""

    def test_module_importable(self):
        from engine.divination.palm import training_skeleton  # noqa: F401

    def test_dataclasses_present(self):
        from engine.divination.palm.training_skeleton import (
            PalmKeypoint, PalmLineMetric, PalmTrainingConfig,
        )
        assert PalmKeypoint and PalmLineMetric and PalmTrainingConfig

    def test_keypoint_iou_metric(self):
        from engine.divination.palm.training_skeleton import (
            PalmKeypoint, compute_keypoint_iou,
        )
        gt = (PalmKeypoint(x=0.5, y=0.5, confidence=1.0),)
        pr = (PalmKeypoint(x=0.51, y=0.51, confidence=0.9),)
        score = compute_keypoint_iou(pr, gt)
        assert score == 1.0  # 임계 0.05 이내

    def test_line_metric_mae(self):
        from engine.divination.palm.training_skeleton import (
            PalmLineMetric, compute_line_metric_mae,
        )
        a = PalmLineMetric("life", 0.7, 0.5, 0.8, ())
        b = PalmLineMetric("life", 0.6, 0.4, 0.7, ())
        mae = compute_line_metric_mae(a, b)
        assert abs(mae["length_mae"] - 0.1) < 1e-9

    def test_train_blocked_without_fair_use(self):
        """fair_use_acknowledged=False → NotImplementedError (가짜 학습 차단)."""
        import pytest as _pytest
        from engine.divination.palm.training_skeleton import (
            PalmTrainingConfig, train_palm_model,
        )
        cfg = PalmTrainingConfig(dataset_root="/tmp/none", fair_use_acknowledged=False)
        with _pytest.raises(NotImplementedError, match="fair_use_acknowledged"):
            train_palm_model(cfg)


# ─────────────────────────── #3 hwapae 마케팅 메시지 슬롯 ───────────────────────────


class TestHwapaeMarketingSlots:
    """#3 hwapae 마케팅 메시지 5 후보 + ADR-006 정합."""

    def test_5_candidates_present(self):
        from engine.divination.hwapae.marketing_slots import MARKETING_CANDIDATES
        assert len(MARKETING_CANDIDATES) == 5

    def test_active_default_academic(self):
        from engine.divination.hwapae.marketing_slots import (
            ACTIVE_MARKETING_KEY, get_active_marketing_message,
        )
        assert ACTIVE_MARKETING_KEY == "academic_kci"
        assert get_active_marketing_message().key == "academic_kci"

    def test_all_5_adr_006_compliant(self):
        """5 후보 모두 ADR-006 단정 어휘 0건."""
        from engine.divination.hwapae.marketing_slots import (
            list_marketing_candidates, validate_adr_006_compliance,
        )
        for m in list_marketing_candidates():
            ok, viol = validate_adr_006_compliance(m)
            assert ok, f"{m.key} ADR-006 위반: {viol}"

    def test_target_demos_diverse(self):
        """20대·30대+·40대+ 다양성 보장 (사업 결단 폭)."""
        from engine.divination.hwapae.marketing_slots import list_marketing_candidates
        demos = {m.target_demo for m in list_marketing_candidates()}
        assert len(demos) >= 3, f"타겟 데모 다양성 부족: {demos}"

    def test_validation_catches_assertion(self):
        """단정 어휘 포함 메시지 → 위반 검출."""
        from engine.divination.hwapae.marketing_slots import (
            MarketingMessage, validate_adr_006_compliance,
        )
        bad = MarketingMessage(
            key="bad", headline="반드시 적중하는 화투",
            body="100% 정확한 풀이", tone="casual", target_demo="20대",
        )
        ok, viol = validate_adr_006_compliance(bad)
        assert not ok
        assert "반드시" in viol
        assert "100%" in viol
