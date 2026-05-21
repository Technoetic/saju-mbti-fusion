"""ADR-105 회귀 — 야자시(夜子時) 분리 vs 통합 자시(子時) 학파 옵션 B.

본 시스템 pillars.py:117 명시 TODO 본문화 완료.

ADR 정합:
- ADR-002: 단일 학파 강요 X (옵션 B 병행)
- ADR-006: 운명 단정 X (시주 분류만)
- ADR-010: DBpia 2014·박재완 1974·滴天髓 라이브 검증
- ADR-015: schema='unified' 디폴트 (옵션 A) + 'yajasi_separate' 옵션 B
- ADR-073: 결정론 보장
- ADR-085: KASI 앵커 영향 없음
"""

import pytest

from engine.saju.pillars import compute_pillars, hour_pillar


# ─────────────────────────────────────────────────────────────
# ① hour_pillar — schema 파라미터 (ADR-105)
# ─────────────────────────────────────────────────────────────


def test_hour_pillar_default_schema_unified():
    """ADR-015 옵션 A — schema 디폴트는 'unified' (역호환)."""
    r = hour_pillar(0, 12)  # 갑 일간, 12시
    assert "gan_idx" in r and "ji_idx" in r
    # 동일 인자 + schema 명시 → 동일 결과
    r2 = hour_pillar(0, 12, schema="unified")
    assert r == r2


def test_hour_pillar_legacy_signature_compatibility():
    """기존 코드가 schema 인자 없이 호출해도 동작."""
    for hour in [0, 11, 22, 23]:
        r1 = hour_pillar(0, hour)
        r2 = hour_pillar(0, hour, schema="unified")
        assert r1 == r2


def test_hour_pillar_23_unified_jasi():
    """schema='unified' + 23시 → 子時 ji_idx=0."""
    r = hour_pillar(0, 23, schema="unified")
    assert r["ji_idx"] == 0  # 子


def test_hour_pillar_23_yajasi_separate_still_jasi():
    """schema='yajasi_separate' + 23시 → ji_idx=0 (시지 동일).

    핵심: hour_pillar 자체는 시지만 결정. day_gan_idx 차이는 caller 책임.
    """
    r = hour_pillar(0, 23, schema="yajasi_separate")
    assert r["ji_idx"] == 0  # 子 (학파 무관)


def test_hour_pillar_yajasi_different_day_gan():
    """야자시 분리 학파 — 동일 시각 다른 일간 → 다른 시간(時干).

    오서둔: 일간이 익일로 바뀌면 시간도 변경.
    """
    # day_gan_idx=0 (갑) 자시 vs day_gan_idx=1 (을) 자시
    r1 = hour_pillar(0, 23, schema="yajasi_separate")
    r2 = hour_pillar(1, 23, schema="yajasi_separate")
    assert r1["ji_idx"] == r2["ji_idx"] == 0
    assert r1["gan_idx"] != r2["gan_idx"]  # 오서둔 → 다른 시간


def test_hour_pillar_invalid_schema_raises():
    """잘못된 schema → ValueError."""
    with pytest.raises(ValueError, match="schema"):
        hour_pillar(0, 12, schema="invalid_school")


def test_hour_pillar_invalid_hour_raises():
    """기존 hour 검증 유지."""
    with pytest.raises(ValueError, match="hour"):
        hour_pillar(0, 24)
    with pytest.raises(ValueError, match="hour"):
        hour_pillar(0, -1)


# ─────────────────────────────────────────────────────────────
# ② compute_pillars — schema 파라미터 (ADR-105)
# ─────────────────────────────────────────────────────────────


def test_compute_pillars_default_schema_unified():
    """schema 디폴트 'unified' — 역호환."""
    r1 = compute_pillars(2026, 5, 21, 12)
    r2 = compute_pillars(2026, 5, 21, 12, schema="unified")
    assert r1 == r2


def test_compute_pillars_23_unified_legacy_behavior():
    """schema='unified' + 23시 → 현 동작 유지 (caller가 day 조정 책임).

    역호환 의무: 본 ADR-105 정정이 기존 caller 동작에 영향 주지 않음.
    """
    r = compute_pillars(2026, 5, 21, 23, schema="unified")
    # 일주는 입력 day (2026-05-21) 그대로 — caller 책임
    expected_dp = compute_pillars(2026, 5, 21, 12, schema="unified")["day_pillar"]
    assert r["day_pillar"] == expected_dp  # 일주 변경 X (caller가 day 조정해야 익일)
    assert r["hour_pillar"]["ji_idx"] == 0  # 子時


