"""ADR-204+205+206 사용자 가치 인프라 회귀."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ───── ADR-204 비교 묘사 ─────

def test_adr204_alar_ratio_comparison_average():
    from engine.divination.face.engagement import compare_alar_ratio
    r = compare_alar_ratio(0.35)
    assert r is not None
    assert r.diff_pct > 0  # 0.32 평균보다 큼
    assert "운명 매핑이 아닙니다" in r.description_ko


def test_adr204_alar_close_to_average():
    from engine.divination.face.engagement import compare_alar_ratio
    r = compare_alar_ratio(0.32)
    assert "거의 같습니다" in r.description_ko


def test_adr204_miss_korea_comparison():
    from engine.divination.face.engagement import compare_to_miss_korea
    r = compare_to_miss_korea(0.40)
    assert r is not None
    assert "미모·운명과 무관합니다" in r.description_ko
    assert "5359635" in r.source_url


def test_adr204_invalid_input_safe():
    from engine.divination.face.engagement import compare_alar_ratio
    assert compare_alar_ratio(0) is None
    assert compare_alar_ratio(-0.1) is None
    assert compare_alar_ratio("invalid") is None  # type: ignore[arg-type]


# ───── ADR-205 prevalence 구체 묘사 ─────

def test_adr205_palm_prevalence_normal():
    from engine.divination.face.engagement import describe_palm_prevalence
    p = describe_palm_prevalence("normal")
    assert p is not None
    assert "흔한" in p.rank_label
    assert "운명·인격 평가가 아닙니다" in p.description_ko


def test_adr205_palm_prevalence_simian():
    from engine.divination.face.engagement import describe_palm_prevalence
    p = describe_palm_prevalence("simian")
    assert p is not None
    assert p.percent > 10
    assert "변종" in p.rank_label


def test_adr205_palm_prevalence_rare():
    from engine.divination.face.engagement import describe_palm_prevalence
    p = describe_palm_prevalence("suwon")
    assert p is not None
    assert "희소" in p.description_ko or "드문" in p.rank_label


# ───── ADR-206 공유 카드 ─────

def test_adr206_share_card_face():
    from engine.divination.face.engagement import build_share_card
    card = build_share_card("face", "재백궁이 환한")
    assert "관상" in card.og_title
    assert "재백궁이 환한" in card.og_description
    assert "운명 단정 아님" in card.og_description
    assert card.twitter_card == "summary_large_image"


def test_adr206_share_card_palm():
    from engine.divination.face.engagement import build_share_card
    card = build_share_card("palm", "단정한 결의")
    assert "손금" in card.og_title


def test_adr206_share_card_json_ld_structured():
    from engine.divination.face.engagement import build_share_card
    card = build_share_card("face", "환한 결")
    assert card.json_ld["@context"] == "https://schema.org"
    assert card.json_ld["@type"] == "WebApplication"
    assert "ADR-006" in card.json_ld["description"]
    assert card.json_ld["inLanguage"] == "ko-KR"


def test_adr206_share_card_disclaimer_present():
    from engine.divination.face.engagement import build_share_card
    card = build_share_card("face", "단정한 결")
    assert "운명·길흉 단정이 아닙니다" in card.disclaimer_ko


# ───── ADR-006 / 171 정합 ─────

def test_engagement_descriptions_pass_fate_assertion_filter():
    """모든 비교·prevalence 묘사가 ADR-171 fate_assertion 통과."""
    from engine.divination.face.engagement import (
        compare_alar_ratio, describe_palm_prevalence,
    )
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r1 = compare_alar_ratio(0.35)
    r2 = describe_palm_prevalence("simian")
    assert r1 is not None and r2 is not None
    for text in (r1.description_ko, r2.description_ko):
        d = detect_fate_assertions(text, domain="face")
        assert d.detected is False, f"fate assertion in: {text!r} ({d.matched_terms})"
