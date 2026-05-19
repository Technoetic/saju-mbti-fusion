"""engine.safety.audit.compliance_report — §14.4 자체 점검 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 매니페스트 ───────────────────────────

def test_manifest_has_all_safety_items():
    """매니페스트에 §5/§7/§10/§14 핵심 항목이 모두 포함."""
    from engine.safety.audit.compliance_report import COMPLIANCE_MANIFEST
    expected_prefixes = ("5.2.4", "5.2.5", "5.2.6", "5.2.7", "5.2.8",
                         "7.1", "7.2.5", "7.2.9", "7.2.10", "7.2.11",
                         "7.2.13", "7.2.14", "7.2.15", "7.2.16", "7.2.17",
                         "7.2.18", "7.2.19", "7.2.20", "7.2.21", "7.2.22",
                         "7.2.23",
                         "7.3.2", "7.3.3", "7.3.4", "7.3.5", "7.3.6",
                         "7.3.8", "7.3.9",
                         "10_", "14.1", "14.2", "14.3")
    keys = list(COMPLIANCE_MANIFEST.keys())
    for prefix in expected_prefixes:
        assert any(k.startswith(prefix) for k in keys), f"missing prefix: {prefix}"


def test_manifest_eu_ai_act_present():
    from engine.safety.audit.compliance_report import COMPLIANCE_MANIFEST
    assert any("EU_AI_Act" in k for k in COMPLIANCE_MANIFEST.keys())


def test_manifest_entries_have_required_fields():
    from engine.safety.audit.compliance_report import COMPLIANCE_MANIFEST
    for k, v in COMPLIANCE_MANIFEST.items():
        assert "module" in v, f"{k} missing module"
        assert "symbols" in v, f"{k} missing symbols"
        assert "anchors" in v, f"{k} missing anchors"
        assert len(v["symbols"]) >= 1


# ─────────────────────────── 단일 항목 ───────────────────────────

def test_check_item_implemented():
    from engine.safety.audit.compliance_report import check_item
    r = check_item("5.2.4_jailbreak_defense")
    assert r.implemented is True
    assert "detect_jailbreak" in r.evidence
    assert r.module == "engine.safety.llm.jailbreak_defense"


def test_check_item_unknown_returns_error():
    from engine.safety.audit.compliance_report import check_item
    r = check_item("not_a_real_item")
    assert r.implemented is False
    assert "unknown_item" in r.error


def test_check_item_missing_symbol_caught():
    """존재하지 않는 심볼이 매니페스트에 있으면 missing으로 보고."""
    from engine.safety.audit.compliance_report import check_item
    manifest = {
        "test_missing": {
            "module": "engine.safety.llm.jailbreak_defense",
            "symbols": ("detect_jailbreak", "nonexistent_function"),
            "anchors": ("test",),
        },
    }
    r = check_item("test_missing", manifest=manifest)
    assert r.implemented is False
    assert "detect_jailbreak" in r.evidence
    assert "nonexistent_function" in r.missing_symbols


def test_check_item_unimportable_module():
    from engine.safety.audit.compliance_report import check_item
    manifest = {
        "test_unimportable": {
            "module": "engine.safety.this_does_not_exist",
            "symbols": ("foo",),
            "anchors": (),
        },
    }
    r = check_item("test_unimportable", manifest=manifest)
    assert r.implemented is False
    assert "import_failed" in r.error


# ─────────────────────────── 전체 보고서 ───────────────────────────

def test_generate_report_high_coverage():
    """현재 시스템은 90% 이상 커버리지 달성."""
    from engine.safety.audit.compliance_report import generate_report
    r = generate_report()
    assert r.coverage_percent >= 90.0
    assert r.implemented_count >= 30


def test_generate_report_all_known_items_implemented():
    """모든 매니페스트 항목이 구현되어 있어야 함.

    ADR-053: 5.2.7 crisis_multilingual·7.2.1 photo_quality·7.2.6 a11y 모두 구현.
    """
    from engine.safety.audit.compliance_report import generate_report
    r = generate_report()
    assert r.missing_items == []
    assert r.coverage_percent == 100.0


def test_generate_report_includes_regulatory_anchors():
    from engine.safety.audit.compliance_report import generate_report
    r = generate_report()
    # 주요 규제 앵커가 보고서에 등장
    anchors_blob = " ".join(r.anchors_covered)
    assert "GDPR" in anchors_blob
    assert "EU AI Act" in anchors_blob
    assert "KR PIPA" in anchors_blob


def test_generate_report_subset_manifest():
    from engine.safety.audit.compliance_report import generate_report
    small = {
        "5.2.4_jailbreak_defense": {
            "module": "engine.safety.llm.jailbreak_defense",
            "symbols": ("detect_jailbreak",),
            "anchors": ("test",),
        },
    }
    r = generate_report(manifest=small)
    assert r.total_items == 1
    assert r.coverage_percent == 100.0


def test_generate_report_partial_coverage():
    from engine.safety.audit.compliance_report import generate_report
    mixed = {
        "real": {
            "module": "engine.safety.llm.jailbreak_defense",
            "symbols": ("detect_jailbreak",),
            "anchors": ("test",),
        },
        "fake": {
            "module": "engine.safety.this_does_not_exist",
            "symbols": ("foo",),
            "anchors": ("test",),
        },
    }
    r = generate_report(manifest=mixed)
    assert r.total_items == 2
    assert r.implemented_count == 1
    assert r.coverage_percent == 50.0
    assert "fake" in r.missing_items


# ─────────────────────────── 포맷 ───────────────────────────

def test_format_report_text_includes_coverage():
    from engine.safety.audit.compliance_report import generate_report, format_report_text
    r = generate_report()
    text = format_report_text(r)
    assert "Compliance Report" in text
    assert "coverage=" in text


def test_format_report_lists_missing():
    from engine.safety.audit.compliance_report import generate_report, format_report_text
    mixed = {
        "fake_x": {
            "module": "engine.safety.does_not_exist",
            "symbols": ("foo",), "anchors": (),
        },
    }
    r = generate_report(manifest=mixed)
    text = format_report_text(r)
    assert "MISSING" in text
    assert "fake_x" in text


# ─────────────────────────── 규제 앵커 매핑 ───────────────────────────

def test_dsr_processor_anchors_include_gdpr():
    from engine.safety.audit.compliance_report import check_item
    r = check_item("10_dsr_processor")
    assert any("GDPR" in a for a in r.regulatory_anchors)
    assert any("PIPA" in a for a in r.regulatory_anchors)


def test_emotion_disclosure_anchors_include_eu_ai_act():
    from engine.safety.audit.compliance_report import check_item
    r = check_item("EU_AI_Act_Art50_3")
    assert any("EU AI Act" in a for a in r.regulatory_anchors)


def test_data_governance_anchors_include_consent_law():
    from engine.safety.audit.compliance_report import check_item
    r = check_item("7.3.3_data_governance")
    assert any("GDPR" in a for a in r.regulatory_anchors)


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_compliance_report():
    import engine.safety as safety
    assert hasattr(safety, "generate_compliance_report")
    assert hasattr(safety, "check_compliance_item")
    assert hasattr(safety, "ComplianceReport")
    assert hasattr(safety, "ItemReport")
    assert hasattr(safety, "COMPLIANCE_MANIFEST")
