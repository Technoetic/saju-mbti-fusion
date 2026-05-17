"""B6 DreamNet 다중모달 융합기 (v4 — 하드웨어 인터페이스만).

문서: EEG/심박 + 텍스트 통합, 목표 정확도 99% (Bertolini DreamNet 2025).

본 모듈은 v4 인터페이스 정의만. 실제 EEG/HRV 융합은 Apple Watch·Galaxy Ring·
가정용 EEG 디바이스가 보급되고 SDK 안정화 후 활성.

현재 활성: 사용자 자가보고 생체 신호 입력 (수면 시간·심박 평균·각성 횟수)
대안 — 텍스트 결과를 단순 가중 보강.
"""

from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field


DREAMNET_LABEL = (
    "B6 DreamNet 다중모달 — EEG/HRV + 텍스트 융합 (v4 R&D). "
    "현재: 자가보고 생체 신호 가중 보강."
)


@dataclass
class BiosignalReport:
    """사용자 자가보고 생체 신호 (웨어러블 SDK 도입 전 임시)."""
    sleep_duration_min: int | None = None
    sleep_quality_self: int | None = None  # 1~5
    avg_heart_rate: int | None = None
    awakenings_count: int | None = None
    rem_estimated_min: int | None = None
    device: str | None = None  # 'self_report' | 'apple_watch' | 'galaxy_ring' | 'eeg' (미래)

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


def boost_text_analysis_with_biosignals(
    text_analysis: dict[str, Any],
    biosignals: BiosignalReport | None,
) -> dict[str, Any]:
    """텍스트 분석 결과에 생체 신호 가중치 적용.

    예: 수면 시간 < 5h + 각성 5회+ → 'tst_level' 신뢰도 ↑,
        악몽 빈도 ↑로 추정.
    """
    if not biosignals or not biosignals.to_dict():
        return {
            "agent": "B6",
            "active": False,
            "note": "생체 신호 미입력 — 텍스트 분석만 사용.",
        }

    bs = biosignals.to_dict()
    adjustments: list[dict[str, Any]] = []
    quality_score = 0  # 0~10

    if bs.get("sleep_duration_min") is not None:
        sd = bs["sleep_duration_min"]
        if sd < 300:
            adjustments.append({"signal": "수면 부족", "adjustment": "+stress, +TST 가능성"})
            quality_score -= 2
        elif sd > 540:
            adjustments.append({"signal": "과수면", "adjustment": "+우울 의심"})
            quality_score -= 1
        else:
            quality_score += 2

    if bs.get("awakenings_count") is not None:
        if bs["awakenings_count"] >= 5:
            adjustments.append({"signal": "잦은 각성", "adjustment": "+불안 의심"})
            quality_score -= 2
        elif bs["awakenings_count"] <= 1:
            quality_score += 1

    if bs.get("sleep_quality_self") is not None:
        quality_score += (bs["sleep_quality_self"] - 3)  # 1~5 → -2~+2

    if bs.get("avg_heart_rate") is not None:
        # 수면 중 평균 심박 > 80 → 각성 우세
        if bs["avg_heart_rate"] > 80:
            adjustments.append({"signal": "심박 상승", "adjustment": "+각성/스트레스"})

    return {
        "agent": "B6",
        "active": True,
        "biosignals": bs,
        "adjustments": adjustments,
        "quality_score": max(-10, min(10, quality_score)),
        "boost_note": (
            f"생체 신호 {len(bs)}항목 반영. 품질 점수 {quality_score} (-10~+10)."
        ),
        "future_v4": (
            "Apple Watch·Galaxy Ring·가정용 EEG SDK 안정화 후 자동 융합으로 전환."
        ),
    }


# ─────────────────────────── B6 v4 — integrate_multimodal_dream ───────────────────────────
# ADR-021 본문화 — 멀티모달 통합 결정론 분석.
# 보고서 §4 명세 적용. ADR-006/010/014 정합 (disclaimers 강제).


@dataclass
class MultimodalIntegration:
    """B6 v4 멀티모달 통합 결과 (결정론, ADR-021)."""
    text_features: dict[str, Any] = field(default_factory=dict)
    voice_features: dict[str, Any] | None = None
    sleep_features: dict[str, Any] | None = None
    korean_baseline_delta: dict[str, Any] = field(default_factory=dict)
    available_modalities: list[str] = field(default_factory=list)
    integration_score: float = 0.0  # -10 ~ +10
    disclaimers: list[str] = field(default_factory=list)
    agent: str = "B6_v4"

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "text_features": self.text_features,
            "voice_features": self.voice_features,
            "sleep_features": self.sleep_features,
            "korean_baseline_delta": self.korean_baseline_delta,
            "available_modalities": self.available_modalities,
            "integration_score": self.integration_score,
            "disclaimers": self.disclaimers,
        }


