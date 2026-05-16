"""engine.safety.output_token_guard — §5.2.6 출력 가드 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# 합격 가능한 사극풍 본문 (≥80자, 사극 어미로 끝남, 한글 90%+)
GOOD = ("허허, 그대의 상을 살피니, 이 늙은이가 짚는 결은 자네의 결이로구먼. "
        "삼정이 고르고 명궁이 환하니, 마음의 결이 맑도다. 코끝이 환하니 중년에 "
        "기개가 굳세고, 입꼬리가 단정하니 말년이 평안할 결이로세. 그대로 가시게.")


# ─────────────────────────── 정상 ───────────────────────────

def test_clean_response_no_issues():
    from engine.safety.output_token_guard import evaluate_output
    r = evaluate_output(GOOD, lang="ko")
    assert r.ok is True
    assert r.issues == []
    assert r.char_count >= 80
    assert r.ends_with_terminal is True


def test_empty_text_too_short():
    from engine.safety.output_token_guard import evaluate_output, ISSUE_TOO_SHORT
    r = evaluate_output("", lang="ko")
    assert ISSUE_TOO_SHORT in r.issues


def test_none_text_too_short():
    from engine.safety.output_token_guard import evaluate_output, ISSUE_TOO_SHORT
    r = evaluate_output(None, lang="ko")
    assert ISSUE_TOO_SHORT in r.issues


# ─────────────────────────── 너무 짧음 ───────────────────────────

def test_short_response_flagged():
    from engine.safety.output_token_guard import evaluate_output, ISSUE_TOO_SHORT
    r = evaluate_output("허허.", lang="ko")
    assert ISSUE_TOO_SHORT in r.issues


# ─────────────────────────── 너무 김 ───────────────────────────

def test_long_response_flagged():
    from engine.safety.output_token_guard import evaluate_output, ISSUE_TOO_LONG
    huge = ("허허 그대 자네 늙은이 결이로세 " * 200) + "구먼."  # 6000+자
    r = evaluate_output(huge, lang="ko")
    assert ISSUE_TOO_LONG in r.issues


# ─────────────────────────── 절단 ───────────────────────────

def test_truncated_no_terminal_marker():
    """본문이 종결 어미 없이 끝나면 truncated (80자 이상)."""
    from engine.safety.output_token_guard import evaluate_output, ISSUE_TRUNCATED
    truncated = ("허허, 그대의 상을 살피니, 이 늙은이가 짚는 결은 자네의 결이로구먼. "
                 "삼정이 고르고 명궁이 환하니, 마음의 결이 맑도. 코끝이 환하고 "
                 "이마가 넓으니 초년에 학문이 깊을 결이고 중년에는 자리가 든든할 듯")
    r = evaluate_output(truncated, lang="ko")
    assert ISSUE_TRUNCATED in r.issues


def test_terminated_with_marker_not_truncated():
    from engine.safety.output_token_guard import evaluate_output, ISSUE_TRUNCATED
    r = evaluate_output(GOOD, lang="ko")
    assert ISSUE_TRUNCATED not in r.issues


def test_short_truncated_no_double_flag():
    """너무 짧으면 truncated를 별도로 flag하지 않음 (too_short만)."""
    from engine.safety.output_token_guard import evaluate_output, ISSUE_TRUNCATED
    short = "허허"
    r = evaluate_output(short, lang="ko")
    assert ISSUE_TRUNCATED not in r.issues


# ─────────────────────────── 언어 drift ───────────────────────────

def test_language_drift_when_ko_ratio_low():
    """lang=ko인데 영어 위주면 drift."""
    from engine.safety.output_token_guard import (
        evaluate_output, ISSUE_LANGUAGE_DRIFT,
    )
    drift = ("Greetings dear friend, this elder physiognomist sees great "
             "fortune ahead in your face. The structure speaks clearly indeed. "
             "이로구먼.")
    r = evaluate_output(drift, lang="ko")
    assert ISSUE_LANGUAGE_DRIFT in r.issues


def test_language_drift_skipped_for_en():
    """lang=en일 때는 한글 비율 검사 안 함."""
    from engine.safety.output_token_guard import (
        evaluate_output, ISSUE_LANGUAGE_DRIFT,
    )
    en_text = ("Greetings dear friend, this elder physiognomist sees great "
               "fortune ahead in your face. The structure speaks clearly indeed yours.")
    r = evaluate_output(en_text, lang="en")
    assert ISSUE_LANGUAGE_DRIFT not in r.issues


def test_ko_ratio_calculation():
    from engine.safety.output_token_guard import evaluate_output
    r = evaluate_output(GOOD, lang="ko")
    assert r.ko_char_ratio > 0.7


# ─────────────────────────── 반복 ───────────────────────────

def test_repetition_detected():
    """LLM degeneration 시뮬레이션 — 같은 8자 구절 5회 반복."""
    from engine.safety.output_token_guard import evaluate_output, ISSUE_REPETITION
    rep = "허허허허허허허허" * 5 + " 그대의 결이로구먼."
    r = evaluate_output(rep, lang="ko")
    assert ISSUE_REPETITION in r.issues
    assert r.repetition_count >= 3


def test_normal_text_no_repetition_flag():
    from engine.safety.output_token_guard import evaluate_output, ISSUE_REPETITION
    r = evaluate_output(GOOD, lang="ko")
    assert ISSUE_REPETITION not in r.issues


# ─────────────────────────── 다중 이슈 ───────────────────────────

def test_short_and_truncated_returned_distinctly():
    """매우 짧고 종결 없음 → too_short만 (truncated는 제외)."""
    from engine.safety.output_token_guard import (
        evaluate_output, ISSUE_TOO_SHORT, ISSUE_TRUNCATED,
    )
    r = evaluate_output("허허 그대", lang="ko")
    assert ISSUE_TOO_SHORT in r.issues
    assert ISSUE_TRUNCATED not in r.issues


# ─────────────────────────── 폴백 트리거 매핑 ───────────────────────────

def test_fallback_trigger_truncated_maps_to_token_limit():
    from engine.safety.output_token_guard import (
        evaluate_output, to_fallback_trigger,
    )
    truncated = ("허허, 그대의 상을 살피니, 이 늙은이가 짚는 결은 자네의 결이로구먼. "
                 "삼정이 고르고 명궁이 환하니, 마음의 결이 맑도. 코끝이 환하고 "
                 "이마가 넓으니 초년에 학문이 깊을 결이고 중년에는 자리가 든든할 듯")
    r = evaluate_output(truncated, lang="ko")
    assert to_fallback_trigger(r) == "token_limit"


def test_fallback_trigger_short_maps_to_empty():
    from engine.safety.output_token_guard import (
        evaluate_output, to_fallback_trigger,
    )
    r = evaluate_output("허허.", lang="ko")
    assert to_fallback_trigger(r) == "empty_response"


def test_fallback_trigger_drift_maps_to_persona_failed():
    from engine.safety.output_token_guard import (
        evaluate_output, to_fallback_trigger,
    )
    drift = ("Hello dear sir, the structure of your face says much indeed. "
             "Many things to share with you on this fine day for sure. yours.")
    r = evaluate_output(drift, lang="ko")
    assert to_fallback_trigger(r) == "persona_failed"


def test_fallback_trigger_clean_returns_empty():
    from engine.safety.output_token_guard import (
        evaluate_output, to_fallback_trigger,
    )
    r = evaluate_output(GOOD, lang="ko")
    assert to_fallback_trigger(r) == ""


def test_should_trigger_fallback_only_when_issues():
    from engine.safety.output_token_guard import (
        evaluate_output, should_trigger_fallback,
    )
    clean = evaluate_output(GOOD, lang="ko")
    short = evaluate_output("허허.", lang="ko")
    assert should_trigger_fallback(clean) is False
    assert should_trigger_fallback(short) is True


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_output_token_guard():
    import engine.safety as safety
    assert hasattr(safety, "evaluate_output")
    assert hasattr(safety, "should_trigger_fallback")
    assert hasattr(safety, "to_fallback_trigger")
    assert hasattr(safety, "TokenGuardResult")
    assert hasattr(safety, "ISSUE_TOO_SHORT")
    assert hasattr(safety, "ISSUE_TRUNCATED")
    assert hasattr(safety, "MIN_CHARS")
    assert hasattr(safety, "MAX_CHARS")
