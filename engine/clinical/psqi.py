"""PSQI (Pittsburgh Sleep Quality Index) — 수면 품질 지수.

출처: Buysse et al. (1989) Psychiatry Research 28(2)
한국판: 손창호 외 (2012) Sleep and Breathing

구조:
  - 7 구성요소(component), 각 0~3점
  - 총점 0~21점
  - cutoff: 5점 초과 → 수면 질 저하

본 구현은 간소화된 자가보고 — 7 component를 사용자가 직접 추정 입력.
완전한 PSQI는 19개 세부 문항이 필요하나, MVP는 7 component 직접 입력으로 시작.
"""

from __future__ import annotations
from typing import Any


PSQI_CUTOFF = 5


PSQI_COMPONENTS: list[dict[str, Any]] = [
    {
        "no": 1,
        "key": "subjective_quality",
        "name": "주관적 수면의 질",
        "question": "지난 한 달 동안 전반적인 수면의 질은 어떠셨습니까?",
        "options": ["매우 좋음", "꽤 좋음", "꽤 나쁨", "매우 나쁨"],
    },
    {
        "no": 2,
        "key": "sleep_latency",
        "name": "수면 잠복기",
        "question": "잠드는 데 보통 얼마나 걸리셨습니까?",
        "options": ["15분 미만", "16~30분", "31~60분", "60분 초과"],
    },
    {
        "no": 3,
        "key": "sleep_duration",
        "name": "수면 시간",
        "question": "밤에 실제로 잠을 잔 시간은?",
        "options": ["7시간 초과", "6~7시간", "5~6시간", "5시간 미만"],
    },
    {
        "no": 4,
        "key": "habitual_efficiency",
        "name": "수면 효율 (실제 수면/침대 시간)",
        "question": "침대에서 보낸 시간 대비 실제 수면 시간 비율은?",
        "options": ["85% 이상", "75~84%", "65~74%", "65% 미만"],
    },
    {
        "no": 5,
        "key": "disturbances",
        "name": "수면 방해",
        "question": "야간 각성·악몽·통증 등 수면 방해가 얼마나 자주 있었습니까?",
        "options": ["없음", "주 1회 미만", "주 1~2회", "주 3회 이상"],
    },
    {
        "no": 6,
        "key": "medication_use",
        "name": "수면제 사용",
        "question": "수면제를 얼마나 자주 사용하셨습니까?",
        "options": ["전혀", "주 1회 미만", "주 1~2회", "주 3회 이상"],
    },
    {
        "no": 7,
        "key": "daytime_dysfunction",
        "name": "주간 기능 장애",
        "question": "낮 동안 졸음·집중력 저하로 일상 활동에 지장이 있었습니까?",
        "options": ["전혀 없음", "약간 있음", "꽤 있음", "매우 큼"],
    },
]


def score_psqi(component_scores: dict[str, int]) -> dict[str, Any]:
    """PSQI 채점.

    Args:
        component_scores: {key: 0~3} dict (7개 component 키)

    Returns:
        총점·cutoff·해석
    """
    expected_keys = {c["key"] for c in PSQI_COMPONENTS}
    received_keys = set(component_scores.keys())
    if expected_keys != received_keys:
        missing = expected_keys - received_keys
        raise ValueError(f"PSQI 누락 component: {missing}")

    total = 0
    for c in PSQI_COMPONENTS:
        v = component_scores[c["key"]]
        if v not in (0, 1, 2, 3):
            raise ValueError(f"{c['key']} 응답은 0~3 (받음: {v})")
        total += v

    exceeded = total > PSQI_CUTOFF
    if total <= 5:
        severity = "양호한 수면"
    elif total <= 10:
        severity = "약한 수면 질 저하"
    elif total <= 15:
        severity = "수면 질 저하"
    else:
        severity = "심한 수면 질 저하"

    return {
        "total_score": total,
        "cutoff": PSQI_CUTOFF,
        "exceeded_cutoff": exceeded,
        "severity": severity,
        "component_scores": component_scores,
        "interpretive_note": (
            "수면 질 cutoff 초과 — 수면 위생 점검·필요 시 수면 클리닉 상담을 권합니다."
            if exceeded
            else "수면 질은 cutoff 미만. 다만 자가보고는 그날의 컨디션에 영향."
        ),
        "referral_recommended": total >= 10,
        "instrument": "PSQI (Buysse 1989)",
    }


__all__ = [
    "PSQI_CUTOFF",
    "PSQI_COMPONENTS",
    "score_psqi",
]
