"""ADR-058 회귀 — EU AI Act §50 AI 생성 라벨 의무 검증.

본 풀이 응답이 AI 생성임을 사용자에게 명시하는 두 채널 의무:
- human-readable: build_legal_footer() 텍스트에 AI 생성 라벨 포함
- machine-readable: build_ai_generation_meta() dict 반환
"""

from engine.safety import (
    AI_GENERATED_LABEL_KO,
    build_legal_footer,
    build_ai_generation_meta,
)


def test_legal_footer_contains_ai_label():
    """build_legal_footer 호출 시 EU AI Act §50 라벨 자동 포함."""
    footer = build_legal_footer()
    assert "AI 시스템" in footer
    assert "EU AI Act §50" in footer


def test_legal_footer_with_data_notice_still_has_ai_label():
    """data notice 옵션 포함 시에도 AI 라벨 유지."""
    footer = build_legal_footer(include_data_notice=True)
    assert AI_GENERATED_LABEL_KO in footer


def test_ai_generation_meta_default():
    """모델 라벨 미명시 시 unspecified로 fallback."""
    meta = build_ai_generation_meta()
    assert meta["ai_generated"] is True
    assert meta["framework"] == "EU AI Act §50"
    assert meta["model_label"] == "unspecified"
    assert meta["human_readable_label_ko"] == AI_GENERATED_LABEL_KO
    assert "confidence" not in meta  # None은 omit


def test_ai_generation_meta_with_model_label():
    """모델 라벨 명시 시 반영."""
    meta = build_ai_generation_meta(model_label="claude-opus-4.7")
    assert meta["model_label"] == "claude-opus-4.7"


def test_ai_generation_meta_confidence_clipped():
    """confidence 0.0~1.0 범위 강제."""
    meta_low = build_ai_generation_meta(confidence=-0.5)
    assert meta_low["confidence"] == 0.0
    meta_high = build_ai_generation_meta(confidence=1.5)
    assert meta_high["confidence"] == 1.0
    meta_normal = build_ai_generation_meta(confidence=0.85)
    assert meta_normal["confidence"] == 0.85


def test_crisis_footer_does_not_lose_ai_context():
    """위기 푸터는 의료 거부 톤이라 별도 — AI 라벨은 정상 푸터에만 의무."""
    crisis = build_legal_footer(is_crisis=True)
    # 위기 푸터는 119·1393 안내 핵심 — AI 라벨은 통합 푸터에만
    assert "1393" in crisis or "119" in crisis
