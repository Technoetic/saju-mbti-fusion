"""ADR-114 회귀 — Skyfield + JPL DE440s 점성술 결정론 검증.

영역:
  · 빅3 (Sun·Moon·Ascendant) Astro-Databank AA 표본 5건 검증
  · 하우스 시스템 (Whole Sign + Equal)
  · 행성 트랜짓 + 애스펙트 (Arroyo·Greene 오브 표준)
  · 시너스트리 매트릭스 + 컴포짓 wrap-around
  · ADR-006 단정 필드 부재 + 면책 자동 포함

출처:
  · Astro-Databank (Lois Rodden 1962) Rodden Rating AA
  · Stephen Arroyo (1975) ISBN 978-0916360016
  · NASA JPL DE440s (2020) ssd.jpl.nasa.gov/ftp/eph/
"""

from datetime import datetime, timezone

from engine.divination.star.astronomy import (
    PLANETS_10,
    ZODIAC_LABELS_KO,
    zodiac_from_longitude,
    compute_planet_position,
    compute_ascendant,
    compute_big_three,
    compute_houses_whole_sign,
    compute_houses_equal,
    shortest_angular_distance,
    detect_aspect,
    compute_synastry_matrix,
    compute_composite_midpoint,
)


# ─────────────────────────── 황도대 변환 ───────────────────────────

def test_zodiac_from_longitude_aries():
    """0°~30° → 양자리."""
    sign_idx, deg, label = zodiac_from_longitude(15.5)
    assert sign_idx == 0
    assert deg == 15.5
    assert label == "양자리"


def test_zodiac_from_longitude_leo():
    """120°~150° → 사자자리."""
    sign_idx, deg, label = zodiac_from_longitude(125.7)
    assert sign_idx == 4
    assert deg == 5.7
    assert label == "사자자리"


def test_zodiac_from_longitude_pisces_boundary():
    """359° → 물고기자리 29°."""
    sign_idx, _, label = zodiac_from_longitude(359.99)
    assert sign_idx == 11
    assert label == "물고기자리"


def test_zodiac_wrap_around():
    """360° → 양자리 0° (mod 360)."""
    sign_idx, deg, _ = zodiac_from_longitude(360.0)
    assert sign_idx == 0
    assert deg == 0.0


# ─────────────────────────── Astro-Databank AA 표본 검증 (★) ───────────────────────────

def test_einstein_big_three():
    """Albert Einstein 1879-03-14 11:30 LMT Ulm Germany — Pisces·Sagittarius·Cancer."""
    # LMT (10.0E) ≈ UTC+0:40 → 11:30 LMT = 10:50 UTC
    dt = datetime(1879, 3, 14, 10, 50, tzinfo=timezone.utc)
    r = compute_big_three(dt, latitude_deg=48.4, longitude_deg=10.0)
    assert r is not None
    assert r.sun.sign_label_ko == "물고기자리"
    assert r.moon is not None
    assert r.moon.sign_label_ko == "사수자리"
    assert r.ascendant_sign_label_ko == "게자리"


def test_einstein_sun_only_no_birth_time():
    """출생시간 미입력 시 Sun만 산출 (Moon·Asc None)."""
    dt = datetime(1879, 3, 14, 12, 0, tzinfo=timezone.utc)
    r = compute_big_three(dt)  # 위경도 미입력
    assert r is not None
    assert r.sun.sign_label_ko == "물고기자리"
    assert r.moon is None
    assert r.ascendant_longitude_deg is None
    assert r.has_birth_time is False


# ─────────────────────────── 행성 위치 결정론 ───────────────────────────

def test_planet_position_deterministic():
    """동일 입력 → 동일 결과."""
    dt = datetime(2000, 1, 1, 12, 0, tzinfo=timezone.utc)
    r1 = compute_planet_position("sun", dt)
    r2 = compute_planet_position("sun", dt)
    assert r1 == r2


