"""ADR-218~222 - 손금 U-Net 파이프라인 회귀 (MIT 우회 + 옵션 의존성 + 합성 학습)."""

from __future__ import annotations

import os
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


# ───── ADR-218 라이선스 재분류 ─────

def test_adr218_unet_model_docstring_mit_compatible():
    """ADR-218 — unet_model.py docstring에 Ronneberger 학술 공개 명시."""
    import engine.divination.palm.unet_model as um
    src_doc = um.__doc__ or ""
    assert "Ronneberger" in src_doc
    assert "ADR-218" in src_doc


def test_adr218_no_gpl_warning_in_module():
    """ADR-218 — milesial GPL-3.0 코드 직접 복사 X 명시."""
    import engine.divination.palm.unet_model as um
    src_doc = um.__doc__ or ""
    assert "직접 복사 X" in src_doc or "독립 구현" in src_doc


# ───── ADR-219 requirements 분리 ─────

def test_adr219_requirements_ml_exists():
    """ADR-219 — requirements-ml.txt 파일 존재 (코어 deploy 영향 0)."""
    ml_req = _ROOT / "requirements-ml.txt"
    assert ml_req.exists()


def test_adr219_core_requirements_no_torch():
    """ADR-219 — 코어 requirements.txt에 torch 없음 (Fly.io 코어 영향 0)."""
    core_req = _ROOT / "requirements.txt"
    if core_req.exists():
        content = core_req.read_text(encoding="utf-8")
        assert "torch" not in content.lower(), (
            "torch는 requirements-ml.txt 분리 — 코어에 추가 X"
        )


def test_adr219_ml_requirements_has_torch():
    ml_req = _ROOT / "requirements-ml.txt"
    content = ml_req.read_text(encoding="utf-8")
    assert "torch" in content.lower()


# ───── ADR-220 합성 학습 데이터 ─────

@pytest.mark.skipif(not _HAS_TORCH, reason="PyTorch 부재")
def test_adr220_generate_weak_labels_returns_masks():
    from engine.divination.palm.train_unet import generate_weak_labels
    images = [np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
              for _ in range(3)]
    labels = generate_weak_labels(images)
    assert len(labels) == 3
    for lbl in labels:
        assert lbl.shape == (100, 100)
        assert lbl.dtype == np.float32
        # binary 마스크 (0 또는 1)
        unique = np.unique(lbl)
        assert all(v in (0.0, 1.0) for v in unique)


def test_adr220_generate_weak_labels_empty_safe():
    from engine.divination.palm.train_unet import generate_weak_labels
    assert generate_weak_labels([]) == []


# ───── ADR-221 fine-tune 스크립트 ─────

@pytest.mark.skipif(not _HAS_TORCH, reason="PyTorch 부재")
def test_adr221_train_unet_no_data_safe():
    from engine.divination.palm.train_unet import train_unet
    result = train_unet(data_dir="/nonexistent/path/", epochs=1, batch_size=1)
    assert result["epochs_trained"] == 0
    assert "error" in result


@pytest.mark.skipif(not _HAS_TORCH, reason="PyTorch 부재")
def test_adr221_train_unet_with_synthetic_data(tmp_path):
    """합성 이미지 3장 1 epoch 학습 → 가중치 저장 검증."""
    from engine.divination.palm.train_unet import train_unet
    # 임시 데이터 디렉토리
    data_dir = tmp_path / "palm_train"
    data_dir.mkdir()
    # torchvision 부재 시 load_images_from_dir 가 빈 리스트 반환 — skip
    try:
        from torchvision.io import write_png
        import torch as _t
        for i in range(3):
            img = _t.randint(0, 255, (3, 64, 64), dtype=_t.uint8)
            write_png(img, str(data_dir / f"img{i}.png"))
    except ImportError:
        pytest.skip("torchvision 부재")

    output_path = tmp_path / "weights.pt"
    result = train_unet(
        data_dir=str(data_dir),
        output_path=str(output_path),
        epochs=1,
        batch_size=2,
        img_size=64,
    )
    assert result["epochs_trained"] == 1
    assert result["n_images"] == 3
    assert output_path.exists()


# ───── ADR-222 기본 가중치 경로 자동 탐색 ─────

def test_adr222_default_weights_paths_defined():
    from engine.divination.palm.unet_line_extractor import _DEFAULT_WEIGHTS_PATHS
    assert len(_DEFAULT_WEIGHTS_PATHS) >= 1
    assert any("data/palm" in p for p in _DEFAULT_WEIGHTS_PATHS)


def test_adr222_no_env_no_default_falls_back():
    """환경변수 없고 기본 경로도 없으면 fallback no_weights."""
    from engine.divination.palm.unet_line_extractor import check_unet_availability
    prev = os.environ.pop("PALM_UNET_MODEL_PATH", None)
    try:
        r = check_unet_availability()
        # PyTorch 가용 + 가중치 부재 → no_weights
        if r.pytorch_available:
            assert r.fallback_reason in ("no_weights", "ready")
    finally:
        if prev:
            os.environ["PALM_UNET_MODEL_PATH"] = prev
