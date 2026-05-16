"""Cartwright 정서 조절 가설 — REM 꿈의 야간 정서 처리 기능.

출처:
  - Cartwright (1991) "Dreams that work: The relation of dream incorporation
    to adaptation to stressful events", Dreaming 1(1)
  - Cartwright (2010) The Twenty-four Hour Mind

핵심:
  - REM 꿈은 깨어 있는 동안의 부정 정서를 야간에 처리·재구성해 아침 기분 조절
  - 이혼·우울 종단연구에서 입증
  - 부정 정서 → REM에서 재맥락화 → 다음날 회복

본 모듈의 역할:
  - 7일 이상의 일기 entries로 mood-dream 곡선 그리기
  - 부정 정서 사용자에게 'REM이 처리 중'이라는 정상화 메시지
"""

from __future__ import annotations
from typing import Any


CARTWRIGHT_LABEL = (
    "Cartwright 정서 조절 — REM 꿈은 부정 정서를 야간에 처리·재구성해 "
    "아침 기분을 조절. 이혼·우울 종단연구로 입증."
)


def analyze_mood_dream_curve(
    daily_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    """7일 이상의 일기 entries로 mood-dream 곡선 분석.

    Args:
        daily_entries: 각 항목은 {date_iso, valence, vividness, recall_quality, narrative_text}

    Returns:
        7일 추세 + Cartwright 해석
    """
    if not daily_entries:
        return {
            "days_observed": 0,
            "valences": [],
            "trend": "데이터 없음",
            "interpretive_note": "Cartwright 분석에는 최소 5일 이상의 일기가 필요합니다.",
        }

    valences = [int(e.get("valence", 0)) for e in daily_entries]
    n = len(valences)

    # 분할: 전반 vs 후반
    half = n // 2
    if half > 0:
        first_mean = sum(valences[:half]) / half
        second_mean = sum(valences[half:]) / (n - half)
        delta = round(second_mean - first_mean, 2)
    else:
        first_mean, second_mean, delta = 0.0, 0.0, 0.0

    overall_mean = round(sum(valences) / n, 2)

    # Cartwright 패턴 분류
    if n < 5:
        pattern = "데이터 부족"
        note = f"{n}일치 데이터 — 5일 이상 누적 후 추세를 본격 분석합니다."
    elif overall_mean < -1.0 and delta > 0.5:
        pattern = "회복 진행"
        note = (
            "전반적으로 부정적이나 후반부 호전 — Cartwright 모델상 "
            "REM이 부정 정서를 야간에 잘 처리하고 있다는 신호."
        )
    elif overall_mean < -1.0 and delta <= 0.5:
        pattern = "정체된 부정"
        note = (
            "지속된 부정 정서 — REM 정서 처리가 막혔을 가능성. "
            "수면 질 점검과 함께 지속될 경우 전문가 상담을 권합니다."
        )
    elif overall_mean >= 0 and delta < -0.5:
        pattern = "악화 추세"
        note = "긍정 → 부정으로 전환 — 최근 스트레스 사건의 영향 가능성."
    elif abs(delta) <= 0.5:
        pattern = "안정"
        note = "정서 추세 안정 — 큰 변동 없음."
    else:
        pattern = "변동"
        note = "정서 변동이 있으나 명확한 추세는 없음."

    # 부정 정서 비율
    negative_count = sum(1 for v in valences if v < 0)
    negative_pct = round(negative_count / n * 100, 1)

    return {
        "days_observed": n,
        "valences": valences,
        "overall_mean": overall_mean,
        "first_half_mean": round(first_mean, 2),
        "second_half_mean": round(second_mean, 2),
        "delta": delta,
        "negative_day_pct": negative_pct,
        "pattern": pattern,
        "interpretive_note": note,
        "cartwright_principle": (
            "REM 꿈은 부정 정서의 야간 재맥락화 기능을 합니다. "
            "악몽도 정서 처리의 일부일 수 있으며, 회복 곡선(첫 주 악화 → 둘째 주 호전)이 정상 패턴입니다."
        ),
    }


def detect_emotion_processing_signal(narrative_text: str) -> dict[str, Any]:
    """단일 꿈 텍스트에서 정서 처리 신호 탐지 — Cartwright 보조."""
    t = narrative_text or ""

    # 정서 처리 완료 신호 (긍정 해결)
    resolution_markers = [
        "결국 해결", "마침내", "끝나서", "안도", "한숨 돌렸", "구조됐",
        "도움 받았", "이겨냈", "벗어났", "평화로워",
    ]
    # 미해결 정서 (반복·고착)
    unresolved_markers = [
        "다시", "또", "반복", "여전히", "계속", "벗어나지 못",
        "도망쳐도", "막다른", "출구가 없",
    ]

    res_hits = [m for m in resolution_markers if m in t]
    unres_hits = [m for m in unresolved_markers if m in t]

    if res_hits and not unres_hits:
        signal = "정서 처리 완료"
        note = "꿈 안에서 해결·안도가 나타남 — REM 정서 조절이 잘 작동."
    elif unres_hits and not res_hits:
        signal = "정서 미해결"
        note = "꿈 안에 반복·고착 모티프 — 같은 정서가 계속 처리 중이거나 막혔을 가능성."
    elif res_hits and unres_hits:
        signal = "정서 처리 중"
        note = "해결과 미해결이 공존 — 능동적 처리 진행 단계."
    else:
        signal = "정서 신호 미감지"
        note = "정서 처리 마커가 충분치 않음."

    return {
        "signal": signal,
        "resolution_markers": res_hits,
        "unresolved_markers": unres_hits,
        "interpretive_note": note,
    }


__all__ = [
    "CARTWRIGHT_LABEL",
    "analyze_mood_dream_curve",
    "detect_emotion_processing_signal",
]
