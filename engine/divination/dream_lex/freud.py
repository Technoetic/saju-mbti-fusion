"""S. Freud 『꿈의 해석(Die Traumdeutung)』 — 꿈-작업(dream-work) 4기제.

기제(메커니즘):
  - condensation(응축): 여러 잠재 사고가 한 이미지로 압축
  - displacement(전치): 정서가 본래 대상에서 무관한 대상으로 이동
  - representation(시각화): 추상적 사고가 구체적 이미지로 번역
  - symbolization(상징화): 검열을 통과하기 위한 변형

비판적 사용 — 모든 상징을 성적으로 환원하지 않는다.
이 기제들은 critic 단계의 평가 축으로 사용된다.
"""

from __future__ import annotations
from typing import Any


FREUD_MECHANISMS = {
    "condensation": "응축 — 여러 인물·장면·감정이 한 이미지로 합쳐짐. 예: 모르는 사람 얼굴에 친구 목소리.",
    "displacement": "전치 — 정서가 본래 대상에서 무관한 대상으로 옮겨감. 사소한 사물에 강렬한 감정.",
    "representation": "시각화 — 추상적 생각·욕망이 구체적 장면으로 번역됨.",
    "symbolization": "상징화 — 검열 회피용 변형. 보편적 상징보다 개인적 연상을 우선.",
}


# 응축 마커 — 한 인물에 여러 정체성 겹침
CONDENSATION_MARKERS = [
    "여러 사람이 한 사람", "여러 얼굴이 겹쳐", "친구인데 가족", "낯선데 익숙",
    "동시에 다른 장소", "두 곳이 동시에", "여러 사람이 합쳐",
    "얼굴이 바뀜", "이름은 같은데 다른", "내가 동시에 누구",
]

# 전치 마커 — 사소한 사물에 과한 정서
DISPLACEMENT_MARKERS = [
    "사소한데 무서웠", "별것 아닌데 슬펐", "이상하게 화났", "왠지 모르게 분노",
    "작은 것에 집착", "엉뚱한 것에 매달려", "이유 없이 두려운",
    "관련 없는데 신경", "엉뚱한 사람한테 화",
]

# 시각화 마커 — 추상 → 구체
REPRESENTATION_MARKERS = [
    "글자가 보였", "숫자가 떠올랐", "지도", "그림으로", "표지판",
    "간판", "포스터", "시간이 멈췄", "거꾸로 흘렀",
]

# 상징화 — 별도 사전 처리 (artemidorus + jung에서 이미 매칭됨)


# 프로이트가 자주 언급한 상징(보편 상징)과 그 보수적 재해석
# — 성환원 회피, 가능성으로만 제시
FREUD_SYMBOLS_CONSERVATIVE: dict[str, str] = {
    "집": "자기 — 다양한 방은 인격의 영역들",
    "왕과 여왕": "부모상",
    "어린아이": "자기 또는 형제자매",
    "긴 옷": "여성성의 보호",
    "지팡이": "권위·지지대 — 성적 환원 비권장",
    "장대": "수직성·야망",
    "터널": "변환의 통로 — 임계 공간(융과 중첩)",
    "동굴": "내면의 깊은 영역",
    "물": "감정·생명의 시작",
    "비행": "야망·자유의 욕구",
    "낙하": "통제 상실에 대한 불안",
    "치아 빠짐": "노화·상실의 두려움 — 신체 변화 인식",
    "벗은 몸": "취약성·진정성 노출 두려움",
    "공중에 떠 있음": "현실과의 거리",
    "사다리": "단계적 욕망",
    "계단": "성취의 단계",
    "기차": "삶의 흐름·이행",
    "비행기": "야망의 도구",
    "총": "공격성 — 권력 욕구",
    "칼": "결단·분리 — 공격성도 포함",
    "왕관": "권위·역할",
    "보석": "본질적 가치",
    "벌": "근면·집단",
    "뱀": "변환·치유와 본능 — 일률 환원 금지",
    "물고기": "재생·풍요",
}


def detect_dream_work(text: str) -> dict[str, Any]:
    """꿈-작업 기제의 흔적을 결정론적으로 탐지."""
    t = text or ""

    cond_hits = [m for m in CONDENSATION_MARKERS if m in t]
    disp_hits = [m for m in DISPLACEMENT_MARKERS if m in t]
    repr_hits = [m for m in REPRESENTATION_MARKERS if m in t]

    sym_hits: list[dict[str, str]] = []
    for kw, meaning in FREUD_SYMBOLS_CONSERVATIVE.items():
        if kw in t:
            sym_hits.append({"keyword": kw, "interpretation": meaning})

    return {
        "condensation": {"detected": len(cond_hits) > 0, "markers": cond_hits},
        "displacement": {"detected": len(disp_hits) > 0, "markers": disp_hits},
        "representation": {"detected": len(repr_hits) > 0, "markers": repr_hits},
        "symbolization": {"detected": len(sym_hits) > 0, "symbols": sym_hits},
        "mechanisms_used": [
            k for k, v in {
                "condensation": cond_hits,
                "displacement": disp_hits,
                "representation": repr_hits,
                "symbolization": sym_hits,
            }.items() if v
        ],
    }


# Critic용 규칙 — Gemini가 프로이트 식 환원에 빠지지 않도록
CRITIC_RULE_NO_SEX_REDUCTION = (
    "프로이트 상징 사용 시: 모든 상징을 성적·리비도적으로 환원하지 말 것. "
    "개인적 연상이 항상 우선. 보편 상징은 가능성으로만 제시. "
    "예: '뱀=남근'은 즉시 부적격. '뱀=변환·치유·본능적 위협의 양가성'은 허용."
)


__all__ = [
    "FREUD_MECHANISMS",
    "CONDENSATION_MARKERS",
    "DISPLACEMENT_MARKERS",
    "REPRESENTATION_MARKERS",
    "FREUD_SYMBOLS_CONSERVATIVE",
    "detect_dream_work",
    "CRITIC_RULE_NO_SEX_REDUCTION",
]
