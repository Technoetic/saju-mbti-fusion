"""Stickgold & Walker 수면-기억 통합 가설.

출처:
  - Stickgold (2005) "Sleep-dependent memory consolidation", Nature 437
  - Walker (2017) Why We Sleep

핵심:
  - NREM: 사실(declarative) 통합
  - REM: 정서·절차·창의적 연결 통합
  - 학습 단편이 27% 꿈에 재등장 (Stickgold 2003)
  - 학습 후 72시간 이내 꿈에 가장 잘 나타남 (dream incorporation lag effect)

본 모듈의 역할:
  - 사용자가 입력한 최근 학습·작업과 꿈 내용 간 매칭
  - 72h window 내 학습 단편이 등장하는지 점수화
"""

from __future__ import annotations
from typing import Any


STICKGOLD_LABEL = (
    "Stickgold & Walker — 수면이 기억을 통합 (NREM=사실, REM=정서·창의). "
    "학습 단편의 27%가 꿈에 재등장, 학습 후 72h 이내 빈출 (dream lag)."
)


# 학습 카테고리 키워드
LEARNING_DOMAINS = {
    "절차_운동": [
        "운전", "악기", "기타", "피아노", "춤", "수영", "자전거",
        "코딩", "타이핑", "조립", "요리",
    ],
    "선언_사실": [
        "공부", "암기", "외웠", "시험", "강의", "수업", "교재",
        "역사", "수학", "영어", "단어", "공식",
    ],
    "정서_사회": [
        "다툼", "화해", "이별", "고백", "면접", "발표", "프레젠테이션",
        "회의", "협상", "데이트", "상담",
    ],
    "창의_문제해결": [
        "디자인", "기획", "아이디어", "발상", "그림", "글쓰기",
        "작곡", "조사", "분석", "전략",
    ],
}


def detect_memory_consolidation(
    dream_text: str,
    recent_activities: list[str] | None = None,
    activity_age_hours: list[int] | None = None,
) -> dict[str, Any]:
    """꿈과 최근 활동(학습·사건) 간 매칭.

    Args:
        dream_text: 꿈 본문
        recent_activities: 최근 활동 텍스트 리스트 (예: ['수학 공부', '면접 준비'])
        activity_age_hours: 각 활동의 경과 시간(시간 단위) — 72 이내가 dream lag window

    Returns:
        도메인 매칭 + 72h window 신호
    """
    t = dream_text or ""

    domain_hits: dict[str, list[str]] = {}
    for domain, kws in LEARNING_DOMAINS.items():
        hits = [k for k in kws if k in t]
        if hits:
            domain_hits[domain] = hits

    # 사용자 입력 활동과 직접 매칭
    direct_matches: list[dict[str, Any]] = []
    if recent_activities:
        for i, activity in enumerate(recent_activities):
            age = activity_age_hours[i] if activity_age_hours and i < len(activity_age_hours) else None
            # 활동 문구의 명사 단편을 꿈에서 검색
            tokens = [w.strip() for w in activity.split() if len(w.strip()) >= 2]
            matched_tokens = [tok for tok in tokens if tok in t]
            if matched_tokens:
                in_window = (age is None) or (age <= 72)
                direct_matches.append({
                    "activity": activity,
                    "age_hours": age,
                    "matched_tokens": matched_tokens,
                    "in_72h_window": in_window,
                    "dream_lag_effect": in_window and (age is not None),
                })

    consolidation_signal = bool(domain_hits) or bool(direct_matches)
    in_window_count = sum(1 for m in direct_matches if m["in_72h_window"])

    return {
        "domain_hits": domain_hits,
        "direct_matches": direct_matches,
        "in_72h_window_count": in_window_count,
        "consolidation_signal": consolidation_signal,
        "interpretive_note": _build_note(domain_hits, direct_matches, in_window_count),
        "stickgold_principle": (
            "Stickgold 27% 재등장률 — 학습 후 72h 이내에 꿈으로 통합되는 비율이 가장 높습니다. "
            "NREM은 사실, REM은 정서·창의를 통합합니다."
        ),
    }


def _build_note(
    domain_hits: dict[str, list[str]],
    direct_matches: list[dict[str, Any]],
    in_window: int,
) -> str:
    if not domain_hits and not direct_matches:
        return "최근 학습·작업과 꿈의 직접 연결 신호 미감지."

    parts = []
    if direct_matches:
        parts.append(
            f"입력하신 최근 활동 {len(direct_matches)}건이 꿈에 직접 등장 "
            f"(72h 이내 lag effect: {in_window}건)."
        )
    if domain_hits:
        parts.append(
            f"학습 도메인 시그널: {', '.join(domain_hits.keys())}."
        )
    parts.append(
        "Stickgold 가설상 이는 수면 중 기억 통합이 능동적으로 진행되고 있다는 신호입니다."
    )
    return " ".join(parts)


__all__ = [
    "STICKGOLD_LABEL",
    "LEARNING_DOMAINS",
    "detect_memory_consolidation",
]
