"""ADR-118·119·120·121 회귀 — palm 5 카드 한국 전통 결정론 검증.

영역:
1. 토정비결 144괘 (ADR-118)
2. 12지 띠 운세 + 12×12 궁합 (ADR-119)
3. 산통점 (ADR-120)
4. 부적 4 표준 (ADR-121)
"""

from datetime import date

from engine.divination.tojeong import (
    SIXTY_FOUR_TOJEONG,
    compute_tojeong_for_year,
    hexagram_by_id,
)
from engine.divination.zodiac_ko import (
    ZODIAC_ANIMALS,
    animal_by_year,
    animal_by_key,
    compute_animal_compatibility,
    compute_year_fortune,
)
from engine.divination.santong import (
    SANTONG_STICKS,
    compute_santong_reading,
)
from engine.divination.talisman import (
    TALISMAN_TYPES,
    talisman_by_key,
    compute_talisman_reading,
)


# ─────────────────────────── ADR-118 토정비결 ───────────────────────────

def test_tojeong_144_count():
    """토정비결 144괘 전부 영속."""
    assert len(SIXTY_FOUR_TOJEONG) == 144


def test_tojeong_first_last():
    """첫 괘 = 111, 마지막 = 863."""
    assert SIXTY_FOUR_TOJEONG[0].label_ko == "111"
    assert SIXTY_FOUR_TOJEONG[143].label_ko == "863"


def test_tojeong_compute():
    """1990-05-15 + 2026 → 결정론 산출."""
    r = compute_tojeong_for_year(date(1990, 5, 15), 2026)
    assert r is not None
    # 상괘: (2026-1900) % 8 + 1 = 126 % 8 + 1 = 6+1 = 7
    # 중괘: (5-1) % 6 + 1 = 5
    # 하괘: (15-1) % 3 + 1 = 14%3+1 = 3
    assert r.upper == 7
    assert r.middle == 5
    assert r.lower == 3
    assert r.label_ko == "753"


def test_tojeong_deterministic():
    """동일 입력 → 동일 괘."""
    r1 = compute_tojeong_for_year(date(2000, 1, 1), 2026)
    r2 = compute_tojeong_for_year(date(2000, 1, 1), 2026)
    assert r1 == r2


def test_tojeong_invalid_year():
    """범위 외 년도 → None."""
    assert compute_tojeong_for_year(date(1990, 5, 15), 1800) is None
    assert compute_tojeong_for_year(date(1990, 5, 15), 2300) is None


def test_tojeong_flow_tone_no_assertion():
    """토정비결 144괘 모두 단정 어휘 차단."""
    forbidden = ["반드시", "확실히", "100%", "단명", "이혼수", "파산"]
    for h in SIXTY_FOUR_TOJEONG:
        for word in forbidden:
            assert word not in h.flow_tone_ko, f"{h.label_ko}: {word} 잔존"


# ─────────────────────────── ADR-119 12지 띠 ───────────────────────────

def test_zodiac_12_animals():
    """12지신 전부 영속."""
    assert len(ZODIAC_ANIMALS) == 12
    keys = {a.key for a in ZODIAC_ANIMALS}
    expected = {"ja","chuk","in","myo","jin","sa","o","mi","sin","yu","sul","hae"}
    assert keys == expected


def test_zodiac_1990_horse():
    """1990 = 말띠."""
    a = animal_by_year(1990)
    assert a.label_ko == "말"
    assert a.hanja == "午"


def test_zodiac_samhap():
    """삼합 — 호랑이+말+개 (寅午戌 火)."""
    r1 = compute_animal_compatibility("in", "o")
    r2 = compute_animal_compatibility("in", "sul")
    r3 = compute_animal_compatibility("o", "sul")
    assert r1.relation_type == "삼합"
    assert r2.relation_type == "삼합"
    assert r3.relation_type == "삼합"
    assert r1.score == 90


def test_zodiac_yukhap():
    """육합 — 子丑·寅亥·卯戌·辰酉·巳申·午未."""
    r = compute_animal_compatibility("o", "mi")  # 午未
    assert r.relation_type == "육합"
    assert r.score == 85


def test_zodiac_wonjinsal():
    """원진살 — 子未."""
    r = compute_animal_compatibility("ja", "mi")
    assert r.relation_type == "원진살"
    assert r.score == 45


