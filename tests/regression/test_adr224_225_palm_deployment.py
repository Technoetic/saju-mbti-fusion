"""ADR-224·225 - Fly.io 가중치 호스팅 + 데이터셋 파이프라인 회귀."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ───── ADR-224 Dockerfile 가중치 호스팅 ─────

def test_adr224_dockerfile_has_enable_palm_unet_arg():
    """Dockerfile에 ENABLE_PALM_UNET 빌드 인자 명시."""
    dockerfile = _ROOT / "Dockerfile"
    content = dockerfile.read_text(encoding="utf-8")
    assert "ARG ENABLE_PALM_UNET" in content
    assert "ADR-224" in content


def test_adr224_dockerfile_conditional_pytorch_install():
    """ENABLE_PALM_UNET=1 시만 PyTorch 설치 (코어 영향 0)."""
    dockerfile = _ROOT / "Dockerfile"
    content = dockerfile.read_text(encoding="utf-8")
    # 조건부 설치 패턴 검증
    assert 'if [ "$ENABLE_PALM_UNET" = "1" ]' in content
    assert "requirements-ml.txt" in content


def test_adr224_dockerfile_includes_training_in_build():
    """빌드 타임 학습 명령 포함."""
    dockerfile = _ROOT / "Dockerfile"
    content = dockerfile.read_text(encoding="utf-8")
    assert "engine.divination.palm.train_unet" in content
    assert "engine.divination.palm.generate_training_data" in content


def test_adr224_dockerfile_cleans_training_data_after_build():
    """학습 후 training/ 임시 데이터 정리 (이미지 크기 ↓)."""
    dockerfile = _ROOT / "Dockerfile"
    content = dockerfile.read_text(encoding="utf-8")
    assert "rm -rf data/palm/training/" in content


# ───── ADR-225 데이터셋 파이프라인 ─────

def test_adr225_synthetic_fallback_no_credentials(tmp_path, monkeypatch):
    """Roboflow API 키 부재 + 사용자 디렉토리 부재 → 합성 폴백."""
    from engine.divination.palm.dataset_pipeline import prepare_training_dataset
    monkeypatch.delenv("ROBOFLOW_API_KEY", raising=False)
    result = prepare_training_dataset(
        output_dir=str(tmp_path),
        n_synthetic_fallback=3,
    )
    assert result.source == "synthetic"
    assert result.n_images > 0 or "torchvision" in result.notes


def test_adr225_invalid_user_dir_falls_back_to_synthetic(tmp_path, monkeypatch):
    """존재하지 않는 사용자 디렉토리 → 합성 폴백."""
    from engine.divination.palm.dataset_pipeline import prepare_training_dataset
    monkeypatch.delenv("ROBOFLOW_API_KEY", raising=False)
    result = prepare_training_dataset(
        output_dir=str(tmp_path),
        n_synthetic_fallback=2,
        user_image_dir="/nonexistent/dir",
    )
    assert result.source == "synthetic"


def test_adr225_user_images_copied(tmp_path, monkeypatch):
    """사용자 디렉토리에 PNG 있으면 복사."""
    from engine.divination.palm.dataset_pipeline import prepare_training_dataset

    monkeypatch.delenv("ROBOFLOW_API_KEY", raising=False)

    # 사용자 사진 디렉토리 생성
    user_dir = tmp_path / "my_palms"
    user_dir.mkdir()
    # 빈 PNG 파일 3개
    for i in range(3):
        (user_dir / f"p{i}.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    output_dir = tmp_path / "train"
    result = prepare_training_dataset(
        output_dir=str(output_dir),
        user_image_dir=str(user_dir),
    )
    assert result.source == "user_provided"
    assert result.n_images == 3


def test_adr225_roboflow_url_correct():
    from engine.divination.palm.dataset_pipeline import ROBOFLOW_PALM_DATASET_URL
    assert "roboflow.com" in ROBOFLOW_PALM_DATASET_URL
    assert "palm-line-detection" in ROBOFLOW_PALM_DATASET_URL


def test_adr225_result_dataclass_fields():
    from engine.divination.palm.dataset_pipeline import DatasetPipelineResult
    r = DatasetPipelineResult(
        source="synthetic", n_images=5, output_dir="/tmp", notes="test",
    )
    assert r.source == "synthetic"
    assert r.n_images == 5


def test_adr225_synthetic_notes_includes_limitation():
    """합성 폴백 시 한계 명시."""
    from engine.divination.palm.dataset_pipeline import prepare_training_dataset
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        result = prepare_training_dataset(
            output_dir=tmp,
            n_synthetic_fallback=1,
        )
        if result.source == "synthetic":
            assert "F1 한계" in result.notes or "실 데이터" in result.notes
