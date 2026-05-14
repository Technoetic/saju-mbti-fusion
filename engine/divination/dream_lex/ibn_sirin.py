"""이븐 시린 해몽학 (Ibn Sirin Oneiromancy) — 이슬람권 표준 3분류.

출처: Ibn Sirin (8C), Muntakhab al-Kalam fi Tafsir al-Ahlam (후대 편집)

3분류:
  - Ruyā (الرؤيا): 신·천사로부터 오는 진실몽 (밝고 명료, 길조)
  - Hulm (الحلم): 사탄·악령의 거짓몽 (혼란·공포, 의미 없음)
  - Hadith al-Nafs (حديث النفس): 자기암시몽 (낮의 생각·욕망의 반영)

중동·동남아·무슬림 시장 핵심 모듈.
한국어 사용자도 이슬람권 친구·여행자 대상으로 사용 가능.
"""

from __future__ import annotations
from typing import Any


IBN_SIRIN_LABEL = (
    "이븐 시린 — 이슬람권 표준 3분류 (Ruyā/Hulm/Hadith al-Nafs). "
    "꿈의 출처를 신·악령·자기 셋으로 가름."
)


IBN_SIRIN_CLASSES = {
    "ruya": {
        "arabic": "الرؤيا (Ruyā)",
        "korean": "진실몽",
        "description": "신·천사가 보내는 명료하고 밝은 꿈. 길조·계시·치유의 메시지.",
        "characteristics": ["밝음", "명료", "평화", "기쁨", "신성한 인물", "물의 정화"],
    },
    "hulm": {
        "arabic": "الحلم (Hulm)",
        "korean": "거짓몽",
        "description": "사탄(Shaytan)·악령으로부터 오는 혼란·공포의 꿈. 의미 부여 금지.",
        "characteristics": ["혼란", "공포", "불결", "끔찍한 변형", "이슬람 금기 위반", "괴물"],
    },
    "hadith_nafs": {
        "arabic": "حديث النفس (Hadith al-Nafs)",
        "korean": "자아몽 (자기암시몽)",
        "description": "낮의 생각·욕망·근심이 수면 중 반영된 꿈. 자기 점검의 자료.",
        "characteristics": ["일상", "최근 사건", "낯익은 사람", "반복되는 걱정", "직장·가족"],
    },
}


# 분류 마커
RUYA_MARKERS = [
    "밝은 빛", "맑은 물", "흰 옷", "천사", "예언자", "신성한", "성스러운",
    "황금 빛", "은빛", "꿀", "젖", "신선한 과일", "푸른 정원",
    "기도", "코란", "메카", "카바", "녹색", "하지", "축복",
    "평화로움", "고요", "치유", "용서", "구원",
]

HULM_MARKERS = [
    "괴물", "악마", "사탄", "지옥", "피", "오물", "쓰레기", "벌레",
    "끔찍한 변형", "광기", "혼란", "공포", "악취", "썩은",
    "돼지", "개", "원숭이",  # 이슬람권 부정 표상
    "벌거벗음", "수치", "다툼", "살인", "전쟁",
    "검은 그림자", "어둠 속 형체",
]

HADITH_NAFS_MARKERS = [
    "회사", "사무실", "동료", "상사", "어제", "오늘", "방금",
    "가족", "엄마", "아빠", "형제", "친구", "동창",
    "시험", "면접", "발표", "회의",
    "걱정", "근심", "스트레스", "고민", "최근",
    "휴대폰", "노트북", "지하철", "버스",
]


def classify_ibn_sirin(text: str) -> dict[str, Any]:
    """이븐 시린 3분류 — 결정론적 마커 카운트."""
    t = text or ""

    ruya_hits = [m for m in RUYA_MARKERS if m in t]
    hulm_hits = [m for m in HULM_MARKERS if m in t]
    nafs_hits = [m for m in HADITH_NAFS_MARKERS if m in t]

    scores = {
        "ruya": len(ruya_hits),
        "hulm": len(hulm_hits),
        "hadith_nafs": len(nafs_hits),
    }
    if max(scores.values()) == 0:
        cls = "hadith_nafs"  # 기본은 자아몽 (가장 흔한 부류)
    else:
        cls = max(scores, key=lambda k: scores[k])

    class_info = IBN_SIRIN_CLASSES[cls]

    # 권고 행동 (이슬람 전통)
    if cls == "ruya":
        action = "신실한 이에게 나누거나 감사 기도. 길조로 받아들임."
    elif cls == "hulm":
        action = "왼쪽으로 세 번 침을 뱉는 시늉(전통), 사탄에서의 보호 기도(Ta'awwudh) — 의미 부여 거부."
    else:
        action = "낮의 생각·근심의 거울로 자기 점검. 큰 의미 부여 자제."

    return {
        "class": cls,
        "arabic": class_info["arabic"],
        "korean_label": class_info["korean"],
        "description": class_info["description"],
        "scores": scores,
        "ruya_markers": ruya_hits,
        "hulm_markers": hulm_hits,
        "nafs_markers": nafs_hits,
        "traditional_action": action,
        "cultural_note": (
            "이븐 시린 분류는 이슬람권 1차 문헌의 전통입니다. "
            "한국·비무슬림 사용자에게는 '꿈의 출처를 가르는 한 관점'으로만 참고하십시오."
        ),
    }


__all__ = [
    "IBN_SIRIN_LABEL",
    "IBN_SIRIN_CLASSES",
    "RUYA_MARKERS",
    "HULM_MARKERS",
    "HADITH_NAFS_MARKERS",
    "classify_ibn_sirin",
]
