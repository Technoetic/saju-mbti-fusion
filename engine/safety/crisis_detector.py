"""자살·자해·정신건강 위기 신호 결정론 탐지.

법적·윤리적 의무:
  - 사용자가 위기 신호를 입력했는데 일반 해석만 제공 → 민법 제750조 불법행위 손해배상 가능
  - Character.AI 자살 사용자 방치 소송(2024) 같은 선례 회피
  - 의료법 제27조 무면허 의료행위 회피 (단정 표현 금지)

방식:
  - 결정론적 키워드 탐지 (LLM 호출 0회, ms 단위)
  - 직접 표현(자살하고 싶다) + 간접 표현(살기 싫다, 사라지고 싶다) + 행동 표현(유서, 약 모음) 3중
  - 1건이라도 매칭 시 모든 해석 일시 정지 + 1393/1577-0199 안내
"""

from __future__ import annotations
from typing import Any


# ─────────────────────────── 한국 공식 위기 상담 채널 ───────────────────────────
EMERGENCY_HOTLINES_KR = {
    "1393": {
        "name": "자살예방상담전화",
        "phone": "1393",
        "hours": "24시간 365일",
        "agency": "보건복지부",
    },
    "1577-0199": {
        "name": "정신건강위기상담전화",
        "phone": "1577-0199",
        "hours": "24시간 365일",
        "agency": "국립정신건강센터",
    },
    "129": {
        "name": "보건복지콜센터",
        "phone": "129",
        "hours": "평일 09:00~18:00",
        "agency": "보건복지부",
    },
    "112": {
        "name": "긴급 신고 (생명 위협 임박 시)",
        "phone": "112",
        "hours": "24시간",
        "agency": "경찰청",
    },
    "119": {
        "name": "응급의료 (자해 직후·약물 과다복용)",
        "phone": "119",
        "hours": "24시간",
        "agency": "소방청",
    },
}


# ─────────────────────────── 위기 키워드 (직접 표현) ───────────────────────────
DIRECT_SUICIDE_KEYWORDS = [
    "자살", "스스로 목숨", "목숨을 끊", "목매", "투신",
    "죽고 싶", "죽어버리고 싶", "죽었으면", "죽는 게 낫",
    "끝내고 싶", "끝내버리고", "끝장내고",
    "내 인생을 끝", "삶을 마감", "생을 마감",
]

DIRECT_SELFHARM_KEYWORDS = [
    "자해", "내 몸을 다치", "스스로를 다치", "팔을 그",
    "긋고 싶", "베고 싶", "찌르고 싶",
    "약을 모", "약을 한꺼번에", "약물 과다", "수면제를 모",
]


# ─────────────────────────── 간접 위기 표현 ───────────────────────────
INDIRECT_DESPAIR_KEYWORDS = [
    "살기 싫", "살 이유가 없", "살 가치가 없", "사는 게 의미",
    "사라지고 싶", "없어지고 싶", "존재하고 싶지 않",
    "더 이상 못 견디", "더 이상 버틸", "더 이상 못 살",
    "희망이 없", "미래가 없", "출구가 없", "탈출구가 없",
    "아무도 날 필요", "내가 없어도", "나 같은 게",
    "다 끝났", "모든 게 끝", "그만 살고",
]

# 행동·계획 신호 (가장 위험)
PLANNING_KEYWORDS = [
    "유서", "유언", "마지막 편지", "마지막 인사",
    "재산 정리", "통장 비밀번호", "장례",
    "방법을 찾", "방법을 알아", "어떻게 하면 죽",
    "옥상", "다리에서 뛰", "건물에서 뛰",
]


# ─────────────────────────── 자살 충동을 나타내지 않는 일반 표현 (false positive 회피) ───────────────────────────
# "꿈에서 죽었다", "꿈에서 자살했다" 같은 꿈 내용 묘사는 위기가 아님
NEGATION_PATTERNS = [
    "꿈에서 죽", "꿈에서 자살", "꿈속에서 죽", "꿈속에서 자살",
    "꿈을 꿨", "꿈을 꿈", "악몽", "꿈에 나왔",
    "영화에서", "드라마에서", "소설에서", "게임에서",
    "친구가 죽", "지인이 죽", "가족이 죽", "할아버지가 죽", "할머니가 죽",
    "고인", "사망자", "장례식장",
    # 영어 부정 컨텍스트
    "in my dream", "in a dream", "in the movie", "in the show",
]