def test_zodiac_same_animal():
    """동일 띠 — 별도 분류."""
    r = compute_animal_compatibility("o", "o")
    assert r.relation_type == "동일"
    assert r.score == 75


def test_zodiac_invalid_keys():
    """잘못된 키 → None."""
    assert compute_animal_compatibility("invalid", "o") is None
    assert compute_animal_compatibility("o", "invalid") is None


def test_zodiac_year_fortune():
    """1990 (말띠) + 2026 (말띠) → 동일."""
    r = compute_year_fortune(1990, 2026)
    assert r is not None
    assert r.relation_type == "동일"


def test_zodiac_144_matrix_callable():
    """12×12 = 144 조합 모두 호출 가능."""
    count = 0
    for a1 in ZODIAC_ANIMALS:
        for a2 in ZODIAC_ANIMALS:
            r = compute_animal_compatibility(a1.key, a2.key)
            assert r is not None
            count += 1
    assert count == 144


# ─────────────────────────── ADR-120 산통점 ───────────────────────────

def test_santong_8_sticks():
    """8 산가지 영속."""
    assert len(SANTONG_STICKS) == 8


def test_santong_compute():
    """3 산가지 뽑기 결정론."""
    r = compute_santong_reading(1, 2, 3)
    assert r is not None
    assert r.label_ko == "일·이·삼"
    assert r.sum_value == 6


def test_santong_deterministic():
    """동일 입력 → 동일 점괘."""
    r1 = compute_santong_reading(5, 5, 5)
    r2 = compute_santong_reading(5, 5, 5)
    assert r1 == r2


def test_santong_sum_range():
    """sum 3~24 모두 22 톤 매핑."""
    r_min = compute_santong_reading(1, 1, 1)
    r_max = compute_santong_reading(8, 8, 8)
    assert r_min.sum_value == 3
    assert r_max.sum_value == 24


def test_santong_invalid():
    """잘못된 값 → None."""
    assert compute_santong_reading(0, 1, 1) is None
    assert compute_santong_reading(9, 1, 1) is None


def test_santong_disclaimer():
    """면책 + 이능화 출처."""
    r = compute_santong_reading(3, 4, 5)
    assert "이능화" in r.disclaimer
    assert "1927" in r.disclaimer or "조선무속고" in r.disclaimer


# ─────────────────────────── ADR-121 부적 4 표준 ───────────────────────────

def test_talisman_4_types():
    """부적 4 표준 영속."""
    assert len(TALISMAN_TYPES) == 4
    keys = {t.key for t in TALISMAN_TYPES}
    assert keys == {"hapgyeok", "jaemul", "yeonae", "geongang"}


def test_talisman_hapgyeok():
    """합격부 메타."""
    t = talisman_by_key("hapgyeok")
    assert t is not None
    assert t.label_ko == "합격부"
    assert t.hanja == "合格符"
    assert "배움의 결" in t.purpose_flow_ko


def test_talisman_jaemul():
    """재물부 메타."""
    t = talisman_by_key("jaemul")
    assert t is not None
    assert t.label_ko == "재물부"
    assert "재물의 결" in t.purpose_flow_ko


def test_talisman_yeonae():
    """연애부 메타 + ADR-006 정합."""
    t = talisman_by_key("yeonae")
    assert t is not None
    assert "결혼·이별·재결합 단정 X" in t.description


def test_talisman_geongang():
    """건강부 메타 + 의료 진단 차단."""
    t = talisman_by_key("geongang")
    assert t is not None
    assert "의료 진단 X" in t.description
    assert "의사 진단 대체 절대 X" in t.description


def test_talisman_invalid_key():
    """잘못된 키 → None."""
    assert talisman_by_key("invalid") is None
    assert compute_talisman_reading("invalid") is None


def test_talisman_reading_disclaimer():
    """면책 자동 포함."""
    r = compute_talisman_reading("hapgyeok")
    assert r is not None
    assert "효과 보장 X" in r.disclaimer
    assert "ADR-006" in r.disclaimer


def test_talisman_no_guaranteed_outcome_field():
    """ADR-006 단정 필드 부재."""
    r = compute_talisman_reading("jaemul")
    forbidden_fields = {"guaranteed_outcome", "cures_disease"}
    for f in forbidden_fields:
        assert not hasattr(r, f)
