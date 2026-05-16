"""engine.safety.response_envelope — §7.2.13 envelope 표준 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 분기 추정 ───────────────────────────

def _normal_envelope():
    return {
        "text": "허허, 그대의 상을 살피니",
        "cached": False,
        "crisis_alert": None,
        "legal_notice": "...",
        "detected_language": "ko",
        "language_advisory": None,
        "a11y": {},
        "persona_self_eval": {"passed": True, "score": 0.9},
    }


def test_detect_branch_normal():
    from engine.safety.response_envelope import detect_branch, ENVELOPE_NORMAL
    assert detect_branch(_normal_envelope()) == ENVELOPE_NORMAL


def test_detect_branch_cached():
    from engine.safety.response_envelope import detect_branch, ENVELOPE_CACHED
    env = _normal_envelope()
    env["cached"] = True
    assert detect_branch(env) == ENVELOPE_CACHED


def test_detect_branch_crisis():
    from engine.safety.response_envelope import detect_branch, ENVELOPE_CRISIS
    env = _normal_envelope()
    env["crisis_alert"] = {"severity": "high"}
    assert detect_branch(env) == ENVELOPE_CRISIS


def test_detect_branch_jailbreak():
    from engine.safety.response_envelope import detect_branch, ENVELOPE_JAILBREAK
    env = _normal_envelope()
    env["jailbreak_categories"] = ["persona_override"]
    env["error_code"] = "persona_override"
    assert detect_branch(env) == ENVELOPE_JAILBREAK


def test_detect_branch_error_err_prefix():
    from engine.safety.response_envelope import detect_branch, ENVELOPE_ERROR
    env = _normal_envelope()
    env["error_code"] = "ERR_FACE_NOT_DETECTED"
    assert detect_branch(env) == ENVELOPE_ERROR


def test_detect_branch_warn_prefix():
    from engine.safety.response_envelope import detect_branch, ENVELOPE_WARN
    env = _normal_envelope()
    env["error_code"] = "WARN_FACE_FLAT"
    assert detect_branch(env) == ENVELOPE_WARN


def test_detect_branch_crisis_takes_priority():
    """crisis_alert가 있으면 다른 키와 무관하게 crisis."""
    from engine.safety.response_envelope import detect_branch, ENVELOPE_CRISIS
    env = _normal_envelope()
    env["crisis_alert"] = {"severity": "high"}
    env["error_code"] = "ERR_FACE_NOT_DETECTED"
    assert detect_branch(env) == ENVELOPE_CRISIS


def test_detect_branch_non_dict_returns_empty():
    from engine.safety.response_envelope import detect_branch
    assert detect_branch(None) == ""  # type: ignore[arg-type]
    assert detect_branch("text") == ""  # type: ignore[arg-type]


# ─────────────────────────── 검증 ───────────────────────────

def test_validate_clean_normal_envelope_passes():
    from engine.safety.response_envelope import validate_envelope
    assert validate_envelope(_normal_envelope()) == []


def test_validate_missing_required_keys():
    from engine.safety.response_envelope import validate_envelope, REQUIRED_KEYS
    env = _normal_envelope()
    del env["text"]
    del env["legal_notice"]
    v = validate_envelope(env)
    assert any("missing_required:text" in x for x in v)
    assert any("missing_required:legal_notice" in x for x in v)


def test_validate_empty_text_invalid():
    from engine.safety.response_envelope import validate_envelope
    env = _normal_envelope()
    env["text"] = ""
    v = validate_envelope(env)
    assert "text_invalid" in v


def test_validate_cached_not_bool():
    from engine.safety.response_envelope import validate_envelope
    env = _normal_envelope()
    env["cached"] = "no"
    v = validate_envelope(env)
    assert "cached_not_bool" in v


def test_validate_crisis_alert_wrong_type():
    from engine.safety.response_envelope import validate_envelope
    env = _normal_envelope()
    env["crisis_alert"] = "yes"
    v = validate_envelope(env)
    assert "crisis_alert_invalid" in v


def test_validate_jailbreak_envelope_requires_categories():
    from engine.safety.response_envelope import validate_envelope
    env = _normal_envelope()
    env["error_code"] = "persona_override"
    # jailbreak_categories 누락
    v = validate_envelope(env)
    # 분기 자체가 ERROR 로 추정되므로 photo_guidance 누락 잡힘
    assert any("missing_branch_key" in x for x in v)


def test_validate_err_envelope_requires_photo_guidance():
    from engine.safety.response_envelope import validate_envelope
    env = _normal_envelope()
    env["error_code"] = "ERR_FACE_NOT_DETECTED"
    v = validate_envelope(env)
    assert any("photo_guidance" in x for x in v)


def test_validate_normal_requires_a11y_and_persona_eval():
    from engine.safety.response_envelope import validate_envelope
    env = _normal_envelope()
    del env["persona_self_eval"]
    v = validate_envelope(env)
    assert any("persona_self_eval" in x for x in v)


def test_validate_non_dict_returns_violation():
    from engine.safety.response_envelope import validate_envelope
    v = validate_envelope("oops")  # type: ignore[arg-type]
    assert "not_a_dict" in v


def test_is_valid_shortcut():
    from engine.safety.response_envelope import is_valid
    assert is_valid(_normal_envelope()) is True
    assert is_valid({}) is False


# ─────────────────────────── 정규화 ───────────────────────────

def test_normalize_fills_missing_required():
    from engine.safety.response_envelope import normalize_envelope
    env = {"text": "test"}
    out = normalize_envelope(env)
    for k in ("cached", "crisis_alert", "legal_notice",
              "detected_language", "language_advisory"):
        assert k in out
    assert out["cached"] is False
    assert out["crisis_alert"] is None


def test_normalize_preserves_existing_values():
    from engine.safety.response_envelope import normalize_envelope
    env = _normal_envelope()
    out = normalize_envelope(env)
    assert out["text"] == env["text"]
    assert out["persona_self_eval"] == env["persona_self_eval"]


def test_normalize_none_text_becomes_empty_string():
    from engine.safety.response_envelope import normalize_envelope
    out = normalize_envelope({"text": None, "cached": False})
    assert out["text"] == ""


def test_normalize_non_dict_returns_empty():
    from engine.safety.response_envelope import normalize_envelope
    assert normalize_envelope(None) == {}  # type: ignore[arg-type]


# ─────────────────────────── 감사 ───────────────────────────

def test_audit_all_valid():
    from engine.safety.response_envelope import audit_envelopes
    envs = [_normal_envelope() for _ in range(5)]
    r = audit_envelopes(envs)
    assert r["total"] == 5
    assert r["valid"] == 5
    assert r["invalid"] == 0
    assert r["all_valid"] is True


def test_audit_mixed_branches_count_distribution():
    from engine.safety.response_envelope import audit_envelopes
    env_normal = _normal_envelope()
    env_crisis = _normal_envelope()
    env_crisis["crisis_alert"] = {"severity": "high"}
    r = audit_envelopes([env_normal, env_crisis, env_normal])
    assert r["branch_distribution"]["normal"] == 2
    assert r["branch_distribution"]["crisis"] == 1


def test_audit_detects_violations():
    from engine.safety.response_envelope import audit_envelopes
    bad = _normal_envelope()
    del bad["text"]
    r = audit_envelopes([_normal_envelope(), bad])
    assert r["invalid"] == 1
    assert 1 in r["violations_by_index"]
    assert r["all_valid"] is False


def test_audit_empty_list():
    from engine.safety.response_envelope import audit_envelopes
    r = audit_envelopes([])
    assert r["total"] == 0
    assert r["all_valid"] is True


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_response_envelope():
    import engine.safety as safety
    assert hasattr(safety, "detect_branch")
    assert hasattr(safety, "validate_envelope")
    assert hasattr(safety, "is_valid")
    assert hasattr(safety, "normalize_envelope")
    assert hasattr(safety, "audit_envelopes")
    assert hasattr(safety, "REQUIRED_KEYS")
    assert hasattr(safety, "ENVELOPE_NORMAL")
    assert hasattr(safety, "ENVELOPE_CRISIS")
