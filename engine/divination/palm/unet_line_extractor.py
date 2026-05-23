"""ADR-216 - U-Net 손금 선 검출 인터페이스 (PyTorch 옵션 의존성).

학술 근거:
  - arXiv 2102.12127 "Efficient Palm-Line Segmentation with U-Net Context Fusion"
    F1 99.42% (Sun-Asterisk Inc 사내 모델, 공개 가중치 부재)
  - milesial/Pytorch-UNet (GPL-3.0)
  - qubvel-org/segmentation_models.pytorch (MIT) — 사전학습 backbone

본 모듈은 **PyTorch 부재 시 자동 fallback 설계**:
  - PyTorch 설치 + 모델 가중치 경로 설정 → U-Net 사용 (F1 99% 목표)
  - PyTorch 부재 또는 가중치 부재 → ADR-215 Gabor fallback (F1 80~90%)

사용자 결단 필요 영역 (본 AI 단독 X):
  - PyTorch 의존성 추가 (`requirements.txt` 변경)
  - 모델 가중치 라이선스 확인·구매·학습
  - GPU 인프라 (Fly.io 비용)

본 모듈은 **인터페이스만** 영속 — 라이선스·인프라 결단 전에도 코드는 보존.

ADR 정합:
  - ADR-215 Gabor (fallback) — 본 ADR이 메인 인터페이스 + Gabor 폴백
  - ADR-162 거절 영역 — U-Net 인터페이스로 추가 회복 경로
  - ADR-006 자문 거절 (학파 명칭 X, 영역 밀도만)
  - ADR-010 사실성 분리 (사용자 결단 영역 분리)
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np


# 환경변수로 모델 경로 지정 (사용자 결단 시 설정)
_MODEL_PATH_ENV = "PALM_UNET_MODEL_PATH"

# ADR-222 + ADR-246 — 기본 가중치 경로 자동 탐색
# models/ 우선 (Fly.io 볼륨 마운트 /app/data 회피 — ADR-246).
# data/palm/ 는 레거시 호환.
_DEFAULT_WEIGHTS_PATHS = (
    "models/unet_weights.pt",
    "models/unet_weights.pth",
    "data/palm/unet_weights.pt",
    "data/palm/unet_weights.pth",
)


# PyTorch 옵션 import
try:
    import torch
    _HAS_TORCH = True
except ImportError:
    _HAS_TORCH = False


SOURCE_URL_PAPER = "https://arxiv.org/abs/2102.12127"
SOURCE_URL_PYTORCH_UNET = "https://github.com/milesial/Pytorch-UNet"


DISCLAIMER = (
    "본 U-Net 검출은 PyTorch + 학습 가중치 사용 시 활성화되며 부재 시 "
    "ADR-215 Gabor fallback. 학파 명칭(생명선·감정선)은 결정론 점수가 "
    "유일한 출처이며 운명·길흉 매핑이 아닙니다."
)


@dataclass(frozen=True)
class UNetAvailability:
    """U-Net 가용성 상태."""
    pytorch_available: bool
    model_weights_path: str | None
    model_loadable: bool
    fallback_reason: str        # "ready" / "no_pytorch" / "no_weights" / "load_failed"


def check_unet_availability() -> UNetAvailability:
    """U-Net 활성화 가능 여부 점검 (모델 로드 없이).

    Returns:
        UNetAvailability — PyTorch 설치·모델 경로·로드 가능 여부.
    """
    if not _HAS_TORCH:
        return UNetAvailability(
            pytorch_available=False,
            model_weights_path=None,
            model_loadable=False,
            fallback_reason="no_pytorch",
        )

    # 1. 환경변수 우선
    weights_path = os.environ.get(_MODEL_PATH_ENV)
    # 2. ADR-222 — 환경변수 부재 시 기본 경로 자동 탐색
    if not weights_path:
        for default_path in _DEFAULT_WEIGHTS_PATHS:
            if os.path.exists(default_path):
                weights_path = default_path
                break

    if not weights_path:
        return UNetAvailability(
            pytorch_available=True,
            model_weights_path=None,
            model_loadable=False,
            fallback_reason="no_weights",
        )

    if not os.path.exists(weights_path):
        return UNetAvailability(
            pytorch_available=True,
            model_weights_path=weights_path,
            model_loadable=False,
            fallback_reason="no_weights",
        )

    return UNetAvailability(
        pytorch_available=True,
        model_weights_path=weights_path,
        model_loadable=True,
        fallback_reason="ready",
    )


@dataclass(frozen=True)
class UNetExtractionResult:
    """U-Net 손금 선 검출 결과."""
    used_unet: bool             # True면 U-Net, False면 Gabor fallback
    mask: np.ndarray | None     # U-Net 픽셀 마스크 (사용 안 함 시 None)
    raw_metrics: dict           # 5 영역 밀도 (Gabor와 동일 형식)
    fallback_reason: str
    source_url: str
    disclaimer: str = DISCLAIMER


def extract_palm_lines_best_available(
    img: np.ndarray,
) -> UNetExtractionResult:
    """가장 정확한 가용 방식으로 손금 선 추출.

    우선순위:
      1. U-Net (PyTorch + 가중치 가용 시) — F1 99% 목표
      2. Gabor (ADR-215) — F1 80~90%

    Args:
        img: numpy array (H, W, 3) RGB 또는 (H, W) gray.

    Returns:
        UNetExtractionResult — used_unet + raw_metrics + fallback 사유.
    """
    avail = check_unet_availability()

    if avail.model_loadable:
        try:
            result = _run_unet_inference(img, avail.model_weights_path)
            if result is not None:
                return UNetExtractionResult(
                    used_unet=True,
                    mask=result["mask"],
                    raw_metrics=result["raw_metrics"],
                    fallback_reason="ready",
                    source_url=SOURCE_URL_PAPER,
                )
        except Exception:
            # U-Net 실패 → Gabor fallback
            pass

    # Gabor fallback (ADR-215)
    from engine.divination.palm.line_extraction import detect_palm_lines
    gabor_result = detect_palm_lines(img)
    return UNetExtractionResult(
        used_unet=False,
        mask=None,
        raw_metrics=gabor_result.raw_metrics,
        fallback_reason=avail.fallback_reason,
        source_url=gabor_result.source_urls[0] if gabor_result.source_urls else "",
    )


def _run_unet_inference(
    img: np.ndarray,
    weights_path: str | None,
) -> dict | None:
    """ADR-217 — U-Net 추론 실 구현.

    PyTorch + 가중치 파일 가용 시 milesial/Pytorch-UNet 아키텍처로 추론.
    GPL-3.0 라이선스 (본 시스템 학습·재사용 시 의무 — 운영 시 사용자 결단).

    Args:
        img: 입력 이미지 (H, W, 3) RGB.
        weights_path: 모델 가중치 파일 경로 (.pt or .pth).

    Returns:
        {"mask": np.ndarray, "raw_metrics": dict} or None on failure.
    """
    if not _HAS_TORCH or not weights_path:
        return None

    try:
        # 동적 import (PyTorch 부재 시 모듈 import 실패 없도록)
        import torch as _torch
        from engine.divination.palm.unet_model import UNet as _UNet
        # ADR-233 — CFM 모델 옵션
        try:
            from engine.divination.palm.unet_cfm import UNetCFM as _UNetCFM
            _has_cfm = True
        except ImportError:
            _has_cfm = False
    except ImportError:
        return None

    try:
        # 가중치 로드 (weights_only=True for security)
        device = _torch.device("cuda" if _torch.cuda.is_available() else "cpu")
        state = _torch.load(weights_path, map_location=device, weights_only=True)
        if isinstance(state, dict) and "state_dict" in state:
            state = state["state_dict"]

        # ADR-233 — 가중치 키 패턴으로 모델 자동 식별
        # CFM 모델은 'cfm.' / 'attention' / 'branch1' 등 키 보유
        is_cfm_weights = (
            _has_cfm and isinstance(state, dict) and any(
                "cfm" in k or "attention" in k or "branch" in k
                for k in state.keys()
            )
        )
        if is_cfm_weights:
            model = _UNetCFM(n_channels=3, n_classes=1)
        else:
            model = _UNet(n_channels=3, n_classes=1)
        model.load_state_dict(state, strict=False)
        model.to(device).eval()

        # 전처리: RGB (H, W, 3) → (1, 3, 256, 256) 정규화
        if img.ndim == 2:
            img_rgb = np.stack([img] * 3, axis=-1)
        else:
            img_rgb = img[..., :3]
        # 256x256 리사이즈 (간단 nearest neighbor — scipy 없을 때 안전)
        img_resized = _resize_nearest(img_rgb.astype(np.float32), 256, 256)
        img_norm = img_resized / 255.0
        # (H, W, 3) → (1, 3, H, W)
        tensor = _torch.from_numpy(img_norm.transpose(2, 0, 1)).unsqueeze(0).float().to(device)

        # 추론
        with _torch.no_grad():
            logits = model(tensor)
            prob = _torch.sigmoid(logits).cpu().numpy()[0, 0]  # (H, W)

        # 픽셀 마스크 (확률 > 0.5)
        mask = prob > 0.5

        # 5 영역 밀도 (Gabor와 동일 형식)
        h, w = mask.shape
        upper = mask[: h // 3, :]
        middle = mask[h // 3 : 2 * h // 3, :]
        lower = mask[2 * h // 3 :, :]
        lower_left = mask[2 * h // 3 :, : w // 2]
        lower_right = mask[2 * h // 3 :, w // 2 :]

        def _density(m: np.ndarray) -> float:
            if m.size == 0:
                return 0.0
            return float(m.sum()) / m.size

        raw_metrics = {
            "upper_density": round(_density(upper), 4),
            "middle_density": round(_density(middle), 4),
            "lower_density": round(_density(lower), 4),
            "lower_left_density": round(_density(lower_left), 4),
            "lower_right_density": round(_density(lower_right), 4),
            "overall_density": round(_density(mask), 4),
            "unet_threshold": 0.5,
        }
        return {"mask": mask, "raw_metrics": raw_metrics}
    except Exception:
        return None


def _resize_nearest(img: np.ndarray, target_h: int, target_w: int) -> np.ndarray:
    """간단 nearest-neighbor 리사이즈 (PIL/cv2 의존성 회피)."""
    h, w = img.shape[:2]
    if h == target_h and w == target_w:
        return img
    y_idx = (np.arange(target_h) * h / target_h).astype(int)
    x_idx = (np.arange(target_w) * w / target_w).astype(int)
    return img[y_idx[:, None], x_idx[None, :]]
