"""engine.safety.crisis_resources — §7.2.12 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_get_crisis_resources_kr():
    from engine.safety.crisis_resources import get_crisis_resources
    hotlines = get_crisis_resources("KR")
    phones = [h.phone for h in hotlines]
    assert "1393" in phones
    assert "1577-0199" in phones
    assert "1388" in phones  # 청소년


def test_get_crisis_resources_us_988():
    """미국 캘리포니아·일리노이는 988 라이프라인."""
    from engine.safety.crisis_resources import get_crisis_resources
    ca = get_crisis_resources("US-CA")
    il = get_crisis_resources("US-IL")
    assert any(h.phone == "988" for h in ca)
    assert any(h.phone == "988" for h in il)


def test_get_crisis_resources_uk_samaritans():
    from engine.safety.crisis_resources import get_crisis_resources
    hotlines = get_crisis_resources("UK")
    assert any("Samaritans" in h.name_local for h in hotlines)
    assert any(h.phone == "116 123" for h in hotlines)


def test_get_crisis_resources_eu_multilang():
    """EU는 116 123 (다국어 사마리탄즈) 포함."""
    from engine.safety.crisis_resources import get_crisis_resources
    hotlines = get_crisis_resources("EU")
    phones = [h.phone for h in hotlines]
    assert "112" in phones
    assert "116 123" in phones


def test_get_crisis_resources_jp_jjp():
    from engine.safety.crisis_resources import get_crisis_resources
    hotlines = get_crisis_resources("JP")
    assert any(h.language == "ja" for h in hotlines)
    assert any("0120" in h.phone for h in hotlines)


def test_get_crisis_resources_cn():
    from engine.safety.crisis_resources import get_crisis_resources
    hotlines = get_crisis_resources("CN")
    assert any(h.language == "zh" for h in hotlines)


def test_unknown_region_falls_back_to_kr():
    """알 수 없는 지역 → 한국 핫라인 보장 (빈 목록 절대 X)."""
    from engine.safety.crisis_resources import get_crisis_resources
    assert get_crisis_resources(None)[0].phone == "1393"
    assert get_crisis_resources("ZZ")[0].phone == "1393"
    assert get_crisis_resources("")[0].phone == "1393"


def test_bcp47_locale_mapping():
    """ko-KR / ja-JP / zh-CN / en-GB / en-US 매핑."""
    from engine.safety.crisis_resources import get_crisis_resources
    assert get_crisis_resources("ko-KR")[0].phone == "1393"
    assert "0120-279-338" in [h.phone for h in get_crisis_resources("ja-JP")]
    assert any(h.language == "zh" for h in get_crisis_resources("zh-CN"))
    assert any("Samaritans" in h.name_local for h in get_crisis_resources("en-GB"))
    assert any(h.phone == "988" for h in get_crisis_resources("en-US"))


def test_format_hotlines_text_korean():
    """포맷팅 — 사극풍 결과 본문에 부착 가능한 텍스트."""
    from engine.safety.crisis_resources import get_crisis_resources, format_hotlines_text
    text = format_hotlines_text(get_crisis_resources("KR"))
    assert "자살예방상담전화" in text
    assert "1393" in text
    assert "24시간" in text


def test_format_hotlines_empty_input():
    from engine.safety.crisis_resources import format_hotlines_text
    assert format_hotlines_text([]) == ""


def test_all_hotlines_have_non_empty_phone():
    """모든 핫라인이 유효한 전화번호 보유."""
    from engine.safety.crisis_resources import (
        get_crisis_resources, list_supported_crisis_regions,
    )
    for region in list_supported_crisis_regions():
        for h in get_crisis_resources(region):
            assert h.phone.strip(), f"{region}: {h.name_ko}에 phone 누락"


def test_crisis_hotline_frozen():
    """CrisisHotline은 frozen dataclass."""
    import dataclasses
    from engine.safety.crisis_resources import get_crisis_resources
    h = get_crisis_resources("KR")[0]
    with __import__("pytest").raises(dataclasses.FrozenInstanceError):
        h.phone = "0000"  # type: ignore[misc]


def test_engine_safety_exports_crisis_resources():
    import engine.safety as safety
    assert hasattr(safety, "get_crisis_resources")
    assert hasattr(safety, "format_hotlines_text")
    assert hasattr(safety, "CrisisHotline")
    assert hasattr(safety, "list_supported_crisis_regions")


def test_at_least_seven_supported_regions():
    """KR/EU/UK/US-CA/US-IL/JP/CN 최소 7개."""
    from engine.safety.crisis_resources import list_supported_crisis_regions
    regions = list_supported_crisis_regions()
    expected = {"KR", "EU", "UK", "US-CA", "US-IL", "JP", "CN"}
    assert expected.issubset(set(regions))
