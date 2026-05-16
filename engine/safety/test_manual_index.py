"""engine.safety.manual_index — §14.10 회귀 테스트."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 매니페스트 ───────────────────────────

def test_all_entries_have_required_fields():
    from engine.safety.manual_index import get_all_entries
    for e in get_all_entries():
        assert e.module.startswith("engine.safety.")
        assert e.standard_ref  # §x.x.x
        assert e.title
        assert e.category
        assert e.timing
        assert e.use_when
        assert len(e.key_apis) >= 1


def test_at_least_40_entries():
    """전체 안전 모듈 40개 이상 인덱싱."""
    from engine.safety.manual_index import get_all_entries
    assert len(get_all_entries()) >= 40


def test_every_module_is_importable():
    import importlib
    from engine.safety.manual_index import get_all_entries
    for e in get_all_entries():
        importlib.import_module(e.module)


def test_entries_have_unique_modules():
    from engine.safety.manual_index import get_all_entries
    modules = [e.module for e in get_all_entries()]
    assert len(modules) == len(set(modules))


# ─────────────────────────── 카테고리 ───────────────────────────

def test_find_input_guard():
    from engine.safety.manual_index import (
        find_by_category, CATEGORY_INPUT_GUARD,
    )
    items = find_by_category(CATEGORY_INPUT_GUARD)
    assert len(items) >= 3
    modules = {e.module for e in items}
    assert "engine.safety.jailbreak_defense" in modules
    assert "engine.safety.input_sanitizer" in modules


def test_find_output_guard():
    from engine.safety.manual_index import (
        find_by_category, CATEGORY_OUTPUT_GUARD,
    )
    items = find_by_category(CATEGORY_OUTPUT_GUARD)
    assert len(items) >= 5
    modules = {e.module for e in items}
    assert "engine.safety.persona_self_eval" in modules
    assert "engine.safety.response_pii_leak" in modules


def test_find_governance():
    from engine.safety.manual_index import (
        find_by_category, CATEGORY_GOVERNANCE,
    )
    items = find_by_category(CATEGORY_GOVERNANCE)
    modules = {e.module for e in items}
    assert "engine.safety.consent_screen" in modules
    assert "engine.safety.data_governance" in modules


def test_all_seven_categories_present():
    from engine.safety.manual_index import (
        find_by_category, CATEGORY_INPUT_GUARD, CATEGORY_OUTPUT_GUARD,
        CATEGORY_RUNTIME, CATEGORY_GOVERNANCE, CATEGORY_OBSERVABILITY,
        CATEGORY_INCIDENT, CATEGORY_DOCS,
    )
    for cat in (CATEGORY_INPUT_GUARD, CATEGORY_OUTPUT_GUARD,
                CATEGORY_RUNTIME, CATEGORY_GOVERNANCE,
                CATEGORY_OBSERVABILITY, CATEGORY_INCIDENT, CATEGORY_DOCS):
        assert len(find_by_category(cat)) >= 1, f"{cat} empty"


# ─────────────────────────── 사용 시점 ───────────────────────────

def test_find_by_timing_preflight():
    from engine.safety.manual_index import find_by_timing, TIMING_PREFLIGHT
    items = find_by_timing(TIMING_PREFLIGHT)
    assert len(items) >= 3


def test_find_by_timing_postflight():
    from engine.safety.manual_index import find_by_timing, TIMING_POSTFLIGHT
    items = find_by_timing(TIMING_POSTFLIGHT)
    assert len(items) >= 5


def test_find_by_timing_periodic():
    from engine.safety.manual_index import find_by_timing, TIMING_PERIODIC
    items = find_by_timing(TIMING_PERIODIC)
    assert len(items) >= 5


# ─────────────────────────── 심각도 ───────────────────────────

def test_find_p0_severity_modules():
    """P0 사고 대응에 쓰이는 모듈은 최소 3개."""
    from engine.safety.manual_index import find_by_severity
    items = find_by_severity("P0")
    assert len(items) >= 3
    modules = {e.module for e in items}
    assert "engine.safety.crisis_detector" in modules


# ─────────────────────────── 규제 ───────────────────────────

def test_find_gdpr_modules():
    from engine.safety.manual_index import find_by_regulation
    items = find_by_regulation("GDPR")
    assert len(items) >= 3
    modules = {e.module for e in items}
    assert "engine.safety.dsr_processor" in modules


def test_find_eu_ai_act_modules():
    from engine.safety.manual_index import find_by_regulation
    items = find_by_regulation("EU_AI_ACT")
    assert len(items) >= 2


def test_find_kr_pipa_modules():
    from engine.safety.manual_index import find_by_regulation
    items = find_by_regulation("KR_PIPA")
    assert len(items) >= 3


# ─────────────────────────── 단일 조회 ───────────────────────────

def test_get_entry_by_module_known():
    from engine.safety.manual_index import get_entry_by_module
    e = get_entry_by_module("engine.safety.jailbreak_defense")
    assert e is not None
    assert e.standard_ref == "§5.2.4"


def test_get_entry_by_module_unknown():
    from engine.safety.manual_index import get_entry_by_module
    assert get_entry_by_module("engine.safety.not_a_real") is None


# ─────────────────────────── 포맷 ───────────────────────────

def test_format_index_text_has_category_headers():
    from engine.safety.manual_index import format_index_text
    text = format_index_text()
    assert "# 운영 매뉴얼 인덱스" in text
    assert "## input_guard" in text
    assert "## output_guard" in text


def test_format_index_text_filtered():
    from engine.safety.manual_index import (
        format_index_text, find_by_category, CATEGORY_INCIDENT,
    )
    incidents = find_by_category(CATEGORY_INCIDENT)
    text = format_index_text(incidents)
    # 다른 카테고리는 등장 안 함
    assert "## input_guard" not in text


# ─────────────────────────── JSON ───────────────────────────

def test_json_summary_serializable():
    from engine.safety.manual_index import to_json_summary
    s = json.dumps(to_json_summary(), ensure_ascii=False)
    parsed = json.loads(s)
    assert parsed["total_entries"] >= 40


def test_json_summary_has_by_category():
    from engine.safety.manual_index import to_json_summary
    j = to_json_summary()
    assert "by_category" in j
    assert all(isinstance(v, int) for v in j["by_category"].values())


# ─────────────────────────── compliance와 일관성 ───────────────────────────

def test_modules_overlap_with_compliance_manifest():
    """manual_index의 모듈이 compliance_report의 매니페스트와 상당 부분 일치."""
    from engine.safety.manual_index import get_all_entries
    from engine.safety.compliance_report import COMPLIANCE_MANIFEST
    manual_modules = {e.module for e in get_all_entries()}
    compliance_modules = {v["module"] for v in COMPLIANCE_MANIFEST.values()}
    overlap = manual_modules & compliance_modules
    # 양쪽 다 안전 모듈을 인덱싱하므로 절반 이상은 겹쳐야
    assert len(overlap) >= 20


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_manual_index():
    import engine.safety as safety
    assert hasattr(safety, "ManualEntry")
    assert hasattr(safety, "get_manual_entries")
    assert hasattr(safety, "find_manual_by_category")
    assert hasattr(safety, "find_manual_by_timing")
    assert hasattr(safety, "find_manual_by_severity")
    assert hasattr(safety, "find_manual_by_regulation")
    assert hasattr(safety, "format_manual_index")
    assert hasattr(safety, "manual_index_to_json")
    assert hasattr(safety, "CATEGORY_INPUT_GUARD")
    assert hasattr(safety, "CATEGORY_OUTPUT_GUARD")