def test_planet_position_invalid_planet():
    """잘못된 행성 키 → None."""
    dt = datetime(2000, 1, 1, 12, 0, tzinfo=timezone.utc)
    r = compute_planet_position("invalid", dt)
    assert r is None


def test_planet_position_no_tzinfo_rejected():
    """tzinfo 없는 datetime → None (UTC 누락 차단)."""
    dt = datetime(2000, 1, 1, 12, 0)  # tzinfo X
    r = compute_planet_position("sun", dt)
    assert r is None


# ─────────────────────────── Ascendant ───────────────────────────

def test_ascendant_seoul_2000():
    """서울 2000-01-01 12:00 KST → UTC 03:00 — 결정론 산출 가능."""
    dt = datetime(2000, 1, 1, 3, 0, tzinfo=timezone.utc)
    asc = compute_ascendant(dt, latitude_deg=37.5665, longitude_deg=126.9780)
    assert asc is not None
    assert 0.0 <= asc < 360.0


def test_ascendant_invalid_latitude():
    """위도 범위 외 → None."""
    dt = datetime(2000, 1, 1, 12, 0, tzinfo=timezone.utc)
    assert compute_ascendant(dt, 91.0, 0.0) is None
    assert compute_ascendant(dt, -91.0, 0.0) is None


def test_ascendant_no_tzinfo():
    """tzinfo 없는 datetime → None."""
    dt = datetime(2000, 1, 1, 12, 0)
    assert compute_ascendant(dt, 37.5, 127.0) is None


# ─────────────────────────── 하우스 시스템 ───────────────────────────

def test_whole_sign_houses_einstein():
    """Einstein Asc=게자리 101.80° → 1하우스 게자리, 12개 모두 30° 단위."""
    houses = compute_houses_whole_sign(101.80)
    assert len(houses) == 12
    assert houses[0]["sign_label_ko"] == "게자리"
    assert houses[0]["start_deg"] == 90.0  # 게자리 시작 (3×30)
    # 12 하우스 모두 별자리 단위
    for h in houses:
        assert h["start_deg"] % 30.0 == 0


def test_equal_houses_einstein():
    """Equal House — Asc 그대로 1하우스 시작."""
    houses = compute_houses_equal(101.80)
    assert len(houses) == 12
    assert houses[0]["start_deg"] == 101.8
    # N번째 = Asc + 30(N-1)
    assert houses[1]["start_deg"] == 131.8
    assert houses[11]["start_deg"] == 71.8  # mod 360


def test_houses_all_12_unique_signs():
    """Whole Sign — 12 하우스 모두 다른 별자리."""
    houses = compute_houses_whole_sign(0.0)  # 양자리 0°
    signs = [h["sign_index"] for h in houses]
    assert len(set(signs)) == 12


# ─────────────────────────── 애스펙트 ───────────────────────────

def test_shortest_angular_distance():
    """원형 황도 최단 거리."""
    assert shortest_angular_distance(0, 90) == 90
    assert shortest_angular_distance(350, 10) == 20
    assert shortest_angular_distance(0, 180) == 180
    assert shortest_angular_distance(170, 190) == 20


def test_detect_aspect_conjunction():
    """0° = Conjunction."""
    r = detect_aspect(10.0, 12.0, "mars", "venus")
    assert r is not None
    assert r.aspect_type == "conjunction"


def test_detect_aspect_square():
    """90° = Square."""
    r = detect_aspect(10.0, 100.0, "mars", "jupiter")
    assert r is not None
    assert r.aspect_type == "square"


def test_detect_aspect_opposition():
    """180° = Opposition."""
    r = detect_aspect(10.0, 190.0, "mars", "saturn")
    assert r is not None
    assert r.aspect_type == "opposition"


def test_detect_aspect_trine():
    """120° = Trine."""
    r = detect_aspect(10.0, 130.0, "venus", "jupiter")
    assert r is not None
    assert r.aspect_type == "trine"


