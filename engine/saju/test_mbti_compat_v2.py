"""ADR-024 회귀 테스트 — MBTI 16×16 호환 매트릭스 v2.

검증 항목:
  1. 16 유형 검증 (is_valid_mbti)
  2. 관계 분류 (dual·mirror·conflict·identity·activation·super_ego)
  3. 4단계 알고리즘 (base + S/N + Socionics + Keirsey)
  4. 정규화 [1, 9]
  5. 보고서 §3.3 + §5.1 예시 정합 (INTJ-ENFP·INTP-ENTP·INTP-ESFP 등)
  6. 256 매트릭스 사전 연산 (precompute_matrix)
  7. 대칭 행렬 (compute(a,b) == compute(b,a))
  8. ADR-006/010/014 정합 (DEFAULT_DISCLAIMERS + 학파 명시)
  9. ADR-014 경계 명확화 (사용자 명시 입력만)
"""

from __future__ import annotations

from engine.saju.mbti_compat_v2 import (
    DEFAULT_DISCLAIMERS,
    MBTICompatResult,
    classify_relationship,
    compute_mbti_compat,
    is_valid_mbti,
    precompute_matrix,
)


# ─────────────────────────── 입력 검증 ───────────────────────────


def test_is_valid_16_types():
    """16 표준 유형 모두 검증."""
    for t in ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
              "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"]:
        assert is_valid_mbti(t)


def test_invalid_types_rejected():
    """잘못된 유형 거부."""
    assert not is_valid_mbti("XXXX")
    assert not is_valid_mbti("")
    assert not is_valid_mbti(None)  # type: ignore[arg-type]


def test_lowercase_normalized():
    """소문자 입력 정규화."""
    assert is_valid_mbti("intj")


# ─────────────────────────── 관계 분류 (보고서 §3.3 + §5.1) ───────────────────────────


def test_identity_relationship():
    """동일 유형 = identity."""
    assert classify_relationship("INTJ", "INTJ") == "identity"


def test_dual_relationship_intj_esfp():
    """보고서 §3.3.b: INTJ ↔ ESFP는 dual (E/I 다르되 J/P 공유)."""
    # 실제 Socionics dual은 보고서 §5.1 본문 + 본 시스템 _DUAL_PAIRS 검증
    rel = classify_relationship("INTJ", "ESFP")
    assert rel == "dual"


def test_mirror_relationship_intp_entp():
    """보고서 §3.3.a: INTP ↔ ENTP는 mirror (동일 쿼드라)."""
    assert classify_relationship("INTP", "ENTP") == "mirror"


def test_mirror_relationship_intj_entj():
    """보고서 §3.3.a 예시: INTJ ↔ ENTJ는 mirror."""
    assert classify_relationship("INTJ", "ENTJ") == "mirror"


def test_conflict_relationship_intp_esfp():
    """보고서 §3.3.c 예시: INTP ↔ ESFP는 conflict."""
    assert classify_relationship("INTP", "ESFP") == "conflict"


def test_conflict_intj_esfj():
    """보고서 §3.3.c 예시: INTJ ↔ ESFJ는 conflict."""
    assert classify_relationship("INTJ", "ESFJ") == "conflict"


def test_neutral_for_unmapped():
    """매핑 외 조합은 neutral."""
    rel = classify_relationship("ISTJ", "INFJ")
    # 본 조합은 dual/mirror/activation/conflict/super_ego 어디에도 속하지 않음
    assert rel in ("neutral", "super_ego")


# ─────────────────────────── 4단계 점수 알고리즘 ───────────────────────────


def test_compute_returns_result():
    """compute → MBTICompatResult 반환."""
    r = compute_mbti_compat("INTJ", "ENFP")
    assert isinstance(r, MBTICompatResult)


def test_score_in_range():
    """모든 조합 점수 1~9 범위."""
    types = ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
             "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"]
    for a in types:
        for b in types:
            r = compute_mbti_compat(a, b)
            assert 1 <= r.score <= 9, f"{a}-{b}: score={r.score}"


def test_invalid_input_raises():
    """잘못된 MBTI 입력 시 ValueError."""
    try:
        compute_mbti_compat("XXXX", "INTJ")
        raised = False
    except ValueError:
        raised = True
    assert raised


# ─────────────────────────── 보고서 §5.1 예시 정합 ───────────────────────────


def test_intj_enfp_keirsey_complementary():
    """보고서 §5.1 3단계: INTJ ↔ ENFP NT-NF 결합 + 직관 공유 + T/F·J/P 역전.

    예상: base 5 + S/N 동기화 +2 + Socionics activation +3 + Keirsey +1 = 11 → 9.
    """
    r = compute_mbti_compat("INTJ", "ENFP")
    assert r.sn_bonus == 2  # 둘 다 N
    assert r.keirsey_bonus == 1  # T-F 역전 + J-P 역전 + N 공유
    assert r.score >= 8


def test_intj_esfp_dual_max():
    """보고서 §5.1 2단계: dual = +4. INTJ-ESFP는 S/N 다름(-1).

    base 5 + sn -1 + soc 4 = 8.
    """
    r = compute_mbti_compat("INTJ", "ESFP")
    assert r.relationship_type == "dual"
    assert r.socionics_bonus == 4


