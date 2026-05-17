"""engine.divination.palm_scoring — 회귀 테스트 (ADR-030).

보고서 §7 30쌍 회귀 + ADR-010 면책 자동 검증 + 결정론.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ───────────────────── 데이터 로드 ─────────────────────


def test_rules_load():
    from engine.divination.palm_scoring import total_lines, is_loaded
    assert is_loaded()
    assert total_lines() == 5  # 4대 선 + 금성대


# ───────────────────── score_palm 기본 ─────────────────────


def test_score_palm_returns_report():
    from engine.divination.palm_scoring import score_palm, PalmScoringReport
    kp = {"lifeline_arc": 0.85, "headline_horizontal": 0.65,
          "heartline_curve": 0.50, "fateline_vertical": 0.20}
    r = score_palm(kp, hand_side="right")
    assert isinstance(r, PalmScoringReport)
    assert r.hand_side == "right"
    assert "lifeline" in r.lines
    assert "headline" in r.lines
    assert "heartline" in r.lines
    assert "fateline" in r.lines
    assert "girdle_of_venus" in r.lines


def test_score_palm_line_score_schema():
    from engine.divination.palm_scoring import score_palm
    kp = {"lifeline_arc": 0.85}
    r = score_palm(kp)
    lifeline = r.lines["lifeline"]
    assert hasattr(lifeline, "score")
    assert hasattr(lifeline, "label")
    assert hasattr(lifeline, "label_ko")
    assert hasattr(lifeline, "evidence")
    assert hasattr(lifeline, "academic_source")
    assert 0.0 <= lifeline.score <= 1.0
    assert lifeline.label in ("low", "medium", "high")


def test_score_palm_thresholds_lifeline():
    """생명선 임계값 low<0.73 / medium [0.73, 0.89] / high>0.89."""
    from engine.divination.palm_scoring import score_palm
    # low
    r_low = score_palm({"lifeline_arc": 0.50})
    assert r_low.lines["lifeline"].label == "low"
    # medium
    r_med = score_palm({"lifeline_arc": 0.81})
    assert r_med.lines["lifeline"].label == "medium"
    # high
    r_hi = score_palm({"lifeline_arc": 0.95})
    assert r_hi.lines["lifeline"].label == "high"


def test_score_palm_thresholds_headline():
    """두뇌선 임계값 low<0.53 / medium [0.53, 0.77] / high>0.77."""
    from engine.divination.palm_scoring import score_palm
    assert score_palm({"headline_horizontal": 0.40}).lines["headline"].label == "low"
    assert score_palm({"headline_horizontal": 0.65}).lines["headline"].label == "medium"
    assert score_palm({"headline_horizontal": 0.88}).lines["headline"].label == "high"


def test_score_palm_thresholds_heartline():
    """감정선 임계값 low<0.43 / medium [0.43, 0.73] / high>0.73."""
    from engine.divination.palm_scoring import score_palm
    assert score_palm({"heartline_curve": 0.30}).lines["heartline"].label == "low"
    assert score_palm({"heartline_curve": 0.58}).lines["heartline"].label == "medium"
    assert score_palm({"heartline_curve": 0.91}).lines["heartline"].label == "high"


def test_score_palm_thresholds_fateline():
    """운명선 임계값 low<0.25 / medium [0.25, 0.65] / high>0.65."""
    from engine.divination.palm_scoring import score_palm
    assert score_palm({"fateline_vertical": 0.15}).lines["fateline"].label == "low"
    assert score_palm({"fateline_vertical": 0.45}).lines["fateline"].label == "medium"
    assert score_palm({"fateline_vertical": 0.85}).lines["fateline"].label == "high"


# ───────────────────── 보고서 §7 회귀 30쌍 ─────────────────────


def _load_regression():
    import json
    p = Path(__file__).resolve().parent.parent.parent / "data" / "palm_scoring_regression.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def test_regression_data_loads():
    """30쌍 회귀 데이터 로드 검증."""
    data = _load_regression()
    assert data["adr"] == "ADR-030"
    assert len(data["tests"]) == 30
    for t in data["tests"]:
        assert "id" in t and t["id"].startswith("palm_")
        assert "hand_side" in t and t["hand_side"] in ("left", "right")
        assert "expected_scores" in t


def test_regression_label_accuracy_4_lines():
    """4대 선 라벨 정확도 — 보고서 30쌍 × 4선 = 120건 모두 PASS."""
    from engine.divination.palm_scoring import score_palm
    data = _load_regression()

    def expected_label_for(value: float, line_key: str) -> str:
        thresholds = {
            "lifeline_arc": (0.73, 0.89),
            "headline_horizontal": (0.53, 0.77),
            "heartline_curve": (0.43, 0.73),
            "fateline_vertical": (0.25, 0.65),
        }
        low, high = thresholds[line_key]
        if value < low:
            return "low"
        if value > high:
            return "high"
        return "medium"

    line_key_map = {
        "lifeline": "lifeline_arc",
        "headline": "headline_horizontal",
        "heartline": "heartline_curve",
        "fateline": "fateline_vertical",
    }

    total = 0
    correct = 0
    for t in data["tests"]:
        kp = t["expected_scores"]
        r = score_palm(kp, hand_side=t["hand_side"])
        for line_key, raw_key in line_key_map.items():
            expected_value = kp[raw_key]
            expected = expected_label_for(expected_value, raw_key)
            got = r.lines[line_key].label
            total += 1
            if got == expected:
                correct += 1

    assert total == 120  # 30 cases × 4 lines
    assert correct == 120, f"Label accuracy {correct}/120"


# ───────────────────── ADR-010 차단 토큰 ─────────────────────


def test_forbidden_tokens_safe():
    from engine.divination.palm_scoring import filter_forbidden_tokens
    safe, matches = filter_forbidden_tokens("이 선은 형태가 뚜렷합니다")
    assert safe is True
    assert matches == []


def test_forbidden_tokens_medical():
    """의료 단정형 토큰 차단."""
    from engine.divination.palm_scoring import filter_forbidden_tokens
    for token in ["단명", "사망", "치매", "유전병", "다운증후군"]:
        safe, matches = filter_forbidden_tokens(f"이 선은 {token} 위험을 보입니다")
        assert safe is False, f"{token} 차단 실패"
        assert token in matches


def test_forbidden_tokens_risk():
    """사적 위험 인과형 차단."""
    from engine.divination.palm_scoring import filter_forbidden_tokens
    for token in ["이혼", "파산", "과부", "절연", "횡사"]:
        safe, matches = filter_forbidden_tokens(f"{token}의 운세")
        assert safe is False, f"{token} 차단 실패"


def test_forbidden_tokens_personality():
    """성격 결함형 차단."""
    from engine.divination.palm_scoring import filter_forbidden_tokens
    for token in ["호르몬 이상", "지능 저하", "어리석음"]:
        safe, matches = filter_forbidden_tokens(f"이 사람은 {token}을 가집니다")
        assert safe is False, f"{token} 차단 실패"


def test_disclaimer_ko_loaded():
    from engine.divination.palm_scoring import disclaimer_palm_ko
    d = disclaimer_palm_ko()
    assert "MediaPipe" in d
    assert "절대적 예언" in d
    assert "의학적 진단" in d


# ───────────────────── 결정론 ─────────────────────


def test_deterministic():
    from engine.divination.palm_scoring import score_palm
    kp = {"lifeline_arc": 0.85, "headline_horizontal": 0.65,
          "heartline_curve": 0.50, "fateline_vertical": 0.20}
    r1 = score_palm(kp, hand_side="right")
    r2 = score_palm(kp, hand_side="right")
    for key in r1.lines:
        assert r1.lines[key].score == r2.lines[key].score
        assert r1.lines[key].label == r2.lines[key].label


def test_rationale_includes_disclaimer():
    """rationale에 학파 명시 + 면책 자동 포함 (ADR-002 + ADR-010)."""
    from engine.divination.palm_scoring import score_palm
    kp = {"lifeline_arc": 0.85}
    r = score_palm(kp, hand_side="right")
    assert "Samudrika Shastra" in r.rationale or "학설" in r.rationale
    assert "인과관계" in r.rationale or "운명" in r.rationale or "예언" in r.rationale


def test_rationale_no_causal_predictions():
    """rationale 본문 (면책 제외) ADR-010 차단 토큰 부재.

    면책 표현 자체에는 '수명·운명' 등 부정 문맥 단어 포함 정당.
    실 본문(점수 설명) 영역만 검사.
    """
    from engine.divination.palm_scoring import (
        score_palm, filter_forbidden_tokens, disclaimer_palm_ko,
    )
    kp_cases = [
        {"lifeline_arc": 0.95, "headline_horizontal": 0.90,
         "heartline_curve": 0.85, "fateline_vertical": 0.88},
        {"lifeline_arc": 0.22, "headline_horizontal": 0.22,
         "heartline_curve": 0.30, "fateline_vertical": 0.15},
    ]
    disclaimer = disclaimer_palm_ko()
    for kp in kp_cases:
        r = score_palm(kp, hand_side="right")
        # 면책 부분 + "운명·수명·재물과 인과관계는 없습니다" 부정 표현 제외
        body = r.rationale.replace(disclaimer, "")
        # 명시적 면책 문구 ("운명·수명·재물과 인과관계는 없습니다") 제외
        body = body.replace("운명·수명·재물과 인과관계는 없습니다", "")
        safe, matches = filter_forbidden_tokens(body)
        assert safe is True, f"rationale 본문 차단 토큰 노출: {matches}"


# ───────────────────── 비대칭성 지수 (C5) ─────────────────────


def test_asymmetry_index():
    """좌우 손 비대칭성 — 보고서 §5.1 패턴."""
    from engine.divination.palm_scoring import score_palm, asymmetry_index
    kp_left = {"lifeline_arc": 0.85, "headline_horizontal": 0.65,
               "heartline_curve": 0.50, "fateline_vertical": 0.20}
    kp_right = {"lifeline_arc": 0.45, "headline_horizontal": 0.85,
                "heartline_curve": 0.75, "fateline_vertical": 0.55}
    left_r = score_palm(kp_left, hand_side="left")
    right_r = score_palm(kp_right, hand_side="right")
    ai = asymmetry_index(left_r, right_r)
    assert "asymmetry_index" in ai
    assert "line_deltas" in ai
    assert "rationale" in ai
    assert ai["asymmetry_index"] >= 0
    # 면책 자동 포함
    from engine.divination.palm_scoring import filter_forbidden_tokens
    safe, matches = filter_forbidden_tokens(ai["rationale"])
    assert safe is True, f"비대칭성 rationale 차단 토큰: {matches}"


def test_asymmetry_school_named():
    """비대칭성 rationale에 학파 명시 (ADR-002)."""
    from engine.divination.palm_scoring import score_palm, asymmetry_index
    kp = {"lifeline_arc": 0.5, "headline_horizontal": 0.5,
          "heartline_curve": 0.5, "fateline_vertical": 0.5}
    lr = score_palm(kp, hand_side="left")
    rr = score_palm(kp, hand_side="right")
    ai = asymmetry_index(lr, rr)
    assert "Samudrika Shastra" in ai["rationale"] or "학설" in ai["rationale"]


# ───────────────────── face_scoring 패턴 호환 ─────────────────────


def test_line_score_has_evidence_field():
    """face_scoring.PalaceScore 패턴 — evidence 필드 존재."""
    from engine.divination.palm_scoring import score_palm
    kp = {"lifeline_arc": 0.85}
    r = score_palm(kp)
    for key, ls in r.lines.items():
        assert hasattr(ls, "evidence")
        assert isinstance(ls.evidence, float)


def test_metadata_adr_reference():
    """metadata에 ADR 참조 명시."""
    from engine.divination.palm_scoring import score_palm
    r = score_palm({"lifeline_arc": 0.85})
    assert "adr" in r.metadata
    assert "ADR-030" in r.metadata["adr"]
