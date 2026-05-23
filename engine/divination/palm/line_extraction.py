"""ADR-215 - 손금 선 검출 (numpy + scipy 단독, OpenCV 의존성 X).

학술 근거:
  - arXiv 1312.6219 "Extracting Region of Interest for Palm Print Authentication"
  - arXiv 2102.12127 "Efficient Palm-Line Segmentation with U-Net Context Fusion" F1 99.42%
  - Gabor 필터 + Hough Transform 고전 CV 접근

본 모듈은 가벼운 학술 기반 Gabor 필터 단독 구현:
  - 사용자 손금 이미지 (numpy array) 입력
  - 4 방향 Gabor 응답 + 임계 → 선 후보 픽셀
  - 영역별 (상·중·하·좌·우) 선 밀도 산출
  - "감정선·두뇌선·생명선" 같은 학파 명칭 매핑 X — 영역 밀도만

ADR-006 자문 거절 정신 보존:
  - 학파 명칭 (감정선·생명선) 본 모듈은 노출 X — scoring.py 위임
  - "긴 생명선이라 장수" 같은 운명 매핑 X
  - prevalence 통계(ADR-192) 와 동일 패턴

ADR 정합:
  - ADR-162 (손금 선 추출 거절 → 본 ADR-215로 부분 회복)
  - ADR-010 사실성 분리 (arXiv 학술 출처 명시)
  - ADR-006 자문 거절 (운명 매핑 차단)
  - ADR-030 palm scoring 인터페이스 (raw metric 입력 형식 정합)
  - ADR-171 fate_assertion (description 통과)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

try:
    from scipy.ndimage import convolve as _ndimage_convolve
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False


SOURCE_URLS = (
    "https://arxiv.org/pdf/2102.12127",  # U-Net Palm Line Segmentation 2021
    "https://arxiv.org/pdf/1312.6219",   # Palm Print ROI Extraction
)


DISCLAIMER = (
    "본 손금 선 검출은 학술 출처(arXiv 2102.12127 / 1312.6219) 기반 정량 측정 "
    "결과로, 운명·길흉·수명·재물 매핑이 아닙니다. 사진 조명·해상도에 따라 "
    "검출 정확도가 변동되며, 의료 진단·인격 평가가 아닙니다."
)


# ───── Gabor 커널 생성 ─────

def gabor_kernel(
    ksize: int = 15,
    sigma: float = 4.0,
    theta: float = 0.0,
    lambd: float = 10.0,
    gamma: float = 0.5,
    psi: float = 0.0,
) -> np.ndarray:
    """Gabor 필터 커널 (numpy 단독, OpenCV 무관).

    공식: g(x,y) = exp(-(x'^2 + gamma^2 y'^2) / (2 sigma^2)) * cos(2π x' / lambd + psi)
      x' = x cos(theta) + y sin(theta)
      y' = -x sin(theta) + y cos(theta)

    Args:
        ksize: 커널 크기 (홀수)
        sigma: 가우시안 표준편차
        theta: 방향 (라디안, 0~π)
        lambd: 파장
        gamma: 종횡비
        psi: 위상 오프셋

    Returns:
        (ksize, ksize) float64 커널.
    """
    half = ksize // 2
    y, x = np.mgrid[-half:half + 1, -half:half + 1]
    x_theta = x * np.cos(theta) + y * np.sin(theta)
    y_theta = -x * np.sin(theta) + y * np.cos(theta)
    sigma_sq = sigma * sigma
    envelope = np.exp(-(x_theta ** 2 + gamma ** 2 * y_theta ** 2) / (2 * sigma_sq))
    carrier = np.cos(2 * np.pi * x_theta / lambd + psi)
    return envelope * carrier


# ───── 그레이스케일 변환 ─────

def to_grayscale(img: np.ndarray) -> np.ndarray:
    """RGB → 그레이스케일 (BT.709 luminance).

    Args:
        img: (H, W, 3) RGB 또는 (H, W) 그레이.

    Returns:
        (H, W) float64.
    """
    if img.ndim == 2:
        return img.astype(np.float64)
    if img.ndim == 3 and img.shape[2] >= 3:
        # BT.709
        return (
            0.2126 * img[..., 0]
            + 0.7152 * img[..., 1]
            + 0.0722 * img[..., 2]
        ).astype(np.float64)
    raise ValueError(f"unsupported image shape: {img.shape}")


# ───── 합성곱 (scipy fallback numpy) ─────

def _convolve(img: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """합성곱 — scipy.ndimage 우선, fallback numpy."""
    if _HAS_SCIPY:
        return _ndimage_convolve(img, kernel, mode="reflect")
    # numpy fallback (느림)
    return _numpy_convolve_2d(img, kernel)


def _numpy_convolve_2d(img: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """numpy 단독 2D 합성곱 (scipy 부재 시)."""
    h, w = img.shape
    kh, kw = kernel.shape
    pad_h = kh // 2
    pad_w = kw // 2
    padded = np.pad(img, ((pad_h, pad_h), (pad_w, pad_w)), mode="reflect")
    out = np.zeros_like(img, dtype=np.float64)
    flipped = kernel[::-1, ::-1]
    for i in range(h):
        for j in range(w):
            out[i, j] = np.sum(padded[i:i + kh, j:j + kw] * flipped)
    return out


# ───── 결과 dataclass ─────

@dataclass(frozen=True)
class PalmLineExtractionResult:
    """손금 선 검출 결과."""
    n_lines_detected: int       # 검출 영역 수 (0~5)
    line_density: float         # 전체 선 밀도 0~1
    raw_metrics: dict[str, float] = field(default_factory=dict)
    description_ko: str = ""
    source_urls: tuple[str, ...] = SOURCE_URLS
    disclaimer: str = DISCLAIMER


# ───── 메인 검출 함수 ─────

def detect_palm_lines(
    img: np.ndarray,
    n_orientations: int = 4,
    threshold_percentile: float = 90.0,
) -> PalmLineExtractionResult:
    """손금 이미지 → 영역별 선 밀도.

    Args:
        img: numpy array (H, W, 3) RGB 또는 (H, W) gray.
        n_orientations: Gabor 방향 수 (4 = 0°·45°·90°·135°)
        threshold_percentile: 선 후보 임계 (90 percentile).

    Returns:
        PalmLineExtractionResult — 영역별 밀도 + disclaimer.
    """
    if not isinstance(img, np.ndarray) or img.size == 0:
        return PalmLineExtractionResult(
            n_lines_detected=0, line_density=0.0,
            description_ko="이미지가 비어 있거나 잘못된 형식입니다.",
        )

    if img.ndim < 2 or (img.ndim == 3 and img.shape[2] < 3):
        return PalmLineExtractionResult(
            n_lines_detected=0, line_density=0.0,
            description_ko="이미지 형식이 잘못되었습니다.",
        )

    try:
        gray = to_grayscale(img)
    except Exception:
        return PalmLineExtractionResult(
            n_lines_detected=0, line_density=0.0,
            description_ko="이미지 변환 실패.",
        )

    h, w = gray.shape
    if h < 30 or w < 30:
        return PalmLineExtractionResult(
            n_lines_detected=0, line_density=0.0,
            description_ko="이미지 해상도가 너무 낮습니다.",
        )

    # 4 방향 Gabor 응답 합 (선 강도)
    thetas = np.linspace(0, np.pi, n_orientations, endpoint=False)
    response = np.zeros_like(gray, dtype=np.float64)
    for theta in thetas:
        k = gabor_kernel(theta=float(theta))
        r = _convolve(gray, k)
        response = np.maximum(response, np.abs(r))

    # 선 후보 마스크 (percentile 임계)
    threshold = float(np.percentile(response, threshold_percentile))
    mask = response > threshold

    # 5 영역 분할 — 상·중·하 + 하좌·하우 (생명선은 손바닥 하좌측 주로)
    upper = mask[: h // 3, :]
    middle = mask[h // 3 : 2 * h // 3, :]
    lower = mask[2 * h // 3 :, :]
    lower_left = mask[2 * h // 3 :, : w // 2]
    lower_right = mask[2 * h // 3 :, w // 2 :]

    def _density(m: np.ndarray) -> float:
        if m.size == 0:
            return 0.0
        return float(m.sum()) / m.size

    upper_d = _density(upper)
    middle_d = _density(middle)
    lower_d = _density(lower)
    lower_left_d = _density(lower_left)
    lower_right_d = _density(lower_right)
    overall_d = _density(mask)

    # 검출 영역 수 (밀도 > 0.05 인 영역 카운트)
    n_lines = sum(
        1 for d in (upper_d, middle_d, lower_d, lower_left_d, lower_right_d)
        if d > 0.05
    )

    raw_metrics = {
        "upper_density": round(upper_d, 4),
        "middle_density": round(middle_d, 4),
        "lower_density": round(lower_d, 4),
        "lower_left_density": round(lower_left_d, 4),
        "lower_right_density": round(lower_right_d, 4),
        "overall_density": round(overall_d, 4),
        "gabor_threshold": round(threshold, 2),
    }

    # 사극풍 묘사 (운명 매핑 X — 영역 밀도만 묘사)
    if n_lines == 0:
        desc = "손금 선이 거의 검출되지 않았습니다. 사진을 다시 살펴보아 주십시오."
    elif n_lines <= 2:
        desc = "손금 선이 일부 영역에서 또렷이 나타났습니다."
    elif n_lines == 3:
        desc = "손금 선이 세 영역(상·중·하)에서 또렷이 나타났습니다."
    else:
        desc = "손금 선이 여러 영역에 걸쳐 풍부하게 나타났습니다."

    return PalmLineExtractionResult(
        n_lines_detected=n_lines,
        line_density=round(overall_d, 4),
        raw_metrics=raw_metrics,
        description_ko=desc,
    )


# ───── scoring.py 호환 raw metric 변환 ─────

def to_scoring_metrics(result: PalmLineExtractionResult) -> dict[str, float]:
    """ADR-030 scoring.py `_compute_lifeline_metric` 등이 받는 raw 메트릭 변환.

    Args:
        result: detect_palm_lines() 결과.

    Returns:
        {
            "lifeline_arc": float,  # 하좌측 밀도 (생명선 영역)
            "headline_horizontal": float,  # 중부 밀도
            "heartline_curve": float,  # 상부 밀도
            ...
        }
    """
    rm = result.raw_metrics
    return {
        # 생명선 영역 = 하좌측 (엄지~손목)
        "lifeline_arc": rm.get("lower_left_density", 0.0),
        # 두뇌선 영역 = 중부 가로
        "headline_horizontal": rm.get("middle_density", 0.0),
        # 감정선 영역 = 상부
        "heartline_curve": rm.get("upper_density", 0.0),
        # 운명선 영역 = 중하부 세로 (밀도 평균)
        "fateline_vertical": (rm.get("middle_density", 0.0)
                              + rm.get("lower_density", 0.0)) / 2.0,
        # 금성대 = 상부 (감정선 위)
        "girdle_arc": rm.get("upper_density", 0.0),
    }
