"""ADR-184 - 표정 잡음 검출 게이트.

MediaPipe Face Landmarker 52 blendshape 강도를 검사해 강한 표정이면
재촬영 권고. ADR-159 한계 절 명시 "무표정 정면 사진 의존" 부분 해소.

배경:
  - blendshape 0~1 강도 (무표정 ≈ 0, 최대 표정 = 1)
  - 강한 웃음·찡그림은 mouth_corner_lift·alar_ratio 측정 오염
  - 결정론 12궁 점수가 본질이 아닌 표정을 측정하는 것 차단

차단 임계 (BLOCK_THRESHOLD = 0.4):
  - 부위별 max blendshape > 0.4 → 차단 + 재촬영 권고
경고 임계 (WARN_THRESHOLD = 0.15):
  - 부위별 max blendshape > 0.15 → 경고만 (사용자 알림, 차단 X)

ADR 정합:
  - ADR-159 (face MediaPipe Phase 1.5) — "무표정 정면 사진 권장" 한계 회복
  - ADR-053 (사진 품질 게이트) — 동일 패턴 (Laplacian·brightness 등)
  - ADR-010 사실성 분리 — 잡음 사진은 본질 측정 X
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# 차단·경고 임계
BLOCK_THRESHOLD = 0.40   # 부위별 max blendshape > 0.40 → 차단
WARN_THRESHOLD = 0.15    # > 0.15 → 경고만


# 카테고리
EXPR_NOISE_NONE = ""
EXPR_NOISE_MOUTH = "expression_mouth"
EXPR_NOISE_EYE = "expression_eye"
EXPR_NOISE_BROW = "expression_brow"
EXPR_NOISE_JAW_CHEEK = "expression_jaw_cheek"
EXPR_NOISE_MULTIPLE = "expression_multiple"


# 부위별 blendshape 키 매핑 (MediaPipe Face Landmarker 52 blendshape 명칭)
_MOUTH_KEYS = (
    "mouthSmileLeft", "mouthSmileRight",
    "mouthFrownLeft", "mouthFrownRight",
    "mouthPucker", "mouthFunnel",
    "mouthShrugUpper", "mouthShrugLower",
    "mouthRollUpper", "mouthRollLower",
    # ADR-212 보강 — 입꼬리 좌우 비대칭 + 다물기 강도
    "mouthDimpleLeft", "mouthDimpleRight",
    "mouthStretchLeft", "mouthStretchRight",
    "mouthPressLeft", "mouthPressRight",
    "mouthClose",
)
_EYE_KEYS = (
    "eyeBlinkLeft", "eyeBlinkRight",
    "eyeWideLeft", "eyeWideRight",
    "eyeSquintLeft", "eyeSquintRight",
    # ADR-212 보강 — 시선 이탈
    "eyeLookInLeft", "eyeLookInRight",
    "eyeLookOutLeft", "eyeLookOutRight",
    "eyeLookUpLeft", "eyeLookUpRight",
    "eyeLookDownLeft", "eyeLookDownRight",
)
_BROW_KEYS = (
    "browInnerUp", "browOuterUpLeft", "browOuterUpRight",
    "browDownLeft", "browDownRight",
)
_JAW_CHEEK_KEYS = (
    "jawOpen", "jawForward", "jawLeft", "jawRight",
    "cheekPuff", "cheekSquintLeft", "cheekSquintRight",
)
# ADR-212 신규 5번째 카테고리 — 미세 표정 (코·콧방울·턱주름)
_NOSE_CHIN_KEYS = (
    "noseSneerLeft", "noseSneerRight",
)
EXPR_NOISE_NOSE_CHIN = "expression_nose_chin"


@dataclass(frozen=True)
class ExpressionNoiseResult:
    """표정 잡음 검출 결과."""
    blocked: bool
    warned: bool
    category: str  # EXPR_NOISE_* 식별자
    max_intensity: float
    user_message: str
    detail: dict[str, float] = field(default_factory=dict)


def _max_in(bs: dict[str, Any], keys: tuple[str, ...]) -> float:
    m = 0.0
    for k in keys:
        v = bs.get(k)
        if isinstance(v, (int, float)):
            if v > m:
                m = float(v)
    return m


def detect_expression_noise(
    blendshapes: dict[str, Any] | None,
) -> ExpressionNoiseResult:
    """blendshape dict → 표정 잡음 검출 결과.

    Args:
        blendshapes: MediaPipe Face Landmarker faceBlendshapes[0] 의 categoryName
            → score 매핑 dict. None/empty 면 검사 면제.

    Returns:
        ExpressionNoiseResult — blocked/warned + 카테고리 + 사용자 메시지.
    """
    if not blendshapes:
        return ExpressionNoiseResult(
            blocked=False, warned=False, category=EXPR_NOISE_NONE,
            max_intensity=0.0, user_message="",
        )

    mouth_max = _max_in(blendshapes, _MOUTH_KEYS)
    eye_max = _max_in(blendshapes, _EYE_KEYS)
    brow_max = _max_in(blendshapes, _BROW_KEYS)
    jaw_cheek_max = _max_in(blendshapes, _JAW_CHEEK_KEYS)
    nose_chin_max = _max_in(blendshapes, _NOSE_CHIN_KEYS)  # ADR-212

    detail = {
        "mouth_max": round(mouth_max, 3),
        "eye_max": round(eye_max, 3),
        "brow_max": round(brow_max, 3),
        "jaw_cheek_max": round(jaw_cheek_max, 3),
        "nose_chin_max": round(nose_chin_max, 3),  # ADR-212
    }
    overall_max = max(mouth_max, eye_max, brow_max, jaw_cheek_max, nose_chin_max)

    # 차단 카테고리 판정 — 여러 부위가 동시 BLOCK 초과면 MULTIPLE
    blocked_categories = []
    if mouth_max > BLOCK_THRESHOLD:
        blocked_categories.append(EXPR_NOISE_MOUTH)
    if eye_max > BLOCK_THRESHOLD:
        blocked_categories.append(EXPR_NOISE_EYE)
    if brow_max > BLOCK_THRESHOLD:
        blocked_categories.append(EXPR_NOISE_BROW)
    if jaw_cheek_max > BLOCK_THRESHOLD:
        blocked_categories.append(EXPR_NOISE_JAW_CHEEK)
    if nose_chin_max > BLOCK_THRESHOLD:  # ADR-212
        blocked_categories.append(EXPR_NOISE_NOSE_CHIN)

    if len(blocked_categories) >= 2:
        return ExpressionNoiseResult(
            blocked=True, warned=True,
            category=EXPR_NOISE_MULTIPLE,
            max_intensity=round(overall_max, 3),
            user_message=(
                "여러 부위 표정 강도가 높습니다. 무표정 정면 사진으로 다시 촬영해 주십시오. "
                "(웃음·찡그림·눈 감음은 측정 정확도를 떨어뜨립니다.)"
            ),
            detail=detail,
        )
    if len(blocked_categories) == 1:
        cat = blocked_categories[0]
        labels = {
            EXPR_NOISE_MOUTH: "입(웃음·다물기)",
            EXPR_NOISE_EYE: "눈(감음·크게 뜸·시선 이탈)",
            EXPR_NOISE_BROW: "눈썹(올림·내림)",
            EXPR_NOISE_JAW_CHEEK: "턱·뺨(벌림·부풀림)",
            EXPR_NOISE_NOSE_CHIN: "코·턱주름(콧방울 찡그림)",  # ADR-212
        }
        return ExpressionNoiseResult(
            blocked=True, warned=True,
            category=cat,
            max_intensity=round(overall_max, 3),
            user_message=(
                f"{labels[cat]} 표정 강도가 높습니다. 무표정 정면 사진으로 다시 "
                "촬영해 주십시오."
            ),
            detail=detail,
        )

    # 경고 카테고리 — 차단까지는 아니나 사용자에게 알림
    if (mouth_max > WARN_THRESHOLD or eye_max > WARN_THRESHOLD
            or brow_max > WARN_THRESHOLD or jaw_cheek_max > WARN_THRESHOLD
            or nose_chin_max > WARN_THRESHOLD):  # ADR-212
        return ExpressionNoiseResult(
            blocked=False, warned=True,
            category=EXPR_NOISE_NONE,
            max_intensity=round(overall_max, 3),
            user_message=(
                "표정 강도가 약간 있습니다. 무표정 사진이면 정확도가 더 높습니다."
            ),
            detail=detail,
        )

    return ExpressionNoiseResult(
        blocked=False, warned=False,
        category=EXPR_NOISE_NONE,
        max_intensity=round(overall_max, 3),
        user_message="",
        detail=detail,
    )
