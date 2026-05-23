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

    weights_path = os.environ.get(_MODEL_PATH_ENV)
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
    """U-Net 추론 — PyTorch + 가중치 가용 시만 실행.

    NOTE: 본 함수는 **placeholder** — 실 모델 가중치·학습 데이터 부재로
    실 추론 로직은 사용자 결단 후 구현. 본 ADR은 인터페이스만 영속.

    Args:
        img: 입력 이미지.
        weights_path: 모델 가중치 파일 경로.

    Returns:
        {"mask": np.ndarray, "raw_metrics": dict} or None if not implemented.
    """
    # 사용자 결단 후 다음 구현 필요:
    # 1. U-Net 모델 정의 (milesial/Pytorch-UNet 등에서 import)
    # 2. weights_path로 torch.load() + state_dict 로드
    # 3. 이미지 전처리 (resize·normalize)
    # 4. model.forward(img) → 픽셀 마스크
    # 5. 마스크를 5 영역으로 분할해 밀도 산출 (Gabor와 동일 형식)
    return None