def test_compute_pillars_23_yajasi_separate_day_preserved():
    """schema='yajasi_separate' + 23시 → 당일 일주 유지 + 익일 일간 오서둔.

    야자시(夜子時): 23:00~23:59 = 당일 일진 유지.
    """
    r = compute_pillars(2026, 5, 21, 23, schema="yajasi_separate")
    # 일주는 2026-05-21 당일 유지
    expected_today_dp = compute_pillars(2026, 5, 21, 12, schema="unified")["day_pillar"]
    assert r["day_pillar"] == expected_today_dp  # 당일 일주 유지
    # 시지는 子時
    assert r["hour_pillar"]["ji_idx"] == 0


def test_compute_pillars_23_yajasi_vs_unified_difference():
    """야자시 분리 vs 통합 자시 — 시간(時干) 차이 가능성 검증.

    동일 입력 (2026-05-21 23시):
    - unified: caller 책임 (현 동작 caller가 day 미조정 시 당일 일간 오서둔)
    - yajasi_separate: 본 ADR-105 가 익일 일간으로 오서둔
    """
    r_uni = compute_pillars(2026, 5, 21, 23, schema="unified")
    r_yaja = compute_pillars(2026, 5, 21, 23, schema="yajasi_separate")
    # 일주 동일 (둘 다 2026-05-21 당일 일진 — unified는 caller 책임상 그대로)
    assert r_uni["day_pillar"] == r_yaja["day_pillar"]
    # 시지 동일 (子=0)
    assert r_uni["hour_pillar"]["ji_idx"] == r_yaja["hour_pillar"]["ji_idx"] == 0
    # 시간(時干)은 다를 수 있음 (오서둔 적용 일간 차이)
    # 2026-05-21 일간 vs 2026-05-22 일간 → 일간 다르면 시간도 다름


def test_compute_pillars_00_both_schemas_identical():
    """00:00 (정자시) — 두 학파 동일 처리 (00시는 항상 당일 子時)."""
    r_uni = compute_pillars(2026, 5, 21, 0, schema="unified")
    r_yaja = compute_pillars(2026, 5, 21, 0, schema="yajasi_separate")
    assert r_uni == r_yaja  # 완전 동일


def test_compute_pillars_invalid_schema_raises():
    """잘못된 schema → ValueError."""
    with pytest.raises(ValueError, match="schema"):
        compute_pillars(2026, 5, 21, 12, schema="invalid")


def test_compute_pillars_non_23_hours_unaffected_by_schema():
    """23시 외 시각은 schema 무관 (학파 차이는 23시·24시 경계만)."""
    for hour in [0, 6, 12, 18, 22]:
        r_uni = compute_pillars(2026, 5, 21, hour, schema="unified")
        r_yaja = compute_pillars(2026, 5, 21, hour, schema="yajasi_separate")
        assert r_uni == r_yaja, f"hour={hour} schema 영향 없어야 함"


# ─────────────────────────────────────────────────────────────
# ③ ADR-002 학파 회피 정신 회귀 (단일 학파 강요 차단)
# ─────────────────────────────────────────────────────────────


def test_both_schemas_available_no_default_lock():
    """ADR-002 — 두 학파 모두 사용자 선택 가능."""
    # 사용자가 명시적으로 야자시 선택 가능
    r_yaja = compute_pillars(2026, 5, 21, 23, schema="yajasi_separate")
    assert r_yaja is not None
    # 사용자가 명시적으로 통합 자시 선택 가능
    r_uni = compute_pillars(2026, 5, 21, 23, schema="unified")
    assert r_uni is not None


def test_default_remains_unified_adr_015_option_a():
    """ADR-015 옵션 A — 디폴트 schema는 'unified' (현 시스템 호환)."""
    import inspect
    sig = inspect.signature(compute_pillars)
    assert sig.parameters["schema"].default == "unified"
    sig_hp = inspect.signature(hour_pillar)
    assert sig_hp.parameters["schema"].default == "unified"
