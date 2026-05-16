"""Schredl Dream Diary Standard — 꿈 일기 표준 양식.

출처: Schredl (2007) International Journal of Dream Research 1(1)
"Dream recall frequency: a useful estimate but imprecise measure"

표준 입력 항목:
  - recall_quality: 회상 명료도 (1~5)
  - vividness: 생생함 (1~5)
  - valence: 정서가 (-3~+3)
  - lucidity: 자각도 (LuCiD 6단계, 0~5)
  - narrative_text: 자유 서술
  - characters/settings/activities: HvDC 호환 태그

본 모듈은 검증·계산 함수만 제공. 저장은 dream.py가 캐시 단계에서 처리.
"""

from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field


SCHREDL_LABEL = (
    "Schredl Dream Diary 표준 — 회상률·정서가·생생함·자각도를 표준화한 학술 호환 양식."
)


# Lucidity 6단계 (LuCiD scale)
LUCIDITY_SCALE = {
    0: "비자각몽 (꿈인 줄 모름)",
    1: "막연한 자각감",
    2: "꿈임을 인지 — 통제는 없음",
    3: "꿈임을 인지 + 일부 통제",
    4: "꿈임을 인지 + 강한 통제",
    5: "완전 자각몽 (의도적 시나리오 변경)",
}


@dataclass
class DreamDiaryEntry:
    """Schredl 표준 + HvDC 호환 꿈 일기 항목."""
    narrative_text: str

    # 핵심 척도 (필수)
    recall_quality: int = 3  # 1~5
    vividness: int = 3  # 1~5
    valence: int = 0  # -3~+3
    lucidity: int = 0  # 0~5

    # 시간·수면 정보 (선택)
    created_at_iso: str | None = None  # 기록 시각
    wake_time_iso: str | None = None  # 깨어난 시각
    sleep_duration_min: int | None = None  # 0~1440

    # HvDC 호환 태그 (선택)
    characters: list[dict[str, Any]] = field(default_factory=list)
    settings: list[str] = field(default_factory=list)
    activities: list[str] = field(default_factory=list)
    emotions_hvdc: dict[str, int] = field(default_factory=dict)  # anger/apprehension/happiness/sadness/confusion

    # 사용자 피드백
    user_helpful: bool | None = None
    user_rating: int | None = None  # 1~5

    def validate(self) -> list[str]:
        """검증 — 위반 메시지 리스트 반환."""
        errors: list[str] = []
        if not self.narrative_text or not self.narrative_text.strip():
            errors.append("narrative_text는 비어 있을 수 없음")
        if not 1 <= self.recall_quality <= 5:
            errors.append(f"recall_quality는 1~5 (받음: {self.recall_quality})")
        if not 1 <= self.vividness <= 5:
            errors.append(f"vividness는 1~5 (받음: {self.vividness})")
        if not -3 <= self.valence <= 3:
            errors.append(f"valence는 -3~+3 (받음: {self.valence})")
        if not 0 <= self.lucidity <= 5:
            errors.append(f"lucidity는 0~5 (받음: {self.lucidity})")
        if self.sleep_duration_min is not None and not 0 <= self.sleep_duration_min <= 1440:
            errors.append(f"sleep_duration_min은 0~1440 (받음: {self.sleep_duration_min})")
        if self.user_rating is not None and not 1 <= self.user_rating <= 5:
            errors.append(f"user_rating은 1~5 (받음: {self.user_rating})")
        if len(self.narrative_text) > 4000:
            errors.append(f"narrative_text는 최대 4000자 (받음: {len(self.narrative_text)})")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "narrative_text": self.narrative_text,
            "recall_quality": self.recall_quality,
            "vividness": self.vividness,
            "valence": self.valence,
            "lucidity": self.lucidity,
            "lucidity_label": LUCIDITY_SCALE.get(self.lucidity),
            "created_at_iso": self.created_at_iso,
            "wake_time_iso": self.wake_time_iso,
            "sleep_duration_min": self.sleep_duration_min,
            "characters": self.characters,
            "settings": self.settings,
            "activities": self.activities,
            "emotions_hvdc": self.emotions_hvdc,
            "user_helpful": self.user_helpful,
            "user_rating": self.user_rating,
        }


def build_diary_entry(data: dict[str, Any]) -> DreamDiaryEntry:
    """dict로부터 안전하게 DreamDiaryEntry 생성."""
    return DreamDiaryEntry(
        narrative_text=str(data.get("narrative_text", "")),
        recall_quality=int(data.get("recall_quality", 3)),
        vividness=int(data.get("vividness", 3)),
        valence=int(data.get("valence", 0)),
        lucidity=int(data.get("lucidity", 0)),
        created_at_iso=data.get("created_at_iso"),
        wake_time_iso=data.get("wake_time_iso"),
        sleep_duration_min=data.get("sleep_duration_min"),
        characters=data.get("characters") or [],
        settings=data.get("settings") or [],
        activities=data.get("activities") or [],
        emotions_hvdc=data.get("emotions_hvdc") or {},
        user_helpful=data.get("user_helpful"),
        user_rating=data.get("user_rating"),
    )


def compute_recall_rate(entries: list[DreamDiaryEntry], days: int = 7) -> dict[str, Any]:
    """최근 N일 회상률 — 기록 일수 / N."""
    if days <= 0:
        return {"recall_rate": 0.0, "entries_logged": 0, "days_observed": 0}
    n_entries = len(entries)
    n_dreams_recalled = sum(1 for e in entries if e.recall_quality >= 2)
    return {
        "recall_rate": round(n_dreams_recalled / days, 2),
        "entries_logged": n_entries,
        "days_observed": days,
        "interpretive_note": (
            f"최근 {days}일 회상률 {round(n_dreams_recalled / days * 100, 0):.0f}%. "
            "Schredl 규준 일반인 평균 ≈ 50% (주 3~4회)."
        ),
    }


def compute_mood_curve(entries: list[DreamDiaryEntry]) -> dict[str, Any]:
    """정서가 곡선 — Cartwright 7일 모드 추적."""
    if not entries:
        return {"mean_valence": 0.0, "trend": "데이터 없음", "samples": 0}
    valences = [e.valence for e in entries]
    mean = round(sum(valences) / len(valences), 2)
    # 단순 추세: 후반/전반 평균 비교
    half = len(valences) // 2
    if half > 0:
        first_half = sum(valences[:half]) / half
        second_half = sum(valences[half:]) / (len(valences) - half)
        diff = second_half - first_half
        if diff > 0.5:
            trend = "정서 회복 추세"
        elif diff < -0.5:
            trend = "정서 악화 추세"
        else:
            trend = "안정"
    else:
        trend = "데이터 부족"
    return {
        "mean_valence": mean,
        "trend": trend,
        "samples": len(valences),
        "interpretive_note": (
            f"평균 정서가 {mean:+.1f} (-3~+3 척도). 추세: {trend}. "
            "Cartwright 가설상 REM 꿈은 야간 정서 처리·아침 기분 조절에 관여."
        ),
    }


__all__ = [
    "SCHREDL_LABEL",
    "LUCIDITY_SCALE",
    "DreamDiaryEntry",
    "build_diary_entry",
    "compute_recall_rate",
    "compute_mood_curve",
]
