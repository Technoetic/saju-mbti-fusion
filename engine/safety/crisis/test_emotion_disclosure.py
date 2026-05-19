"""engine.safety.crisis.emotion_disclosure — EU AI Act §50(3) 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 지역 판정 ───────────────────────────

def test_eu_aggregate_code_required():
    from engine.safety.crisis.emotion_disclosure import is_emotion_disclosure_required
    assert is_emotion_disclosure_required("EU") is True


def test_eu_member_states_required():
    from engine.safety.crisis.emotion_disclosure import is_emotion_disclosure_required
    for code in ("DE", "FR", "IT", "ES", "NL", "PL", "SE", "FI", "AT"):
        assert is_emotion_disclosure_required(code) is True


def test_uk_recommended_not_required():
    from engine.safety.crisis.emotion_disclosure import (
        is_emotion_disclosure_required,
        is_emotion_disclosure_recommended,
    )
    assert is_emotion_disclosure_required("UK") is False
    assert is_emotion_disclosure_required("GB") is False
    assert is_emotion_disclosure_recommended("UK") is True
    assert is_emotion_disclosure_recommended("GB") is True


def test_non_eu_neither_required_nor_recommended():
    from engine.safety.crisis.emotion_disclosure import (
        is_emotion_disclosure_required,
        is_emotion_disclosure_recommended,
    )
    for code in ("KR", "JP", "CN", "US-CA", "US-IL"):
        assert is_emotion_disclosure_required(code) is False
        assert is_emotion_disclosure_recommended(code) is False


def test_none_and_empty_region_not_required():
    from engine.safety.crisis.emotion_disclosure import is_emotion_disclosure_required
    assert is_emotion_disclosure_required(None) is False
    assert is_emotion_disclosure_required("") is False


def test_case_insensitive_region():
    from engine.safety.crisis.emotion_disclosure import is_emotion_disclosure_required
    assert is_emotion_disclosure_required("eu") is True
    assert is_emotion_disclosure_required(" de ") is True  # strip


# ─────────────────────────── 고지문 ───────────────────────────

def test_disclosure_4_languages():
    from engine.safety.crisis.emotion_disclosure import build_emotion_disclosure
    for lang in ("ko", "en", "ja", "zh"):
        d = build_emotion_disclosure(lang)
        assert isinstance(d, str)
        assert len(d) > 30


def test_disclosure_unknown_lang_falls_back_to_en():
    from engine.safety.crisis.emotion_disclosure import build_emotion_disclosure
    assert build_emotion_disclosure("fr") == build_emotion_disclosure("en")


def test_disclosure_en_cites_legal_article():
    from engine.safety.crisis.emotion_disclosure import build_emotion_disclosure
    en = build_emotion_disclosure("en")
    assert "EU AI Act" in en
    assert "Article 50" in en or "Art.50" in en or "50(3)" in en


def test_disclosure_ko_uses_saguk_tone():
    from engine.safety.crisis.emotion_disclosure import build_emotion_disclosure
    ko = build_emotion_disclosure("ko")
    # 사극풍 — "이 늙은이" 또는 "그대"
    assert "늙은이" in ko or "그대" in ko


def test_disclosure_starts_with_double_newline():
    """응답 본문에 그대로 concat 가능하도록 \\n\\n으로 시작."""
    from engine.safety.crisis.emotion_disclosure import build_emotion_disclosure
    for lang in ("ko", "en", "ja", "zh"):
        assert build_emotion_disclosure(lang).startswith("\n\n")


# ─────────────────────────── inject ───────────────────────────

def test_inject_appends_for_eu():
    from engine.safety.crisis.emotion_disclosure import inject_emotion_disclosure
    base = "허허, 그대의 상을 살피니..."
    out = inject_emotion_disclosure(base, region="DE", lang="en")
    assert out.startswith(base)
    assert "EU AI Act" in out


def test_inject_appends_for_uk_recommended():
    from engine.safety.crisis.emotion_disclosure import inject_emotion_disclosure
    base = "허허, 그대의 상을 살피니..."
    out = inject_emotion_disclosure(base, region="UK", lang="en")
    assert "EU AI Act" in out


def test_inject_no_change_for_non_eu():
    from engine.safety.crisis.emotion_disclosure import inject_emotion_disclosure
    base = "허허, 그대의 상을 살피니..."
    out = inject_emotion_disclosure(base, region="KR", lang="ko")
    assert out == base


def test_inject_no_change_for_none_region():
    from engine.safety.crisis.emotion_disclosure import inject_emotion_disclosure
    base = "허허..."
    assert inject_emotion_disclosure(base, region=None, lang="en") == base


# ─────────────────────────── 메타데이터 ───────────────────────────

def test_metadata_for_eu_has_legal_basis():
    from engine.safety.crisis.emotion_disclosure import get_disclosure_metadata
    m = get_disclosure_metadata("DE", "en")
    assert m["required"] is True
    assert m["recommended"] is False
    assert m["legal_basis"] == "EU AI Act Art.50(3)"
    assert isinstance(m["disclosure_text"], str)


def test_metadata_for_uk_is_recommended():
    from engine.safety.crisis.emotion_disclosure import get_disclosure_metadata
    m = get_disclosure_metadata("UK", "en")
    assert m["required"] is False
    assert m["recommended"] is True
    assert m["legal_basis"] == "UK EHRR §6 (recommended)"
    assert m["disclosure_text"]


def test_metadata_for_non_eu_no_legal_basis():
    from engine.safety.crisis.emotion_disclosure import get_disclosure_metadata
    m = get_disclosure_metadata("KR", "ko")
    assert m["required"] is False
    assert m["recommended"] is False
    assert m["legal_basis"] is None
    assert m["disclosure_text"] is None


def test_metadata_passes_through_lang():
    from engine.safety.crisis.emotion_disclosure import get_disclosure_metadata
    m = get_disclosure_metadata("FR", "ja")
    assert m["lang"] == "ja"


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_emotion_disclosure():
    import engine.safety as safety
    assert hasattr(safety, "is_emotion_disclosure_required")
    assert hasattr(safety, "is_emotion_disclosure_recommended")
    assert hasattr(safety, "build_emotion_disclosure")
    assert hasattr(safety, "inject_emotion_disclosure")
    assert hasattr(safety, "get_disclosure_metadata")