# ADR-006/010/014 정합 — 사용자 출력 면책 강제 (보고서 §6.2 권장 패턴)
DEFAULT_DISCLAIMERS = [
    "본 결과는 자기 보고 분석이며 임상 진단이 아닙니다.",
    "Hall-Van de Castle(1966) 시스템 + 한국 KCI 학술 규준 비교 통계입니다.",
    "꿈 패턴 해석은 다중 요인 영향이며 미래 사건 예언 아닙니다.",
]


def _compute_korean_baseline_delta(
    hvdc_parsed_data: dict[str, Any] | None,
) -> dict[str, Any]:
    """HVDC 파싱 결과 vs 한국 KCI 규준 편차 계산.

    출처: engine/divination/dream_lex/dreambank.py NORMS_KOREAN
         (김성재 외 2004 + 김린 외 2007, 수면정신생리 KCI)
    """
    if not hvdc_parsed_data:
        return {}

    try:
        from engine.divination.dream_lex.dreambank import NORMS_KOREAN
    except ImportError:
        return {}

    norm = NORMS_KOREAN.get("default", {})
    delta: dict[str, Any] = {}

    # HVDC parsed → 한국 규준 편차 (단순 % 차이)
    for key in ["aggression_pct", "negative_emotion_pct", "misfortune_pct"]:
        if key in hvdc_parsed_data and key in norm:
            try:
                observed = float(hvdc_parsed_data[key])
                baseline = float(norm[key])
                diff = observed - baseline
                sign = "+" if diff >= 0 else ""
                delta[key] = f"{sign}{diff:.1f}%"
            except (TypeError, ValueError):
                continue

    return delta


def integrate_multimodal_dream(
    text: str,
    hvdc_parsed_data: dict[str, Any] | None = None,
    voice_audio_features: dict[str, Any] | None = None,
    sleep_stages: dict[str, Any] | None = None,
    user_baseline: dict[str, Any] | None = None,
) -> MultimodalIntegration:
    """B6 v4 멀티모달 꿈 통합 분석 (결정론).

    보고서 §4 명세 본문화 (ADR-021).

    Args:
        text: 꿈 보고 텍스트 (기본 모달리티).
        hvdc_parsed_data: A1·A2 HVDC 파싱 결과 (있을 시).
        voice_audio_features: A11 음성 메타 (emotion_tone·speech_rate, 있을 시).
        sleep_stages: 수면 단계 (REM 비율 등, 있을 시).
        user_baseline: 사용자 개인 베이스라인 (post_traffic, 있을 시).

    Returns:
        MultimodalIntegration — 입력된 모달리티만 통합. disclaimers 강제 포함.

    설계 (ADR-006/010/014 정합):
        · 결정론 (LLM 호출 0)
        · 입력된 모달리티만 통합 (없으면 None 유지)
        · 한국 KCI 규준 vs HVDC 편차 계산 (delta 표시)
        · disclaimers 자동 포함 (의료 단정·예언 절대 금지)
    """
    available: list[str] = []
    if text and isinstance(text, str) and len(text) > 0:
        available.append("text")
    if voice_audio_features:
        available.append("voice")
    if sleep_stages:
        available.append("sleep")

    # HVDC parsed가 있으면 한국 규준 편차 계산
    delta = _compute_korean_baseline_delta(hvdc_parsed_data)

    # 점수 통합 (단순 합산, -10 ~ +10)
    score = 0.0
    if hvdc_parsed_data:
        score += 1.0
    if voice_audio_features:
        score += 1.0
    if sleep_stages:
        score += 1.0
    if user_baseline:
        score += 1.0

    text_features = {"text_length": len(text) if text else 0}
    if hvdc_parsed_data:
        text_features["hvdc_parsed"] = True

    return MultimodalIntegration(
        text_features=text_features,
        voice_features=voice_audio_features,
        sleep_features=sleep_stages,
        korean_baseline_delta=delta,
        available_modalities=available,
        integration_score=max(-10.0, min(10.0, score)),
        disclaimers=list(DEFAULT_DISCLAIMERS),
        agent="B6_v4",
    )


__all__ = [
    "DREAMNET_LABEL",
    "BiosignalReport",
    "MultimodalIntegration",
    "DEFAULT_DISCLAIMERS",
    "integrate_multimodal_dream",
    "boost_text_analysis_with_biosignals",
]
