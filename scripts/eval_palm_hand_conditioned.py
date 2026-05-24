"""ADR-251 - hand-conditioned vs 전체 추론 F1 비교 (200장 hold-out).

목적: MediaPipe keypoint로 손 영역만 crop 추론 시 F1 향상 측정.

11k Hands 손바닥은 이미 손 영역 대부분 차지하므로 효과가 작을 수 있음.
실 사용 시나리오 (배경 많음)는 더 큰 효과 기대.

사용:
  python scripts/eval_palm_hand_conditioned.py \\
    --weights models/unet_weights.pt \\
    --eval-dir D:/palm_dataset/eval_holdout/
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", required=True)
    parser.add_argument("--eval-dir", required=True)
    parser.add_argument("--img-size", type=int, default=256)
    args = parser.parse_args()

    import numpy as np
    import torch
    from torchvision.io import read_image

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    os.environ["PALM_UNET_MODEL_PATH"] = args.weights

    from engine.divination.palm.unet_line_extractor import (
        extract_palm_lines_best_available,
        extract_palm_lines_hand_conditioned,
        _resize_nearest,
    )
    from engine.divination.palm.line_extraction import (
        gabor_kernel, to_grayscale, _convolve,
    )

    # Gabor weak label
    thetas = np.linspace(0, np.pi, 4, endpoint=False)
    gks = [gabor_kernel(theta=float(t)) for t in thetas]

    def gabor_label(img_resized: np.ndarray) -> np.ndarray:
        gray = to_grayscale(img_resized)
        resp = np.zeros_like(gray, dtype=np.float64)
        for k in gks:
            resp = np.maximum(resp, np.abs(_convolve(gray, k)))
        thr = float(np.percentile(resp, 90.0))
        return (resp > thr).astype(np.float32)

    # Mock keypoint (이미지 중앙 70% 영역 — 실 사용 시 MediaPipe 결과 대신)
    def mock_keypoints():
        kp = {}
        for i in range(21):
            kp[f"kp{i}"] = [0.15 + (i % 7) * 0.1, 0.15 + (i // 7) * 0.25, 0.0]
        return kp

    eval_dir = Path(args.eval_dir)
    img_paths = []
    for ext in ("*.jpg", "*.png", "*.JPG"):
        img_paths.extend(sorted(eval_dir.glob(ext)))
    print(f"[eval] {len(img_paths)} 장 / weights={args.weights}")

    # 결과
    full_f1s, full_ious, full_consistencies = [], [], []
    hc_f1s, hc_ious, hc_consistencies = [], [], []

    for i, p in enumerate(img_paths):
        tensor = read_image(str(p))
        arr = tensor.permute(1, 2, 0).numpy()
        if arr.shape[-1] >= 3:
            arr = arr[..., :3].astype(np.uint8)

        # 1. 전체 이미지 추론
        r_full = extract_palm_lines_best_available(arr)
        # 2. hand-conditioned 추론
        r_hc = extract_palm_lines_hand_conditioned(arr, mock_keypoints())

        # F1 계산 (Gabor weak GT, 256x256 비교)
        img_r = _resize_nearest(arr.astype(np.float32), args.img_size, args.img_size)
        gt = gabor_label(img_r)

        def metric(mask: np.ndarray | None) -> tuple[float, float]:
            if mask is None:
                return 0.0, 0.0
            # mask 가 원본 크기일 수 있음 → 256 리사이즈
            if mask.shape != gt.shape:
                m = _resize_nearest(
                    mask[..., None].astype(np.float32), args.img_size, args.img_size,
                )[..., 0]
                m = m > 0.5
            else:
                m = mask.astype(bool)
            pred = m.astype(np.float32)
            inter = float((pred * gt).sum())
            union = float(pred.sum() + gt.sum() - inter)
            iou = inter / max(union, 1.0)
            tp = inter
            fp = float(pred.sum() - inter)
            fn = float(gt.sum() - inter)
            p_ = tp / max(tp + fp, 1.0)
            r_ = tp / max(tp + fn, 1.0)
            f1 = 2 * p_ * r_ / max(p_ + r_, 1.0)
            return f1, iou

        f1_full, iou_full = metric(r_full.mask)
        f1_hc, iou_hc = metric(r_hc.mask)

        full_f1s.append(f1_full)
        full_ious.append(iou_full)
        hc_f1s.append(f1_hc)
        hc_ious.append(iou_hc)

        if (i + 1) % 20 == 0:
            print(f"  [{i+1}/{len(img_paths)}] "
                  f"full F1={np.mean(full_f1s):.4f} | "
                  f"hc F1={np.mean(hc_f1s):.4f} | "
                  f"Δ={np.mean(hc_f1s) - np.mean(full_f1s):+.4f}", flush=True)

    print()
    print("=" * 60)
    print(f"[비교 결과] {len(img_paths)} 장")
    print(f"  [전체 이미지]    F1={np.mean(full_f1s):.4f}  IoU={np.mean(full_ious):.4f}")
    print(f"  [hand-cond]      F1={np.mean(hc_f1s):.4f}  IoU={np.mean(hc_ious):.4f}")
    print(f"  Δ F1: {np.mean(hc_f1s) - np.mean(full_f1s):+.4f}  "
          f"({(np.mean(hc_f1s) - np.mean(full_f1s)) / max(np.mean(full_f1s), 1e-6) * 100:+.1f}%)")
    print("=" * 60)


if __name__ == "__main__":
    main()
