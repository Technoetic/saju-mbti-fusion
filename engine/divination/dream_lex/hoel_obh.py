"""Hoel 과적합 뇌 가설 (Overfitted Brain Hypothesis).

출처: Hoel (2021) "The Overfitted Brain: Dreams evolved to assist
       generalization", Patterns / arXiv:2007.09560

핵심:
  - 딥러닝 '과적합(overfitting)' 문제의 신경학적 적용
  - 뇌는 반복적 일상에 과적합되어 일반화(generalization) 능력이 떨어짐
  - 꿈 = 뇌가 스스로에게 주입하는 생물학적 노이즈
  - 기괴함(bizarreness)은 오류가 아니라 정규화(regularization) 기능

기존 #7 hobson.py 기괴성 측정의 신경학적 재해석:
  - 홉슨: 기괴성 = 신경 잡음 (의미 없음)
  - Hoel: 기괴성 = 과적합 방지 노이즈 (적응적·기능적)
  → 본 모듈은 일상 반복도(routine repetitiveness)와 꿈 기괴성을 대조해
    '과적합 → 정규화 시도' 신호를 정량화한다.
"""

from __future__ import annotations
from typing import Any


HOEL_OBH_LABEL = (
    "Hoel 과적합 뇌 가설 — 꿈은 뇌가 일상 과적합을 해소하기 위해 주입하는 "
    "생물학적 노이즈. 기괴함은 정규화의 결과 (Hoel 2021)."
)


# 일상 반복성 지표 — '깨어 있는 삶의 과적합' 신호
ROUTINE_REPETITION_MARKERS = [
    "매일", "반복", "똑같", "지루", "단조", "변화 없",
    "출근", "퇴근", "야근", "회의", "수업", "강의",
    "매번", "항상", "늘", "또 그", "같은 곳", "같은 사람",
    "루틴", "일과", "정해진",
]

# 정규화(노이즈 주입) 신호 — 일상 파괴적 꿈 모티프
NORMALIZATION_MARKERS = [
    # 시공간 위반
    "갑자기 다른 곳", "장소가 바뀜", "시간이 멈춤", "시간이 거꾸로",
    "끝없이", "무한히",
    # 정체성 변형
    "내가 동물", "내가 다른 사람", "얼굴이 바뀜", "성별이 바뀜",
    "어른인데 아이", "아이인데 어른",
    # 물리 위반
    "벽 통과", "공중 부양", "중력 무시", "물 위를 걸",
    "사물이 살아", "동물이 말",
    # 비일상적 환경
    "외계", "다른 행성", "환상의 세계", "동화 속",
]


def measure_overfitting_signal(
    text: str,
    *,
    daily_routine_text: str | None = None,
) -> dict[str, Any]:
    """과적합·정규화 신호 측정.

    Args:
        text: 꿈 본문
        daily_routine_text: (선택) 사용자가 보고한 최근 일상 (반복도 측정)

    Returns:
        overfitting_score: 일상 반복도 (꿈에 등장한 routine 마커 수)
        normalization_score: 노이즈 주입도 (일상 파괴 모티프 수)
        net_signal: 정규화가 활발한지 / 과적합이 누적 중인지
    """
    t = text or ""
    routine_in_dream = [m for m in ROUTINE_REPETITION_MARKERS if m in t]
    normalization = [m for m in NORMALIZATION_MARKERS if m in t]

    # daily_routine_text 분석 — 일상의 단조로움 정도
    routine_density = 0
    if daily_routine_text:
        rt = daily_routine_text
        routine_density = sum(1 for m in ROUTINE_REPETITION_MARKERS if m in rt)

    overfitting_score = len(routine_in_dream) + routine_density
    normalization_score = len(normalization)

    # 해석
    if normalization_score >= 4 and overfitting_score >= 3:
        verdict = "활발한 정규화"
        note = (
            "일상 과적합 신호 + 강한 정규화 시도 — 뇌가 깨어 있는 단조로움을 "
            "해소하기 위해 적극적으로 노이즈를 주입 중. 창의적 발산 가능성."
        )
    elif normalization_score >= 4:
        verdict = "노이즈 주입 활발"
        note = (
            "꿈에 일상 파괴적 모티프가 다수. Hoel 관점에서는 일반화 능력 강화 신호. "
            "기괴함을 두려워하지 말고 '정상 작동 중'으로 받아들이세요."
        )
    elif overfitting_score >= 4 and normalization_score < 2:
        verdict = "과적합 누적 의심"
        note = (
            "일상 반복도가 꿈에까지 침투, 정규화 신호 부족. "
            "환경 변화·새로운 자극이 필요한 시기일 수 있습니다."
        )
    elif normalization_score >= 2:
        verdict = "보통 정규화"
        note = "일정 수준의 일반화 기능 작동 중."
    else:
        verdict = "신호 미감지"
        note = "이 꿈에서는 OBH 관점의 신호가 충분치 않습니다."

    return {
        "overfitting_score": overfitting_score,
        "normalization_score": normalization_score,
        "routine_markers_in_dream": routine_in_dream,
        "normalization_markers": normalization,
        "verdict": verdict,
        "interpretive_note": note,
        "hoel_principle": (
            "딥러닝 모델이 훈련 데이터에 과적합되면 일반화에 실패. 뇌도 같은 위험을 갖고, "
            "꿈은 이를 막기 위한 정기적 노이즈 주입 (Simulated Annealing)."
        ),
    }


__all__ = [
    "HOEL_OBH_LABEL",
    "ROUTINE_REPETITION_MARKERS",
    "NORMALIZATION_MARKERS",
    "measure_overfitting_signal",
]
