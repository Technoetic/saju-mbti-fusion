"""ADR-199 - 조명 정규화 (sclera 기준 백색 균형).

ADR-178 한계 절 명시: "사진 조명 정규화 부재 — 백색 균형·sclera 보정 ADR 별도"

원리:
  - sclera(흰자)는 인종·연령·성별 무관 흰색 표준 (D65 illuminant 1.0/1.0/1.0)
  - 사용자 사진의 sclera RGB가 (240, 240, 240) 같이 측정되면 조명이 약함
  - 모든 ROI RGB를 sclera 기준으로 정규화 → 한국인 베이스라인 비교 정확도 ↑

활용:
  - face/complexion.py 입력 전 ROI RGB 보정
  - 사진 조명 변동성 흡수 → ADR-178 ROI 비교 정확도 향상

ADR 정합:
  - ADR-178 (complexion 베이스라인 — 정규화 전제로 신뢰도 향상)
  - ADR-010 사실성 분리 (정규화 수학 명시)
  - ADR-006 (의료 진단 아님 — 색공간 보정만)
"""

from __future__ import annotations

from dataclasses import dataclass


# sclera 흰색 표준 (D65 illuminant 가정)
_SCLERA_REFERENCE_RGB: tuple[float, float, float] = (245.0, 245.0, 245.0)
# 240보다 약간 높게 — 실 sclera는 완전 흰색이 아닌 매우 밝은 회백색

# 정규화 게인 안전 범위 (극단 보정 차단)
_GAIN_MIN = 0.7
_GAIN_MAX = 1.5


@dataclass(frozen=True)
class LightingNormalizationResult:
    """조명 정규화 결과."""
    gain_r: float       # 적색 채널 게인
    gain_g: float       # 녹색 채널 게인
    gain_b: float       # 청색 채널 게인
    confidence: str     # "high" / "medium" / "low" — sclera 측정 신뢰도
    sclera_rgb_input: tuple[float, float, float]
    sclera_rgb_target: tuple[float, float, float] = _SCLERA_REFERENCE_RGB


def compute_lighting_gains(
    sclera_rgb: tuple[float, float, float] | None,
) -> LightingNormalizationResult:
    """사용자 sclera RGB → 채널별 게인 산출.

    Args:
        sclera_rgb: (r, g, b) — 사용자 사진의 sclera 평균 RGB.
            None이면 게인 1.0 (정규화 면제).

    Returns:
        LightingNormalizationResult — 각 채널 곱셈 게인 + 신뢰도.
            확신도 낮으면 안전 범위 클램프.
    """
    if sclera_rgb is None or not isinstance(sclera_rgb, (tuple, list)):
        return LightingNormalizationResult(
            gain_r=1.0, gain_g=1.0, gain_b=1.0,
            confidence="low", sclera_rgb_input=(0.0, 0.0, 0.0),
        )
    if len(sclera_rgb) < 3:
        return LightingNormalizationResult(
            gain_r=1.0, gain_g=1.0, gain_b=1.0,
            confidence="low", sclera_rgb_input=(0.0, 0.0, 0.0),
        )

    r_in, g_in, b_in = float(sclera_rgb[0]), float(sclera_rgb[1]), float(sclera_rgb[2])

    # 너무 어둡거나 너무 밝으면 신뢰도 ↓ (sclera 추출 실패 가능성)
    avg = (r_in + g_in + b_in) / 3
    if avg < 100 or avg > 254:
        confidence = "low"
    elif 180 <= avg <= 250:
        confidence = "high"
    else:
        confidence = "medium"

    # 게인 산출 — target / input (0으로 나누기 차단)
    r_tgt, g_tgt, b_tgt = _SCLERA_REFERENCE_RGB
    gain_r = r_tgt / max(r_in, 1.0)
    gain_g = g_tgt / max(g_in, 1.0)
    gain_b = b_tgt / max(b_in, 1.0)

    # 안전 범위 클램프 (극단 보정 차단)
    gain_r = max(_GAIN_MIN, min(_GAIN_MAX, gain_r))
    gain_g = max(_GAIN_MIN, min(_GAIN_MAX, gain_g))
    gain_b = max(_GAIN_MIN, min(_GAIN_MAX, gain_b))

    return LightingNormalizationResult(
        gain_r=round(gain_r, 4),
        gain_g=round(gain_g, 4),
        gain_b=round(gain_b, 4),
        confidence=confidence,
        sclera_rgb_input=(round(r_in, 1), round(g_in, 1), round(b_in, 1)),
    )


def apply_gains_to_rgb(
    rgb: tuple[float, float, float],
    gains: LightingNormalizationResult,
) -> tuple[float, float, float]:
    """단일 ROI RGB에 정규화 게인 적용.

    Args:
        rgb: ROI 평균 RGB.
        gains: compute_lighting_gains() 결과.

    Returns:
        정규화 RGB (0~255 clamp).
    """
    if not isinstance(rgb, (tuple, list)) or len(rgb) < 3:
        return (0.0, 0.0, 0.0)
    r = max(0.0, min(255.0, float(rgb[0]) * gains.gain_r))
    g = max(0.0, min(255.0, float(rgb[1]) * gains.gain_g))
    b = max(0.0, min(255.0, float(rgb[2]) * gains.gain_b))
    return (round(r, 2), round(g, 2), round(b, 2))


def normalize_roi_rgb(
    roi_rgb: dict[str, tuple[float, float, float]],
    sclera_rgb: tuple[float, float, float] | None,
) -> tuple[dict[str, tuple[float, float, float]], LightingNormalizationResult]:
    """ROI RGB dict 전체 정규화.

    Args:
        roi_rgb: {roi_key: (r, g, b)}.
        sclera_rgb: sclera 평균 RGB (None이면 정규화 면제).

    Returns:
        (정규화 ROI dict, 게인 결과). face/complexion.py 입력으로 사용 가능.
    """
    gains = compute_lighting_gains(sclera_rgb)
    if gains.confidence == "low" or sclera_rgb is None:
        # sclera 신뢰도 낮으면 원본 그대로 (안전 우선)
        return roi_rgb, gains
    normalized = {k: apply_gains_to_rgb(v, gains) for k, v in roi_rgb.items()}
    return normalized, gains
