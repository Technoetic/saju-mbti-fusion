"""ADR-092 회귀 — 궁합 양면 해석 균형도 강화.

ADR-090 단정 차단 + ADR-091 성명학 인용 강화 후 라이브 평가 결과 균형도 15~27%.
긍정 표현 4~7배 많음 → '암묵적 긍정 단정' 위험 → ADR-092로 1:1 균형 지시.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
EXPLAIN_PY = ROOT / "engine" / "saju" / "explain.py"


def _src() -> str:
    return EXPLAIN_PY.read_text(encoding="utf-8")


# ── ① ADR-092 균형도 지시 ──────────────────────────


def test_adr_092_in_directive_list():
    """[지시] 헤더에 ADR-092 명시."""
    src = _src()
    assert "ADR-092" in src
    assert "ADR-006·ADR-010·ADR-014·ADR-091·ADR-092" in src


def test_balance_ratio_directive_present():
    """1:1 균형 비율 지시 명시."""
    src = _src()
    assert "1:1" in src
    assert "균형도" in src or "ADR-092 균형도" in src


def test_per_section_dual_obligation():
    """매 섹션마다 (a) 강점 + (b) 약점 동시 작성 의무 명시."""
    src = _src()
    assert "강점/조화/보완" in src
    assert "갈등/약점/주의" in src
    assert "1+ 문장" in src


def test_single_polarity_section_banned():
    """한 섹션이 긍정만 또는 부정만으로 구성되면 안 됨 명시."""
    src = _src()
    assert "긍정만 또는 부정만으로 구성되면 안 됨" in src


def test_implicit_assertion_warning():
    """'암묵적 긍정 단정' 경고 명시."""
    src = _src()
    assert "암묵적 긍정 단정" in src


# ── ② _COMPAT_SYSTEM 시스템 프롬프트 강화 ──────────


def test_compat_system_no_score_directive():
    """_COMPAT_SYSTEM에 점수·등급·좋은/안 좋은 궁합 금지 명시."""
    from engine.saju.explain import _COMPAT_SYSTEM
    assert "점수" in _COMPAT_SYSTEM and "등급" in _COMPAT_SYSTEM
    assert "좋은/안 좋은 궁합" in _COMPAT_SYSTEM
    assert "절대 금지" in _COMPAT_SYSTEM


def test_compat_system_dual_interpretation():
    """_COMPAT_SYSTEM에 양면 해석 의무 명시."""
    from engine.saju.explain import _COMPAT_SYSTEM
    assert "양면 해석" in _COMPAT_SYSTEM
    assert "강점과 약점" in _COMPAT_SYSTEM
    assert "조화와 갈등" in _COMPAT_SYSTEM


def test_compat_system_single_basis_warning():
    """_COMPAT_SYSTEM에 '단독 근거 X' 명시 (ADR-006)."""
    from engine.saju.explain import _COMPAT_SYSTEM
    assert "단독 근거 X" in _COMPAT_SYSTEM


def test_compat_system_mentions_naming():
    """_COMPAT_SYSTEM에 성명학 음령오행 인용 명시."""
    from engine.saju.explain import _COMPAT_SYSTEM
    assert "성명학" in _COMPAT_SYSTEM
    assert "음령오행" in _COMPAT_SYSTEM


def test_compat_system_mentions_socionics():
    """_COMPAT_SYSTEM에 MBTI Socionics 분류 명시."""
    from engine.saju.explain import _COMPAT_SYSTEM
    assert "Socionics" in _COMPAT_SYSTEM


# ── ③ 옛 잘못된 지시 잔존 차단 ─────────────────


def test_no_old_mbti_score_in_system():
    """옛 'MBTI 호환 점수' 표현 _COMPAT_SYSTEM에서 제거."""
    from engine.saju.explain import _COMPAT_SYSTEM
    assert "MBTI 호환 점수" not in _COMPAT_SYSTEM


def test_no_fixed_4_section_in_system():
    """_COMPAT_SYSTEM이 고정 4섹션 명시 X (조건부 5섹션 정합)."""
    from engine.saju.explain import _COMPAT_SYSTEM
    assert "4섹션" not in _COMPAT_SYSTEM


# ── ④ 기존 ADR 정합 유지 ─────────────────────


def test_adr_090_no_score_grade_preserved():
    """ADR-090 점수·등급 차단 유지."""
    src = _src()
    assert "점수 (X/100)" in src
    assert "점수·등급 단정 X" in src


def test_adr_091_5_section_preserved():
    """ADR-091 5섹션 조건부 작성 형식 유지."""
    src = _src()
    assert "### 5. Naming Resonance" in src
    assert "has_name_flow" in src


def test_adr_071_naming_label_preserved():
    """ADR-071 융합 패턴 라벨 유지."""
    src = _src()
    assert "ADR-071 융합 패턴" in src
    assert "성명학 음령오행 결합" in src
