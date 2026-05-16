"""Friston 자유 에너지 원리 (Free Energy Principle / Predictive Processing).

출처: Friston (2010) "The free-energy principle: a unified brain theory?",
       Nature Reviews Neuroscience

핵심:
  - 뇌는 예측 오차(prediction error)를 최소화하는 거대 추론 기계
  - 계층적 생성 모델 (hierarchical generative model)
  - 깨어 있을 때: 정밀도 가중치(precision weighting) 높음 → 예측 협소
  - 수면 REM: 외부 입력 차단 + 정밀도 감소 → 억압된 priors가 풀려 시뮬레이션
  - 꿈 = 안전 환경에서 내부 모델 최적화 (model optimization)

본 모듈의 역할:
  - '억압된 prior'(낮에 해결 못한 예측 오차) 신호 탐지
  - '생성적 자유'의 흔적 (시공간 비현실성) 측정
  - 모델 최적화 단계 추정 (재배치/통합/완료)
"""

from __future__ import annotations
from typing import Any


FRISTON_FEP_LABEL = (
    "Friston FEP — 뇌는 예측 오차 최소화 추론 기계. 꿈 = 정밀도 가중치 감소로 "
    "억압된 priors가 풀려 안전 환경에서 모델 최적화."
)


# 억압된 prior 신호 — 낮에 해결 못한 예측 오차
SUPPRESSED_PRIOR_MARKERS = [
    # 미해결 갈등의 재상연
    "다시 만났", "또 그 사람", "또 그 일", "여전히",
    "예전 일", "옛날", "전에 있었던",
    # 처리 못한 감정
    "마음이 무거", "걱정", "근심", "마무리 못", "끝내지 못",
    "후회", "미안", "사과 못",
    # 사회적 prior 위반
    "벗은 몸", "사람들 앞", "발표 망침", "지각",
    "옷을 못 찾", "시험 망",
]

# 생성적 자유 (정밀도 감소) — 시공간·논리 위반
GENERATIVE_FREEDOM_MARKERS = [
    "동시에 여러 곳", "한 사람이 여러", "이상한 조합",
    "현실에선 불가능", "꿈에서만 가능",
    "기괴한", "그로테스크", "초현실",
    "원리가 다른", "물리가 다른",
]

# 모델 최적화 단계 신호
MODEL_REARRANGEMENT_MARKERS = [
    "재배치", "다시 배열", "장면이 바뀜", "재구성",
    "퍼즐", "조각이 맞춰",
]
MODEL_INTEGRATION_MARKERS = [
    "이해됐", "깨달았", "알게 됐", "맞아 떨어졌",
    "연결됐", "맥락이 보였",
]


def detect_prediction_processing(text: str) -> dict[str, Any]:
    """예측 처리·자유 에너지 신호 탐지."""
    t = text or ""

    suppressed = [m for m in SUPPRESSED_PRIOR_MARKERS if m in t]
    free = [m for m in GENERATIVE_FREEDOM_MARKERS if m in t]
    rearr = [m for m in MODEL_REARRANGEMENT_MARKERS if m in t]
    integ = [m for m in MODEL_INTEGRATION_MARKERS if m in t]

    n_sup = len(suppressed)
    n_free = len(free)
    n_rearr = len(rearr)
    n_integ = len(integ)

    # 모델 최적화 단계 추정
    if n_integ >= 1:
        stage = "통합 완료"
        note = "꿈 안에서 깨달음·연결의 모티프 — 모델 최적화가 성공적 단계."
    elif n_rearr >= 1 or n_free >= 3:
        stage = "재배치 진행"
        note = "생성적 자유 활발 — 억압된 priors를 재조합 중. 정착엔 시간 필요."
    elif n_sup >= 2:
        stage = "재처리 시도"
        note = (
            "낮에 해결 못한 예측 오차가 다수 재상연 — 뇌가 처리하려 시도 중. "
            "같은 모티프가 며칠 반복되면 깨어 있을 때의 의식적 결단이 필요."
        )
    elif n_sup + n_free == 0:
        stage = "신호 미감지"
        note = "FEP 관점의 신호가 충분치 않음."
    else:
        stage = "초기 신호"
        note = "약한 예측 처리 신호."

    free_energy_estimate = round(n_sup * 1.0 - n_integ * 0.5, 1)
    # 양수 = 자유에너지 누적, 음수 = 해소

    return {
        "suppressed_prior_markers": suppressed,
        "generative_freedom_markers": free,
        "rearrangement_markers": rearr,
        "integration_markers": integ,
        "stage": stage,
        "interpretive_note": note,
        "free_energy_estimate": free_energy_estimate,
        "fep_principle": (
            "REM 중 정밀도 가중치 감소 → 억압된 priors가 풀림 → 안전 환경에서 시뮬레이션 → "
            "예측 오차 해소 → 깨어 있을 때 자유에너지 감소."
        ),
    }


__all__ = [
    "FRISTON_FEP_LABEL",
    "SUPPRESSED_PRIOR_MARKERS",
    "GENERATIVE_FREEDOM_MARKERS",
    "detect_prediction_processing",
]
