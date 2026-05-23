"""ADR-200 - 다중 사진 자동 선택 회귀."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_empty_list_returns_invalid():
    from engine.divination.face.photo_selector import select_best_photo
    r = select_best_photo([])
    assert r.selected_index == -1
    assert r.n_photos == 0


def test_single_photo_selected():
    from engine.divination.face.photo_selector import select_best_photo
    r = select_best_photo([{"blendshapes": {}, "head_tilt_deg": 0, "asymmetry": 0.01}])
    assert r.selected_index == 0
    assert r.n_photos == 1
    assert "단일" in r.reason


def test_best_photo_selected_by_expression():
    """3장 중 표정 강한 사진 제외 — 무표정 선택."""
    from engine.divination.face.photo_selector import select_best_photo
    photos = [
        {"blendshapes": {"mouthSmileLeft": 0.5}, "head_tilt_deg": 0, "asymmetry": 0.01},  # 잡음 ↑
        {"blendshapes": {}, "head_tilt_deg": 0, "asymmetry": 0.01},  # 무표정
        {"blendshapes": {"eyeBlinkLeft": 0.6}, "head_tilt_deg": 0, "asymmetry": 0.01},  # 잡음 ↑
    ]
    r = select_best_photo(photos)
    assert r.selected_index == 1
    assert r.selected_score <= 0.1


def test_best_photo_selected_by_tilt():
    """기울기 적은 사진 선택."""
    from engine.divination.face.photo_selector import select_best_photo
    photos = [
        {"blendshapes": {}, "head_tilt_deg": 25, "asymmetry": 0.01},  # 기울기 ↑
        {"blendshapes": {}, "head_tilt_deg": 1, "asymmetry": 0.01},   # 정면
    ]
    r = select_best_photo(photos)
    assert r.selected_index == 1


def test_best_photo_selected_by_asymmetry():
    from engine.divination.face.photo_selector import select_best_photo
    photos = [
        {"blendshapes": {}, "head_tilt_deg": 0, "asymmetry": 0.04},  # 비대칭 ↑
        {"blendshapes": {}, "head_tilt_deg": 0, "asymmetry": 0.005},  # 대칭
    ]
    r = select_best_photo(photos)
    assert r.selected_index == 1


def test_all_invalid_returns_invalid():
    from engine.divination.face.photo_selector import select_best_photo
    r = select_best_photo([None, None, "invalid"])
    assert r.selected_index == -1


def test_mixed_valid_invalid_selects_valid():
    from engine.divination.face.photo_selector import select_best_photo
    photos = [
        None,
        {"blendshapes": {}, "head_tilt_deg": 0, "asymmetry": 0.01},
        None,
    ]
    r = select_best_photo(photos)
    assert r.selected_index == 1


def test_all_noisy_warns_user():
    """모두 잡음 ↑ → 재촬영 권고."""
    from engine.divination.face.photo_selector import select_best_photo
    photos = [
        {"blendshapes": {"mouthSmileLeft": 0.5}, "head_tilt_deg": 20, "asymmetry": 0.04},
        {"blendshapes": {"eyeBlinkLeft": 0.6}, "head_tilt_deg": 15, "asymmetry": 0.04},
    ]
    r = select_best_photo(photos)
    assert "재촬영" in r.reason or r.selected_score > 0.3


def test_reason_in_korean():
    from engine.divination.face.photo_selector import select_best_photo
    r = select_best_photo([{"blendshapes": {}, "head_tilt_deg": 0, "asymmetry": 0.01}])
    assert any(c.isalpha() and ord(c) >= 0xAC00 for c in r.reason)  # 한글 포함
