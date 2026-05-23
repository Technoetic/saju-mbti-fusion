"""ADR-235 - 11k Hands 데이터셋 자동 다운로드 + palmar 필터링.

학술 출처:
  - 11k Hands Dataset (sites.google.com/view/11khands)
  - Mahmoud Afifi 2019, IEEE Trans. Image Processing
  - 11,076장 실 손바닥/손등 사진 (190명, 18-75세, 1600x1200)
  - 라이선스: FREE for reasonable academic fair use

본 시스템 활용:
  - palmar 사진(5,396장)만 필터링 → 학습 데이터
  - 합성 데이터 한계 회복 (실 사진 분포 학습)
  - F1 학술 검증 수준 도달

ADR 정합:
  - ADR-225 dataset_pipeline 5번째 갈래
  - ADR-220 self-training (실 사진 + Gabor 약지도)
  - ADR-006 학파 명칭 X
"""

from __future__ import annotations

import csv
import os
import shutil
import zipfile
from dataclasses import dataclass


SOURCE_URL = "https://sites.google.com/view/11khands"
IMAGES_GDRIVE_ID = "1KcMYcNJgtK1zZvfl_9sTqnyBUTri2aP2"
METADATA_GDRIVE_ID = "1RC86-rVOR8c93XAfM9b9R45L7C2B0FdA"


@dataclass(frozen=True)
class Download11kResult:
    n_total: int
    n_palmar: int
    palmar_dir: str
    metadata_csv: str
    license_notice: str = (
        "11k Hands Dataset — FREE for reasonable academic fair use. "
        "본 시스템은 학술적 손금 선 검출 모델 학습 목적 사용. "
        "운명·길흉 매핑 X (ADR-006)."
    )


def download_11k_hands(
    output_dir: str,
    extract: bool = True,
) -> Download11kResult:
    """11k Hands 데이터셋 자동 다운로드 + palmar 필터링.

    Args:
        output_dir: 다운로드 + 압축 풀기 디렉토리 (e.g. /d/palm_dataset/).
        extract: ZIP 압축 해제 여부.

    Returns:
        Download11kResult — palmar 사진 폴더 + 메타데이터 경로.
    """
    try:
        import gdown
    except ImportError:
        # gdown 부재 — pip install로 자동 설치 시도
        import subprocess
        try:
            subprocess.run(
                ["pip", "install", "--quiet", "gdown"],
                check=True, timeout=120,
            )
            import gdown  # type: ignore[no-redef]
        except Exception:
            return Download11kResult(
                n_total=0, n_palmar=0, palmar_dir="",
                metadata_csv="",
                license_notice="gdown 설치 실패 — 수동 다운로드 필요.",
            )

    os.makedirs(output_dir, exist_ok=True)
    zip_path = os.path.join(output_dir, "11k_hands.zip")
    csv_path = os.path.join(output_dir, "HandInfo.csv")
    hands_dir = os.path.join(output_dir, "11k_hands", "Hands")
    palmar_dir = os.path.join(output_dir, "palmar_only")

    # 1. 이미지 ZIP 다운로드 (이미 있으면 스킵)
    if not os.path.exists(zip_path):
        gdown.download(id=IMAGES_GDRIVE_ID, output=zip_path, quiet=True)

    # 2. 메타데이터 CSV 다운로드
    if not os.path.exists(csv_path):
        gdown.download(id=METADATA_GDRIVE_ID, output=csv_path, quiet=True)

    # 3. 압축 해제
    if extract and not os.path.exists(hands_dir):
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(os.path.join(output_dir, "11k_hands"))

    # 4. palmar 필터링
    os.makedirs(palmar_dir, exist_ok=True)
    n_palmar = 0
    n_total = 0
    if os.path.exists(csv_path) and os.path.exists(hands_dir):
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                n_total += 1
                aspect = row.get("aspectOfHand", "").lower()
                if "palmar" in aspect:
                    img_name = row.get("imageName", "")
                    src = os.path.join(hands_dir, img_name)
                    dst = os.path.join(palmar_dir, img_name)
                    if os.path.exists(src) and not os.path.exists(dst):
                        try:
                            shutil.copy(src, dst)
                            n_palmar += 1
                        except Exception:
                            continue
                    elif os.path.exists(dst):
                        n_palmar += 1

    return Download11kResult(
        n_total=n_total,
        n_palmar=n_palmar,
        palmar_dir=palmar_dir,
        metadata_csv=csv_path,
    )


def main():
    import argparse
    parser = argparse.ArgumentParser(description="11k Hands 다운로드 + palmar 필터링")
    parser.add_argument("--output-dir", default="data/palm/11k_dataset/",
                        help="다운로드 디렉토리 (기본 data/palm/11k_dataset/)")
    parser.add_argument("--no-extract", action="store_true",
                        help="ZIP 압축 해제 스킵")
    args = parser.parse_args()
    r = download_11k_hands(output_dir=args.output_dir, extract=not args.no_extract)
    print(f"n_total: {r.n_total}")
    print(f"n_palmar: {r.n_palmar}")
    print(f"palmar_dir: {r.palmar_dir}")
    print(f"license: {r.license_notice}")


if __name__ == "__main__":
    main()
