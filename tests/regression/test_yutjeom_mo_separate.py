"""ADR-145 회귀 — yutjeom 모(5) 별개 사위 학파 분기 (옵션 B 125괘).

ADR-112 한계 절 해소:
> 모를 별도 사위로 다루는 학파는 별도 ADR 가능 (옵션 B)

본 회귀는 학파 옵션 두 갈래 병행 검증:
  · school="folkmuseum" (디폴트): 국립민속박물관·이능화 정통 — 4사위 64괘
  · school="mo_separate" (옵션 B): 모(5) 별개 사위 — 5사위 125괘

기존 ADR-112 회귀 18건 무회귀 보장 (디폴트 변경 X).
/domain-priorities #13 (32점) 해소.
"""
from __future__ import annotations

import pytest

from engine.divination.yutjeom.scoring import (
    MO_SIDE,
    ONE_HUNDRED_TWENTY_FIVE_HEXAGRAMS,
    SIDES_5,
    SIXTY_FOUR_HEXAGRAMS,
    YUT_SIDES,
    compute_yut_hexagram,
    hexagram_by_id,
    yut_side_by_value_v5,
)


class TestMoSideMetadata:
    """모(5) 신규 사위 메타데이터."""

    def test_mo_side_defined(self):
        """MO_SIDE 사위 정의 — key='mo', value=5."""
        assert MO_SIDE.key == "mo"
        assert MO_SIDE.label_ko == "모"
        assert MO_SIDE.value == 5
        assert "비약" in MO_SIDE.meaning_ko

    def test_sides_5_has_5_elements(self):
        """SIDES_5 = 4사위(YUT_SIDES) + 모(MO_SIDE) = 5개."""
        assert len(SIDES_5) == 5
        assert SIDES_5[:4] == YUT_SIDES
        assert SIDES_5[4] == MO_SIDE

    def test_yut_side_by_value_v5_callable(self):
        """yut_side_by_value_v5(5) → MO_SIDE (모를 별개로 반환)."""
        r = yut_side_by_value_v5(5)
        assert r is not None
        assert r.key == "mo"

    def test_yut_side_by_value_v5_invalid(self):
        """잘못된 값 → None."""
        assert yut_side_by_value_v5(0) is None
        assert yut_side_by_value_v5(6) is None


class TestHundred25Generation:
    """125괘 자동 생성."""

    def test_total_count_125(self):
        """5사위 × 5사위 × 5사위 = 125괘."""
        assert len(ONE_HUNDRED_TWENTY_FIVE_HEXAGRAMS) == 125

    def test_all_hex_ids_unique(self):
        """hex_id 0~124 모두 고유."""
        hex_ids = [h.hex_id for h in ONE_HUNDRED_TWENTY_FIVE_HEXAGRAMS]
        assert len(set(hex_ids)) == 125
        assert min(hex_ids) == 0
        assert max(hex_ids) == 124

    def test_all_labels_present(self):
        """모든 괘에 label_ko (3사위 결합) 명시."""
        for h in ONE_HUNDRED_TWENTY_FIVE_HEXAGRAMS:
            assert len(h.label_ko) == 3
            for char in h.label_ko:
                assert char in ("도", "개", "걸", "윷", "모")

    def test_all_flow_tones_non_empty(self):
        """모든 괘에 흐름 톤 비어있지 않음."""
        for h in ONE_HUNDRED_TWENTY_FIVE_HEXAGRAMS:
            assert h.flow_tone_ko.strip(), f"hex_id {h.hex_id} 빈 톤"

    def test_first_hexagram_is_dododo(self):
        """hex_id 0 = 도도도 (64괘와 동일)."""
        h = ONE_HUNDRED_TWENTY_FIVE_HEXAGRAMS[0]
        assert h.label_ko == "도도도"
        assert h.upper == "do"

    def test_last_hexagram_is_momomo(self):
        """hex_id 124 = 모모모."""
        h = ONE_HUNDRED_TWENTY_FIVE_HEXAGRAMS[124]
        assert h.label_ko == "모모모"
        assert h.upper == "mo"

    def test_mo_combination_count_61(self):
        """모 포함 조합 = 125 - 64 = 61괘 (4사위 부분 제외)."""
        mo_count = sum(1 for h in ONE_HUNDRED_TWENTY_FIVE_HEXAGRAMS if "모" in h.label_ko)
        assert mo_count == 61, f"모 포함 괘: {mo_count} (목표: 61)"

    def test_non_mo_combinations_reuse_64_tones(self):
        """모가 없는 조합 64건은 SIXTY_FOUR_HEXAGRAMS와 톤 일치 (재사용)."""
        # 도도도 (idx 0) ~ 윷윷윷 (4사위 모두)
        for h_125 in ONE_HUNDRED_TWENTY_FIVE_HEXAGRAMS:
            if "모" not in h_125.label_ko:
                # 64괘에서 같은 label_ko 찾기
                matching = [h64 for h64 in SIXTY_FOUR_HEXAGRAMS if h64.label_ko == h_125.label_ko]
                assert len(matching) == 1, f"{h_125.label_ko} 매칭 안 됨"
                assert matching[0].flow_tone_ko == h_125.flow_tone_ko, (
                    f"{h_125.label_ko}: 톤 불일치 — 64괘 재사용 깨짐"
                )


