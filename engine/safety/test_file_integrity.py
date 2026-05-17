"""engine.safety.file_integrity — 회귀 테스트.

ADR-010 + reports/input-guardrails.md L1 계층 검증.
순수 파이썬 매직 넘버 검증 (의존성 0).
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 매직 넘버 픽스처 ───────────────────────────

# 최소 유효 JPEG (FF D8 FF + EOI FF D9)
_VALID_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"

# 최소 PNG 시그니처 (실제 PNG 데이터 — 1x1 투명)
_VALID_PNG = bytes.fromhex(
    "89504e470d0a1a0a"  # PNG 시그니처 8바이트
    "0000000d49484452"  # IHDR chunk 길이+타입
    "0000000100000001"  # width=1, height=1
    "0806000000"        # bit depth=8, color type=6
    "1f15c4890000000d"  # CRC + 다음 chunk
    "49444154789c6300"
    "01000000050001"
    "0d0a2db40000000049454e44ae426082"
)

# 최소 WebP RIFF 헤더 (RIFF????WEBPVP8L...)
_VALID_WEBP = (
    b"RIFF" + b"\x24\x00\x00\x00" + b"WEBP"
    + b"VP8L\x18\x00\x00\x00\x2f\x00\x00\x00\x10\x07\x10\x11\x11\x88\x88\xfe\x07\x90\xff\xff\xff\xff\xff\xff\xff\xff\xff\x9f\x00"
)


# ─────────────────────────── 기본 검증 ───────────────────────────


def test_valid_jpeg_passes():
    from engine.safety.file_integrity import validate_image_bytes
    r = validate_image_bytes(_VALID_JPEG)
    assert r.valid is True
    assert r.detected_mime == "image/jpeg"


def test_valid_png_passes():
    from engine.safety.file_integrity import validate_image_bytes
    r = validate_image_bytes(_VALID_PNG)
    assert r.valid is True
    assert r.detected_mime == "image/png"


def test_valid_webp_passes():
    from engine.safety.file_integrity import validate_image_bytes
    r = validate_image_bytes(_VALID_WEBP)
    assert r.valid is True
    assert r.detected_mime == "image/webp"


# ─────────────────────────── 거부 케이스 ───────────────────────────


def test_empty_data_rejected():
    from engine.safety.file_integrity import validate_image_bytes
    r = validate_image_bytes(b"")
    assert r.valid is False
    assert r.error_code == "empty_file"


def test_oversized_rejected():
    from engine.safety.file_integrity import validate_image_bytes
    big = b"\xff\xd8\xff" + b"\x00" * (6 * 1024 * 1024)
    r = validate_image_bytes(big, max_bytes=5 * 1024 * 1024)
    assert r.valid is False
    assert r.error_code == "size_exceeded"


def test_text_disguised_as_jpg_rejected():
    """확장자만 .jpg인 텍스트 파일 — 매직 넘버 검증으로 차단."""
    from engine.safety.file_integrity import validate_image_bytes
    fake = b"This is a text file pretending to be a JPEG."
    r = validate_image_bytes(fake, claimed_mime="image/jpeg")
    assert r.valid is False
    assert r.error_code == "unknown_format"


def test_gif_rejected():
    """GIF는 허용 목록에 없음."""
    from engine.safety.file_integrity import validate_image_bytes
    gif = b"GIF89a" + b"\x00" * 20
    r = validate_image_bytes(gif)
    assert r.valid is False
    assert r.error_code == "unknown_format"


def test_executable_rejected():
    """Windows PE 헤더 (MZ) — 실행 파일은 차단."""
    from engine.safety.file_integrity import validate_image_bytes
    pe = b"MZ\x90\x00" + b"\x00" * 100
    r = validate_image_bytes(pe)
    assert r.valid is False
    assert r.error_code == "unknown_format"


def test_mime_mismatch_rejected():
    """클라이언트는 PNG라 주장하나 실제는 JPEG."""
    from engine.safety.file_integrity import validate_image_bytes
    r = validate_image_bytes(_VALID_JPEG, claimed_mime="image/png")
    assert r.valid is False
    assert r.error_code == "mime_mismatch"


def test_mime_match_passes():
    """클라이언트 MIME과 매직 넘버 일치."""
    from engine.safety.file_integrity import validate_image_bytes
    r = validate_image_bytes(_VALID_JPEG, claimed_mime="image/jpeg")
    assert r.valid is True


# ─────────────────────────── base64 인터페이스 ───────────────────────────


def test_raw_base64_jpeg():
    from engine.safety.file_integrity import validate_image_base64
    b64 = base64.b64encode(_VALID_JPEG).decode()
    r = validate_image_base64(b64)
    assert r.valid is True
    assert r.detected_mime == "image/jpeg"


def test_data_url_png_with_matching_mime():
    from engine.safety.file_integrity import validate_image_base64
    b64 = base64.b64encode(_VALID_PNG).decode()
    data_url = f"data:image/png;base64,{b64}"
    r = validate_image_base64(data_url)
    assert r.valid is True
    assert r.detected_mime == "image/png"


def test_data_url_mime_mismatch():
    """data URL은 webp라 주장하나 실제 JPEG."""
    from engine.safety.file_integrity import validate_image_base64
    b64 = base64.b64encode(_VALID_JPEG).decode()
    data_url = f"data:image/webp;base64,{b64}"
    r = validate_image_base64(data_url)
    assert r.valid is False
    assert r.error_code == "mime_mismatch"


def test_invalid_base64_rejected():
    from engine.safety.file_integrity import validate_image_base64
    r = validate_image_base64("not-valid-base64-!!!")
    assert r.valid is False
    assert r.error_code == "invalid_encoding"


def test_invalid_data_url_format():
    """data: 접두사 있으나 콤마 없음."""
    from engine.safety.file_integrity import validate_image_base64
    r = validate_image_base64("data:image/jpeg;base64NOCOMMA")
    assert r.valid is False
    assert r.error_code == "invalid_data_url"


# ─────────────────────────── 사용자 메시지 ───────────────────────────


def test_reason_is_user_facing_korean():
    """실패 메시지는 사용자에게 노출되므로 한국어 + 정중함."""
    from engine.safety.file_integrity import validate_image_bytes
    r = validate_image_bytes(b"")
    assert r.valid is False
    assert r.reason  # 비어있지 않음
    # 한국어 포함 검증 (가/나/다 등 한글 음절)
    assert any("가" <= ch <= "힣" for ch in r.reason)


def test_no_medical_or_legal_claim_in_reason():
    """L1 모듈은 단순 파일 검증 — 의료·법률 자문 표현 없음."""
    from engine.safety.file_integrity import validate_image_bytes
    forbidden = ["진단", "치료", "법적", "의료", "변호사"]
    for sample in (b"", b"GIF89a", b"MZ\x90\x00"):
        r = validate_image_bytes(sample)
        for w in forbidden:
            assert w not in r.reason
