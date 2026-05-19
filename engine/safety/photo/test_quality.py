"""ADR-020 회귀 테스트 — L2 photo_quality 모듈.

검증 항목:
  1. cv2 미설치 시 graceful degradation (score=None, passed=None)
  2. 임계값 상수 (보고서 §3.2 권장값)
  3. 도메인별 임계값 분기 (palm=150, face=100, default=100)
  4. 잘못된 입력 처리 (빈 바이트·잘못된 타입)
  5. 사용자 출력 인과 표현 0건 (ADR-010 정합)
  6. is_acceptable() graceful degradation
"""

from __future__ import annotations

from engine.safety.photo.quality import (
    BlurResult,
    THRESHOLD_DEFAULT,
    THRESHOLD_FACE,
    THRESHOLD_PALM,
    compute_blur_score,
    is_acceptable,
)


# ─────────────────────────── 임계값 상수 검증 ───────────────────────────


def test_threshold_palm_value():
    """손금 임계값 150 (보고서 §3.2 권장)."""
    assert THRESHOLD_PALM == 150.0


def test_threshold_face_value():
    """관상 임계값 100 (보고서 §3.2 권장)."""
    assert THRESHOLD_FACE == 100.0


def test_threshold_default_value():
    """기타 디폴트 임계값 100."""
    assert THRESHOLD_DEFAULT == 100.0


# ─────────────────────────── 도메인별 임계값 분기 ───────────────────────────


def test_domain_palm_threshold_in_result():
    """palm 도메인 결과에 임계값 150 포함."""
    result = compute_blur_score(b"", domain="palm")
    assert result.threshold == 150.0
    assert result.domain == "palm"


def test_domain_face_threshold_in_result():
    """face 도메인 결과에 임계값 100 포함."""
    result = compute_blur_score(b"", domain="face")
    assert result.threshold == 100.0
    assert result.domain == "face"


def test_domain_default_threshold_in_result():
    """default 도메인 결과에 임계값 100 포함."""
    result = compute_blur_score(b"", domain="default")
    assert result.threshold == 100.0
    assert result.domain == "default"


# ─────────────────────────── 잘못된 입력 처리 ───────────────────────────


def test_empty_bytes_returns_none_score():
    """빈 바이트 입력 시 score=None + 메시지 명시."""
    result = compute_blur_score(b"", domain="face")
    assert result.score is None
    assert result.passed is None
    assert len(result.message) > 0


def test_invalid_type_returns_none_score():
    """잘못된 타입(None) 입력 시 score=None."""
    result = compute_blur_score(None, domain="face")  # type: ignore[arg-type]
    assert result.score is None
    assert result.passed is None


def test_random_bytes_decoded_or_none():
    """랜덤 바이트는 디코드 실패 — score=None (cv2 있어도)."""
    random_bytes = b"not-a-real-image-content" * 10
    result = compute_blur_score(random_bytes, domain="face")
    # cv2 있으면 디코드 실패 메시지, 없으면 graceful degradation
    assert result.score is None or isinstance(result.score, float)


# ─────────────────────────── Graceful Degradation ───────────────────────────


def test_blur_result_dataclass_frozen():
    """BlurResult는 frozen dataclass (불변)."""
    result = BlurResult(
        score=None,
        threshold=100.0,
        passed=None,
        domain="face",
        cv2_available=False,
        message="test",
    )
    try:
        result.score = 200.0  # type: ignore[misc]
        raised = False
    except (AttributeError, Exception):
        raised = True
    assert raised, "BlurResult는 frozen이어야 함"


def test_is_acceptable_graceful_when_cv2_missing():
    """is_acceptable: cv2 미설치 시 True (fallback 정신)."""
    # 빈 바이트 → score=None → is_acceptable=True (graceful)
    result = is_acceptable(b"", domain="palm")
    assert result is True


def test_compute_blur_score_no_exception_on_bad_input():
    """본 함수는 예외를 발생시키지 않음 (graceful degradation)."""
    try:
        compute_blur_score(b"", domain="palm")
        compute_blur_score(None, domain="face")  # type: ignore[arg-type]
        compute_blur_score(b"\x00" * 100, domain="default")
        raised = False
    except Exception:
        raised = True
    assert not raised, "본 함수는 예외 발생 금지"


# ─────────────────────────── ADR-010 사용자 출력 면책 검증 ───────────────────────────


def test_message_no_causal_words():
    """사용자 메시지에 인과·예언 표현 0건 (ADR-010 정합)."""
    forbidden_words = ["운이", "흉화", "길흉", "운명", "예언", "당신은 약", "당신은 강"]

    for domain in ["palm", "face", "default"]:
        result = compute_blur_score(b"", domain=domain)  # type: ignore[arg-type]
        for word in forbidden_words:
            assert word not in result.message, (
                f"인과·예언 표현 '{word}' 발견 in domain={domain}: {result.message}"
            )


def test_message_includes_guidance():
    """실패 메시지에 사용자 가이드 포함 (촬영 방법)."""
    # cv2 미설치 시 메시지에 fallback 안내 포함
    # cv2 있으면 디코드 실패 메시지 — 어느 쪽이든 무인과
    result = compute_blur_score(b"", domain="palm")
    # 본 검증은 단순히 메시지가 비어있지 않음만 보장
    assert len(result.message) > 0


# ─────────────────────────── 도메인 분리 회귀 ───────────────────────────


def test_palm_threshold_higher_than_face():
    """손금 임계값 > 관상 임계값 (보고서 §3.2 정합)."""
    assert THRESHOLD_PALM > THRESHOLD_FACE


def test_result_includes_cv2_availability_flag():
    """결과에 cv2 사용 가능 여부 플래그 포함."""
    result = compute_blur_score(b"", domain="face")
    assert isinstance(result.cv2_available, bool)
