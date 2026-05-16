"""B4 양가 해석 가중치 학습기 — 사용자 선택 피드백 기록·반영.

문서: 사용자 선택 피드백으로 #4 vs #12 카드 가중치 개인화.

구현:
  - 단순 누적 학습: 사용자가 "이 카드가 더 맞다"를 클릭할 때마다 카운트 +1
  - SQLite의 dream_diary.analysis_summary_json 활용 (스키마 변경 없음)
  - 또는 in-memory dict (재시작 시 사라짐 — MVP 적합)
  - 다음 해석에서 해당 사용자의 source(아르테미도로스/주공해몽/한국민속) 가중치 조정

MVP는 in-memory dict + DB 저장 옵션.
"""

from __future__ import annotations
from typing import Any
from collections import defaultdict
import json


WEIGHT_LEARNER_LABEL = (
    "B4 양가 가중치 학습기 — 사용자 피드백으로 사전 소스별 가중치 개인화."
)


# in-memory 가중치 저장소 (서버 인스턴스당)
# {user_id: {source: count}}
_user_source_weights: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))


# 기본 가중치 (사전 소스별)
DEFAULT_SOURCE_WEIGHTS = {
    "artemidorus": 0.6,
    "zhougong": 0.7,
    "korean_folk": 0.8,
    "ibn_sirin": 0.5,
}


def record_feedback(
    user_id: str,
    chosen_source: str,
    polarity: str,
    keyword: str | None = None,
) -> dict[str, Any]:
    """사용자가 양가 카드 중 하나를 선택한 피드백 기록.

    Args:
        user_id: 익명 ID
        chosen_source: 'artemidorus' | 'zhougong' | 'korean_folk' | ...
        polarity: '길' | '흉' | '양가'
        keyword: 어떤 표상에 대한 선택인지 (선택)
    """
    if not user_id or not chosen_source:
        return {"recorded": False, "reason": "user_id 또는 source 누락"}

    # 학습 룰: 선택된 source +1.0, 같은 polarity 패턴이 반복되면 가중치 ↑
    _user_source_weights[user_id][chosen_source] += 1.0
    key_polarity = f"polarity_{polarity}"
    _user_source_weights[user_id][key_polarity] += 0.5

    if keyword:
        # 키워드별 선호도도 기록 (메모리만)
        _user_source_weights[user_id][f"kw:{keyword}"] += 1.0

    return {
        "recorded": True,
        "user_id": user_id,
        "current_weights": dict(_user_source_weights[user_id]),
    }


def get_personalized_weights(user_id: str | None) -> dict[str, float]:
    """사용자별 개인화 가중치 — A3 양가 카드 에이전트가 호출."""
    base = dict(DEFAULT_SOURCE_WEIGHTS)
    if not user_id or user_id not in _user_source_weights:
        return base

    user_history = _user_source_weights[user_id]
    total_feedback = sum(
        v for k, v in user_history.items()
        if not k.startswith("polarity_") and not k.startswith("kw:")
    )

    if total_feedback < 3:
        # 충분치 않은 피드백 → 기본 가중치
        return base

    # 학습된 가중치 — 사용자 선호 source에 +0.2~0.5
    for source, default_w in DEFAULT_SOURCE_WEIGHTS.items():
        user_count = user_history.get(source, 0.0)
        if user_count > 0:
            preference_ratio = user_count / max(1.0, total_feedback)
            # 최대 +0.5 보너스
            base[source] = min(1.0, default_w + preference_ratio * 0.5)

    return base


def get_user_feedback_summary(user_id: str) -> dict[str, Any]:
    """사용자의 피드백 누적 요약 (디버깅·UI 표시용)."""
    if user_id not in _user_source_weights:
        return {"user_id": user_id, "feedback_count": 0, "weights": DEFAULT_SOURCE_WEIGHTS}

    history = dict(_user_source_weights[user_id])
    total = sum(
        v for k, v in history.items()
        if not k.startswith("polarity_") and not k.startswith("kw:")
    )
    return {
        "user_id": user_id,
        "feedback_count": int(total),
        "raw_history": history,
        "personalized_weights": get_personalized_weights(user_id),
    }


def reset_user_feedback(user_id: str) -> dict[str, Any]:
    """사용자 피드백 초기화 (개인정보보호법 삭제권 보조)."""
    if user_id in _user_source_weights:
        del _user_source_weights[user_id]
    return {"reset": True, "user_id": user_id}


__all__ = [
    "WEIGHT_LEARNER_LABEL",
    "DEFAULT_SOURCE_WEIGHTS",
    "record_feedback",
    "get_personalized_weights",
    "get_user_feedback_summary",
    "reset_user_feedback",
]
