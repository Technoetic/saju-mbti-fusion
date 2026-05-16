"""engine.safety.photo_guide — §7.2.9 사진 가이드 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 체크리스트 ───────────────────────────

def test_checklist_all_4_languages():
    from engine.safety.photo_guide import get_photo_checklist
    for lang in ("ko", "en", "ja", "zh"):
        items = get_photo_checklist(lang)
        assert isinstance(items, list)
        assert len(items) >= 4  # 정면·조명·가림·1인·안정 중 최소 4개
        for line in items:
            assert isinstance(line, str)
            assert len(line.strip()) > 0


def test_checklist_unknown_lang_falls_back_to_en():
    from engine.safety.photo_guide import get_photo_checklist, PHOTO_CHECKLIST_EN
    assert get_photo_checklist("fr") == PHOTO_CHECKLIST_EN
    assert get_photo_checklist("") == PHOTO_CHECKLIST_EN


def test_checklist_ko_uses_saguk_tone():
    """한국어 체크리스트는 사극풍 어미('~시게')를 사용해야 운학 도사 페르소나와 일치."""
    from engine.safety.photo_guide import PHOTO_CHECKLIST_KO
    saguk_hits = sum(1 for line in PHOTO_CHECKLIST_KO if "시게" in line)
    assert saguk_hits >= 3  # 5개 중 3개 이상은 ~시게로 끝나야 함


# ─────────────────────────── 에러별 안내 ───────────────────────────

def test_error_hint_known_codes_ko():
    from engine.safety.photo_guide import get_error_hint
    assert "허허" in get_error_hint("ERR_FACE_NOT_DETECTED", "ko")
    assert "한 분" in get_error_hint("ERR_FACE_MULTIPLE", "ko")
    assert get_error_hint("ERR_FACE_BACKLIT", "ko")  # 비어있지 않음


def test_error_hint_known_codes_en():
    from engine.safety.photo_guide import get_error_hint
    h = get_error_hint("ERR_FACE_NOT_DETECTED", "en")
    assert "face" in h.lower() or "detect" in h.lower()
    h = get_error_hint("ERR_FACE_MULTIPLE", "en")
    assert "one" in h.lower() or "person" in h.lower()


def test_error_hint_unknown_code_returns_empty():
    from engine.safety.photo_guide import get_error_hint
    assert get_error_hint("ERR_UNKNOWN_FUTURE_CODE", "ko") == ""


def test_error_hint_unknown_lang_falls_back_to_en():
    from engine.safety.photo_guide import get_error_hint
    h_fr = get_error_hint("ERR_FACE_NOT_DETECTED", "fr")
    h_en = get_error_hint("ERR_FACE_NOT_DETECTED", "en")
    assert h_fr == h_en


def test_all_9_error_codes_have_hints_in_all_4_languages():
    """§7.2.1 9종 에러코드는 ko/en/ja/zh 모두 비어있지 않아야 함."""
    from engine.safety.photo_guide import get_error_hint
    codes = [
        "ERR_FACE_NOT_DETECTED",
        "ERR_FACE_MULTIPLE",
        "ERR_FACE_NON_HUMAN",
        "ERR_FACE_BLUR",
        "ERR_FACE_PROFILE",
        "ERR_FACE_BACKLIT",
        "ERR_FACE_OCCLUDED",
        "WARN_FACE_FILTERED",
        "WARN_FACE_FLAT",
    ]
    for code in codes:
        for lang in ("ko", "en", "ja", "zh"):
            h = get_error_hint(code, lang)
            assert h, f"{code} ({lang}) 안내가 비어있음"


# ─────────────────────────── 재시도 팁 ───────────────────────────

def test_retry_tips_for_main_errors_ko():
    from engine.safety.photo_guide import get_retry_tips
    for code in ("ERR_FACE_NOT_DETECTED", "ERR_FACE_BACKLIT", "ERR_FACE_OCCLUDED",
                 "ERR_FACE_PROFILE", "ERR_FACE_BLUR"):
        tips = get_retry_tips(code, "ko")
        assert len(tips) >= 2, f"{code} 재시도 팁이 너무 적음"


def test_retry_tips_unknown_code_returns_empty_list():
    from engine.safety.photo_guide import get_retry_tips
    assert get_retry_tips("ERR_UNKNOWN_FUTURE_CODE", "ko") == []


def test_retry_tips_returns_independent_list():
    """반환값을 변형해도 내부 상태가 오염되면 안 됨."""
    from engine.safety.photo_guide import get_retry_tips
    a = get_retry_tips("ERR_FACE_NOT_DETECTED", "ko")
    a.append("MUTATION")
    b = get_retry_tips("ERR_FACE_NOT_DETECTED", "ko")
    assert "MUTATION" not in b


# ─────────────────────────── build_photo_guidance ───────────────────────────

def test_build_photo_guidance_no_error_returns_checklist_only():
    """error_code=None이면 체크리스트만 포함."""
    from engine.safety.photo_guide import build_photo_guidance
    g = build_photo_guidance(None, "ko")
    assert g["lang"] == "ko"
    assert "checklist" in g
    assert "error_code" not in g
    assert "hint" not in g
    assert "retry_tips" not in g


def test_build_photo_guidance_first_attempt_no_retry_tips():
    """retry_count=0이면 hint만, retry_tips 없음."""
    from engine.safety.photo_guide import build_photo_guidance
    g = build_photo_guidance("ERR_FACE_NOT_DETECTED", "ko", retry_count=0)
    assert g["error_code"] == "ERR_FACE_NOT_DETECTED"
    assert "hint" in g
    assert "retry_tips" not in g


def test_build_photo_guidance_retry_includes_tips():
    """retry_count>=1이면 retry_tips 포함."""
    from engine.safety.photo_guide import build_photo_guidance
    g = build_photo_guidance("ERR_FACE_BACKLIT", "ko", retry_count=1)
    assert g["error_code"] == "ERR_FACE_BACKLIT"
    assert "hint" in g
    assert "retry_tips" in g
    assert len(g["retry_tips"]) >= 2


def test_build_photo_guidance_unknown_lang_normalized():
    """미지원 언어는 영어로 정규화."""
    from engine.safety.photo_guide import build_photo_guidance
    g = build_photo_guidance("ERR_FACE_NOT_DETECTED", "fr", retry_count=1)
    assert g["lang"] == "en"


def test_build_photo_guidance_unknown_code_no_hint_key():
    """미상 에러코드는 hint/retry_tips 키 자체가 없어야 함."""
    from engine.safety.photo_guide import build_photo_guidance
    g = build_photo_guidance("ERR_UNKNOWN_FUTURE", "ko", retry_count=5)
    assert g["error_code"] == "ERR_UNKNOWN_FUTURE"
    assert "hint" not in g
    assert "retry_tips" not in g


def test_build_photo_guidance_all_languages_smoke():
    """4언어 × 주요 에러코드 조합이 모두 예외 없이 작동."""
    from engine.safety.photo_guide import build_photo_guidance
    for lang in ("ko", "en", "ja", "zh"):
        for code in ("ERR_FACE_NOT_DETECTED", "ERR_FACE_BACKLIT", "WARN_FACE_FLAT"):
            g = build_photo_guidance(code, lang, retry_count=1)
            assert g["lang"] == lang
            assert g["error_code"] == code
            assert g["checklist"]


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_photo_guide():
    import engine.safety as safety
    assert hasattr(safety, "get_photo_checklist")
    assert hasattr(safety, "get_error_hint")
    assert hasattr(safety, "get_retry_tips")
    assert hasattr(safety, "build_photo_guidance")
