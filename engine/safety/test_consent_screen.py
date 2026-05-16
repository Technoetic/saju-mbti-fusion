"""engine.safety.consent_screen — §14.1 동의 화면 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── get_consent_screen ───────────────────────────

def test_consent_screen_all_4_languages():
    from engine.safety.consent_screen import get_consent_screen
    for lang in ("ko", "en", "ja", "zh"):
        s = get_consent_screen(lang)
        assert s["lang"] == lang
        assert s["title"]
        assert s["intro"]
        assert s["rights"]
        assert s["disclaimer"]
        assert isinstance(s["items"], list)
        assert len(s["items"]) == 4
        assert isinstance(s["required_keys"], list)


def test_consent_screen_unknown_lang_falls_back_to_en():
    from engine.safety.consent_screen import get_consent_screen
    s = get_consent_screen("fr")
    assert s["lang"] == "en"


def test_consent_screen_items_have_required_fields():
    from engine.safety.consent_screen import get_consent_screen
    s = get_consent_screen("ko")
    for it in s["items"]:
        assert "key" in it
        assert "title" in it
        assert "description" in it
        assert "required" in it
        assert isinstance(it["required"], bool)


def test_consent_screen_3_required_1_optional():
    """§14.1 — processing/storage/third_party_sharing은 필수, training만 선택."""
    from engine.safety.consent_screen import get_consent_screen
    s = get_consent_screen("ko")
    required = {it["key"]: it["required"] for it in s["items"]}
    assert required["processing"] is True
    assert required["storage"] is True
    assert required["third_party_sharing"] is True
    assert required["training"] is False
    assert set(s["required_keys"]) == {"processing", "storage", "third_party_sharing"}


def test_consent_screen_keys_match_data_governance():
    """consent_screen의 item key 집합이 REQUIRED_CONSENT_FIELDS와 정확히 일치해야 함."""
    from engine.safety.consent_screen import get_consent_screen
    from engine.safety.data_governance import REQUIRED_CONSENT_FIELDS
    s = get_consent_screen("ko")
    keys = {it["key"] for it in s["items"]}
    assert keys == set(REQUIRED_CONSENT_FIELDS)


def test_consent_screen_ko_uses_saguk_tone():
    """한국어 본문은 운학 도사 페르소나와 일관되게 사극풍이어야 함."""
    from engine.safety.consent_screen import get_consent_screen
    s = get_consent_screen("ko")
    blob = s["intro"] + s["rights"] + s["disclaimer"]
    # '늙은이' 또는 '그대'가 반드시 등장
    assert "그대" in blob or "늙은이" in blob


def test_consent_screen_legal_citations_present():
    """rights에 GDPR과 한국 개인정보보호법 조항이 모두 명시되어야 함."""
    from engine.safety.consent_screen import get_consent_screen
    for lang in ("ko", "en", "ja", "zh"):
        rights = get_consent_screen(lang)["rights"]
        assert "GDPR" in rights
        # 한국 개인정보보호법: 'PIPA' 또는 '개인정보보호법'/'個人情報保護法'/'个人信息保护法'
        ko_law_markers = ("PIPA", "개인정보보호법", "個人情報保護法", "个人信息保护法")
        assert any(m in rights for m in ko_law_markers)


def test_consent_screen_disclaimer_mentions_no_medical_legal_financial():
    """면책에 의료·법률·금융 자문 아님 명시."""
    from engine.safety.consent_screen import get_consent_screen
    en = get_consent_screen("en")["disclaimer"]
    assert "medical" in en.lower()
    assert "legal" in en.lower()
    assert "financial" in en.lower()


# ─────────────────────────── validate_consent_payload ───────────────────────────

def test_validate_consent_full_consent_passes():
    from engine.safety.consent_screen import validate_consent_payload
    r = validate_consent_payload({
        "processing": True,
        "storage": True,
        "training": True,
        "third_party_sharing": True,
    })
    assert r["ok"] is True
    assert r["missing_required"] == []
    assert r["denied_required"] == []
    assert r["training_opt_in"] is True


def test_validate_consent_optional_only_passes():
    """training만 거부해도 필수 3개가 통과면 ok."""
    from engine.safety.consent_screen import validate_consent_payload
    r = validate_consent_payload({
        "processing": True,
        "storage": True,
        "training": False,
        "third_party_sharing": True,
    })
    assert r["ok"] is True
    assert r["training_opt_in"] is False


def test_validate_consent_missing_required_blocks():
    from engine.safety.consent_screen import validate_consent_payload
    r = validate_consent_payload({"processing": True})  # 2개 누락
    assert r["ok"] is False
    assert set(r["missing_required"]) == {"storage", "third_party_sharing"}


def test_validate_consent_denied_required_blocks():
    from engine.safety.consent_screen import validate_consent_payload
    r = validate_consent_payload({
        "processing": True,
        "storage": False,  # 거부
        "training": True,
        "third_party_sharing": True,
    })
    assert r["ok"] is False
    assert "storage" in r["denied_required"]


def test_validate_consent_none_payload_blocks():
    from engine.safety.consent_screen import validate_consent_payload
    r = validate_consent_payload(None)
    assert r["ok"] is False
    assert len(r["missing_required"]) == 3


def test_validate_consent_non_dict_payload_blocks():
    from engine.safety.consent_screen import validate_consent_payload
    r = validate_consent_payload("yes")  # type: ignore[arg-type]
    assert r["ok"] is False


def test_validate_consent_truthy_but_not_true_blocks():
    """is True 검사 — 1이나 'yes' 같은 truthy는 부동의로 취급 (엄격 동의)."""
    from engine.safety.consent_screen import validate_consent_payload
    r = validate_consent_payload({
        "processing": 1,
        "storage": "yes",
        "training": True,
        "third_party_sharing": True,
    })
    assert r["ok"] is False
    assert "processing" in r["denied_required"]
    assert "storage" in r["denied_required"]


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_consent_screen():
    import engine.safety as safety
    assert hasattr(safety, "get_consent_screen")
    assert hasattr(safety, "validate_consent_payload")
    assert hasattr(safety, "CONSENT_FIELDS")