class TestComputeOptionDefault:
    """디폴트 (folkmuseum) — ADR-112 호환성 보장."""

    def test_default_school_returns_64_hexagram(self):
        """디폴트 호출 = 64괘 매핑."""
        r = compute_yut_hexagram(1, 1, 1)
        assert r is not None
        assert r.hex_id == 0  # 0~63 범위
        assert r.label_ko == "도도도"

    def test_default_mo_input_unified_to_yut(self):
        """디폴트에서 모(5) 입력 → 윷(4)로 단일화 (ADR-112 정통 보존)."""
        r = compute_yut_hexagram(5, 5, 5)
        assert r is not None
        assert r.label_ko == "윷윷윷"
        assert r.hex_id == 63

    def test_explicit_folkmuseum_same_as_default(self):
        """school='folkmuseum' 명시 = 디폴트와 동일."""
        r1 = compute_yut_hexagram(2, 3, 4)
        r2 = compute_yut_hexagram(2, 3, 4, school="folkmuseum")
        assert r1 == r2


class TestComputeOptionMoSeparate:
    """옵션 B (mo_separate) — 125괘 모(5) 별개."""

    def test_mo_separate_returns_momomo_for_555(self):
        """옵션 B에서 (5,5,5) → 모모모 (hex_id 124)."""
        r = compute_yut_hexagram(5, 5, 5, school="mo_separate")
        assert r is not None
        assert r.label_ko == "모모모"
        assert r.hex_id == 124

    def test_mo_separate_dodomo(self):
        """옵션 B에서 (1,1,5) → 도도모 (hex_id 4)."""
        r = compute_yut_hexagram(1, 1, 5, school="mo_separate")
        assert r is not None
        assert r.label_ko == "도도모"
        assert r.hex_id == 4

    def test_mo_separate_modogo(self):
        """옵션 B에서 (5,1,1) → 모도도 (hex_id 100)."""
        r = compute_yut_hexagram(5, 1, 1, school="mo_separate")
        assert r is not None
        assert r.label_ko == "모도도"
        assert r.hex_id == 100

    def test_mo_separate_non_mo_combination_same_label(self):
        """옵션 B에서 모 없는 조합 (1,2,3) = 도개걸 — 64괘와 같은 라벨."""
        r = compute_yut_hexagram(1, 2, 3, school="mo_separate")
        r_default = compute_yut_hexagram(1, 2, 3)
        assert r is not None and r_default is not None
        assert r.label_ko == r_default.label_ko
        # 단 hex_id는 다를 수 있음 (125괘 인덱스 ≠ 64괘 인덱스)


class TestInvalidInputs:
    """경계 케이스."""

    def test_invalid_value_returns_none(self):
        """잘못된 사위 값 (0·6) → None."""
        assert compute_yut_hexagram(0, 1, 1, school="mo_separate") is None
        assert compute_yut_hexagram(6, 1, 1, school="mo_separate") is None
        assert compute_yut_hexagram(1, 1, 0) is None

    def test_invalid_school_returns_none(self):
        """잘못된 school 값 → None."""
        assert compute_yut_hexagram(1, 1, 1, school="invalid") is None
        assert compute_yut_hexagram(1, 1, 1, school="") is None


class TestHexagramByIdSchoolOption:
    """hexagram_by_id의 school 옵션."""

    def test_default_returns_64_only(self):
        """디폴트 = 0~63만 유효."""
        assert hexagram_by_id(0) is not None
        assert hexagram_by_id(63) is not None
        assert hexagram_by_id(64) is None
        assert hexagram_by_id(100) is None  # 125괘 범위 밖

    def test_mo_separate_returns_125(self):
        """옵션 B = 0~124 유효."""
        assert hexagram_by_id(0, school="mo_separate") is not None
        assert hexagram_by_id(64, school="mo_separate") is not None
        assert hexagram_by_id(124, school="mo_separate") is not None
        assert hexagram_by_id(125, school="mo_separate") is None

    def test_invalid_school(self):
        assert hexagram_by_id(0, school="invalid") is None


class TestSafetyAndDeterminism:
    """ADR-006 결정론 + 안전성."""

    def test_deterministic_default(self):
        """동일 입력 → 동일 결과 (5회)."""
        for _ in range(5):
            r = compute_yut_hexagram(3, 2, 1)
            assert r is not None
            assert r.label_ko == "걸개도"

    def test_deterministic_mo_separate(self):
        """옵션 B도 결정론."""
        for _ in range(5):
            r = compute_yut_hexagram(5, 3, 2, school="mo_separate")
            assert r is not None
            assert r.label_ko == "모걸개"

    def test_no_assertion_words_in_125_tones(self):
        """125괘 흐름 톤에 단정 어휘 0건 (ADR-006 정합)."""
        forbidden = ["반드시", "확실히", "절대", "100%", "대길", "대흉", "길몽", "흉몽"]
        for h in ONE_HUNDRED_TWENTY_FIVE_HEXAGRAMS:
            for w in forbidden:
                assert w not in h.flow_tone_ko, (
                    f"hex_id {h.hex_id} ({h.label_ko}): 단정 어휘 '{w}' 검출"
                )


class TestBackwardCompatibility:
    """ADR-112 기존 회귀 무회귀 (디폴트 동작 보존)."""

    @pytest.mark.parametrize("u,m,l,expected_label", [
        (1, 1, 1, "도도도"),
        (4, 4, 4, "윷윷윷"),
        (1, 2, 3, "도개걸"),
        (2, 3, 4, "개걸윷"),
    ])
    def test_64_hexagram_default_labels(self, u, m, l, expected_label):
        """기존 64괘 라벨 디폴트 보존."""
        r = compute_yut_hexagram(u, m, l)
        assert r is not None
        assert r.label_ko == expected_label
