"""ADR-112 회귀 — 한국 정통 윷점 64괘 결정론 검증.

영역:
  · 4사위 (도·개·걸·윷) × 3회 조합 = 64괘 전부 영속
  · 동일 입력 → 동일 괘 결정론
  · ADR-006 길흉 단정 차단 (흐름 톤만)
  · 모(5) 단일화 (윷=4로 처리)

출처:
  · 국립민속박물관 PS0100200100109517400000
  · 이능화 (1927) 조선무속고 ISBN 9788936471391
"""

from engine.divination.yutjeom import (
    YUT_SIDES,
    SIXTY_FOUR_HEXAGRAMS,
    compute_yut_hexagram,
    hexagram_by_id,
    format_hexagram_for_prompt,
)
from engine.divination.yutjeom.scoring import yut_side_by_value


# ─────────────────────────── 4사위 ───────────────────────────

def test_four_sides_count():
    """4사위 전부 영속."""
    assert len(YUT_SIDES) == 4
    keys = {s.key for s in YUT_SIDES}
    assert keys == {"do", "gae", "geol", "yut"}


def test_side_values():
    """사위 값 1~4."""
    values = {s.value for s in YUT_SIDES}
    assert values == {1, 2, 3, 4}


def test_mo_unified_to_yut():
    """모(5) → 윷(4) 단일화."""
    mo = yut_side_by_value(5)
    yut = yut_side_by_value(4)
    assert mo == yut
    assert mo is not None
    assert mo.key == "yut"


def test_invalid_value_returns_none():
    """잘못된 값 → None."""
    assert yut_side_by_value(0) is None
    assert yut_side_by_value(6) is None
    assert yut_side_by_value(-1) is None


# ─────────────────────────── 64괘 ───────────────────────────

def test_64_hexagrams_count():
    """64괘 전부 영속."""
    assert len(SIXTY_FOUR_HEXAGRAMS) == 64


def test_64_hexagrams_unique_ids():
    """64괘 ID 0~63 순차 유일."""
    ids = [h.hex_id for h in SIXTY_FOUR_HEXAGRAMS]
    assert ids == list(range(64))


def test_first_hexagram_dododo():
    """첫 괘 = 도도도 (hex_id=0)."""
    h = hexagram_by_id(0)
    assert h is not None
    assert h.label_ko == "도도도"
    assert h.upper == "do"
    assert h.middle == "do"
    assert h.lower == "do"


def test_last_hexagram_yutyutyut():
    """마지막 괘 = 윷윷윷 (hex_id=63)."""
    h = hexagram_by_id(63)
    assert h is not None
    assert h.label_ko == "윷윷윷"
    assert h.upper == "yut"
    assert h.middle == "yut"
    assert h.lower == "yut"


# ─────────────────────────── 결정론 ───────────────────────────

def test_compute_deterministic():
    """동일 3사위 → 동일 괘 (결정론)."""
    r1 = compute_yut_hexagram(2, 3, 4)
    r2 = compute_yut_hexagram(2, 3, 4)
    assert r1 == r2


def test_compute_dododo():
    """1-1-1 → 도도도."""
    r = compute_yut_hexagram(1, 1, 1)
    assert r is not None
    assert r.hex_id == 0
    assert r.label_ko == "도도도"


def test_compute_yutyutyut():
    """4-4-4 → 윷윷윷."""
    r = compute_yut_hexagram(4, 4, 4)
    assert r is not None
    assert r.hex_id == 63


def test_compute_dogegeol():
    """1-2-3 → 도개걸."""
    r = compute_yut_hexagram(1, 2, 3)
    assert r is not None
    assert r.label_ko == "도개걸"
    # hex_id = 0*16 + 1*4 + 2 = 6
    assert r.hex_id == 6


def test_compute_mo_unified():
    """모(5) 입력도 윷(4)로 단일화."""
    r_yut = compute_yut_hexagram(4, 4, 4)
    r_mo = compute_yut_hexagram(5, 5, 5)
    assert r_yut == r_mo


def test_compute_invalid_returns_none():
    """잘못된 입력 → None."""
    assert compute_yut_hexagram(0, 1, 1) is None
    assert compute_yut_hexagram(1, 0, 1) is None
    assert compute_yut_hexagram(1, 1, 7) is None


# ─────────────────────────── 64괘 전체 호출 ───────────────────────────

def test_all_64_callable():
    """64괘 전부 호출 가능 (4×4×4 = 64)."""
    seen = set()
    for u in range(1, 5):
        for m in range(1, 5):
            for low in range(1, 5):
                r = compute_yut_hexagram(u, m, low)
                assert r is not None
                seen.add(r.hex_id)
    assert len(seen) == 64


def test_hexagram_by_id_invalid():
    """잘못된 ID → None."""
    assert hexagram_by_id(-1) is None
    assert hexagram_by_id(64) is None
    assert hexagram_by_id(100) is None


# ─────────────────────────── 흐름 톤 (ADR-006) ───────────────────────────

def test_all_hexagrams_have_flow_tone():
    """64괘 모두 흐름 톤 보유."""
    for h in SIXTY_FOUR_HEXAGRAMS:
        assert h.flow_tone_ko != ""
        # 단정 어휘 차단 (간단 검증)
        forbidden = ["길흉", "단명", "이혼", "사망", "재물운"]
        for word in forbidden:
            assert word not in h.flow_tone_ko, f"{h.label_ko} 단정 어휘 잔존: {word}"


# ─────────────────────────── 프롬프트 포맷 ───────────────────────────

def test_format_prompt_includes_safety():
    """프롬프트 포맷에 ADR-006 안전 장치 + 면책 포함."""
    r = compute_yut_hexagram(1, 2, 3)
    assert r is not None
    text = format_hexagram_for_prompt(r)
    assert "ADR-006" in text
    assert "단정 금지" in text
    assert "도개걸" in text
    assert "국립민속박물관" in text or "이능화" in text
