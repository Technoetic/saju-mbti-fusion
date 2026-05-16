"""engine.safety.response_alignment — §7.2.20 응답 정렬 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 주제 감지 ───────────────────────────

def test_detect_topic_marriage():
    from engine.safety.response_alignment import detect_topic
    topic, hits = detect_topic("올해 결혼운이 어떤가요?")
    assert topic == "marriage"
    assert "결혼" in hits


def test_detect_topic_wealth():
    from engine.safety.response_alignment import detect_topic
    topic, _ = detect_topic("재물 운이 따를까요?")
    assert topic == "wealth"


def test_detect_topic_health():
    from engine.safety.response_alignment import detect_topic
    topic, _ = detect_topic("건강은 괜찮을까요?")
    assert topic == "health"


def test_detect_topic_career():
    from engine.safety.response_alignment import detect_topic
    topic, _ = detect_topic("승진할 수 있을까요?")
    assert topic == "career"


def test_detect_topic_none_for_short_question():
    from engine.safety.response_alignment import detect_topic
    topic, hits = detect_topic("어떤가요?")
    assert topic == ""
    assert hits == []


def test_detect_topic_none_for_empty():
    from engine.safety.response_alignment import detect_topic
    assert detect_topic("") == ("", [])
    assert detect_topic(None) == ("", [])


def test_detect_topic_picks_most_hits():
    """여러 주제 단어가 섞이면 더 많이 매칭되는 쪽."""
    from engine.safety.response_alignment import detect_topic
    topic, _ = detect_topic("건강과 결혼운 모두, 결혼이 가장 궁금해요")
    # 결혼/결혼/연애... 등 marriage 마커가 더 많이 매칭됨
    assert topic == "marriage"


# ─────────────────────────── 응답 주제 검사 ───────────────────────────

def test_check_response_topic_marriage_hit():
    from engine.safety.response_alignment import check_response_topic
    hits = check_response_topic(
        "허허, 그대의 처첩궁이 환하니 배우자 인연이 따르겠구먼.",
        "marriage",
    )
    assert "처첩궁" in hits or "배우자" in hits


def test_check_response_topic_wealth_miss():
    from engine.safety.response_alignment import check_response_topic
    hits = check_response_topic(
        "허허, 그대의 처첩궁이 환하니 배우자 인연이 따르겠구먼.",
        "wealth",
    )
    assert hits == []


def test_check_response_topic_empty_text():
    from engine.safety.response_alignment import check_response_topic
    assert check_response_topic("", "marriage") == []
    assert check_response_topic(None, "marriage") == []


# ─────────────────────────── 통합 평가 ───────────────────────────

def test_aligned_marriage_question_response():
    from engine.safety.response_alignment import evaluate_alignment
    r = evaluate_alignment(
        question="결혼운이 어떤가요?",
        response_text="허허, 처첩궁이 환하니 배우자와의 인연이 좋겠구먼.",
    )
    assert r.aligned is True
    assert r.topic_detected == "marriage"


def test_misaligned_topic_missing():
    """결혼 화두인데 응답은 건강만 다룸."""
    from engine.safety.response_alignment import (
        evaluate_alignment, ALIGN_TOPIC_MISSING,
    )
    r = evaluate_alignment(
        question="결혼운이 어떤가요?",
        response_text="허허, 그대의 산근이 곧으니 건강과 수명이 길겠구먼.",
    )
    assert r.aligned is False
    assert ALIGN_TOPIC_MISSING in r.issues
    assert r.topic_detected == "marriage"


def test_no_topic_detected_skips_check():
    """화두에서 주제 감지 불가 → 검증 면제."""
    from engine.safety.response_alignment import evaluate_alignment
    r = evaluate_alignment(
        question="안녕하세요",
        response_text="허허, 그대의 상이로구먼.",
    )
    assert r.aligned is True
    assert r.topic_detected == ""


def test_empty_response_question_ignored():
    from engine.safety.response_alignment import (
        evaluate_alignment, ALIGN_QUESTION_IGNORED,
    )
    r = evaluate_alignment(question="결혼운?", response_text="")
    assert ALIGN_QUESTION_IGNORED in r.issues


def test_none_response_question_ignored():
    from engine.safety.response_alignment import (
        evaluate_alignment, ALIGN_QUESTION_IGNORED,
    )
    r = evaluate_alignment(question="결혼운?", response_text=None)
    assert ALIGN_QUESTION_IGNORED in r.issues


# ─────────────────────────── 다양한 주제 ───────────────────────────

def test_wealth_question_with_wealth_response_aligned():
    from engine.safety.response_alignment import evaluate_alignment
    r = evaluate_alignment(
        question="재물운이 좋을까요?",
        response_text="허허, 콧방울이 두툼하니 재백궁이 후하겠구먼.",
    )
    assert r.aligned is True


def test_career_question_with_career_response_aligned():
    from engine.safety.response_alignment import evaluate_alignment
    r = evaluate_alignment(
        question="직업 운은 어떤가요?",
        response_text="허허, 이마가 평평하니 관록궁이 든든하겠구먼.",
    )
    assert r.aligned is True


def test_children_question_misaligned():
    from engine.safety.response_alignment import evaluate_alignment
    r = evaluate_alignment(
        question="자녀운은 어떤가요?",
        response_text="허허, 재물의 결만 짚어보았구먼.",
    )
    assert r.aligned is False


def test_family_question_aligned():
    from engine.safety.response_alignment import evaluate_alignment
    r = evaluate_alignment(
        question="부모님 인연은요?",
        response_text="허허, 일각 월각이 환하니 부모궁이 두터우시구먼.",
    )
    assert r.aligned is True


# ─────────────────────────── 폴백 트리거 ───────────────────────────

def test_fallback_trigger_misaligned_maps_to_persona_failed():
    from engine.safety.response_alignment import (
        evaluate_alignment, to_fallback_trigger,
    )
    r = evaluate_alignment(
        question="결혼운?",
        response_text="허허, 건강만 짚어드렸네.",
    )
    assert to_fallback_trigger(r) == "persona_failed"


def test_fallback_trigger_aligned_returns_empty():
    from engine.safety.response_alignment import (
        evaluate_alignment, to_fallback_trigger,
    )
    r = evaluate_alignment(
        question="결혼운?",
        response_text="허허, 배우자의 결을 짚으니 처첩궁이 환하구먼.",
    )
    assert to_fallback_trigger(r) == ""


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_response_alignment():
    import engine.safety as safety
    assert hasattr(safety, "evaluate_alignment")
    assert hasattr(safety, "detect_topic")
    assert hasattr(safety, "check_response_topic")
    assert hasattr(safety, "AlignmentResult")
    assert hasattr(safety, "ALIGN_TOPIC_MISSING")
