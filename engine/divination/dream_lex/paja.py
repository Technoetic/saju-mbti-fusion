"""파자(破字) 해몽 — 꿈에 나타난 한자·한국어 단어를 자소로 분해해 의미를 추출.

전통 한국 해몽 기법. 예: 꿈에 '木+子' 보면 → 합쳐 '李'(이) → 이 씨 사람.
한국어 단어는 자소(초/중/종성)로 분해해 의미 패턴을 본다.

hanja_data.py(412 한자 사전)를 재사용해 한자 등장 시 의미 매핑.
"""

from __future__ import annotations
from typing import Any
import unicodedata


PAJA_LABEL = (
    "파자(破字) — 꿈에 나온 글자(한자·한국어)를 자소로 분해해 숨은 의미를 추출. "
    "전통 동양 해몽의 핵심 기법."
)


# 자주 등장하는 한자 분해 + 의미 (412 한자 사전 외 핵심 추출)
HANJA_DECOMPOSITION: dict[str, dict[str, str]] = {
    "李": {"parts": "木+子", "meaning": "이씨 — 가지에 열매 — 인물 만남·자녀"},
    "明": {"parts": "日+月", "meaning": "밝음 — 진리·통찰의 도래"},
    "森": {"parts": "木+木+木", "meaning": "숲 — 풍요·집단·복잡"},
    "炎": {"parts": "火+火", "meaning": "이중 불 — 정열·격렬"},
    "焱": {"parts": "火+火+火", "meaning": "맹렬한 불 — 극단의 변환"},
    "淼": {"parts": "水+水+水", "meaning": "넓은 물 — 감정의 범람·기회"},
    "森": {"parts": "木+木+木", "meaning": "숲 — 풍요·은닉"},
    "鑫": {"parts": "金+金+金", "meaning": "큰 부 — 재물의 누적"},
    "好": {"parts": "女+子", "meaning": "여자+아이 — 좋음·자녀의 길조"},
    "安": {"parts": "宀+女", "meaning": "지붕 아래 여자 — 안정·가정"},
    "家": {"parts": "宀+豕", "meaning": "지붕 아래 돼지 — 집안 — 재물 비축"},
    "信": {"parts": "人+言", "meaning": "사람의 말 — 신뢰·약속"},
    "休": {"parts": "人+木", "meaning": "나무 아래 사람 — 쉼·재충전"},
    "森": {"parts": "木+木+木", "meaning": "삼림 — 가려진 본질"},
    "看": {"parts": "手+目", "meaning": "손과 눈 — 관찰·주의"},
    "聽": {"parts": "耳+王+十+目+一+心", "meaning": "귀와 마음 — 깊은 경청"},
    "夢": {"parts": "艹+冖+夕", "meaning": "풀과 덮개와 저녁 — 꿈 그 자체"},
    "想": {"parts": "相+心", "meaning": "마음의 모습 — 생각·바람"},
    "戀": {"parts": "言+絲+心+絲+言", "meaning": "말과 마음의 실 — 사랑·집착"},
    "愛": {"parts": "爪+冖+心+夂", "meaning": "마음을 받쳐 듦 — 사랑"},
    "福": {"parts": "示+一+口+田", "meaning": "제단·입·밭 — 복록"},
    "禄": {"parts": "示+彔", "meaning": "제단의 새김 — 녹봉·봉록"},
    "壽": {"parts": "士+口+一+工+一+口+寸", "meaning": "오랜 삶 — 장수"},
    "財": {"parts": "貝+才", "meaning": "조개·재능 — 재물"},
    "權": {"parts": "木+雚", "meaning": "나무에 황새 — 권위"},
    "智": {"parts": "知+日", "meaning": "앎의 햇빛 — 지혜"},
    "勇": {"parts": "甬+力", "meaning": "용솟음의 힘 — 용기"},
    "義": {"parts": "羊+我", "meaning": "양과 나 — 의로움"},
    "禮": {"parts": "示+曲+豆", "meaning": "제단·굽음·콩 — 예의"},
    "仁": {"parts": "人+二", "meaning": "두 사람 — 인(仁)·관계"},
    "孝": {"parts": "老+子", "meaning": "노인과 아이 — 효"},
    "忠": {"parts": "中+心", "meaning": "마음의 가운데 — 충"},
    "誠": {"parts": "言+成", "meaning": "말의 이룸 — 정성"},
    "貞": {"parts": "卜+貝", "meaning": "점치는 조개 — 곧음·정절"},
}


# 한국어(한글) 자모 의미 단서 — 거친 패턴
HANGUL_INITIAL_HINTS: dict[str, str] = {
    "ㄱ": "굳건·시작",
    "ㄴ": "내면·은밀",
    "ㄷ": "결단·문턱",
    "ㄹ": "흐름·연결",
    "ㅁ": "마음·어머니",
    "ㅂ": "보호·바깥",
    "ㅅ": "솟음·생명",
    "ㅇ": "원·완성",
    "ㅈ": "재물·자기",
    "ㅊ": "촉발·천(天)",
    "ㅋ": "큼·확장",
    "ㅌ": "토대·뚫음",
    "ㅍ": "퍼짐·평면",
    "ㅎ": "하늘·해방",
}


def _decompose_hangul(syllable: str) -> dict[str, str]:
    """한글 한 음절을 초성·중성·종성으로 분해."""
    if not syllable:
        return {"initial": "", "medial": "", "final": ""}
    code = ord(syllable) - 0xAC00
    if code < 0 or code > 11171:
        return {"initial": "", "medial": "", "final": ""}
    initials = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
    medials = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
    finals = " ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"
    i = code // (21 * 28)
    m = (code % (21 * 28)) // 28
    f = code % 28
    return {
        "initial": initials[i] if 0 <= i < len(initials) else "",
        "medial": medials[m] if 0 <= m < len(medials) else "",
        "final": finals[f].strip() if 0 <= f < len(finals) else "",
    }


def analyze_paja(text: str, max_hanja: int = 6, max_keyword_syllables: int = 5) -> dict[str, Any]:
    """텍스트에서 한자 + 핵심 단어를 자소 분해."""
    if not text:
        return {"hanja_decompositions": [], "hangul_analyses": []}

    # 한자 추출
    hanja_found: list[dict[str, str]] = []
    for ch in text:
        if "CJK UNIFIED" in (unicodedata.name(ch, "") or ""):
            if ch in HANJA_DECOMPOSITION:
                hanja_found.append({"char": ch, **HANJA_DECOMPOSITION[ch]})
                if len(hanja_found) >= max_hanja:
                    break

    # 핵심 단어 자소 분석 (등장한 의미있는 명사 후보)
    # 간단히 길이 2~4의 한글 어절 추출
    words = [w for w in text.split() if any("가" <= c <= "힣" for c in w) and 2 <= len(w) <= 4]
    hangul_analyses: list[dict[str, Any]] = []
    for w in words[:max_keyword_syllables]:
        syllables = []
        for ch in w:
            if "가" <= ch <= "힣":
                parts = _decompose_hangul(ch)
                hint = HANGUL_INITIAL_HINTS.get(parts["initial"], "")
                syllables.append({**parts, "initial_hint": hint})
        if syllables:
            hangul_analyses.append({"word": w, "syllables": syllables})

    return {
        "hanja_decompositions": hanja_found,
        "hangul_analyses": hangul_analyses,
    }


__all__ = [
    "PAJA_LABEL",
    "HANJA_DECOMPOSITION",
    "HANGUL_INITIAL_HINTS",
    "analyze_paja",
]
