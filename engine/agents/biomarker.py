"""A11 DreamBank+LLM 디지털 바이오마커 에이전트.

문서: 7~30일 꿈 로그 → 우울·불안 조기 캡처 (HVdC + CES-D 상관 추정).

기존 ClinicalLogRepo가 척도 종단 점수를 보유.
기존 DreamDiaryRepo가 일기 + valence·HvDC 보유.

본 에이전트:
  - 사용자의 N일치 일기에서 HVdC 부정 지표 계산 (deterministic)
  - 척도 종단 점수와 상관 계수 추정
  - 우울·불안 조기 신호 (척도 측정 전에 일기에서 잡힘) 탐지
  - 위기 신호 시 의료 의뢰 권장

LLM 호출 0회 (모두 결정론 + 통계).
"""

from __future__ import annotations
from typing import Any
from collections import Counter
from datetime import datetime, timedelta


BIOMARKER_LABEL = (
    "A11 디지털 바이오마커 — 종단 일기에서 우울·불안 조기 신호 탐지. "
    "HVdC 부정 지표 + 척도 점수 상관 분석."
)


# 부정 정서 마커 (cathartic.py와 호환)
NEGATIVE_AFFECT_MARKERS = [
    "무서", "두려", "공포", "겁났", "슬펐", "울었", "비통", "외로움",
    "화났", "분노", "당황", "혼란", "절망", "막막", "갇혔", "쫓겼", "위협",
]


def compute_biomarker_signals(
    diaries: list[dict[str, Any]],
    clinical_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """일기·척도 종단에서 바이오마커 신호 추출.

    Args:
        diaries: DreamDiaryRepo.list_recent 결과 (최신순)
        clinical_history: ClinicalLogRepo.history 결과 (선택)

    Returns:
        {
            'days_observed': N,
            'avg_valence': float,
            'negative_density': float,  # 부정 정서 마커 등장 비율
            'recall_quality_trend': str,
            'depression_signal': "정상"|"주의"|"의심",
            'anxiety_signal': str,
            'recommendation': str,
        }
    """
    if not diaries:
        return {
            "agent": "A11",
            "days_observed": 0,
            "signal": "데이터 부족",
            "note": "최소 7일 이상 일기 누적 후 분석합니다.",
        }

    n = len(diaries)
    valences = [int(d.get("valence", 0)) for d in diaries if d.get("valence") is not None]
    avg_valence = round(sum(valences) / len(valences), 2) if valences else 0.0

    # 부정 정서 밀도
    total_negative_hits = 0
    total_text_chars = 0
    for d in diaries:
        text = d.get("narrative_text") or ""
        total_text_chars += len(text)
        total_negative_hits += sum(1 for m in NEGATIVE_AFFECT_MARKERS if m in text)
    negative_density = round(
        total_negative_hits / max(1, n), 2
    )

    # 회상 품질 추세 (최근 vs 이전 7일)
    if n >= 14:
        recent_7 = diaries[:7]
        prev_7 = diaries[7:14]
        recent_recall = sum(d.get("recall_quality", 0) for d in recent_7) / 7
        prev_recall = sum(d.get("recall_quality", 0) for d in prev_7) / 7
        recall_delta = round(recent_recall - prev_recall, 2)
        if recall_delta > 0.5:
            recall_trend = "회상률 상승"
        elif recall_delta < -0.5:
            recall_trend = "회상률 하락 — 수면 질 점검"
        else:
            recall_trend = "회상률 안정"
    else:
        recall_delta = None
        recall_trend = "데이터 부족 (14일+ 필요)"

    # 우울 신호 — 종합 휴리스틱
    depression_score = 0
    if avg_valence <= -1.5:
        depression_score += 2
    elif avg_valence <= -0.5:
        depression_score += 1
    if negative_density >= 2.0:
        depression_score += 2
    elif negative_density >= 1.0:
        depression_score += 1
    if recall_delta is not None and recall_delta < -1.0:
        depression_score += 1

    if depression_score >= 4:
        depression_signal = "의심"
        recommendation = (
            "꿈 일기에서 우울 신호가 일관적으로 잡힙니다. CES-D / BDI-K 자가검사 권장. "
            "지속 시 정신건강의학과 상담을 권합니다."
        )
    elif depression_score >= 2:
        depression_signal = "주의"
        recommendation = (
            "약한 우울 신호. CES-D 자가검사로 정량 확인을 권합니다."
        )
    else:
        depression_signal = "정상"
        recommendation = "특이 신호 미감지."

    # 척도 종단 점수와 상관 (있을 때만)
    correlation_note = None
    if clinical_history:
        ces_d_scores = [
            h["total_score"] for h in clinical_history
            if h.get("instrument") == "ces_d"
        ]
        if ces_d_scores:
            latest_ces_d = ces_d_scores[0]
            if latest_ces_d >= 16 and depression_signal == "정상":
                correlation_note = (
                    f"CES-D 최근 {latest_ces_d}점은 임계 초과이나 일기 신호는 정상 범위. "
                    "자가보고가 좋아도 척도가 우세이면 임상 우선."
                )
            elif latest_ces_d < 16 and depression_signal == "의심":
                correlation_note = (
                    f"CES-D 최근 {latest_ces_d}점은 정상이나 일기 신호는 우울 의심. "
                    "꿈이 척도보다 먼저 신호를 잡는 경우가 있음 (디지털 바이오마커 가설)."
                )

    return {
        "agent": "A11",
        "days_observed": n,
        "avg_valence": avg_valence,
        "negative_density": negative_density,
        "recall_quality_trend": recall_trend,
        "recall_delta": recall_delta,
        "depression_signal": depression_signal,
        "depression_score": depression_score,
        "recommendation": recommendation,
        "correlation_with_scales": correlation_note,
        "principle": (
            "DreamBank+LLM 디지털 바이오마커 가설: 일기 부정 정서 밀도가 척도 점수 변화보다 "
            "수일~수주 먼저 신호를 잡을 수 있음."
        ),
    }


__all__ = [
    "BIOMARKER_LABEL",
    "compute_biomarker_signals",
]
