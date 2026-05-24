"""ADR-249 - CFM 가중치 평가 (hold-out 100장 vs Gabor weak label).

목적: 학습된 CFM 가중치의 일반화 성능을 hold-out 100장으로 측정.
GT는 Gabor weak label (self-training 기준과 동일) — 절대 F1 아닌 상대 비교.

사용:
  python scripts/eval_palm_cfm.py \\
    --weights models/unet_weights_cfm_30ep.pt \\
    --eval-dir D:/palm_dataset/eval_holdout/ \\
    --img-size 256
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
    import torch.nn as nn
    from torchvision.io import read_image

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from engine.divination.palm.unet_cfm import UNetCFM
    from engine.divination.palm.unet_model import UNet
    from engine.divination.palm.unet_line_extractor import _resize_nearest
    from engine.divination.palm.line_extraction import (
        gabor_kernel, to_grayscale, _convolve,
    )

    # 1. 모델 로드 (CFM/UNet 자동 식별)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    state = torch.load(args.weights, map_location=device, weights_only=True)
    keys = list(state.keys()) if isinstance(state, dict) else []
    is_cfm = any("cfm" in k or "branch" in k or ("attention" in k and "psi" in k) for k in keys)
    model = (UNetCFM if is_cfm else UNet)(n_channels=3, n_classes=1).to(device).eval()
    model.load_state_dict(state, strict=False)
    print(f"[모델] {'CFM' if is_cfm else 'UNet'} / device={device} / keys={len(keys)}")

    # 2. Gabor weak label 함수
    thetas = np.linspace(0, np.pi, 4, endpoint=False)
    gks = [gabor_kernel(theta=float(t)) for t in thetas]

    def gabor_label(img_resized: np.ndarray) -> np.ndarray:
        gray = to_grayscale(img_resized)
        resp = np.zeros_like(gray, dtype=np.float64)
        for k in gks:
            resp = np.maximum(resp, np.abs(_convolve(gray, k)))
        thr = float(np.percentile(resp, 90.0))
        return (resp > thr).astype(np.float32)

    # 3. eval 루프
    eval_dir = Path(args.eval_dir)
    img_paths = []
    for ext in ("*.jpg", "*.png", "*.JPG"):
        img_paths.extend(sorted(eval_dir.glob(ext)))
    print(f"[eval] {len(img_paths)} 장")

    bce = nn.BCEWithLogitsLoss()
    losses = []
    ious = []
    f1s = []
    consistencies = []  # TTA 일관성 (원본 vs 수평반전 IoU)

    with torch.no_grad():
        for i, p in enumerate(img_paths):
            tensor = read_image(str(p))
            arr = tensor.permute(1, 2, 0).numpy()
            if arr.shape[-1] >= 3:
                arr = arr[..., :3].astype(np.uint8)
            img_r = _resize_nearest(arr, args.img_size, args.img_size)

            # Gabor weak label
            lbl = gabor_label(img_r)
            lbl_t = torch.from_numpy(lbl).unsqueeze(0).unsqueeze(0).float().to(device)

            # CFM 추론
            img_norm = img_r.astype(np.float32) / 255.0
            img_t = torch.from_numpy(img_norm.transpose(2, 0, 1)).unsqueeze(0).float().to(device)
            logits = model(img_t)
            loss = bce(logits, lbl_t).item()
            losses.append(loss)

            prob = torch.sigmoid(logits).cpu().numpy()[0, 0]
            pred = (prob > 0.5).astype(np.float32)

            # IoU
            inter = float((pred * lbl).sum())
            union = float(pred.sum() + lbl.sum() - inter)
            iou = inter / max(union, 1.0)
            ious.append(iou)

            # F1 (Gabor 기준)
            tp = inter
            fp = float(pred.sum() - inter)
            fn = float(lbl.sum() - inter)
            precision = tp / max(tp + fp, 1.0)
            recall = tp / max(tp + fn, 1.0)
            f1 = 2 * precision * recall / max(precision + recall, 1.0)
            f1s.append(f1)

            # TTA 일관성: 수평반전 후 추론 → 다시 반전 → 원본 pred와 IoU
            img_flip = img_r[:, ::-1].copy()
            img_t_flip = torch.from_numpy(
                (img_flip.astype(np.float32) / 255.0).transpose(2, 0, 1)
            ).unsqueeze(0).float().to(device)
            logits_flip = model(img_t_flip)
            pred_flip_back = (torch.sigmoid(logits_flip).cpu().numpy()[0, 0] > 0.5)[:, ::-1].astype(np.float32)
            inter_c = float((pred * pred_flip_back).sum())
            union_c = float(pred.sum() + pred_flip_back.sum() - inter_c)
            consistencies.append(inter_c / max(union_c, 1.0))

            if (i + 1) % 20 == 0:
                print(f"  [{i+1}/{len(img_paths)}] loss={np.mean(losses):.4f} "
                      f"iou={np.mean(ious):.4f} f1={np.mean(f1s):.4f} "
                      f"consistency={np.mean(consistencies):.4f}", flush=True)

    print()
    print("=" * 60)
    print(f"[최종 결과] hold-out {len(img_paths)} 장")
    print(f"  BCE loss (vs Gabor weak):  {np.mean(losses):.4f}")
    print(f"  IoU (vs Gabor weak):        {np.mean(ious):.4f}")
    print(f"  F1 (vs Gabor weak):         {np.mean(f1s):.4f}")
    print(f"  Consistency (TTA hflip):    {np.mean(consistencies):.4f}")
    print("=" * 60)
    print("(주의) Gabor 약지도 기준 — 절대 F1 아님. consistency 가 더 신뢰 가능.")


if __name__ == "__main__":
    main()
