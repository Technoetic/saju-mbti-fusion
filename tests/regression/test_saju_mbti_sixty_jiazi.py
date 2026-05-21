"""ADR-108 회귀 — 60갑자 일주별 MBTI 4축 가중치 보정 검증.

영역:
  · 60갑자 전부 영속
  · 가중치 결정론 (동일 일주 → 동일 가중치)
  · ADR-014 단정 회피 (미정 → 라벨 강제 전환 X)
  · 면책 자동 포함
"""

from engine.divination.saju_mbti.sixty_jiazi_weights import (
    SIXTY_JIAZI,
    get_axis_weights,
    apply_jiazi_weight_to_axis,
)


# ─────────────────────────── 60갑자 영속 ───────────────────────────

def test_sixty_jiazi_count():
    """60갑자 전부 영속."""
    assert len(SIXTY_JIAZI) == 60


def test_sixty_jiazi_unique():
    """60갑자 중복 없음."""
    assert len(set(SIXTY_JIAZI)) == 60


def test_first_jiazi_is_gapja():
    """첫 갑자는 '甲子'."""
    assert SIXTY_JIAZI[0] == "甲子"


def test_last_jiazi_is_gyehae():
    """마지막은 '癸亥'."""
    assert SIXTY_JIAZI[59] == "癸亥"


# ─────────────────────────── 가중치 결정론 ───────────────────────────

def test_axis_weights_deterministic():
    """동일 일주 → 동일 가중치."""
    w1 = get_axis_weights("甲子")
    w2 = get_axis_weights("甲子")
    assert w1 == w2


def test_axis_weights_all_60_callable():
    """60갑자 전부 가중치 산출 가능."""
    for jz in SIXTY_JIAZI:
        w = get_axis_weights(jz)
        assert w is not None, f"{jz} 가중치 산출 실패"


def test_axis_weights_invalid_returns_none():
    """잘못된 입력 → None."""
    assert get_axis_weights("") is None
    assert get_axis_weights("甲") is None  # 1글자
    assert get_axis_weights("甲子丑") is None  # 3글자
    assert get_axis_weights("XX") is None
    assert get_axis_weights("甲A") is None  # 지지 잘못


def test_axis_weights_range():
    """모든 가중치 -0.20 ~ +0.20 범위."""
    for jz in SIXTY_JIAZI:
        w = get_axis_weights(jz)
        assert w is not None
        for weight in (w.ei_weight, w.sn_weight, w.tf_weight, w.jp_weight):
            assert -0.20 <= weight <= 0.20, f"{jz}: {weight} 범위 초과"


# ─────────────────────────── 정합 검증 ───────────────────────────

def test_gapja_weight_sum():
    """甲子 = 갑(+0.05) + 자(-0.05) = 0.0 (E_I)."""
    w = get_axis_weights("甲子")
    assert w is not None
    assert w.ei_weight == 0.0


def test_byeong_oh_extrovert():
    """丙午 = 양화 + 양화·양지 — E 강한 보정."""
    w = get_axis_weights("丙午")
    assert w is not None
    # 丙(+0.08) + 午(+0.08) = +0.16
    assert w.ei_weight == 0.16


def test_gye_hae_introvert():
    """癸亥 = 음수 + 음지·수 — E_I는 음수+양 = 약함."""
    w = get_axis_weights("癸亥")
    assert w is not None
    # 癸(-0.05) + 亥(+0.03) = -0.02
    assert w.ei_weight == -0.02


def test_rationale_includes_disclaimer():
    """rationale에 면책 자동 포함."""
    w = get_axis_weights("甲子")
    assert w is not None
    assert "본 시스템 자체 룰" in w.rationale
    assert "MBTI 검사 대체 X" in w.rationale


# ─────────────────────────── ADR-014 단정 회피 ───────────────────────────

def test_apply_weight_preserves_uncertain():
    """미정 라벨은 보정해도 미정 유지 (ADR-014)."""
    result = apply_jiazi_weight_to_axis("미정", "E_I", 0.20)
    assert result == "미정"


def test_apply_weight_no_force_label_switch():
    """본 시스템 자체 룰: 60갑자 보정은 라벨 강제 전환 X (ADR-014)."""
    # 단정 회피 — base_label 그대로 유지
    result = apply_jiazi_weight_to_axis("E", "E_I", 0.20)
    assert result == "E"
    result = apply_jiazi_weight_to_axis("I", "E_I", -0.20)
    assert result == "I"


def test_apply_weight_below_threshold_preserved():
    """임계값 미만 변화 → 라벨 유지."""
    result = apply_jiazi_weight_to_axis("E", "E_I", 0.03)
    assert result == "E"


# ─────────────────────────── 240 매트릭스 ───────────────────────────

def test_240_weight_matrix():
    """60갑자 × 4축 = 240 가중치 모두 산출."""
    total = 0
    for jz in SIXTY_JIAZI:
        w = get_axis_weights(jz)
        assert w is not None
        # 각 일주당 4축 가중치
        for _ in (w.ei_weight, w.sn_weight, w.tf_weight, w.jp_weight):
            total += 1
    assert total == 240
