"""ADR-232 - 좌·우 손 분리 분석 + 비대칭 점수.

학술 근거:
  - dermatoglyphic asymmetry — 좌·우 손금 차이는 생물학적 변이 (의료 인과 X)
  - 손금학 통설 — 왼손/오른손 의미 차이 (단정 매핑은 ADR-006 차단)

본 모듈은 좌·우 손 사진 각각 분석 → 비대칭 점수 산출:
  - 영역 밀도 차이 (좌·우)
  - 우세 손 (강한 선) 식별
  - 비대칭 점수 (0~1, 0 = 완전 대칭)

ADR 정합:
  - ADR-160 MediaPipe Hand Landmarker (handedness 식별)
  - ADR-215 line_extraction 재사용
  - ADR-006 학파 명칭 X (대칭성 점수만)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LeftRightAnalysisResult:
    """좌·우 손 비교 결과."""
    left_metrics: dict           # 좌측 손 raw_metrics
    right_metrics: dict          # 우측 손 raw_metrics
    asymmetry_score: float       # 0~1 (0 = 완전 대칭, 1 = 극단 비대칭)
    dominant_side: str           # "left" / "right" / "balanced"
    description_ko: str
    disclaimer: str = (
        "본 좌·우 비교는 dermatoglyphic 변이 통계 분석이며 "
        "운명·길흉 매핑이 아닙니다."
    )


def compute_asymmetry(
    left_metrics: dict,
    right_metrics: dict,
) -> tuple[float, str]:
    """좌·우 손 raw_metrics → 비대칭 점수 + 우세 손.

    Args:
        left_metrics: 좌측 손 영역 밀도 dict (line_extraction 결과).
        right_metrics: 우측 손 동일.

    Returns:
        (asymmetry_score, dominant_side).
    """
    keys = ("upper_density", "middle_density", "lower_density",
            "lower_left_density", "lower_right_density")

    diffs = []
    left_total = 0.0
    right_total = 0.0
    for k in keys:
        lv = float(left_metrics.get(k, 0.0))
        rv = float(right_metrics.get(k, 0.0))
        diffs.append(abs(lv - rv))
        left_total += lv
        right_total += rv

    # 비대칭 점수 = 평균 차이 (0~1 정규화)
    asym = min(1.0, sum(diffs) / max(len(diffs), 1) * 5)  # 5× scale (실 차이 0~0.2)

    # 우세 손
    if abs(left_total - right_total) < 0.05:
        dominant = "balanced"
    elif left_total > right_total:
        dominant = "left"
    else:
        dominant = "right"

    return round(asym, 4), dominant


def analyze_palms(
    left_image: np.ndarray | None,
    right_image: np.ndarray | None,
) -> LeftRightAnalysisResult:
    """좌·우 손 이미지 → 비대칭 분석.

    Args:
        left_image: 좌측 손 RGB 이미지.
        right_image: 우측 손 RGB 이미지.
            한쪽만 있으면 단측 분석 (asymmetry=0).

    Returns:
        LeftRightAnalysisResult.
    """
    try:
        from engine.divination.palm.unet_line_extractor import (
            extract_palm_lines_best_available,
        )
    except ImportError:
        return LeftRightAnalysisResult(
            left_metrics={}, right_metrics={}, asymmetry_score=0.0,
            dominant_side="balanced",
            description_ko="분석 모듈 부재.",
        )

    left_metrics: dict = {}
    right_metrics: dict = {}
    if left_image is not None and isinstance(left_image, np.ndarray):
        r = extract_palm_lines_best_available(left_image)
        left_metrics = r.raw_metrics
    if right_image is not None and isinstance(right_image, np.ndarray):
        r = extract_palm_lines_best_available(right_image)
        right_metrics = r.raw_metrics

    if not left_metrics or not right_metrics:
        return LeftRightAnalysisResult(
            left_metrics=left_metrics, right_metrics=right_metrics,
            asymmetry_score=0.0, dominant_side="balanced",
            description_ko=(
                "한 손만 분석되었습니다. 좌·우 양손 사진 시 비대칭 분석 가능합니다."
            ),
        )

    asym, dominant = compute_asymmetry(left_metrics, right_metrics)

    if asym < 0.15:
        desc = f"좌·우 손금이 대칭에 가까운 결입니다 (비대칭 {asym:.2f})."
    elif asym < 0.40:
        side_ko = {"left": "왼손", "right": "오른손", "balanced": "양손"}[dominant]
        desc = (
            f"좌·우 손금에 약간의 차이가 있습니다 (비대칭 {asym:.2f}). "
            f"{side_ko}의 결이 약간 더 두드러집니다."
        )
    else:
        side_ko = {"left": "왼손", "right": "오른손", "balanced": "양손"}[dominant]
        desc = (
            f"좌·우 손금 차이가 두드러집니다 (비대칭 {asym:.2f}). "
            f"{side_ko}의 결이 우세합니다. 이는 dermatoglyphic 변이이며 "
            f"운명 매핑이 아닙니다."
        )

    return LeftRightAnalysisResult(
        left_metrics=left_metrics,
        right_metrics=right_metrics,
        asymmetry_score=asym,
        dominant_side=dominant,
        description_ko=desc,
    )