# ─────────────────────────── 다국어 위기 키워드 (소문자 매칭) ───────────────────────────
# 영어 — 988 라이프라인이 기준
DIRECT_SUICIDE_KEYWORDS_EN = [
    "want to die", "wanna die", "kill myself", "kill me",
    "end my life", "take my own life", "commit suicide",
    "i want to be dead", "rather be dead", "better off dead",
    "suicidal",
]
DIRECT_SELFHARM_KEYWORDS_EN = [
    "self-harm", "self harm", "cut myself", "cutting myself",
    "hurt myself", "overdose",
]
INDIRECT_DESPAIR_KEYWORDS_EN = [
    "no reason to live", "no point in living", "can't go on",
    "i can't take it anymore", "no way out", "nobody needs me",
    "want to disappear", "wish i was gone", "tired of living",
    "give up on life",
]
PLANNING_KEYWORDS_EN = [
    "suicide note", "final letter", "how to die", "how to kill myself",
    "jump off", "from a bridge", "from a building",
]

# 일본어
DIRECT_SUICIDE_KEYWORDS_JA = [
    "自殺", "死にたい", "消えたい", "命を絶", "首を吊",
    "死のうと", "死ぬしかない", "もう死にたい",
]
DIRECT_SELFHARM_KEYWORDS_JA = [
    "自傷", "リストカット", "リスカ", "自分を傷つけ",
    "薬を一気に", "オーバードーズ",
]
INDIRECT_DESPAIR_KEYWORDS_JA = [
    "生きる意味がない", "もう限界", "もう無理", "誰も必要としない",
    "生きる価値がない", "希望がない", "存在したくない",
]
PLANNING_KEYWORDS_JA = [
    "遺書", "別れの手紙", "ビルから飛び", "電車に飛び込",
]

# 중국어 — 简体/繁体 모두
DIRECT_SUICIDE_KEYWORDS_ZH = [
    "自杀", "自殺",            # 简/繁 자살
    "想死", "我想死",
    "不想活了", "活不下去",
    "结束生命", "結束生命",
    "上吊", "跳楼", "跳樓",
]
DIRECT_SELFHARM_KEYWORDS_ZH = [
    "自残", "自殘",
    "划伤自己", "劃傷自己",
    "伤害自己", "傷害自己",
    "服药过量", "服藥過量",
]
INDIRECT_DESPAIR_KEYWORDS_ZH = [
    "活着没意思", "活著沒意思",
    "没有希望", "沒有希望",
    "没有出路", "沒有出路",
    "我消失了", "消失就好",
    "再也撑不下去", "再也撐不下去",
    "没人需要我", "沒人需要我",
]
PLANNING_KEYWORDS_ZH = [
    "遗书", "遺書",
    "最后的信", "最後的信",
    "怎么死", "怎麼死",
    "从楼上跳", "從樓上跳",
]


# ─────────────────────────── 위기 응답 메시지 (한국어, 법적 안전 톤) ───────────────────────────
CRISIS_RESPONSE_KO = """잠시 멈추겠습니다. 손님의 글에서 무거운 마음이 느껴집니다.

지금 마음이 많이 힘드시다면, 혼자 견디지 마시고 아래 전문 상담에 연결해 주십시오. 모두 무료이며, 24시간 운영됩니다.

  • 자살예방상담전화 1393 (24시간, 보건복지부)
  • 정신건강위기상담전화 1577-0199 (24시간, 국립정신건강센터)
  • 응급 상황(자해 직후·약물 과다복용) 119
  • 즉시 생명 위협 112

본 서비스는 의료 상담이 아니며, 위기 상황을 충분히 도울 수 없습니다. 위 번호의 전문가가 손님의 이야기를 안전하게 들어드릴 것입니다.

해몽 해석은 손님이 안전하다고 느끼실 때 다시 도와드리겠습니다."""


def _contains_any(text: str, keywords: list[str]) -> list[str]:
    """텍스트에 매칭된 키워드 리스트 반환."""
    return [k for k in keywords if k in text]


def _is_negated_context(text: str, matched_keyword: str) -> bool:
    """매칭된 키워드가 꿈 내용 묘사·3인칭·미디어 인용 맥락인지 판단.

    영어 키워드는 소문자 매칭이라 원본 text에서 idx 검색 시 못 찾을 수 있음.
    따라서 소문자 windowing으로 폴백.
    """
    # 매칭된 키워드 주변 ±25자 윈도우에서 부정 패턴 검색
    idx = text.find(matched_keyword)
    if idx < 0:
        # 영어/일본어 — 원본은 대소문자 혼합이라 idx 못 찾을 수 있음 → 소문자에서 재시도
        idx = text.lower().find(matched_keyword.lower())
    if idx < 0:
        return False
    start = max(0, idx - 25)
    end = min(len(text), idx + len(matched_keyword) + 25)
    window = text[start:end].lower()  # 부정 패턴은 모두 소문자
    for neg in NEGATION_PATTERNS:
        if neg.lower() in window:
            return True
    return False


