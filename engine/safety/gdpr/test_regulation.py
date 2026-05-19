"""engine.safety.gdpr.regulation — 운영표준 §7.2.5 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_get_regulation_profile_kr():
    from engine.safety.gdpr.regulation import get_regulation_profile
    p = get_regulation_profile("KR")
    assert p.region_code == "KR"
    assert "PIPA" in p.law_keys
    assert p.biometric_sensitive is True
    assert p.consent_required is True


def test_get_regulation_profile_eu():
    from engine.safety.gdpr.regulation import get_regulation_profile
    p = get_regulation_profile("EU")
    assert "GDPR Art.9" in p.law_keys
    assert "EU AI Act §5(g)" in p.law_keys


def test_get_regulation_profile_default_to_eu():
    """미지 지역·None → 가장 엄격한 EU."""
    from engine.safety.gdpr.regulation import get_regulation_profile
    assert get_regulation_profile(None).region_code == "EU"
    assert get_regulation_profile("").region_code == "EU"
    assert get_regulation_profile("ZZ").region_code == "EU"


def test_get_regulation_profile_bcp47_locale_mapping():
    """BCP-47 로케일 → 지역 코드 변환."""
    from engine.safety.gdpr.regulation import get_regulation_profile
    assert get_regulation_profile("ko-KR").region_code == "KR"
    assert get_regulation_profile("ja-JP").region_code == "JP"
    assert get_regulation_profile("zh-CN").region_code == "CN"
    assert get_regulation_profile("en-GB").region_code == "UK"
    assert get_regulation_profile("en-US").region_code == "US-CA"


def test_bipa_illinois():
    from engine.safety.gdpr.regulation import get_regulation_profile
    p = get_regulation_profile("US-IL")
    assert "BIPA" in p.law_keys
    assert p.consent_required is True


def test_china_data_localization():
    from engine.safety.gdpr.regulation import get_regulation_profile
    p = get_regulation_profile("CN")
    assert "PIPL" in p.law_keys
    assert "현지화" in p.notes_ko


def test_delete_response_days():
    """각 지역 SLA. 캘리포니아 90일, 중국 15일, 한국 30일 등."""
    from engine.safety.gdpr.regulation import get_regulation_profile
    assert get_regulation_profile("US-CA").delete_response_days == 90
    assert get_regulation_profile("CN").delete_response_days == 15
    assert get_regulation_profile("KR").delete_response_days == 30


def test_is_biometric_inference_restricted():
    """EU AI Act §5(g) 적용 지역 — EU, UK만 True."""
    from engine.safety.gdpr.regulation import is_biometric_inference_restricted
    assert is_biometric_inference_restricted("EU") is True
    assert is_biometric_inference_restricted("UK") is True
    assert is_biometric_inference_restricted("KR") is False
    assert is_biometric_inference_restricted("US-CA") is False
    assert is_biometric_inference_restricted(None) is True  # default=EU


def test_list_supported_regions():
    from engine.safety.gdpr.regulation import list_supported_regions
    regs = list_supported_regions()
    assert "KR" in regs and "EU" in regs and "JP" in regs and "CN" in regs
    assert len(regs) >= 7


def test_regulation_profile_immutable():
    """RegulationProfile은 frozen dataclass — 우발적 변경 차단."""
    import dataclasses
    from engine.safety.gdpr.regulation import get_regulation_profile
    p = get_regulation_profile("KR")
    with __import__("pytest").raises(dataclasses.FrozenInstanceError):
        p.delete_response_days = 999  # type: ignore[misc]


def test_engine_safety_exports_regulation():
    """engine.safety 패키지에서 함수 노출."""
    import engine.safety as safety
    assert hasattr(safety, "get_regulation_profile")
    assert hasattr(safety, "is_biometric_inference_restricted")
    assert hasattr(safety, "list_supported_regions")
    assert hasattr(safety, "RegulationProfile")
