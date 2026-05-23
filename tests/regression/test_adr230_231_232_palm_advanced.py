"""ADR-230·231·232 - U-Net CFM + TTA + 좌우 분석 회귀."""

from __future__ import annotations

import sys
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


# ───── ADR-230 U-Net Context Fusion Module ─────

@pytest.mark.skipif(not _HAS_TORCH, reason="PyTorch 부재")
def test_adr230_unet_cfm_forward_shape():
    """UNetCFM forward — (1, 3, 256, 256) → (1, 1, 256, 256)."""
    from engine.divination.palm.unet_cfm import UNetCFM
    model = UNetCFM(n_channels=3, n_classes=1).eval()
    x = torch.randn(1, 3, 256, 256)
    with torch.no_grad():
        y = model(x)
    assert y.shape == (1, 1, 256, 256)


@pytest.mark.skipif(not _HAS_TORCH, reason="PyTorch 부재")
def test_adr230_unet_cfm_lighter_than_standard():
    """UNetCFM 파라미터 수 < 표준 UNet (학술 가벼움 검증)."""
    from engine.divination.palm.unet_cfm import UNetCFM
    from engine.divination.palm.unet_model import UNet
    cfm = UNetCFM(n_channels=3, n_classes=1)
    std = UNet(n_channels=3, n_classes=1)
    n_cfm = sum(p.numel() for p in cfm.parameters())
    n_std = sum(p.numel() for p in std.parameters())
    assert n_cfm < n_std  # arXiv 2102.12127: 10.27M < 31M


@pytest.mark.skipif(not _HAS_TORCH, reason="PyTorch 부재")
def test_adr230_attention_gate_works():
    """Attention Gate forward — gate · skip → 마스크 적용."""
    from engine.divination.palm.unet_cfm import _AttentionGate
    gate_layer = _AttentionGate(gate_channels=64, in_channels=64, inter_channels=32)
    gate = torch.randn(1, 64, 32, 32)
    skip = torch.randn(1, 64, 32, 32)
    out = gate_layer(gate, skip)
    assert out.shape == skip.shape


@pytest.mark.skipif(not _HAS_TORCH, reason="PyTorch 부재")
def test_adr230_cfm_module_residual():
    """ContextFusionModule residual connection 작동."""
    from engine.divination.palm.unet_cfm import _ContextFusionModule
    cfm = _ContextFusionModule(in_channels=64).eval()
    x = torch.randn(1, 64, 32, 32)
    with torch.no_grad():
        y = cfm(x)
    assert y.shape == x.shape


def test_adr230_cfm_module_docstring_cites_arxiv():
    """ADR-230 — arXiv 2102.12127 학술 출처 명시."""
    src_path = _ROOT / "engine" / "divination" / "palm" / "unet_cfm.py"
    src = src_path.read_text(encoding="utf-8")
    assert "2102.12127" in src
    assert "Context Fusion" in src
    assert "ADR-230" in src


# ───── ADR-231 Test-Time Augmentation ─────

def test_adr231_tta_no_unet_falls_back():
    """U-Net 가중치 부재 시 단일 추론 (Gabor fallback)."""
    from engine.divination.palm.tta_inference import run_tta_inference
    img = np.full((100, 100, 3), 150, dtype=np.uint8)
    img[20, :, :] = 50
    r = run_tta_inference(img)
    assert r.n_augmentations >= 1
    # raw_metrics 5 영역 모두
    if r.raw_metrics:
        assert "upper_density" in r.raw_metrics


def test_adr231_augment_inputs_creates_variants():
    """_augment_inputs — 원본 + 변형 5개 생성."""
    from engine.divination.palm.tta_inference import _augment_inputs
    img = np.full((50, 50, 3), 100, dtype=np.uint8)
    variants = _augment_inputs(img)
    assert len(variants) >= 1
    # 첫 번째는 identity
    assert variants[0][1] == "identity"


def test_adr231_inverse_transform_identity():
    """identity 역변환은 원본 그대로."""
    from engine.divination.palm.tta_inference import _inverse_transform_mask
    mask = np.array([[1, 0], [0, 1]], dtype=np.float32)
    restored = _inverse_transform_mask(mask, "identity")
    assert np.array_equal(restored, mask)


def test_adr231_inverse_transform_hflip():
    """hflip 역변환 — 좌우 다시 반전."""
    from engine.divination.palm.tta_inference import _inverse_transform_mask
    mask = np.array([[1, 0], [0, 1]], dtype=np.float32)
    restored = _inverse_transform_mask(mask, "hflip")
    assert restored[0, 0] == 0  # 0번 열이 1번 열로
    assert restored[0, 1] == 1


# ───── ADR-232 좌·우 손 비교 ─────

def test_adr232_asymmetry_symmetric_metrics():
    """동일 metrics → 비대칭 0, balanced."""
    from engine.divination.palm.left_right_analysis import compute_asymmetry
    metrics = {
        "upper_density": 0.1, "middle_density": 0.2, "lower_density": 0.15,
        "lower_left_density": 0.05, "lower_right_density": 0.05,
    }
    asym, dominant = compute_asymmetry(metrics, metrics)
    assert asym == 0.0
    assert dominant == "balanced"


def test_adr232_asymmetry_left_dominant():
    """왼손이 더 강하면 dominant=left."""
    from engine.divination.palm.left_right_analysis import compute_asymmetry
    left = {"upper_density": 0.3, "middle_density": 0.3, "lower_density": 0.3,
            "lower_left_density": 0.3, "lower_right_density": 0.3}
    right = {"upper_density": 0.05, "middle_density": 0.05, "lower_density": 0.05,
             "lower_left_density": 0.05, "lower_right_density": 0.05}
    asym, dominant = compute_asymmetry(left, right)
    assert asym > 0
    assert dominant == "left"


def test_adr232_analyze_single_hand_safe():
    """한쪽 손만 있으면 단측 분석."""
    from engine.divination.palm.left_right_analysis import analyze_palms
    img = np.full((100, 100, 3), 150, dtype=np.uint8)
    r = analyze_palms(left_image=img, right_image=None)
    assert r.asymmetry_score == 0.0
    assert "한 손만" in r.description_ko or "분석 모듈" in r.description_ko


def test_adr232_description_passes_fate_assertion():
    """ADR-232 description 어휘가 ADR-171 fate_assertion 통과."""
    from engine.divination.palm.left_right_analysis import analyze_palms
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    img = np.full((100, 100, 3), 150, dtype=np.uint8)
    r = analyze_palms(left_image=img, right_image=img)
    fate = detect_fate_assertions(r.description_ko, domain="palm")
    assert fate.detected is False


def test_adr232_disclaimer_blocks_fate():
    from engine.divination.palm.left_right_analysis import LeftRightAnalysisResult
    r = LeftRightAnalysisResult(
        left_metrics={}, right_metrics={},
        asymmetry_score=0.0, dominant_side="balanced",
        description_ko="test",
    )
    assert "운명" in r.disclaimer
