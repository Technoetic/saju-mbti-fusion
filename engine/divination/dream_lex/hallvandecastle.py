"""Hall-Van de Castle 꿈 코딩 시스템 (10대 카테고리).

1966년 캘빈 홀·로버트 반더캐슬이 정립한 표준 꿈 분석 코딩 — DreamBank의
기반. 정량적·반복가능한 분류로, LLM의 인상주의적 해석을 보정한다.

10대 카테고리:
  1. 등장인물(characters) — 가족·친구·낯선이·생물 등
  2. 사회적 상호작용(social interactions) — 우호/공격/성/대화
  3. 활동(activities) — 신체활동·이동·인지활동
  4. 성공/실패(success/failure)
  5. 행운/불운(fortune/misfortune)
  6. 정서(emotions) — 행복·분노·슬픔·공포·당혹
  7. 환경/장소(settings)
  8. 사물(objects)
  9. 묘사 요소(descriptive) — 색·크기·강도
  10. 음식과 식사(food & eating)

이 모듈은 결정론적 코더와, 추가로 LLM 구조화 추출용 스키마를 제공.
"""

from __future__ import annotations
from typing import Any


HVDC_LABEL = (
    "Hall-Van de Castle 코딩 — 꿈을 10대 카테고리로 분해해 정량 분석. "
    "인상주의적 해석에 객관적 골격을 제공."
)


HVDC_CATEGORIES = [
    "characters",
    "social_interactions",
    "activities",
    "success_failure",
    "fortune_misfortune",
    "emotions",
    "settings",
    "objects",
    "descriptive",
    "food_eating",
]


# 결정론적 표지 — 빠른 1차 코딩
CHARACTERS = [
    "엄마", "아빠", "어머니", "아버지", "형", "누나", "언니", "오빠", "동생",
    "할머니", "할아버지", "친구", "동료", "상사", "선생님",
    "남편", "아내", "연인", "남친", "여친",
    "낯선 사람", "외국인", "아이", "노인",
    "고양이", "개", "강아지", "새", "물고기", "뱀", "호랑이", "용",
]
SOCIAL_FRIENDLY = ["대화", "이야기", "안아줌", "포옹", "키스", "미소", "도와줌", "선물"]
SOCIAL_AGGRESSIVE = ["싸움", "다툼", "공격", "때림", "욕설", "비난", "협박", "전쟁"]
SOCIAL_SEXUAL = ["성관계", "키스", "애무", "유혹"]
ACTIVITIES_PHYSICAL = ["달리기", "걷기", "수영", "춤", "운동", "싸움", "노동"]
ACTIVITIES_MOVEMENT = ["이동", "여행", "운전", "비행", "버스", "기차", "비행기"]
ACTIVITIES_COGNITIVE = ["생각", "읽기", "쓰기", "공부", "계산", "기억"]
SUCCESS = ["성공", "이김", "합격", "1등", "수석", "당선", "수상"]
FAILURE = ["실패", "탈락", "낙방", "패배", "지각", "실수", "사고"]
FORTUNE = ["횡재", "복권 당첨", "돈 줍기", "행운", "구조됨"]
MISFORTUNE = ["사고", "재난", "분실", "도난", "병", "다침"]
EMOTION_HAPPY = ["기뻐", "행복", "즐거", "신나", "웃었"]
EMOTION_ANGRY = ["화났", "분노", "짜증", "성났", "격노"]
EMOTION_SAD = ["슬펐", "울었", "비통", "외로움", "쓸쓸"]
EMOTION_FEAR = ["무서웠", "두려", "공포", "겁났", "떨었"]
EMOTION_CONFUSED = ["당황", "혼란", "헷갈", "당혹"]
SETTINGS_HOME = ["집", "방", "거실", "부엌", "침실", "화장실"]
SETTINGS_WORK = ["회사", "사무실", "직장"]
SETTINGS_SCHOOL = ["학교", "교실", "학원", "도서관"]
SETTINGS_OUTDOOR = ["산", "바다", "강", "공원", "숲", "들판"]
SETTINGS_PUBLIC = ["거리", "시장", "병원", "역", "공항", "지하철"]
OBJECTS = ["책", "휴대폰", "차", "옷", "가방", "지갑", "열쇠", "거울", "사진"]
DESCRIPTIVE_COLOR = ["빨간", "파란", "노란", "초록", "검은", "흰", "황금"]
DESCRIPTIVE_SIZE = ["거대한", "큰", "작은", "조그만", "거대"]
FOOD = ["밥", "음식", "고기", "과일", "빵", "케이크", "술", "차", "물", "먹었", "마셨"]


