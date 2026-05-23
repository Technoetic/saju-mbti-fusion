"""ADR-217 - U-Net 실 추론 회귀.

PyTorch 가용 환경에서만 실행 — 부재 시 skip.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


try:
    import torch
    _HAS_TORCH = True
except ImportError:
    _HAS_TORCH = False


pytestmark = pytest.mark.skipif(not _HAS_TORCH, reason="PyTorch 부재 — ADR-217 skip")


def test_unet_model_imports():
    """U-Net 모듈 import 가능."""
    from engine.divination.palm.unet_model import UNet
    model = UNet(n_channels=3, n_classes=1)
    assert model.n_channels == 3
    assert model.n_classes == 1


def test_unet_forward_pass_shape():
    """U-Net forward — (1, 3, 256, 256) → (1, 1, 256, 256)."""
    from engine.divination.palm.unet_model import UNet
    model = UNet(n_channels=3, n_classes=1).eval()
    x = torch.randn(1, 3, 256, 256)
    with torch.no_grad():
        y = model(x)
    assert y.shape == (1, 1, 256, 256)


def test_unet_forward_pass_smaller_input():
    """홀수 크기 입력 — pad 로직 작동."""
    from engine.divination.palm.unet_model import UNet
    model = UNet(n_channels=3, n_classes=1).eval()
    x = torch.randn(1, 3, 128, 128)
    with torch.no_grad():
        y = model(x)
    assert y.shape == (1, 1, 128, 128)


def test_run_unet_inference_random_weights():
    """가중치 없으면 random init — 모델은 동작하나 mask는 의미 없음.

    본 테스트는 추론 흐름이 깨지지 않는지만 검증.
    """
    from engine.divination.palm.unet_line_extractor import _run_unet_inference
    from engine.divination.palm.unet_model import UNet
    import torch as _t

    # 임시 가중치 파일 — random init 저장
    model = UNet(n_channels=3, n_classes=1)
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as tmp:
        weights_path = tmp.name
    _t.save(model.state_dict(), weights_path)
    try:
        img = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        result = _run_unet_inference(img, weights_path)
        assert result is not None
        assert "mask" in result
        assert "raw_metrics" in result
        assert "upper_density" in result["raw_metrics"]
        # 5 영역 모두
        for k in ("middle_density", "lower_density", "lower_left_density",
                  "lower_right_density", "overall_density"):
            assert k in result["raw_metrics"]
    finally:
        os.unlink(weights_path)


def test_extract_palm_lines_uses_unet_when_weights_available():
    """PALM_UNET_MODEL_PATH 환경변수 설정 시 U-Net 사용 (used_unet=True)."""
    from engine.divination.palm.unet_line_extractor import (
        extract_palm_lines_best_available,
    )
    from engine.divination.palm.unet_model import UNet
    import torch as _t

    model = UNet(n_channels=3, n_classes=1)
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as tmp:
        weights_path = tmp.name
    _t.save(model.state_dict(), weights_path)

    prev = os.environ.get("PALM_UNET_MODEL_PATH")
    os.environ["PALM_UNET_MODEL_PATH"] = weights_path
    try:
        img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        result = extract_palm_lines_best_available(img)
        assert result.used_unet is True
        assert result.mask is not None
        assert result.fallback_reason == "ready"
    finally:
        if prev:
            os.environ["PALM_UNET_MODEL_PATH"] = prev
        else:
            os.environ.pop("PALM_UNET_MODEL_PATH", None)
        os.unlink(weights_path)


def test_resize_nearest():
    """nearest-neighbor 리사이즈."""
    from engine.divination.palm.unet_line_extractor import _resize_nearest
    img = np.arange(100, dtype=np.float32).reshape(10, 10)
    resized = _resize_nearest(img[..., None], 5, 5)
    assert resized.shape == (5, 5, 1)


def test_unet_handles_grayscale_input():
    """그레이스케일 (H, W) 입력 → 3채널 자동 변환."""
    from engine.divination.palm.unet_line_extractor import _run_unet_inference
    from engine.divination.palm.unet_model import UNet
    import torch as _t

    model = UNet(n_channels=3, n_classes=1)
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as tmp:
        weights_path = tmp.name
    _t.save(model.state_dict(), weights_path)
    try:
        img_gray = np.random.randint(0, 255, (200, 200), dtype=np.uint8)
        result = _run_unet_inference(img_gray, weights_path)
        assert result is not None
    finally:
        os.unlink(weights_path)
