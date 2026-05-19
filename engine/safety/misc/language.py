"""언어 감지·정책 게이트 — 운영표준 §7.2.3 본문화.

본 모듈은 다음을 결정론적으로 처리:
  1. 입력 텍스트의 주 언어 휴리스틱 감지 (ko/en/ja/zh/other)
  2. 운영 정책 — 외국어 화두에 대한 처리 방침
     · 풀이 본문은 한국어 고정 (운영표준 §7.2.3 정책)
     · 응답 envelope의 lang 필드로 사용 언어 명시
     · 외국어 화두 시 사용자에게 "한국어로 응답" 안내 가능

외부 의존성 0 (한자·가나·한글 유니코드 블록 검사).
"""

from __future__ import annotations


# 유니코드 블록 시작·끝 (포함)
_HANGUL_RANGES = [(0xAC00, 0xD7A3), (0x1100, 0x11FF), (0x3130, 0x318F)]
_HIRAGANA = (0x3040, 0x309F)
_KATAKANA = (0x30A0, 0x30FF)
_CJK_UNIFIED = (0x4E00, 0x9FFF)
_LATIN_BASIC = (0x0041, 0x007A)  # A-z


def _in_range(cp: int, rng: tuple[int, int]) -> bool:
    return rng[0] <= cp <= rng[1]


def _in_any_range(cp: int, ranges: list[tuple[int, int]]) -> bool:
    return any(_in_range(cp, r) for r in ranges)


def detect_language(text: str) -> str:
    """입력 텍스트의 주 언어를 휴리스틱으로 감지.

    Returns:
        'ko' / 'ja' / 'zh' / 'en' / 'other'

    규칙:
      - 한글 점유율 ≥ 30% → 'ko'
      - 히라가나·가타카나 1자 이상 → 'ja' (일본어 고유 글자)
      - 한글·가나 없이 CJK Unified만 → 'zh' (한자 위주는 중국어로 추정)
      - 라틴 알파벳 점유율 ≥ 50% → 'en'
      - 그 외 'other'
    """
    if not text:
        return "other"

    has_hangul = 0
    has_hiragana = 0
    has_katakana = 0
    has_cjk = 0
    has_latin = 0
    total_relevant = 0

    for ch in text:
        cp = ord(ch)
        if _in_any_range(cp, _HANGUL_RANGES):
            has_hangul += 1
            total_relevant += 1
        elif _in_range(cp, _HIRAGANA):
            has_hiragana += 1
            total_relevant += 1
        elif _in_range(cp, _KATAKANA):
            has_katakana += 1
            total_relevant += 1
        elif _in_range(cp, _CJK_UNIFIED):
            has_cjk += 1
            total_relevant += 1
        elif _in_range(cp, _LATIN_BASIC):
            has_latin += 1
            total_relevant += 1

    if total_relevant == 0:
        return "other"

    # 가나가 1자라도 있으면 일본어 (한자는 일본어에서도 흔함)
    if has_hiragana > 0 or has_katakana > 0:
        return "ja"

    # 한글 점유율
    if has_hangul / total_relevant >= 0.30:
        return "ko"

    # 한자만 (가나·한글 없음) → 중국어로 추정
    if has_cjk > 0 and has_hangul == 0:
        return "zh"

    # 라틴 알파벳 점유율
    if has_latin / total_relevant >= 0.50:
        return "en"

    return "other"


# 운영표준 §7.2.3 정책 메시지 — 외국어 화두 사용자에게 안내
_NON_KOREAN_ADVISORY = {
    "en": (
        "Note: This service currently provides physiognomy readings in Korean only. "
        "Your question will be considered, and the reading will be in Korean."
    ),
    "ja": (
        "ご案内: 本サービスは現在、観相の解釈を韓国語のみで提供しています。"
        "ご質問は反映されますが、解釈は韓国語で表示されます。"
    ),
    "zh": (
        "提示: 本服务目前仅以韩文提供观相解读。"
        "您的问题会被参考，但解读以韩文显示。"
    ),
    "other": (
        "Note: Reading is provided in Korean. Your question will be reflected in the reading."
    ),
}


def get_language_advisory(detected_lang: str) -> str | None:
    """감지된 언어가 한국어 외이면 운영표준 §7.2.3에 따른 안내 문구 반환.

    Returns:
        한국어이거나 빈 입력이면 None, 외국어면 모국어 안내 문구.
    """
    if detected_lang == "ko" or not detected_lang:
        return None
    return _NON_KOREAN_ADVISORY.get(detected_lang, _NON_KOREAN_ADVISORY["other"])
