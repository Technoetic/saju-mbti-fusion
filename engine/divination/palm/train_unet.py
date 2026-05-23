"""ADR-220+221 - 손금 U-Net 합성 학습 데이터 + fine-tune 스크립트.

전략:
  1. 사용자 손바닥 사진 입력 또는 공개 손금 데이터셋 (Roboflow 46건)
  2. Gabor 출력(ADR-215)을 약지도(weak label)로 활용 — self-training
  3. U-Net이 Gabor보다 부드러운 boundary 학습 → F1 ↑
  4. 가중치 → data/palm/unet_weights.pt 저장

사용:
  python -m engine.divination.palm.train_unet \\
    --data-dir data/palm/training/ \\
    --epochs 20 \\
    --batch-size 4 \\
    --output data/palm/unet_weights.pt

PyTorch 가용 + 학습 데이터 있어야 작동. CPU 학습 가능 (느림), GPU 권장.

ADR 정합:
  - ADR-217 U-Net 아키텍처 활용
  - ADR-215 Gabor 약지도 self-training
  - ADR-218 MIT 라이선스 (표준 학술 아키텍처만 사용)
  - ADR-006 학파 명칭 X (픽셀 마스크만)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np


def _ensure_torch():
    """PyTorch 필수 — 부재 시 오류."""
    try:
        import torch
        return torch
    except ImportError as e:
        print("ERROR: PyTorch 필요. pip install -r requirements-ml.txt", file=sys.stderr)
        raise SystemExit(1) from e


def load_images_from_dir(data_dir: str) -> list[np.ndarray]:
    """data_dir 의 모든 이미지 로드 (PIL 없이 numpy + 표준 라이브러리).

    Args:
        data_dir: 손바닥 이미지 디렉토리 경로.

    Returns:
        numpy array 리스트. 빈 디렉토리 또는 미지원 형식은 스킵.
    """
    import struct

    images: list[np.ndarray] = []
    p = Path(data_dir)
    if not p.exists():
        return images

    # 간단 PNG/JPEG 로드 — PyTorch torchvision 의 read_image 사용
    try:
        from torchvision.io import read_image  # type: ignore[import-not-found]
        for img_path in sorted(p.glob("*.png")) + sorted(p.glob("*.jpg")) + sorted(p.glob("*.jpeg")):
            try:
                tensor = read_image(str(img_path))
                # (C, H, W) → (H, W, C) numpy
                arr = tensor.permute(1, 2, 0).numpy()
                if arr.shape[2] >= 3:
                    images.append(arr[..., :3].astype(np.uint8))
            except Exception:
                continue
    except ImportError:
        # torchvision 부재 — 무시 (실 사용 시 PyTorch 필수)
        pass
    return images


def generate_weak_labels(images: list[np.ndarray]) -> list[np.ndarray]:
    """ADR-220 — Gabor 출력을 약지도(weak label)로 변환.

    Args:
        images: 손바닥 RGB 이미지 리스트.

    Returns:
        각 이미지의 binary 마스크 리스트 (Gabor 응답 > 90 percentile).
    """
    from engine.divination.palm.line_extraction import (
        gabor_kernel, to_grayscale, _convolve,
    )

    labels: list[np.ndarray] = []
    thetas = np.linspace(0, np.pi, 4, endpoint=False)
    for img in images:
        try:
            gray = to_grayscale(img)
            response = np.zeros_like(gray, dtype=np.float64)
            for theta in thetas:
                k = gabor_kernel(theta=float(theta))
                r = _convolve(gray, k)
                response = np.maximum(response, np.abs(r))
            threshold = float(np.percentile(response, 90.0))
            mask = (response > threshold).astype(np.float32)
            labels.append(mask)
        except Exception:
            labels.append(np.zeros_like(img[..., 0] if img.ndim == 3 else img, dtype=np.float32))
    return labels


def train_unet(
    data_dir: str,
    output_path: str = "data/palm/unet_weights.pt",
    epochs: int = 20,
    batch_size: int = 4,
    learning_rate: float = 1e-4,
    img_size: int = 256,
    model_type: str = "unet",  # ADR-233: "unet" | "cfm"
) -> dict:
    """ADR-221 + ADR-233 — U-Net / UNetCFM fine-tune.

    Args:
        data_dir: 학습 이미지 디렉토리.
        output_path: 가중치 저장 경로.
        epochs: 에폭 수.
        batch_size: 배치 크기.
        learning_rate: 학습률.
        img_size: 입력 크기.
        model_type: "unet" (ADR-217 표준) 또는 "cfm" (ADR-230 Context Fusion).

    Returns:
        {"epochs_trained": int, "final_loss": float, "output_path": str, "model_type": str}
    """
    torch = _ensure_torch()
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    from engine.divination.palm.unet_line_extractor import _resize_nearest

    # ADR-233 — 모델 선택
    if model_type == "cfm":
        from engine.divination.palm.unet_cfm import UNetCFM as _ModelClass
    else:
        from engine.divination.palm.unet_model import UNet as _ModelClass

    # 1. 데이터 로드
    images = load_images_from_dir(data_dir)
    if not images:
        return {"epochs_trained": 0, "final_loss": float("inf"),
                "output_path": "", "error": f"이미지 없음: {data_dir}"}

    # 2. 약지도 생성 (Gabor)
    labels = generate_weak_labels(images)

    # 3. 리사이즈
    def _resize_to(img: np.ndarray, h: int, w: int) -> np.ndarray:
        if img.ndim == 2:
            return _resize_nearest(img[..., None], h, w)[..., 0]
        return _resize_nearest(img, h, w)

    images_resized = [_resize_to(img, img_size, img_size) for img in images]
    labels_resized = [_resize_to(lbl, img_size, img_size) for lbl in labels]

    # 4. Dataset
    class PalmDataset(Dataset):
        def __len__(self):
            return len(images_resized)

        def __getitem__(self, idx):
            img = images_resized[idx].astype(np.float32) / 255.0
            lbl = labels_resized[idx].astype(np.float32)
            # (H, W, 3) → (3, H, W)
            img_t = torch.from_numpy(img.transpose(2, 0, 1))
            lbl_t = torch.from_numpy(lbl).unsqueeze(0)  # (1, H, W)
            return img_t, lbl_t

    dataset = PalmDataset()
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # 5. 모델·optimizer·loss (ADR-233 — model_type 선택)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = _ModelClass(n_channels=3, n_classes=1).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.BCEWithLogitsLoss()

    # 6. 학습 루프
    final_loss = float("inf")
    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        n_batches = 0
        for img_batch, lbl_batch in loader:
            img_batch = img_batch.to(device)
            lbl_batch = lbl_batch.to(device)
            optimizer.zero_grad()
            logits = model(img_batch)
            loss = criterion(logits, lbl_batch)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            n_batches += 1
        avg_loss = total_loss / max(n_batches, 1)
        final_loss = avg_loss
        if epoch % 5 == 0 or epoch == epochs - 1:
            print(f"[Epoch {epoch + 1}/{epochs}] loss={avg_loss:.4f}")

    # 7. 가중치 저장
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    torch.save(model.state_dict(), output_path)

    return {
        "epochs_trained": epochs,
        "final_loss": final_loss,
        "output_path": output_path,
        "n_images": len(images),
        "model_type": model_type,
    }


def main():
    parser = argparse.ArgumentParser(description="손금 U-Net fine-tune (ADR-221+233)")
    parser.add_argument("--data-dir", required=True, help="학습 이미지 디렉토리")
    parser.add_argument("--output", default="data/palm/unet_weights.pt",
                        help="가중치 저장 경로 (기본 data/palm/unet_weights.pt)")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--img-size", type=int, default=256)
    parser.add_argument("--model", choices=["unet", "cfm"], default="unet",
                        help="ADR-233: unet (표준) 또는 cfm (Context Fusion)")
    args = parser.parse_args()

    result = train_unet(
        data_dir=args.data_dir,
        output_path=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        img_size=args.img_size,
        model_type=args.model,
    )
    print(result)


if __name__ == "__main__":
    main()
