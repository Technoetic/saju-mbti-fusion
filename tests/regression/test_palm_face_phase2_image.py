"""ADR-081·082 회귀 — palm·face Phase 2 사진 입력 처리.

content/reading에서 imageB64 입력 시 Phase 2 (Vision 풀 호출) 가이드 명시.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SERVER_PY = ROOT / "web" / "server.py"


def _src() -> str:
    return SERVER_PY.read_text(encoding="utf-8")


# ── ADR-081 palm Phase 2 ────────────────────────────────


def test_palm_image_field_extracted():
    """palm 분기가 imageB64 필드 추출."""
    src = _src()
    assert 'palm_image_b64 = (fields.get("imageB64") or fields.get("image") or "").strip()' in src


def test_palm_image_branch_uses_phase2():
    """palm imageB64 입력 시 Phase 2 분기 활성."""
    src = _src()
    assert "if palm_image_b64:" in src
    assert "Phase 2 — engine/divination/palm/reading.generate_palm_reading" in src


def test_palm_image_endpoint_guidance():
    """palm Phase 2 분기가 별도 엔드포인트 사용 가이드 명시."""
    src = _src()
    assert "/api/palm/read" in src


# ── ADR-082 face Phase 2 ────────────────────────────────


def test_face_image_field_extracted():
    """face 분기가 imageB64 필드 추출."""
    src = _src()
    assert 'face_image_b64 = (fields.get("imageB64") or fields.get("image") or "").strip()' in src


def test_face_image_branch_uses_phase2():
    """face imageB64 입력 시 Phase 2 분기 활성."""
    src = _src()
    assert "if face_image_b64:" in src
    assert "Phase 2 — engine/divination/face/reading.generate_face_reading" in src


def test_face_image_endpoint_guidance():
    """face Phase 2 분기가 별도 엔드포인트 사용 가이드 명시."""
    src = _src()
    assert "/api/face/read" in src


# ── Phase 1 fallback 정합 ────────────────────────────────


def test_palm_phase1_fallback_when_no_image():
    """palm 사진 미입력 시 Phase 1 (학파/라벨 풀) 유지."""
    src = _src()
    # else 분기에 학파 6개 + 4 보조선 라벨 풀
    assert "else:" in src
    assert "사진 미입력 시 라이브 분류 불가" in src


def test_face_phase1_fallback_when_no_image():
    """face 사진 미입력 시 Phase 1 (학파·삼정·12궁) 유지."""
    src = _src()
    assert "구조 인용만 허용" in src


# ── 결정론 엔진 함수 정합 ──────────────────────────────


def test_generate_palm_reading_signature():
    """generate_palm_reading 함수 시그니처 정합 (image_b64 입력)."""
    from engine.divination.palm.reading import generate_palm_reading
    import inspect
    sig = inspect.signature(generate_palm_reading)
    assert "image_b64" in sig.parameters


def test_generate_face_reading_signature():
    """generate_face_reading 함수 시그니처 정합 (image_b64 입력)."""
    from engine.divination.face.reading import generate_face_reading
    import inspect
    sig = inspect.signature(generate_face_reading)
    assert "image_b64" in sig.parameters


def test_palm_reading_validates_image_required():
    """generate_palm_reading이 image_b64 빈 입력 거절."""
    from engine.divination.palm.reading import generate_palm_reading
    import pytest
    with pytest.raises((ValueError, Exception)):
        generate_palm_reading(image_b64="")


def test_face_reading_validates_image_required():
    """generate_face_reading이 image_b64 빈 입력 거절."""
    from engine.divination.face.reading import generate_face_reading
    import pytest
    with pytest.raises((ValueError, Exception)):
        generate_face_reading(image_b64="")


# ── ADR-006 단정 매핑 부재 ─────────────────────────────


def test_palm_disclaimers_in_module():
    """palm 모듈 disclaimer가 운명·재물·결혼 단정 부재 명시."""
    from engine.divination.palm.knowledge import _DISCLAIMER_BASE
    assert "운명" in _DISCLAIMER_BASE
    assert "인과 매핑 X" in _DISCLAIMER_BASE


def test_face_palace_no_fate_mapping():
    """face TwelvePalace dataclass에 fate_mapping 필드 부재 (ADR-006)."""
    from engine.divination.face.knowledge import TwelvePalace
    import dataclasses
    fields = {f.name for f in dataclasses.fields(TwelvePalace)}
    # 의도적 부재
    assert "fate_mapping" not in fields
    assert "운명" not in " ".join(fields)
