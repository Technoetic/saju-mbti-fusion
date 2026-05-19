"""ADR-022 5형 결정론 안면 형태 분류 (목·화·토·금·수 + 복합형).

보고서 §3 본문화:
  · MediaPipe 478 키포인트 + 한국인 안면 인체측정학 KCI 학술 출처
  · 3 핵심 메트릭: face_width_height_ratio · jaw_angle_deg · bizygomatic_to_bigonial_ratio
  · 5형(五行) 매핑: 목(수직)·화(역삼각)·토(수평)·금(각진)·수(둥근) + 복합형 fallback
  · 학파 회피 (마의·유장 인과 도그마 차단) — ADR-002·006·010·018 정합

설계 (CLAUDE.md §0 결정론 + LLM 분리):
  · 순수 기하학 연산 (LLM 호출 0)
  · 입력: MediaPipe 478 키포인트에서 추출된 너비·높이·각도 메트릭
  · 출력: shape_type (한글 오행명) + morphological_name (객관 형태명) + 임계값 통과 근거
  · 학술 출처 URL 영속화 (vault/references/korean-face-anthropometry.md 참조)

학술 근거:
  · 송우철 외 (2017) DBpia NODE07133895 — 얼굴 너비·길이 비율
  · 최윤경·이경희 (2009) DBpia NODE09916734 — 안면 형태 분류
  · 노상훈 외 (1998) JKAOMS — 하악각 통계
  · POSTECH HFES 2012 — 한국인 안면 측정 데이터

ADR-018(face-golden-set-policy) DEFER 해소: 5형 분류 설계 ACCEPT → 본 모듈로 구현.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


# ─────────────────────────── 5형 매핑 (영문 ↔ 한글 오행) ───────────────────────────

# face_scoring.py 영문 face_shape (round·square·oval·long·inverted_tri) 호환 매핑
# 보고서 §3 + ADR-018 정합
SHAPE_KOREAN_TO_LATIN: dict[str, str] = {
    "목형": "long",
    "화형": "inverted_tri",
    "토형": "oval",      # 수평발달, 두툼한 타원
    "금형": "square",    # 하악각 강조, 사각형
    "수형": "round",     # 둥근 곡선형
    "복합형": "oval",    # fallback — 평균
}

SHAPE_LATIN_TO_KOREAN: dict[str, str] = {v: k for k, v in SHAPE_KOREAN_TO_LATIN.items() if k != "복합형"}


# ─────────────────────────── 결과 dataclass ───────────────────────────


@dataclass(frozen=True)
class FaceShapeResult:
    """5형 분류 결정론 결과.

    Attributes:
        shape_type: 한글 오행명 (목형·화형·토형·금형·수형·복합형).
        latin: 영문 face_shape (face_scoring.py 호환).
        morphological_name: 객관 형태명 (학파 도그마 회피).
        metrics: 입력 메트릭 (face_width_height_ratio 등).
        matched_criteria: 통과한 임계값 조건 목록.
        reference_paper: 학술 출처 URL.
    """

    shape_type: str
    latin: str
    morphological_name: str
    metrics: dict[str, float]
    matched_criteria: list[str]
    reference_paper: str


# ─────────────────────────── 메트릭 산출 (보고서 §2.2) ───────────────────────────


def compute_face_metrics(
    face_width: float,
    face_height: float,
    jaw_angle_deg: float,
    zygo_width: float,
    bigo_width: float,
    upper_face_height: float | None = None,
    lower_face_height: float | None = None,
) -> dict[str, float]:
    """MediaPipe 키포인트에서 추출된 거리·각도 → 분류 메트릭.

    Args:
        face_width: Bizygomatic width (좌측 234 ↔ 우측 454 거리).
        face_height: Trichion-Gnathion (10 ↔ 152 거리).
        jaw_angle_deg: 하악각 (Go_L 58 + Gn 152 + Go_R 288 벡터 내적 각도).
        zygo_width: 좌우 광대점 너비 (234 ↔ 454).
        bigo_width: 좌우 하악각 너비 (58 ↔ 288).
        upper_face_height: 상정 (Trichion 10 ↔ Glabella 9 또는 nasion까지) 옵션.
        lower_face_height: 하정 (Stomion 13 ↔ Gnathion 152) 옵션.

    Returns:
        dict — face_width_height_ratio, jaw_angle_deg, bizygomatic_to_bigonial_ratio,
        upper_to_lower_face_ratio (옵션).
    """
    metrics: dict[str, float] = {}

    if face_height > 0:
        metrics["face_width_height_ratio"] = round(face_width / face_height, 3)

    metrics["jaw_angle_deg"] = round(float(jaw_angle_deg), 1)

    if bigo_width > 0:
        metrics["bizygomatic_to_bigonial_ratio"] = round(zygo_width / bigo_width, 3)

    if upper_face_height is not None and lower_face_height is not None and lower_face_height > 0:
        metrics["upper_to_lower_face_ratio"] = round(upper_face_height / lower_face_height, 3)

    return metrics


def jaw_angle_from_points(
    go_left: tuple[float, float, float],
    gnathion: tuple[float, float, float],
    go_right: tuple[float, float, float],
) -> float:
    """3D 좌표 → 하악각 (벡터 내적, 도 단위).

    Go_L → Gn 과 Go_R → Gn 벡터 사이 각도. 보고서 §2.2.
    """
    v1 = (gnathion[0] - go_left[0], gnathion[1] - go_left[1], gnathion[2] - go_left[2])
    v2 = (gnathion[0] - go_right[0], gnathion[1] - go_right[1], gnathion[2] - go_right[2])

    dot = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]
    mag1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2 + v1[2] ** 2)
    mag2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2 + v2[2] ** 2)

    if mag1 == 0 or mag2 == 0:
        return 0.0

    cos_theta = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return round(math.degrees(math.acos(cos_theta)), 1)


# ─────────────────────────── 5형 임계값 분류 (보고서 §3 YAML) ───────────────────────────


def _check_wood(m: dict[str, float]) -> tuple[bool, list[str]]:
    """목형: 수직발달 (긴 얼굴). 보고서 §3 라인 252-259."""
    criteria = []
    fwhr = m.get("face_width_height_ratio")
    jaw = m.get("jaw_angle_deg")

    if fwhr is None or jaw is None:
        return False, []

    if fwhr < 0.82:
        criteria.append(f"face_width_height_ratio={fwhr} < 0.82")
    if 115 <= jaw <= 130:
        criteria.append(f"jaw_angle_deg={jaw} in [115, 130]")

    return len(criteria) == 2, criteria


def _check_fire(m: dict[str, float]) -> tuple[bool, list[str]]:
    """화형: 상광하협 (역삼각). 보고서 §3 라인 261-268."""
    criteria = []
    bz_bg = m.get("bizygomatic_to_bigonial_ratio")
    jaw = m.get("jaw_angle_deg")

    if bz_bg is None or jaw is None:
        return False, []

    if bz_bg > 1.25:
        criteria.append(f"bizygomatic_to_bigonial_ratio={bz_bg} > 1.25")
    if jaw > 125:
        criteria.append(f"jaw_angle_deg={jaw} > 125")

    # upper_to_lower_face_ratio > 0.60는 옵션 (메트릭 없으면 1차 조건 충족 시 통과)
    return len(criteria) == 2, criteria


def _check_earth(m: dict[str, float]) -> tuple[bool, list[str]]:
    """토형: 수평발달 (넓고 두꺼운 얼굴). 보고서 §3 라인 270-277."""
    criteria = []
    fwhr = m.get("face_width_height_ratio")
    jaw = m.get("jaw_angle_deg")

    if fwhr is None or jaw is None:
        return False, []

    if fwhr >= 0.88:
        criteria.append(f"face_width_height_ratio={fwhr} >= 0.88")
    if jaw >= 115:
        criteria.append(f"jaw_angle_deg={jaw} >= 115")

    return len(criteria) == 2, criteria


def _check_metal(m: dict[str, float]) -> tuple[bool, list[str]]:
    """금형: 하악발달 (각진 얼굴). 보고서 §3 라인 279-286."""
    criteria = []
    fwhr = m.get("face_width_height_ratio")
    jaw = m.get("jaw_angle_deg")
    bz_bg = m.get("bizygomatic_to_bigonial_ratio")

    if fwhr is None or jaw is None or bz_bg is None:
        return False, []

    if fwhr >= 0.85:
        criteria.append(f"face_width_height_ratio={fwhr} >= 0.85")
    if jaw < 112:
        criteria.append(f"jaw_angle_deg={jaw} < 112")
    if bz_bg <= 1.15:
        criteria.append(f"bizygomatic_to_bigonial_ratio={bz_bg} <= 1.15")

    return len(criteria) == 3, criteria


def _check_water(m: dict[str, float]) -> tuple[bool, list[str]]:
    """수형: 곡선발달 (둥근 얼굴). 보고서 §3 라인 288-296."""
    criteria = []
    fwhr = m.get("face_width_height_ratio")
    jaw = m.get("jaw_angle_deg")
    bz_bg = m.get("bizygomatic_to_bigonial_ratio")

    if fwhr is None or jaw is None or bz_bg is None:
        return False, []

    if 0.83 <= fwhr <= 0.88:
        criteria.append(f"face_width_height_ratio={fwhr} in [0.83, 0.88]")
    if jaw > 120:
        criteria.append(f"jaw_angle_deg={jaw} > 120")
    if bz_bg <= 1.20:
        criteria.append(f"bizygomatic_to_bigonial_ratio={bz_bg} <= 1.20")

    return len(criteria) == 3, criteria


# ─────────────────────────── 학술 출처 (보고서 §3) ───────────────────────────


_REFERENCE_PAPERS: dict[str, str] = {
    "목형": "https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE07133895",   # 송우철 외 (2017)
    "화형": "https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE09916734",   # 최윤경·이경희 (2009)
    "토형": "https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE07133895",   # 송우철 외 (2017)
    "금형": "https://www.jkaoms.org/journal/download_pdf.php?spage=129&volume=32&number=2",  # 노상훈 외 (1998)
    "수형": "http://center.postech.ac.kr/homepage_data/publication_proceedings_international/12_HFES_OxygenMask.pdf",  # POSTECH 2012
    "복합형": "https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE07133895",
}


_MORPHOLOGICAL_NAMES: dict[str, str] = {
    "목형": "수직발달형 (긴 얼굴)",
    "화형": "상광하협형 (역삼각 얼굴)",
    "토형": "수평발달형 (넓고 두꺼운 얼굴)",
    "금형": "하악발달형 (각진 얼굴)",
    "수형": "곡선발달형 (둥근 얼굴)",
    "복합형": "표준형 (균형 얼굴)",
}


# ─────────────────────────── 핵심 분류 함수 ───────────────────────────


def classify_face_shape(metrics: dict[str, float]) -> FaceShapeResult:
    """3 메트릭 → 5형 결정론 분류 + 복합형 fallback.

    보고서 §3 YAML 임계값 순차 점검. 우선순위:
    1. 목형 (수직 극단)
    2. 화형 (역삼각 극단)
    3. 금형 (각진 극단)
    4. 토형 (수평 발달)
    5. 수형 (둥근 평균)
    6. 복합형 fallback

    Args:
        metrics: compute_face_metrics() 결과 또는 동일 키 dict.

    Returns:
        FaceShapeResult — 결정론 분류 + 학술 근거.
    """
    # 우선순위 점검 (극단 → 평균)
    checks = [
        ("목형", _check_wood),
        ("화형", _check_fire),
        ("금형", _check_metal),
        ("토형", _check_earth),
        ("수형", _check_water),
    ]

    for shape, check_fn in checks:
        passed, criteria = check_fn(metrics)
        if passed:
            return FaceShapeResult(
                shape_type=shape,
                latin=SHAPE_KOREAN_TO_LATIN[shape],
                morphological_name=_MORPHOLOGICAL_NAMES[shape],
                metrics=dict(metrics),
                matched_criteria=criteria,
                reference_paper=_REFERENCE_PAPERS[shape],
            )

    # fallback
    return FaceShapeResult(
        shape_type="복합형",
        latin=SHAPE_KOREAN_TO_LATIN["복합형"],
        morphological_name=_MORPHOLOGICAL_NAMES["복합형"],
        metrics=dict(metrics),
        matched_criteria=["fallback — 임계값 교집합 외, 한국인 평균"],
        reference_paper=_REFERENCE_PAPERS["복합형"],
    )


# ─────────────────────────── ADR-006/010 면책 가이드라인 ───────────────────────────

# 사용자 출력 시 반드시 동반 (LLM 페르소나 시스템 프롬프트 주입용)
DEFAULT_DISCLAIMERS: list[str] = [
    "본 결과는 객관 기하학적 형태 분류이며 길흉화복·운명·성격과 무관합니다.",
    "한국인 안면 인체측정학 KCI 학술 출처 기반의 통계 비교입니다.",
    "마의상법·유장상법 등 전통 관상학 인과 해석은 채택하지 않습니다.",
]


__all__ = [
    "FaceShapeResult",
    "SHAPE_KOREAN_TO_LATIN",
    "SHAPE_LATIN_TO_KOREAN",
    "DEFAULT_DISCLAIMERS",
    "compute_face_metrics",
    "jaw_angle_from_points",
    "classify_face_shape",
]
