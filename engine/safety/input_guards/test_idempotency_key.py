"""engine.safety.input_guards.idempotency_key — §7.2.14 멱등 키 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 키 생성 결정론 ───────────────────────────

def test_key_is_deterministic():
    from engine.safety.input_guards.idempotency_key import compute_idempotency_key
    a = compute_idempotency_key(image_b64="abc", question="q", uid="u1")
    b = compute_idempotency_key(image_b64="abc", question="q", uid="u1")
    assert a == b


def test_key_length_24():
    from engine.safety.input_guards.idempotency_key import compute_idempotency_key
    k = compute_idempotency_key(image_b64="x", question="y", uid="z")
    assert len(k) == 24


def test_different_image_yields_different_key():
    from engine.safety.input_guards.idempotency_key import compute_idempotency_key
    a = compute_idempotency_key(image_b64="img1", question="q", uid="u")
    b = compute_idempotency_key(image_b64="img2", question="q", uid="u")
    assert a != b


def test_different_question_yields_different_key():
    from engine.safety.input_guards.idempotency_key import compute_idempotency_key
    a = compute_idempotency_key(image_b64="img", question="q1", uid="u")
    b = compute_idempotency_key(image_b64="img", question="q2", uid="u")
    assert a != b


def test_different_uid_yields_different_key():
    from engine.safety.input_guards.idempotency_key import compute_idempotency_key
    a = compute_idempotency_key(image_b64="img", question="q", uid="u1")
    b = compute_idempotency_key(image_b64="img", question="q", uid="u2")
    assert a != b


def test_extra_dimension_yields_different_key():
    from engine.safety.input_guards.idempotency_key import compute_idempotency_key
    a = compute_idempotency_key(image_b64="x", question="y", uid="z", extra="ko")
    b = compute_idempotency_key(image_b64="x", question="y", uid="z", extra="en")
    assert a != b


def test_none_inputs_safe():
    """None은 빈 문자열로 처리되어 예외 없이 키 생성."""
    from engine.safety.input_guards.idempotency_key import compute_idempotency_key
    k = compute_idempotency_key(image_b64=None, question=None, uid=None)
    assert len(k) == 24


# ─────────────────────────── 슬롯 선점 ───────────────────────────

def test_first_claim_succeeds():
    from engine.safety.input_guards.idempotency_key import (
        IdempotencyManager, SLOT_PENDING,
    )
    mgr = IdempotencyManager()
    claimed, slot = mgr.claim("k1", now=1000.0)
    assert claimed is True
    assert slot.state == SLOT_PENDING


def test_second_claim_within_window_blocked():
    from engine.safety.input_guards.idempotency_key import IdempotencyManager
    mgr = IdempotencyManager(window_sec=60)
    mgr.claim("k1", now=1000.0)
    claimed, slot = mgr.claim("k1", now=1030.0)  # 30초 후
    assert claimed is False
    # 두 번째 호출자는 첫 슬롯을 받음
    assert slot.key == "k1"


def test_claim_after_window_can_re_acquire():
    from engine.safety.input_guards.idempotency_key import IdempotencyManager
    mgr = IdempotencyManager(window_sec=60)
    mgr.claim("k1", now=1000.0)
    claimed, _ = mgr.claim("k1", now=1100.0)  # 100초 후 (윈도우 초과)
    assert claimed is True


def test_different_keys_independent():
    from engine.safety.input_guards.idempotency_key import IdempotencyManager
    mgr = IdempotencyManager()
    c1, _ = mgr.claim("a", now=1000.0)
    c2, _ = mgr.claim("b", now=1000.0)
    assert c1 is True
    assert c2 is True


# ─────────────────────────── 결과 등록 ───────────────────────────

def test_resolve_updates_slot():
    from engine.safety.input_guards.idempotency_key import (
        IdempotencyManager, SLOT_RESOLVED,
    )
    mgr = IdempotencyManager()
    mgr.claim("k1", now=1000.0)
    mgr.resolve("k1", result={"text": "허허"})
    slot = mgr.get("k1")
    assert slot is not None
    assert slot.state == SLOT_RESOLVED
    assert slot.result == {"text": "허허"}


def test_second_caller_receives_resolved_result():
    """첫 호출자가 resolve 후 두 번째 호출자는 같은 결과를 받음."""
    from engine.safety.input_guards.idempotency_key import (
        IdempotencyManager, SLOT_RESOLVED,
    )
    mgr = IdempotencyManager(window_sec=60)
    c1, _ = mgr.claim("k1", now=1000.0)
    assert c1 is True
    mgr.resolve("k1", result={"text": "허허"})
    # 30초 후 동시 요청
    c2, slot2 = mgr.claim("k1", now=1030.0)
    assert c2 is False
    assert slot2.state == SLOT_RESOLVED
    assert slot2.result == {"text": "허허"}


def test_fail_marks_slot_failed():
    from engine.safety.input_guards.idempotency_key import (
        IdempotencyManager, SLOT_FAILED,
    )
    mgr = IdempotencyManager()
    mgr.claim("k1", now=1000.0)
    mgr.fail("k1", error="LLM timeout")
    slot = mgr.get("k1")
    assert slot is not None
    assert slot.state == SLOT_FAILED
    assert slot.error == "LLM timeout"


def test_resolve_unknown_key_is_noop():
    from engine.safety.input_guards.idempotency_key import IdempotencyManager
    mgr = IdempotencyManager()
    mgr.resolve("nonexistent", result={"x": 1})  # 예외 없이 무시
    assert mgr.get("nonexistent") is None


# ─────────────────────────── 만료 청소 ───────────────────────────

def test_purge_expired_removes_old_slots():
    from engine.safety.input_guards.idempotency_key import IdempotencyManager
    mgr = IdempotencyManager(window_sec=60)
    mgr.claim("a", now=1000.0)
    mgr.claim("b", now=1500.0)
    assert mgr.size() == 2
    removed = mgr.purge_expired(now=1100.0)  # a는 만료(100초 후), b는 유지(-400초)
    # b는 미래 timestamp이므로 만료 아님 → a만 제거
    assert removed == 1
    assert mgr.size() == 1


def test_purge_expired_returns_count():
    from engine.safety.input_guards.idempotency_key import IdempotencyManager
    mgr = IdempotencyManager(window_sec=60)
    mgr.claim("a", now=1000.0)
    mgr.claim("b", now=1000.0)
    mgr.claim("c", now=1000.0)
    removed = mgr.purge_expired(now=2000.0)
    assert removed == 3
    assert mgr.size() == 0


def test_reset_clears_all_slots():
    from engine.safety.input_guards.idempotency_key import IdempotencyManager
    mgr = IdempotencyManager()
    mgr.claim("a", now=1000.0)
    mgr.claim("b", now=1000.0)
    mgr.reset()
    assert mgr.size() == 0


# ─────────────────────────── 트레이스 페이로드 ───────────────────────────

def test_trace_event_claimed():
    from engine.safety.input_guards.idempotency_key import (
        to_trace_event, SLOT_PENDING,
    )
    e = to_trace_event(key="abc", claimed=True, slot_state=SLOT_PENDING)
    assert e["idempotency_key"] == "abc"
    assert e["idempotency_claimed"] is True
    assert e["idempotency_slot_state"] == SLOT_PENDING


def test_trace_event_dedup_hit():
    from engine.safety.input_guards.idempotency_key import (
        to_trace_event, SLOT_RESOLVED,
    )
    e = to_trace_event(key="abc", claimed=False, slot_state=SLOT_RESOLVED)
    assert e["idempotency_claimed"] is False
    assert e["idempotency_slot_state"] == SLOT_RESOLVED


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_idempotency_key():
    import engine.safety as safety
    assert hasattr(safety, "compute_idempotency_key")
    assert hasattr(safety, "IdempotencyManager")
    assert hasattr(safety, "IdempotencySlot")
    assert hasattr(safety, "SLOT_PENDING")
    assert hasattr(safety, "SLOT_RESOLVED")
    assert hasattr(safety, "SLOT_FAILED")
    assert hasattr(safety, "DEFAULT_WINDOW_SEC")
