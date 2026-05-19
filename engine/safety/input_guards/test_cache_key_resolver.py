"""engine.safety.input_guards.cache_key_resolver — §7.2.23 캐시 키 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _base_kwargs():
    return {
        "system_prompt_hash": "p1",
        "image_b64": "img_data",
        "age": 30,
        "gender": "male",
        "question": "운세?",
        "metrics": {"face_count": 1, "head_tilt_deg": 5.0},
        "lang": "ko",
        "region": "KR",
    }


# ─────────────────────────── 결정론 ───────────────────────────

def test_same_input_same_key():
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key
    a = resolve_cache_key(**_base_kwargs())
    b = resolve_cache_key(**_base_kwargs())
    assert a.key == b.key


def test_key_length():
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key, CACHE_KEY_LENGTH
    k = resolve_cache_key(**_base_kwargs())
    assert len(k.key) == CACHE_KEY_LENGTH


def test_missing_prompt_hash_raises():
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key
    kw = _base_kwargs()
    kw["system_prompt_hash"] = ""
    with pytest.raises(ValueError):
        resolve_cache_key(**kw)


# ─────────────────────────── 차원별 차이 ───────────────────────────

def test_prompt_hash_change_invalidates_cache():
    """시스템 프롬프트 해시 변경 시 같은 입력이라도 새 키."""
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key
    kw = _base_kwargs()
    a = resolve_cache_key(**kw)
    kw["system_prompt_hash"] = "p2"
    b = resolve_cache_key(**kw)
    assert a.key != b.key


def test_image_change_yields_different_key():
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key
    kw = _base_kwargs()
    a = resolve_cache_key(**kw)
    kw["image_b64"] = "different_image"
    b = resolve_cache_key(**kw)
    assert a.key != b.key


def test_age_bucket_boundary_changes_key():
    """29세 → 20s, 30세 → 30s — bucket 다르면 키도 다름."""
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key
    kw = _base_kwargs()
    kw["age"] = 29
    a = resolve_cache_key(**kw)
    kw["age"] = 30
    b = resolve_cache_key(**kw)
    assert a.key != b.key


def test_same_age_bucket_same_key():
    """30세와 35세는 모두 30s bucket → 같은 키 (개인정보 축소)."""
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key
    kw = _base_kwargs()
    kw["age"] = 30
    a = resolve_cache_key(**kw)
    kw["age"] = 35
    b = resolve_cache_key(**kw)
    assert a.key == b.key


def test_gender_change_yields_different_key():
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key
    kw = _base_kwargs()
    kw["gender"] = "male"
    a = resolve_cache_key(**kw)
    kw["gender"] = "female"
    b = resolve_cache_key(**kw)
    assert a.key != b.key


def test_question_change_yields_different_key():
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key
    kw = _base_kwargs()
    a = resolve_cache_key(**kw)
    kw["question"] = "다른 화두"
    b = resolve_cache_key(**kw)
    assert a.key != b.key


def test_metrics_change_yields_different_key():
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key
    kw = _base_kwargs()
    a = resolve_cache_key(**kw)
    kw["metrics"] = {"face_count": 1, "head_tilt_deg": 20.0}
    b = resolve_cache_key(**kw)
    assert a.key != b.key


def test_metrics_dict_order_stable():
    """dict 키 입력 순서가 달라도 같은 캐시 키."""
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key
    kw = _base_kwargs()
    kw["metrics"] = {"face_count": 1, "head_tilt_deg": 5.0}
    a = resolve_cache_key(**kw)
    kw["metrics"] = {"head_tilt_deg": 5.0, "face_count": 1}
    b = resolve_cache_key(**kw)
    assert a.key == b.key


def test_metrics_tiny_float_noise_stable():
    """5번째 자리 이하 float 잡음은 같은 키 (소수점 4자리 반올림)."""
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key
    kw = _base_kwargs()
    kw["metrics"] = {"head_tilt_deg": 5.000001}
    a = resolve_cache_key(**kw)
    kw["metrics"] = {"head_tilt_deg": 5.000009}
    b = resolve_cache_key(**kw)
    assert a.key == b.key


def test_lang_change_yields_different_key():
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key
    kw = _base_kwargs()
    a = resolve_cache_key(**kw)
    kw["lang"] = "en"
    b = resolve_cache_key(**kw)
    assert a.key != b.key


def test_region_class_change_yields_different_key():
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key
    kw = _base_kwargs()
    kw["region"] = "KR"
    a = resolve_cache_key(**kw)
    kw["region"] = "DE"
    b = resolve_cache_key(**kw)
    assert a.key != b.key


def test_same_region_class_same_key():
    """DE와 FR은 모두 'eu' 클래스 → 같은 키 (개인정보 축소)."""
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key
    kw = _base_kwargs()
    kw["region"] = "DE"
    a = resolve_cache_key(**kw)
    kw["region"] = "FR"
    b = resolve_cache_key(**kw)
    assert a.key == b.key


# ─────────────────────────── 정규화 ───────────────────────────

def test_age_unknown_for_none():
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key
    kw = _base_kwargs()
    kw["age"] = None
    k = resolve_cache_key(**kw)
    assert k.age_bucket == "unknown"


def test_age_unknown_for_negative():
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key
    kw = _base_kwargs()
    kw["age"] = -1
    k = resolve_cache_key(**kw)
    assert k.age_bucket == "unknown"


def test_age_buckets_full_range():
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key
    kw = _base_kwargs()
    cases = [(15, "teen"), (25, "20s"), (35, "30s"), (45, "40s"),
             (55, "50s"), (75, "60s+")]
    for age, expected in cases:
        kw["age"] = age
        k = resolve_cache_key(**kw)
        assert k.age_bucket == expected


def test_gender_korean_form_normalized():
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key
    kw = _base_kwargs()
    kw["gender"] = "남"
    a = resolve_cache_key(**kw)
    kw["gender"] = "male"
    b = resolve_cache_key(**kw)
    assert a.key == b.key


def test_lang_unsupported_falls_back_to_en():
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key
    kw = _base_kwargs()
    kw["lang"] = "fr"
    a = resolve_cache_key(**kw)
    kw["lang"] = "en"
    b = resolve_cache_key(**kw)
    assert a.key == b.key


def test_region_unknown_classified_as_other():
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key
    kw = _base_kwargs()
    kw["region"] = "ZZ"
    k = resolve_cache_key(**kw)
    assert k.region_class == "other"


# ─────────────────────────── invalidates_on_prompt_change ───────────────────────────

def test_invalidates_returns_true_when_different():
    from engine.safety.input_guards.cache_key_resolver import invalidates_on_prompt_change
    assert invalidates_on_prompt_change("v1", "v2") is True


def test_invalidates_returns_false_when_same():
    from engine.safety.input_guards.cache_key_resolver import invalidates_on_prompt_change
    assert invalidates_on_prompt_change("v1", "v1") is False


# ─────────────────────────── tracing ───────────────────────────

def test_trace_event_omits_raw_pii():
    """tracing 페이로드는 원본 화두/이미지 미포함 (해시만)."""
    from engine.safety.input_guards.cache_key_resolver import resolve_cache_key, to_trace_event
    k = resolve_cache_key(**_base_kwargs())
    e = to_trace_event(k)
    assert "운세" not in str(e)
    assert "img_data" not in str(e)


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_cache_key_resolver():
    import engine.safety as safety
    assert hasattr(safety, "resolve_cache_key")
    assert hasattr(safety, "invalidates_on_prompt_change")
    assert hasattr(safety, "CacheKey")
    assert hasattr(safety, "CACHE_KEY_LENGTH")
