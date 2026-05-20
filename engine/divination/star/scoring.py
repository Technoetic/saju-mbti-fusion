"""ADR-068 — 서양 점성술 결정론 점수 엔진 (성하 공자).

본 모듈은 ADR-005·063 패턴 정합 — 결정론 점수 산출만, LLM 작문 분리.

영역:
  · 12 황도대 (Aries~Pisces) 생년월일 → 태양 별자리 결정
  · Big Three (Sun·Moon·Ascendant) 입문 분류
  · 12 별자리 메타 (4 element·3 modality·지배 행성)
  · 매일 별빛 흐름 (date-based deterministic horoscope tone)

원칙 (ADR-002·006·010 정합):
  · 단정적 예언 차단 (운명·재물·연애 단정 X)
  · 4 element + 3 modality 표준 분류 (학파 단일 강요 X)
  · 사용자 입력 무관 검증 가능 출처 (NASA·국제천문연맹 표준 황도대)
  · 별자리별 부정적·긍정적 균형 묘사 (편향 차단)

면책:
  · 의료·법률·금융 단독 근거 X
  · 사주·MBTI·관상과 직교 (별빛은 보조 도메인)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


# ─────────────────────────── 12 황도대 메타 ───────────────────────────

@dataclass(frozen=True)
class ZodiacSign:
    """12 황도대 단일 별자리 메타.

    Attributes:
        key: 영문 키 (aries~pisces)
        label_ko: 한국어 명칭
        label_en: 영문 명칭
        symbol: 점성술 기호 (♈~♓)
        element: 4 element (fire·earth·air·water)
        modality: 3 modality (cardinal·fixed·mutable)
        ruling_planet: 전통 지배 행성
        date_start: 시작일 (월, 일)
        date_end: 종료일 (월, 일)
    """
    key: str
    label_ko: str
    label_en: str
    symbol: str
    element: str
    modality: str
    ruling_planet: str
    date_start: tuple[int, int]
    date_end: tuple[int, int]


ZODIAC_SIGNS: tuple[ZodiacSign, ...] = (
    ZodiacSign("aries",       "양자리",   "Aries",       "♈", "fire",  "cardinal", "Mars",    (3, 21),  (4, 19)),
    ZodiacSign("taurus",      "황소자리", "Taurus",      "♉", "earth", "fixed",    "Venus",   (4, 20),  (5, 20)),
    ZodiacSign("gemini",      "쌍둥이자리", "Gemini",   "♊", "air",   "mutable",  "Mercury", (5, 21),  (6, 21)),
    ZodiacSign("cancer",      "게자리",   "Cancer",      "♋", "water", "cardinal", "Moon",    (6, 22),  (7, 22)),
    ZodiacSign("leo",         "사자자리", "Leo",         "♌", "fire",  "fixed",    "Sun",     (7, 23),  (8, 22)),
    ZodiacSign("virgo",       "처녀자리", "Virgo",       "♍", "earth", "mutable",  "Mercury", (8, 23),  (9, 22)),
    ZodiacSign("libra",       "천칭자리", "Libra",       "♎", "air",   "cardinal", "Venus",   (9, 23),  (10, 22)),
    ZodiacSign("scorpio",     "전갈자리", "Scorpio",     "♏", "water", "fixed",    "Mars",    (10, 23), (11, 21)),
    ZodiacSign("sagittarius", "사수자리", "Sagittarius", "♐", "fire",  "mutable",  "Jupiter", (11, 22), (12, 21)),
    ZodiacSign("capricorn",   "염소자리", "Capricorn",   "♑", "earth", "cardinal", "Saturn",  (12, 22), (1, 19)),
    ZodiacSign("aquarius",    "물병자리", "Aquarius",    "♒", "air",   "fixed",    "Saturn",  (1, 20),  (2, 18)),
    ZodiacSign("pisces",      "물고기자리", "Pisces",   "♓", "water", "mutable",  "Jupiter", (2, 19),  (3, 20)),
)


# ─────────────────────────── 4 element + 3 modality 메타 ───────────────────────────

ELEMENT_LABELS_KO: dict[str, str] = {
    "fire":  "불",
    "earth": "흙",
    "air":   "바람",
    "water": "물",
}

MODALITY_LABELS_KO: dict[str, str] = {
    "cardinal": "활동궁 — 시작·주도",
    "fixed":    "고정궁 — 지속·결단",
    "mutable":  "변동궁 — 적응·유연",
}


# ─────────────────────────── 별자리 결정 ───────────────────────────

def sign_for_date(birth: date) -> ZodiacSign:
    """생년월일 → 태양 별자리 (12 황도대 표준).

    Args:
        birth: datetime.date 객체

    Returns:
        해당 ZodiacSign. 모든 날짜는 12 별자리 중 하나에 매핑.

    Examples:
        >>> from datetime import date
        >>> sign_for_date(date(1990, 5, 15)).key
        'taurus'
        >>> sign_for_date(date(2026, 12, 25)).key
        'capricorn'
    """
    m, d = birth.month, birth.day
    for sign in ZODIAC_SIGNS:
        sm, sd = sign.date_start
        em, ed = sign.date_end
        # 염소자리는 12/22 ~ 1/19 — 연도 경계 처리
        if sm > em:  # 연도 경계 (12월 → 1월)
            if (m == sm and d >= sd) or (m == em and d <= ed) or m > sm or m < em:
                return sign
        else:
            if (m == sm and d >= sd) or (m == em and d <= ed) or (sm < m < em):
                return sign
    # 안전망 (이론상 도달 X)
    return ZODIAC_SIGNS[0]


def sign_by_key(key: str) -> ZodiacSign | None:
    """영문 키로 별자리 조회."""
    for s in ZODIAC_SIGNS:
        if s.key == key:
            return s
    return None


# ─────────────────────────── 매일 별빛 톤 (date-based deterministic) ───────────────────────────

# 7 톤 — 별자리 × 날짜의 결정론 모듈로 (운명 단정 X, 흐름 톤만)
DAILY_TONES_KO: tuple[str, ...] = (
    "고요한 흐름 — 안으로 돌아보는 결",
    "도약의 결 — 한 걸음 떼어보는 신호",
    "교차의 결 — 사람과의 만남이 짙은 흐름",
    "정돈의 결 — 어지러운 것을 가지런히 두는 흐름",
    "결심의 결 — 미루던 일을 꺼내는 신호",
    "여백의 결 — 잠시 쉬어가도 좋은 흐름",
    "확장의 결 — 가능성을 살피는 결",
)


def daily_tone_for_sign(sign_key: str, target_date: date) -> str:
    """별자리 + 날짜 → 결정론 일일 톤.

    동일 별자리·동일 날짜는 항상 동일 톤 반환 (결정론).
    7 톤 중 하나로 모듈로 회전. 운명 단정 X — 흐름 톤만.
    """
    sign_idx = next((i for i, s in enumerate(ZODIAC_SIGNS) if s.key == sign_key), 0)
    # 날짜를 정수로 변환 (year * 10000 + month * 100 + day) → 7 톤 모듈로
    day_int = target_date.year * 10000 + target_date.month * 100 + target_date.day
    tone_idx = (sign_idx + day_int) % len(DAILY_TONES_KO)
    return DAILY_TONES_KO[tone_idx]


# ─────────────────────────── 결과 dataclass (★ 운명 매핑 필드 부재) ───────────────────────────

@dataclass(frozen=True)
class DailyStarReading:
    """일일 별빛 풀이 결정론 결과.

    ★ 의도적 부재 필드 (ADR-006 운명 단정 차단):
      - love_outcome, career_outcome, money_outcome — 연애·직업·재물 단정 X
      - lucky_number, lucky_color — 미신적 단정 X
    """
    sign_key: str
    sign_label_ko: str
    sign_symbol: str
    element_ko: str
    modality_ko: str
    ruling_planet: str
    daily_tone_ko: str
    target_date: str  # YYYY-MM-DD
    disclaimer: str


_DISCLAIMER = (
    "본 별빛 풀이는 결정론 흐름 톤으로, 운명·연애·재물·직업 단정 X. "
    "참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다. "
    "12 황도대는 국제천문연맹 표준 분류."
)


def compute_daily_star_reading(birth: date, target_date: date) -> DailyStarReading:
    """일일 별빛 풀이 결정론 — 생년월일 + 대상 날짜.

    Args:
        birth: 사용자 생년월일
        target_date: 풀이 대상 날짜 (오늘)

    Returns:
        DailyStarReading — 7 톤 결정론 매핑 + 별자리 메타
    """
    sign = sign_for_date(birth)
    tone = daily_tone_for_sign(sign.key, target_date)
    return DailyStarReading(
        sign_key=sign.key,
        sign_label_ko=sign.label_ko,
        sign_symbol=sign.symbol,
        element_ko=ELEMENT_LABELS_KO.get(sign.element, sign.element),
        modality_ko=MODALITY_LABELS_KO.get(sign.modality, sign.modality),
        ruling_planet=sign.ruling_planet,
        daily_tone_ko=tone,
        target_date=target_date.isoformat(),
        disclaimer=_DISCLAIMER,
    )


# ─────────────────────────── 헬퍼 (Stage 2 프롬프트 주입용) ───────────────────────────

def format_sign_meta_for_prompt(sign: ZodiacSign) -> str:
    """Stage 2 시스템 프롬프트에 주입할 별자리 메타 텍스트."""
    return (
        f"[별자리] {sign.label_ko} ({sign.symbol}, {sign.label_en})\n"
        f"  · element: {ELEMENT_LABELS_KO.get(sign.element, sign.element)}\n"
        f"  · modality: {MODALITY_LABELS_KO.get(sign.modality, sign.modality)}\n"
        f"  · 전통 지배 행성: {sign.ruling_planet}\n"
        f"[안전 장치 — ADR-006] 별자리 분류·요소·모달리티만 사용. "
        f"운명·연애·재물·직업·럭키 번호 단정 금지."
    )


__all__ = [
    "ZodiacSign", "ZODIAC_SIGNS",
    "ELEMENT_LABELS_KO", "MODALITY_LABELS_KO",
    "DAILY_TONES_KO",
    "DailyStarReading",
    "sign_for_date", "sign_by_key",
    "daily_tone_for_sign",
    "compute_daily_star_reading",
    "format_sign_meta_for_prompt",
]
