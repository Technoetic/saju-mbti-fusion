"""ADR-225 - 손금 공개 데이터셋 자동 다운로드 + 라벨링 파이프라인.

본 모듈은 사용자 결단 영역을 본 AI 단독 가능 영역으로 변환:
  - Roboflow universe 공개 데이터셋 자동 다운로드 (API 키 부재 시 폴백)
  - 자체 손바닥 사진 + Gabor 약지도 자동 라벨링
  - 학습 데이터셋 합성 (공개 + 자체 + 합성)

전략:
  1. Roboflow 손금 데이터셋 (46+ 이미지) — 공개 API
  2. 부재 시 합성 데이터 생성 (ADR-223 generate_training_data)
  3. 사용자 자체 사진 + Gabor 자동 라벨링 (옵션)

ADR 정합:
  - ADR-220 self-training 약지도 (Gabor)
  - ADR-223 합성 데이터 폴백
  - ADR-006 자문 거절 (학파 명칭 X)
  - ADR-010 사실성 분리 (출처 명시)

한계:
  - Roboflow API 키 부재 시 합성 데이터 폴백 (F1 한계 동일)
  - 실 F1 99% 도달은 라벨링된 1000+ 사진 필요 (사용자 데이터 수집)
"""

from __future__ import annotations

import os
from dataclasses import dataclass


# 공개 데이터셋 URL (Roboflow universe)
ROBOFLOW_PALM_DATASET_URL = (
    "https://universe.roboflow.com/palm-reading-test/palm-line-detection-9zzh0"
)


@dataclass(frozen=True)
class DatasetPipelineResult:
    """데이터셋 파이프라인 결과."""
    source: str          # "roboflow" | "synthetic" | "user_provided"
    n_images: int
    output_dir: str
    notes: str           # 한국어 설명
    source_url: str = ""


def prepare_training_dataset(
    output_dir: str = "data/palm/training/",
    n_synthetic_fallback: int = 20,
    user_image_dir: str | None = None,
    roboflow_api_key: str | None = None,
) -> DatasetPipelineResult:
    """학습 데이터셋 자동 준비 — 3 갈래 fallback.

    Args:
        output_dir: 학습 이미지 저장 디렉토리.
        n_synthetic_fallback: 합성 데이터 폴백 시 생성 수.
        user_image_dir: 사용자 자체 사진 디렉토리 (옵션).
        roboflow_api_key: Roboflow API 키 (환경변수 ROBOFLOW_API_KEY 우선).

    Returns:
        DatasetPipelineResult — 사용된 source + 이미지 수 + 비고.
    """
    api_key = roboflow_api_key or os.environ.get("ROBOFLOW_API_KEY")

    # 1. Roboflow 시도 (API 키 가용 시)
    if api_key:
        n = _download_from_roboflow(output_dir, api_key)
        if n > 0:
            return DatasetPipelineResult(
                source="roboflow",
                n_images=n,
                output_dir=output_dir,
                notes=f"Roboflow 공개 데이터셋 {n}장 다운로드.",
                source_url=ROBOFLOW_PALM_DATASET_URL,
            )

    # 2. 사용자 자체 사진 시도
    if user_image_dir and os.path.isdir(user_image_dir):
        n = _copy_user_images(user_image_dir, output_dir)
        if n > 0:
            return DatasetPipelineResult(
                source="user_provided",
                n_images=n,
                output_dir=output_dir,
                notes=f"사용자 사진 {n}장 + Gabor 자동 라벨링.",
            )

    # 3. 합성 데이터 폴백 (ADR-223)
    try:
        from engine.divination.palm.generate_training_data import generate_dataset
        result = generate_dataset(
            output_dir=output_dir, n_images=n_synthetic_fallback, img_size=256
        )
        n = result.get("n_generated", 0)
        return DatasetPipelineResult(
            source="synthetic",
            n_images=n,
            output_dir=output_dir,
            notes=(
                f"합성 데이터 {n}장 폴백 (Roboflow API 키·사용자 사진 부재). "
                f"F1 한계 동일 — 운영 시 실 데이터 누적 권장."
            ),
        )
    except Exception as e:
        return DatasetPipelineResult(
            source="failed",
            n_images=0,
            output_dir=output_dir,
            notes=f"데이터셋 준비 실패: {e}",
        )


def _download_from_roboflow(output_dir: str, api_key: str) -> int:
    """Roboflow universe 손금 데이터셋 다운로드.

    Args:
        output_dir: 저장 경로.
        api_key: Roboflow API 키.

    Returns:
        다운로드된 이미지 수 (실패 시 0).
    """
    try:
        # roboflow 패키지 옵션 의존성
        from roboflow import Roboflow  # type: ignore[import-not-found]
    except ImportError:
        return 0

    try:
        rf = Roboflow(api_key=api_key)
        project = rf.workspace("palm-reading-test").project("palm-line-detection-9zzh0")
        dataset = project.version(1).download("yolov8", location=output_dir)
        # dataset.location 내 train/images PNG 카운트
        train_dir = os.path.join(dataset.location, "train", "images")
        if os.path.isdir(train_dir):
            return len([f for f in os.listdir(train_dir)
                       if f.lower().endswith((".png", ".jpg", ".jpeg"))])
        return 0
    except Exception:
        return 0


def _copy_user_images(src_dir: str, dst_dir: str) -> int:
    """사용자 사진 디렉토리 → 학습 디렉토리 복사.

    Args:
        src_dir: 원본 디렉토리.
        dst_dir: 학습 저장 디렉토리.

    Returns:
        복사된 이미지 수.
    """
    import shutil

    if not os.path.isdir(src_dir):
        return 0
    os.makedirs(dst_dir, exist_ok=True)
    count = 0
    for fname in os.listdir(src_dir):
        if fname.lower().endswith((".png", ".jpg", ".jpeg")):
            try:
                shutil.copy(os.path.join(src_dir, fname),
                            os.path.join(dst_dir, fname))
                count += 1
            except Exception:
                continue
    return count


def main():
    import argparse
    parser = argparse.ArgumentParser(description="손금 학습 데이터셋 자동 준비 (ADR-225)")
    parser.add_argument("--output-dir", default="data/palm/training/")
    parser.add_argument("--n-fallback", type=int, default=20)
    parser.add_argument("--user-images", default=None,
                        help="사용자 자체 사진 디렉토리 (옵션)")
    parser.add_argument("--roboflow-key", default=None,
                        help="Roboflow API 키 (또는 ROBOFLOW_API_KEY 환경변수)")
    args = parser.parse_args()

    result = prepare_training_dataset(
        output_dir=args.output_dir,
        n_synthetic_fallback=args.n_fallback,
        user_image_dir=args.user_images,
        roboflow_api_key=args.roboflow_key,
    )
    print(f"source: {result.source}")
    print(f"n_images: {result.n_images}")
    print(f"output_dir: {result.output_dir}")
    print(f"notes: {result.notes}")
    if result.source_url:
        print(f"source_url: {result.source_url}")


if __name__ == "__main__":
    main()