def detect_crisis(text: str) -> dict[str, Any]:
    """위기 신호 결정론 탐지.

    Returns:
        {
            "crisis_detected": bool,
            "severity": "none" | "indirect" | "direct" | "planning",
            "matched_keywords": list[str],
            "filtered_false_positives": list[str],
            "response_required": str | None,  # 위기 시 사용자에게 보여줄 텍스트
            "hotlines": dict | None,  # 위기 시 함께 표시할 핫라인
        }
    """
    t = text or ""
    if not t.strip():
        return {
            "crisis_detected": False,
            "severity": "none",
            "matched_keywords": [],
            "filtered_false_positives": [],
            "response_required": None,
            "hotlines": None,
        }

    # 1차: 모든 키워드 매칭 (한국어 + 영어 소문자 + 일본어 + 중국어)
    t_lower = t.lower()
    direct_suicide = (
        _contains_any(t, DIRECT_SUICIDE_KEYWORDS)
        + _contains_any(t_lower, DIRECT_SUICIDE_KEYWORDS_EN)
        + _contains_any(t, DIRECT_SUICIDE_KEYWORDS_JA)
        + _contains_any(t, DIRECT_SUICIDE_KEYWORDS_ZH)
    )
    direct_selfharm = (
        _contains_any(t, DIRECT_SELFHARM_KEYWORDS)
        + _contains_any(t_lower, DIRECT_SELFHARM_KEYWORDS_EN)
        + _contains_any(t, DIRECT_SELFHARM_KEYWORDS_JA)
        + _contains_any(t, DIRECT_SELFHARM_KEYWORDS_ZH)
    )
    indirect = (
        _contains_any(t, INDIRECT_DESPAIR_KEYWORDS)
        + _contains_any(t_lower, INDIRECT_DESPAIR_KEYWORDS_EN)
        + _contains_any(t, INDIRECT_DESPAIR_KEYWORDS_JA)
        + _contains_any(t, INDIRECT_DESPAIR_KEYWORDS_ZH)
    )
    planning = (
        _contains_any(t, PLANNING_KEYWORDS)
        + _contains_any(t_lower, PLANNING_KEYWORDS_EN)
        + _contains_any(t, PLANNING_KEYWORDS_JA)
        + _contains_any(t, PLANNING_KEYWORDS_ZH)
    )

    # 2차: false positive 필터 (꿈 내용·3인칭·미디어)
    def _filter(matches: list[str]) -> tuple[list[str], list[str]]:
        kept, filtered = [], []
        for m in matches:
            if _is_negated_context(t, m):
                filtered.append(m)
            else:
                kept.append(m)
        return kept, filtered

    direct_suicide, fp1 = _filter(direct_suicide)
    direct_selfharm, fp2 = _filter(direct_selfharm)
    indirect, fp3 = _filter(indirect)
    planning, fp4 = _filter(planning)

    all_matches = direct_suicide + direct_selfharm + indirect + planning
    all_fp = fp1 + fp2 + fp3 + fp4

    if not all_matches:
        return {
            "crisis_detected": False,
            "severity": "none",
            "matched_keywords": [],
            "filtered_false_positives": all_fp,
            "response_required": None,
            "hotlines": None,
        }

    # 심각도 결정 — planning > direct(자살/자해) > indirect
    if planning:
        severity = "planning"
    elif direct_suicide or direct_selfharm:
        severity = "direct"
    else:
        severity = "indirect"

    return {
        "crisis_detected": True,
        "severity": severity,
        "matched_keywords": all_matches,
        "filtered_false_positives": all_fp,
        "response_required": CRISIS_RESPONSE_KO,
        "hotlines": EMERGENCY_HOTLINES_KR,
    }


__all__ = [
    "detect_crisis",
    "CRISIS_RESPONSE_KO",
    "EMERGENCY_HOTLINES_KR",
    "DIRECT_SUICIDE_KEYWORDS",
    "DIRECT_SELFHARM_KEYWORDS",
    "INDIRECT_DESPAIR_KEYWORDS",
    "PLANNING_KEYWORDS",
]
