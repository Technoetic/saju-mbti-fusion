"""ADR-184 - 표정 잡음 검출 회귀."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_none_blendshapes_passes():
    from engine.safety.photo.expression_noise import detect_expression_noise
    r = detect_expression_noise(None)
    assert r.blocked is False
    assert r.warned is False


def test_empty_blendshapes_passes():
    from engine.safety.photo.expression_noise import detect_expression_noise
    r = detect_expression_noise({})
    assert r.blocked is False
    assert r.warned is False


def test_neutral_face_passes():
    """무표정 — 모든 blendshape ≈ 0."""
    from engine.safety.photo.expression_noise import detect_expression_noise
    bs = {
        "mouthSmileLeft": 0.02, "mouthSmileRight": 0.03,
        "eyeBlinkLeft": 0.05, "eyeBlinkRight": 0.05,
        "browInnerUp": 0.01,
        "jawOpen": 0.02,
    }
    r = detect_expression_noise(bs)
    assert r.blocked is False
    assert r.warned is False


def test_strong_smile_blocked():
    """강한 웃음 → mouth 차단."""
    from engine.safety.photo.expression_noise import (
        detect_expression_noise, EXPR_NOISE_MOUTH,
    )
    bs = {
        "mouthSmileLeft": 0.6, "mouthSmileRight": 0.55,
    }
    r = detect_expression_noise(bs)
    assert r.blocked is True
    assert r.category == EXPR_NOISE_MOUTH
    assert "무표정" in r.user_message


def test_strong_eye_blink_blocked():
    """강한 눈 감음 → eye 차단."""
    from engine.safety.photo.expression_noise import (
        detect_expression_noise, EXPR_NOISE_EYE,
    )
    bs = {
        "eyeBlinkLeft": 0.7, "eyeBlinkRight": 0.65,
    }
    r = detect_expression_noise(bs)
    assert r.blocked is True
    assert r.category == EXPR_NOISE_EYE


def test_multiple_strong_blocked():
    """입 + 눈썹 동시 강한 표정 → multiple 차단."""
    from engine.safety.photo.expression_noise import (
        detect_expression_noise, EXPR_NOISE_MULTIPLE,
    )
    bs = {
        "mouthSmileLeft": 0.5,
        "browInnerUp": 0.5,
    }
    r = detect_expression_noise(bs)
    assert r.blocked is True
    assert r.category == EXPR_NOISE_MULTIPLE


def test_moderate_smile_warned_not_blocked():
    """중간 강도 웃음 → 경고만, 차단 X."""
    from engine.safety.photo.expression_noise import detect_expression_noise
    bs = {"mouthSmileLeft": 0.2}
    r = detect_expression_noise(bs)
    assert r.blocked is False
    assert r.warned is True
    assert "정확도" in r.user_message


def test_just_under_warn_threshold_passes():
    """경고 임계 직전 → 통과."""
    from engine.safety.photo.expression_noise import detect_expression_noise
    bs = {"mouthSmileLeft": 0.10}
    r = detect_expression_noise(bs)
    assert r.blocked is False
    assert r.warned is False


def test_detail_contains_all_categories():
    from engine.safety.photo.expression_noise import detect_expression_noise
    bs = {"mouthSmileLeft": 0.5}
    r = detect_expression_noise(bs)
    assert "mouth_max" in r.detail
    assert "eye_max" in r.detail
    assert "brow_max" in r.detail
    assert "jaw_cheek_max" in r.detail


def test_max_intensity_reported():
    from engine.safety.photo.expression_noise import detect_expression_noise
    bs = {"mouthSmileLeft": 0.7}
    r = detect_expression_noise(bs)
    assert r.max_intensity >= 0.7
