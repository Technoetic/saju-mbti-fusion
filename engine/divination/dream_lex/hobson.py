"""J.A. Hobson 활성-합성 가설(Activation-Synthesis Hypothesis).

REM 수면 중 뇌간(특히 PGO파)의 무작위 활성을 전뇌가 사후적으로
이야기로 '합성'한다는 신경생리학적 관점.

이 모듈의 역할: 꿈의 'bizarreness'(기괴성) 수준을 측정해
- 일부 장면이 단순한 신경 잡음의 산물일 가능성을 정량화
- 모든 요소에 동등한 의미 부여를 막는 critic 신호 제공
"""

from __future__ import annotations
from typing import Any


HOBSON_LABEL = (
    "활성-합성 — REM 중 뇌간 활성을 전뇌가 사후 합성한 산물. "
    "기괴성이 높을수록 신경생리적 잡음의 비중이 큼."
)


# 기괴성(bizarreness) 마커 — 물리·논리 위반, 비연속성
BIZARRE_MARKERS = [
    # 형태 변환
    "변신", "변형", "녹아내림", "녹아 내림", "녹아내리", "녹아 내리",
    "몸이 늘어남", "몸이 줄어듦", "거대해짐", "작아짐",
    "동물이 사람", "사람이 동물", "사물이 살아 움직",

    # 공간 위반
    "벽 통과", "유리 통과", "공중 부양", "중력 무시", "거꾸로 걸",
    "동시에 두 곳", "장소가 바뀜", "끝없는 복도", "끝없이 이어",

    # 시간 위반
    "시간이 멈춤", "시간이 거꾸로", "갑자기 어른", "갑자기 아이",
    "어제와 오늘", "과거와 현재",

    # 인물 위반
    "여러 사람이 한 사람", "얼굴이 계속 바뀜", "이름 다른 같은 사람",
    "죽은 사람이 살아", "모르는 사람이 가족",

    # 감각 이상
    "소리 안 나옴", "발음 안 됨", "달려도 제자리", "다리가 안 움직",
    "팔이 안 들림", "안 보이는데 보이는",

    # 환상 생물
    "유니콘", "켄타우로스", "그리핀", "용", "이무기", "도깨비",
]


def measure_bizarreness(text: str) -> dict[str, Any]:
    """기괴성 점수 측정 — 0~10 스케일."""
    t = text or ""
    hits = [m for m in BIZARRE_MARKERS if m in t]
    score = min(len(hits), 10)

    if score == 0:
        level = "낮음"
        note = "물리·논리 위반 거의 없음 — 정상 서사형 꿈. 상징 해석 무게 ↑."
    elif score <= 3:
        level = "중간"
        note = "일부 기괴성 — 핵심 모티프 위주로 해석, 사소한 위반은 잡음 가능."
    elif score <= 6:
        level = "높음"
        note = "기괴성 강함 — 일부 장면은 신경생리적 합성의 산물일 가능성."
    else:
        level = "매우 높음"
        note = "강한 활성-합성 신호 — 강한 정서 모티프만 의미 부여, 나머지는 잡음 가능성."

    return {
        "bizarreness_score": score,
        "bizarreness_level": level,
        "markers_found": hits,
        "interpretive_note": note,
    }


# Critic 규칙
CRITIC_RULE_BIZARRENESS = (
    "기괴성 점수가 6 이상일 때: 모든 디테일을 동등 의미로 해석하지 말 것. "
    "감정적으로 강하거나 반복되는 핵심 모티프만 상징적으로 풀고, "
    "사소한 물리·논리 위반은 신경생리적 합성 산물로 부수 처리."
)


__all__ = [
    "HOBSON_LABEL",
    "BIZARRE_MARKERS",
    "measure_bizarreness",
    "CRITIC_RULE_BIZARRENESS",
]
