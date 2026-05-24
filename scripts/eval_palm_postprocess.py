"""ADR-252 - 후처리 적용 vs raw F1 비교 (200장 hold-out)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-dir", required=True)
    parser.add_argument("--img-size", type=int, default=256)
    args = parser.parse_args()

    import numpy as np
    from torchvision.io import read_image

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from engine.divination.palm.unet_line_extractor import (
        extract_palm_lines_best_available, _resize_nearest,
    )
    from engine.divination.palm.line_extraction import (
        gabor_kernel, to_grayscale, _convolve,
    )
    from engine.divination.palm.mask_postprocess import postprocess_palm_mask

    thetas = np.linspace(0, np.pi, 4, endpoint=False)
    gks = [gabor_kernel(theta=float(t)) for t in thetas]

    def gabor_label(img_resized: np.ndarray) -> np.ndarray:
        gray = to_grayscale(img_resized)
        resp = np.zeros_like(gray, dtype=np.float64)
        for k in gks:
            resp = np.maximum(resp, np.abs(_convolve(gray, k)))
        thr = float(np.percentile(resp, 90.0))
        return (resp > thr).astype(np.float32)

    def metric(pred: np.ndarray, gt: np.ndarray):
        pred = pred.astype(np.float32)
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

    eval_dir = Path(args.eval_dir)
    img_paths = []
    for ext in ("*.jpg", "*.png", "*.JPG"):
        img_paths.extend(sorted(eval_dir.glob(ext)))
    print(f"[eval] {len(img_paths)} 장")

    raw_f1s, raw_ious = [], []
    pp_f1s, pp_ious = [], []
    skel_f1s = []

    for i, p in enumerate(img_paths):
        tensor = read_image(str(p))
        arr = tensor.permute(1, 2, 0).numpy()
        if arr.shape[-1] >= 3:
            arr = arr[..., :3].astype(np.uint8)
        img_r = _resize_nearest(arr.astype(np.float32), args.img_size, args.img_size)
        gt = gabor_label(img_r)

        r = extract_palm_lines_best_available(arr)
        if r.mask is None:
            continue
        raw = r.mask.astype(bool)
        # postprocess
        pp = postprocess_palm_mask(raw, apply_skeleton=False, min_component_size=20)
        cleaned = pp["cleaned"]

        f1_r, iou_r = metric(raw, gt)
        f1_p, iou_p = metric(cleaned, gt)
        raw_f1s.append(f1_r)
        raw_ious.append(iou_r)
        pp_f1s.append(f1_p)
        pp_ious.append(iou_p)

        if (i + 1) % 20 == 0:
            print(f"  [{i+1}/{len(img_paths)}] "
                  f"raw F1={np.mean(raw_f1s):.4f} | pp F1={np.mean(pp_f1s):.4f} | "
                  f"Δ={np.mean(pp_f1s) - np.mean(raw_f1s):+.4f}", flush=True)

    print()
    print("=" * 60)
    print(f"[비교] {len(raw_f1s)} 장")
    print(f"  raw         F1={np.mean(raw_f1s):.4f}  IoU={np.mean(raw_ious):.4f}")
    print(f"  postprocess F1={np.mean(pp_f1s):.4f}  IoU={np.mean(pp_ious):.4f}")
    print(f"  Δ F1: {np.mean(pp_f1s) - np.mean(raw_f1s):+.4f}  "
          f"({(np.mean(pp_f1s) - np.mean(raw_f1s)) / max(np.mean(raw_f1s), 1e-6) * 100:+.1f}%)")
    print("=" * 60)


if __name__ == "__main__":
    main()
