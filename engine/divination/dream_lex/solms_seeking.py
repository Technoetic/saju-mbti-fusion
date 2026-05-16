"""Solms 정서-동기 가설 (SEEKING) — 신경정신분석 꿈 이론.

출처:
  - Solms (2000) "Dreaming and REM sleep are controlled by different brain mechanisms",
    Behavioral and Brain Sciences 23(6)
  - Solms (2021) The Hidden Spring

핵심:
  - 꿈은 REM이 아니라 복측 피개야(VTA) 메소림빅 도파민 SEEKING 회로 활성에서 발생
  - SEEKING = 욕구·갈망·탐색·호기심의 신경 회로 (Panksepp 7대 정서 회로 중 핵심)
  - 전두-변연 백질 손상 시 꿈이 사라짐 → 도파민이 꿈의 본체

본 모듈의 역할:
  - 꿈 텍스트에서 SEEKING 신호(욕구·탐색·갈망) 추출
  - 프로이트 #5의 신경학적 재해석 — '소망 충족'을 도파민 회로로
"""

from __future__ import annotations
from typing import Any


SOLMS_LABEL = (
    "Solms SEEKING — 꿈은 VTA 메소림빅 도파민 욕구·탐색 회로의 활성. "
    "프로이트 소망 충족론의 신경학적 재해석 (2021 The Hidden Spring)."
)


# Panksepp 7대 정서 회로 중 SEEKING 관련 마커
SEEKING_MARKERS = {
    "탐색": [
        "찾고 있", "찾으러", "탐색", "헤매", "두리번", "샅샅이",
        "어디인지", "어디로 갈", "길을 찾", "방향을",
    ],
    "욕구": [
        "원했다", "갖고 싶", "되고 싶", "이루고 싶", "얻고 싶",
        "갈망", "간절", "꼭 해야", "반드시",
    ],
    "추구": [
        "쫓아갔", "따라갔", "추적", "잡으려", "도달하려",
        "오르려", "건너려", "넘으려",
    ],
    "호기심": [
        "궁금", "신기", "처음 보는", "낯선 곳", "새로운",
        "열어 봤", "들여다 봤", "안에 뭐가",
    ],
    "보상_기대": [
        "보물", "황금", "선물", "복권", "상", "트로피", "메달",
        "발견했", "찾아냈",
    ],
}


# 프로이트 잠재 소망 매핑 (Solms는 이를 SEEKING의 표면 발현으로 본다)
LATENT_WISH_PATTERNS = {
    "인정 욕구": ["박수", "칭찬", "수상", "1등", "주목", "환호"],
    "안전 욕구": ["피신", "보호받", "안전한 곳", "엄마 품", "집으로"],
    "결합 욕구": ["만났", "포옹", "키스", "결혼", "재회", "함께"],
    "지배 욕구": ["내가 이겼", "내가 명령", "왕이 됐", "권력을 잡"],
    "탈출 욕구": ["떠났", "도망쳐 성공", "벗어났", "자유로워"],
}


def detect_seeking(text: str) -> dict[str, Any]:
    """SEEKING 신호 결정론 탐지."""
    t = text or ""

    category_hits: dict[str, list[str]] = {}
    for category, markers in SEEKING_MARKERS.items():
        hits = [m for m in markers if m in t]
        if hits:
            category_hits[category] = hits

    wish_hits: dict[str, list[str]] = {}
    for wish, markers in LATENT_WISH_PATTERNS.items():
        hits = [m for m in markers if m in t]
        if hits:
            wish_hits[wish] = hits

    total_seeking = sum(len(v) for v in category_hits.values())
    total_wishes = sum(len(v) for v in wish_hits.values())

    if total_seeking >= 5:
        intensity = "강함"
        note = "꿈에 SEEKING 회로 활성이 강함 — 깨어 있는 삶에서 추구 중인 것이 있다는 신호."
    elif total_seeking >= 2:
        intensity = "보통"
        note = "일정 수준의 SEEKING 활성 — 일반적 욕구·호기심의 야간 반영."
    elif total_seeking >= 1:
        intensity = "약함"
        note = "약한 SEEKING 신호."
    else:
        intensity = "없음"
        note = "SEEKING 신호 미감지 — Solms 관점에서는 이례적."

    return {
        "seeking_categories": category_hits,
        "total_seeking_markers": total_seeking,
        "seeking_intensity": intensity,
        "latent_wishes": wish_hits,
        "total_wish_markers": total_wishes,
        "interpretive_note": note,
        "freud_reinterpretation": (
            "프로이트의 '잠재 소망'을 Solms는 SEEKING 회로의 도파민 활성으로 재해석합니다. "
            "두 이론은 대체가 아니라 같은 현상의 심리/신경 두 층위입니다."
            if total_wishes > 0
            else None
        ),
    }


__all__ = [
    "SOLMS_LABEL",
    "SEEKING_MARKERS",
    "LATENT_WISH_PATTERNS",
    "detect_seeking",
]
