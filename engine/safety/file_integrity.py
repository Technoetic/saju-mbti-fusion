"""파일 무결성 검증 — 매직 넘버 + 크기 + MIME 3중 검증.

본 모듈은 base64 또는 바이트 데이터를 받아 다음을 검증:
  1. 크기 한계 (기본 5MB)
  2. 파일 헤더 매직 넘버 (JPEG/PNG/WebP 시그니처)
  3. 매직 넘버와 클라이언트가 주장한 MIME 일치

ADR-010 사실성 분리 원칙 + reports/input-guardrails.md (L1 계층) 본문화.

순수 파이썬 구현 — 외부 라이브러리(python-magic, libmagic) 의존 없음.
헤더 바이트 직접 비교로 의존성·빌드 복잡도 0.

본 모듈은 face_reading / palm_reading 등 이미지 업로드 경로에서 LLM 호출
이전에 호출되어야 한다.
"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass


# ─────────────────────────── 정책 상수 ───────────────────────────

# 기본 5MB — 보고서 권장값. SaaS 운영 시 트래픽 데이터로 조정 가능.
DEFAULT_MAX_BYTES = 5 * 1024 * 1024

# 허용 MIME — face_reading·palm_reading이 모두 지원하는 포맷
ALLOWED_MIMES = frozenset({"image/jpeg", "image/png", "image/webp"})


# ─────────────────────────── 매직 넘버 시그니처 ───────────────────────────
# 파일 헤더 첫 N 바이트로 실제 포맷 식별. 확장자·MIME 조작 우회 차단.
#
# JPEG:  FF D8 FF (3 bytes)
# PNG:   89 50 4E 47 0D 0A 1A 0A (8 bytes)
# WebP:  RIFF????WEBP (12 bytes — bytes 0-3=RIFF, 8-11=WEBP)
# HEIC/HEIF/AVIF: ISO BMFF ftyp box (bytes 4-7=ftyp, 8-11=brand)

_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_WEBP_RIFF = b"RIFF"
_WEBP_WEBP = b"WEBP"

# HEIC/AVIF — ISO BMFF 컨테이너 brand 목록 (ADR-035 Phase 3회차)
_HEIC_BRANDS = frozenset({b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis", b"hevm", b"hevs"})
_HEIF_BRANDS = frozenset({b"mif1", b"msf1", b"miaf", b"miag"})
_AVIF_BRANDS = frozenset({b"avif", b"avis", b"MA1B", b"MA1A"})


def _detect_mime_from_magic(data: bytes) -> str | None:
    """파일 헤더 바이트만으로 실제 MIME 식별. 알 수 없으면 None.

    ADR-035: HEIC/AVIF도 식별해 명확한 오류 메시지 제공.
    """
    if len(data) < 3:
        return None
    if data.startswith(_JPEG_MAGIC):
        return "image/jpeg"
    if len(data) >= 8 and data.startswith(_PNG_MAGIC):
        return "image/png"
    if (
        len(data) >= 12
        and data[0:4] == _WEBP_RIFF
        and data[8:12] == _WEBP_WEBP
    ):
        return "image/webp"
    # ISO BMFF 컨테이너 (HEIC/HEIF/AVIF) — ftyp box 감지
    if len(data) >= 12 and data[4:8] == b"ftyp":
        brand = data[8:12]
        if brand in _HEIC_BRANDS:
            return "image/heic"
        if brand in _HEIF_BRANDS:
            return "image/heif"
        if brand in _AVIF_BRANDS:
            return "image/avif"
    return None


# ─────────────────────────── 결과 모델 ───────────────────────────


@dataclass(frozen=True)
class IntegrityResult:
    """파일 무결성 검증 결과.

    Attributes:
        valid: 모든 검증 통과 여부.
        reason: 실패 사유 (사용자 노출용 한국어). valid=True면 빈 문자열.
        detected_mime: 매직 넘버로 식별된 실제 MIME. 식별 실패 시 None.
        size_bytes: 검증된 파일 바이트 크기.
        error_code: 시스템 로그용 식별자 (사용자 노출 X).
    """

    valid: bool
    reason: str
    detected_mime: str | None
    size_bytes: int
    error_code: str


# ─────────────────────────── 검증 메인 ───────────────────────────


def validate_image_bytes(
    data: bytes,
    *,
    claimed_mime: str | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> IntegrityResult:
    """원시 바이트 데이터를 검증한다.

    Args:
        data: 검증할 이미지 바이트.
        claimed_mime: 클라이언트가 주장한 MIME (선택). 매직 넘버와 대조.
        max_bytes: 허용 최대 크기.

    Returns:
        IntegrityResult — valid=True이면 안전, False이면 reason에 사유.
    """
    size = len(data)

    if size == 0:
        return IntegrityResult(
            valid=False,
            reason="빈 파일입니다. 이미지를 다시 업로드해주세요.",
            detected_mime=None,
            size_bytes=0,
            error_code="empty_file",
        )

    if size > max_bytes:
        mb = max_bytes // (1024 * 1024)
        return IntegrityResult(
            valid=False,
            reason=f"파일 크기는 {mb}MB를 초과할 수 없습니다.",
            detected_mime=None,
            size_bytes=size,
            error_code="size_exceeded",
        )

    detected = _detect_mime_from_magic(data)

    if detected is None:
        return IntegrityResult(
            valid=False,
            reason="지원하지 않는 이미지 형식입니다. JPG, PNG, WEBP만 가능합니다.",
            detected_mime=None,
            size_bytes=size,
            error_code="unknown_format",
        )

    if detected not in ALLOWED_MIMES:
        # HEIC/AVIF — 구체적 안내 메시지
        if detected in ("image/heic", "image/heif"):
            reason = (
                "HEIC 형식은 지원하지 않습니다. "
                "사진 앱에서 JPG로 내보내기 후 업로드해주세요."
            )
        elif detected == "image/avif":
            reason = (
                "AVIF 형식은 지원하지 않습니다. "
                "JPG 또는 PNG로 변환 후 업로드해주세요."
            )
        else:
            reason = "지원하지 않는 이미지 형식입니다. JPG, PNG, WEBP만 가능합니다."
        return IntegrityResult(
            valid=False,
            reason=reason,
            detected_mime=detected,
            size_bytes=size,
            error_code="format_not_allowed",
        )

    # 클라이언트 MIME 주장과 실제 매직 넘버 대조 (선택적)
    if claimed_mime is not None and claimed_mime != detected:
        return IntegrityResult(
            valid=False,
            reason="파일 형식이 일치하지 않습니다. 올바른 이미지를 업로드해주세요.",
            detected_mime=detected,
            size_bytes=size,
            error_code="mime_mismatch",
        )

    return IntegrityResult(
        valid=True,
        reason="",
        detected_mime=detected,
        size_bytes=size,
        error_code="",
    )


def validate_image_base64(
    image_b64: str,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> IntegrityResult:
    """data URL 또는 raw base64 문자열을 받아 검증.

    `data:image/jpeg;base64,...` 형식이면 MIME을 claimed_mime으로 사용.
    raw base64만 들어오면 매직 넘버만으로 식별.

    base64 디코딩 실패는 invalid_encoding 에러로 반환.
    """
    claimed_mime: str | None = None
    raw_b64 = image_b64

    # data URL 파싱
    if image_b64.startswith("data:"):
        try:
            header, raw_b64 = image_b64.split(",", 1)
            # header: data:image/jpeg;base64
            mime_part = header[5:].split(";")[0].strip()
            claimed_mime = mime_part or None
        except ValueError:
            return IntegrityResult(
                valid=False,
                reason="이미지 데이터 형식이 올바르지 않습니다.",
                detected_mime=None,
                size_bytes=0,
                error_code="invalid_data_url",
            )

    try:
        data = base64.b64decode(raw_b64, validate=True)
    except (binascii.Error, ValueError):
        return IntegrityResult(
            valid=False,
            reason="이미지 데이터를 읽을 수 없습니다.",
            detected_mime=None,
            size_bytes=0,
            error_code="invalid_encoding",
        )

    return validate_image_bytes(
        data,
        claimed_mime=claimed_mime,
        max_bytes=max_bytes,
    )