def code_dream(text: str) -> dict[str, Any]:
    """결정론적 1차 HvDC 코딩."""
    t = text or ""

    def hits(lst: list[str]) -> list[str]:
        return [k for k in lst if k in t]

    coding: dict[str, Any] = {
        "characters": hits(CHARACTERS),
        "social_interactions": {
            "friendly": hits(SOCIAL_FRIENDLY),
            "aggressive": hits(SOCIAL_AGGRESSIVE),
            "sexual": hits(SOCIAL_SEXUAL),
        },
        "activities": {
            "physical": hits(ACTIVITIES_PHYSICAL),
            "movement": hits(ACTIVITIES_MOVEMENT),
            "cognitive": hits(ACTIVITIES_COGNITIVE),
        },
        "success_failure": {
            "success": hits(SUCCESS),
            "failure": hits(FAILURE),
        },
        "fortune_misfortune": {
            "fortune": hits(FORTUNE),
            "misfortune": hits(MISFORTUNE),
        },
        "emotions": {
            "happy": hits(EMOTION_HAPPY),
            "angry": hits(EMOTION_ANGRY),
            "sad": hits(EMOTION_SAD),
            "fear": hits(EMOTION_FEAR),
            "confused": hits(EMOTION_CONFUSED),
        },
        "settings": {
            "home": hits(SETTINGS_HOME),
            "work": hits(SETTINGS_WORK),
            "school": hits(SETTINGS_SCHOOL),
            "outdoor": hits(SETTINGS_OUTDOOR),
            "public": hits(SETTINGS_PUBLIC),
        },
        "objects": hits(OBJECTS),
        "descriptive": {
            "color": hits(DESCRIPTIVE_COLOR),
            "size": hits(DESCRIPTIVE_SIZE),
        },
        "food_eating": hits(FOOD),
    }

    return coding


def compute_indices(coding: dict[str, Any]) -> dict[str, float]:
    """HvDC 지표 — 비율 기반.

    - Aggression/Friendliness % = aggressive / (aggressive + friendly)
    - Negative Emotion % = (angry+sad+fear+confused) / total_emotions
    - Misfortune % = misfortune / (fortune + misfortune)
    """
    si = coding["social_interactions"]
    em = coding["emotions"]
    fm = coding["fortune_misfortune"]
    sf = coding["success_failure"]

    aggressive = len(si["aggressive"])
    friendly = len(si["friendly"])
    si_total = aggressive + friendly
    ag_ratio = round(aggressive / si_total * 100, 1) if si_total else 0.0

    pos_em = len(em["happy"])
    neg_em = len(em["angry"]) + len(em["sad"]) + len(em["fear"]) + len(em["confused"])
    em_total = pos_em + neg_em
    neg_em_ratio = round(neg_em / em_total * 100, 1) if em_total else 0.0

    fortune = len(fm["fortune"])
    misfortune = len(fm["misfortune"])
    fm_total = fortune + misfortune
    misfortune_ratio = round(misfortune / fm_total * 100, 1) if fm_total else 0.0

    success = len(sf["success"])
    failure = len(sf["failure"])
    sf_total = success + failure
    failure_ratio = round(failure / sf_total * 100, 1) if sf_total else 0.0

    return {
        "aggression_pct": ag_ratio,
        "negative_emotion_pct": neg_em_ratio,
        "misfortune_pct": misfortune_ratio,
        "failure_pct": failure_ratio,
    }


# LLM 구조화 추출용 스키마 (HvDC code_dream과 동일 모양 — JSON으로 받는다)
LLM_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "characters": {"type": "array", "items": {"type": "string"}},
        "social_interactions": {
            "type": "object",
            "properties": {
                "friendly": {"type": "array", "items": {"type": "string"}},
                "aggressive": {"type": "array", "items": {"type": "string"}},
                "sexual": {"type": "array", "items": {"type": "string"}},
            },
        },
        "activities": {
            "type": "object",
            "properties": {
                "physical": {"type": "array", "items": {"type": "string"}},
                "movement": {"type": "array", "items": {"type": "string"}},
                "cognitive": {"type": "array", "items": {"type": "string"}},
            },
        },
        "success_failure": {"type": "object"},
        "fortune_misfortune": {"type": "object"},
        "emotions": {"type": "object"},
        "settings": {"type": "object"},
        "objects": {"type": "array", "items": {"type": "string"}},
        "descriptive": {"type": "object"},
        "food_eating": {"type": "array", "items": {"type": "string"}},
    },
}


__all__ = [
    "HVDC_LABEL",
    "HVDC_CATEGORIES",
    "code_dream",
    "compute_indices",
    "LLM_EXTRACTION_SCHEMA",
]
