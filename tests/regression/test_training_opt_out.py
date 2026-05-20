"""ADR-062 회귀 — RLHF·모델 학습 거부 권리 (opt-out) 검증."""

import time

from engine.safety.gdpr.training_opt_out import (
    user_hash,
    set_opt_out,
    is_opted_out,
    get_record,
    get_aggregate_stats,
)


def test_user_hash_anonymizes_uid():
    """UID 원본 저장 X — 해시 앞 16자만 사용."""
    h = user_hash("user@example.com")
    assert len(h) == 16
    assert h.isalnum()
    # 다른 UID는 다른 해시
    assert user_hash("user@example.com") != user_hash("other@example.com")
    # 동일 UID는 동일 해시
    assert user_hash("user@example.com") == user_hash("user@example.com")


def test_user_hash_empty():
    """빈 UID는 빈 해시."""
    assert user_hash("") == ""


def test_default_opt_in():
    """미설정 사용자는 opt-in (학습 허용) 디폴트."""
    uid = f"new_user_{time.time()}"
    assert is_opted_out(uid) is False
    assert get_record(uid) is None


def test_set_opt_out_persists():
    """opt-out 설정 후 영속 저장 + 조회."""
    uid = f"test_optout_{time.time()}"
    record = set_opt_out(uid, opted_out=True)
    assert record.opted_out is True
    assert record.user_hash == user_hash(uid)

    # 재조회
    assert is_opted_out(uid) is True
    loaded = get_record(uid)
    assert loaded is not None
    assert loaded.opted_out is True


def test_toggle_back_to_opt_in():
    """opt-out → opt-in 토글 변경 영속."""
    uid = f"test_toggle_{time.time()}"
    set_opt_out(uid, opted_out=True)
    assert is_opted_out(uid) is True

    set_opt_out(uid, opted_out=False)
    assert is_opted_out(uid) is False


def test_change_log_tracks_history():
    """토글 변경 이력 추적 (감사 로그)."""
    uid = f"test_audit_{time.time()}"
    set_opt_out(uid, opted_out=True)
    time.sleep(0.01)  # 시간 차이 보장
    set_opt_out(uid, opted_out=False)
    time.sleep(0.01)
    set_opt_out(uid, opted_out=True)

    record = get_record(uid)
    assert record is not None
    # 3회 변경 (True → False → True), 각 변경마다 로그 추가
    assert len(record.change_log) >= 3


def test_same_value_no_duplicate_log():
    """동일 값 재설정 시 로그 추가 X."""
    uid = f"test_dedup_{time.time()}"
    set_opt_out(uid, opted_out=True)
    initial_log_len = len(get_record(uid).change_log)
    set_opt_out(uid, opted_out=True)  # 동일 값
    final_log_len = len(get_record(uid).change_log)
    assert final_log_len == initial_log_len


def test_aggregate_stats_no_pii():
    """전체 통계는 PII 미포함."""
    stats = get_aggregate_stats()
    assert "total_users_with_preference" in stats
    assert "opted_out_count" in stats
    assert "opted_in_count" in stats
    # PII 필드 부재
    assert "user_hash" not in stats
    assert "user_id" not in stats


def test_empty_user_id_rejected():
    """빈 user_id는 ValueError."""
    import pytest
    with pytest.raises(ValueError):
        set_opt_out("", True)
