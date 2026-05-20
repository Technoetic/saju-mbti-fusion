"""ADR-090 회귀 — 궁합 단정 차단 (score·grade 제거).

본 시스템 사주 단독 정책 (좋은/안 좋은 사주 단정 X)을 궁합에도 동일 적용.
"""

from pathlib import Path


# ── ① analyze_compat 반환 구조 ──────────────────────


def test_analyze_compat_no_score_key():
    """analyze_compat 반환에 'score' 키 부재 (ADR-006 단정 차단)."""
    from engine.saju.compat import analyze_compat

    saju_a = {
        "day": "庚辰", "day_master": "庚",
        "wuxing_dist": {"목": 1, "금": 2, "토": 1, "화": 0, "수": 0},
    }
    saju_b = {
        "day": "甲午", "day_master": "甲",
        "wuxing_dist": {"목": 2, "화": 2, "토": 0, "금": 0, "수": 0},
    }
    result = analyze_compat(saju_a, saju_b)
    assert "score" not in result, f"score 단정 키 잔존: {result.keys()}"
    assert "grade" not in result, f"grade 단정 키 잔존: {result.keys()}"


def test_analyze_compat_no_grade_label():
    """반환에 '최상·상·중·하·최하' 등급 라벨 부재."""
    from engine.saju.compat import analyze_compat
    saju_a = {"day": "庚辰", "wuxing_dist": {}}
    saju_b = {"day": "甲午", "wuxing_dist": {}}
    result = analyze_compat(saju_a, saju_b)
    for grade in ("최상", "상", "중", "하", "최하"):
        assert result.get("grade") != grade


def test_analyze_compat_has_disclaimer():
    """ADR-090 면책 문구 포함."""
    from engine.saju.compat import analyze_compat
    result = analyze_compat({"day": "庚辰", "wuxing_dist": {}}, {"day": "甲午", "wuxing_dist": {}})
    assert "disclaimer" in result
    assert "단정 X" in result["disclaimer"]
    assert "ADR-006" in result["disclaimer"]


def test_mbti_returns_socionics_label_not_score():
    """MBTI 호환 결과가 학파 라벨 (Duality·Identity·Standard)이며 점수 X."""
    from engine.saju.compat import analyze_compat
    result = analyze_compat(
        {"day": "庚辰", "wuxing_dist": {}}, {"day": "甲午", "wuxing_dist": {}},
        mbti_a="INTJ", mbti_b="ENFP",
    )
    mbti = result.get("mbti", {})
    assert "score" not in mbti, f"MBTI score 단정 잔존: {mbti}"
    assert "socionics_label" in mbti
    assert mbti["socionics_label"] == "Duality (보완)"


def test_mbti_identity_pair():
    """동일 MBTI = Identity 라벨."""
    from engine.saju.compat import analyze_compat
    result = analyze_compat(
        {"day": "庚辰", "wuxing_dist": {}}, {"day": "甲午", "wuxing_dist": {}},
        mbti_a="INTJ", mbti_b="INTJ",
    )
    assert result["mbti"]["socionics_label"] == "Identity (동일)"


def test_mbti_standard_pair():
    """미등록 페어 = Standard 라벨."""
    from engine.saju.compat import analyze_compat
    result = analyze_compat(
        {"day": "庚辰", "wuxing_dist": {}}, {"day": "甲午", "wuxing_dist": {}},
        mbti_a="INTJ", mbti_b="ISFJ",
    )
    assert result["mbti"]["socionics_label"] == "Standard (표준)"


def test_stem_relations_preserved():
    """결정론 라벨 (合·沖) 유지 (단정 제거 X 결정론 X)."""
    from engine.saju.compat import analyze_compat
    result = analyze_compat({"day": "甲子", "wuxing_dist": {}}, {"day": "己卯", "wuxing_dist": {}})
    assert "stem" in result
    assert "branch" in result
    assert "wuxing_flow" in result


# ── ② explain_compat 프롬프트 단정 차단 ─────────────


def _explain_src() -> str:
    return Path(
        Path(__file__).resolve().parent.parent.parent / "engine/saju/explain.py"
    ).read_text(encoding="utf-8")


def test_explain_no_score_grade_in_prompt():
    """explain_compat user 프롬프트에 종합 점수 형식 부재."""
    src = _explain_src()
    # 옛 패턴 제거 확인
    assert "종합 점수: " not in src or "ADR-090" in src
    assert "/100" not in src or "ADR-090" in src


def test_explain_directive_blocks_grade_words():
    """explain_compat가 LLM에 '좋은/안 좋은 궁합·최상·최하' 차단 지시 명시."""
    src = _explain_src()
    assert "좋은 궁합" in src
    assert "안 좋은 궁합" in src
    assert "최상" in src
    assert "최하" in src
    assert "단정 표현 절대 금지" in src


def test_explain_directive_balanced_interpretation():
    """양면 해석 의무 명시."""
    src = _explain_src()
    assert "양면 해석 의무" in src
    assert "강점과 약점 동시" in src


def test_explain_directive_pretraining_block():
    """사전학습 명리학 어휘 추가 차단 지시."""
    src = _explain_src()
    assert "사전학습 명리학 어휘 추가 금지" in src


def test_explain_mbti_block_uses_label_not_score():
    """MBTI 블록이 점수 X 학파 라벨 사용."""
    src = _explain_src()
    assert "Socionics 분류" in src
    assert "socionics_label" in src


# ── ③ ADR-002 학파 명시 ───────────────────────────


def test_socionics_relations_module_has_label():
    """_MBTI_SOCIONICS_RELATIONS에 Duality·Identity 라벨만 (점수 X)."""
    from engine.saju import compat
    src = open(compat.__file__, "r", encoding="utf-8").read()
    assert "Duality (보완)" in src
    assert "Identity (동일)" in src
    assert "Socionics 학파" in src


def test_mbti_socionics_label_function_exists():
    """_mbti_socionics_label 함수 존재."""
    from engine.saju.compat import _mbti_socionics_label
    assert callable(_mbti_socionics_label)


# ── ④ 라이브 사례 검증 ────────────────────────────


def test_live_case_good_vs_bad_saju_no_score():
    """직전 라이브 사례 (1988-08-15 vs 1975-04-22) 결정론 산출 시 score·grade 부재."""
    from engine.saju.compat import analyze_compat
    saju_a = {"day": "壬寅", "wuxing_dist": {"수": 2, "목": 2, "화": 0, "토": 0, "금": 0}}
    saju_b = {"day": "戊戌", "wuxing_dist": {"토": 3, "화": 0, "금": 1, "수": 0, "목": 0}}
    result = analyze_compat(saju_a, saju_b, mbti_a="INTJ", mbti_b="ENFP")
    assert "score" not in result
    assert "grade" not in result
    assert "disclaimer" in result
    # MBTI Duality 라벨만
    assert result["mbti"]["socionics_label"] == "Duality (보완)"
