"""ADR-227 - 손금 학습 데이터 자동 증강 (data augmentation).

학술 근거:
  - Shorten & Khoshgoftaar 2019 "A survey on Image Data Augmentation for Deep Learning"
  - 일반 segmentation: rotation·flip·noise·color jitter 표준

본 모듈은 numpy 단독 구현 — PyTorch 의존성 옵션.

ADR 정합:
  - ADR-220 self-training (본 ADR이 증강으로 데이터 증폭)
  - ADR-223 합성 데이터 + 본 ADR 증강 → 효과적 학습량 증대
  - ADR-006 학파 명칭 X
"""

from __future__ import annotations

import numpy as np


def augment_horizontal_flip(img: np.ndarray, mask: np.ndarray) -> tuple:
    """좌우 반전."""
    return img[:, ::-1].copy(), mask[:, ::-1].copy()


def augment_rotation(
    img: np.ndarray, mask: np.ndarray, angle_deg: float,
) -> tuple:
    """회전 — 단순 nearest neighbor (PIL/cv2 의존성 회피).

    Args:
        img: (H, W, 3) RGB.
        mask: (H, W) binary.
        angle_deg: 회전 각도 (도). 양수 = 시계방향.

    Returns:
        (회전된 이미지, 회전된 마스크).
    """
    h, w = img.shape[:2]
    cy, cx = h / 2, w / 2
    theta = np.deg2rad(-angle_deg)  # 영상 좌표계 보정
    cos_t, sin_t = np.cos(theta), np.sin(theta)

    # 출력 좌표 그리드
    y_out, x_out = np.indices((h, w))
    # 중심 기준 좌표
    dy = y_out - cy
    dx = x_out - cx
    # 역회전 (소스 좌표)
    x_src = cos_t * dx - sin_t * dy + cx
    y_src = sin_t * dx + cos_t * dy + cy
    # nearest neighbor
    x_src_int = np.clip(np.round(x_src).astype(int), 0, w - 1)
    y_src_int = np.clip(np.round(y_src).astype(int), 0, h - 1)

    img_rot = img[y_src_int, x_src_int]
    mask_rot = mask[y_src_int, x_src_int]
    return img_rot.copy(), mask_rot.copy()


def augment_brightness(
    img: np.ndarray, mask: np.ndarray, delta: int,
) -> tuple:
    """밝기 조절 (±delta).

    Args:
        delta: -50 ~ +50 권장.
    """
    img_aug = np.clip(img.astype(np.int16) + delta, 0, 255).astype(np.uint8)
    return img_aug, mask.copy()


def augment_gaussian_noise(
    img: np.ndarray, mask: np.ndarray, sigma: float = 10.0,
    seed: int | None = None,
) -> tuple:
    """가우시안 노이즈 추가."""
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, sigma, img.shape).astype(np.int16)
    img_aug = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return img_aug, mask.copy()


def augment_color_jitter(
    img: np.ndarray, mask: np.ndarray,
    r_scale: float = 1.0, g_scale: float = 1.0, b_scale: float = 1.0,
) -> tuple:
    """채널별 색 강도 조절."""
    img_aug = img.astype(np.float32).copy()
    img_aug[..., 0] *= r_scale
    img_aug[..., 1] *= g_scale
    img_aug[..., 2] *= b_scale
    img_aug = np.clip(img_aug, 0, 255).astype(np.uint8)
    return img_aug, mask.copy()


def augment_batch(
    img: np.ndarray, mask: np.ndarray, n_variants: int = 5,
    seed: int = 42,
) -> list[tuple]:
    """단일 (img, mask) 쌍 → n개 증강 변형 리스트.

    Args:
        img: 원본 이미지.
        mask: 원본 마스크.
        n_variants: 증강 변형 수 (기본 5).
        seed: 난수 시드.

    Returns:
        [(원본+변형들 (img, mask)] 리스트.
    """
    rng = np.random.default_rng(seed)
    results = [(img.copy(), mask.copy())]  # 원본 포함

    augmentation_pool = [
        lambda i, m: augment_horizontal_flip(i, m),
        lambda i, m: augment_rotation(i, m, float(rng.uniform(-15, 15))),
        lambda i, m: augment_brightness(i, m, int(rng.integers(-30, 31))),
        lambda i, m: augment_gaussian_noise(i, m, sigma=float(rng.uniform(5, 15))),
        lambda i, m: augment_color_jitter(
            i, m,
            r_scale=float(rng.uniform(0.85, 1.15)),
            g_scale=float(rng.uniform(0.85, 1.15)),
            b_scale=float(rng.uniform(0.85, 1.15)),
        ),
    ]

    for _ in range(n_variants):
        # 1~2개 무작위 증강 조합
        n_ops = int(rng.integers(1, 3))
        ops_idx = rng.choice(len(augmentation_pool), size=n_ops, replace=False)
        cur_img, cur_mask = img.copy(), mask.copy()
        for idx in ops_idx:
            cur_img, cur_mask = augmentation_pool[idx](cur_img, cur_mask)
        results.append((cur_img, cur_mask))
    return results
