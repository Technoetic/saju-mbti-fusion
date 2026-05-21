"""ADR-106 회귀 — 12 별자리 144 궁합 매트릭스 결정론 검증.

영역:
  · 144 조합 전체 카운트
  · element 동기·보완·이질 분류
  · 결정론 (동일 입력 → 동일 결과)
  · ADR-006 단정 필드 부재 자동 검증
"""

from engine.divination.star.compatibility import (
    ELEMENT_AFFINITY_SCORE,
    compute_compatibility,
    compatibility_matrix_summary,
    format_compatibility_for_prompt,
)


# ─────────────────────────── 매트릭스 카운트 ───────────────────────────

def test_compatibility_matrix_total():
    """12 × 12 = 144 조합 전부 산출 가능."""
    summary = compatibility_matrix_summary()
    assert summary["total"] == 144


def test_compatibility_matrix_element_distribution():
    """element 분포: resonant·complementary·frictional 합 = 144."""
    summary = compatibility_matrix_summary()
    total = summary["resonant"] + summary["complementary"] + summary["frictional"]
    assert total == 144
    # 12 별자리 = 3 fire + 3 earth + 3 air + 3 water
    # resonant (동일 element): 3×3 × 4 = 36
    # complementary (fire-air, earth-water): 3×3 × 4 = 36
    # frictional (나머지): 144 - 36 - 36 = 72
    assert summary["resonant"] == 36
    assert summary["complementary"] == 36
    assert summary["frictional"] == 72


# ─────────────────────────── element 호환 매트릭스 ───────────────────────────

def test_element_resonant_score():
    """동일 element는 85점."""
    for elem in ("fire", "earth", "air", "water"):
        assert ELEMENT_AFFINITY_SCORE[(elem, elem)] == 85


def test_element_complementary_score():
    """보완 element (fire-air, earth-water)는 75점."""
    assert ELEMENT_AFFINITY_SCORE[("fire", "air")] == 75
    assert ELEMENT_AFFINITY_SCORE[("air", "fire")] == 75
    assert ELEMENT_AFFINITY_SCORE[("earth", "water")] == 75
    assert ELEMENT_AFFINITY_SCORE[("water", "earth")] == 75


def test_element_frictional_score():
    """이질 element는 45~55점."""
    assert ELEMENT_AFFINITY_SCORE[("fire", "water")] == 45
    assert ELEMENT_AFFINITY_SCORE[("water", "fire")] == 45
    assert ELEMENT_AFFINITY_SCORE[("fire", "earth")] == 55
    assert ELEMENT_AFFINITY_SCORE[("air", "earth")] == 55


def test_element_symmetry():
    """element 매트릭스 대칭 (A↔B 동일 점수)."""
    for (a, b), score in ELEMENT_AFFINITY_SCORE.items():
        assert ELEMENT_AFFINITY_SCORE[(b, a)] == score, f"비대칭: {a}↔{b}"


# ─────────────────────────── 결정론 ───────────────────────────

def test_compatibility_deterministic():
    """동일 입력 → 동일 결과 (결정론)."""
    r1 = compute_compatibility("aries", "leo")
    r2 = compute_compatibility("aries", "leo")
    assert r1 == r2


def test_compatibility_invalid_key_returns_none():
    """잘못된 키 → None."""
    assert compute_compatibility("invalid", "leo") is None
    assert compute_compatibility("aries", "wrong") is None
    assert compute_compatibility("xx", "yy") is None


# ─────────────────────────── 정합 점수 ───────────────────────────

def test_aries_leo_resonant():
    """양자리(fire) × 사자자리(fire) = resonant."""
    r = compute_compatibility("aries", "leo")
    assert r is not None
    assert r.relation_type == "resonant"
    assert r.element_affinity_score == 85


def test_aries_libra_complementary():
    """양자리(fire) × 천칭자리(air) = complementary."""
    r = compute_compatibility("aries", "libra")
    assert r is not None
    assert r.relation_type == "complementary"
    assert r.element_affinity_score == 75


def test_aries_cancer_frictional():
    """양자리(fire) × 게자리(water) = frictional."""
    r = compute_compatibility("aries", "cancer")
    assert r is not None
    assert r.relation_type == "frictional"
    assert r.element_affinity_score == 45


def test_overall_score_range():
    """종합 점수는 element 70% + modality 30% 가중."""
    r = compute_compatibility("aries", "leo")
    assert r is not None
    # aries(fire, cardinal) × leo(fire, fixed)
    # element: 85, modality: cardinal-fixed = 72
    # overall = 85 * 0.7 + 72 * 0.3 = 59.5 + 21.6 = 81.1 → 81
    assert r.overall_score == 81


# ─────────────────────────── ADR-006 단정 필드 부재 ───────────────────────────

def test_no_marriage_outcome_field():
    """ADR-006 — 결혼·이별·재정 단정 필드 부재."""
    r = compute_compatibility("aries", "leo")
    assert r is not None
    forbidden_fields = {
        "marriage_outcome", "breakup_risk", "sex_compatibility", "financial_outcome",
    }
    for field in forbidden_fields:
        assert not hasattr(r, field), f"단정 필드 잔존: {field}"


def test_disclaimer_present():
    """면책 자동 포함."""
    r = compute_compatibility("aries", "leo")
    assert r is not None
    assert "단정 X" in r.disclaimer
    assert "단독 근거" in r.disclaimer


# ─────────────────────────── 프롬프트 포맷 ───────────────────────────

def test_format_compatibility_for_prompt_contains_safety():
    """프롬프트 포맷에 ADR-006 안전 장치 명시."""
    r = compute_compatibility("aries", "leo")
    assert r is not None
    text = format_compatibility_for_prompt(r)
    assert "ADR-006" in text
    assert "단정 금지" in text
    assert "양자리" in text
    assert "사자자리" in text


# ─────────────────────────── 144 매트릭스 비호출 검증 ───────────────────────────

def test_all_144_combinations_callable():
    """144 조합 모두 호출 가능 + None 반환 없음."""
    from engine.divination.star.scoring import ZODIAC_SIGNS

    count = 0
    for s1 in ZODIAC_SIGNS:
        for s2 in ZODIAC_SIGNS:
            r = compute_compatibility(s1.key, s2.key)
            assert r is not None, f"{s1.key} × {s2.key} 산출 실패"
            count += 1
    assert count == 144
