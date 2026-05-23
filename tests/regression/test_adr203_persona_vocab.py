"""ADR-203 - 운학 도사 사극 어휘 사전 회귀."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_total_vocab_over_50():
    """총 어휘 수 50건 이상 (ADR-203 목표)."""
    from engine.divination.face.persona_vocab import total_vocab_count
    assert total_vocab_count() > 50


def test_self_references_includes_unhak_dosa():
    from engine.divination.face.persona_vocab import SELF_REFERENCES
    assert "이 운학 도사가" in SELF_REFERENCES
    assert "이 늙은이" in SELF_REFERENCES


def test_palace_labels_12_complete():
    from engine.divination.face.persona_vocab import PALACE_LABELS_KO
    assert len(PALACE_LABELS_KO) == 12
    assert "재백궁(財帛宮)" in PALACE_LABELS_KO.values()


def test_shape_descriptors_have_hue():
    from engine.divination.face.persona_vocab import SHAPE_DESCRIPTORS
    assert "환하다" in SHAPE_DESCRIPTORS
    assert "고르다" in SHAPE_DESCRIPTORS


def test_transitions_include_no_prediction_phrase():
    """'예언이 아닌' 같은 단정 회피 어귀 포함."""
    from engine.divination.face.persona_vocab import SAJUK_TRANSITIONS
    assert any("예언이 아닌" in t for t in SAJUK_TRANSITIONS)
    assert any("단정할 일은 아니" in t for t in SAJUK_TRANSITIONS)


def test_vocab_passes_fate_assertion_filter():
    """모든 카테고리 어휘가 ADR-171 fate_assertion 사전 통과 (운명 단정 X)."""
    from engine.divination.face.persona_vocab import ALL_CATEGORIES
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    for cat_name, vocab in ALL_CATEGORIES.items():
        for word in vocab:
            r = detect_fate_assertions(word, domain="face")
            assert r.detected is False, f"{cat_name}.{word!r} triggers fate_assertion"


def test_render_for_system_prompt_includes_categories():
    from engine.divination.face.persona_vocab import render_for_system_prompt
    text = render_for_system_prompt()
    assert "운학 도사" in text
    assert "자기지칭" in text
    assert "호명" in text
    assert "ADR-203" in text


def test_get_category_unknown_returns_empty():
    from engine.divination.face.persona_vocab import get_category
    assert get_category("nonexistent") == ()


def test_get_category_known_returns_tuple():
    from engine.divination.face.persona_vocab import get_category, SELF_REFERENCES
    assert get_category("self_references") == SELF_REFERENCES
