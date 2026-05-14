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


__all__ = [
    "DREAMNET_LABEL",
    "BiosignalReport",
    "boost_text_analysis_with_biosignals",
]
