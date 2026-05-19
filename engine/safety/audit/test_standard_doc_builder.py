"""engine.safety.audit.standard_doc_builder — §14.5 회귀 테스트."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 마크다운 ───────────────────────────

def test_markdown_starts_with_header_ko():
    from engine.safety.audit.standard_doc_builder import build_markdown_report
    md = build_markdown_report(lang="ko")
    assert md.startswith("# 운영표준 점검 보고서")


def test_markdown_starts_with_header_en():
    from engine.safety.audit.standard_doc_builder import build_markdown_report
    md = build_markdown_report(lang="en")
    assert md.startswith("# Operational Standard Compliance Report")


def test_markdown_contains_coverage():
    from engine.safety.audit.standard_doc_builder import build_markdown_report
    md = build_markdown_report()
    assert "Coverage:" in md
    assert "%" in md


def test_markdown_contains_items_section():
    from engine.safety.audit.standard_doc_builder import build_markdown_report
    md = build_markdown_report()
    assert "## Items" in md
    # 적어도 알려진 항목이 한두 개 등장
    assert "5.2.4_jailbreak_defense" in md


def test_markdown_includes_evidence_when_requested():
    from engine.safety.audit.standard_doc_builder import build_markdown_report
    md = build_markdown_report(include_evidence=True)
    assert "Symbols (verified)" in md


def test_markdown_omits_evidence_when_disabled():
    from engine.safety.audit.standard_doc_builder import build_markdown_report
    md = build_markdown_report(include_evidence=False)
    assert "Symbols (verified)" not in md


def test_markdown_marks_implemented_items_ok():
    from engine.safety.audit.standard_doc_builder import build_markdown_report
    md = build_markdown_report()
    # 현재 시스템은 100% 구현 → "MISSING" 라인이 거의 없어야
    assert "— OK" in md


# ─────────────────────────── JSON ───────────────────────────

def test_json_summary_has_top_level_fields():
    from engine.safety.audit.standard_doc_builder import build_json_summary
    d = build_json_summary()
    for k in ("service", "generated_at_utc", "coverage_percent",
              "implemented_count", "total_items", "missing_items",
              "anchors_covered", "items"):
        assert k in d


def test_json_summary_service_is_face_reading():
    from engine.safety.audit.standard_doc_builder import build_json_summary
    d = build_json_summary()
    assert d["service"] == "face_reading"


def test_json_summary_coverage_is_float():
    from engine.safety.audit.standard_doc_builder import build_json_summary
    d = build_json_summary()
    assert isinstance(d["coverage_percent"], float)
    assert 0 <= d["coverage_percent"] <= 100


def test_json_summary_items_have_required_fields():
    from engine.safety.audit.standard_doc_builder import build_json_summary
    d = build_json_summary()
    assert len(d["items"]) > 0
    for it in d["items"]:
        for k in ("item_id", "implemented", "module", "evidence_count",
                  "missing_symbols", "anchors", "error"):
            assert k in it


def test_json_string_is_valid_json():
    from engine.safety.audit.standard_doc_builder import build_json_string
    s = build_json_string()
    parsed = json.loads(s)
    assert isinstance(parsed, dict)
    assert parsed["service"] == "face_reading"


def test_json_string_indented():
    from engine.safety.audit.standard_doc_builder import build_json_string
    s = build_json_string(indent=2)
    assert "\n  " in s  # 2-space indent


# ─────────────────────────── 감사 letter ───────────────────────────

def test_audit_letter_korean_format():
    from engine.safety.audit.standard_doc_builder import build_audit_letter
    letter = build_audit_letter()
    assert "수신:" in letter
    assert "face_reading 운영팀" in letter
    assert "운영표준 점검 결과 통보" in letter


def test_audit_letter_custom_organization():
    from engine.safety.audit.standard_doc_builder import build_audit_letter
    letter = build_audit_letter(organization="개인정보보호위원회")
    assert "개인정보보호위원회" in letter


def test_audit_letter_includes_coverage_count():
    from engine.safety.audit.standard_doc_builder import build_audit_letter
    letter = build_audit_letter()
    assert "점검 항목" in letter
    assert "구현 완료" in letter


def test_audit_letter_lists_key_regulations():
    from engine.safety.audit.standard_doc_builder import build_audit_letter
    letter = build_audit_letter()
    # 주요 규제 앵커가 본문에 나타남
    assert "GDPR" in letter or "EU AI Act" in letter or "KR PIPA" in letter


def test_audit_letter_mentions_self_check_module():
    from engine.safety.audit.standard_doc_builder import build_audit_letter
    letter = build_audit_letter()
    assert "run_quick_check" in letter or "build_markdown_report" in letter


# ─────────────────────────── 결정론 ───────────────────────────

def test_json_summary_idempotent_in_same_second():
    """같은 시점 두 호출은 generated_at_utc만 다르고 구조는 동일."""
    from engine.safety.audit.standard_doc_builder import build_json_summary
    a = build_json_summary()
    b = build_json_summary()
    # items / coverage 등은 동일
    assert a["coverage_percent"] == b["coverage_percent"]
    assert a["total_items"] == b["total_items"]
    assert len(a["items"]) == len(b["items"])


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_standard_doc_builder():
    import engine.safety as safety
    assert hasattr(safety, "build_markdown_report")
    assert hasattr(safety, "build_json_summary")
    assert hasattr(safety, "build_json_string")
    assert hasattr(safety, "build_audit_letter")
