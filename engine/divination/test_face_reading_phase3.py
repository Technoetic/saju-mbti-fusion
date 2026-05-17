"""face_reading Phase 3회차 신규 회귀 테스트 — ADR-035.

항목 1+4: _postprocess_remove_fate_mapping 운명/학파/사상체질 필터
항목 2:   _detect_image_mime HEIC/AVIF 감지
항목 3:   web/server.py POST /api/face/reading 413 응답 (base64 크기 초과)
항목 5:   _hash_payload question 제외 캐시 키

LLM 호출 없는 순수 로직 테스트.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 항목 1+4: 후처리 필터 ───────────────────────────


def test_postprocess_clean_text_unchanged():
    """운명 키워드 없는 정상 문장 — 변경 없어야 함."""
    from engine.divination.face_reading import _postprocess_remove_fate_mapping
    text = "허허, 이마가 넓고 평평한 결이로구먼. 눈빛이 또렷한 기운이로다."
    result = _postprocess_remove_fate_mapping(text)
    assert "이마가 넓고" in result
    assert "눈빛이 또렷한" in result


def test_postprocess_removes_daewun():
    """'대운' 포함 문장 제거."""
    from engine.divination.face_reading import _postprocess_remove_fate_mapping
    text = "허허, 이마가 넓구먼.\n대운이 트이는 상이로다.\n눈빛이 맑다."
    result = _postprocess_remove_fate_mapping(text)
    assert "대운이 트이는" not in result
    assert "이마가 넓구먼" in result


def test_postprocess_removes_hakmunbok():
    """'학문복' 포함 문장 제거."""
    from engine.divination.face_reading import _postprocess_remove_fate_mapping
    text = "이마가 넓으니 학문복이 있다네.\n코는 곧은 결이로다."
    result = _postprocess_remove_fate_mapping(text)
    assert "학문복" not in result
    assert "코는 곧은" in result


def test_postprocess_removes_gilfung():
    """'길흉' 포함 문장 제거."""
    from engine.divination.face_reading import _postprocess_remove_fate_mapping
    text = "길흉화복을 헤아리기 어렵구먼.\n얼굴 윤곽은 둥근 결이로세."
    result = _postprocess_remove_fate_mapping(text)
    assert "길흉화복" not in result
    assert "얼굴 윤곽은" in result


def test_postprocess_removes_sasang_constitution():
    """사상체질 어휘(태양인/태음인/소양인/소음인/사상체질) 포함 줄 제거."""
    from engine.divination.face_reading import _postprocess_remove_fate_mapping
    for term in ["태양인", "태음인", "소양인", "소음인", "사상체질"]:
        # 사상체질 포함 줄과 정상 줄을 개행으로 분리
        text = f"그대는 {term}의 형상이로구먼.\n눈이 또렷하다."
        result = _postprocess_remove_fate_mapping(text)
        assert term not in result, f"{term} 이 제거되어야 함"
        assert "눈이 또렷하다" in result, "정상 문장은 유지되어야 함"


def test_postprocess_removes_prophecy_ending():
    """단정 예언 어미 '~의 운이 있다' 제거."""
    from engine.divination.face_reading import _postprocess_remove_fate_mapping
    text = "재물의 운이 있도다.\n코가 곧은 결이로세."
    result = _postprocess_remove_fate_mapping(text)
    assert "운이 있도다" not in result
    assert "코가 곧은" in result


def test_postprocess_removes_school_citation():
    """마의상법/신상전편/달마상법 인용 제거."""
    from engine.divination.face_reading import _postprocess_remove_fate_mapping
    for school in ["마의상법", "신상전편", "달마상법"]:
        text = f"{school}에 이르길 이마가 넓으면 좋다 하였네.\n눈은 맑구나."
        result = _postprocess_remove_fate_mapping(text)
        assert school not in result, f"{school} 이 제거되어야 함"


def test_postprocess_removes_time_fate():
    """초년/중년/말년 운 조합 제거."""
    from engine.divination.face_reading import _postprocess_remove_fate_mapping
    text = "초년에 복록이 풍성할 상이로다.\n눈썹은 짙은 결이로세."
    result = _postprocess_remove_fate_mapping(text)
    assert "초년" not in result or "복록" not in result
    assert "눈썹은 짙은" in result


def test_postprocess_adds_disclaimer_when_removed():
    """운명 키워드 제거 시 자동 면책 추가."""
    from engine.divination.face_reading import _postprocess_remove_fate_mapping, _FATE_DISCLAIMER
    text = "대운이 크게 열릴 상이로다."
    result = _postprocess_remove_fate_mapping(text)
    assert _FATE_DISCLAIMER.strip() in result or "[이 풀이는 얼굴 시각 형상 묘사" in result


def test_postprocess_no_disclaimer_when_nothing_removed():
    """운명 키워드 없는 텍스트 — 면책 추가 없음."""
    from engine.divination.face_reading import _postprocess_remove_fate_mapping, _FATE_DISCLAIMER
    text = "허허, 이마가 넓고 고른 결이로구먼. 눈빛이 또렷하고 맑다."
    result = _postprocess_remove_fate_mapping(text)
    assert _FATE_DISCLAIMER not in result


def test_postprocess_empty_string():
    """빈 문자열 입력 — 빈 문자열 반환."""
    from engine.divination.face_reading import _postprocess_remove_fate_mapping
    assert _postprocess_remove_fate_mapping("") == ""


# ─────────────────────────── 항목 4: 시스템 프롬프트 사상체질 금지 ───────────────────────────


def test_stage1_system_forbids_sasang_terms():
    """Stage 1 시스템 프롬프트에 사상체질 4상 + 사상체질 어휘 금지 명시."""
    from engine.divination.face_reading import _STAGE1_OBJECTIVE_SYSTEM
    for term in ["태양인", "태음인", "소양인", "소음인", "사상체질"]:
        assert term in _STAGE1_OBJECTIVE_SYSTEM, f"Stage 1 시스템에 '{term}' 금지 명시 필요"


def test_stage2_system_forbids_sasang_terms():
    """Stage 2 시스템 프롬프트에 사상체질 어휘 금지 명시."""
    from engine.divination.face_reading import _STAGE2_PERSONA_SYSTEM
    for term in ["태양인", "태음인", "소양인", "소음인", "사상체질"]:
        assert term in _STAGE2_PERSONA_SYSTEM, f"Stage 2 시스템에 '{term}' 금지 명시 필요"


def test_stage2_system_retains_existing_fate_bans():
    """기존 운명 매핑 금지 어휘 유지 확인."""
    from engine.divination.face_reading import _STAGE2_PERSONA_SYSTEM
    for term in ["대운", "학문복", "재물복", "길흉", "초년", "중년", "말년"]:
        assert term in _STAGE2_PERSONA_SYSTEM, f"Stage 2 기존 금지 어휘 '{term}' 누락"


# ─────────────────────────── 항목 2: HEIC/AVIF 감지 ───────────────────────────


def test_detect_mime_heic():
    """HEIC base64 → 'image/heic' 감지."""
    import base64
    from engine.divination.face_reading import _detect_image_mime

    # ISO BMFF ftyp box: box_size(4B) + "ftyp"(4B) + brand(4B) + version(4B)
    # brand = b"heic"
    heic_bytes = b"\x00\x00\x00\x18ftyp" + b"heic" + b"\x00\x00\x00\x00"
    b64 = base64.b64encode(heic_bytes).decode()
    result = _detect_image_mime(b64)
    assert result == "image/heic", f"Expected image/heic, got {result}"


def test_detect_mime_avif():
    """AVIF base64 → 'image/avif' 감지."""
    import base64
    from engine.divination.face_reading import _detect_image_mime

    avif_bytes = b"\x00\x00\x00\x18ftyp" + b"avif" + b"\x00\x00\x00\x00"
    b64 = base64.b64encode(avif_bytes).decode()
    result = _detect_image_mime(b64)
    assert result == "image/avif", f"Expected image/avif, got {result}"


def test_detect_mime_heif():
    """HEIF (mif1 brand) base64 → 'image/heif' 감지."""
    import base64
    from engine.divination.face_reading import _detect_image_mime

    heif_bytes = b"\x00\x00\x00\x18ftyp" + b"mif1" + b"\x00\x00\x00\x00"
    b64 = base64.b64encode(heif_bytes).decode()
    result = _detect_image_mime(b64)
    assert result == "image/heif", f"Expected image/heif, got {result}"


def test_detect_mime_png_still_works():
    """HEIC/AVIF 추가 후 PNG 감지 회귀 방지."""
    from engine.divination.face_reading import _detect_image_mime
    # PNG base64 매직
    assert _detect_image_mime("iVBORw0KGgo=") == "image/png"


def test_detect_mime_jpeg_still_works():
    """HEIC/AVIF 추가 후 JPEG 감지 회귀 방지."""
    from engine.divination.face_reading import _detect_image_mime
    assert _detect_image_mime("/9j/4AAQ") == "image/jpeg"


def test_file_integrity_heic_rejected_with_message():
    """file_integrity가 HEIC를 format_not_allowed로 거부 + 한국어 안내 메시지."""
    import base64
    from engine.safety.file_integrity import validate_image_bytes

    heic_bytes = b"\x00\x00\x00\x18ftyp" + b"heic" + b"\x00\x00\x00\x00" + b"\x00" * 20
    result = validate_image_bytes(heic_bytes)
    assert result.valid is False
    assert result.error_code == "format_not_allowed"
    assert result.detected_mime == "image/heic"
    assert "HEIC" in result.reason or "JPG" in result.reason


def test_file_integrity_avif_rejected_with_message():
    """file_integrity가 AVIF를 format_not_allowed로 거부 + 한국어 안내 메시지."""
    import base64
    from engine.safety.file_integrity import validate_image_bytes

    avif_bytes = b"\x00\x00\x00\x18ftyp" + b"avif" + b"\x00\x00\x00\x00" + b"\x00" * 20
    result = validate_image_bytes(avif_bytes)
    assert result.valid is False
    assert result.error_code == "format_not_allowed"
    assert result.detected_mime == "image/avif"
    assert "AVIF" in result.reason or "JPG" in result.reason


# ─────────────────────────── 항목 3: 서버 413 응답 ───────────────────────────


def test_face_reading_oversized_returns_413():
    """5MB 초과 base64 → HTTP 413 응답."""
    import sys
    import os

    # FastAPI TestClient 는 starlette 필요. 없으면 스킵
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        import pytest
        pytest.skip("fastapi[testclient] 미설치")

    # minimal server import
    try:
        from web.server import PersonalityAPIServer
    except Exception:
        import pytest
        pytest.skip("web.server import 실패 — 환경 의존")

    server = PersonalityAPIServer()
    client = TestClient(server.app, raise_server_exceptions=False)

    # 7MB + 1 byte base64 문자열 (5MB 초과)
    oversized_b64 = "A" * (7 * 1024 * 1024 + 1)
    payload = {"image_base64": oversized_b64}
    resp = client.post("/api/face/reading", json=payload)
    assert resp.status_code == 413, f"Expected 413, got {resp.status_code}"


def test_face_reading_normal_size_does_not_413():
    """정상 크기 base64 → 413 아님 (크기 검사 통과, 이후는 LLM 오류 가능)."""
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        import pytest
        pytest.skip("fastapi[testclient] 미설치")

    try:
        from web.server import PersonalityAPIServer
    except Exception:
        import pytest
        pytest.skip("web.server import 실패 — 환경 의존")

    server = PersonalityAPIServer()
    client = TestClient(server.app, raise_server_exceptions=False)

    # 소형 base64 (100 chars — 크기 검사는 통과)
    small_b64 = "A" * 100
    payload = {"image_base64": small_b64}
    resp = client.post("/api/face/reading", json=payload)
    # 413이 아니면 성공 (400/500은 다른 이유로 발생 가능)
    assert resp.status_code != 413, f"소형 입력에서 413 발생 — 버그"


# ─────────────────────────── 항목 5: 캐시 키 question 제외 ───────────────────────────


def test_hash_payload_ignores_question():
    """question이 달라도 같은 해시 — 캐시 키에서 question 제외 확인."""
    from engine.divination.face_reading import _hash_payload
    h1 = _hash_payload("img", 30, "남성", "재물운 알려주세요", None)
    h2 = _hash_payload("img", 30, "남성", None, None)
    assert h1 == h2, "question 제외 캐시 키: question 달라도 동일 해시여야 함"


def test_hash_payload_ignores_question_with_metrics():
    """메트릭 있을 때도 question 제외 확인."""
    from engine.divination.face_reading import _hash_payload
    metrics = {"alar_ratio": 0.35}
    h1 = _hash_payload("img", 25, "여성", "성격 분석해주세요", metrics)
    h2 = _hash_payload("img", 25, "여성", "운세 알려주세요", metrics)
    assert h1 == h2, "question 제외 캐시 키: 메트릭 있을 때도 question 무시"


def test_hash_payload_different_image_different_hash():
    """이미지가 다르면 여전히 다른 해시."""
    from engine.divination.face_reading import _hash_payload
    h1 = _hash_payload("img-A", 30, "남성", "질문", None)
    h2 = _hash_payload("img-B", 30, "남성", "질문", None)
    assert h1 != h2


def test_hash_payload_different_age_different_hash():
    """나이가 다르면 다른 해시."""
    from engine.divination.face_reading import _hash_payload
    h1 = _hash_payload("img", 25, "남성", None, None)
    h2 = _hash_payload("img", 35, "남성", None, None)
    assert h1 != h2


def test_hash_payload_different_gender_different_hash():
    """성별이 다르면 다른 해시."""
    from engine.divination.face_reading import _hash_payload
    h1 = _hash_payload("img", 30, "남성", None, None)
    h2 = _hash_payload("img", 30, "여성", None, None)
    assert h1 != h2
