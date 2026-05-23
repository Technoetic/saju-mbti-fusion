"""ADR-223 - 합성 손금 학습 데이터 회귀."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_generate_synthetic_palm_shape():
    from engine.divination.palm.generate_training_data import generate_synthetic_palm
    img = generate_synthetic_palm(img_size=128, seed=1)
    assert img.shape == (128, 128, 3)
    assert img.dtype == np.uint8


def test_generate_synthetic_palm_deterministic():
    """같은 시드 → 같은 이미지."""
    from engine.divination.palm.generate_training_data import generate_synthetic_palm
    img1 = generate_synthetic_palm(img_size=64, seed=7)
    img2 = generate_synthetic_palm(img_size=64, seed=7)
    assert np.array_equal(img1, img2)


def test_generate_synthetic_palm_different_seeds():
    """다른 시드 → 다른 이미지."""
    from engine.divination.palm.generate_training_data import generate_synthetic_palm
    img1 = generate_synthetic_palm(img_size=64, seed=1)
    img2 = generate_synthetic_palm(img_size=64, seed=2)
    assert not np.array_equal(img1, img2)


def test_generate_synthetic_palm_has_dark_lines():
    """손금 선이 어두운 픽셀로 표시되는지."""
    from engine.divination.palm.generate_training_data import generate_synthetic_palm
    img = generate_synthetic_palm(img_size=256, seed=42)
    # 어두운 픽셀(R < 100) 존재
    dark_count = np.sum((img[..., 0] < 100) & (img[..., 1] < 100))
    assert dark_count > 100  # 손금 선 픽셀


def test_generate_dataset_torchvision_missing_safe(tmp_path):
    """torchvision 부재 시 에러 안전 반환."""
    from engine.divination.palm.generate_training_data import generate_dataset
    result = generate_dataset(output_dir=str(tmp_path), n_images=2, img_size=32)
    # torchvision 가용 시 n_generated > 0, 부재 시 에러
    assert "n_generated" in result


try:
    import torch  # noqa: F401
    import torchvision  # noqa: F401
    _HAS_TV = True
except ImportError:
    _HAS_TV = False


@pytest.mark.skipif(not _HAS_TV, reason="torchvision 부재")
def test_generate_dataset_writes_png(tmp_path):
    from engine.divination.palm.generate_training_data import generate_dataset
    result = generate_dataset(output_dir=str(tmp_path), n_images=3, img_size=64)
    assert result["n_generated"] == 3
    png_files = list(tmp_path.glob("*.png"))
    assert len(png_files) == 3
