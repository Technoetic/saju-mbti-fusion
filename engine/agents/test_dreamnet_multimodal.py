"""ADR-021 회귀 테스트 — B6 DreamNet v4 멀티모달 통합.

검증 항목:
  1. integrate_multimodal_dream 함수 정합
  2. 입력 모달리티만 통합 (없으면 None 유지)
  3. DEFAULT_DISCLAIMERS 강제 포함 (ADR-006/010/014)
  4. 한국 KCI 규준 편차 계산 (NORMS_KOREAN 연동)
  5. 사용자 출력 인과 표현 0건
  6. integration_score 범위 (-10 ~ +10)
  7. 보고서 §8 회귀 사례 5건 (dreamnet_001~005 핵심)
"""

from __future__ import annotations

from engine.agents.dreamnet_multimodal import (
    DEFAULT_DISCLAIMERS,
    MultimodalIntegration,
    integrate_multimodal_dream,
)


# ─────────────────────────── 기본 함수 정합 ───────────────────────────


def test_integrate_text_only_returns_integration():
    """텍스트 단독 입력 — 통합 결과 반환."""
    result = integrate_multimodal_dream(text="추락하는 꿈")
    assert isinstance(result, MultimodalIntegration)
    assert result.agent == "B6_v4"


def test_available_modalities_text_only():
    """텍스트만 입력 시 available에 'text'만."""
    result = integrate_multimodal_dream(text="꿈")
    assert "text" in result.available_modalities
    assert "voice" not in result.available_modalities
    assert "sleep" not in result.available_modalities


def test_available_modalities_multi():
    """voice·sleep 추가 시 available에 포함."""
    result = integrate_multimodal_dream(
        text="꿈",
        voice_audio_features={"emotion_tone": "fear"},
        sleep_stages={"rem_pct": 0.20},
    )
    assert "text" in result.available_modalities
    assert "voice" in result.available_modalities
    assert "sleep" in result.available_modalities


def test_empty_text_no_text_modality():
    """빈 텍스트 — text 모달리티 미포함."""
    result = integrate_multimodal_dream(text="")
    assert "text" not in result.available_modalities


# ─────────────────────────── ADR-006/010/014 disclaimers 강제 ───────────────────────────


def test_disclaimers_always_present():
    """모든 호출에서 disclaimers 배열 비어있지 않음."""
    result = integrate_multimodal_dream(text="꿈")
    assert len(result.disclaimers) > 0
    assert isinstance(result.disclaimers, list)


def test_disclaimers_includes_no_medical_diagnosis():
    """disclaimers에 '임상 진단 아님' 명시."""
    result = integrate_multimodal_dream(text="꿈")
    combined = " ".join(result.disclaimers)
    assert "임상" in combined or "진단" in combined


def test_disclaimers_includes_hvdc_attribution():
    """disclaimers에 학파 명시 (Hall-Van de Castle)."""
    result = integrate_multimodal_dream(text="꿈")
    combined = " ".join(result.disclaimers)
    assert "Hall-Van de Castle" in combined or "HVDC" in combined


def test_default_disclaimers_count():
    """DEFAULT_DISCLAIMERS 3건 이상."""
    assert len(DEFAULT_DISCLAIMERS) >= 3


# ─────────────────────────── ADR-010 사용자 출력 인과 표현 0건 ───────────────────────────


def test_disclaimers_no_causal_words():
    """disclaimers에 인과·예언 표현 0건."""
    forbidden = ["확실히", "반드시 발생", "당신은 우울증", "당신은 불안 장애", "예언합니다", "운명입니다"]
    result = integrate_multimodal_dream(text="꿈")
    combined = " ".join(result.disclaimers)
    for word in forbidden:
        assert word not in combined, f"인과 표현 발견: {word}"


# ─────────────────────────── 한국 baseline delta ───────────────────────────


def test_korean_baseline_delta_empty_without_hvdc():
    """HVDC 데이터 없으면 delta 비어있음."""
    result = integrate_multimodal_dream(text="꿈")
    assert result.korean_baseline_delta == {}


