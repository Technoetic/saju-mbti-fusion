"""ADR-277 — 관상 5형 전통 기질 매핑 회귀.

"정통 관상"이 형태 묘사에 그치지 않고 5형(목·화·토·금·수) 본바탕 캐릭터를
풀도록, 기질 매핑이 (a) 5형 모두 존재 (b) 단정 어조 금지 (c) 양면 제시
(d) reading.py 두 경로에 주입되는지 검증.
"""
import pytest

from engine.divination.face.knowledge import (
    FIVE_SHAPE_TRAITS,
    get_five_shape_trait,
    format_five_shape_trait_for_prompt,
)


SHAPES = ["목형", "화형", "토형", "금형", "수형"]
OHAENG = {"목형": "木", "화형": "火", "토형": "土", "금형": "金", "수형": "水"}
OHSANG = {"목형": "仁", "화형": "禮", "토형": "信", "금형": "義", "수형": "智"}


def test_all_five_shapes_present():
    assert len(FIVE_SHAPE_TRAITS) == 5
    types = {t.shape_type for t in FIVE_SHAPE_TRAITS}
    assert types == set(SHAPES)


@pytest.mark.parametrize("shape", SHAPES)
def test_ohaeng_ohsang_mapping(shape):
    t = get_five_shape_trait(shape)
    assert t is not None
    assert t.ohaeng == OHAENG[shape]
    assert t.ohsang == OHSANG[shape]


@pytest.mark.parametrize("shape", SHAPES)
def test_tendency_is_gradient_not_assertion(shape):
    """단정 어조 금지 (ADR-006) — '~로 봅니다/풀이합니다' 경향 어조."""
    t = get_five_shape_trait(shape)
    assert t is not None
    assert ("봅니다" in t.tendency) or ("풀이합니다" in t.tendency)
    # 단정·예언 어휘 금지
    for banned in ["사람이다", "할 것이다", "운이 있다", "틀림없", "반드시"]:
        assert banned not in t.tendency, f"{shape}: 단정어 '{banned}'"


@pytest.mark.parametrize("shape", SHAPES)
def test_strength_and_caution_both_present(shape):
    """양면 제시 (ADR-094) — 강점 결 + 주의 결 모두."""
    t = get_five_shape_trait(shape)
    assert t is not None
    assert t.strength.strip()
    assert t.caution.strip()


def test_composite_returns_none():
    """복합형·미상은 기질 매핑 없음 (형용사 인상 방식으로 폴백)."""
    assert get_five_shape_trait("복합형") is None
    assert get_five_shape_trait("") is None
    assert get_five_shape_trait("미상") is None


@pytest.mark.parametrize("shape", SHAPES)
def test_prompt_block_format(shape):
    block = format_five_shape_trait_for_prompt(shape)
    assert block is not None
    assert "ADR-277" in block
    assert shape in block
    assert "출처:" in block
    # 단정 금지 가드 명시
    assert "단정 X" in block or "단정" in block


def test_prompt_block_none_for_composite():
    assert format_five_shape_trait_for_prompt("복합형") is None


def test_injected_into_stage2_summary():
    """Stage 2 결정론 요약 dict의 face_shape에 ohaeng_trait 주입."""
    from engine.divination.face.reading import _build_deterministic_scores_summary

    out = _build_deterministic_scores_summary(
        palace_scores=None,
        face_shape={"shape_type": "토형", "morphological_name": "수평발달형"},
    )
    trait = out.get("face_shape", {}).get("ohaeng_trait")
    assert trait is not None
    assert trait["ohaeng"] == "土"
    assert trait["ohsang"] == "信"
    assert "봅니다" in trait["tendency"] or "풀이합니다" in trait["tendency"]


def test_composite_not_injected_into_stage2():
    from engine.divination.face.reading import _build_deterministic_scores_summary

    out = _build_deterministic_scores_summary(
        palace_scores=None,
        face_shape={"shape_type": "복합형", "morphological_name": "평균"},
    )
    assert "ohaeng_trait" not in out.get("face_shape", {})
