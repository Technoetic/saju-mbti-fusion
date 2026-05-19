"""engine.safety.llm.persona_self_eval — §5.2.5 페르소나 자체 평가 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 빈 입력 ───────────────────────────

def test_empty_text_returns_zero_hits():
    from engine.safety.llm.persona_self_eval import evaluate_persona_tone
    for t in ("", None, "   "):
        r = evaluate_persona_tone(t)
        assert r.encouraged_hits == 0
        assert r.passed is False
        assert r.score == 0.0


# ─────────────────────────── 합격 사례 ───────────────────────────

def test_typical_saguk_passes():
    from engine.safety.llm.persona_self_eval import evaluate_persona_tone
    text = "허허, 그대의 상을 살피니, 이 늙은이가 짚는 결은 곧 자네의 결이로구먼."
    r = evaluate_persona_tone(text)
    assert r.encouraged_hits >= 3
    assert r.forbidden_hits == 0
    assert r.medical_legal_hits == 0
    assert r.passed is True


def test_score_perfect_when_many_hits_and_no_violations():
    from engine.safety.llm.persona_self_eval import evaluate_persona_tone
    text = "허허, 그대여, 자네의 상을 보시게나. 이 늙은이의 결이로세. 그대로 흐르시게나."
    r = evaluate_persona_tone(text)
    assert r.score >= 0.9


# ─────────────────────────── 금지 어휘 ───────────────────────────

def test_forbidden_word_blocks_pass():
    from engine.safety.llm.persona_self_eval import evaluate_persona_tone
    text = "허허, 그대, 자네의 상에 대박 운이 따르겠구먼."
    r = evaluate_persona_tone(text)
    assert r.encouraged_hits >= 3
    assert "대박" in r.matched_forbidden
    assert r.passed is False


def test_metalinguistic_ai_word_blocks_pass():
    from engine.safety.llm.persona_self_eval import evaluate_persona_tone
    text = "허허, 그대, 자네의 상에 대해 AI 모델이 분석한 결과이로구먼."
    r = evaluate_persona_tone(text)
    assert any(w in r.matched_forbidden for w in ("AI", "모델"))
    assert r.passed is False


def test_korean_addressing_words_block():
    from engine.safety.llm.persona_self_eval import evaluate_persona_tone
    text = "허허, 회원님께서 보내신 사진을 그대로 살펴보았네."
    r = evaluate_persona_tone(text)
    assert "회원님" in r.matched_forbidden
    assert r.passed is False


# ─────────────────────────── 의료·법률 단정 ───────────────────────────

def test_medical_assertion_blocks_pass():
    from engine.safety.llm.persona_self_eval import evaluate_persona_tone
    text = "허허, 그대, 자네, 짚는 결에 단명할 상이 보이는구먼."
    r = evaluate_persona_tone(text)
    assert "단명" in r.matched_medical_legal
    assert r.passed is False


def test_financial_assertion_blocks_pass():
    from engine.safety.llm.persona_self_eval import evaluate_persona_tone
    text = "허허, 그대, 자네, 비트코인을 사두시게."
    r = evaluate_persona_tone(text)
    assert "비트코인" in r.matched_medical_legal
    assert r.passed is False


def test_legal_assertion_blocks_pass():
    from engine.safety.llm.persona_self_eval import evaluate_persona_tone
    text = "허허, 그대, 자네는 이혼한다는 결이로구먼."
    r = evaluate_persona_tone(text)
    assert "이혼한다" in r.matched_medical_legal
    assert r.passed is False


# ─────────────────────────── 점수 가중 ───────────────────────────

def test_score_penalty_for_forbidden():
    from engine.safety.llm.persona_self_eval import evaluate_persona_tone
    base = "허허, 그대, 자네, 이 늙은이의 결이로세."
    bad = base + " 대박 운이로구먼."
    r_base = evaluate_persona_tone(base)
    r_bad = evaluate_persona_tone(bad)
    assert r_bad.score < r_base.score


def test_score_zero_floor():
    """음수 점수는 0.0으로 클램프."""
    from engine.safety.llm.persona_self_eval import evaluate_persona_tone
    text = "회원님 대박 단명 비트코인 AI 모델"
    r = evaluate_persona_tone(text)
    assert r.score == 0.0


# ─────────────────────────── 합격 임계 ───────────────────────────

def test_two_hits_does_not_pass():
    """encouraged_hits=2면 불합격 (3 이상 필요)."""
    from engine.safety.llm.persona_self_eval import evaluate_persona_tone
    text = "허허 그대"  # 권장 어휘 2개만
    r = evaluate_persona_tone(text)
    assert r.encouraged_hits == 2
    assert r.passed is False


# ─────────────────────────── 직렬화 + 집계 ───────────────────────────

def test_to_response_dict_keys():
    from engine.safety.llm.persona_self_eval import (
        evaluate_persona_tone, to_response_dict,
    )
    r = evaluate_persona_tone("허허, 그대, 자네, 이 늙은이의 결이로세.")
    d = to_response_dict(r)
    for k in ("passed", "score", "encouraged_hits",
              "forbidden_hits", "medical_legal_hits"):
        assert k in d


def test_aggregate_pass_rate():
    from engine.safety.llm.persona_self_eval import (
        evaluate_persona_tone, aggregate_pass_rate,
    )
    results = [
        evaluate_persona_tone("허허, 그대, 자네, 이 늙은이의 결이로세."),  # 합격
        evaluate_persona_tone("허허, 그대, 자네, 대박이로구먼."),         # 불합격 (대박)
        evaluate_persona_tone("허허, 그대, 자네, 이 늙은이의 결이로세."),  # 합격
    ]
    assert aggregate_pass_rate(results) == round(2 / 3, 4)


def test_aggregate_pass_rate_empty():
    from engine.safety.llm.persona_self_eval import aggregate_pass_rate
    assert aggregate_pass_rate([]) == 0.0


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_persona_self_eval():
    import engine.safety as safety
    assert hasattr(safety, "evaluate_persona_tone")
    assert hasattr(safety, "PersonaEvalResult")
    assert hasattr(safety, "aggregate_pass_rate")
    assert hasattr(safety, "PERSONA_ENCOURAGED")
    assert hasattr(safety, "PERSONA_FORBIDDEN")
    assert hasattr(safety, "MEDICAL_LEGAL_FORBIDDEN")
