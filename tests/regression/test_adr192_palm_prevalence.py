"""ADR-192 - 한국인 손금 prevalence 통계 회귀."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_normal_prevalence_84_pct():
    from engine.divination.palm.prevalence import get_prevalence
    r = get_prevalence("normal")
    assert 0.83 < r.prevalence_pct < 0.86
    assert r.rank == "most_common"


def test_simian_prevalence_11_pct():
    from engine.divination.palm.prevalence import get_prevalence
    r = get_prevalence("simian")
    assert 0.10 < r.prevalence_pct < 0.13
    assert r.rank == "variant"


def test_suwon_prevalence_rare():
    from engine.divination.palm.prevalence import get_prevalence
    r = get_prevalence("suwon")
    assert r.prevalence_pct < 0.01
    assert r.rank in ("rare", "unknown")


def test_unknown_falls_back_to_other():
    from engine.divination.palm.prevalence import get_prevalence
    r = get_prevalence("nonexistent")
    assert r.crease_type == "other"


def test_disclaimer_blocks_fate_mapping():
    from engine.divination.palm.prevalence import get_prevalence
    r = get_prevalence("simian")
    assert "운명" in r.disclaimer
    assert "의료 진단" in r.disclaimer
    assert "인격 평가" in r.disclaimer


def test_source_urls_verified():
    from engine.divination.palm.prevalence import get_prevalence
    r = get_prevalence("normal")
    assert any("koreamed" in u.lower() for u in r.source_urls)


def test_all_prevalences_sum_close_to_1():
    """4 형태 prevalence 합이 1.0에 근접 (rounding 오차 허용)."""
    from engine.divination.palm.prevalence import KOREAN_PALM_CREASE_PREVALENCE
    total = sum(KOREAN_PALM_CREASE_PREVALENCE.values())
    assert 0.98 < total < 1.02


def test_descriptions_korean():
    from engine.divination.palm.prevalence import get_prevalence
    r = get_prevalence("simian")
    assert "단지" in r.description_ko
    assert "11" in r.description_ko or "변종" in r.description_ko


def test_no_fate_assertion_in_descriptions():
    """모든 description이 ADR-171 fate_assertion 사전과 충돌하지 X."""
    from engine.divination.palm.prevalence import CREASE_DESCRIPTIONS_KO
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    for ct, desc in CREASE_DESCRIPTIONS_KO.items():
        r = detect_fate_assertions(desc, domain="palm")
        assert r.detected is False, f"{ct} description triggers fate_assertion: {r.matched_terms}"


def test_all_prevalences_function():
    from engine.divination.palm.prevalence import all_prevalences
    all_r = all_prevalences()
    assert len(all_r) == 4
    assert "normal" in all_r
    assert "simian" in all_r