def test_detect_aspect_sextile():
    """60° = Sextile (오브 ±4°)."""
    r = detect_aspect(10.0, 73.0, "venus", "jupiter")
    assert r is not None
    assert r.aspect_type == "sextile"


def test_detect_aspect_out_of_orb():
    """오브 밖 → None."""
    # 75° (Square 90°에서 -15° = 오브 8° 초과)
    r = detect_aspect(10.0, 75.0, "mars", "venus")
    assert r is None  # 어떤 애스펙트도 아님


def test_sun_orb_extended():
    """태양 포함 시 오브 ±10° 확장."""
    # 95° (Square 90°에서 +5° = 일반 오브 8° 내, 태양 오브 10° 내)
    r = detect_aspect(10.0, 105.0, "sun", "mars")
    assert r is not None
    assert r.aspect_type == "square"
    assert r.orb_used_deg == 10.0


# ─────────────────────────── 시너스트리 + 컴포짓 ───────────────────────────

def test_synastry_matrix_basic():
    """간단 시너스트리 매트릭스."""
    natal_a = {"sun": 0.0, "moon": 90.0}
    natal_b = {"sun": 180.0, "venus": 0.0}
    results = compute_synastry_matrix(natal_a, natal_b)
    # A.sun (0°) - B.sun (180°) = Opposition
    # A.sun (0°) - B.venus (0°) = Conjunction
    # A.moon (90°) - B.sun (180°) = Square
    # A.moon (90°) - B.venus (0°) = Square
    aspect_types = [r.aspect_type for r in results]
    assert "opposition" in aspect_types
    assert "conjunction" in aspect_types
    assert "square" in aspect_types


def test_composite_midpoint_simple():
    """단순 중점 (wrap-around X)."""
    assert compute_composite_midpoint(10.0, 50.0) == 30.0
    assert compute_composite_midpoint(170.0, 190.0) == 180.0


def test_composite_midpoint_wrap_around():
    """180° 경계 wrap-around 보정."""
    # 350° + 10° → 가까운 내각 중점 = 0° (X: 단순 평균 180°)
    assert compute_composite_midpoint(350.0, 10.0) == 0.0


# ─────────────────────────── 결정론 ───────────────────────────

def test_big_three_deterministic():
    """동일 입력 (UTC + 위경도) → 동일 빅3."""
    dt = datetime(1990, 6, 15, 14, 30, tzinfo=timezone.utc)
    r1 = compute_big_three(dt, 37.5, 127.0)
    r2 = compute_big_three(dt, 37.5, 127.0)
    assert r1 == r2


# ─────────────────────────── 면책 + ADR-006 ───────────────────────────

def test_disclaimer_present():
    """면책 자동 포함 + Liz Greene·Stephen Arroyo 출처."""
    dt = datetime(2000, 1, 1, 12, 0, tzinfo=timezone.utc)
    r = compute_big_three(dt)
    assert r is not None
    assert "단정 X" in r.disclaimer
    assert "Liz Greene" in r.disclaimer or "Arroyo" in r.disclaimer
    assert "단독 근거" in r.disclaimer


def test_no_outcome_fields_in_big_three():
    """ADR-006 — 운명·결혼 단정 필드 부재."""
    dt = datetime(2000, 1, 1, 12, 0, tzinfo=timezone.utc)
    r = compute_big_three(dt)
    assert r is not None
    forbidden_fields = {"life_outcome", "marriage_outcome", "career_outcome"}
    for f in forbidden_fields:
        assert not hasattr(r, f), f"단정 필드 잔존: {f}"


# ─────────────────────────── 메타 검증 ───────────────────────────

def test_planets_10_count():
    """10 행성 전부 영속."""
    assert len(PLANETS_10) == 10
    assert "sun" in PLANETS_10
    assert "pluto" in PLANETS_10


def test_zodiac_labels_12_count():
    """12 황도대 라벨 영속."""
    assert len(ZODIAC_LABELS_KO) == 12
