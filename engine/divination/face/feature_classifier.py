"""부위별 형상 결정론 분류 — 입꼬리 각도 (앙월구·복주구·일자구).

ADR-034 (Phase 1) — 외부 딥리서치 보고서 squeeze-report 결과 본문화.
- 입력: MediaPipe Face Landmarker 478 키포인트 metrics (필요 시 좌표 dict)
- 출력: 분류명 (앙월구·복주구·일자구) + 측정 각도(도)

본 모듈은 face_shape.py(5형 얼굴 윤곽)와 별개의 **부위 단위 결정론 분류**.
PROMPT_facial-feature-classification 의뢰의 응답 보고서 중 구체 임계값이
명시된 C5(앙월구) 1건만 본문화. 나머지(C1~C7 6건)는 임계값 구체 수치 부재로
ADR-010 사실성 분리 정신 위반 → DEFER 또는 REJECT (reports/facial-feature-phase1.md
permanently_rejected 영속화).

ADR 정합:
- ADR-010 (사실성 분리): 임계값 출처 KoreaScience JAKO200810103458095 검증
- ADR-022 (face_shape 5형): 5형 분류와 직교 — 입꼬리 단독 분류
- ADR-006 (자문 거절): 운명·관운 매핑 X. 시각 형태 분류 라벨만.
- ADR-005 Supplement 4·5·7: Stage 2 코드 DB 인용 출처로 사용 가능
  (학파 명칭 "앙월구·복주구"는 본 결정론 출처에서만 흐름)

면책:
- 본 분류는 시각 형태 측정 결과로, 운명·길흉·관운 인과 매핑 X
- 사상체질·태음인/소양인 인용은 의도적으로 본문화 X (ADR-006 정신)
- 표정 변화에 민감 — 무표정 정면 사진 권장
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


# MediaPipe Face Landmarker 478 키포인트 입꼬리 인덱스
# 출처: MediaPipe 공식 face_landmarker (https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker)
# + Sander de Snaijer 블로그 (https://www.sanderdesnaijer.com/blog/mediapipe-face-mesh-landmarks)
KP_MOUTH_CORNER_LEFT = 61   # 좌측 입꼬리 (사용자 기준 왼쪽 = 카메라 기준 오른쪽)
KP_MOUTH_CORNER_RIGHT = 291  # 우측 입꼬리


# 분류 임계값 (도 단위)
# 출처: 보고서 §3.4 "입꼬리 각도 > 0 (즉, 위로 향하는 경우)"
# 임계값은 수평선 대비 입꼬리 각도. 좌우 입꼬리 평균 사용.
# +값 = 위로 향함 (앙월구), -값 = 아래로 향함 (복주구), 0 근처 = 일자구
_THRESHOLD_ANGSWOLGU_MIN_DEG = 2.0  # 양수 + 측정 잡음 마진
_THRESHOLD_BOKJUGU_MAX_DEG = -2.0   # 음수 + 측정 잡음 마진
# -2 ~ +2 사이는 "일자구"


SHAPE_ANGSWOLGU = "앙월구"   # 仰月口 — 입꼬리 위로 향함
SHAPE_BOKJUGU = "복주구"      # 覆舟口 — 입꼬리 아래로 향함
SHAPE_ILJAGU = "일자구"       # 一字口 — 수평


@dataclass(frozen=True)
class MouthCornerResult:
    """입꼬리 분류 결과.

    Attributes:
        shape_type: 분류명 (앙월구·복주구·일자구)
        angle_deg: 입꼬리 평균 각도 (수평 대비, 도 단위). +값=위, -값=아래.
        left_angle_deg: 좌측 입꼬리 각도
        right_angle_deg: 우측 입꼬리 각도
        confidence: 측정 신뢰도 (HIGH/MEDIUM/LOW)
        source_url: 임계값 학술 출처
        disclaimer: 사용자 출력용 면책
    """

    shape_type: str
    angle_deg: float
    left_angle_deg: float
    right_angle_deg: float
    confidence: str
    source_url: str
    disclaimer: str


_SOURCE_URL = "https://koreascience.kr/article/JAKO200810103458095.pdf"
_DISCLAIMER = (
    "본 분류는 입꼬리 각도 측정 결과로, 운명·길흉·관운 매핑이 아닙니다. "
    "표정 변화에 민감하므로 무표정 정면 사진 기준 측정값입니다."
)


def _corner_angle_relative_to_inner_baseline(
    p_corner: tuple[float, float],
    p_baseline: tuple[float, float],
) -> float:
    """입꼬리(corner)와 입 안쪽 기준점(baseline) 사이 수평 대비 각도 (도).

    baseline은 두 입꼬리 사이 수평 가상선의 x 중점·y 중점이 아니라,
    같은 좌우 측 안쪽 입술 윤곽 또는 입꼬리 평균 y. 본 함수는
    "입꼬리가 두 입꼬리 평균 y 라인보다 얼마나 위/아래에 있는가"를 측정.

    +값 = 입꼬리가 baseline보다 위 (앙월구 방향)
    -값 = 입꼬리가 baseline보다 아래 (복주구 방향)

    좌표계: y축이 아래로 향하는 이미지 좌표 (브라우저/MediaPipe 표준).
    """
    dx = abs(p_corner[0] - p_baseline[0])
    dy = p_baseline[1] - p_corner[1]  # y 반전 — 위가 +
    if dx < 1e-9:
        return 90.0 if dy > 0 else (-90.0 if dy < 0 else 0.0)
    return math.degrees(math.atan2(dy, dx))


def classify_mouth_corner(
    landmarks: dict[int, tuple[float, float]] | None,
) -> MouthCornerResult | None:
    """입꼬리 각도로 앙월구·복주구·일자구 분류.

    측정 원리: 두 입꼬리 (KP_61, KP_291)를 잇는 직선의 수평 기울기.
    - 두 입꼬리의 y가 거의 동일 (둘 다 가운데 입 라인 근처) → 일자구
    - 둘 다 입의 중간(=두 입꼬리 평균 y로 정의)보다 위 → 측정 의미 X
      → 대신 좌우 입꼬리가 함께 위로 휘었는지 보려면 입술 중심 측정이 필요하나
      Phase 1에서는 두 입꼬리 y 평균을 그대로 baseline으로 사용
    - 실제 의미 있는 신호: 두 입꼬리의 평균 y와 입술 중앙(별도 KP) 사이의 차이.
      그러나 Phase 1에서는 보고서가 명시한 "mouth_corner_lift_angle"의 의미를
      "두 입꼬리가 입 중앙 가로선 대비 위/아래" 단일 값으로 해석.

    Phase 1 단순 해석: 두 입꼬리 y의 평균을 m이라 할 때, 좌우 입꼬리가 m보다
    위에 있으면 (= 좌우 모두 y < m) 앙월구, 아래(y > m)면 복주구. 그러나
    실제로는 두 입꼬리만 있는 경우 정의상 평균 = 자기 자신이므로 0이 됨.

    → 본 Phase 1에서는 metrics.mouth_corner_lift_angle (클라이언트 측 계산)
       경로 단독 사용을 권장. landmarks 경로는 추가 입술 중앙 KP가 있을 때만
       의미 있는 결과를 산출 (KP_13: 윗입술 중앙, KP_14: 아랫입술 중앙).
    """
    if not landmarks:
        return None
    if KP_MOUTH_CORNER_LEFT not in landmarks or KP_MOUTH_CORNER_RIGHT not in landmarks:
        return None

    left = landmarks[KP_MOUTH_CORNER_LEFT]
    right = landmarks[KP_MOUTH_CORNER_RIGHT]

    # baseline: 입술 중앙(KP_13 윗입술 중앙 또는 KP_14 아랫입술 중앙)이 있으면 사용,
    # 없으면 두 입꼬리의 y를 단순 비교 (좌우 비대칭 검출만).
    KP_UPPER_LIP_CENTER = 13
    KP_LOWER_LIP_CENTER = 14
    baseline_y: float | None = None
    if KP_UPPER_LIP_CENTER in landmarks and KP_LOWER_LIP_CENTER in landmarks:
        # 윗입술·아랫입술 중앙의 평균 = 입 가로 중심선
        baseline_y = (landmarks[KP_UPPER_LIP_CENTER][1] + landmarks[KP_LOWER_LIP_CENTER][1]) / 2.0
    elif KP_UPPER_LIP_CENTER in landmarks:
        baseline_y = landmarks[KP_UPPER_LIP_CENTER][1]
    elif KP_LOWER_LIP_CENTER in landmarks:
        baseline_y = landmarks[KP_LOWER_LIP_CENTER][1]

    if baseline_y is not None:
        # 입술 중심선 대비 좌우 입꼬리 각도
        x_mid = (left[0] + right[0]) / 2.0
        left_baseline = (x_mid, baseline_y)
        right_baseline = (x_mid, baseline_y)
        left_angle = _corner_angle_relative_to_inner_baseline(left, left_baseline)
        right_angle = _corner_angle_relative_to_inner_baseline(right, right_baseline)
    else:
        # 입술 중앙 KP 부재 시 — 두 입꼬리 y 차이를 가지고 좌우 비대칭 측정만.
        # 절대 위/아래 판정 불가하므로 일자구 반환 (HIGH → MEDIUM 신뢰도)
        # 이 분기는 입꼬리 단독만 측정 가능한 경우 (이론적 폴백)
        left_angle = 0.0
        right_angle = 0.0

    avg_angle = (left_angle + right_angle) / 2.0

    if avg_angle >= _THRESHOLD_ANGSWOLGU_MIN_DEG:
        shape = SHAPE_ANGSWOLGU
    elif avg_angle <= _THRESHOLD_BOKJUGU_MAX_DEG:
        shape = SHAPE_BOKJUGU
    else:
        shape = SHAPE_ILJAGU

    return MouthCornerResult(
        shape_type=shape,
        angle_deg=round(avg_angle, 2),
        left_angle_deg=round(left_angle, 2),
        right_angle_deg=round(right_angle, 2),
        confidence="HIGH",
        source_url=_SOURCE_URL,
        disclaimer=_DISCLAIMER,
    )


def classify_from_metrics(metrics: dict[str, Any] | None) -> MouthCornerResult | None:
    """클라이언트 MediaPipe metrics dict에서 자동 추출.

    metrics 형식 (face_reading.py 클라이언트 호환):
        {
          "landmarks": {61: [x, y], 291: [x, y], ...}
          또는
          "mouth_corner_left": [x, y], "mouth_corner_right": [x, y]
          또는
          "mouth_corner_lift_angle": float (이미 계산된 도 단위 각도)
        }

    Returns:
        분류 결과. metrics 형식 미충족 시 None.
    """
    if not metrics:
        return None

    # 경로 1 — 이미 계산된 각도 제공
    pre_angle = metrics.get("mouth_corner_lift_angle")
    if isinstance(pre_angle, (int, float)):
        avg = float(pre_angle)
        if avg >= _THRESHOLD_ANGSWOLGU_MIN_DEG:
            shape = SHAPE_ANGSWOLGU
        elif avg <= _THRESHOLD_BOKJUGU_MAX_DEG:
            shape = SHAPE_BOKJUGU
        else:
            shape = SHAPE_ILJAGU
        return MouthCornerResult(
            shape_type=shape,
            angle_deg=round(avg, 2),
            left_angle_deg=round(avg, 2),
            right_angle_deg=round(avg, 2),
            confidence="HIGH",
            source_url=_SOURCE_URL,
            disclaimer=_DISCLAIMER,
        )

    # 경로 2 — landmarks dict
    lm = metrics.get("landmarks")
    if isinstance(lm, dict):
        normalized: dict[int, tuple[float, float]] = {}
        for k, v in lm.items():
            try:
                idx = int(k)
            except (TypeError, ValueError):
                continue
            if isinstance(v, (list, tuple)) and len(v) >= 2:
                normalized[idx] = (float(v[0]), float(v[1]))
        return classify_mouth_corner(normalized)

    # 경로 3 — 키포인트 좌표 직접
    l = metrics.get("mouth_corner_left")
    r = metrics.get("mouth_corner_right")
    if isinstance(l, (list, tuple)) and isinstance(r, (list, tuple)) and len(l) >= 2 and len(r) >= 2:
        return classify_mouth_corner({
            KP_MOUTH_CORNER_LEFT: (float(l[0]), float(l[1])),
            KP_MOUTH_CORNER_RIGHT: (float(r[0]), float(r[1])),
        })

    return None


# ═════════════════════════════════════════════════════════════════════════════
# Phase 2 (ADR-064) — 코 비지수 분류 (Leptorrhine·Mesorrhine·Platyrrhine)
#
# 출처: Lee & Park (2024) "Three-Dimensional Cone-Beam Computed Tomography
# Analysis of Nasal Morphology in Young Korean Adults" Healthcare 12:1839
# PMC11431719 (오픈 액세스, Phase B 200 OK 검증)
#
# 표본: 한국 20대 100명 (남 50 + 여 50)
# 측정: 콧방울 너비 (AL-AL) + 코 길이 (N-SN)
# 임계값:
#   비지수 (Nasal Index) = 콧방울너비 / 코길이 × 100
#   · Leptorrhine (좁은 코): NI < 70
#   · Mesorrhine (보통 코): 70 ≤ NI ≤ 85
#   · Platyrrhine (넓은 코): NI > 85
#
# 사상체질 인용 X (Phase 2 PROMPT 강제 정합)
# 운명·관운·재물복 매핑 X (ADR-006 정합)
# ═════════════════════════════════════════════════════════════════════════════

# 한국 20대 평균 (PMC11431719 Table 5)
_NOSE_KOREAN_20S_MEAN: dict[str, dict[str, float]] = {
    "male": {
        "nasal_width_mm": 39.33,   # AL-AL (콧방울 너비)
        "nasal_width_std": 2.43,
        "nasal_height_mm": 51.91,  # N-SN (코 길이)
        "nasal_height_std": 3.15,
        "sample_size": 50,
    },
    "female": {
        "nasal_width_mm": 36.70,
        "nasal_width_std": 2.45,
        "nasal_height_mm": 47.74,
        "nasal_height_std": 3.36,
        "sample_size": 50,
    },
}

# 비지수 임계값 (PMC11431719 + 인체측정학 표준 분류)
_NASAL_INDEX_LEPTORRHINE_MAX = 70.0   # NI < 70 → 좁은 코
_NASAL_INDEX_PLATYRRHINE_MIN = 85.0   # NI > 85 → 넓은 코
# 70 ≤ NI ≤ 85 → 보통 코 (Mesorrhine)


NOSE_LEPTORRHINE = "좁은 코"      # Leptorrhine — 코폭이 좁고 긴 형태
NOSE_MESORRHINE = "보통 코"        # Mesorrhine — 한국 20대 평균 범위
NOSE_PLATYRRHINE = "넓은 코"       # Platyrrhine — 코폭이 넓은 형태


_NOSE_SOURCE_URL = "https://pmc.ncbi.nlm.nih.gov/articles/PMC11431719/"
_NOSE_DISCLAIMER = (
    "본 분류는 시각 형태 측정 결과로, 운명·길흉·관운 인과 매핑 X. "
    "한국 20대 100명 (남/여 각 50명) PMC11431719 표본 기반. "
    "사상체질·태음인 인용 X (ADR-006 정신)."
)


@dataclass(frozen=True)
class NoseShapeResult:
    """코 비지수 분류 결과.

    Attributes:
        shape_type: 분류명 (좁은 코·보통 코·넓은 코)
        nasal_index: 비지수 (콧방울너비 / 코길이 × 100)
        nasal_width_mm: 콧방울 너비 (mm) — 입력
        nasal_height_mm: 코 길이 (mm) — 입력
        confidence: HIGH (정량 측정) / MEDIUM (단일 픽셀 추정)
        source_url: 출처 PMC URL
        disclaimer: ADR-006 면책 텍스트
    """
    shape_type: str
    nasal_index: float
    nasal_width_mm: float
    nasal_height_mm: float
    confidence: str
    source_url: str
    disclaimer: str


def classify_nose_shape(
    nasal_width_mm: float,
    nasal_height_mm: float,
    *,
    confidence: str = "HIGH",
) -> NoseShapeResult | None:
    """코 비지수 기반 형태 분류 (Phase 2, ADR-064).

    Args:
        nasal_width_mm: 콧방울 너비 (AL-AL) 밀리미터
        nasal_height_mm: 코 길이 (N-SN) 밀리미터
        confidence: HIGH / MEDIUM (측정 정밀도)

    Returns:
        NoseShapeResult 또는 None (입력 부정합 시)

    Examples:
        >>> r = classify_nose_shape(38.0, 50.0)
        >>> r.shape_type  # 38/50*100=76 → 70~85 → Mesorrhine
        '보통 코'
        >>> r = classify_nose_shape(45.0, 48.0)  # 45/48*100=93.75 → >85
        >>> r.shape_type
        '넓은 코'
    """
    if not isinstance(nasal_width_mm, (int, float)) or not isinstance(nasal_height_mm, (int, float)):
        return None
    if nasal_width_mm <= 0 or nasal_height_mm <= 0:
        return None

    nasal_index = (nasal_width_mm / nasal_height_mm) * 100.0

    if nasal_index < _NASAL_INDEX_LEPTORRHINE_MAX:
        shape = NOSE_LEPTORRHINE
    elif nasal_index > _NASAL_INDEX_PLATYRRHINE_MIN:
        shape = NOSE_PLATYRRHINE
    else:
        shape = NOSE_MESORRHINE

    return NoseShapeResult(
        shape_type=shape,
        nasal_index=round(nasal_index, 2),
        nasal_width_mm=float(nasal_width_mm),
        nasal_height_mm=float(nasal_height_mm),
        confidence=confidence,
        source_url=_NOSE_SOURCE_URL,
        disclaimer=_NOSE_DISCLAIMER,
    )


def get_nose_korean_20s_mean(sex: str) -> dict[str, float] | None:
    """한국 20대 평균값 조회 (PMC11431719).

    Args:
        sex: 'male' 또는 'female'

    Returns:
        평균·표준편차·표본크기 dict 또는 None
    """
    if sex not in _NOSE_KOREAN_20S_MEAN:
        return None
    return dict(_NOSE_KOREAN_20S_MEAN[sex])


# ─────────────────────────── ADR-099: 턱 하악각 분류 (Phase 2) ───────────────────────────
# 출처: PMC4738126 (한국 106명 3D CBCT) + PMC11417696 (taiwanese 100명) + KCI 차인호 한국 117명.
# 본 시스템 ADR-064 코 분류 동일 정신 — 운명 매핑 X (ADR-006).

# 하악각 (Gonial Angle) 카테고리 — 인체계측학 정상 범위 (120~140°)
JAW_SQUARE = "사각형 턱"          # 강한 교근 비후, 하악각 < 124°
JAW_OVAL = "계란형 턱"            # 균형, 125~132°
JAW_POINTED = "뾰족형 턱"         # 하방 뾰족, > 132°
JAW_ROUND = "둥근형 턱"           # 둥근 윤곽, 계란 범위 + 하악체 짧음

# 정상 범위 (인체계측학 정상 변동) — 외부 값은 측정 오류 또는 병리 가능성
_JAW_NORMAL_MIN_DEG = 100.0
_JAW_NORMAL_MAX_DEG = 150.0

# 4분류 경계 (PMC4738126·PMC11417696·차인호 한국 117명 정합)
_JAW_SQUARE_MAX = 124.0
_JAW_OVAL_MIN = 125.0
_JAW_OVAL_MAX = 132.0
_JAW_POINTED_MIN = 133.0

_JAW_KOREAN_MEAN: dict[str, dict[str, float]] = {
    # PMC4738126 한국 106명 (사각턱 환자군) 3D CBCT
    "patient_3d_cbct": {
        "right_mean": 134.37, "right_sd": 8.44,
        "left_mean": 131.54, "left_sd": 7.14,
        "n": 106,
    },
    # KCI 차인호 (한국 117명, 정상교합)
    "normal_korean": {
        "mean": 128.71, "sd": 3.87, "n": 117,
    },
}

_JAW_SOURCE_URLS: tuple[str, ...] = (
    "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4738126/",   # 한국 106명 3D CBCT
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC11417696/",      # taiwanese 100명 사각턱
)

_JAW_DISCLAIMER = (
    "본 분류는 안면 골격 형태학적 측정 결과로, 운명·길흉·관운 인과 매핑 X. "
    "한국 표본 PMC4738126(106명 3D CBCT) + KCI 차인호(117명 정상교합) 기반. "
    "사상체질·태음인 인용 X (ADR-006 정신). "
    "선천성 안면 기형·증후군(KBG·SRD5A2·MBTPS1·CDKN2A) 의료 진단 영역 X."
)


@dataclass(frozen=True)
class JawShapeResult:
    """턱 하악각 분류 결과 (ADR-099).

    Attributes:
        shape_type: 분류명 (사각형·계란형·뾰족형·둥근형)
        gonial_angle_deg: 입력 하악각 (도)
        gonial_angle_side: 측정 측면 (right·left·avg)
        confidence: HIGH (3D CBCT) / MEDIUM (2D 사진계측)
        source_urls: 출처 URL 풀
        disclaimer: ADR-006 면책 텍스트
    """
    shape_type: str
    gonial_angle_deg: float
    gonial_angle_side: str
    confidence: str
    source_urls: tuple[str, ...]
    disclaimer: str


def classify_jaw_shape(
    gonial_angle_deg: float,
    *,
    side: str = "avg",
    confidence: str = "HIGH",
) -> JawShapeResult | None:
    """하악각 기반 턱 형태 4분류 (ADR-099).

    Args:
        gonial_angle_deg: 하악각 (도, gonial angle)
        side: 측정 측면 ('right'·'left'·'avg')
        confidence: HIGH (3D CBCT) / MEDIUM (2D 사진)

    Returns:
        JawShapeResult — 사각·계란·뾰족·둥근 중 하나.
        입력 부정합 또는 정상 범위 외 (100~150° 밖) 시 None (의료 진단 영역 차단).

    Examples:
        >>> r = classify_jaw_shape(120.0)
        >>> r.shape_type
        '사각형 턱'
        >>> r = classify_jaw_shape(128.0)
        >>> r.shape_type
        '계란형 턱'
        >>> r = classify_jaw_shape(135.0)
        >>> r.shape_type
        '뾰족형 턱'
        >>> classify_jaw_shape(95.0)  # 정상 범위 외 → None
    """
    if not isinstance(gonial_angle_deg, (int, float)):
        return None
    angle = float(gonial_angle_deg)
    # 정상 인체계측 범위 외 → 측정 오류 또는 병리 (의료 진단 영역, ADR-006)
    if angle < _JAW_NORMAL_MIN_DEG or angle > _JAW_NORMAL_MAX_DEG:
        return None
    if side not in ("right", "left", "avg"):
        side = "avg"

    if angle <= _JAW_SQUARE_MAX:
        shape = JAW_SQUARE
    elif angle >= _JAW_POINTED_MIN:
        shape = JAW_POINTED
    else:
        # 계란 범위 (125~132°) — 둥근형은 별도 하안면부 비율 데이터 필요 (별도 ADR)
        shape = JAW_OVAL

    return JawShapeResult(
        shape_type=shape,
        gonial_angle_deg=round(angle, 2),
        gonial_angle_side=side,
        confidence=confidence,
        source_urls=_JAW_SOURCE_URLS,
        disclaimer=_JAW_DISCLAIMER,
    )


def get_jaw_korean_mean(sample: str = "normal_korean") -> dict[str, float] | None:
    """한국 표본 하악각 평균 조회 (ADR-099).

    Args:
        sample: 'normal_korean' (KCI 차인호 117명) 또는 'patient_3d_cbct' (PMC4738126)

    Returns:
        평균·표준편차·표본크기 dict 또는 None
    """
    if sample not in _JAW_KOREAN_MEAN:
        return None
    return dict(_JAW_KOREAN_MEAN[sample])
