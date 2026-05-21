"""캐릭터 비디오 7장 첫 프레임을 JPG poster로 추출.

본 시스템 카드 갤러리 (card-gallery.js)에서 비디오가 디코드되기 전
빈 패널이 보이는 UX 버그 해결. video element에 poster 속성으로 첫 프레임
정지 이미지를 지정하면 비디오 로드/디코드 전에도 첫 프레임 표시.

성하 공자(star)는 비디오 없음 (별빛 배경 + 텍스트만) — skip.

사용법:
    python scripts/extract_character_posters.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = ROOT / "front" / "media" / "characters"

CHARACTER_VIDEOS = [
    ("manweol_assi", "만월 아씨"),
    ("mongi_doryeong", "몽이 도령"),
    ("hwaseon_nangja", "화선 낭자"),
    ("unhak_dosa", "운학 도사"),
    ("okseon_halmi", "옥선 할미"),
    ("mukhyang_seonsaeng", "묵향 선생"),
]


def get_ffmpeg() -> str:
    """imageio-ffmpeg 번들 ffmpeg 경로."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        # 시스템 ffmpeg fallback
        ff = shutil.which("ffmpeg")
        if ff:
            return ff
        sys.stderr.write(
            "ffmpeg 부재. 설치:\n"
            "  python -m pip install imageio-ffmpeg\n"
        )
        sys.exit(1)


def extract_first_frame(ffmpeg: str, mp4_path: Path, jpg_path: Path) -> bool:
    """비디오 첫 프레임을 JPG로 추출."""
    if not mp4_path.exists():
        print(f"  ⚠ {mp4_path.name} 부재 → skip")
        return False
    cmd = [
        ffmpeg,
        "-y",
        "-loglevel", "error",
        "-i", str(mp4_path),
        "-vframes", "1",
        "-q:v", "3",  # 품질 (1=최고~31=최저)
        str(jpg_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ✗ {mp4_path.name} 실패: {result.stderr.strip()}")
        return False
    return True


def main() -> None:
    ffmpeg = get_ffmpeg()
    print(f"ffmpeg: {ffmpeg}")
    print(f"media_dir: {MEDIA_DIR}")
    print()

    success = 0
    for key, name in CHARACTER_VIDEOS:
        mp4 = MEDIA_DIR / f"{key}.mp4"
        jpg = MEDIA_DIR / f"{key}.jpg"
        ok = extract_first_frame(ffmpeg, mp4, jpg)
        if ok:
            size_kb = jpg.stat().st_size / 1024
            print(f"  ✅ {name} → {jpg.name} ({size_kb:.1f} KB)")
            success += 1
        else:
            print(f"  ✗ {name}")
    print(f"\n총 {success}/{len(CHARACTER_VIDEOS)} 추출 완료")


if __name__ == "__main__":
    main()
