"""engine.safety.gdpr.rights_information — §14.2 권리 행사 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 4언어 ───────────────────────────

def test_rights_information_4_languages():
    from engine.safety.gdpr.rights_information import get_rights_information
    for lang in ("ko", "en", "ja", "zh"):
        r = get_rights_information(lang)
        assert r["lang"] == lang
        assert isinstance(r["rights"], list)
        assert len(r["rights"]) == 7


def test_rights_information_unknown_lang_falls_back_to_en():
    from engine.safety.gdpr.rights_information import get_rights_information
    r = get_rights_information("fr")
    assert r["lang"] == "en"


def test_rights_information_all_7_keys_present():
    from engine.safety.gdpr.rights_information import get_rights_information, RIGHT_KEYS
    for lang in ("ko", "en", "ja", "zh"):
        keys = {r["key"] for r in get_rights_information(lang)["rights"]}
        assert keys == set(RIGHT_KEYS)


def test_rights_information_each_item_has_required_fields():
    from engine.safety.gdpr.rights_information import get_rights_information
    for r in get_rights_information("ko")["rights"]:
        assert r["key"]
        assert r["title"]
        assert r["description"]
        assert r["automation_status"] in ("auto", "manual", "na")
        assert isinstance(r["sla_business_days"], int)
        assert r["sla_business_days"] > 0
        assert isinstance(r["authentication_required"], bool)


def test_rights_information_ko_uses_saguk_tone():
    from engine.safety.gdpr.rights_information import get_rights_information
    blob = " ".join(r["title"] + r["description"] for r in get_rights_information("ko")["rights"])
    assert "그대" in blob or "늙은이" in blob


# ─────────────────────────── 자동화 분류 ───────────────────────────

def test_withdraw_consent_is_automated():
    from engine.safety.gdpr.rights_information import get_right_by_key
    r = get_right_by_key("withdraw_consent", "en")
    assert r is not None
    assert r["automation_status"] == "auto"
    assert r["sla_business_days"] <= 7  # 동의 철회는 빠른 응답


def test_object_right_is_manual():
    """이의 제기는 자동화된 의사결정 검토가 필요해 수동 처리."""
    from engine.safety.gdpr.rights_information import get_right_by_key
    r = get_right_by_key("object", "en")
    assert r is not None
    assert r["automation_status"] == "manual"


def test_list_automatable_rights():
    from engine.safety.gdpr.rights_information import list_automatable_rights
    autos = list_automatable_rights("en")
    assert "access" in autos
    assert "erase" in autos
    assert "withdraw_consent" in autos
    assert "object" not in autos  # manual
    assert "restrict" not in autos  # manual


def test_get_right_by_key_unknown_returns_none():
    from engine.safety.gdpr.rights_information import get_right_by_key
    assert get_right_by_key("not_a_real_right", "en") is None


# ─────────────────────────── 지역별 SLA ───────────────────────────

def test_sla_eu_uses_gdpr_30_days():
    from engine.safety.gdpr.rights_information import get_sla_for_region
    assert get_sla_for_region("access", "DE") == 30
    assert get_sla_for_region("erase", "EU") == 30


def test_sla_kr_uses_pipa_10_days():
    from engine.safety.gdpr.rights_information import get_sla_for_region
    assert get_sla_for_region("access", "KR") == 10
    assert get_sla_for_region("erase", "KR") == 10


def test_sla_jp_uses_14_days():
    from engine.safety.gdpr.rights_information import get_sla_for_region
    assert get_sla_for_region("access", "JP") == 14


def test_sla_cn_uses_15_days():
    from engine.safety.gdpr.rights_information import get_sla_for_region
    assert get_sla_for_region("access", "CN") == 15


def test_sla_withdraw_consent_is_fast_everywhere():
    """동의 철회는 어느 지역에서도 5일 내."""
    from engine.safety.gdpr.rights_information import get_sla_for_region
    for region in ("KR", "DE", "JP", "CN", "US-CA"):
        sla = get_sla_for_region("withdraw_consent", region)
        assert 0 < sla <= 7, f"{region} withdraw SLA too long: {sla}"


def test_sla_unknown_key_returns_negative():
    from engine.safety.gdpr.rights_information import get_sla_for_region
    assert get_sla_for_region("not_a_real_right", "EU") == -1


def test_sla_unknown_region_falls_back_to_en():
    from engine.safety.gdpr.rights_information import get_sla_for_region
    # 미지원 지역은 영어판(=GDPR) 30일 SLA
    assert get_sla_for_region("access", "ZZ") == 30
    assert get_sla_for_region("access", None) == 30


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_rights_information():
    import engine.safety as safety
    assert hasattr(safety, "RIGHT_KEYS")
    assert hasattr(safety, "RightInfo")
    assert hasattr(safety, "get_rights_information")
    assert hasattr(safety, "get_right_by_key")
    assert hasattr(safety, "list_automatable_rights")
    assert hasattr(safety, "get_sla_for_region")