def test_korean_baseline_delta_computed_with_hvdc():
    """HVDC 데이터 있으면 delta 계산."""
    result = integrate_multimodal_dream(
        text="꿈",
        hvdc_parsed_data={
            "aggression_pct": 73.5,  # 한국 규준 45 대비 +28.5%
        },
    )
    assert "aggression_pct" in result.korean_baseline_delta
    delta_str = result.korean_baseline_delta["aggression_pct"]
    assert "+" in delta_str  # 양수 편차 표시


def test_korean_baseline_delta_negative():
    """음수 편차도 표시."""
    result = integrate_multimodal_dream(
        text="꿈",
        hvdc_parsed_data={
            "negative_emotion_pct": 25.0,  # 한국 규준 40 대비 -15%
        },
    )
    if "negative_emotion_pct" in result.korean_baseline_delta:
        delta_str = result.korean_baseline_delta["negative_emotion_pct"]
        assert "-" in delta_str


# ─────────────────────────── integration_score 범위 ───────────────────────────


def test_integration_score_in_range():
    """integration_score는 -10 ~ +10 범위."""
    result = integrate_multimodal_dream(
        text="꿈",
        hvdc_parsed_data={"aggression_pct": 50},
        voice_audio_features={"emotion_tone": "fear"},
        sleep_stages={"rem_pct": 0.20},
        user_baseline={"aggression_pct": 30},
    )
    assert -10.0 <= result.integration_score <= 10.0


# ─────────────────────────── 보고서 §8 회귀 5건 (dreamnet_001~005 핵심) ───────────────────────────


def test_dreamnet_001_falling_dream():
    """보고서 §8 dreamnet_001: 절벽 추락 꿈 (강한 공포·불안)."""
    result = integrate_multimodal_dream(
        text="끝이 보이지 않는 깎아지른 절벽에서 계속해서 아래로 추락했다.",
        hvdc_parsed_data={"aggression_pct": 73.5},  # +28.5%
    )
    assert "text" in result.available_modalities
    assert len(result.disclaimers) > 0
    # 보고서 expected_disclaimer: "임상적 불안 장애를 진단하는 도구가 아닙니다"
    combined = " ".join(result.disclaimers)
    assert "임상" in combined or "진단" in combined


def test_dreamnet_002_unfamiliar_characters():
    """보고서 §8 dreamnet_002: 낯선 남성들 (남성 캐릭터 100%)."""
    result = integrate_multimodal_dream(
        text="얼굴을 전혀 모르는 건장한 남성 세 명이 무표정하게 노려보고 있었다.",
    )
    assert "text" in result.available_modalities
    assert "Hall-Van de Castle" in " ".join(result.disclaimers) or "HVDC" in " ".join(result.disclaimers)


def test_dreamnet_003_teeth_falling():
    """보고서 §8 dreamnet_003: 이빨 빠짐 (신체 불운)."""
    result = integrate_multimodal_dream(
        text="앞니 두 개가 심하게 흔들리더니 툭 하고 빠졌다.",
    )
    # ADR-006 정합: '신체적 질병 예언 아닙니다' 명시
    combined = " ".join(result.disclaimers)
    assert "예언" in combined or "진단" in combined


def test_dreamnet_004_flying_freedom():
    """보고서 §8 dreamnet_004: 비행·자유 (긍정)."""
    result = integrate_multimodal_dream(
        text="크고 하얀 날개를 단 것처럼 도시의 빌딩 숲 위를 자유롭게 날아다녔다.",
    )
    assert result.agent == "B6_v4"
    assert len(result.disclaimers) > 0


def test_dreamnet_005_pursuit():
    """보고서 §8 dreamnet_005: 추적 (불안)."""
    result = integrate_multimodal_dream(
        text="누군가가 끈질기게 나를 쫓아왔다. 다리가 움직이지 않았다.",
    )
    assert "text" in result.available_modalities
    assert len(result.disclaimers) >= 3


# ─────────────────────────── MultimodalIntegration to_dict ───────────────────────────


def test_to_dict_returns_all_fields():
    """to_dict 메서드가 모든 필드 반환."""
    result = integrate_multimodal_dream(text="꿈")
    d = result.to_dict()
    assert "agent" in d
    assert "disclaimers" in d
    assert "korean_baseline_delta" in d
    assert "available_modalities" in d
    assert "integration_score" in d
