"""engine.safety.onboarding_checklist — §14.6 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 매니페스트 ───────────────────────────

def test_all_items_have_required_fields():
    from engine.safety.onboarding_checklist import get_all_items
    for it in get_all_items():
        assert it.item_id
        assert it.phase
        assert it.title
        assert it.summary
        assert len(it.modules) >= 1
        assert it.estimated_minutes >= 0


def test_four_phases_present():
    from engine.safety.onboarding_checklist import (
        get_all_items, PHASE_DAY1, PHASE_WEEK1, PHASE_MONTH1, PHASE_ONGOING,
    )
    phases = {it.phase for it in get_all_items()}
    assert phases == {PHASE_DAY1, PHASE_WEEK1, PHASE_MONTH1, PHASE_ONGOING}


def test_each_phase_has_at_least_3_items():
    from engine.safety.onboarding_checklist import (
        get_items_by_phase, PHASE_DAY1, PHASE_WEEK1, PHASE_MONTH1, PHASE_ONGOING,
    )
    for p in (PHASE_DAY1, PHASE_WEEK1, PHASE_MONTH1, PHASE_ONGOING):
        items = get_items_by_phase(p)
        assert len(items) >= 3, f"{p} has only {len(items)} items"


def test_day1_includes_persona_and_crisis():
    from engine.safety.onboarding_checklist import (
        get_items_by_phase, PHASE_DAY1,
    )
    ids = {it.item_id for it in get_items_by_phase(PHASE_DAY1)}
    assert "d1_persona" in ids
    assert "d1_crisis" in ids
    assert "d1_pii" in ids


def test_month1_includes_gdpr_eu_governance():
    from engine.safety.onboarding_checklist import (
        get_items_by_phase, PHASE_MONTH1,
    )
    ids = {it.item_id for it in get_items_by_phase(PHASE_MONTH1)}
    assert "m1_gdpr_dsr" in ids
    assert "m1_eu_ai_act" in ids
    assert "m1_governance" in ids


def test_each_item_lists_at_least_one_module():
    from engine.safety.onboarding_checklist import get_all_items
    for it in get_all_items():
        assert all(m.startswith("engine.") for m in it.modules), \
            f"{it.item_id} has non-engine module path"


# ─────────────────────────── 단일 조회 ───────────────────────────

def test_get_item_known():
    from engine.safety.onboarding_checklist import get_item, PHASE_DAY1
    it = get_item("d1_persona")
    assert it is not None
    assert it.phase == PHASE_DAY1


def test_get_item_unknown_returns_none():
    from engine.safety.onboarding_checklist import get_item
    assert get_item("not_a_real_item") is None


# ─────────────────────────── 시간 추정 ───────────────────────────

def test_total_estimated_minutes_positive():
    from engine.safety.onboarding_checklist import total_estimated_minutes
    total = total_estimated_minutes()
    assert total > 0
    # 전체 학습 시간이 너무 짧지 않음 — 최소 5시간 (300분)
    assert total >= 300


def test_total_estimated_minutes_by_phase():
    from engine.safety.onboarding_checklist import (
        total_estimated_minutes, PHASE_DAY1, PHASE_MONTH1,
    )
    d1 = total_estimated_minutes(phase=PHASE_DAY1)
    m1 = total_estimated_minutes(phase=PHASE_MONTH1)
    assert d1 > 0
    assert m1 > 0
    # month1이 day1보다 길어야 (심화 학습)
    assert m1 > d1


# ─────────────────────────── 진행률 ───────────────────────────

def test_evaluate_progress_empty_status():
    from engine.safety.onboarding_checklist import (
        evaluate_progress, PHASE_DAY1,
    )
    r = evaluate_progress({})
    assert r["completed"] == 0
    assert r["completed_percent"] == 0.0
    assert r["next_phase"] == PHASE_DAY1  # 아무것도 안 했으면 Day1부터


def test_evaluate_progress_partial():
    from engine.safety.onboarding_checklist import (
        evaluate_progress, STATUS_COMPLETED, STATUS_IN_PROGRESS,
    )
    r = evaluate_progress({
        "d1_persona": STATUS_COMPLETED,
        "d1_crisis": STATUS_IN_PROGRESS,
    })
    assert r["completed"] == 1
    assert r["in_progress"] == 1
    assert r["completed_percent"] > 0


def test_evaluate_progress_day1_complete_moves_to_week1():
    from engine.safety.onboarding_checklist import (
        evaluate_progress, get_items_by_phase, STATUS_COMPLETED,
        PHASE_DAY1, PHASE_WEEK1,
    )
    # Day1 전체 완료
    statuses = {it.item_id: STATUS_COMPLETED
                for it in get_items_by_phase(PHASE_DAY1)}
    r = evaluate_progress(statuses)
    assert r["next_phase"] == PHASE_WEEK1


def test_evaluate_progress_all_complete():
    from engine.safety.onboarding_checklist import (
        evaluate_progress, get_all_items, STATUS_COMPLETED, PHASE_ONGOING,
    )
    statuses = {it.item_id: STATUS_COMPLETED for it in get_all_items()}
    r = evaluate_progress(statuses)
    assert r["completed"] == r["total"]
    assert r["completed_percent"] == 100.0
    # 모두 완료면 ongoing이 next
    assert r["next_phase"] == PHASE_ONGOING


def test_format_progress_text_includes_counts():
    from engine.safety.onboarding_checklist import (
        evaluate_progress, format_progress_text,
    )
    r = evaluate_progress({})
    text = format_progress_text(r)
    assert "Onboarding" in text
    assert "%" in text
    assert "next:" in text


# ─────────────────────────── 모듈 참조 일관성 ───────────────────────────

def test_referenced_modules_actually_importable():
    """체크리스트가 참조하는 모듈은 실제로 import 가능해야 (속성 path 제외)."""
    import importlib
    from engine.safety.onboarding_checklist import get_all_items
    for it in get_all_items():
        for module_path in it.modules:
            # "_FACE_SYSTEM" 같은 상수는 모듈명 외 . 뒤 속성 제거
            parts = module_path.split(".")
            # engine.divination.face_reading._FACE_SYSTEM → engine.divination.face_reading
            # 마지막 파트가 소문자가 아니면 (e.g. _FACE_SYSTEM) 잘라냄
            if parts[-1].startswith("_") or parts[-1].isupper():
                module_path = ".".join(parts[:-1])
            importlib.import_module(module_path)


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_onboarding_checklist():
    import engine.safety as safety
    assert hasattr(safety, "get_onboarding_items")
    assert hasattr(safety, "get_onboarding_items_by_phase")
    assert hasattr(safety, "evaluate_onboarding_progress")
    assert hasattr(safety, "ChecklistItem")
    assert hasattr(safety, "PHASE_DAY1")
    assert hasattr(safety, "PHASE_ONGOING")
    assert hasattr(safety, "STATUS_COMPLETED")
