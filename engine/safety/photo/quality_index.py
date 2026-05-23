"""ADR-210 - face image 5-factor quality index.

학술 근거 (Scientific Programming 2021):
  - sharpness, brightness, contrast, illumination, focus 5 factor 합성 quality index
  - https://www.hindawi.com/journals/sp/2021/4606828/

본 시스템 적용:
  - MediaPipe 좌표 추출 정확도 ↑ 위해 입력 사진 조기 검증 강화
  - 기존 engine/safety/photo/quality.py (blur/brightness/resolution) 보완
  - 5 factor 0~1 정규화 + 가중 합 → quality_index ∈ [0, 1]

ADR 정합:
  - ADR-053 사진 품질 게이트 (기존 — 본 ADR이 5 factor로 확장)
  - ADR-006 의료 진단 X (사진 품질 지표만)
  - ADR-010 사실성 분리 (학술 가중치 출처 명시)
"""

from __future__ import annotations

from dataclasses import dataclass


# 학술 출처 (Scientific Programming 2021)
SOURCE_URL = "https://www.hindawi.com/journals/sp/2021/4606828/"


# 5 factor 가중치 (Scientific Programming 2021 § Methodology — recognition oriented)
_WEIGHTS = {
    "sharpness": 0.30,
    "brightness": 0.20,
    "contrast": 0.20,
    "illumination": 0.20,
    "focus": 0.10,
}


# 합격 임계 (운영표준 §5.1 + 학술 기반 보수적)
QUALITY_GOOD_THRESHOLD = 0.70
QUALITY_WARN_THRESHOLD = 0.50


@dataclass(frozen=True)
class QualityIndexResult:
    """5 factor 합성 quality index 결과."""
    quality_index: float          # 0~1
    sharpness: float
    brightness: float
    contrast: float
    illumination: float
    focus: float
    verdict: str                  # "good" / "warn" / "bad"
    user_message: str             # 한국어 권고
    source_url: str = SOURCE_URL


def _clip01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def compute_quality_index(
    sharpness: float | None = None,
    brightness: float | None = None,
    contrast: float | None = None,
    illumination: float | None = None,
    focus: float | None = None,
) -> QualityIndexResult:
    """5 factor → quality index.

    Args:
        모든 인자는 0~1 정규화된 값. None이면 0.5 폴백 (중립).
        sharpness: Laplacian variance / max_lv (호출자 정규화)
        brightness: mean intensity / 255 (0.4~0.85 ideal)
        contrast: stddev / 128 (clamp)
        illumination: 균일도 (1 - shadow variance) — 1.0이 가장 균일
        focus: edge sharpness 추가 지표

    Returns:
        QualityIndexResult — verdict + 한국어 메시지.
    """
    s = _clip01(0.5 if sharpness is None else sharpness)
    b = _clip01(0.5 if brightness is None else brightness)
    c = _clip01(0.5 if contrast is None else contrast)
    i = _clip01(0.5 if illumination is None else illumination)
    f = _clip01(0.5 if focus is None else focus)

    qi = (s * _WEIGHTS["sharpness"]
          + b * _WEIGHTS["brightness"]
          + c * _WEIGHTS["contrast"]
          + i * _WEIGHTS["illumination"]
          + f * _WEIGHTS["focus"])
    qi = round(qi, 4)

    if qi >= QUALITY_GOOD_THRESHOLD:
        verdict = "good"
        msg = "사진 품질이 좋습니다."
    elif qi >= QUALITY_WARN_THRESHOLD:
        verdict = "warn"
        # 가장 낮은 factor 지목
        factors = {
            "sharpness": s, "brightness": b, "contrast": c,
            "illumination": i, "focus": f,
        }
        weakest = min(factors, key=lambda k: factors[k])
        label_ko = {
            "sharpness": "선명도",
            "brightness": "밝기",
            "contrast": "명암",
            "illumination": "조명 균일도",
            "focus": "초점",
        }.get(weakest, weakest)
        msg = f"사진 {label_ko}가 낮습니다. 더 좋은 사진이면 분석 정확도가 올라갑니다."
    else:
        verdict = "bad"
        msg = "사진 품질이 낮습니다. 밝고 선명한 정면 사진으로 다시 촬영해 주십시오."

    return QualityIndexResult(
        quality_index=qi,
        sharpness=round(s, 4), brightness=round(b, 4), contrast=round(c, 4),
        illumination=round(i, 4), focus=round(f, 4),
        verdict=verdict, user_message=msg,
    )
