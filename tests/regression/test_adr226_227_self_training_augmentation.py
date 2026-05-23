"""ADR-226·227 - Self-training + Augmentation 회귀."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


try:
    import torch  # noqa: F401
    _HAS_TORCH = True
except ImportError:
    _HAS_TORCH = False


# ───── ADR-227 Augmentation ─────

def test_adr227_horizontal_flip():
    from engine.divination.palm.augmentation import augment_horizontal_flip
    img = np.zeros((10, 10, 3), dtype=np.uint8)
    img[5, 0, 0] = 255  # 좌측 점
    mask = np.zeros((10, 10), dtype=np.float32)
    mask[5, 0] = 1.0
    img_f, mask_f = augment_horizontal_flip(img, mask)
    # 좌측 점이 우측으로
    assert img_f[5, 9, 0] == 255
    assert mask_f[5, 9] == 1.0


def test_adr227_rotation():
    from engine.divination.palm.augmentation import augment_rotation
    img = np.zeros((20, 20, 3), dtype=np.uint8)
    mask = np.zeros((20, 20), dtype=np.float32)
    img_r, mask_r = augment_rotation(img, mask, 90.0)
    assert img_r.shape == img.shape
    assert mask_r.shape == mask.shape


def test_adr227_brightness():
    from engine.divination.palm.augmentation import augment_brightness
    img = np.full((10, 10, 3), 100, dtype=np.uint8)
    mask = np.zeros((10, 10), dtype=np.float32)
    img_b, _ = augment_brightness(img, mask, delta=30)
    assert img_b[0, 0, 0] == 130


def test_adr227_brightness_clamp():
    """음수·255 초과 클램프."""
    from engine.divination.palm.augmentation import augment_brightness
    img = np.full((5, 5, 3), 250, dtype=np.uint8)
    mask = np.zeros((5, 5), dtype=np.float32)
    img_b, _ = augment_brightness(img, mask, delta=50)
    assert img_b[0, 0, 0] == 255  # clamp


def test_adr227_gaussian_noise_changes_image():
    from engine.divination.palm.augmentation import augment_gaussian_noise
    img = np.full((20, 20, 3), 128, dtype=np.uint8)
    mask = np.zeros((20, 20), dtype=np.float32)
    img_n, _ = augment_gaussian_noise(img, mask, sigma=10.0, seed=42)
    assert not np.array_equal(img_n, img)


def test_adr227_color_jitter():
    from engine.divination.palm.augmentation import augment_color_jitter
    img = np.full((5, 5, 3), 100, dtype=np.uint8)
    mask = np.zeros((5, 5), dtype=np.float32)
    img_c, _ = augment_color_jitter(img, mask, r_scale=1.5, g_scale=1.0, b_scale=1.0)
    assert img_c[0, 0, 0] == 150  # R 증가
    assert img_c[0, 0, 1] == 100  # G 변동 없음


def test_adr227_batch_returns_original_plus_variants():
    from engine.divination.palm.augmentation import augment_batch
    img = np.full((30, 30, 3), 128, dtype=np.uint8)
    mask = np.zeros((30, 30), dtype=np.float32)
    results = augment_batch(img, mask, n_variants=3, seed=42)
    assert len(results) == 4  # 원본 + 3 변형
    # 첫 번째는 원본
    assert np.array_equal(results[0][0], img)


# ───── ADR-226 Self-training ─────

@pytest.mark.skipif(not _HAS_TORCH, reason="PyTorch 부재")
def test_adr226_generate_pseudo_label():
    from engine.divination.palm.unet_model import UNet
    from engine.divination.palm.self_training import generate_pseudo_label
    import torch as _t

    model = UNet(n_channels=3, n_classes=1).eval()
    img = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
    mask, conf = generate_pseudo_label(model, img)
    assert mask.shape == (64, 64)
    assert mask.dtype == np.float32
    assert 0.0 <= conf <= 1.0


def test_adr226_run_self_training_no_data_safe():
    from engine.divination.palm.self_training import run_self_training
    result = run_self_training(
        initial_weights_path="/nonexistent.pt",
        data_dir="/nonexistent/dir/",
        n_iterations=1,
    )
    assert result.iterations_completed == 0


def test_adr226_pseudo_label_confidence_threshold():
    from engine.divination.palm.self_training import PSEUDO_LABEL_CONFIDENCE
    assert 0.5 < PSEUDO_LABEL_CONFIDENCE < 1.0


def test_adr226_min_pseudo_pixels_defined():
    from engine.divination.palm.self_training import MIN_PSEUDO_PIXELS
    assert MIN_PSEUDO_PIXELS > 0


def test_adr226_result_dataclass_fields():
    from engine.divination.palm.self_training import SelfTrainingResult
    r = SelfTrainingResult(
        iterations_completed=2, final_loss=0.3, n_pseudo_labels=10000,
        confidence_threshold=0.8, output_path="/tmp/w.pt", notes="test",
    )
    assert r.iterations_completed == 2
    assert r.final_loss == 0.3
