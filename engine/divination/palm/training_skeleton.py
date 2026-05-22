"""ADR-154 — palm ML 학습 파이프라인 스켈레톤.

/domain-priorities 잔여 #2 부분 해소 — 사용자 결단 (11k Hands 학술 fair use 동의 +
실 다운로드)이 필요한 영역의 본 AI 단독 가능 코드 영속.

본 모듈은 데이터셋·모델 가중치 부재 상태에서도 import·평가 인터페이스 정합 보장.
실 학습은 사용자가 11k Hands 데이터셋 (Mahmoud Afifi 2017, IEEE) 학술 fair use
조건 확인 + 다운로드 + 라벨링 후 별건 진행.

원칙 (ADR-006·010 정합):
  · 손금 ML 산출 = 결정론 점수만 (선 굵기·교차각·길이 메트릭)
  · 길흉·결혼·이별·재정 단정 라벨 X (학습 라벨도 메트릭만)
  · 실 데이터 부재 시 NotImplementedError 명시 (가짜 모델 차단)

학술 출처 후보 (사용자 결단 영역):
  · 11k Hands (Mahmoud Afifi 2017) — https://sites.google.com/view/11khands
    · 11,076개 손 이미지 (남성/여성/dorsal/palmar)
    · 학술 fair use 조건 확인 필요
  · Kaggle 대안: shyambhu/11k-hands, gulivin/palm-print
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PalmKeypoint:
    """ADR-004 정합 — palm 결정론 keypoint (선 1개 끝점)."""
    x: float  # 0.0~1.0 정규화 좌표
    y: float
    confidence: float  # 0.0~1.0


@dataclass(frozen=True)
class PalmLineMetric:
    """단일 손금선 결정론 메트릭 (학습 후 산출)."""
    line_name: str  # "life" | "head" | "heart" | "fate"
    length_ratio: float    # 손바닥 대각선 대비 비율 (0.0~1.0)
    thickness_norm: float  # 정규화 굵기 (0.0~1.0)
    clarity_score: float   # 선명도 (0.0~1.0)
    keypoints: tuple[PalmKeypoint, ...]


@dataclass(frozen=True)
class PalmTrainingConfig:
    """학습 파이프라인 설정 (사용자 결단 영역 진입 시 사용)."""
    dataset_root: str           # 11k Hands 다운로드 경로
    train_val_split: float = 0.8
    image_size: int = 512       # 입력 해상도
    batch_size: int = 8
    epochs: int = 50
    learning_rate: float = 1e-4
    fair_use_acknowledged: bool = False  # 학술 fair use 명시 동의 (사용자 결단)


class PalmModel(Protocol):
    """ML 모델 인터페이스 (실 구현은 사용자 결단 후 별건)."""

    def predict(self, image_path: str) -> tuple[PalmLineMetric, ...]:
        """이미지 → 4 손금선 메트릭."""
        ...


# ─────────────────────────── 평가 메트릭 (학습 무관 영속) ───────────────────────────


def compute_keypoint_iou(
    predicted: tuple[PalmKeypoint, ...],
    ground_truth: tuple[PalmKeypoint, ...],
    distance_threshold: float = 0.05,
) -> float:
    """ADR-154 — keypoint 매칭 정확도 (PCK — Percentage of Correct Keypoints).

    distance_threshold 이내 매칭된 keypoint 비율.

    Args:
        predicted: 모델 예측 keypoint 튜플
        ground_truth: 라벨 keypoint 튜플
        distance_threshold: 정규화 좌표 거리 임계 (디폴트 0.05 = 손바닥 5%)

    Returns:
        PCK 점수 (0.0~1.0)
    """
    if not ground_truth:
        return 0.0
    matched = 0
    for gt in ground_truth:
        for pr in predicted:
            dist = ((pr.x - gt.x) ** 2 + (pr.y - gt.y) ** 2) ** 0.5
            if dist <= distance_threshold:
                matched += 1
                break
    return matched / len(ground_truth)


def compute_line_metric_mae(
    predicted: PalmLineMetric,
    ground_truth: PalmLineMetric,
) -> dict[str, float]:
    """선 메트릭 평균 절대 오차 (MAE) — 학습 평가용.

    Returns:
        {"length_mae": float, "thickness_mae": float, "clarity_mae": float}
    """
    return {
        "length_mae": abs(predicted.length_ratio - ground_truth.length_ratio),
        "thickness_mae": abs(predicted.thickness_norm - ground_truth.thickness_norm),
        "clarity_mae": abs(predicted.clarity_score - ground_truth.clarity_score),
    }


# ─────────────────────────── 학습 진입점 (사용자 결단 후만) ───────────────────────────


def train_palm_model(config: PalmTrainingConfig) -> None:
    """ML 학습 진입점 — 사용자 결단 (#2 외부 영역) 후 호출.

    Raises:
        NotImplementedError: 데이터셋 fair use 동의 부재 또는 실 데이터 부재 시.

    Note:
        본 함수는 의도적 미구현. 사용자가 다음 조건 충족 후 실 구현:
          1. 11k Hands 학술 fair use 명시 동의 (config.fair_use_acknowledged=True)
          2. config.dataset_root 경로에 실 데이터 다운로드
          3. 라벨링 (4 손금선 keypoint + 메트릭)
          4. PyTorch/TensorFlow 모델 정의 + 학습 루프 구현
    """
    if not config.fair_use_acknowledged:
        raise NotImplementedError(
            "ADR-154 — palm ML 학습은 사용자 결단 영역. "
            "11k Hands 데이터셋 학술 fair use 동의 (config.fair_use_acknowledged=True) 필요. "
            "결단 자료: vault/decisions/ADR-150-external-decisions-support-brief.md"
        )
    raise NotImplementedError(
        "ADR-154 — palm ML 학습 본 구현은 사용자 결단 후 별건. "
        "본 모듈은 인터페이스 + 평가 메트릭만 영속."
    )


__all__ = [
    "PalmKeypoint", "PalmLineMetric", "PalmTrainingConfig", "PalmModel",
    "compute_keypoint_iou", "compute_line_metric_mae",
    "train_palm_model",
]
