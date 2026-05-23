"""ADR-178 - 한국인 얼굴 L*a*b* 화장품 베이스라인 결정론 분석.

ADR-162에서 사상의학 PMC 자료(Cold/Heat 처방군 매핑)는 ADR-006 의료 인과
위반으로 본문화 거절. 본 모듈은 그와 독립으로 화장품 베이스라인 출처
(Biomedical Dermatology 2017, N=543; ResearchGate 2017, N=157)를 본문화.

핵심 차이:
  - ADR-162 거절 자료: 사상체질 + 약물 처방 매핑 = 의료 인과
  - 본 ADR-178 자료: 화장품 base makeup reference = 의료 인과 부재

목적:
  - 사용자 사진의 얼굴 ROI L*a*b* 산출
  - 한국인 평균 베이스라인 대비 z-score 묘사
  - 사극풍 색 라벨 ("환하다/고르다/은은하다/옅다")

ADR 정합:
  - ADR-010 사실성 분리: Springer 검증 출처 사용
  - ADR-006 자문 거절: 의료 인과 매핑 X (장기 단정 sanitize 7중)
  - ADR-159: face MediaPipe Phase 1.5 호환
  - ADR-171: 운명 단정 어휘 사전 차단
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import math


# ───── 한국인 평균 베이스라인 (Biomedical Dermatology 2017, N=543) ─────
# 출처:
#   - https://link.springer.com/article/10.1186/s41702-017-0002-7 (N=543 화장품)
#   - https://pmc.ncbi.nlm.nih.gov/articles/PMC9907718/ (N=595, ADR-193 보강)
# ADR-193: PMC 9907718 한국인 N=595 (평균 24.2세±2.36) skin clustering 자료
#   추가 검증 — L*a*b* (60.66 dark / 63.87 normal / 66.66 bright) tone 군집
#   본 베이스라인 L=64.5 (forehead) 등은 normal~bright 군집과 정합.
# 본 베이스라인은 보수적 디폴트 — 운영 데이터 누적 후 정밀화 가능.

_KOREAN_FACIAL_LAB_BASELINE: dict[str, dict[str, float]] = {
    "forehead": {"L": 64.5, "a": 12.5, "b": 16.2},
    "nose_tip": {"L": 60.2, "a": 14.8, "b": 17.5},
    "chin": {"L": 62.8, "a": 12.0, "b": 16.0},
    "cheekbone": {"L": 63.0, "a": 13.5, "b": 16.8},
    "cheek": {"L": 64.0, "a": 12.8, "b": 16.3},
    "jaw": {"L": 62.5, "a": 11.8, "b": 15.8},
    "neck": {"L": 65.0, "a": 11.0, "b": 15.0},
    "nose_bridge": {"L": 61.5, "a": 13.8, "b": 17.0},
}

_BASELINE_STD: dict[str, float] = {"L": 3.5, "a": 2.0, "b": 2.5}


# ADR-006 sanitize - 의료 인과 어휘 차단
_FORBIDDEN_MEDICAL_TERMS = (
    "심장", "신장", "간장", "비장", "폐장",
    "심허", "간허", "신허", "비허", "폐허",
    "사상체질", "태양인", "태음인", "소양인", "소음인",
    "음허", "양허", "기허", "혈허",
    "한증", "열증", "허증", "실증",
    "황달", "빈혈", "혈압", "당뇨",
)


SOURCE_URL = "https://link.springer.com/article/10.1186/s41702-017-0002-7"
SOURCE_URL_CLUSTERING = "https://pmc.ncbi.nlm.nih.gov/articles/PMC9907718/"
# ADR-193: 한국인 N=595 skin clustering tone 군집 (24.2세±2.36)
KOREAN_TONE_CLUSTERS: dict[str, float] = {
    "dark": 60.66,    # L* mean
    "normal": 63.87,
    "bright": 66.66,
}
DISCLAIMER = (
    "본 색상 분석은 한국인 화장품 베이스라인(Biomedical Dermatology 2017, "
    "N=543) + skin clustering(Skin Research and Technology 2022, N=595) 대비 "
    "정량 측정 결과이며, 의료 진단·체질 분류·운명 매핑이 아닙니다. "
    "사진 조명에 따라 변동성이 큽니다. 본 베이스라인은 여성 표본 위주로 "
    "남성 사용자는 변동성이 더 클 수 있습니다(ADR-193 한계)."
)


@dataclass(frozen=True)
class FacialColorResult:
    """단일 ROI의 L*a*b* 분석 결과."""
    roi_key: str
    L: float
    a: float
    b: float
    L_zscore: float
    a_zscore: float
    b_zscore: float
    label_short: str  # "환하다/고르다/은은하다/옅다"
    source_url: str = SOURCE_URL


@dataclass(frozen=True)
class ComplexionReport:
    """전체 면색 분석 리포트."""
    rois: dict[str, FacialColorResult]
    overall_L_mean: float
    overall_uniformity: float  # 부위간 L 표준편차 (낮을수록 균일)
    disclaimer: str = DISCLAIMER
    metrics_used: list[str] = field(default_factory=list)


# ───── RGB → L*a*b* 변환 (numpy 의존성 X, 순수 수학) ─────

def _srgb_to_linear(c: float) -> float:
    """sRGB [0,1] -> linear RGB."""
    c = c / 255.0 if c > 1.0 else c
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def _f_lab(t: float) -> float:
    """CIE L*a*b* helper function."""
    delta = 6.0 / 29.0
    if t > delta ** 3:
        return t ** (1.0 / 3.0)
    return t / (3.0 * delta ** 2) + 4.0 / 29.0


def rgb_to_lab(r: float, g: float, b: float) -> tuple[float, float, float]:
    """sRGB (0-255 or 0-1) -> CIE L*a*b* (D65 illuminant).

    출처: https://en.wikipedia.org/wiki/CIELAB_color_space
    """
    r_lin = _srgb_to_linear(r)
    g_lin = _srgb_to_linear(g)
    b_lin = _srgb_to_linear(b)

    # sRGB -> XYZ (D65)
    X = 0.4124564 * r_lin + 0.3575761 * g_lin + 0.1804375 * b_lin
    Y = 0.2126729 * r_lin + 0.7151522 * g_lin + 0.0721750 * b_lin
    Z = 0.0193339 * r_lin + 0.1191920 * g_lin + 0.9503041 * b_lin

    # D65 reference white
    Xn, Yn, Zn = 0.95047, 1.00000, 1.08883

    fx = _f_lab(X / Xn)
    fy = _f_lab(Y / Yn)
    fz = _f_lab(Z / Zn)

    L = 116.0 * fy - 16.0
    a_val = 500.0 * (fx - fy)
    b_val = 200.0 * (fy - fz)
    return L, a_val, b_val


# ───── ROI 평균 RGB 산출 (입력은 dict 형식) ─────

def compute_facial_color(
    roi_rgb: dict[str, tuple[float, float, float]],
) -> ComplexionReport:
    """8 ROI 평균 RGB → L*a*b* 분석 + 한국인 베이스라인 z-score.

    Args:
        roi_rgb: {roi_key: (r, g, b)} - 사용자 사진 ROI 평균 RGB.
            roi_key는 _KOREAN_FACIAL_LAB_BASELINE 키 (forehead/nose_tip/
            chin/cheekbone/cheek/jaw/neck/nose_bridge).

    Returns:
        ComplexionReport with per-ROI z-scores + overall uniformity.
    """
    rois: dict[str, FacialColorResult] = {}
    L_values: list[float] = []
    metrics_used: list[str] = []

    for roi_key, rgb in roi_rgb.items():
        if roi_key not in _KOREAN_FACIAL_LAB_BASELINE:
            continue
        if not isinstance(rgb, (tuple, list)) or len(rgb) < 3:
            continue
        r, g, b = float(rgb[0]), float(rgb[1]), float(rgb[2])
        L, a_val, b_val = rgb_to_lab(r, g, b)

        baseline = _KOREAN_FACIAL_LAB_BASELINE[roi_key]
        L_z = (L - baseline["L"]) / _BASELINE_STD["L"]
        a_z = (a_val - baseline["a"]) / _BASELINE_STD["a"]
        b_z = (b_val - baseline["b"]) / _BASELINE_STD["b"]

        label = _label_from_lightness(L_z)

        rois[roi_key] = FacialColorResult(
            roi_key=roi_key,
            L=round(L, 2),
            a=round(a_val, 2),
            b=round(b_val, 2),
            L_zscore=round(L_z, 3),
            a_zscore=round(a_z, 3),
            b_zscore=round(b_z, 3),
            label_short=label,
        )
        L_values.append(L)
        metrics_used.append(roi_key)

    overall_L = sum(L_values) / len(L_values) if L_values else 0.0
    if len(L_values) > 1:
        var = sum((x - overall_L) ** 2 for x in L_values) / len(L_values)
        uniformity = math.sqrt(var)  # 표준편차 (낮을수록 균일)
    else:
        uniformity = 0.0

    return ComplexionReport(
        rois=rois,
        overall_L_mean=round(overall_L, 2),
        overall_uniformity=round(uniformity, 2),
        metrics_used=metrics_used,
    )


def _label_from_lightness(L_z: float) -> str:
    """L* z-score → 사극풍 색 라벨.

    +1.0 이상 → "환하다" (한국인 평균 대비 밝음)
    +0.3 ~ +1.0 → "고르다"
    -0.3 ~ +0.3 → "은은하다"
    -0.3 미만 → "옅다" (어둠)
    """
    if L_z >= 1.0:
        return "환하다"
    if L_z >= 0.3:
        return "고르다"
    if L_z >= -0.3:
        return "은은하다"
    return "옅다"


# ───── ADR-006 sanitize ─────

def sanitize_complexion_text(text: str) -> tuple[bool, list[str]]:
    """면색 풀이 텍스트에서 의료 인과 어휘 검출.

    Returns:
        (안전 여부, 검출된 차단 어휘 리스트)
    """
    if not text:
        return True, []
    matched: list[str] = []
    for term in _FORBIDDEN_MEDICAL_TERMS:
        if term in text:
            matched.append(term)
    return (len(matched) == 0, matched)


def classify_tone(L_mean: float) -> str:
    """ADR-193 — 전체 얼굴 평균 L* → 한국인 skin tone 군집 라벨.

    PMC 9907718 N=595 군집:
      L* < 62.27 (dark/normal 경계) → "어둡다"
      62.27 ≤ L* < 65.27 (normal/bright 경계) → "보통"
      L* ≥ 65.27 → "환하다"

    경계값은 각 군집 평균의 중점.
    """
    if L_mean < 62.27:
        return "어둡다"
    if L_mean < 65.27:
        return "보통"
    return "환하다"


def report_to_dict(report: ComplexionReport) -> dict[str, Any]:
    """ComplexionReport → JSON 직렬화 dict."""
    return {
        "rois": {
            k: {
                "roi_key": v.roi_key,
                "L": v.L, "a": v.a, "b": v.b,
                "L_zscore": v.L_zscore,
                "a_zscore": v.a_zscore,
                "b_zscore": v.b_zscore,
                "label_short": v.label_short,
            }
            for k, v in report.rois.items()
        },
        "overall_L_mean": report.overall_L_mean,
        "overall_uniformity": report.overall_uniformity,
        "overall_tone": classify_tone(report.overall_L_mean),  # ADR-193
        "disclaimer": report.disclaimer,
        "metrics_used": list(report.metrics_used),
        "source_url": SOURCE_URL,
        "source_url_clustering": SOURCE_URL_CLUSTERING,  # ADR-193
    }
