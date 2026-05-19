"""engine.safety.llm.response_consistency — §5.2.9 응답 일관성 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# 페르소나 통과 응답 샘플
GOOD_1 = ("허허, 그대의 처첩궁이 환하니, 이 늙은이가 짚는 결은 자네에게 인연이 따르는 결이로구먼. "
          "삼정이 고르고 명궁이 환하니 마음의 결이 맑도다.")
GOOD_2 = ("허허, 그대의 어미가 매끈하니, 이 늙은이 짚으니 자네에게 부부 화목이 따르는 결이로세. "
          "처첩궁이 환하고 명궁이 맑으니 마음이 평안하구먼.")
GOOD_3 = ("허허, 그대 처첩궁이 환한 결이로구먼. 이 늙은이가 자네의 상을 짚으니 "
          "삼정 고르고 명궁 맑아 마음이 환하도다.")


# ─────────────────────────── 표본 부족 ───────────────────────────

def test_empty_returns_unevaluated():
    from engine.safety.llm.response_consistency import evaluate_consistency
    r = evaluate_consistency([])
    assert r.sample_count == 0
    assert r.issues == []


def test_single_response_skipped():
    from engine.safety.llm.response_consistency import evaluate_consistency
    r = evaluate_consistency([GOOD_1])
    # MIN_SAMPLES_FOR_EVAL=2 미만이면 검증 면제
    assert r.sample_count == 1
    assert r.issues == []


# ─────────────────────────── 일관성 ───────────────────────────

def test_consistent_responses_pass():
    from engine.safety.llm.response_consistency import evaluate_consistency
    r = evaluate_consistency([GOOD_1, GOOD_2, GOOD_3])
    assert r.consistent is True
    assert r.persona_pass_rate >= 0.8
    assert r.forbidden_total == 0
    assert r.medical_legal_total == 0


def test_consistent_with_question_aligned():
    from engine.safety.llm.response_consistency import evaluate_consistency
    r = evaluate_consistency(
        [GOOD_1, GOOD_2, GOOD_3],
        question="결혼운이 어떤가요?",
    )
    assert r.consistent is True
    assert r.dominant_topic == "marriage"
    assert r.topic_agreement >= 0.8


# ─────────────────────────── persona drop ───────────────────────────

def test_persona_drop_detected():
    """절반이 페르소나 깨지면 위반."""
    from engine.safety.llm.response_consistency import (
        evaluate_consistency, CONSISTENCY_PERSONA_DROP,
    )
    bad = ("안녕하세요 회원님, 분석 결과를 알려드립니다. 행운이 따르시기를 바랍니다. "
           "오늘은 좋은 하루가 될 것입니다.")
    r = evaluate_consistency([GOOD_1, bad, bad])  # 1/3 pass
    assert CONSISTENCY_PERSONA_DROP in r.issues


def test_partial_persona_drop_below_80pct_caught():
    from engine.safety.llm.response_consistency import (
        evaluate_consistency, CONSISTENCY_PERSONA_DROP,
    )
    bad = "안녕하세요 분석 결과 알려드립니다. 오늘은 좋은 하루가 될 것입니다."
    # 4 중 1만 통과 → 25%
    r = evaluate_consistency([GOOD_1, bad, bad, bad])
    assert CONSISTENCY_PERSONA_DROP in r.issues


# ─────────────────────────── 의료·법률 누출 ───────────────────────────

def test_medical_leak_in_one_response_caught():
    """단 하나만 의료 단정이 있어도 일관성 깨짐."""
    from engine.safety.llm.response_consistency import (
        evaluate_consistency, CONSISTENCY_MEDICAL_LEAK,
    )
    med = GOOD_1 + " 단명할 결이로다."
    r = evaluate_consistency([GOOD_1, GOOD_2, med])
    assert CONSISTENCY_MEDICAL_LEAK in r.issues
    assert r.medical_legal_total >= 1


def test_clean_responses_no_medical_issue():
    from engine.safety.llm.response_consistency import (
        evaluate_consistency, CONSISTENCY_MEDICAL_LEAK,
    )
    r = evaluate_consistency([GOOD_1, GOOD_2])
    assert CONSISTENCY_MEDICAL_LEAK not in r.issues


# ─────────────────────────── 금지어 ───────────────────────────

def test_forbidden_word_in_one_response_caught():
    from engine.safety.llm.response_consistency import (
        evaluate_consistency, CONSISTENCY_FORBIDDEN_INCONSISTENT,
    )
    bad = GOOD_1 + " 대박 운이로구먼."
    r = evaluate_consistency([GOOD_1, GOOD_2, bad])
    assert CONSISTENCY_FORBIDDEN_INCONSISTENT in r.issues
    assert r.forbidden_total >= 1


# ─────────────────────────── 주제 일관성 ───────────────────────────

def test_topic_drift_caught():
    """일부 응답이 다른 주제를 다룸."""
    from engine.safety.llm.response_consistency import (
        evaluate_consistency, CONSISTENCY_TOPIC_DRIFT,
    )
    # 결혼 화두인데 응답 일부가 건강만 다룸
    health_only = ("허허, 그대 산근이 곧고 기색이 맑으니 건강과 수명이 길겠구먼. "
                   "이 늙은이가 짚는 결이 자네에게 건강이로다.")
    r = evaluate_consistency(
        [GOOD_1, health_only, health_only, health_only],
        question="결혼운?",
    )
    assert CONSISTENCY_TOPIC_DRIFT in r.issues
    assert r.topic_agreement < 0.8


def test_topic_agreement_skipped_without_question():
    """화두 없으면 topic_agreement 검증 면제."""
    from engine.safety.llm.response_consistency import (
        evaluate_consistency, CONSISTENCY_TOPIC_DRIFT,
    )
    r = evaluate_consistency([GOOD_1, GOOD_2])
    assert CONSISTENCY_TOPIC_DRIFT not in r.issues
    assert r.dominant_topic == ""


# ─────────────────────────── 길이 변동 ───────────────────────────

def test_high_length_variance_caught():
    """응답 길이가 매우 들쭉날쭉이면 위반."""
    from engine.safety.llm.response_consistency import (
        evaluate_consistency, CONSISTENCY_LENGTH_VARIANCE_HIGH,
    )
    short = "허허, 그대, 자네의 결이로세."
    very_long = GOOD_1 * 8  # 8배
    r = evaluate_consistency([GOOD_1, short, very_long])
    assert CONSISTENCY_LENGTH_VARIANCE_HIGH in r.issues
    assert r.length_cv > 0.5


def test_similar_length_no_variance_issue():
    from engine.safety.llm.response_consistency import (
        evaluate_consistency, CONSISTENCY_LENGTH_VARIANCE_HIGH,
    )
    r = evaluate_consistency([GOOD_1, GOOD_2, GOOD_3])
    assert CONSISTENCY_LENGTH_VARIANCE_HIGH not in r.issues


# ─────────────────────────── 다중 위반 ───────────────────────────

def test_multiple_issues_aggregated():
    """페르소나 + 금지어 + 길이 변동 동시."""
    from engine.safety.llm.response_consistency import evaluate_consistency
    bad_persona = "안녕하세요. 분석 결과입니다."
    bad_forbidden = GOOD_1 + " 대박 운이로구먼."
    r = evaluate_consistency([GOOD_1, bad_persona, bad_forbidden])
    assert len(r.issues) >= 2


# ─────────────────────────── 알람 ───────────────────────────

def test_alert_clean_is_p3():
    from engine.safety.llm.response_consistency import (
        evaluate_consistency, to_alert_payload,
    )
    r = evaluate_consistency([GOOD_1, GOOD_2])
    p = to_alert_payload(r)
    assert p["severity"] == "P3"


def test_alert_medical_leak_is_p1():
    from engine.safety.llm.response_consistency import (
        evaluate_consistency, to_alert_payload,
    )
    med = GOOD_1 + " 단명할 결이로다."
    r = evaluate_consistency([GOOD_1, med])
    p = to_alert_payload(r)
    assert p["severity"] == "P1"


def test_alert_single_issue_is_p2():
    from engine.safety.llm.response_consistency import (
        evaluate_consistency, to_alert_payload,
    )
    bad = GOOD_1 + " 대박 운이로구먼."
    r = evaluate_consistency([GOOD_1, bad])
    p = to_alert_payload(r)
    assert p["severity"] == "P2"


# ─────────────────────────── 폴백 ───────────────────────────

def test_fallback_trigger_issues_maps_persona_failed():
    from engine.safety.llm.response_consistency import (
        evaluate_consistency, to_fallback_trigger,
    )
    bad = GOOD_1 + " 대박."
    r = evaluate_consistency([GOOD_1, bad])
    assert to_fallback_trigger(r) == "persona_failed"


def test_fallback_trigger_clean_returns_empty():
    from engine.safety.llm.response_consistency import (
        evaluate_consistency, to_fallback_trigger,
    )
    r = evaluate_consistency([GOOD_1, GOOD_2])
    assert to_fallback_trigger(r) == ""


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_response_consistency():
    import engine.safety as safety
    assert hasattr(safety, "evaluate_consistency")
    assert hasattr(safety, "ConsistencyReport")
    assert hasattr(safety, "CONSISTENCY_PERSONA_DROP")
    assert hasattr(safety, "CONSISTENCY_MEDICAL_LEAK")
    assert hasattr(safety, "CONSISTENCY_TOPIC_DRIFT")
    assert hasattr(safety, "LENGTH_CV_MAX")
    assert hasattr(safety, "TOPIC_AGREEMENT_MIN")
