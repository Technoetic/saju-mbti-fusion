"""engine.safety.llm.response_fact_check — §5.2.8 응답 사실 검증 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 빈 입력 ───────────────────────────

def test_empty_text_passes():
    from engine.safety.llm.response_fact_check import check_response
    r = check_response("", age=30)
    assert r.passed is True
    assert r.violations == []


def test_none_inputs_safe():
    from engine.safety.llm.response_fact_check import check_response
    r = check_response(None)
    assert r.passed is True


# ─────────────────────────── 나이 일관성 ───────────────────────────

def test_age_consistent_young_passes():
    from engine.safety.llm.response_fact_check import check_response
    r = check_response("허허, 그대의 상은 청년의 결이로구먼.", age=25)
    assert r.passed is True


def test_age_mismatch_elderly_word_for_young_user():
    """입력 나이 25인데 '고희를 넘기' 언급 → 위반."""
    from engine.safety.llm.response_fact_check import check_response, FACT_AGE
    r = check_response("허허, 그대가 고희를 넘기신 모습이로다.", age=25)
    assert FACT_AGE in r.violations
    assert "고희" in " ".join(r.matched_terms)


def test_age_mismatch_young_word_for_elderly_user():
    from engine.safety.llm.response_fact_check import check_response, FACT_AGE
    r = check_response("허허, 그대의 청년 같은 결이로세.", age=70)
    assert FACT_AGE in r.violations


def test_age_unknown_skips_check():
    """age=None이면 검사 안 함."""
    from engine.safety.llm.response_fact_check import check_response, FACT_AGE
    r = check_response("허허, 노년의 결이로다.", age=None)
    assert FACT_AGE not in r.violations


def test_age_negated_context_ignored():
    """'고희를 넘기신 듯하나 아니라' 같은 부정문맥은 위반 아님."""
    from engine.safety.llm.response_fact_check import check_response, FACT_AGE
    r = check_response("고희를 넘기신 듯하나 그것은 아니라 청년의 결이로세.",
                       age=25)
    assert FACT_AGE not in r.violations


# ─────────────────────────── 성별 일관성 ───────────────────────────

def test_gender_consistent_male_passes():
    from engine.safety.llm.response_fact_check import check_response
    r = check_response("허허, 사내의 상이로구먼.", gender="male")
    assert r.passed is True


def test_gender_mismatch_female_word_for_male():
    from engine.safety.llm.response_fact_check import check_response, FACT_GENDER
    r = check_response("허허, 따님의 상이로구먼.", gender="male")
    assert FACT_GENDER in r.violations


def test_gender_mismatch_male_word_for_female():
    from engine.safety.llm.response_fact_check import check_response, FACT_GENDER
    r = check_response("허허, 사내아이의 상이로구먼.", gender="female")
    assert FACT_GENDER in r.violations


def test_gender_korean_form_normalization():
    """'남' / '여' 도 인식."""
    from engine.safety.llm.response_fact_check import check_response, FACT_GENDER
    r = check_response("허허, 따님의 상이로구먼.", gender="남")
    assert FACT_GENDER in r.violations


def test_gender_none_skips_check():
    from engine.safety.llm.response_fact_check import check_response, FACT_GENDER
    r = check_response("허허, 따님의 상이로구먼.", gender=None)
    assert FACT_GENDER not in r.violations


# ─────────────────────────── face_count ───────────────────────────

def test_face_count_one_alone_passes():
    from engine.safety.llm.response_fact_check import check_response
    r = check_response("허허, 그대 한 분의 상이로세.", metrics={"face_count": 1})
    assert r.passed is True


def test_face_count_one_but_multi_face_word():
    from engine.safety.llm.response_fact_check import check_response, FACT_FACE_COUNT
    r = check_response("허허, 두 분의 상을 함께 짚어보니",
                       metrics={"face_count": 1})
    assert FACT_FACE_COUNT in r.violations


def test_face_count_two_skipped():
    """face_count != 1이면 multi-face 언급 허용."""
    from engine.safety.llm.response_fact_check import check_response, FACT_FACE_COUNT
    r = check_response("두 분의 상을 함께 짚어보니",
                       metrics={"face_count": 2})
    assert FACT_FACE_COUNT not in r.violations


# ─────────────────────────── region 일관성 ───────────────────────────

def test_region_kr_consistent_passes():
    from engine.safety.llm.response_fact_check import check_response
    r = check_response("허허, 동방의 사람의 결이로세.", region="KR")
    assert r.passed is True


def test_region_kr_but_european_word():
    from engine.safety.llm.response_fact_check import check_response, FACT_REGION
    r = check_response("허허, 유럽인의 상이로다.", region="KR")
    assert FACT_REGION in r.violations


def test_region_eu_but_korean_word():
    from engine.safety.llm.response_fact_check import check_response, FACT_REGION
    r = check_response("허허, 한국인의 상이로구먼.", region="DE")
    assert FACT_REGION in r.violations


def test_region_unknown_skips():
    from engine.safety.llm.response_fact_check import check_response, FACT_REGION
    r = check_response("유럽인의 상이로다.", region="US-CA")
    assert FACT_REGION not in r.violations


# ─────────────────────────── 시선 ───────────────────────────

def test_gaze_locked_passes():
    from engine.safety.llm.response_fact_check import check_response
    r = check_response("맑게 정면을 보시는 결이로구먼.",
                       metrics={"gaze_locked": True})
    assert r.passed is True


def test_gaze_unlocked_but_strong_gaze_word():
    from engine.safety.llm.response_fact_check import check_response, FACT_GAZE
    r = check_response("허허, 그대 맑게 정면을 보시는 결이로다.",
                       metrics={"gaze_locked": False})
    assert FACT_GAZE in r.violations


def test_gaze_none_skips():
    from engine.safety.llm.response_fact_check import check_response, FACT_GAZE
    r = check_response("맑게 정면을 보시는 결이로다.", metrics={})
    assert FACT_GAZE not in r.violations


# ─────────────────────────── 통합 ───────────────────────────

def test_multiple_violations_aggregated():
    """여러 차원 동시 위반 시 모두 수집."""
    from engine.safety.llm.response_fact_check import check_response
    r = check_response(
        "허허, 따님의 고희를 넘기신 유럽인의 상이로다.",
        age=25,
        gender="male",
        region="KR",
    )
    assert len(r.violations) >= 3


def test_clean_response_no_violations():
    from engine.safety.llm.response_fact_check import check_response
    r = check_response(
        "허허, 그대 한 분의 상을 짚으니 청년의 결이로구먼.",
        age=25,
        gender="male",
        region="KR",
        metrics={"face_count": 1, "gaze_locked": True},
    )
    assert r.passed is True
    assert r.violations == []


# ─────────────────────────── 폴백 매핑 ───────────────────────────

def test_fallback_trigger_violation_maps_to_persona_failed():
    from engine.safety.llm.response_fact_check import (
        check_response, to_fallback_trigger,
    )
    r = check_response("따님의 상이로구먼.", gender="male")
    assert to_fallback_trigger(r) == "persona_failed"


def test_fallback_trigger_clean_returns_empty():
    from engine.safety.llm.response_fact_check import (
        check_response, to_fallback_trigger,
    )
    r = check_response("허허, 그대의 결이로세.", gender="male")
    assert to_fallback_trigger(r) == ""


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_fact_check():
    import engine.safety as safety
    assert hasattr(safety, "check_response")
    assert hasattr(safety, "FactCheckResult")
    assert hasattr(safety, "FACT_AGE")
    assert hasattr(safety, "FACT_GENDER")
    assert hasattr(safety, "FACT_FACE_COUNT")
    assert hasattr(safety, "FACT_REGION")
    assert hasattr(safety, "FACT_GAZE")


# ───── ADR-004 Phase 3 — palace_score 단정 환각 검출 회귀 ─────

def test_palace_score_none_skips_check():
    """palace_scores=None이면 검증 면제(역호환)."""
    from engine.safety.llm.response_fact_check import (
        check_response, FACT_PALACE_SCORE,
    )
    r = check_response("재백궁이 환하게 빛나는도다.", palace_scores=None)
    assert FACT_PALACE_SCORE not in r.violations


def test_palace_score_strong_assertion_with_low_score_violates():
    """결정론 점수 0.15인데 '재물복이 풍성' 단정 → 위반."""
    from engine.safety.llm.response_fact_check import (
        check_response, FACT_PALACE_SCORE,
    )
    r = check_response(
        "허허, 그대 재물복이 풍성하니 곳간이 넉넉하리라.",
        palace_scores={"jaebaek": 0.15},
    )
    assert FACT_PALACE_SCORE in r.violations
    assert any("jaebaek:strong" in m for m in r.matched_terms)


def test_palace_score_weak_assertion_with_high_score_violates():
    """결정론 점수 0.85인데 '재물이 빈약' 단정 → 위반."""
    from engine.safety.llm.response_fact_check import (
        check_response, FACT_PALACE_SCORE,
    )
    r = check_response(
        "허허, 그대 재물이 빈약한 결이로구먼.",
        palace_scores={"jaebaek": 0.85},
    )
    assert FACT_PALACE_SCORE in r.violations
    assert any("jaebaek:weak" in m for m in r.matched_terms)


def test_palace_score_medium_score_allows_either_phrasing():
    """중간 점수(0.5)는 두 어휘 모두 허용 — 단정 환각 검출만 목표."""
    from engine.safety.llm.response_fact_check import (
        check_response, FACT_PALACE_SCORE,
    )
    r1 = check_response("재백궁이 환하게 빛나는도다.",
                        palace_scores={"jaebaek": 0.5})
    r2 = check_response("재물이 빈약한 결이로다.",
                        palace_scores={"jaebaek": 0.5})
    assert FACT_PALACE_SCORE not in r1.violations
    assert FACT_PALACE_SCORE not in r2.violations


def test_palace_score_consistent_strong_passes():
    """결정론 점수 0.85 + '재백궁이 환하' 단정 → 일치, 위반 아님."""
    from engine.safety.llm.response_fact_check import (
        check_response, FACT_PALACE_SCORE,
    )
    r = check_response(
        "허허, 그대 재백궁이 환하게 빛나는도다.",
        palace_scores={"jaebaek": 0.85},
    )
    assert FACT_PALACE_SCORE not in r.violations


def test_palace_score_negated_assertion_ignored():
    """'재물복이 풍성한 것은 아니로다' 부정문맥은 위반 아님."""
    from engine.safety.llm.response_fact_check import (
        check_response, FACT_PALACE_SCORE,
    )
    r = check_response(
        "재물복이 풍성한 것은 아니라 평이한 결이로세.",
        palace_scores={"jaebaek": 0.15},
    )
    assert FACT_PALACE_SCORE not in r.violations


def test_palace_score_multi_palace_independent():
    """여러 궁 동시 검증 — 한 궁 위반이 다른 궁 면제 안 함."""
    from engine.safety.llm.response_fact_check import (
        check_response, FACT_PALACE_SCORE,
    )
    r = check_response(
        "재백궁이 환하고 관록궁이 흐리니, 재물은 두텁고 벼슬은 약하리라.",
        palace_scores={"jaebaek": 0.10, "gwanrok": 0.90},
    )
    # jaebaek: 점수 낮은데 "환하" 단정 → 위반
    # gwanrok: 점수 높은데 "흐리" 단정 → 위반
    assert FACT_PALACE_SCORE in r.violations
    matched = " ".join(r.matched_terms)
    assert "jaebaek" in matched
    assert "gwanrok" in matched


def test_palace_score_non_numeric_skipped():
    """점수가 숫자가 아니면 해당 궁만 스킵, 다른 궁은 검증."""
    from engine.safety.llm.response_fact_check import (
        check_response, FACT_PALACE_SCORE,
    )
    r = check_response(
        "재백궁이 환하게 빛나는도다.",
        palace_scores={"jaebaek": "invalid", "gwanrok": 0.5},  # type: ignore[dict-item]
    )
    # jaebaek 점수가 비정상이므로 검증 면제
    assert FACT_PALACE_SCORE not in r.violations


def test_palace_score_fallback_trigger_maps_to_persona_failed():
    """단정 환각 검출 시 폴백 트리거 = persona_failed."""
    from engine.safety.llm.response_fact_check import (
        check_response, to_fallback_trigger,
    )
    r = check_response(
        "재물복이 풍성하리라.",
        palace_scores={"jaebaek": 0.10},
    )
    assert to_fallback_trigger(r) == "persona_failed"


def test_palace_score_exported_const():
    """FACT_PALACE_SCORE 상수 노출 확인."""
    from engine.safety.llm.response_fact_check import FACT_PALACE_SCORE
    assert FACT_PALACE_SCORE == "palace_score_mismatch"


def test_safety_gate_accepts_palace_scores_kwarg():
    """run_safety_gates가 palace_scores kwarg를 받아 fact_check로 전달."""
    from engine.safety.llm.output_safety_gate import run_safety_gates
    r = run_safety_gates(
        "재물복이 풍성하리니 곳간이 넉넉하리라. 허허, 청년의 결이 두텁고 결이 환하니 좋은 자리로다.",
        palace_scores={"jaebaek": 0.10},
    )
    # 단정 환각 검출이 fact_check로 흘러야 함
    assert "fact_mismatch" in r.failures
