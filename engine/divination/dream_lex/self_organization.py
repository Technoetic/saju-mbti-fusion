"""Zhang & Kahn 자기조직화·연속 활성화 모델.

출처:
  - Zhang (2005~) Continual-Activation Theory
  - Kahn et al. Self-Organization in REM Sleep

핵심:
  - 수면 중 뇌 = 평형 벗어난 복잡계(complex system), '가장자리 혼돈(edge of chaos)'
  - 작업 기억 하위 시스템은 끊임없는 활성화 필요
  - 외부 입력 차단 → 장기 기억에서 무작위 데이터 스트림이 단기로 흘러듦
  - 자기조직화 특성이 파편을 강제로 서사로 조립
  - → 시공간 단절·불연속이 흔한 이유

본 모듈의 역할:
  - 꿈 서사의 불연속성(scene cut)·시공간 점프 측정
  - 자기조직화 강도 추정 (파편의 양 vs 통합 정도)
  - 홉슨 기괴성과 차별화: 홉슨은 '무의미한 잡음', 지앙·칸은 '능동적 자기조직화'
"""

from __future__ import annotations
from typing import Any


SELF_ORG_LABEL = (
    "Zhang & Kahn 자기조직화 — 수면 중 뇌는 가장자리 혼돈 상태. "
    "장기 기억의 파편을 자기조직화가 서사로 조립 → 시공간 불연속이 흔함."
)


# 장면 전환(scene cut) 신호 — 자기조직화의 흔적
SCENE_CUT_MARKERS = [
    "갑자기", "어느새", "어느 순간", "정신을 차려보니", "눈을 떠보니",
    "다음 순간", "그 다음에", "그러더니",
    "장소가 바뀜", "갑자기 다른 곳", "어느 틈에",
    "어딘지 모르는", "낯선 곳",
]

# 시공간 점프
SPATIAL_JUMPS = [
    "여기인데 저기", "한 발 디뎠더니 다른 곳", "들어갔더니",
    "건너편이 갑자기", "벽 뒤가 다른 세계",
]

TEMPORAL_JUMPS = [
    "시간이 빨라", "시간이 멈춤", "시간이 거꾸로", "갑자기 밤",
    "갑자기 낮", "어른인데 어린 시절", "과거로",
]

# 인물·사물 변형 (파편이 다른 파편에 결합)
ENTITY_MORPHING = [
    "얼굴이 바뀌었", "한 사람이 여러", "이름은 같은데 다른",
    "사물이 다른 것으로", "내가 다른 사람이 됐",
]

# 통합·일관성 신호 (자기조직화 성공)
COHERENCE_MARKERS = [
    "이야기가 이어졌", "처음부터 끝까지", "흐름이 자연스러",
    "맥락이 명확", "기승전결",
]


def measure_self_organization(text: str) -> dict[str, Any]:
    """자기조직화 활동·서사 일관성 측정."""
    t = text or ""

    cuts = [m for m in SCENE_CUT_MARKERS if m in t]
    spatial = [m for m in SPATIAL_JUMPS if m in t]
    temporal = [m for m in TEMPORAL_JUMPS if m in t]
    morph = [m for m in ENTITY_MORPHING if m in t]
    coherence = [m for m in COHERENCE_MARKERS if m in t]

    fragmentation_score = len(cuts) + len(spatial) * 2 + len(temporal) * 2 + len(morph) * 2
    coherence_score = len(coherence) * 3

    # 자기조직화 강도 산출
    if fragmentation_score >= 6 and coherence_score == 0:
        verdict = "강한 파편화 (자기조직화 진행)"
        note = (
            "장기 기억의 파편이 다수 활성화되었으나 통합이 약함. "
            "지앙·칸 관점: 정상적 자기조직화 과정 중 — 깨어 있는 뇌가 통합."
        )
    elif fragmentation_score >= 4 and coherence_score >= 3:
        verdict = "활발한 자기조직화 + 부분 통합"
        note = "파편이 다수이나 자기조직화가 서사 일관성을 부여 중. 건강한 패턴."
    elif coherence_score >= 6:
        verdict = "강한 일관성 (자기조직화 성공)"
        note = "통합된 서사 — 자기조직화 후 의식적 후처리도 잘 작동."
    elif fragmentation_score == 0 and coherence_score == 0:
        verdict = "신호 미감지"
        note = "자기조직화 모델 기준으로는 특이 신호 없음 — 짧은 서사."
    else:
        verdict = "약한 파편화"
        note = "약한 장면 전환·통합 신호."

    return {
        "scene_cuts": cuts,
        "spatial_jumps": spatial,
        "temporal_jumps": temporal,
        "entity_morphing": morph,
        "coherence_markers": coherence,
        "fragmentation_score": fragmentation_score,
        "coherence_score": coherence_score,
        "verdict": verdict,
        "interpretive_note": note,
        "zhang_kahn_principle": (
            "꿈의 시공간 단절·인물 변형은 '오류'가 아니라 자기조직화의 흔적. "
            "장기 기억의 무작위 파편을 단기 작업 기억으로 끌어와 강제로 서사를 만드는 과정."
        ),
        "vs_hobson": (
            "홉슨(#7): 기괴성 = 의미 없는 신경 잡음. "
            "Zhang·Kahn: 기괴성 = 능동적 자기조직화의 부산물 — 의미 추출 가능."
        ),
    }


__all__ = [
    "SELF_ORG_LABEL",
    "SCENE_CUT_MARKERS",
    "SPATIAL_JUMPS",
    "TEMPORAL_JUMPS",
    "ENTITY_MORPHING",
    "measure_self_organization",
]
