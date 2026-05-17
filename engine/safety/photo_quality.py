"""ADR-020 L2 사진 품질 검증 — Laplacian Variance 결정론 점수.

vault/reports/input-guardrails.md §3 본문화:
  · cv2.Laplacian(gray, cv2.CV_64F, ksize=3).var() 표준 OpenCV
  · 손금 임계값 150.0 (미세 선 분석 절대)
  · 관상 임계값 100.0 (조명·화장품 영향)

설계 원칙 (CLAUDE.md §0 + ADR-010):
  · 결정론 보장 (cv2 있으면 정확 산출)
  · Graceful degradation (cv2 없으면 None — photo_guide.py 텍스트 가이드 fallback)
  · 사용자 출력 인과 표현 0건 (순수 입력 품질 측정, 운세 무관)
  · 외부 의존 최소화 (cv2·numpy는 선택적)

L1 file_integrity → L2 photo_quality → L3 MediaPipe Fail-Fast 파이프라인.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


# ─────────────────────────── 임계값 상수 (보고서 §3.2 권장) ───────────────────────────

THRESHOLD_PALM: float = 150.0  # 손금 — 미세 선 분석 절대
THRESHOLD_FACE: float = 100.0  # 관상 — 조명·화장품 영향, 약간 낮게
THRESHOLD_DEFAULT: float = 100.0  # 기타 — 보수 디폴트


Domain = Literal["palm", "face", "default"]


# ─────────────────────────── cv2 가용성 점검 (graceful degradation) ───────────────────────────


def _cv2_available() -> bool:
    """cv2·numpy 설치 여부. 매 호출 시 import 시도 — 재현성 보장."""
    try:
        import cv2  # noqa: F401
        import numpy  # noqa: F401
        return True
    except ImportError:
        return False


# ─────────────────────────── 결과 dataclass ───────────────────────────


@dataclass(frozen=True)
class BlurResult:
    """L2 blur 검증 결과.

    Attributes:
        score: Laplacian variance 점수 (cv2 미설치 또는 디코드 실패 시 None).
        threshold: 적용된 임계값 (도메인별).
        passed: score >= threshold 여부. score=None 이면 None (판정 보류).
        domain: 적용 도메인 (palm·face·default).
        cv2_available: cv2 사용 가능 여부.
        message: 사용자 가이드 메시지 (인과 표현 0건, ADR-010 정합).
    """

    score: float | None
    threshold: float
    passed: bool | None
    domain: str
    cv2_available: bool
    message: str


# ─────────────────────────── 임계값 선택 ───────────────────────────


def _select_threshold(domain: Domain) -> float:
    """도메인별 임계값 반환 (보고서 §3.2 권장)."""
    if domain == "palm":
        return THRESHOLD_PALM
    if domain == "face":
        return THRESHOLD_FACE
    return THRESHOLD_DEFAULT


# ─────────────────────────── 핵심 함수 ───────────────────────────


def compute_blur_score(
    image_bytes: bytes,
    domain: Domain = "default",
) -> BlurResult:
    """이미지 바이트 → Laplacian variance blur 점수.

    Args:
        image_bytes: 이미지 raw 바이트 (JPEG·PNG 등).
        domain: 적용 도메인 (palm·face·default). 임계값 결정.

    Returns:
        BlurResult — score는 cv2 설치 + 디코드 성공 시 float, 아니면 None.

    설계:
        · 예외 발생 금지 (graceful degradation)
        · cv2 미설치 → score=None, passed=None, fallback 메시지
        · 디코드 실패 → score=None, passed=None, 명시 메시지
        · 성공 → score=float, passed=bool, 가이드 메시지
    """
    threshold = _select_threshold(domain)
    cv2_ok = _cv2_available()

    # 입력 검증 (graceful)
    if not isinstance(image_bytes, (bytes, bytearray)) or len(image_bytes) == 0:
        return BlurResult(
            score=None,
            threshold=threshold,
            passed=None,
            domain=domain,
            cv2_available=cv2_ok,
            message="이미지 데이터가 비어있어 품질 검증을 건너뜁니다. 다시 업로드해 주세요.",
        )

    # cv2 미설치 → graceful degradation
    if not cv2_ok:
        return BlurResult(
            score=None,
            threshold=threshold,
            passed=None,
            domain=domain,
            cv2_available=False,
            message="이미지 품질 정량 검증을 건너뜁니다. photo_guide의 텍스트 가이드를 참고해 주세요.",
        )

    # cv2 + numpy 로드
    try:
        import cv2
        import numpy as np
    except ImportError:
        return BlurResult(
            score=None,
            threshold=threshold,
            passed=None,
            domain=domain,
            cv2_available=False,
            message="이미지 품질 검증 라이브러리 로드에 실패했습니다.",
        )

    # 디코드 시도
    try:
        nparr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return BlurResult(
                score=None,
                threshold=threshold,
                passed=None,
                domain=domain,
                cv2_available=True,
                message="이미지 형식을 인식할 수 없습니다. JPEG 또는 PNG 형식으로 다시 업로드해 주세요.",
            )

        # Laplacian variance 산출 (표준 OpenCV)
        laplacian = cv2.Laplacian(img, cv2.CV_64F, ksize=3)
        variance = float(laplacian.var())
        passed = variance >= threshold

        if passed:
            message = "이미지 품질 검증을 통과했습니다."
        else:
            message = (
                "이미지가 흐려 분석이 어렵습니다. "
                "밝은 곳에서 손떨림 없이 다시 촬영해 주세요."
            )

        return BlurResult(
            score=variance,
            threshold=threshold,
            passed=passed,
            domain=domain,
            cv2_available=True,
            message=message,
        )

    except Exception:
        # graceful — 디코드·연산 예외 발생 시 None 반환
        return BlurResult(
            score=None,
            threshold=threshold,
            passed=None,
            domain=domain,
            cv2_available=True,
            message="이미지 품질 검증 중 오류가 발생했습니다. 다른 이미지로 다시 시도해 주세요.",
        )


# ─────────────────────────── Helper ───────────────────────────


def is_acceptable(image_bytes: bytes, domain: Domain = "default") -> bool:
    """단순 합격 여부 — graceful degradation 시 True (분석 진행 허용).

    설계:
        · cv2 미설치 → True (검증 스킵, 후속 모듈에 맡김)
        · 디코드 실패 → True (입력 검증은 L1·L3 책임)
        · score 산출 → score >= threshold
    """
    result = compute_blur_score(image_bytes, domain=domain)
    if result.passed is None:
        return True  # graceful — fallback 패턴
    return result.passed


__all__ = [
    "BlurResult",
    "Domain",
    "THRESHOLD_PALM",
    "THRESHOLD_FACE",
    "THRESHOLD_DEFAULT",
    "compute_blur_score",
    "is_acceptable",
]
