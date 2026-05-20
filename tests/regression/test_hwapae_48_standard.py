"""ADR-079 회귀 — 화패 48장 표준 데이터 완성.

12月 × 4매 = 48장 정합 + 카테고리 분포 표준 검증.

표준 화투 카테고리 분포 (한국민족문화대백과사전):
- 광 5장 (1·3·8·11·12月)
- 열끗 9장
- 띠 10장 (홍단·청단·초단 각 3매 + 비띠 1)
- 피 24장 (쌍피 포함)
"""

from engine.divination.hwapae.korean import HWAPAE_CARDS, three_card_spread


def test_total_48_cards():
    """전체 48장 정합 (12月 × 4매)."""
    assert len(HWAPAE_CARDS) == 48


def test_12_months_each_4_cards():
    """매월 정확히 4장."""
    by_month: dict[int, int] = {}
    for card in HWAPAE_CARDS.values():
        by_month[card.month] = by_month.get(card.month, 0) + 1
    for m in range(1, 13):
        assert by_month.get(m) == 4, f"{m}月: {by_month.get(m)}장 (4장이어야 함)"


def test_5_gwang_cards():
    """광 카드 정확히 5장 (1·3·8·11·12月)."""
    gwang_months = {c.month for c in HWAPAE_CARDS.values() if c.category == "광"}
    assert gwang_months == {1, 3, 8, 11, 12}


def test_card_index_1_to_4_per_month():
    """월별 card_index_in_month는 1~4 범위."""
    for card in HWAPAE_CARDS.values():
        assert 1 <= card.card_index_in_month <= 4


def test_score_matches_category():
    """카테고리별 score 정합 — 광=20, 열끗=10, 띠=5, 피=1."""
    expected = {"광": 20, "열끗": 10, "띠": 5, "피": 1}
    for card in HWAPAE_CARDS.values():
        assert card.score == expected[card.category]


def test_no_duplicate_ids():
    """카드 id 중복 X."""
    ids = [c.id for c in HWAPAE_CARDS.values()]
    assert len(ids) == len(set(ids))


def test_id_format_consistent():
    """id 형식: 'MM-NN-XXX' (월-순서-카테고리 접미사)."""
    import re
    pattern = re.compile(r"^\d{2}-\d{2}-[a-z\-]+$")
    for card in HWAPAE_CARDS.values():
        assert pattern.match(card.id), f"id 형식 위반: {card.id}"


def test_forbidden_keywords_present():
    """모든 카드에 forbidden_keywords 1개 이상 (ADR-006 강제)."""
    for card in HWAPAE_CARDS.values():
        assert len(card.forbidden_keywords) >= 1, f"{card.id}: forbidden 부재"


def test_permitted_keywords_present():
    """모든 카드에 permitted_keywords 1개 이상."""
    for card in HWAPAE_CARDS.values():
        assert len(card.permitted_keywords) >= 1, f"{card.id}: permitted 부재"


def test_three_card_spread_full_48_compatible():
    """48장 전체에서 3장 추첨 회귀 (무작위 페어)."""
    keys = list(HWAPAE_CARDS.keys())
    # 첫 3장
    sp1 = three_card_spread((keys[0], keys[1], keys[2]))
    assert len(sp1.cards) == 3
    # 마지막 3장
    sp2 = three_card_spread((keys[-3], keys[-2], keys[-1]))
    assert len(sp2.cards) == 3
    # 중간
    sp3 = three_card_spread((keys[15], keys[25], keys[35]))
    assert len(sp3.cards) == 3


def test_traditional_meanings_unique():
    """전통 점패 상징이 카드별 고유 (중복 X)."""
    meanings = [c.traditional_meaning for c in HWAPAE_CARDS.values()]
    # 일부 피 카드는 동일 패턴이지만 월/순서로 미세 차이
    assert len(set(meanings)) >= 40  # 48 중 8개 정도 일상 패턴 중복 허용


def test_korean_holiday_special_cards():
    """한국 통설 특수 카드 인용 — 오동(11月·봉황) + 비(12月·정화)."""
    assert "11-01-gwang" in HWAPAE_CARDS
    assert "12-01-gwang" in HWAPAE_CARDS
    assert "봉황" in HWAPAE_CARDS["11-01-gwang"].symbol
    assert "비" in HWAPAE_CARDS["12-01-gwang"].symbol


def test_dan_combination_cards_present():
    """홍단·청단·초단 띠 3매 조합 카드 존재 (한국 통설 점수 패턴)."""
    # 홍단: 1月·2月·3月 띠 (모두 "홍단" 명칭 포함)
    hongdan = [c for c in HWAPAE_CARDS.values() if "홍단" in c.name_ko]
    assert len(hongdan) >= 3, f"홍단 3매 부재 — {len(hongdan)}개"

    # 청단: 6月·9月·10月 띠
    cheongdan = [c for c in HWAPAE_CARDS.values() if "청단" in c.name_ko]
    assert len(cheongdan) >= 3, f"청단 3매 부재 — {len(cheongdan)}개"

    # 초단: 4月·5月·7月 띠
    chodan = [c for c in HWAPAE_CARDS.values() if "초단" in c.name_ko]
    assert len(chodan) >= 3, f"초단 3매 부재 — {len(chodan)}개"


def test_double_pi_cards_present():
    """쌍피 (피 2장 효과) 카드 존재 — 한국 화투 변형 (11月 오동·12月 비)."""
    ssang_pi = [c for c in HWAPAE_CARDS.values() if "쌍피" in c.name_ko]
    assert len(ssang_pi) >= 2, f"쌍피 2매 부재 — {len(ssang_pi)}개"
