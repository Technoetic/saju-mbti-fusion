"""ADR-211 - 피지·광택 정량 분석 (의료 인과 X).

학술 근거:
  - Springer 2020 (DOI 10.1007/s00403-020-02070-5) 차등 편광 이미지 기반 정량
  - https://kao.com/global/en/research-development/...quantifying-shiny-skin
  - Laplacian Gaussian edge 기반 광택 영역 검출

ADR-006 의료 진단 X — 화장품 평가 학술 영역. 본 시스템:
  - 광택(shine) 정량: 사진 RGB → 고휘도 픽셀 비율
  - 피지 색인(sebum index): 면색 부위별 광택 평균
  - 운명·체질·의료 매핑 X

ADR 정합:
  - ADR-178 (complexion 베이스라인과 보완)
  - ADR-006 (의료 인과 부재)
  - ADR-010 (학술 출처 명시)
"""

from __future__ import annotations

from dataclasses import dataclass


SOURCE_URL = "https://link.springer.com/article/10.1007/s00403-020-02070-5"


# 광택 검출 임계 (Springer 2020 § Methods 보수적 적용)
_SHINE_LUMINANCE_THRESHOLD = 220   # RGB 평균 > 220 = 광택 후보
_SHINE_PCT_THRESHOLDS = {
    "low": 0.02,      # < 2% = 매트
    "moderate": 0.10, # 2~10% = 보통
    # > 10% = 광택 ↑
}


@dataclass(frozen=True)
class SebumShineResult:
    """피지·광택 분석 결과."""
    shine_pct: float          # 0~1 (광택 픽셀 비율)
    shine_level: str          # "matte" / "moderate" / "shiny"
    label_ko: str             # 사극풍 라벨
    description_ko: str
    source_url: str = SOURCE_URL
    disclaimer: str = (
        "본 광택 측정은 사진 RGB 분석이며 의료 진단·체질 분류·운명 매핑이 "
        "아닙니다. 화장품·조명에 따라 변동성이 있습니다."
    )


def compute_shine_pct(
    pixels_rgb: list[tuple[float, float, float]],
) -> float:
    """픽셀 RGB 리스트 → 광택 픽셀 비율.

    Args:
        pixels_rgb: ROI 픽셀의 (r, g, b) 리스트.

    Returns:
        광택 픽셀 비율 0~1. 빈 리스트는 0.
    """
    if not pixels_rgb:
        return 0.0
    n_shine = 0
    n_total = 0
    for px in pixels_rgb:
        if not isinstance(px, (tuple, list)) or len(px) < 3:
            continue
        r, g, b = float(px[0]), float(px[1]), float(px[2])
        avg = (r + g + b) / 3.0
        if avg > _SHINE_LUMINANCE_THRESHOLD:
            n_shine += 1
        n_total += 1
    if n_total == 0:
        return 0.0
    return n_shine / n_total


def analyze_sebum_shine(shine_pct: float) -> SebumShineResult:
    """광택 비율 → SebumShineResult."""
    pct = max(0.0, min(1.0, float(shine_pct)))
    if pct < _SHINE_PCT_THRESHOLDS["low"]:
        level = "matte"
        label_ko = "결이 매끈하다"
        desc = "광택이 거의 없는 매트한 결입니다."
    elif pct < _SHINE_PCT_THRESHOLDS["moderate"]:
        level = "moderate"
        label_ko = "결이 고르다"
        desc = "광택이 적당히 어우러진 고른 결입니다."
    else:
        level = "shiny"
        label_ko = "결이 윤기롭다"
        desc = "광택이 두드러진 윤기 있는 결입니다."
    return SebumShineResult(
        shine_pct=round(pct, 4),
        shine_level=level,
        label_ko=label_ko,
        description_ko=desc,
    )
