"""ADR-231 - Test-Time Augmentation (TTA) — 추론 시 다중 변형 평균.

학술 근거:
  - Krizhevsky et al. 2012 (AlexNet) — TTA 표준 패턴
  - F1 +1~3% 향상 보고 일반적

전략:
  1. 원본 + 4 변형 (수평 반전·회전 ±10° / ±5°) 추론
  2. 5 마스크 평균 → 더 안정적 예측
  3. 단일 추론 대비 +1~3% F1 향상

비용:
  - 추론 시간 5배 (5장)
  - 정확도 ↑

ADR 정합:
  - ADR-217 U-Net 추론 인터페이스 재사용
  - ADR-227 augmentation 변형 함수 재사용
  - ADR-006 학파 명칭 X
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TTAResult:
    """Test-Time Augmentation 추론 결과."""
    averaged_mask: np.ndarray | None    # 평균 마스크 (확률 0~1)
    n_augmentations: int                # 사용된 변형 수
    raw_metrics: dict                   # 5 영역 밀도 (평균 마스크 기반)
    confidence_avg: float               # 평균 confidence (양극단 비율)


def _augment_inputs(img: np.ndarray) -> list[tuple[np.ndarray, str]]:
    """원본 + 4 변형 생성.

    Returns:
        [(변형 이미지, 역변환 키)] 리스트.
        역변환 키: "identity" / "hflip" / "rot+10" / "rot-10" / "rot+5"
    """
    try:
        from engine.divination.palm.augmentation import (
            augment_horizontal_flip, augment_rotation,
        )
    except ImportError:
        return [(img.copy(), "identity")]

    h, w = img.shape[:2]
    dummy_mask = np.zeros((h, w), dtype=np.float32)

    variants = [(img.copy(), "identity")]
    # 수평 반전
    flipped_img, _ = augment_horizontal_flip(img, dummy_mask)
    variants.append((flipped_img, "hflip"))
    # 회전 ±10°
    for angle in [10, -10, 5]:
        rot_img, _ = augment_rotation(img, dummy_mask, float(angle))
        variants.append((rot_img, f"rot{angle:+d}"))
    return variants


def _inverse_transform_mask(
    mask: np.ndarray, transform_key: str,
) -> np.ndarray:
    """추론 마스크를 원본 좌표계로 역변환.

    Args:
        mask: 변형된 이미지의 추론 마스크.
        transform_key: 적용된 변형 키.

    Returns:
        원본 좌표계 마스크.
    """
    if transform_key == "identity":
        return mask
    if transform_key == "hflip":
        return mask[:, ::-1].copy()
    if transform_key.startswith("rot"):
        try:
            from engine.divination.palm.augmentation import augment_rotation
            angle_str = transform_key.replace("rot", "")
            angle = float(angle_str)
            # 역회전
            dummy_img = np.zeros((*mask.shape, 3), dtype=np.uint8)
            _, restored = augment_rotation(dummy_img, mask, -angle)
            return restored
        except Exception:
            return mask
    return mask


def run_tta_inference(
    img: np.ndarray,
) -> TTAResult:
    """TTA 추론 — 원본 + 4 변형 평균.

    Args:
        img: 입력 이미지 (H, W, 3) RGB.

    Returns:
        TTAResult — 평균 마스크 + raw_metrics.
    """
    try:
        from engine.divination.palm.unet_line_extractor import (
            extract_palm_lines_best_available, check_unet_availability,
        )
    except ImportError:
        return TTAResult(
            averaged_mask=None, n_augmentations=0,
            raw_metrics={}, confidence_avg=0.0,
        )

    avail = check_unet_availability()
    if not avail.model_loadable:
        # U-Net 부재 — Gabor 단일 추론
        r = extract_palm_lines_best_available(img)
        return TTAResult(
            averaged_mask=None, n_augmentations=1,
            raw_metrics=r.raw_metrics, confidence_avg=0.0,
        )

    # U-Net + TTA
    variants = _augment_inputs(img)
    masks = []
    for variant_img, transform_key in variants:
        r = extract_palm_lines_best_available(variant_img)
        if r.mask is None:
            continue
        # 역변환
        restored = _inverse_transform_mask(r.mask.astype(np.float32), transform_key)
        masks.append(restored)

    if not masks:
        return TTAResult(
            averaged_mask=None, n_augmentations=0,
            raw_metrics={}, confidence_avg=0.0,
        )

    # 평균 마스크
    h, w = masks[0].shape
    # 모든 마스크가 동일 크기 보장 (회전 시 약간 차이 가능 — clip)
    masks_aligned = [m[:h, :w] if m.shape >= (h, w) else m for m in masks]
    avg_mask = np.mean(np.stack(masks_aligned, axis=0), axis=0)

    # 이진화 (확률 > 0.5)
    binary_mask = avg_mask > 0.5

    # 5 영역 밀도
    upper = binary_mask[: h // 3, :]
    middle = binary_mask[h // 3 : 2 * h // 3, :]
    lower = binary_mask[2 * h // 3 :, :]
    lower_left = binary_mask[2 * h // 3 :, : w // 2]
    lower_right = binary_mask[2 * h // 3 :, w // 2 :]

    def _density(m: np.ndarray) -> float:
        return float(m.sum() / max(m.size, 1))

    raw_metrics = {
        "upper_density": round(_density(upper), 4),
        "middle_density": round(_density(middle), 4),
        "lower_density": round(_density(lower), 4),
        "lower_left_density": round(_density(lower_left), 4),
        "lower_right_density": round(_density(lower_right), 4),
        "overall_density": round(_density(binary_mask), 4),
        "tta_n_variants": len(masks),
    }

    # 평균 confidence (양극단 = 확신)
    confidence = float(np.abs(avg_mask - 0.5).mean() * 2)

    return TTAResult(
        averaged_mask=avg_mask.astype(np.float32),
        n_augmentations=len(masks),
        raw_metrics=raw_metrics,
        confidence_avg=round(confidence, 4),
    )
