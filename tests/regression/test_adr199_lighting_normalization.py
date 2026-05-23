"""ADR-199 - 조명 정규화 회귀."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_none_sclera_returns_identity():
    """sclera 없으면 게인 1.0."""
    from engine.divination.face.lighting_normalization import compute_lighting_gains
    r = compute_lighting_gains(None)
    assert r.gain_r == 1.0
    assert r.gain_g == 1.0
    assert r.gain_b == 1.0
    assert r.confidence == "low"


def test_perfect_white_sclera_returns_unity_gain():
    """sclera = 245,245,245 (target) → 게인 거의 1.0."""
    from engine.divination.face.lighting_normalization import compute_lighting_gains
    r = compute_lighting_gains((245, 245, 245))
    assert abs(r.gain_r - 1.0) < 0.01
    assert abs(r.gain_g - 1.0) < 0.01
    assert abs(r.gain_b - 1.0) < 0.01
    assert r.confidence == "high"


def test_warm_lighting_blue_gain_higher():
    """따뜻한 조명(주황 빛) — sclera에 적·녹 ↑, 청 ↓. 청색 게인 ↑."""
    from engine.divination.face.lighting_normalization import compute_lighting_gains
    r = compute_lighting_gains((230, 220, 180))
    # 청 게인이 적·녹 게인보다 커야 (sclera 청 ↓ → target까지 보정)
    assert r.gain_b > r.gain_r


def test_dark_sclera_low_confidence():
    """너무 어두운 sclera → 신뢰도 low (sclera 추출 실패 추정)."""
    from engine.divination.face.lighting_normalization import compute_lighting_gains
    r = compute_lighting_gains((50, 50, 50))
    assert r.confidence == "low"


def test_high_confidence_range():
    from engine.divination.face.lighting_normalization import compute_lighting_gains
    r = compute_lighting_gains((220, 220, 220))
    assert r.confidence == "high"


def test_gain_clamping_extreme_dark():
    """극단 어두운 sclera → 게인 1.5 클램프."""
    from engine.divination.face.lighting_normalization import compute_lighting_gains
    r = compute_lighting_gains((110, 110, 110))
    assert r.gain_r <= 1.5
    assert r.gain_g <= 1.5
    assert r.gain_b <= 1.5


def test_apply_gains_basic():
    """게인 적용 후 입력값 × 게인 결과 검증."""
    from engine.divination.face.lighting_normalization import (
        compute_lighting_gains, apply_gains_to_rgb,
    )
    gains = compute_lighting_gains((230, 220, 180))
    out = apply_gains_to_rgb((150, 130, 110), gains)
    # 각 채널이 입력값 × 게인 (clamp 후)
    assert abs(out[0] - 150 * gains.gain_r) < 1.0
    assert abs(out[1] - 130 * gains.gain_g) < 1.0
    assert abs(out[2] - 110 * gains.gain_b) < 1.0


def test_apply_gains_clamps_255():
    from engine.divination.face.lighting_normalization import (
        compute_lighting_gains, apply_gains_to_rgb,
    )
    gains = compute_lighting_gains((200, 200, 180))
    out = apply_gains_to_rgb((250, 250, 250), gains)
    # 255 clamp
    assert all(0 <= v <= 255 for v in out)


def test_normalize_roi_rgb_low_confidence_returns_original():
    """sclera 신뢰도 low면 원본 보존 (안전 우선)."""
    from engine.divination.face.lighting_normalization import normalize_roi_rgb
    roi = {"forehead": (180, 150, 130)}
    out, gains = normalize_roi_rgb(roi, (50, 50, 50))
    assert out == roi
    assert gains.confidence == "low"


def test_normalize_roi_rgb_high_confidence_applies():
    """sclera 신뢰도 high면 정규화 적용."""
    from engine.divination.face.lighting_normalization import normalize_roi_rgb
    roi = {"forehead": (180, 150, 130)}
    out, gains = normalize_roi_rgb(roi, (220, 200, 170))
    # 청색이 증가했어야
    assert out["forehead"][2] > 130


def test_invalid_rgb_safe():
    from engine.divination.face.lighting_normalization import (
        compute_lighting_gains, apply_gains_to_rgb,
    )
    gains = compute_lighting_gains((220, 220, 220))
    out = apply_gains_to_rgb((), gains)
    assert out == (0.0, 0.0, 0.0)
