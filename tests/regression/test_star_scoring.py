"""ADR-068 회귀 — 서양 점성술 결정론 점수 (성하 공자) 검증.

12 황도대 (국제천문연맹 표준) + 4 element + 3 modality + 7 일일 톤
+ ADR-006 운명 단정 차단 (필드 부재 자동 검증).
"""

from datetime import date

from engine.divination.star.scoring import (
    ZODIAC_SIGNS,
    ELEMENT_LABELS_KO,
    MODALITY_LABELS_KO,
    DAILY_TONES_KO,
    DailyStarReading,
    sign_for_date,
    sign_by_key,
    daily_tone_for_sign,
    compute_daily_star_reading,
    format_sign_meta_for_prompt,
)


# ─────────────────────────── 12 황도대 메타 ───────────────────────────

def test_twelve_zodiac_signs():
    """12 황도대 전부 영속."""
    assert len(ZODIAC_SIGNS) == 12
    keys = {s.key for s in ZODIAC_SIGNS}
    expected = {
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    }
    assert keys == expected


def test_four_elements_split():
    """4 element 균등 분배 (fire·earth·air·water 각 3개)."""
    counts: dict[str, int] = {}
    for s in ZODIAC_SIGNS:
        counts[s.element] = counts.get(s.element, 0) + 1
    assert counts == {"fire": 3, "earth": 3, "air": 3, "water": 3}


def test_three_modalities_split():
    """3 modality 균등 분배 (cardinal·fixed·mutable 각 4개)."""
    counts: dict[str, int] = {}
    for s in ZODIAC_SIGNS:
        counts[s.modality] = counts.get(s.modality, 0) + 1
    assert counts == {"cardinal": 4, "fixed": 4, "mutable": 4}


def test_element_labels_complete():
    """element 한국어 라벨 4종."""
    assert set(ELEMENT_LABELS_KO.keys()) == {"fire", "earth", "air", "water"}


def test_modality_labels_complete():
    """modality 한국어 라벨 3종."""
    assert set(MODALITY_LABELS_KO.keys()) == {"cardinal", "fixed", "mutable"}


# ─────────────────────────── 별자리 결정 ───────────────────────────

def test_sign_for_date_taurus():
    """5월 15일 → 황소자리."""
    assert sign_for_date(date(1990, 5, 15)).key == "taurus"


def test_sign_for_date_capricorn_december():
    """12월 25일 → 염소자리 (연도 경계)."""
    assert sign_for_date(date(2026, 12, 25)).key == "capricorn"


def test_sign_for_date_capricorn_january():
    """1월 5일 → 염소자리 (연도 경계 다른 쪽)."""
    assert sign_for_date(date(2026, 1, 5)).key == "capricorn"


def test_sign_for_date_aquarius():
    """1월 25일 → 물병자리."""
    assert sign_for_date(date(2026, 1, 25)).key == "aquarius"


def test_sign_for_date_all_months_covered():
    """1~12월 모든 날짜가 12 별자리 중 하나에 매핑."""
    from datetime import timedelta
    cur = date(2026, 1, 1)
    end = date(2026, 12, 31)
    while cur <= end:
        s = sign_for_date(cur)
        assert s in ZODIAC_SIGNS
        cur += timedelta(days=1)


def test_sign_by_key():
    """영문 키 조회."""
    aries = sign_by_key("aries")
    assert aries is not None
    assert aries.label_ko == "양자리"
    assert sign_by_key("nonexistent") is None


# ─────────────────────────── 일일 톤 결정론 ───────────────────────────

def test_daily_tones_seven():
    """7 일일 톤."""
    assert len(DAILY_TONES_KO) == 7


def test_daily_tone_deterministic():
    """동일 별자리 + 동일 날짜 → 항상 동일 톤."""
    target = date(2026, 5, 20)
    t1 = daily_tone_for_sign("aries", target)
    t2 = daily_tone_for_sign("aries", target)
    assert t1 == t2
    assert t1 in DAILY_TONES_KO


def test_daily_tone_differs_by_date():
    """동일 별자리, 다른 날짜 → 톤 결정론 회전 (대부분 다름)."""
    diffs = 0
    base = daily_tone_for_sign("leo", date(2026, 5, 1))
    for i in range(1, 8):
        from datetime import timedelta
        t = daily_tone_for_sign("leo", date(2026, 5, 1) + timedelta(days=i))
        if t != base:
            diffs += 1
    assert diffs >= 5  # 7일 중 최소 5일은 변화


# ─────────────────────────── 통합 결과 ───────────────────────────

def test_compute_daily_star_reading_basic():
    """일일 별빛 풀이 통합 결과."""
    r = compute_daily_star_reading(date(1990, 5, 15), date(2026, 5, 20))
    assert isinstance(r, DailyStarReading)
    assert r.sign_key == "taurus"
    assert r.sign_label_ko == "황소자리"
    assert r.element_ko == "흙"
    assert "고정궁" in r.modality_ko
    assert r.ruling_planet == "Venus"
    assert r.target_date == "2026-05-20"
    assert r.daily_tone_ko in DAILY_TONES_KO


def test_reading_no_fate_mapping_fields():
    """★ ADR-006 — 운명·연애·재물·직업·럭키 매핑 필드 부재."""
    r = compute_daily_star_reading(date(1990, 5, 15), date(2026, 5, 20))
    assert not hasattr(r, "love_outcome")
    assert not hasattr(r, "career_outcome")
    assert not hasattr(r, "money_outcome")
    assert not hasattr(r, "lucky_number")
    assert not hasattr(r, "lucky_color")


def test_reading_disclaimer_adr_006():
    """면책에 ADR-006 핵심 차단 명시."""
    r = compute_daily_star_reading(date(1990, 5, 15), date(2026, 5, 20))
    assert "운명" in r.disclaimer
    assert "연애" in r.disclaimer
    assert "재물" in r.disclaimer
    assert "참고용" in r.disclaimer


def test_format_prompt_safety_clause():
    """Stage 2 프롬프트 주입 텍스트에 ADR-006 안전 절 자동 포함."""
    sign = sign_by_key("leo")
    assert sign is not None
    text = format_sign_meta_for_prompt(sign)
    assert "ADR-006" in text
    assert "단정 금지" in text
    assert "럭키" in text


def test_reading_deterministic_across_calls():
    """동일 입력 → 동일 결과 (결정론 보장)."""
    r1 = compute_daily_star_reading(date(1990, 5, 15), date(2026, 5, 20))
    r2 = compute_daily_star_reading(date(1990, 5, 15), date(2026, 5, 20))
    assert r1 == r2


def test_zodiac_meta_complete_fields():
    """모든 ZodiacSign에 9 필드 완비."""
    for s in ZODIAC_SIGNS:
        assert s.key
        assert s.label_ko
        assert s.label_en
        assert s.symbol
        assert s.element
        assert s.modality
        assert s.ruling_planet
        assert s.date_start
        assert s.date_end
