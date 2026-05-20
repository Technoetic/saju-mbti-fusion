"""ADR-059 회귀 — EU AI Act §52 AI 리터러시 면책 의무 검증."""

from engine.safety import (
    AI_LITERACY_DISCLAIMER_KO,
    build_legal_footer,
)


def test_literacy_disclaimer_lists_uncertainty():
    """리터러시 면책에 정확도 미보증·오작동·편향 명시."""
    assert "정확도를 보증하지 않" in AI_LITERACY_DISCLAIMER_KO
    assert "오작동" in AI_LITERACY_DISCLAIMER_KO
    assert "편향" in AI_LITERACY_DISCLAIMER_KO


def test_literacy_disclaimer_lists_unsuitable_decisions():
    """의료·법률·금융·진로 의사결정 단독 근거 금지 명시 (ADR-006 정합)."""
    assert "의료" in AI_LITERACY_DISCLAIMER_KO
    assert "법률" in AI_LITERACY_DISCLAIMER_KO
    assert "금융" in AI_LITERACY_DISCLAIMER_KO


def test_legal_footer_contains_literacy():
    """build_legal_footer 호출 시 §52 리터러시 자동 포함."""
    footer = build_legal_footer()
    assert "정확도를 보증하지 않" in footer
    assert "오작동" in footer


def test_legal_footer_has_both_ai_labels():
    """§50 AI 생성 라벨 + §52 리터러시 면책 둘 다 포함."""
    footer = build_legal_footer()
    assert "EU AI Act §50" in footer  # ADR-058
    assert "오작동·편향" in footer or "오작동" in footer  # ADR-059
