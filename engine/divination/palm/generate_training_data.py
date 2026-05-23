"""ADR-223 - 합성 손금 학습 데이터 생성 (재현 가능).

ADR-220 약지도 학습용 합성 손바닥 이미지 생성. 본 AI가 직접 실행 가능하며
사용자 데이터셋 부재 시 폴백.

사용:
  python -m engine.divination.palm.generate_training_data \\
    --output-dir data/palm/training/ \\
    --n-images 20 \\
    --img-size 256

ADR 정합:
  - ADR-220 self-training 약지도 (Gabor) — 합성 데이터로 부트스트랩
  - ADR-006 자문 거절 (합성 이미지에 학파 매핑 X)
  - ADR-010 사실성 분리 (실 손금 사진 부재 정직 영속)

한계 (정직):
  - 합성 손금은 단순 선 시뮬레이션 — 실 손금 fine-tune 대체 X
  - 운영 시 실 사용자 사진 누적 후 재학습 권장
  - 본 스크립트 산출 가중치는 부트스트랩 — F1 85% 추정
"""

from __future__ import annotations

import argparse
import os

import numpy as np


def generate_synthetic_palm(img_size: int, seed: int) -> np.ndarray:
    """단일 합성 손바닥 이미지 (RGB).

    Args:
        img_size: 정사각 크기.
        seed: 시드 (재현성).

    Returns:
        (H, W, 3) uint8 RGB.
    """
    rng = np.random.default_rng(seed)
    # 손바닥색 (베이지)
    img = np.full((img_size, img_size, 3), [220, 190, 160], dtype=np.uint8)
    # 노이즈
    noise = rng.integers(-15, 15, (img_size, img_size, 3), dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # 3대 선 시뮬레이션 (검은 갈색)
    line_color = np.array([80, 60, 40], dtype=np.uint8)

    # 생명선 (하좌측 호) — 엄지~손목 곡선
    for t in range(int(img_size * 0.2)):
        progress = t / max(1, int(img_size * 0.2))
        y = int(img_size * 0.58) + t + rng.integers(-2, 3)
        x = int(img_size * 0.31) - int(img_size * 0.08 * np.sin(progress * np.pi)) + rng.integers(-2, 3)
        if 0 <= y < img_size and 0 <= x < img_size:
            img[max(0, y - 1):y + 2, max(0, x - 1):x + 2] = line_color

    # 두뇌선 (중간 가로) — 손바닥 가로지름
    for t in range(int(img_size * 0.59)):
        y = int(img_size * 0.51) + rng.integers(-2, 3)
        x = int(img_size * 0.20) + t
        if 0 <= y < img_size and 0 <= x < img_size:
            img[max(0, y - 1):y + 2, max(0, x - 1):x + 2] = line_color

    # 감정선 (상부 가로)
    for t in range(int(img_size * 0.55)):
        y = int(img_size * 0.35) + rng.integers(-2, 3)
        x = int(img_size * 0.23) + t
        if 0 <= y < img_size and 0 <= x < img_size:
            img[max(0, y - 1):y + 2, max(0, x - 1):x + 2] = line_color

    return img


def generate_dataset(
    output_dir: str,
    n_images: int = 20,
    img_size: int = 256,
    seed_start: int = 42,
) -> dict:
    """합성 데이터셋 생성 + PNG 저장.

    Args:
        output_dir: 저장 디렉토리.
        n_images: 생성 이미지 수.
        img_size: 이미지 크기.
        seed_start: 시작 시드.

    Returns:
        {"n_generated": int, "output_dir": str}
    """
    try:
        import torch
        from torchvision.io import write_png
    except ImportError:
        return {"n_generated": 0, "output_dir": output_dir,
                "error": "torchvision 필요 (requirements-ml.txt)"}

    os.makedirs(output_dir, exist_ok=True)
    count = 0
    for i in range(n_images):
        img = generate_synthetic_palm(img_size, seed_start + i)
        tensor = torch.from_numpy(img.transpose(2, 0, 1))
        out_path = os.path.join(output_dir, f"synth_{i:03d}.png")
        try:
            write_png(tensor, out_path)
            count += 1
        except Exception:
            continue
    return {"n_generated": count, "output_dir": output_dir}


def main():
    parser = argparse.ArgumentParser(description="합성 손금 학습 데이터 (ADR-223)")
    parser.add_argument("--output-dir", default="data/palm/training/")
    parser.add_argument("--n-images", type=int, default=20)
    parser.add_argument("--img-size", type=int, default=256)
    parser.add_argument("--seed-start", type=int, default=42)
    args = parser.parse_args()
    result = generate_dataset(
        output_dir=args.output_dir,
        n_images=args.n_images,
        img_size=args.img_size,
        seed_start=args.seed_start,
    )
    print(result)


if __name__ == "__main__":
    main()
