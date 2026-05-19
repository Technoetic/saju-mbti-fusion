"""engine.safety.audit.changelog_tracker — §14.12 회귀 테스트."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _fresh_store():
    from engine.safety.audit.changelog_tracker import ChangelogStore
    return ChangelogStore()


# ─────────────────────────── 기본 record ───────────────────────────

def test_record_change_basic():
    from engine.safety.audit.changelog_tracker import CHANGE_ADDED, REASON_IMPROVEMENT
    store = _fresh_store()
    e = store.record_change(
        change_type=CHANGE_ADDED,
        standard_ref="§7.2.99",
        module="engine.safety.new_thing",
        summary="신규 모듈 추가",
        reason=REASON_IMPROVEMENT,
    )
    assert e.change_type == CHANGE_ADDED
    assert e.timestamp_iso  # 자동 채워짐
    assert store.size() == 1


def test_record_change_with_explicit_timestamp():
    from engine.safety.audit.changelog_tracker import CHANGE_MODIFIED, REASON_REGULATION
    store = _fresh_store()
    e = store.record_change(
        change_type=CHANGE_MODIFIED,
        standard_ref="§14.X",
        module="engine.safety.x",
        summary="EU AI Act 발효 대응",
        reason=REASON_REGULATION,
        now_iso="2026-05-15T10:00:00+00:00",
    )
    assert e.timestamp_iso == "2026-05-15T10:00:00+00:00"


def test_record_change_breaking_flag():
    from engine.safety.audit.changelog_tracker import (
        CHANGE_REMOVED, REASON_DEPRECATION,
    )
    store = _fresh_store()
    e = store.record_change(
        change_type=CHANGE_REMOVED,
        standard_ref="§7.2.0",
        module="engine.safety.legacy",
        summary="레거시 모듈 제거",
        reason=REASON_DEPRECATION,
        breaking=True,
    )
    assert e.breaking is True


def test_record_change_with_metadata():
    from engine.safety.audit.changelog_tracker import CHANGE_MODIFIED, REASON_INCIDENT
    store = _fresh_store()
    e = store.record_change(
        change_type=CHANGE_MODIFIED,
        standard_ref="§5.2.7",
        module="engine.safety.crisis.detector",
        summary="zh 키워드 추가",
        reason=REASON_INCIDENT,
        related_incident="crisis_block_failed",
        related_pr="https://github.com/example/saju/pull/123",
        metadata={"keywords_added": 12},
    )
    assert e.related_incident == "crisis_block_failed"
    assert e.metadata["keywords_added"] == 12


# ─────────────────────────── 필터 ───────────────────────────

def test_by_change_type():
    from engine.safety.audit.changelog_tracker import (
        CHANGE_ADDED, CHANGE_REMOVED, REASON_IMPROVEMENT,
    )
    store = _fresh_store()
    store.record_change(change_type=CHANGE_ADDED, standard_ref="§A", module="m1",
                        summary="a", reason=REASON_IMPROVEMENT)
    store.record_change(change_type=CHANGE_REMOVED, standard_ref="§B", module="m2",
                        summary="b", reason=REASON_IMPROVEMENT)
    assert len(store.by_change_type(CHANGE_ADDED)) == 1
    assert len(store.by_change_type(CHANGE_REMOVED)) == 1


def test_by_module():
    from engine.safety.audit.changelog_tracker import CHANGE_MODIFIED, REASON_IMPROVEMENT
    store = _fresh_store()
    store.record_change(change_type=CHANGE_MODIFIED, standard_ref="§A",
                        module="engine.safety.a", summary="x",
                        reason=REASON_IMPROVEMENT)
    store.record_change(change_type=CHANGE_MODIFIED, standard_ref="§A",
                        module="engine.safety.a", summary="y",
                        reason=REASON_IMPROVEMENT)
    store.record_change(change_type=CHANGE_MODIFIED, standard_ref="§B",
                        module="engine.safety.b", summary="z",
                        reason=REASON_IMPROVEMENT)
    a = store.by_module("engine.safety.a")
    assert len(a) == 2


def test_by_reason():
    from engine.safety.audit.changelog_tracker import (
        CHANGE_MODIFIED, REASON_INCIDENT, REASON_REGULATION,
    )
    store = _fresh_store()
    store.record_change(change_type=CHANGE_MODIFIED, standard_ref="§A",
                        module="m", summary="x", reason=REASON_INCIDENT)
    store.record_change(change_type=CHANGE_MODIFIED, standard_ref="§B",
                        module="m", summary="y", reason=REASON_REGULATION)
    assert len(store.by_reason(REASON_INCIDENT)) == 1
    assert len(store.by_reason(REASON_REGULATION)) == 1


def test_by_incident():
    from engine.safety.audit.changelog_tracker import (
        CHANGE_MODIFIED, REASON_INCIDENT,
    )
    store = _fresh_store()
    store.record_change(change_type=CHANGE_MODIFIED, standard_ref="§A",
                        module="m", summary="x", reason=REASON_INCIDENT,
                        related_incident="crisis_block_failed")
    store.record_change(change_type=CHANGE_MODIFIED, standard_ref="§B",
                        module="m", summary="y", reason=REASON_INCIDENT,
                        related_incident="pii_leak_detected")
    assert len(store.by_incident("crisis_block_failed")) == 1


def test_breaking_changes_only():
    from engine.safety.audit.changelog_tracker import CHANGE_REMOVED, REASON_DEPRECATION
    store = _fresh_store()
    store.record_change(change_type=CHANGE_REMOVED, standard_ref="§A", module="m1",
                        summary="x", reason=REASON_DEPRECATION, breaking=True)
    store.record_change(change_type=CHANGE_REMOVED, standard_ref="§B", module="m2",
                        summary="y", reason=REASON_DEPRECATION, breaking=False)
    bk = store.breaking_changes()
    assert len(bk) == 1
    assert bk[0].module == "m1"


# ─────────────────────────── since ───────────────────────────

def test_since_filters_by_timestamp():
    from engine.safety.audit.changelog_tracker import CHANGE_ADDED, REASON_IMPROVEMENT
    store = _fresh_store()
    store.record_change(change_type=CHANGE_ADDED, standard_ref="§A", module="m",
                        summary="early", reason=REASON_IMPROVEMENT,
                        now_iso="2026-01-01T00:00:00+00:00")
    store.record_change(change_type=CHANGE_ADDED, standard_ref="§B", module="m",
                        summary="late", reason=REASON_IMPROVEMENT,
                        now_iso="2026-06-01T00:00:00+00:00")
    recent = store.since("2026-03-01T00:00:00+00:00")
    assert len(recent) == 1
    assert recent[0].summary == "late"


# ─────────────────────────── reset ───────────────────────────

def test_reset_clears_all():
    from engine.safety.audit.changelog_tracker import CHANGE_ADDED, REASON_IMPROVEMENT
    store = _fresh_store()
    store.record_change(change_type=CHANGE_ADDED, standard_ref="§A", module="m",
                        summary="x", reason=REASON_IMPROVEMENT)
    assert store.size() == 1
    store.reset()
    assert store.size() == 0


# ─────────────────────────── 직렬화 ───────────────────────────

def test_entry_to_dict():
    from engine.safety.audit.changelog_tracker import (
        CHANGE_ADDED, REASON_IMPROVEMENT, entry_to_dict,
    )
    store = _fresh_store()
    e = store.record_change(change_type=CHANGE_ADDED, standard_ref="§A",
                            module="m", summary="x", reason=REASON_IMPROVEMENT)
    d = entry_to_dict(e)
    for k in ("timestamp_iso", "change_type", "standard_ref", "module",
              "summary", "reason", "breaking", "metadata"):
        assert k in d


def test_to_jsonl_lines_valid_json():
    from engine.safety.audit.changelog_tracker import (
        CHANGE_ADDED, REASON_IMPROVEMENT, to_jsonl_lines,
    )
    store = _fresh_store()
    store.record_change(change_type=CHANGE_ADDED, standard_ref="§A", module="m",
                        summary="x", reason=REASON_IMPROVEMENT)
    store.record_change(change_type=CHANGE_ADDED, standard_ref="§B", module="m",
                        summary="y", reason=REASON_IMPROVEMENT)
    lines = to_jsonl_lines(store.all())
    assert len(lines) == 2
    for line in lines:
        parsed = json.loads(line)
        assert "change_type" in parsed


# ─────────────────────────── 텍스트 포맷 ───────────────────────────

def test_format_changelog_includes_count():
    from engine.safety.audit.changelog_tracker import (
        CHANGE_ADDED, REASON_IMPROVEMENT, format_changelog_text,
    )
    store = _fresh_store()
    store.record_change(change_type=CHANGE_ADDED, standard_ref="§A", module="m",
                        summary="x", reason=REASON_IMPROVEMENT)
    text = format_changelog_text(store.all())
    assert "Changelog" in text
    assert "1 entries" in text


def test_format_changelog_sorts_newest_first():
    from engine.safety.audit.changelog_tracker import (
        CHANGE_ADDED, REASON_IMPROVEMENT, format_changelog_text,
    )
    store = _fresh_store()
    store.record_change(change_type=CHANGE_ADDED, standard_ref="§A", module="m",
                        summary="older", reason=REASON_IMPROVEMENT,
                        now_iso="2026-01-01T00:00:00+00:00")
    store.record_change(change_type=CHANGE_ADDED, standard_ref="§B", module="m",
                        summary="newer", reason=REASON_IMPROVEMENT,
                        now_iso="2026-06-01T00:00:00+00:00")
    text = format_changelog_text(store.all())
    # newer가 older보다 먼저 등장
    assert text.find("newer") < text.find("older")


def test_format_changelog_shows_breaking_flag():
    from engine.safety.audit.changelog_tracker import (
        CHANGE_REMOVED, REASON_DEPRECATION, format_changelog_text,
    )
    store = _fresh_store()
    store.record_change(change_type=CHANGE_REMOVED, standard_ref="§A", module="m",
                        summary="x", reason=REASON_DEPRECATION, breaking=True)
    text = format_changelog_text(store.all())
    assert "[BREAKING]" in text


# ─────────────────────────── 글로벌 인스턴스 ───────────────────────────

def test_default_store_is_singleton():
    from engine.safety.audit.changelog_tracker import get_default_store
    a = get_default_store()
    b = get_default_store()
    assert a is b


def test_record_change_module_function_records_to_default():
    """모듈 수준 record_change()는 DEFAULT_STORE에 기록."""
    from engine.safety.audit.changelog_tracker import (
        record_change, get_default_store,
        CHANGE_ADDED, REASON_IMPROVEMENT,
    )
    store = get_default_store()
    initial = store.size()
    record_change(
        change_type=CHANGE_ADDED, standard_ref="§TEST", module="m",
        summary="test", reason=REASON_IMPROVEMENT,
    )
    assert store.size() == initial + 1
    # cleanup
    store.reset()


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_changelog_tracker():
    import engine.safety as safety
    assert hasattr(safety, "ChangelogEntry")
    assert hasattr(safety, "ChangelogStore")
    assert hasattr(safety, "CHANGE_ADDED")
    assert hasattr(safety, "CHANGE_MODIFIED")
    assert hasattr(safety, "CHANGE_REMOVED")
    assert hasattr(safety, "REASON_INCIDENT")
    assert hasattr(safety, "record_change_log")
    assert hasattr(safety, "get_changelog_store")
