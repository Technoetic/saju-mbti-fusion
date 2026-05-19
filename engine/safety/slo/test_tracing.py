"""engine.safety.slo.tracing — §7.3.4 로깅 회귀 테스트."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _capture(capsys) -> dict:
    """stdout에서 마지막 JSON 라인 파싱."""
    out = capsys.readouterr().out.strip()
    last = out.splitlines()[-1]
    return json.loads(last)


def test_emit_basic_event(capsys):
    from engine.safety.slo.tracing import emit_face_reading_event, _now_ms
    emit_face_reading_event(
        event_type="request_completed",
        request_started_at_ms=_now_ms() - 100,
    )
    ev = _capture(capsys)
    assert ev["event"] == "request_completed"
    assert ev["service"] == "face_reading"
    assert ev["elapsed_ms"] >= 0


def test_emit_uid_is_hashed(capsys):
    """UID 원본 절대 미저장 — 해시만 노출."""
    from engine.safety.slo.tracing import emit_face_reading_event, _now_ms
    emit_face_reading_event(
        event_type="request_completed",
        request_started_at_ms=_now_ms(),
        uid="user-secret-123",
    )
    ev = _capture(capsys)
    assert "uid" not in ev  # 원본 키 없음
    assert "uid_hash" in ev
    assert "user-secret-123" not in json.dumps(ev)


def test_emit_question_hash_and_length_no_body(capsys):
    """원본 화두 본문은 저장되지 않고 해시·길이만."""
    from engine.safety.slo.tracing import emit_face_reading_event, _now_ms
    q = "올해 내가 결혼할 수 있을까"
    emit_face_reading_event(
        event_type="request_completed",
        request_started_at_ms=_now_ms(),
        question=q,
    )
    ev = _capture(capsys)
    assert "question" not in ev
    assert "question_hash" in ev
    assert ev["question_len"] == len(q)
    assert q not in json.dumps(ev, ensure_ascii=False)


def test_emit_age_bucketed(capsys):
    """나이는 버킷으로 — 개별 노출 방지."""
    from engine.safety.slo.tracing import emit_face_reading_event, _now_ms
    for age, expected in [(15, "minor"), (25, "20s"), (45, "40s"), (75, "70+")]:
        emit_face_reading_event(
            event_type="request_completed",
            request_started_at_ms=_now_ms(),
            age=age,
        )
        ev = _capture(capsys)
        assert ev["age_bucket"] == expected
        assert "age" not in ev  # 원본 노출 X


def test_emit_extra_masks_pii(capsys):
    """extra에 이메일·전화 들어가도 자동 마스킹."""
    from engine.safety.slo.tracing import emit_face_reading_event, _now_ms
    emit_face_reading_event(
        event_type="request_completed",
        request_started_at_ms=_now_ms(),
        extra={"note": "고객 hello@example.com 또는 010-1234-5678"},
    )
    ev = _capture(capsys)
    assert "[EMAIL]" in ev["extra"]["note"]
    assert "[PHONE]" in ev["extra"]["note"]
    assert "hello@example.com" not in json.dumps(ev, ensure_ascii=False)


def test_emit_crisis_and_error_flags(capsys):
    from engine.safety.slo.tracing import emit_face_reading_event, _now_ms
    emit_face_reading_event(
        event_type="crisis_blocked",
        request_started_at_ms=_now_ms(),
        crisis_detected=True,
        error_code="ERR_FACE_NOT_DETECTED",
    )
    ev = _capture(capsys)
    assert ev["crisis_detected"] is True
    assert ev["error_code"] == "ERR_FACE_NOT_DETECTED"


def test_emit_metrics_keys_only_not_values(capsys):
    """메트릭 키 이름만 — 값(수치) 노출 X."""
    from engine.safety.slo.tracing import emit_face_reading_event, _now_ms
    emit_face_reading_event(
        event_type="request_completed",
        request_started_at_ms=_now_ms(),
        metrics_keys=["three_thirds", "alar_ratio", "face_shape"],
    )
    ev = _capture(capsys)
    assert ev["metrics_keys"] == ["alar_ratio", "face_shape", "three_thirds"]


def test_emit_jsonl_format(capsys):
    """단일 JSON 라인 — 줄바꿈으로 구분되는 jsonl."""
    from engine.safety.slo.tracing import emit_face_reading_event, _now_ms
    emit_face_reading_event(event_type="a", request_started_at_ms=_now_ms())
    emit_face_reading_event(event_type="b", request_started_at_ms=_now_ms())
    out = capsys.readouterr().out
    lines = [l for l in out.strip().splitlines() if l]
    assert len(lines) == 2
    for line in lines:
        json.loads(line)  # 각 라인 파싱 가능


# ─────────────────────────── 컨텍스트 매니저 ───────────────────────────

def test_trace_context_manager_emits_on_exit(capsys):
    from engine.safety.slo.tracing import FaceReadingTrace
    with FaceReadingTrace(region="KR") as tr:
        tr.set(error_code="ERR_FACE_NOT_DETECTED")
    ev = _capture(capsys)
    assert ev["event"] == "request_completed"
    assert ev["region"] == "KR"
    assert ev["error_code"] == "ERR_FACE_NOT_DETECTED"


def test_trace_emits_failure_on_exception(capsys):
    from engine.safety.slo.tracing import FaceReadingTrace
    with pytest.raises(RuntimeError):
        with FaceReadingTrace(region="US-CA"):
            raise RuntimeError("test exception")
    ev = _capture(capsys)
    assert ev["event"] == "request_failed"
    # exception은 extra에 들어감
    assert ev["extra"]["exception"] == "RuntimeError"


def test_trace_set_overrides_initial(capsys):
    from engine.safety.slo.tracing import FaceReadingTrace
    with FaceReadingTrace(region="KR") as tr:
        tr.set(region="US-CA")  # override
    ev = _capture(capsys)
    assert ev["region"] == "US-CA"


def test_engine_safety_exports_tracing():
    import engine.safety as safety
    assert hasattr(safety, "FaceReadingTrace")
    assert hasattr(safety, "emit_face_reading_event")
