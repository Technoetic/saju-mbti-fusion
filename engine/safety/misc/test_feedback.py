"""engine.safety.misc.feedback — §7.2.7 사용자 피드백 수집기 단위 테스트.

원칙 검증:
  · 익명 카운트만 (UID·본문·이미지 미저장)
  · 같은 풀이 같은 키 (결정론)
  · 무효 kind는 무시
  · 누적 통계의 비율 계산
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


@pytest.fixture(autouse=True)
def _isolated_feedback_file(monkeypatch, tmp_path):
    """각 테스트마다 임시 파일로 격리 — 다른 테스트와 상태 공유 방지."""
    from engine.safety import feedback
    monkeypatch.setattr(feedback, "_FEEDBACK_FILE", tmp_path / "feedback.json")


def test_reading_hash_deterministic():
    """같은 본문 → 같은 키."""
    from engine.safety.misc.feedback import reading_hash
    assert reading_hash("허허, 그대의 상이 잘 잡혀 있구먼.") == reading_hash("허허, 그대의 상이 잘 잡혀 있구먼.")
    assert len(reading_hash("test")) == 8


def test_reading_hash_different_text():
    """다른 본문 → 다른 키."""
    from engine.safety.misc.feedback import reading_hash
    assert reading_hash("A") != reading_hash("B")


def test_reading_hash_empty():
    from engine.safety.misc.feedback import reading_hash
    assert reading_hash("") == ""


def test_record_feedback_basic():
    """단일 피드백 기록 → get_reading_counts에서 +1."""
    from engine.safety.misc.feedback import record_feedback, get_reading_counts
    text = "허허, 시험이로세."
    assert record_feedback(text, "accuracy_yes") is True
    c = get_reading_counts(text)
    assert c is not None
    assert c["accuracy_yes"] == 1
    assert c["accuracy_no"] == 0


def test_record_feedback_invalid_kind():
    """무효 kind 무시."""
    from engine.safety.misc.feedback import record_feedback
    assert record_feedback("text", "invalid_kind") is False
    assert record_feedback("text", "") is False


def test_record_feedback_empty_text():
    """빈 본문 무시."""
    from engine.safety.misc.feedback import record_feedback
    assert record_feedback("", "accuracy_yes") is False


def test_record_feedback_multiple_kinds():
    """여러 종류 카운트 독립."""
    from engine.safety.misc.feedback import record_feedback, get_reading_counts
    text = "동일 풀이"
    record_feedback(text, "accuracy_yes")
    record_feedback(text, "accuracy_yes")
    record_feedback(text, "accuracy_no")
    record_feedback(text, "satisfaction_yes")
    record_feedback(text, "regenerate_count")
    c = get_reading_counts(text)
    assert c == {
        "accuracy_yes": 2,
        "accuracy_no": 1,
        "satisfaction_yes": 1,
        "satisfaction_no": 0,
        "regenerate_count": 1,
    }


def test_get_reading_counts_unknown_returns_none():
    """없는 본문 → None."""
    from engine.safety.misc.feedback import get_reading_counts
    assert get_reading_counts("never recorded") is None


def test_get_aggregate_stats_basic():
    """누적 통계 — 합계 + 비율."""
    from engine.safety.misc.feedback import record_feedback, get_aggregate_stats
    # 풀이 A: 정합 yes 3 / no 1
    for _ in range(3):
        record_feedback("풀이 A", "accuracy_yes")
    record_feedback("풀이 A", "accuracy_no")
    # 풀이 B: 만족도 yes 2 / no 8
    for _ in range(2):
        record_feedback("풀이 B", "satisfaction_yes")
    for _ in range(8):
        record_feedback("풀이 B", "satisfaction_no")
    s = get_aggregate_stats()
    assert s["total_readings_with_feedback"] == 2
    assert s["accuracy_yes"] == 3
    assert s["accuracy_no"] == 1
    assert s["satisfaction_yes"] == 2
    assert s["satisfaction_no"] == 8
    assert s["accuracy_rate"] == 0.75  # 3 / 4
    assert s["satisfaction_rate"] == 0.20  # 2 / 10


def test_get_aggregate_stats_empty():
    """데이터 없을 때 — 비율 None."""
    from engine.safety.misc.feedback import get_aggregate_stats
    s = get_aggregate_stats()
    assert s["total_readings_with_feedback"] == 0
    assert s["accuracy_rate"] is None
    assert s["satisfaction_rate"] is None


def test_anonymity_no_uid_in_storage():
    """저장 파일에 풀이 본문이 절대 포함되지 않음 (§7.2.7 원칙)."""
    from engine.safety import feedback
    text = "허허, 그대의 콧대가 곧으니"
    feedback.record_feedback(text, "accuracy_yes")
    raw = feedback._FEEDBACK_FILE.read_text(encoding="utf-8")
    assert "허허" not in raw
    assert "콧대" not in raw
    # 해시 키만 들어가야
    assert feedback.reading_hash(text) in raw


def test_engine_safety_exports_feedback():
    """engine.safety 패키지에서 함수 노출."""
    import engine.safety as safety
    assert hasattr(safety, "record_feedback")
    assert hasattr(safety, "get_aggregate_stats")
    assert hasattr(safety, "get_reading_counts")
    assert hasattr(safety, "reading_hash")