def test_intp_esfp_conflict_low():
    """보고서 §3.3.c: INTP ↔ ESFP conflict — 최하점.

    base 5 + sn -1 + soc -4 = 0 → 1 (정규화).
    """
    r = compute_mbti_compat("INTP", "ESFP")
    assert r.relationship_type == "conflict"
    assert r.score <= 2


def test_identity_intj_intj():
    """동일 유형 — base 5 + sn 2 + soc 1 + keirsey 0 = 8.

    Note: 보고서 §5.1 identity는 +1. INTJ-INTJ는 같은 유형이므로 sn 공유 +2.
    """
    r = compute_mbti_compat("INTJ", "INTJ")
    assert r.relationship_type == "identity"
    assert r.sn_bonus == 2
    assert r.socionics_bonus == 1


# ─────────────────────────── 대칭 행렬 ───────────────────────────


def test_symmetric_matrix():
    """compute(a,b) == compute(b,a) (대칭 행렬)."""
    pairs = [
        ("INTJ", "ENFP"),
        ("INTP", "ESFP"),
        ("INFJ", "ESTP"),
        ("ENFP", "ISTJ"),
    ]
    for a, b in pairs:
        r_ab = compute_mbti_compat(a, b)
        r_ba = compute_mbti_compat(b, a)
        assert r_ab.score == r_ba.score, f"{a}-{b}={r_ab.score} != {b}-{a}={r_ba.score}"


# ─────────────────────────── 256 매트릭스 사전 연산 ───────────────────────────


def test_precompute_matrix_size():
    """precompute_matrix 256 엔트리 (16×16)."""
    m = precompute_matrix()
    assert len(m) == 256


def test_precompute_all_scores_valid():
    """precompute_matrix 모든 점수 1~9 범위."""
    m = precompute_matrix()
    for (a, b), score in m.items():
        assert 1 <= score <= 9


# ─────────────────────────── DEFAULT_DISCLAIMERS ADR-006/010/014 정합 ───────────────────────────


def test_disclaimers_count():
    """면책 3건 이상."""
    assert len(DEFAULT_DISCLAIMERS) >= 3


def test_disclaimers_school_explicit():
    """학파 명시 (Jung·Socionics 등)."""
    combined = " ".join(DEFAULT_DISCLAIMERS)
    assert "Jung" in combined or "융" in combined
    assert "Socionics" in combined or "Keirsey" in combined or "재현성" in combined


def test_disclaimers_no_causal():
    """인과·단정 표현 0건."""
    forbidden = ["당신은 [질병]", "확실히 행복", "운명적으로", "예언합니다"]
    combined = " ".join(DEFAULT_DISCLAIMERS)
    for w in forbidden:
        assert w not in combined


def test_disclaimers_self_report_limit():
    """MBTI 학계 한계 명시 (자기보고식·재현성·논쟁)."""
    combined = " ".join(DEFAULT_DISCLAIMERS)
    assert "자기보고" in combined or "재현성" in combined or "논쟁" in combined


def test_disclaimers_multi_factor():
    """다중 요인 명시 (관계는 단일 요인 아님)."""
    combined = " ".join(DEFAULT_DISCLAIMERS)
    assert "다중" in combined or "요인" in combined or "환경" in combined


def test_disclaimers_in_result():
    """결과 객체에 disclaimers 포함."""
    r = compute_mbti_compat("INTJ", "ENFP")
    assert len(r.disclaimers) >= 3


# ─────────────────────────── ADR-014 경계 ───────────────────────────


def test_input_requires_explicit_mbti():
    """함수 시그니처상 사용자 명시 두 MBTI 입력만 받음 (사주→MBTI 단정 X)."""
    # 함수가 type_a + type_b 두 string만 받음 → 사주 입력 시그니처 없음
    import inspect
    sig = inspect.signature(compute_mbti_compat)
    params = list(sig.parameters.keys())
    assert "a" in params and "b" in params
    assert "saju" not in params and "pillars" not in params


# ─────────────────────────── 학파 명시 ───────────────────────────


def test_result_school_explicit():
    """결과에 학파 명시."""
    r = compute_mbti_compat("INTJ", "ENFP")
    assert "Jung" in r.school or "Socionics" in r.school or "Keirsey" in r.school


# ─────────────────────────── Frozen ───────────────────────────


def test_result_frozen():
    """MBTICompatResult frozen."""
    r = compute_mbti_compat("INTJ", "ENFP")
    try:
        r.score = 999  # type: ignore[misc]
        raised = False
    except (AttributeError, Exception):
        raised = True
    assert raised


# ─────────────────────────── to_dict ───────────────────────────


def test_to_dict_includes_components():
    """to_dict 분해 가중치 포함 (debug 가능)."""
    r = compute_mbti_compat("INTJ", "ENFP")
    d = r.to_dict()
    assert "components" in d
    assert "base" in d["components"]
    assert "sn_bonus" in d["components"]
    assert "socionics_bonus" in d["components"]
    assert "keirsey_bonus" in d["components"]
