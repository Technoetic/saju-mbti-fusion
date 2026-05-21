"""ADR-107 회귀 — 동양 28수 (천상열차분야지도) 결정론 검증.

영역:
  · 4 궁 (청룡·현무·백호·주작) 각 7수 = 28수 전부
  · 28일 순환 결정론
  · ADR-006 길흉 단정 필드 부재 자동 검증
  · 한국 천상열차분야지도 정통 분류 정합
"""

from datetime import date

from engine.divination.star.twenty_eight_mansions import (
    FOUR_PALACES,
    TWENTY_EIGHT_MANSIONS,
    palace_by_key,
    mansion_by_idx,
    mansion_by_key,
    mansion_for_date,
    mansions_in_palace,
    compute_twenty_eight_mansion_reading,
    format_mansion_for_prompt,
)


# ─────────────────────────── 4 궁 ───────────────────────────

def test_four_palaces_count():
    """4 궁 전부 영속."""
    assert len(FOUR_PALACES) == 4
    keys = {p.key for p in FOUR_PALACES}
    expected = {"azure_dragon", "black_tortoise", "white_tiger", "vermilion_bird"}
    assert keys == expected


def test_palace_directions():
    """4 궁 방위 정합 (동·북·서·남)."""
    palace_dir = {p.key: p.direction_ko for p in FOUR_PALACES}
    assert palace_dir["azure_dragon"] == "동"
    assert palace_dir["black_tortoise"] == "북"
    assert palace_dir["white_tiger"] == "서"
    assert palace_dir["vermilion_bird"] == "남"


def test_palace_seasons():
    """4 궁 계절 정합 (봄·겨울·가을·여름)."""
    palace_season = {p.key: p.season_ko for p in FOUR_PALACES}
    assert palace_season["azure_dragon"] == "봄"
    assert palace_season["black_tortoise"] == "겨울"
    assert palace_season["white_tiger"] == "가을"
    assert palace_season["vermilion_bird"] == "여름"


# ─────────────────────────── 28수 ───────────────────────────

def test_twenty_eight_mansions_count():
    """28수 전부 영속."""
    assert len(TWENTY_EIGHT_MANSIONS) == 28


def test_twenty_eight_mansions_unique_keys():
    """28수 키 중복 없음."""
    keys = {m.key for m in TWENTY_EIGHT_MANSIONS}
    assert len(keys) == 28


def test_twenty_eight_mansions_idx_sequence():
    """28수 idx 0~27 순차."""
    for i, m in enumerate(TWENTY_EIGHT_MANSIONS):
        assert m.idx == i


def test_mansions_per_palace_equals_seven():
    """각 4궁당 7수 정합."""
    for palace in FOUR_PALACES:
        mansions = mansions_in_palace(palace.key)
        assert len(mansions) == 7, f"{palace.key} 7수 아님"


def test_azure_dragon_first_mansion():
    """동방 청룡 첫 수 = 각수 (角宿)."""
    m = mansion_by_idx(0)
    assert m is not None
    assert m.label_ko == "각수"
    assert m.label_hanja == "角宿"
    assert m.palace_key == "azure_dragon"


def test_vermilion_bird_last_mansion():
    """남방 주작 마지막 수 = 진수 (軫宿)."""
    m = mansion_by_idx(27)
    assert m is not None
    assert m.label_ko == "진수"
    assert m.label_hanja == "軫宿"
    assert m.palace_key == "vermilion_bird"


def test_horn_mansion_animal():
    """각수 배속 동물 = 교룡 (28수 정통)."""
    m = mansion_by_key("horn")
    assert m is not None
    assert m.animal_ko == "교룡"


# ─────────────────────────── 결정론 ───────────────────────────

def test_mansion_for_date_deterministic():
    """동일 날짜 → 동일 수 (결정론)."""
    d = date(2026, 5, 21)
    m1 = mansion_for_date(d)
    m2 = mansion_for_date(d)
    assert m1.key == m2.key


def test_mansion_for_date_28_day_cycle():
    """28일 주기 순환."""
    d1 = date(2026, 5, 21)
    d2 = date(2026, 6, 18)  # +28일
    m1 = mansion_for_date(d1)
    m2 = mansion_for_date(d2)
    assert m1.key == m2.key


def test_mansion_for_epoch_date():
    """1900-01-01 = 각수 (epoch)."""
    m = mansion_for_date(date(1900, 1, 1))
    assert m.key == "horn"
    assert m.idx == 0


def test_mansion_invalid_idx_returns_none():
    """잘못된 idx → None."""
    assert mansion_by_idx(-1) is None
    assert mansion_by_idx(28) is None
    assert mansion_by_idx(100) is None


def test_mansion_invalid_key_returns_none():
    """잘못된 key → None."""
    assert mansion_by_key("invalid") is None


# ─────────────────────────── ADR-006 단정 필드 부재 ───────────────────────────

def test_no_lucky_outcome_field():
    """ADR-006 — 길흉·관혼상제 단정 필드 부재."""
    r = compute_twenty_eight_mansion_reading(date(2026, 5, 21))
    forbidden_fields = {"lucky_outcome", "unlucky_outcome", "marriage_day", "funeral_day"}
    for field in forbidden_fields:
        assert not hasattr(r, field), f"단정 필드 잔존: {field}"


def test_disclaimer_present():
    """면책 자동 포함 + 학파 출처 명시."""
    r = compute_twenty_eight_mansion_reading(date(2026, 5, 21))
    assert "천상열차분야지도" in r.disclaimer
    assert "국보 228호" in r.disclaimer
    assert "단정 X" in r.disclaimer
    assert "안상현" in r.disclaimer or "KCI" in r.disclaimer


# ─────────────────────────── 프롬프트 포맷 ───────────────────────────

def test_format_mansion_for_prompt_safety():
    """프롬프트 포맷에 ADR-006 안전 장치 명시."""
    r = compute_twenty_eight_mansion_reading(date(1900, 1, 1))
    text = format_mansion_for_prompt(r)
    assert "ADR-006" in text
    assert "단정 금지" in text
    assert "각수" in text
    assert "천상열차분야지도" in text


# ─────────────────────────── 28수 전체 호출 검증 ───────────────────────────

def test_all_28_mansions_callable():
    """1900-01-01부터 28일간 모든 수 정확히 한 번씩 등장."""
    seen = set()
    for i in range(28):
        d = date(1900, 1, 1 + i) if i < 30 else date(1900, 1, 1)
        m = mansion_for_date(d)
        seen.add(m.key)
    assert len(seen) == 28


def test_palace_key_validity():
    """모든 28수의 palace_key가 4궁 중 하나."""
    valid_palaces = {p.key for p in FOUR_PALACES}
    for m in TWENTY_EIGHT_MANSIONS:
        assert m.palace_key in valid_palaces


def test_palace_by_key_returns_correct():
    """palace_by_key 정합."""
    p = palace_by_key("azure_dragon")
    assert p is not None
    assert p.label_ko == "동방 청룡"
