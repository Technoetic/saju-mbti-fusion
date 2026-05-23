"""ADR-210/211/212/213 4 차원 추가 개선 회귀."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ───── ADR-210 quality index 5 factor ─────

def test_adr210_quality_index_all_high():
    from engine.safety.photo.quality_index import compute_quality_index
    r = compute_quality_index(sharpness=0.9, brightness=0.8, contrast=0.85,
                              illumination=0.9, focus=0.85)
    assert r.quality_index > 0.7
    assert r.verdict == "good"


def test_adr210_quality_index_all_low():
    from engine.safety.photo.quality_index import compute_quality_index
    r = compute_quality_index(sharpness=0.2, brightness=0.3, contrast=0.2,
                              illumination=0.3, focus=0.2)
    assert r.verdict == "bad"
    assert "다시 촬영" in r.user_message


def test_adr210_quality_index_warn():
    from engine.safety.photo.quality_index import compute_quality_index
    r = compute_quality_index(sharpness=0.5, brightness=0.5, contrast=0.5,
                              illumination=0.5, focus=0.5)
    assert r.verdict == "warn"


def test_adr210_none_inputs_neutral():
    from engine.safety.photo.quality_index import compute_quality_index
    r = compute_quality_index()
    assert r.quality_index == 0.5
    assert r.verdict == "warn"


def test_adr210_source_url_hindawi():
    from engine.safety.photo.quality_index import compute_quality_index, SOURCE_URL
    r = compute_quality_index(sharpness=0.8)
    assert r.source_url == SOURCE_URL
    assert "hindawi" in SOURCE_URL.lower()


# ───── ADR-211 sebum/shine ─────

def test_adr211_compute_shine_pct():
    from engine.divination.face.sebum_shine import compute_shine_pct
    # 5 픽셀 중 2개가 밝음 → 40%
    px = [(230, 230, 230), (250, 250, 250), (100, 80, 70), (90, 80, 60), (100, 90, 80)]
    pct = compute_shine_pct(px)
    assert pct == 0.4


def test_adr211_analyze_matte():
    from engine.divination.face.sebum_shine import analyze_sebum_shine
    r = analyze_sebum_shine(0.005)
    assert r.shine_level == "matte"
    assert "매끈" in r.label_ko


def test_adr211_analyze_moderate():
    from engine.divination.face.sebum_shine import analyze_sebum_shine
    r = analyze_sebum_shine(0.05)
    assert r.shine_level == "moderate"


def test_adr211_analyze_shiny():
    from engine.divination.face.sebum_shine import analyze_sebum_shine
    r = analyze_sebum_shine(0.30)
    assert r.shine_level == "shiny"
    assert "윤기" in r.label_ko


def test_adr211_disclaimer_medical():
    from engine.divination.face.sebum_shine import analyze_sebum_shine
    r = analyze_sebum_shine(0.1)
    assert "의료 진단" in r.disclaimer


def test_adr211_empty_pixels():
    from engine.divination.face.sebum_shine import compute_shine_pct
    assert compute_shine_pct([]) == 0.0


# ───── ADR-212 표정 5번째 카테고리 ─────

def test_adr212_nose_chin_detected():
    from engine.safety.photo.expression_noise import (
        detect_expression_noise, EXPR_NOISE_NOSE_CHIN,
    )
    bs = {"noseSneerLeft": 0.5}
    r = detect_expression_noise(bs)
    assert r.blocked is True
    assert r.category == EXPR_NOISE_NOSE_CHIN


def test_adr212_mouth_press_expanded():
    """입 카테고리 보강 — mouthPressLeft도 검출."""
    from engine.safety.photo.expression_noise import (
        detect_expression_noise, EXPR_NOISE_MOUTH,
    )
    bs = {"mouthPressLeft": 0.5}
    r = detect_expression_noise(bs)
    assert r.blocked is True
    assert r.category == EXPR_NOISE_MOUTH


def test_adr212_eye_look_in_expanded():
    """눈 카테고리 보강 — eyeLookInLeft도 검출."""
    from engine.safety.photo.expression_noise import (
        detect_expression_noise, EXPR_NOISE_EYE,
    )
    bs = {"eyeLookInLeft": 0.5}
    r = detect_expression_noise(bs)
    assert r.blocked is True


def test_adr212_detail_has_nose_chin():
    from engine.safety.photo.expression_noise import detect_expression_noise
    r = detect_expression_noise({"noseSneerLeft": 0.05})
    assert "nose_chin_max" in r.detail


# ───── ADR-213 persona_vocab Stage 2 주입 ─────

def test_adr213_persona_vocab_renders():
    from engine.divination.face.persona_vocab import render_for_system_prompt
    text = render_for_system_prompt()
    assert "운학 도사" in text
    assert "자기지칭" in text


def test_adr213_render_passes_fate_assertion():
    """LLM 시스템 프롬프트에 주입되는 어휘 가이드가 fate_assertion 통과."""
    from engine.divination.face.persona_vocab import render_for_system_prompt
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    text = render_for_system_prompt()
    r = detect_fate_assertions(text, domain="face")
    assert r.detected is False
