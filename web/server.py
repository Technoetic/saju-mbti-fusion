"""웹 대시보드 백엔드 — 클래스 지향 + 완전 비동기.

PersonalityAPIServer 클래스가 FastAPI 앱과 9 라이브러리 호출을 감싼다.
Engine 의 비동기 메서드를 사용해 LLM/시스템 호출을 모두 await 가능하게 한다.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# 프로젝트 루트를 sys.path 에 추가 (uvicorn 단독 실행 호환)
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# .env 자동 로드 (Bizrouter API 키 등)
try:
    from dotenv import load_dotenv

    load_dotenv(_ROOT / ".env")
except ImportError:
    pass

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

try:
    from engine import EngineConfig, PersonalityEngine

    _ENGINE_AVAILABLE = True
except ImportError:
    PersonalityEngine = None  # type: ignore
    EngineConfig = None  # type: ignore
    _ENGINE_AVAILABLE = False

from engine.saju import SajuCLI


# === ADR-094 후속 — dream 응답 단정 어휘 사후 필터링 ===
# DREAM_SYSTEM 프롬프트가 차단해도 LLM(Gemini Flash Lite)이
# "길몽으로 해석될 수 있습니다" 같은 가능형 우회 표현 자주 사용.
# 본 함수로 실 응답을 정정 (학파 분류 라벨로 변환).
# ADR-094 단정 어휘 사후 필터링 — 어휘 단위 치환 (문장 문법 유지).
# "길몽" → "길한 결" 단일 단어 치환 → 뒤따르는 동사 활용/조사는 그대로 유지.
# 예: "길몽으로 해석됩니다" → "길한 결로 해석됩니다" (단정 어휘 제거됨)
#     "이 꿈은 길몽입니다" → "이 꿈은 길한 결입니다" (단정 톤 완화)
_DREAM_ASSERTION_REPLACEMENTS = (
    # 구체 표현 우선 (대길의 꿈 → 표현 통째 교체)
    ("대길의 꿈", "한국 민간에서 길조로 분류되는 꿈"),
    ("대흉의 꿈", "한국 민간에서 주의 결로 분류되는 꿈"),
    # 강조 어휘 완화
    ("반드시 ", "대개 "),
    ("확실히 ", "흔히 "),
    # 조사 결합 우선 치환 (어색한 "결으로" 회피)
    ("길몽으로", "길한 결로"),
    ("흉몽으로", "흉한 결로"),
    ("길몽이라", "길한 결이라"),
    ("흉몽이라", "흉한 결이라"),
    # 단정 어휘 단순 치환 (구체 단어 단위만)
    ("길몽", "길한 결"),
    ("흉몽", "흉한 결"),
    ("대길", "길조"),
    ("대흉", "주의 결"),
)


# === 사용자 입력 필드 라벨/값 변환 — LLM 활용도 향상 ===
# front/js/data/contents.js의 select options와 동등한 한국어 라벨 매핑.
# raw value("crush") → display label("짝사랑·썸")으로 변환해 LLM 컨텍스트 풍부화.
_FIELD_LABEL_MAP: dict[str, str] = {
    # 공통 필드 라벨 (한국어)
    "fullName": "내 이름",
    "theirName": "상대 이름",
    "concern": "마음에 떠오르는 것",
    "wish": "소원·바람",
    "birth": "생년월일",
    "gender": "성별",
    "mbti": "MBTI",
    "context": "특히 알고 싶은 곳",
    "relation": "관계",
    "duration": "관계 기간",
    "guess": "짚이는 사람",
    "when": "헤어진 시기",
    "contact": "연락 상태",
    "mood": "오늘 내 마음",
    "decision": "결정 주제",
    "optionA": "선택지 A",
    "optionB": "선택지 B",
    "deadline": "결정 시한",
    "idealType": "이상형",
    "dreamText": "꿈 내용",
    "feeling": "꿈 깬 후 느낌",
    "recent": "최근 스트레스",
    "frequency": "꿈 빈도",
    "whoDream": "꿈 꾼 사람",
    "experience": "자각몽 경험",
    "goal": "자각몽 목표",
    "keyword": "꿈에 나온 것",
}

_FIELD_VALUE_LABEL_MAP: dict[str, dict[str, str]] = {
    "relation": {
        "crush": "짝사랑·썸", "dating": "연애 중",
        "fight": "다툼 후", "breakup": "이별 후", "reunion": "재회 모색 중",
    },
    "duration": {
        "~6m": "6개월 미만", "6m-1y": "6개월~1년",
        "1-3y": "1~3년", "3-5y": "3~5년", "5+": "5년 이상",
    },
    "when": {
        "1m": "한 달 이내", "3m": "1~3개월 전",
        "6m": "3~6개월 전", "1y": "6개월~1년 전", "long": "1년 이상",
    },
    "contact": {
        "none": "연락 없음", "sometimes": "가끔 안부",
        "recent": "최근에 연락 옴", "mine": "내가 먼저 연락",
    },
    "mood": {
        "hope": "희망적", "sad": "쓸쓸함",
        "angry": "화남", "numb": "아무 느낌 없음",
    },
    "context": {
        "work": "직장", "friend": "친구 사이",
        "family": "가족", "romance": "연애", "all": "전반적",
    },
    "gender": {"M": "남자", "F": "여자"},
    "frequency": {
        "weekly": "주 1~2회", "monthly": "한 달에 몇 번",
        "years": "몇 년째 가끔", "lifetime": "평생",
    },
    "whoDream": {
        "mother": "엄마 본인", "father": "아빠",
        "grandmother": "할머니·외할머니", "relative": "친지",
    },
    "experience": {
        "never": "없음 (입문)", "few": "몇 번 있음", "often": "자주 경험",
    },
}


def _resolve_field_labels(
    char_key: str,
    content_key: str,
    fields: dict[str, str] | None,
) -> list[dict[str, str]]:
    """fields raw → 한국어 라벨 + display value 변환.

    LLM이 일반론에 묻지 않고 구체 입력을 인용하도록 라벨/값 풍부화.
    """
    if not fields:
        return []
    out = []
    for k, v in fields.items():
        if v is None or v == "":
            continue
        label = _FIELD_LABEL_MAP.get(k, k)
        value_map = _FIELD_VALUE_LABEL_MAP.get(k, {})
        display = value_map.get(str(v), str(v))
        out.append({"key": k, "label": label, "raw": str(v), "display": display})
    return out


# 공통 단정 어휘 — 모든 캐릭터(hwapae·face·palm·name·star·saju·dream) 적용
# ADR-113 (2026-05-21) 확장: palm 도메인 IHRA 윤리 강령 어휘 추가
#   출처: PMID 7986776 + IHRA 윤리 강령 + Skeptical Inquirer 1982 Michael Alan Park
_COMMON_ASSERTION_REPLACEMENTS = (
    # 일반 단정 부사 (ADR-094 기본)
    ("반드시 ", "대개 "),
    ("확실히 ", "흔히 "),
    ("100% ", "높은 가능성으로 "),
    ("절대 ", "거의 "),
    ("틀림없이 ", "매우 자주 "),
    # palm 도메인 — 결혼·이혼·정신질환 단정 어휘 (ADR-113, IHRA 강령)
    ("이혼할 ", "관계 변화의 결이 비치는 "),
    ("재혼할 ", "새로운 인연의 결이 비치는 "),
    ("결혼 실패", "관계의 결의 흐름"),
    ("다중 결혼", "다양한 인연의 결"),
    ("우울증", "감정의 결"),
    ("정신질환", "내면의 결"),
    ("단명할 ", "건강의 결을 살피는 "),
    ("불행한 말년", "노년의 결의 흐름"),
    ("파탄", "큰 변화"),
    # ADR-116 (2026-05-21) — face 운학 도사 단정 어휘 확장.
    # 발견: past-life·feng-shui 응답에 "길흉화복·대운·금전수·길운" 단정 누설.
    # 본 어휘들은 단독 명사 형태 (공백 미결합) — palm 어휘와 동일 패턴.
    ("길흉화복", "삶의 결의 흐름"),
    ("대운", "큰 흐름"),
    ("금전수", "재물의 결"),
    ("재물수", "재물의 결"),
    ("관운", "공직·직장의 결"),
    ("학문복", "배움의 결"),
    ("재물복", "재물의 결"),
    ("길운", "좋은 흐름"),
    ("흉운", "어려운 시기의 결"),
    ("흉상이라", "그러한 형상이라"),
    ("길상이라", "균형 잡힌 형상이라"),
    ("흉을 막", "어려움을 다스리"),
    ("운명은 늘 고정", "흐름은 늘 변화"),
)


def _sanitize_common_assertion_words(text: str) -> str:
    """모든 캐릭터 공통 단정 어휘 사후 필터링 (ADR-006/094 정신)."""
    if not text:
        return text
    for pat, repl in _COMMON_ASSERTION_REPLACEMENTS:
        text = text.replace(pat, repl)
    return text


# ADR-115 (2026-05-21): 한국어 응답 중 비ASCII 라틴 (악센트 부호) 단어 hallucination 차단.
# 발견 사례: face/reading.py 운학 도사 응답에 포르투갈어 "saudável" 침입.
# 본 시스템은 한국 사용자 대상 한국어 SaaS — LLM 다국어 hallucination은 신뢰 저하 + 의미 불통.
#
# 정책:
# - 악센트 부호 포함 라틴 알파벳 단어는 무조건 제거 (포르투갈어·스페인어·프랑스어·독일어 등)
# - 일반 ASCII 라틴 단어는 보존 (영문 식별자 ADR·KCI·PMID·Sun·Moon·MBTI 등 운영 의무)
import re as _re

# 라틴-1·라틴 확장 영역 악센트 부호 집합 (Unicode 라틴 보충 + 확장-A 핵심)
_ACCENTED_LATIN_PATTERN = _re.compile(
    r"[A-Za-z]*[À-ÿĀ-ſƀ-ɏ][A-Za-zÀ-ÿĀ-ſƀ-ɏ]*"
)


def _sanitize_foreign_hallucination(text: str) -> str:
    """ADR-115 — 한국어 응답 중 악센트 부호 포함 라틴 단어 (다국어 hallucination) 차단.

    예시 차단:
    - "saudável" (포르투갈어 "건강한")
    - "élégant" (프랑스어)
    - "señor" (스페인어)
    - "schön" (독일어)

    예시 보존 (ASCII만):
    - "ADR-006", "KCI", "PMID 7986776", "MBTI", "Sun·Moon", "element·modality"

    Args:
        text: LLM 응답 텍스트

    Returns:
        악센트 부호 라틴 단어 제거된 텍스트 (공백 정리 포함)
    """
    if not text:
        return text
    # 악센트 부호 포함 단어를 한 칸 공백으로 치환 → 한국어 문장 흐름 유지
    cleaned = _ACCENTED_LATIN_PATTERN.sub(" ", text)
    # 연속 공백 정리
    cleaned = _re.sub(r" {2,}", " ", cleaned)
    # 공백 앞 punctuation 정리 (한국어 조사 자연 보존)
    cleaned = _re.sub(r" ([.,;:!?])", r"\1", cleaned)
    return cleaned


# ADR-117 (2026-05-22): face 2단계 파이프라인 응답 한국어 문법 어미·단어 중복 차단.
# 발견 사례 (face 실 어진 라이브 검증):
# - "평평한한" (어미 '한' 중복)
# - "차분한한" (동일 패턴)
# - "콧방울 들린 콧방울" (단어 중복)
# - "이마 넓음 평평함한" (조사 문법 깨짐)
# 원인: Stage 1 영문 라벨 단일어 → Stage 2 사극풍 변환 시 LLM 조립 오류.

# 어미 중복 패턴: ㄴ한·ㄹ한·ㅁ한 같이 종성+한 중복 (한국어 형용사 어미 깨짐)
# ★ 순서 의무: 더 긴 패턴 먼저 적용 (specific → general)
_KOREAN_GRAMMAR_REPAIRS = (
    # 1. 'X음 평평함한' → 'X은 평평한' (조사·어미 정합) — 가장 긴 패턴 먼저
    (_re.compile(r"([가-힣])음 평평함한(?![가-힣])"), r"\1은 평평한"),
    (_re.compile(r"([가-힣])음 ([가-힣]+)함한(?![가-힣])"), r"\1은 \2한"),
    # 2. 'X곧음 하고' → 'X 곧고' 형식 정정 (Stage 2 영문 라벨 조립 오류 fix)
    (_re.compile(r"([가-힣]+)음하고"), r"\1고"),
    (_re.compile(r"([가-힣]+)함하고"), r"\1하고"),
    # 3. 어미 'X한한' → 'X한' (반복 정정) — 가장 일반적 패턴 마지막
    (_re.compile(r"([가-힣])한한(?![가-힣])"), r"\1한"),
    # 4. 어미 'X함한' → 'X함' (어미 병합)
    (_re.compile(r"([가-힣])함한(?![가-힣])"), r"\1함"),
)


def _sanitize_korean_grammar_dupes(text: str) -> str:
    """ADR-117 — 한국어 응답 어미·단어 중복 정정.

    예시:
    - "평평한한" → "평평한"
    - "차분한한" → "차분한"
    - "콧방울 들린 콧방울이로세" → "콧방울 들린 형태이로세"
    - "이마 넓음 평평함한" → "이마 넓은 평평한"

    Args:
        text: LLM 응답 텍스트

    Returns:
        문법 정정된 텍스트.
    """
    if not text:
        return text

    # 1. 정규식 어미 중복 정정
    for pat, repl in _KOREAN_GRAMMAR_REPAIRS:
        text = pat.sub(repl, text)

    # 2. 단어 중복 정정 (2개 이상 연속 동일 단어 검출 → 1개로)
    # 예: "콧방울 들린 콧방울" → "콧방울 들린 (단어 보존)"
    #     2~4 글자 한글 단어가 짧은 거리(15자 이내) 반복 시 후위 단어 제거
    def _dedupe_pattern(m):
        word = m.group(1)
        # 일반 한국어 명사 (얼굴 부위 등) — 너무 짧으면 skip
        if len(word) < 2:
            return m.group(0)
        return f"{word}{m.group(2)}"

    text = _re.sub(
        r"([가-힣]{2,4})(\s+[가-힣]{1,6}\s+)\1",
        _dedupe_pattern,
        text,
    )

    # 3. "X은 평평한 결에" / "X 결" 자연 보존 (불필요 정정 X)
    return text


def _sanitize_dream_assertion_words(text: str) -> str:
    """dream 도메인 LLM 응답 사후 필터링 — ADR-094 단정 어휘 차단 강화.

    DREAM_SYSTEM 프롬프트가 차단해도 LLM(Gemini Flash Lite) 우회 빈번 → 직접 치환.
    어휘 단위 치환으로 문장 문법 유지하며 단정 톤만 완화.
    """
    if not text:
        return text
    for pattern, replacement in _DREAM_ASSERTION_REPLACEMENTS:
        text = text.replace(pattern, replacement)
    return text


# ADR-122 sanitize 5중 안전망 — ancestor (조상 메시지) 단정·빙의·접신 차단
# 학술 근거: 한국학중앙연구원·국립민속박물관·이능화 1927·Skeptical Inquirer
# Susan Gerbic 'Grief Vampires' 콜드/핫 리딩 비판
_ANCESTOR_FORBIDDEN_REPLACEMENTS: list[tuple[str, str]] = [
    # 접신·빙의 어휘 (11건 — 보고서 §3.3 + YAML permanently_forbidden 정합)
    ("빙의된", "보살핌이 깃든"),
    ("빙의", "선대의 보살핌"),
    ("접신한", "정성스러운"),
    ("접신", "선대 추모"),
    ("신내림을 받은", "정성스러운"),
    ("신내림", "선대 추모의 결"),
    ("영안이 트인", "지혜로운"),
    ("영안", "혜안"),
    ("망자의 목소리", "선대의 결"),
    ("영혼의 대화", "추모의 결"),
    ("저승사자", "사후 의례의 결"),
    ("환생하신", "선대로 이어진"),
    ("환생", "이어지는 결"),
    ("채널링", "추모의 결"),
    # 1인칭 망자 빙의 화법 (§3.3 명시 단정 화법 차단)
    ("내가 너를 늘 지켜보고 있다", "선대의 결이 따뜻하게 비추는 흐름"),
    ("네 할아버지가 지금 내게 말하기를", "선대로부터 이어져 온 인연의 결이"),
    ("네 할머니가 지금 내게 말하기를", "선대로부터 이어져 온 인연의 결이"),
    ("네 뒤에 영혼이 서 있다", "선대의 보이지 않는 보살핌이 함께하는 흐름"),
    ("억울하게 물에 빠져 죽은 조상", "선대의 결"),
    ("억울하게 돌아가신 조상이 크게 노했다", "선대의 추모를 다하는 정성이 필요한 흐름"),
    # 사망 원인·윤회·업보 단정 차단
    ("위장병으로 고통받다 돌아가신 조상의 원한", "선대를 추모하는 정성의 흐름"),
    ("전생에 지은 씻을 수 없는 업보", "현재를 보살피는 결"),
    ("전생의 업보", "현재의 결"),
    ("지옥불에 떨어진 영혼의 외침", "선대 추모의 정서"),
    ("지옥", "사후 의례의 결"),
]


def _sanitize_ancestor_assertion_words(text: str) -> str:
    """ancestor 도메인 LLM 응답 사후 필터링 — ADR-122 sanitize 5중 안전망.

    학술 근거 (한국학중앙연구원·국립민속박물관·이능화 1927·Skeptical Inquirer):
      - 접신·빙의·신내림·영안·채널링 어휘 차단 (11건)
      - 망자 1인칭 빙의 화법 차단 (예: "내가 너를 늘 지켜보고 있다")
      - 사망 원인·윤회·업보 단정 차단

    Grief Vampire 위험 (Susan Gerbic 콜드/핫 리딩 비판) 자동 격리.
    LLM(Gemini Flash Lite) 우회 빈번 → 직접 치환.
    """
    if not text:
        return text
    for pattern, replacement in _ANCESTOR_FORBIDDEN_REPLACEMENTS:
        text = text.replace(pattern, replacement)
    return text


# === 요청 모델 ===


class SajuRequest(BaseModel):
    dt_local: str
    tz: str = "Asia/Seoul"
    longitude: float = 126.978
    latitude: float = 37.5665
    is_lunar: bool = False
    is_leap_month: bool = False
    time_unknown: bool = False
    gender: str | None = None
    interpret: bool = False
    mbti: str | None = None
    # 시주 모름 시 보조 시간대 힌트 — "dawn"(05) / "morning"(09) / "noon"(12) /
    # "afternoon"(15) / "evening"(19) / "night"(23). None 이면 기본 12시 fallback.
    time_hint: str | None = None
    # 성명학 — 이름 입력 시 결정론적 분석 + 융합 해설 5섹션 자동 추가
    name_ko: str | None = None
    name_han: str | None = None
    # 응답 언어 — "ko" (기본) / "en" / "ja". LLM 해설/페르소나 언어에만 영향.
    lang: str = "ko"


class SajuExplainRequest(BaseModel):
    section: str  # "pillar" | "wuxing" | "tengods" | "luck" | "shensha"
    saju: dict[str, Any]
    context: str | None = None


class SajuFusionRequest(BaseModel):
    saju: dict[str, Any]
    mbti: str
    lang: str = "ko"


class SajuMyeongRequest(BaseModel):
    name_ko: str
    name_han: str | None = None
    saju_wuxing: dict[str, float] | None = None


class SajuCompatPerson(BaseModel):
    dt_local: str
    tz: str = "Asia/Seoul"
    longitude: float = 126.978
    latitude: float = 37.5665
    is_lunar: bool = False
    is_leap_month: bool = False
    time_unknown: bool = False
    gender: str | None = None
    mbti: str | None = None
    name_ko: str | None = None
    name_han: str | None = None


class SajuCompatRequest(BaseModel):
    a: SajuCompatPerson
    b: SajuCompatPerson
    interpret: bool = True
    # 관계 모드 — "romantic" (기본·연인) / "family" / "work" / "friend"
    # 해설 톤과 듀엣 가사 분위기에 영향
    relation_mode: str = "romantic"
    lang: str = "ko"


class SajuCompatBatchRequest(BaseModel):
    """한 명(a) vs 여러 명(others) 비교 — 점수 표만 반환."""

    a: SajuCompatPerson
    others: list[SajuCompatPerson]


class TranslateRequest(BaseModel):
    text: str
    target: str  # "en" | "ja"


class LLMChatRequest(BaseModel):
    """raw prompt를 백엔드 Bizrouter LLM에 위임. 스트리밍 SSE 응답."""

    prompt: str
    model: str | None = None  # 무시 가능 (백엔드 기본 모델 사용)
    stream: bool = True
    system: str | None = None
    max_tokens: int = 4096


class ManwolReadingRequest(BaseModel):
    """만월아씨 통합 서사 요청 — 사주 + 이름 + 관상/꿈/자미/타로/생활/고민.

    페이로드는 모두 optional. 있는 도메인만 만월아씨 서사에 자연 융합.
    시스템 프롬프트는 서버 고정 (클라이언트 override 불가).
    """

    saju: dict[str, Any] | None = None
    name_analysis: dict[str, Any] | None = None
    life_context: dict[str, Any] | None = None
    concern: str | None = None
    dream_text: str | None = None
    dream_summary: dict[str, Any] | None = None  # /api/dream/interpret analysis_summary (도메인 매칭)
    face_metrics: dict[str, Any] | None = None
    face_reading: dict[str, Any] | None = None  # /api/face/reading 결정론 (palace_scores·visualization·shape)
    face_photo_base64: str | None = None  # 카메라 캡쳐 base64 (data URL 또는 raw). Vision 폴백.
    ziwei_summary: str | None = None
    tarot_cards: list[dict[str, Any]] | None = None
    gender: str | None = None
    age: int | None = None
    stream: bool = True
    max_tokens: int = 4096


class HwapaeCard(BaseModel):
    """추첨된 화패 카드 한 장."""

    한자: str = ""
    한글: str = ""
    sub: str = ""
    의미: str = ""
    position: str | None = None
    group: str | None = None  # major/봉/잔/도/전
    인물: str | None = None
    꽃: str | None = None
    꽃말: str | None = None


class HwapaeReadingRequest(BaseModel):
    """화선 낭자 화패 풀이 요청 — 카드 + 질문 → 백엔드 critic 루프."""

    question: str = ""
    cards: list[HwapaeCard]
    category: str | None = None
    menu_label: str | None = None


class FaceReadingRequest(BaseModel):
    """운학 도사 얼굴 풀이 요청 — 사진(base64) + 보조 정보 + 클라이언트 측 메트릭."""

    image_base64: str  # data URL 또는 raw base64. 1024px 이하 권장.
    age: int | None = None
    gender: str | None = None  # 'M' / 'F' / 자유 문자열
    question: str | None = None  # 화두
    # 클라이언트(MediaPipe Face Landmarker)에서 산출한 정량 메트릭. 없어도 정상 동작.
    # face_scoring으로 12궁 정량 점수 산출에 사용.
    metrics: dict[str, Any] | None = None
    # ADR-274 — 학파 선택 (옵션 D)
    # "mayi": 麻衣相法 (송대 진박, 중국 정통)
    # "yujang": 柳莊相法 (명대, 실용 중시)
    # "korean": 한국 전통 관상 (조선·근대)
    # "samudrika": 인도 Samudrika Shastra
    # None: 통합 (현 default)
    school: str | None = None


class PalmReadingRequest(BaseModel):
    """옥선 할미 손금 풀이 요청 — 손바닥 사진(base64) + 보조 정보.

    ADR-160 Phase 1.5: metrics 필드는 MediaPipe Hand Landmarker 21 keypoint
    프론트 추론 결과 (engine/divination/palm/scoring.score_palm 인터페이스 정합).
    """

    image_base64: str
    age: int | None = None
    gender: str | None = None
    hand: str | None = None  # '왼손' / '오른손' / 자유
    question: str | None = None
    metrics: dict[str, Any] | None = None  # ADR-160 MediaPipe Hand 21 keypoint + 메타


class NameReadingRequest(BaseModel):
    """묵향 선생 이름 풀이 요청 — 한글/한자/사주 보조."""

    fullname_ko: str  # 한글 이름 (필수)
    fullname_han: str | None = None  # 한자 (선택)
    gender: str | None = None
    birth: str | None = None  # 'YYYY-MM-DD' 형식 권장
    saju_day_master: str | None = None  # 일간 (있으면 더 깊은 풀이)
    saju_summary: str | None = None  # 사주 요약 텍스트


class StarReadingRequest(BaseModel):
    """성하 공자 별빛 풀이 요청 — 12 황도대 일일 톤 (ADR-068)."""

    birth: str  # 'YYYY-MM-DD'
    target_date: str | None = None  # None이면 오늘


class ZiweiChartRequest(BaseModel):
    """자미두수 결정론 명반 산출 요청 (ADR-010).

    양력 생년월일시 → 안성법 결정론 명반. LLM 자체산출 X.
    """

    birth: str  # 'YYYY-MM-DD'
    birth_hour: int = 12  # 0~23 시각 (시지 산출용). 미상이면 정오(오시) 기본.
    gender: str = "M"  # 'M'|'F' (배치는 성별 무관, 에코용)


class ContentReadingRequest(BaseModel):
    """메뉴 콘텐츠 풀이 요청 — saju 도메인 결정론 + LLM 결합 (ADR-069).

    char_key 'saju' + content_key 'today' 일 때 사주 엔진 (day_pillar·ten_gods)
    결정론 결과를 system 프롬프트에 주입 → LLM 작문. 결정론 보장 + 사실성 분리.
    """

    char_key: str  # 'saju' | 'dream' | 'hwapae' | 'star' | 'face' | 'palm' | 'name'
    content_key: str  # 'today' | 'tomorrow' | ...
    fields: dict[str, str] | None = None  # 사용자 입력 (fullName·birth 등)


class DreamInterpretRequest(BaseModel):
    """해몽 요청 — 꿈 본문 + 개인 맥락(사주/MBTI 등)."""

    dream_text: str
    # 개인 맥락 (모두 옵션) — PersonalContext.to_dict 키와 동일
    name: str | None = None
    gender: str | None = None  # 'M' or 'F'
    age: int | None = None
    occupation: str | None = None
    marital_status: str | None = None
    has_children: bool | None = None
    is_pregnant: bool | None = None
    current_concerns: list[str] = []
    day_master: str | None = None
    day_master_element: str | None = None
    yongsin: str | None = None
    current_daewoon_element: str | None = None
    saju_summary: str | None = None
    mbti: str | None = None


class SajuAskRequest(BaseModel):
    """사주 페르소나에게 질문 — 사주 컨텍스트로 LLM 대화."""

    saju: dict[str, Any]
    question: str
    history: list[dict[str, str]] = []  # [{role:"user"|"assistant", content:"..."}]
    lang: str = "ko"


# ─────────────────────────── 임상 척도 ───────────────────────────
class ClinicalScreeningRequest(BaseModel):
    """임상 척도 자가검사 — 모든 척도 동시 채점 가능."""

    age: int | None = None
    ces_d_responses: list[int] | None = None  # 20개, 0~3
    bdi_k_responses: list[int] | None = None  # 21개, 0~3
    stai_k_state_responses: list[int] | None = None  # 20개, 1~4
    psqi_component_scores: dict[str, int] | None = None  # 7 component
    isi_responses: list[int] | None = None  # 7개, 0~4
    # 만성 악몽 (IRT 트리거)
    chronic_nightmare_weeks: int | None = None
    nightmare_freq_per_week: int | None = None


# ─────────────────────────── IRT ───────────────────────────
class IRTRescriptRequest(BaseModel):
    """IRT Step 4 — 표적 악몽 재각본 생성 요청."""

    nightmare_text: str


class HVdCLLMRequest(BaseModel):
    """LLM 자동 HVdC 코딩 요청 — Bertolini 2024 한국어 적용."""

    dream_text: str
    merge_with_deterministic: bool = True  # 결정론 코더와 union 병합


class LucidProgramRequest(BaseModel):
    """7일 자각몽 입문 프로그램 요청."""

    pass  # 인자 없음 — 표준 프로그램 반환


class MoodCurveRequest(BaseModel):
    """Cartwright mood-dream 곡선 분석 요청 (7일+).

    daily_entries가 비어 있고 user_id가 있으면 DB에서 최근 14일치를 자동 로드.
    """

    daily_entries: list[dict[str, Any]] = []
    user_id: str | None = None
    days: int = 14


class MyoeLongTermRequest(BaseModel):
    """묘에 몽기 — 장기 일기(14일+) 모티프·곡선 분석.

    entries가 비고 user_id가 있으면 DB에서 자동 로드 (최대 30일).
    """

    entries: list[dict[str, Any]] = []
    user_id: str | None = None
    min_entries: int = 14
    days: int = 30


class IChingDivinationRequest(BaseModel):
    """주역 64괘 — 꿈 본문으로부터 괘 도출."""

    dream_text: str


class DormioSessionRequest(BaseModel):
    """Dormio TDI — N1 표적 부화 세션 빌드."""

    target_topic: str
    category: str = "creative_problem"
    cycles: int = 2


class DormioSynthesizeRequest(BaseModel):
    """Dormio 미세꿈 보고들 통합."""

    target_topic: str
    reports: list[dict[str, Any]]


class UllmanGroupRequest(BaseModel):
    """Ullman 그룹 꿈 분석 — N개 페르소나 투사 생성."""

    dream_text: str
    personas: list[dict[str, str]] | None = None  # None이면 기본 5개 페르소나


class HillStepRequest(BaseModel):
    """Clara Hill 3단계 — 한 단계씩 진행."""

    dream_text: str
    step: int  # 1=Exploration, 2=Insight, 3=Action
    exploration_responses: list[str] = []
    insight_text: str | None = None


# ─────────────────────────── 익명 사용자 / 종단 데이터 ───────────────────────────
class UserProfileRequest(BaseModel):
    """사용자 프로필 부분 갱신."""
    user_id: str
    gender: str | None = None
    age: int | None = None
    occupation: str | None = None
    mbti: str | None = None
    day_master: str | None = None
    yongsin: str | None = None


class ConsentRequest(BaseModel):
    """민감정보(정신건강 데이터) 별도 동의."""
    user_id: str
    consent: bool


class SignupRequest(BaseModel):
    """이메일/비번 회원가입 + 사주 프리필(선택)."""
    email: str
    password: str
    nickname: str | None = None
    # 사주 프리필 (전부 선택)
    name_ko: str | None = None
    birth_year: int | None = None
    birth_month: int | None = None
    birth_day: int | None = None
    birth_hour_branch: str | None = None
    birthplace: str | None = None
    is_lunar: bool = False
    gender: str | None = None
    mbti: str | None = None


class LoginRequest(BaseModel):
    """이메일/비번 로그인."""
    email: str
    password: str


class DiaryAddRequest(BaseModel):
    """Schredl 표준 일기 저장."""
    user_id: str
    narrative_text: str
    recall_quality: int = 3
    vividness: int = 3
    valence: int = 0
    lucidity: int = 0
    wake_time_iso: str | None = None
    sleep_duration_min: int | None = None
    # 묘에 필드 (선택)
    core_image: str | None = None
    felt_meaning: str | None = None
    spiritual_resonance: str | None = None
    next_intention: str | None = None
    # 자동 분석·저장
    analyze: bool = False  # True면 dream.interpret_dream 분석 결과도 저장


class ClinicalLogRequest(BaseModel):
    """임상 척도 채점 결과를 영구 저장."""
    user_id: str
    instrument: str  # 'ces_d' | 'bdi_k' | 'stai_k_state' | 'psqi' | 'isi'
    responses: list[Any] | dict[str, Any] | None = None
    age: int | None = None
    psqi_components: dict[str, int] | None = None


class LearningLogRequest(BaseModel):
    """학습/작업 로그 — Stickgold 72h 매칭용."""
    user_id: str
    activity_text: str
    domain: str | None = None
    activity_at_iso: str | None = None


class UserScopedRequest(BaseModel):
    """user_id만 필요한 요청 (조회/삭제)."""
    user_id: str


# ─────────────────────────── v2 오케스트레이터 ───────────────────────────
class InterpretV2Request(BaseModel):
    """v2 오케스트레이션 — 14 에이전트 + 30 도메인 통합 해석."""
    dream_text: str
    user_id: str | None = None
    profile: dict[str, Any] | None = None  # PersonalContext dict
    locale: str = "ko"
    religion: str | None = None
    user_target_domain: str | None = None  # 'career'|'romance'|...
    enable_llm_agents: bool = True


class BivalentFeedbackRequest(BaseModel):
    """양가 카드 사용자 선택 피드백."""
    user_id: str
    chosen_source: str  # 'artemidorus' | 'zhougong' | 'korean_folk' | 'ibn_sirin'
    polarity: str  # '길' | '흉' | '양가'
    keyword: str | None = None


# ─────────────────────────── 꿈 부화 ───────────────────────────
class IncubationRequest(BaseModel):
    """꿈 부화 안내 요청."""

    question: str = ""
    low_recall: bool = False
    upcoming_decision: bool = False
    high_stress: bool = False
    lucid_dream_practice: bool = False


class SajuImageRequest(BaseModel):
    kind: str  # "persona" | "pillar" | "wuxing" | "luck" | "compat"
    saju: dict[str, Any] | None = None
    alias: dict[str, Any] | None = None
    compat_score: int | None = None
    compat_grade: str | None = None
    # 궁합 전용 — 두 사람 컨텍스트 (kind="compat")
    compat_a: dict[str, Any] | None = None
    compat_b: dict[str, Any] | None = None
    compat_stem_rel: str | None = None
    compat_branch_rel: str | None = None


class SajuMusicRequest(BaseModel):
    persona: str | None = None
    mbti: str | None = None
    strongest_wuxing: str | None = None
    weakest_wuxing: str | None = None
    day_master: str | None = None
    name_ko: str | None = None
    # 성명학 4격 — 곡 구조(Intro/Verse/Chorus/Outro) 매핑용
    grids: dict[str, Any] | None = None


class SajuCompatMusicRequest(BaseModel):
    a_persona: str | None = None
    b_persona: str | None = None
    a_mbti: str | None = None
    b_mbti: str | None = None
    a_day_master: str | None = None
    b_day_master: str | None = None
    a_name_ko: str | None = None
    b_name_ko: str | None = None
    a_strongest_wuxing: str | None = None
    b_strongest_wuxing: str | None = None
    a_grids: dict[str, Any] | None = None
    b_grids: dict[str, Any] | None = None
    score: int | None = None
    grade: str | None = None
    stem_rel: str | None = None
    branch_rel: str | None = None
    relation_mode: str = "romantic"


class TarotRequest(BaseModel):
    question: str = "오늘의 메시지"
    spread: str = "three"
    seed: int | None = None


class IChingRequest(BaseModel):
    question: str = "오늘의 흐름"
    seed: int | None = None


class AssessAllRequest(BaseModel):
    """9 시스템 통합 비동기 평가."""

    nl_text: str | None = None
    saju: SajuRequest | None = None
    oracle_question: str | None = None
    oracle_seed: int | None = None


# === API 서버 클래스 ===


class PersonalityAPIServer:
    """9 라이브러리 비동기 API 서버.

    FastAPI 앱 + Engine 인스턴스를 보유. 모든 endpoint 가 `async`.
    `app` 속성으로 ASGI 앱 노출.
    """

    _MBTI_TYPES = frozenset(
        {
            "INTJ",
            "INTP",
            "ENTJ",
            "ENTP",
            "INFJ",
            "INFP",
            "ENFJ",
            "ENFP",
            "ISTJ",
            "ISFJ",
            "ESTJ",
            "ESFJ",
            "ISTP",
            "ISFP",
            "ESTP",
            "ESFP",
        }
    )

    def __init__(self, engine=None, mount_static: bool = True):
        if engine is not None:
            self.engine = engine
        elif _ENGINE_AVAILABLE and PersonalityEngine is not None:
            self.engine = PersonalityEngine(EngineConfig())  # type: ignore[arg-type]
        else:
            self.engine = None
        self.saju_cli = SajuCLI()
        self.app = FastAPI(title="Personality Fusion Dashboard")
        cors_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 정적 파일 캐시 무효화 — 모바일 브라우저(iOS Safari·Chrome)가 공격적으로
        # 캐시해 변경이 즉시 안 보이던 문제 해결.
        # 1) ?v= 쿼리가 있으면 → 강제 새 URL이라 안전하게 1년 캐시
        # 2) 그 외 정적 파일 → no-store + no-cache + must-revalidate + max-age=0
        @self.app.middleware("http")
        async def add_no_cache_headers(request, call_next):
            response = await call_next(request)
            path = request.url.path
            query = request.url.query
            if path.endswith((".js", ".css", ".html")) or path == "/":
                if "v=" in query:
                    # 버전 쿼리 있는 정적 리소스 → 안전하게 1년 캐시
                    response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
                else:
                    # 쿼리 없는 정적 리소스(직접 접근 등) → 절대 캐시 X
                    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
                    response.headers["Pragma"] = "no-cache"
                    response.headers["Expires"] = "0"
            return response

        # GET "/" 직접 처리 — StaticFiles mount보다 먼저 등록되어야 catch.
        # 새 배포마다 사용자 브라우저가 옛 HTML/JS/CSS를 캐싱해 깨지는 사고 방지.
        # HTML 본문 안의 모든 정적 리소스 URL에 ?v=<빌드시각> 자동 주입 →
        # 새 배포마다 URL이 바뀌어 브라우저는 무조건 새 파일을 받아옴.
        from fastapi.responses import HTMLResponse
        import re as _re_for_static
        import time as _time_for_build

        _BUILD_TAG = str(int(_time_for_build.time()))

        @self.app.get("/", include_in_schema=False)
        async def serve_index_no_cache():
            front_dir = Path(__file__).resolve().parent.parent / "front"
            index_path = front_dir / "index.html"
            if not index_path.exists():
                index_path = Path(__file__).resolve().parent / "index.html"

            html = index_path.read_text(encoding="utf-8")

            # <script src="..."> 와 <link ... href="..."> 의 정적 URL에 ?v=BUILD_TAG 주입.
            # 외부 도메인(https://) 은 건너뛰고, 쿼리가 이미 있어도 안전하게 덮어씀.
            def _inject(match):
                attr_name = match.group(1)
                url = match.group(2)
                if url.startswith(("http://", "https://", "//", "data:")):
                    return match.group(0)
                # 기존 쿼리 제거 후 새 v= 부착
                clean = url.split("?", 1)[0]
                return f'{attr_name}="{clean}?v={_BUILD_TAG}"'

            html = _re_for_static.sub(
                r'\b(src|href)="([^"]+\.(?:js|css))(?:\?[^"]*)?"',
                _inject,
                html,
            )

            return HTMLResponse(
                content=html,
                headers={
                    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            )

        # 단순 카운터 + 응답시간 누적 모니터링 (Prometheus 호환 텍스트)
        self._metrics = {
            "requests_total": 0,
            "errors_total": 0,
            "duration_sum_ms": 0.0,
            # 최근 1000개 응답 시간 (p50/p95/p99 계산용)
            "duration_samples": [],
        }
        # 분석 로그 — 호출 패턴 카운터 (in-memory)
        self._analytics = {
            "mbti_counts": {},          # 사용된 MBTI별 카운트
            "day_master_counts": {},    # 사용된 일간별 카운트
            "compat_grade_counts": {},  # 궁합 등급별 카운트
            "music_calls": 0,
            "image_calls": 0,
            "compat_music_calls": 0,
            "compat_image_calls": 0,
            # 캐시 hit/miss
            "cache_music_hit": 0,
            "cache_music_miss": 0,
            "cache_image_hit": 0,
            "cache_image_miss": 0,
            # critic 통계 (이미지)
            "image_critic_totals": [],
            "image_critic_rounds": [],
            # 외부 API 마지막 ping
            "minimax_last_ok": None,
            "bizrouter_last_ok": None,
            # 클라이언트 에러 로그 (최근 50개)
            "client_errors": [],
            # v2 오케스트레이션 통계
            "dream_v2_calls": 0,
            "dream_v2_crisis_blocked": 0,
            "dream_v2_elapsed_ms_samples": [],  # 최근 50개
            "dream_v2_persona_counts": {},
            "dream_v2_cathartic_counts": 0,
            "clinical_log_calls": 0,
            "diary_add_calls": 0,
            "irt_rescript_calls": 0,
        }
        # IP별 슬라이딩 윈도 (60s) rate limit
        self._rate_window: dict[str, list[float]] = {}
        self._rate_limit_per_min = int(os.environ.get("RATE_LIMIT_PER_MIN", "60"))
        self._install_rate_limit_middleware()
        self._install_metrics_middleware()
        self._register_routes()
        # DB 초기화 (스키마 생성, idempotent)
        try:
            from engine.storage import init_db, init_ops_tables
            init_db()
            init_ops_tables()
        except Exception as e:
            print(f"[storage] init_db failed (non-fatal): {e}")
        # 시작 시 캐시 LRU 정리 (각 디렉토리 500MB 상한)
        try:
            self._cleanup_caches()
        except Exception:
            pass
        # 1시간마다 주기적 cleanup (백그라운드 태스크)
        @self.app.on_event("startup")
        async def _periodic_cleanup():
            async def _loop():
                while True:
                    await asyncio.sleep(3600)
                    try:
                        await asyncio.to_thread(self._cleanup_caches)
                    except Exception:
                        pass
                    # ops 정리 (24시간마다)
                    try:
                        from engine.storage import ErrorLogRepo, CrisisStatsRepo, RateLimitRepo
                        await asyncio.to_thread(ErrorLogRepo.cleanup_old, 30)
                        await asyncio.to_thread(CrisisStatsRepo.cleanup_old, 30)
                        await asyncio.to_thread(RateLimitRepo.cleanup_old, 7)
                    except Exception:
                        pass
            asyncio.create_task(_loop())

        # ADR-256 — ONNX 세션 사전 빌드 (첫 사용자 502 회피)
        @self.app.on_event("startup")
        async def _warmup_palm_unet():
            try:
                from engine.divination.palm.unet_line_extractor import warmup_unet_session
                ok = await asyncio.to_thread(warmup_unet_session)
                print(f"[ADR-256 warmup] palm UNet session ready={ok}")
            except Exception as e:
                print(f"[ADR-256 warmup] skipped: {e}")

        # 24시간마다 DB 백업
        @self.app.on_event("startup")
        async def _periodic_backup():
            async def _bk_loop():
                while True:
                    await asyncio.sleep(86400)  # 24h
                    try:
                        from engine.storage import backup_db
                        result = await asyncio.to_thread(backup_db, max_keep=7)
                        if result.get("ok"):
                            print(f"[backup] OK: {result['backup_path']} ({result['size_bytes']} bytes)")
                    except Exception as e:
                        print(f"[backup] failed: {e}")
            asyncio.create_task(_bk_loop())
        if mount_static:
            self._mount_static()

    def _install_rate_limit_middleware(self) -> None:
        import time as _t

        @self.app.middleware("http")
        async def rate_limit_mw(request, call_next):
            # API 호출만 제한 (정적 자산 통과)
            path = request.url.path
            if not path.startswith("/api/"):
                return await call_next(request)
            ip = (request.client.host if request.client else "anon") or "anon"
            now = _t.time()
            window = self._rate_window.setdefault(ip, [])
            cutoff = now - 60.0
            # 슬라이딩 윈도 청소
            while window and window[0] < cutoff:
                window.pop(0)
            if len(window) >= self._rate_limit_per_min:
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    {"detail": "Too many requests. 잠시 후 다시 시도해주세요."},
                    status_code=429,
                )
            window.append(now)
            return await call_next(request)

    def _cleanup_caches(self) -> None:
        """캐시 디렉토리 LRU 정리 — 각 500MB 초과 시 오래된 파일 삭제."""
        root = Path(__file__).resolve().parent.parent / "step_archive"
        limits = {
            "img_cache": 500 * 1024 * 1024,
            "music_cache": 500 * 1024 * 1024,
            "explain_cache": 100 * 1024 * 1024,
        }
        for name, limit in limits.items():
            d = root / name
            if not d.exists():
                continue
            files = [(f, f.stat().st_size, f.stat().st_mtime) for f in d.iterdir() if f.is_file()]
            total = sum(s for _, s, _ in files)
            if total <= limit:
                continue
            # 오래된 순으로 삭제
            files.sort(key=lambda x: x[2])
            for f, size, _ in files:
                if total <= limit:
                    break
                try:
                    f.unlink()
                    total -= size
                except Exception:
                    pass

    def _install_metrics_middleware(self) -> None:
        import time

        @self.app.middleware("http")
        async def metrics_middleware(request, call_next):
            t0 = time.perf_counter()
            try:
                response = await call_next(request)
                return response
            except Exception:
                self._metrics["errors_total"] += 1
                raise
            finally:
                elapsed_ms = (time.perf_counter() - t0) * 1000
                self._metrics["requests_total"] += 1
                self._metrics["duration_sum_ms"] += elapsed_ms
                samples = self._metrics["duration_samples"]
                samples.append(elapsed_ms)
                if len(samples) > 1000:
                    del samples[: len(samples) - 1000]

    # === 라우터 등록 ===

    def _register_routes(self) -> None:
        self.app.post("/api/saju")(self.post_saju)
        self.app.post("/api/saju/explain")(self.post_saju_explain)
        self.app.post("/api/saju/fusion")(self.post_saju_fusion)
        self.app.post("/api/saju/myeong")(self.post_saju_myeong)
        self.app.post("/api/saju/compat")(self.post_saju_compat)
        self.app.get("/api/hanja/candidates")(self.get_hanja_candidates)
        self.app.post("/api/saju/image")(self.post_saju_image)
        self.app.post("/api/saju/music")(self.post_saju_music)
        self.app.post("/api/saju/compat/music")(self.post_saju_compat_music)
        self.app.post("/api/tarot")(self.post_tarot)
        self.app.post("/api/iching")(self.post_iching)
        self.app.post("/api/assess_all")(self.post_assess_all)
        self.app.get("/api/profile/{type_}")(self.get_profile)
        self.app.get("/api/health")(self.get_health)
        self.app.get("/metrics")(self.get_metrics)
        self.app.get("/api/analytics")(self.get_analytics)
        self.app.get("/api/saju/daily")(self.get_saju_daily)
        self.app.get("/api/saju/daily_month")(self.get_saju_daily_month)
        self.app.post("/api/saju/compat_batch")(self.post_saju_compat_batch)
        self.app.post("/api/saju/ask")(self.post_saju_ask)
        self.app.post("/api/translate")(self.post_translate)
        self.app.post("/api/llm/chat")(self.post_llm_chat)
        self.app.post("/api/manwol/reading")(self.post_manwol_reading)
        self.app.post("/api/hwapae/reading")(self.post_hwapae_reading)
        self.app.post("/api/face/reading")(self.post_face_reading)
        self.app.post("/api/palm/reading")(self.post_palm_reading)
        self.app.get("/api/palm/diagnostics")(self.get_palm_diagnostics)
        self.app.post("/api/star/reading")(self.post_star_reading)
        self.app.post("/api/ziwei/chart")(self.post_ziwei_chart)
        self.app.post("/api/content/reading")(self.post_content_reading)
        self.app.post("/api/name/reading")(self.post_name_reading)
        self.app.post("/api/dream/interpret")(self.post_dream_interpret)
        self.app.post("/api/clinical/screening")(self.post_clinical_screening)
        self.app.get("/api/clinical/instruments")(self.get_clinical_instruments)
        self.app.post("/api/irt/rescript")(self.post_irt_rescript)
        self.app.post("/api/incubation/session")(self.post_incubation_session)
        self.app.post("/api/dream/hvdc_llm")(self.post_dream_hvdc_llm)
        self.app.get("/api/lucid/program")(self.get_lucid_program)
        self.app.post("/api/cartwright/mood_curve")(self.post_mood_curve)
        self.app.post("/api/myoe/long_term")(self.post_myoe_long_term)
        self.app.get("/api/myoe/diary_template")(self.get_myoe_diary_template)
        self.app.post("/api/iching/divine")(self.post_iching_divine)
        self.app.post("/api/dormio/session")(self.post_dormio_session)
        self.app.post("/api/dormio/synthesize")(self.post_dormio_synthesize)
        self.app.post("/api/ullman/group")(self.post_ullman_group)
        self.app.post("/api/hill/step")(self.post_hill_step)
        # ─── 익명 사용자 + 종단 데이터 ───
        self.app.post("/api/user/new")(self.post_user_new)
        self.app.post("/api/user/profile")(self.post_user_profile)
        self.app.post("/api/user/consent")(self.post_user_consent)
        self.app.post("/api/user/delete")(self.post_user_delete)
        self.app.post("/api/auth/signup")(self.post_auth_signup)
        self.app.post("/api/auth/login")(self.post_auth_login)
        self.app.get("/api/auth/me")(self.get_auth_me)
        self.app.post("/api/diary/add")(self.post_diary_add)
        self.app.post("/api/diary/list")(self.post_diary_list)
        self.app.post("/api/clinical/log")(self.post_clinical_log)
        self.app.post("/api/clinical/trend")(self.post_clinical_trend)
        self.app.post("/api/learning/add")(self.post_learning_add)
        # v2 오케스트레이터
        self.app.post("/api/dream/interpret_v2")(self.post_dream_interpret_v2)
        self.app.post("/api/dream/bivalent_feedback")(self.post_bivalent_feedback)
        # 운영
        self.app.get("/api/ops/error_log")(self.get_ops_error_log)
        self.app.get("/api/ops/crisis_stats")(self.get_ops_crisis_stats)
        self.app.post("/api/ops/backup_db")(self.post_ops_backup)
        self.app.post("/api/freud/map")(self.post_freud_map)
        self.app.get("/api/social/unconscious")(self.get_social_unconscious)
        self.app.get("/api/legal/terms")(self.get_legal_terms)
        self.app.get("/api/legal/privacy")(self.get_legal_privacy)
        self.app.post("/api/errors")(self.post_error_log)
        self.app.get("/sw.js")(self.get_service_worker)
        self.app.get("/api/diag/kasi-verify")(self.get_diag_kasi_verify)

    def _mount_static(self) -> None:
        # 프론트 디렉토리 — 프로젝트 루트의 front/ 사용
        front_dir = Path(__file__).resolve().parent.parent / "front"
        if not front_dir.exists():
            # fallback: web/ 자체 (이전 구조 호환)
            front_dir = Path(__file__).resolve().parent
        self.app.mount(
            "/",
            StaticFiles(directory=str(front_dir), html=True),
            name="static",
        )

    # === Endpoint 메서드 (모두 async) ===

    _TIME_HINT_HOUR = {
        "dawn": 5,
        "morning": 9,
        "noon": 12,
        "afternoon": 15,
        "evening": 19,
        "night": 23,
    }

    async def post_saju(self, req: SajuRequest) -> dict[str, Any]:
        """SajuCLI 기반 결정론적 사주 평가 (engine.saju). interpret=True 면 LLM 해설 첨부."""
        if req.mbti:
            self._analytics["mbti_counts"][req.mbti.upper()] = (
                self._analytics["mbti_counts"].get(req.mbti.upper(), 0) + 1
            )
        try:
            # time_unknown + time_hint 조합: 시간대 힌트로 시:분 보정 + time_unknown 해제
            dt_local = req.dt_local
            time_unknown = req.time_unknown
            if req.time_unknown and req.time_hint:
                hour = self._TIME_HINT_HOUR.get(req.time_hint.lower())
                if hour is not None and "T" in dt_local:
                    date_part = dt_local.split("T")[0]
                    dt_local = f"{date_part}T{hour:02d}:00"
                    time_unknown = False
            result = await asyncio.to_thread(
                self.saju_cli.assess,
                dt_local=dt_local,
                tz=req.tz,
                longitude=req.longitude,
                latitude=req.latitude,
                is_lunar=req.is_lunar,
                is_leap_month=req.is_leap_month,
                time_unknown=time_unknown,
                gender=req.gender,
            )
            # 추정 시각 메타에 기록 (프론트엔드 표시용)
            if req.time_unknown and req.time_hint:
                result.setdefault("meta", {})["time_hint"] = req.time_hint
                result["meta"]["estimated_hour"] = self._TIME_HINT_HOUR.get(
                    req.time_hint.lower()
                )

            # 성명학 분석 (이름 입력 시) — 보완도 계산 후 result 에 첨부
            myeong = None
            if req.name_ko:
                try:
                    from engine.saju.myeong import analyze_name

                    myeong = await asyncio.to_thread(
                        analyze_name,
                        req.name_ko,
                        result.get("wuxing_dist"),
                        req.name_han,
                    )
                    result["myeong"] = myeong
                except Exception as e:
                    result["myeong_error"] = str(e)

            # 융합 별칭 v2 (이름 수식어 추가)
            if myeong and req.mbti:
                try:
                    from engine.saju.alias import compute_fusion_alias_v2

                    result["fusion_alias"] = compute_fusion_alias_v2(
                        result, req.mbti, myeong
                    )
                except Exception as e:
                    result["fusion_alias_error"] = str(e)

            if req.interpret:
                try:
                    if req.mbti:
                        from engine.saju.explain import explain_fusion_with_critic

                        fusion = await asyncio.to_thread(
                            explain_fusion_with_critic,
                            result,
                            req.mbti,
                            None,
                            2,
                            myeong,
                            req.lang,
                        )
                        result["interpretation"] = fusion["text"]
                        result["interpretation_meta"] = {
                            "rounds": fusion["rounds"],
                            "critic_history": fusion["critic_history"],
                        }
                    else:
                        from engine.saju.explain import explain_saju

                        interpretation = await asyncio.to_thread(explain_saju, result)
                        result["interpretation"] = interpretation
                except Exception as e:
                    result["interpretation_error"] = str(e)
            return result
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(400, str(e))

    async def post_saju_explain(self, req: SajuExplainRequest) -> dict[str, Any]:
        """카드별 부분 해설 (pillar/wuxing/tengods/luck/shensha)."""
        try:
            from engine.saju.explain import explain_section

            text = await asyncio.to_thread(
                explain_section, req.section, req.saju, None, req.context
            )
            return {"section": req.section, "text": text}
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_saju_fusion(self, req: SajuFusionRequest) -> dict[str, Any]:
        """사주 + MBTI 융합 해설 + 결정론적 융합 별칭."""
        try:
            from engine.saju.alias import compute_fusion_alias
            from engine.saju.explain import explain_fusion

            alias = compute_fusion_alias(req.saju, req.mbti)
            text = await asyncio.to_thread(
                explain_fusion, req.saju, req.mbti, None, None, req.lang
            )
            return {"mbti": req.mbti.upper(), "text": text, "alias": alias}
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_saju_music(self, req: SajuMusicRequest) -> dict[str, Any]:
        """페르소나 사운드트랙 — 가사 에이전트 + MiniMax music-2.6."""
        self._analytics["music_calls"] += 1
        try:
            from engine.saju.music_gen import generate_music_with_critic

            ctx = {
                "persona": req.persona,
                "mbti": req.mbti,
                "strongest_wuxing": req.strongest_wuxing,
                "weakest_wuxing": req.weakest_wuxing,
                "day_master": req.day_master,
                "name_ko": req.name_ko,
                "grids": req.grids,
            }
            result = await asyncio.to_thread(
                generate_music_with_critic, ctx, max_rounds=2
            )
            self._analytics[
                "cache_music_hit" if result.get("cached") else "cache_music_miss"
            ] += 1
            self._analytics["minimax_last_ok"] = time.time() if not result.get("cached") else self._analytics["minimax_last_ok"]
            return result
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_saju_compat_music(
        self, req: SajuCompatMusicRequest
    ) -> dict[str, Any]:
        """궁합 듀엣 사운드트랙 — 두 사람의 합/충/생/극을 한 곡에."""
        self._analytics["compat_music_calls"] += 1
        if req.grade:
            self._analytics["compat_grade_counts"][req.grade] = (
                self._analytics["compat_grade_counts"].get(req.grade, 0) + 1
            )
        try:
            from engine.saju.music_gen import generate_compat_music

            ctx = {
                "a_persona": req.a_persona,
                "b_persona": req.b_persona,
                "a_mbti": req.a_mbti,
                "b_mbti": req.b_mbti,
                "a_day_master": req.a_day_master,
                "b_day_master": req.b_day_master,
                "a_name_ko": req.a_name_ko,
                "b_name_ko": req.b_name_ko,
                "a_strongest_wuxing": req.a_strongest_wuxing,
                "b_strongest_wuxing": req.b_strongest_wuxing,
                "a_grids": req.a_grids,
                "b_grids": req.b_grids,
                "score": req.score,
                "grade": req.grade,
                "stem_rel": req.stem_rel,
                "branch_rel": req.branch_rel,
                "relation_mode": req.relation_mode,
            }
            result = await asyncio.to_thread(
                generate_compat_music, ctx, max_rounds=2
            )
            self._analytics[
                "cache_music_hit" if result.get("cached") else "cache_music_miss"
            ] += 1
            return result
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_saju_image(self, req: SajuImageRequest) -> dict[str, Any]:
        """Nano Banana 일러스트 — 프롬프트 에이전트가 입력 데이터 보고 작성."""
        if req.kind == "compat":
            self._analytics["compat_image_calls"] += 1
        else:
            self._analytics["image_calls"] += 1
        try:
            from engine.saju.image_gen import generate_image, smart_prompt

            ctx: dict[str, Any] = {}
            if req.kind == "persona" and req.alias:
                ctx["persona"] = req.alias.get("persona") or req.alias.get("headline")
                ctx["mbti"] = req.alias.get("mbti")
                ctx["strongest_wuxing"] = req.alias.get("strongest")
                ctx["weakest_wuxing"] = req.alias.get("weakest")
                ctx["day_master"] = (req.saju or {}).get("day_master")
            elif req.kind == "pillar" and req.saju:
                ctx["year"] = req.saju.get("year")
                ctx["month"] = req.saju.get("month")
                ctx["day"] = req.saju.get("day")
                ctx["hour"] = req.saju.get("hour")
                ctx["day_master"] = req.saju.get("day_master")
            elif req.kind == "wuxing" and req.saju:
                wx = req.saju.get("wuxing_dist", {})
                ctx["wuxing_distribution"] = ", ".join(f"{k}={v}" for k, v in wx.items())
                ctx["strongest"] = max(wx, key=lambda k: wx[k]) if wx else None
                ctx["weakest"] = min(wx, key=lambda k: wx[k]) if wx else None
            elif req.kind == "luck" and req.saju:
                lc = req.saju.get("luck_cycle", [])
                ctx["luck_first"] = lc[0] if lc else None
                ctx["luck_last"] = lc[-1] if lc else None
                ctx["day_master"] = req.saju.get("day_master")
            elif req.kind == "compat":
                ctx["score"] = req.compat_score or 50
                ctx["grade"] = req.compat_grade or "중"
                a = req.compat_a or {}
                b = req.compat_b or {}
                if a.get("persona"):
                    ctx["a_persona"] = a.get("persona")
                if b.get("persona"):
                    ctx["b_persona"] = b.get("persona")
                if a.get("mbti"):
                    ctx["a_mbti"] = a.get("mbti")
                if b.get("mbti"):
                    ctx["b_mbti"] = b.get("mbti")
                _STEM_EN = {
                    "甲": "Wood (tall upright tree)",
                    "乙": "Vine-Wood (flexible grass)",
                    "丙": "Sun-Fire (radiant)",
                    "丁": "Candle-Fire (intimate warmth)",
                    "戊": "Mountain-Earth (grounded)",
                    "己": "Field-Earth (nurturing soil)",
                    "庚": "Metal (sharp steel)",
                    "辛": "Jewel-Metal (refined gem)",
                    "壬": "Ocean-Water (vast flow)",
                    "癸": "Mist-Water (soft dew)",
                }
                if a.get("day_master"):
                    ctx["a_day_master"] = a.get("day_master")
                    ctx["a_element_en"] = _STEM_EN.get(a.get("day_master"), "")
                if b.get("day_master"):
                    ctx["b_day_master"] = b.get("day_master")
                    ctx["b_element_en"] = _STEM_EN.get(b.get("day_master"), "")
                if a.get("name_ko"):
                    ctx["a_name_ko"] = a.get("name_ko")
                if b.get("name_ko"):
                    ctx["b_name_ko"] = b.get("name_ko")
                if a.get("gender"):
                    ctx["a_gender"] = a.get("gender")
                if b.get("gender"):
                    ctx["b_gender"] = b.get("gender")
                if req.compat_stem_rel:
                    ctx["stem_rel"] = req.compat_stem_rel
                if req.compat_branch_rel:
                    ctx["branch_rel"] = req.compat_branch_rel
            else:
                raise HTTPException(400, f"invalid kind or missing data: {req.kind}")

            from engine.saju.image_gen import generate_image_with_critic

            prompt = await asyncio.to_thread(smart_prompt, req.kind, ctx)
            result = await asyncio.to_thread(
                generate_image_with_critic, prompt, ctx, max_rounds=2
            )
            self._analytics[
                "cache_image_hit" if result.get("cached") else "cache_image_miss"
            ] += 1
            # critic 통계
            hist = result.get("critic_history") or []
            if hist:
                last = hist[-1]
                if last.get("total"):
                    self._analytics["image_critic_totals"].append(last["total"])
                    # 최근 100개만 유지
                    self._analytics["image_critic_totals"] = self._analytics["image_critic_totals"][-100:]
                self._analytics["image_critic_rounds"].append(len(hist))
                self._analytics["image_critic_rounds"] = self._analytics["image_critic_rounds"][-100:]
            return {"kind": req.kind, "prompt": prompt, **result}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_hanja_candidates(
        self, ko: str, weak: str = "", strong: str = ""
    ) -> dict[str, Any]:
        """한글 음 → 후보 한자 리스트 (음/획수/자원오행/뜻).

        weak: 사주의 약한 오행 (목/화/토/금/수). 해당 오행 한자에 `recommended=True` 부여.
        strong: 사주의 강한 오행. 해당 오행 한자에 `overload=True` 부여 (과한 보강 경고).
        """
        try:
            from engine.saju.hanja_data import candidates_by_ko

            cands = candidates_by_ko(ko)
            for c in cands:
                wx = c.get("wuxing") or c.get("자원오행") or ""
                if weak and wx == weak:
                    c["recommended"] = True
                if strong and wx == strong:
                    c["overload"] = True
            # 추천 한자를 앞으로 정렬
            cands.sort(
                key=lambda c: (not c.get("recommended"), c.get("overload", False))
            )
            return {"ko": ko, "candidates": cands}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def _assess_person(self, p) -> dict[str, Any]:
        """SajuCompatPerson → SajuCLI assess + myeong 분석."""
        result = await asyncio.to_thread(
            self.saju_cli.assess,
            dt_local=p.dt_local,
            tz=p.tz,
            longitude=p.longitude,
            latitude=p.latitude,
            is_lunar=p.is_lunar,
            is_leap_month=p.is_leap_month,
            time_unknown=p.time_unknown,
            gender=p.gender,
        )
        myeong = None
        if p.name_ko:
            try:
                from engine.saju.myeong import analyze_name

                myeong = await asyncio.to_thread(
                    analyze_name, p.name_ko, result.get("wuxing_dist"), p.name_han
                )
                result["myeong"] = myeong
            except Exception as e:
                result["myeong_error"] = str(e)
        return result

    async def post_saju_compat(self, req: SajuCompatRequest) -> dict[str, Any]:
        """두 사람 사주 + MBTI + 이름 → 궁합 분석."""
        try:
            from engine.saju.compat import analyze_compat
            from engine.saju.explain import explain_compat

            saju_a = await self._assess_person(req.a)
            saju_b = await self._assess_person(req.b)
            compat = analyze_compat(
                saju_a,
                saju_b,
                mbti_a=req.a.mbti,
                mbti_b=req.b.mbti,
                myeong_a=saju_a.get("myeong"),
                myeong_b=saju_b.get("myeong"),
            )
            interpretation = None
            if req.interpret:
                try:
                    interpretation = await asyncio.to_thread(
                        explain_compat, compat, None, req.relation_mode, req.lang
                    )
                except Exception as e:
                    interpretation = f"(궁합 해설 생성 실패: {e})"
            return {
                "a": {
                    "day_master": saju_a.get("day_master"),
                    "day": saju_a.get("day"),
                    "myeong": saju_a.get("myeong"),
                    "mbti": req.a.mbti,
                    "name_ko": req.a.name_ko,
                    "gender": req.a.gender,
                    "alias": saju_a.get("alias"),
                },
                "b": {
                    "day_master": saju_b.get("day_master"),
                    "day": saju_b.get("day"),
                    "myeong": saju_b.get("myeong"),
                    "mbti": req.b.mbti,
                    "name_ko": req.b.name_ko,
                    "gender": req.b.gender,
                    "alias": saju_b.get("alias"),
                },
                "compat": compat,
                "interpretation": interpretation,
                "relation_mode": req.relation_mode,
            }
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_saju_compat_batch(
        self, req: SajuCompatBatchRequest
    ) -> dict[str, Any]:
        """한 명(a) vs 여러 명(others) — 점수만 비교 표로 반환."""
        try:
            from engine.saju.compat import analyze_compat

            saju_a = await self._assess_person(req.a)
            # 친구들 사주 계산을 병렬화 (gather)
            others = req.others[:10]

            async def _process(b):
                try:
                    saju_b = await self._assess_person(b)
                    c = analyze_compat(
                        saju_a, saju_b,
                        mbti_a=req.a.mbti, mbti_b=b.mbti,
                        myeong_a=saju_a.get("myeong"),
                        myeong_b=saju_b.get("myeong"),
                    )
                    return {
                        "name_ko": b.name_ko,
                        "mbti": b.mbti,
                        "day_master": saju_b.get("day_master"),
                        "score": c.get("score"),
                        "grade": c.get("grade"),
                    }
                except Exception as e:
                    return {"name_ko": b.name_ko, "error": str(e)}

            rows = list(await asyncio.gather(*(_process(b) for b in others)))
            rows.sort(key=lambda r: -(r.get("score") or 0))
            return {
                "a": {
                    "name_ko": req.a.name_ko,
                    "mbti": req.a.mbti,
                    "day_master": saju_a.get("day_master"),
                },
                "rows": rows,
            }
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_saju_myeong(self, req: SajuMyeongRequest) -> dict[str, Any]:
        """성명학 결정론적 분석 — 음령오행 + 수리오격 + 사주 보완도."""
        try:
            from engine.saju.myeong import analyze_name

            return await asyncio.to_thread(
                analyze_name, req.name_ko, req.saju_wuxing, req.name_han
            )
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_tarot(self, req: TarotRequest) -> dict[str, Any]:
        if self.engine is None:
            raise HTTPException(503, "tarot 모듈은 본 배포에서 비활성화됨")
        try:
            return await self.engine.cast_tarot_async(
                req.question, req.spread, req.seed
            )
        except Exception as e:
            raise HTTPException(400, str(e))

    async def post_iching(self, req: IChingRequest) -> dict[str, Any]:
        if self.engine is None:
            raise HTTPException(503, "iching 모듈은 본 배포에서 비활성화됨")
        try:
            return await self.engine.cast_iching_async(req.question, req.seed)
        except Exception as e:
            raise HTTPException(400, str(e))

    async def post_assess_all(self, req: AssessAllRequest) -> dict[str, Any]:
        """9 시스템 병렬 평가 — Engine.assess_all_async 직접 위임."""
        if self.engine is None:
            raise HTTPException(503, "assess_all 모듈은 본 배포에서 비활성화됨")
        try:
            saju_kwargs: dict[str, Any] | None = None
            if req.saju:
                saju_kwargs = {
                    "dt_local": datetime.fromisoformat(req.saju.dt_local),
                    "tz": req.saju.tz,
                    "longitude": req.saju.longitude,
                    "latitude": req.saju.latitude,
                    "is_lunar": req.saju.is_lunar,
                    "is_leap_month": req.saju.is_leap_month,
                    "time_unknown": req.saju.time_unknown,
                    "gender": req.saju.gender,
                }
            result = await self.engine.assess_all_async(
                nl_text=req.nl_text,
                saju_kwargs=saju_kwargs,
                oracle_question=req.oracle_question,
                oracle_seed=req.oracle_seed,
            )
            return result.to_dict()
        except Exception as e:
            raise HTTPException(400, str(e))

    async def get_profile(self, type_: str) -> dict[str, Any]:
        type_ = type_.upper()
        if type_ in self._MBTI_TYPES:
            try:
                from mbti.profiles.lookup import profile_for

                profile = await asyncio.to_thread(profile_for, type_)
                return profile.to_dict()
            except KeyError:
                pass
        raise HTTPException(404, f"unknown type: {type_}")

    async def get_health(self) -> dict[str, Any]:
        # 외부 API 키 존재 점검 (실제 ping은 비용/지연 때문에 skip)
        ext = {
            "minimax_api_key_set": bool(os.environ.get("MINIMAX_API_KEY", "").strip()),
            "bizrouter_api_key_set": bool(os.environ.get("BIZROUTER_API_KEY", "").strip()),
            # BizRouter 장애 시 LLM 폴백 가능 여부 진단용.
            "anthropic_api_key_set": bool(os.environ.get("ANTHROPIC_API_KEY", "").strip()),
            "rate_limit_per_min": self._rate_limit_per_min,
        }
        if self.engine is None:
            return {"status": "ok", "engine_config": {"mode": "saju-only"}, "external": ext}
        return {
            "status": "ok",
            "engine_config": {
                "parallel": self.engine.config.parallel,
                "enable_llm": self.engine.config.enable_llm,
            },
            "external": ext,
        }

    async def get_metrics(self) -> dict[str, Any]:
        m = self._metrics
        total = m["requests_total"] or 1
        samples = sorted(m["duration_samples"])

        def percentile(p: float) -> float:
            if not samples:
                return 0.0
            idx = min(len(samples) - 1, int(len(samples) * p))
            return samples[idx]

        return {
            "requests_total": m["requests_total"],
            "errors_total": m["errors_total"],
            "error_rate": m["errors_total"] / total,
            "avg_duration_ms": m["duration_sum_ms"] / total,
            "p50_ms": percentile(0.5),
            "p95_ms": percentile(0.95),
            "p99_ms": percentile(0.99),
            "sample_count": len(samples),
        }

    async def get_saju_daily(self, day_master: str = "", date: str = "") -> dict[str, Any]:
        """오늘(또는 지정 날짜) 일진 + 본명 일간과의 십신 관계.

        Args:
            day_master: 본명 일간 한자 (甲~癸). 없으면 일진만 반환.
            date: YYYY-MM-DD (없으면 KST 오늘).

        일주 경계(자시) 회피를 위해 정오(12시) 기준으로 만세력 계산.
        """
        from datetime import datetime, timezone, timedelta
        from engine.saju.pillars import compute_pillars
        from engine.saju.ten_gods import ten_god

        kst = timezone(timedelta(hours=9))
        try:
            d = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now(kst)
        except Exception:
            d = datetime.now(kst)
        # 일주 경계 회피 위해 정오 12시
        pillars = compute_pillars(d.year, d.month, d.day, 12)
        dp = pillars["day_pillar"]
        result: dict[str, Any] = {
            "date": d.strftime("%Y-%m-%d"),
            "day_pillar": {
                "ganzhi_ko": f"{dp.get('gan','')}{dp.get('ji','')}",
                "ganzhi_han": f"{dp.get('gan_han','')}{dp.get('ji_han','')}",
                "gan_han": dp.get("gan_han"),
                "ji_han": dp.get("ji_han"),
            },
            "month_pillar": pillars["month_pillar"],
            "year_pillar": pillars["year_pillar"],
        }
        if day_master and day_master in "甲乙丙丁戊己庚辛壬癸":
            today_gan = dp.get("gan_han")
            relation = ten_god(day_master, today_gan) if today_gan else None
            result["relation"] = relation
            result["natal_day_master"] = day_master
            # 한 줄 톤 가이드
            tone_map = {
                "비견": "협력자·동지의 기운. 사람과 함께 움직이기 좋은 날.",
                "겁재": "경쟁·도전의 기운. 경계심 갖고 자기 입장을 지킬 것.",
                "식신": "베풂·창작의 기운. 표현·요리·여유 시간에 좋음.",
                "상관": "재능·반항의 기운. 새로운 시도가 빛나지만 규칙 충돌 주의.",
                "편재": "기회·확장의 기운. 외부 활동과 인맥에 좋음.",
                "정재": "안정·정착의 기운. 재산·관리·꼼꼼한 일에 좋음.",
                "편관": "압박·도전 과제. 결단력 필요한 날, 무리는 금물.",
                "정관": "질서·책임의 기운. 공식 일정·약속·계약에 좋음.",
                "편인": "직관·영감의 기운. 학습·명상·아이디어에 좋음.",
                "정인": "보호·인덕의 기운. 부모·스승·도움을 받는 날.",
            }
            result["tone"] = tone_map.get(relation, "")
        return result

    async def get_saju_daily_month(
        self, day_master: str = "", year: int = 0, month: int = 0
    ) -> dict[str, Any]:
        """한 달 일진 캘린더 — 본명 일간 기준 길흉 분류.

        길(吉) = 정관·정재·정인·식신, 평(平) = 비견·편재, 흉(凶) = 겁재·편관·상관·편인.
        """
        from datetime import datetime, timezone, timedelta
        from calendar import monthrange
        from engine.saju.pillars import compute_pillars
        from engine.saju.ten_gods import ten_god

        kst = timezone(timedelta(hours=9))
        now = datetime.now(kst)
        y = int(year) if year else now.year
        m = int(month) if month else now.month
        last_day = monthrange(y, m)[1]
        TONE = {
            "정관": "길", "정재": "길", "정인": "길", "식신": "길",
            "비견": "평", "편재": "평",
            "겁재": "흉", "편관": "흉", "상관": "흉", "편인": "흉",
        }
        days: list[dict[str, Any]] = []
        best_day = None
        worst_day = None
        for d in range(1, last_day + 1):
            try:
                pillars = compute_pillars(y, m, d, 12)
                gan = pillars["day_pillar"]["gan_han"]
                ji = pillars["day_pillar"]["ji_han"]
                rel = ten_god(day_master, gan) if day_master else None
                tone = TONE.get(rel, "평") if rel else "평"
                days.append({
                    "day": d,
                    "ganzhi": f"{gan}{ji}",
                    "relation": rel,
                    "tone": tone,
                })
                if rel == "정관" or rel == "정인":
                    if not best_day:
                        best_day = d
                if rel == "편관" or rel == "겁재":
                    if not worst_day:
                        worst_day = d
            except Exception:
                pass
        return {
            "year": y,
            "month": m,
            "day_master": day_master,
            "days": days,
            "best_day": best_day,
            "worst_day": worst_day,
        }

    async def post_saju_ask(self, req: SajuAskRequest) -> dict[str, Any]:
        """사주 페르소나에게 질문 — 사주 데이터를 컨텍스트로 LLM 대화. 세션당 10턴 제한."""
        from engine.saju.explain import MAX_CHAT_TURNS
        from engine.safety import detect_crisis, CRISIS_RESPONSE_KO, EMERGENCY_HOTLINES_KR, build_legal_footer

        # 0. 위기 신호 검사 — 자살/자해 키워드 즉시 차단
        crisis = detect_crisis(req.question or "")
        if crisis["crisis_detected"]:
            return {
                "answer": CRISIS_RESPONSE_KO + build_legal_footer(is_crisis=True),
                "lang": req.lang,
                "turns_used": sum(1 for m in (req.history or []) if (m or {}).get("role") == "user") + 1,
                "turns_max": MAX_CHAT_TURNS,
                "crisis_alert": {
                    "severity": crisis["severity"],
                    "hotlines": EMERGENCY_HOTLINES_KR,
                    "matched_count": len(crisis["matched_keywords"]),
                },
                "legal_notice": None,
            }

        # 턴 수 체크 — 1턴 = user/assistant 한 쌍 (2 메시지)
        user_turns = sum(1 for m in (req.history or []) if (m or {}).get("role") == "user")
        if user_turns >= MAX_CHAT_TURNS:
            return {
                "answer": (
                    f"한 세션 최대 {MAX_CHAT_TURNS}개 질문까지 지원합니다. "
                    "새 분석을 시작하면 다시 대화할 수 있어요."
                ),
                "lang": req.lang,
                "limited": True,
            }
        try:
            from engine.llm_sync import call_llm_sync

            saju = req.saju
            day_master = saju.get("day_master")
            wx = saju.get("wuxing_dist") or {}
            strongest = max(wx, key=lambda k: wx.get(k, 0)) if wx else None
            weakest = min(wx, key=lambda k: wx.get(k, 0)) if wx else None
            alias = saju.get("alias") or {}
            ctx_lines = (
                f"[사용자 사주 컨텍스트]\n"
                f"  • 일간: {day_master}\n"
                f"  • 강한 오행: {strongest}, 약한 오행: {weakest}\n"
                f"  • 4기둥: {saju.get('year')} {saju.get('month')} {saju.get('day')} {saju.get('hour')}\n"
                f"  • 페르소나: {alias.get('persona', '')}\n"
            )
            lang_directive = {
                "en": "Answer in natural English.",
                "ja": "自然な日本語で回答してください。",
            }.get(req.lang, "한국어로 답변하세요.")
            system = (
                f"당신은 위 사주 데이터를 가진 사용자의 사주 페르소나 입장에서 답변하는 명리 상담사입니다.\n"
                f"엄격한 가드레일:\n"
                f"  • **단정적 예언 절대 금지**: '~가 좋다/나쁘다', '~할 것이다', '~이다' 같은 단언 X.\n"
                f"  • 대신 '~경향이 있다', '~을 점검해보면 좋다', '~흐름이 두드러진다' 같은 경향성 표현.\n"
                f"  • 점쟁이 톤 금지 (재물운/금전수/대박/대운 폭발 같은 자극 어휘 금지).\n"
                f"  • 의료/법률/투자 자문 거절 ('전문가 상담 권장').\n"
                f"  • 답변은 3~5문장, 통찰적·따뜻한 톤.\n"
                f"  • 사주는 한 가지 관점일 뿐이며 본인 판단이 최종임을 자연스럽게 환기.\n\n"
                f"{lang_directive}\n\n{ctx_lines}"
            )
            # 이전 대화 + 새 질문 (최근 6개만)
            messages_text = ""
            for m in (req.history or [])[-6:]:
                role = m.get("role", "user")
                content = m.get("content", "")
                messages_text += f"[{role}] {content}\n"
            messages_text += f"[user] {req.question}\n[assistant] "
            answer = await asyncio.to_thread(
                call_llm_sync, user_text=messages_text, system_prompt=system
            )
            return {
                "answer": (answer or "").strip(),
                "lang": req.lang,
                "turns_used": user_turns + 1,
                "turns_max": MAX_CHAT_TURNS,
                "crisis_alert": None,
                "legal_notice": build_legal_footer(),
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_service_worker(self) -> Any:
        """Service Worker 응답 — 매 배포마다 캐시 무효화 위해 버전 자동 증가.

        SW_VERSION env var이 있으면 사용, 없으면 서버 시작 시각 기반 fallback.
        """
        from fastapi.responses import Response

        version = os.environ.get("SW_VERSION") or os.environ.get("RAILWAY_DEPLOYMENT_ID")
        if not version:
            # 서버 부팅 시각 한 번 (인스턴스 lifecycle 동안 고정)
            if not hasattr(self, "_sw_version"):
                self._sw_version = str(int(time.time()))
            version = self._sw_version
        # front/sw.js 우선, 없으면 web/sw.js fallback
        front_sw = Path(__file__).resolve().parent.parent / "front" / "sw.js"
        web_sw = Path(__file__).resolve().parent / "sw.js"
        sw_path = front_sw if front_sw.exists() else web_sw
        try:
            body = sw_path.read_text(encoding="utf-8")
        except Exception:
            body = ""
        # 캐시 이름의 v1 → 동적 버전
        body = body.replace("saju-app-shell-v1", f"saju-app-shell-{version}")
        return Response(
            content=body,
            media_type="text/javascript; charset=utf-8",
            headers={"Cache-Control": "no-cache"},
        )

    async def post_llm_chat(self, req: LLMChatRequest) -> Any:
        """raw prompt → Bizrouter Gemini Flash Lite. 스트리밍 chunk text 응답.

        front 의 callFreeAI(prompt) 호환 — Pollinations 대체.
        """
        from fastapi.responses import StreamingResponse
        from engine.llm_sync import bizrouter_client

        client = bizrouter_client()
        system = req.system or (
            "당신은 따뜻하고 깊이 있는 사주·운명학 풀이 작가입니다. "
            "단정적 예언 금지, 경향성·자기이해 위주. 점쟁이 톤 금지. "
            "한국어로 자연스럽게 작성하세요."
        )
        # 요청에 model이 명시되면 우선 사용(클라이언트 모델 선택 허용), 없으면 env 기본.
        bizrouter_model = req.model or os.environ.get(
            "BIZROUTER_MODEL", "google/gemini-2.5-flash-lite"
        )

        if not req.stream:
            # 비스트리밍 — 단일 JSON 응답
            try:
                resp = await asyncio.to_thread(
                    client.chat.completions.create,
                    model=bizrouter_model,
                    max_tokens=req.max_tokens,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": req.prompt},
                    ],
                )
                content = resp.choices[0].message.content or ""
                return {"text": content}
            except Exception as e:
                raise HTTPException(500, str(e))

        # 스트리밍 — text/plain chunks (OpenAI SDK stream=True)
        async def _gen():
            try:
                stream = await asyncio.to_thread(
                    client.chat.completions.create,
                    model=bizrouter_model,
                    max_tokens=req.max_tokens,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": req.prompt},
                    ],
                    stream=True,
                )
                for chunk in stream:
                    try:
                        delta = chunk.choices[0].delta
                        piece = getattr(delta, "content", None) or ""
                        if piece:
                            yield piece
                    except Exception:
                        continue
            except Exception as e:
                yield f"\n\n[스트리밍 오류: {e}]"

        return StreamingResponse(_gen(), media_type="text/plain; charset=utf-8")

    async def post_manwol_reading(self, req: ManwolReadingRequest) -> Any:
        """만월아씨 통합 서사 — 사주 + 이름 + 관상/꿈/자미/타로/생활/고민 → 심야 방송 반말 산문.

        시스템 프롬프트는 서버 고정 (engine/divination/manwol_reading.MANWOL_SYSTEM).
        결정론 페이로드를 build_manwol_user_prompt 로 자연 문장으로 구조화 후 LLM 스트리밍.
        face_photo_base64 가 있으면 OpenAI-호환 multimodal content 로 이미지 첨부 → Sonnet Vision.
        """
        from fastapi.responses import StreamingResponse
        from engine.llm_sync import bizrouter_client
        from engine.divination.manwol_reading import (
            MANWOL_SYSTEM,
            build_manwol_user_prompt,
        )

        payload = req.model_dump()
        # 이미지는 별도로 처리. text 프롬프트에 base64 를 넣지 않는다.
        face_b64 = payload.pop("face_photo_base64", None)
        # 이미지 준비 (data URL 로 정규화)
        image_url: str | None = None
        if face_b64 and isinstance(face_b64, str):
            b = face_b64.strip()
            # 이미 data URL 이면 그대로
            if b.startswith("data:"):
                image_url = b
            else:
                # raw base64 — 기본 jpeg 로 wrap
                # 길이 검사 (5MB 안팎 · base64 7MB)
                if len(b) < 7 * 1024 * 1024:
                    image_url = f"data:image/jpeg;base64,{b}"
        # face_photo 플래그를 prompt builder 에 남겨두고 (프롬프트에 안내 포함)
        if image_url:
            payload["face_photo_base64"] = "PRESENT"

        user_prompt = build_manwol_user_prompt(payload)

        # 만월아씨 서사는 톤·통합력이 중요 → 이전 사주 웹툰이 사용하던 Sonnet 4.6 고정.
        # 환경변수 override 로 다운그레이드 가능.
        bizrouter_model = os.environ.get(
            "MANWOL_MODEL", "anthropic/claude-sonnet-4.6"
        )
        client = bizrouter_client()

        # 이미지 있으면 multimodal content, 없으면 plain text
        if image_url:
            user_content: Any = [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]
        else:
            user_content = user_prompt

        if not req.stream:
            try:
                resp = await asyncio.to_thread(
                    client.chat.completions.create,
                    model=bizrouter_model,
                    max_tokens=req.max_tokens,
                    messages=[
                        {"role": "system", "content": MANWOL_SYSTEM},
                        {"role": "user", "content": user_content},
                    ],
                )
                content = resp.choices[0].message.content or ""
                return {"text": content}
            except Exception as e:
                raise HTTPException(500, str(e))

        async def _gen():
            try:
                stream = await asyncio.to_thread(
                    client.chat.completions.create,
                    model=bizrouter_model,
                    max_tokens=req.max_tokens,
                    messages=[
                        {"role": "system", "content": MANWOL_SYSTEM},
                        {"role": "user", "content": user_content},
                    ],
                    stream=True,
                )
                for chunk in stream:
                    try:
                        delta = chunk.choices[0].delta
                        piece = getattr(delta, "content", None) or ""
                        if piece:
                            yield piece
                    except Exception:
                        continue
            except Exception as e:
                yield f"\n\n[스트리밍 오류: {e}]"

        return StreamingResponse(_gen(), media_type="text/plain; charset=utf-8")

    async def post_hwapae_reading(
        self, req: HwapaeReadingRequest
    ) -> dict[str, Any]:
        """화선 낭자 화패 풀이 — critic 루프 + 캐시 적용 백엔드 에이전트."""
        try:
            from engine.divination.hwapae.core import generate_hwapae_reading

            cards = [c.model_dump() for c in req.cards]
            result = await asyncio.to_thread(
                generate_hwapae_reading,
                req.question,
                cards,
                req.category,
                req.menu_label,
            )
            # ADR-006/094 단정 어휘 + ADR-115 다국어 hallucination 사후 필터링
            if isinstance(result, dict) and "text" in result:
                result["text"] = _sanitize_common_assertion_words(result["text"])
                result["text"] = _sanitize_foreign_hallucination(result["text"])
                result["text"] = _sanitize_korean_grammar_dupes(result["text"])
            return result
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_face_reading(
        self, req: FaceReadingRequest
    ) -> dict[str, Any]:
        """운학 도사 얼굴 풀이 — Gemini Vision 멀티모달 호출 + 캐시.

        ADR-035 (Phase 3회차): 5MB 초과 시 HTTP 413 명확 오류 반환.
        base64 길이 사전 검사 (7MB ≈ 5MB 바이너리) → 조기 차단.
        """
        # 서버측 이미지 크기 안전망 — 5MB 바이너리 ≈ base64 7MB
        _MAX_B64_LEN = 7 * 1024 * 1024  # 7_340_032 chars
        raw_b64 = req.image_base64 or ""
        # data URL prefix 제거 후 길이 체크
        b64_body = raw_b64.split(",", 1)[-1] if "," in raw_b64 else raw_b64
        if len(b64_body) > _MAX_B64_LEN:
            raise HTTPException(
                status_code=413,
                detail="이미지가 너무 큽니다 — 5MB 이하 JPG/PNG/WEBP로 변환 후 업로드해주세요.",
            )

        try:
            from engine.divination.face.reading import generate_face_reading

            # ADR-274 — 학파 선택 메타를 metrics에 주입 (face/reading.py 시스템 프롬프트 분기)
            _metrics_with_school = dict(req.metrics or {}) if req.metrics else {}
            if req.school:
                _metrics_with_school["physiognomy_school"] = req.school
            result = await asyncio.to_thread(
                generate_face_reading,
                req.image_base64,
                req.age,
                req.gender,
                req.question,
                _metrics_with_school if _metrics_with_school else None,
            )

            # ADR-273 — 관상 12궁 + 5악 시각화 오버레이
            try:
                face_keypoints = None
                if req.metrics and isinstance(req.metrics, dict):
                    face_keypoints = req.metrics.get("face_keypoints")
                if face_keypoints and req.image_base64:
                    from engine.divination.face.visualization import overlay_face_analysis
                    from PIL import Image as _PILImg
                    from io import BytesIO as _BIO
                    import base64 as _b64m
                    import numpy as _npm
                    _s = req.image_base64
                    if "," in _s and _s.startswith("data:"):
                        _s = _s.split(",", 1)[1]
                    img_bytes = _b64m.b64decode(_s)
                    pil_img = _PILImg.open(_BIO(img_bytes)).convert("RGB")
                    img_arr = _npm.asarray(pil_img)
                    fviz = await asyncio.to_thread(
                        overlay_face_analysis,
                        img_arr, face_keypoints, None, True, True, False,
                    )
                    if isinstance(result, dict):
                        result["visualization"] = {
                            "image_base64": fviz.image_base64,
                            "width": fviz.width,
                            "height": fviz.height,
                            "n_palaces_drawn": fviz.n_palaces_drawn,
                            "metadata": fviz.metadata,
                        }
            except Exception:
                pass

            # ADR-006/094 단정 어휘 + ADR-115 다국어 hallucination 사후 필터링
            # (face Vision API 직접 호출 경로 — content/reading 분기 우회)
            if isinstance(result, dict) and "text" in result:
                result["text"] = _sanitize_common_assertion_words(result["text"])
                result["text"] = _sanitize_foreign_hallucination(result["text"])
                result["text"] = _sanitize_korean_grammar_dupes(result["text"])
            # LLM 출력 운영 모니터링 — 1% 샘플링, 사용자 영향 0
            try:
                from engine.safety.llm.output_sampler import sample_llm_output
                sample_llm_output("face_reading", result.get("text", ""))
            except Exception:
                pass  # silent
            return result
        except ValueError as ve:
            raise HTTPException(400, str(ve))
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_palm_diagnostics(self) -> dict[str, Any]:
        """ADR-242 — 손금 U-Net/CFM 가중치 활성화 진단 (라이브 검증용).

        반환: PyTorch 가용·가중치 경로·파일 크기·모델 유형(CFM/UNet)·상태.
        Vision LLM 호출 없이 가벼움.
        """
        try:
            import os as _os
            from engine.divination.palm.unet_line_extractor import check_unet_availability
            avail = check_unet_availability()
            weights_size = None
            model_type = "unknown"
            state_keys_sample: list[str] = []
            if avail.model_weights_path and _os.path.exists(avail.model_weights_path):
                weights_size = _os.path.getsize(avail.model_weights_path)
                # ADR-253 — .onnx 경로면 ONNX 메타 추출, 아니면 .pt state_dict
                if avail.model_weights_path.endswith(".onnx"):
                    try:
                        import onnx as _onnx
                        m = _onnx.load(avail.model_weights_path)
                        names = [init.name for init in m.graph.initializer]
                        state_keys_sample = names[:6]
                        is_cfm = any(
                            "cfm" in k or "branch" in k
                            or ("attention" in k and "psi" in k)
                            for k in names
                        )
                        model_type = "cfm-onnx" if is_cfm else "unet-onnx"
                    except Exception as e:
                        model_type = f"onnx_meta_error: {type(e).__name__}"
                elif avail.pytorch_available:
                    try:
                        import torch as _torch
                        state = _torch.load(
                            avail.model_weights_path,
                            map_location="cpu",
                            weights_only=True,
                        )
                        if isinstance(state, dict) and "state_dict" in state:
                            state = state["state_dict"]
                        if isinstance(state, dict):
                            keys = list(state.keys())
                            state_keys_sample = keys[:6]
                            is_cfm = any(
                                "cfm" in k or "branch" in k
                                or ("attention" in k and "psi" in k)
                                for k in keys
                            )
                            model_type = "cfm" if is_cfm else "unet"
                    except Exception as e:
                        model_type = f"load_error: {type(e).__name__}"
            return {
                "pytorch_available": avail.pytorch_available,
                "model_weights_path": avail.model_weights_path,
                "model_loadable": avail.model_loadable,
                "fallback_reason": avail.fallback_reason,
                "weights_size_bytes": weights_size,
                "model_type": model_type,
                "state_keys_sample": state_keys_sample,
            }
        except Exception as e:
            return {"error": str(e), "type": type(e).__name__}

    async def post_palm_reading(
        self, req: PalmReadingRequest
    ) -> dict[str, Any]:
        """옥선 할미 손금 풀이 — Vision 멀티모달 + ADR-160 MediaPipe 결정론 점수."""
        try:
            from engine.divination.palm.reading import generate_palm_reading

            # ADR-160 — MediaPipe Hand 21 keypoint 입력 시 결정론 점수 산출.
            # 산출 실패·keypoint 부재 시 LLM Vision 단독 유지 (무회귀).
            palm_deterministic_block = None
            palm_visualization = None  # ADR-259 시각화 오버레이

            # ADR-261 — keypoints 부재 시도 CFM 마스크 단독 시각화 (마스크 + 영역 박스만).
            # MediaPipe 추출 실패한 사용자도 모델 검출 결과 시각 확인 가능.
            if (palm_visualization is None
                    and req.image_base64
                    and not (req.metrics and isinstance(req.metrics, dict)
                             and isinstance(req.metrics.get("keypoints"), dict)
                             and any(k.startswith("kp") for k in req.metrics.get("keypoints", {})))):
                try:
                    from PIL import Image as _PILImg
                    from io import BytesIO as _BIO
                    import base64 as _b64_mod
                    import numpy as _np_mod
                    # ADR-261 fix — data URL prefix ("data:image/jpeg;base64,") 제거
                    _img_str = req.image_base64
                    if "," in _img_str and _img_str.startswith("data:"):
                        _img_str = _img_str.split(",", 1)[1]
                    img_bytes = _b64_mod.b64decode(_img_str)
                    pil_img = _PILImg.open(_BIO(img_bytes)).convert("RGB")
                    img_array_solo = _np_mod.asarray(pil_img)

                    from engine.divination.palm.unet_line_extractor import (
                        extract_palm_lines_best_available,
                    )
                    from engine.divination.palm.visualization import overlay_palm_analysis
                    cfm_r = await asyncio.to_thread(
                        extract_palm_lines_best_available, img_array_solo,
                    )
                    if cfm_r and cfm_r.used_unet and cfm_r.mask is not None:
                        # ADR-271 — keypoint 부재 시 곱선/라벨 미표시.
                        # 표준 비율로 그린 곱선이 손 위치와 무관해 잘못된 시각화 차단.
                        # CFM 마스크만 보여줘 모델 검출 결과만 표시.
                        viz_solo = await asyncio.to_thread(
                            overlay_palm_analysis,
                            img_array_solo, None, cfm_r.mask, None, cfm_r.raw_metrics,
                            0.4, False, True, False,  # show_keypoints=False, show_mask=True, show_regions=False
                        )
                        palm_visualization = {
                            "image_base64": viz_solo.image_base64,
                            "width": viz_solo.width,
                            "height": viz_solo.height,
                            "n_keypoints": 0,
                            "has_cfm_mask": viz_solo.has_cfm_mask,
                            "metadata": viz_solo.metadata,
                            "keypoint_mode": "absent",
                        }
                except Exception:
                    pass

            if req.metrics and isinstance(req.metrics, dict):
                keypoints = req.metrics.get("keypoints")
                if isinstance(keypoints, dict) and any(k.startswith("kp") for k in keypoints):
                    try:
                        # ADR-250 — score_palm_with_cfm: keypoint + CFM 마스크 결합.
                        # image 디코드 성공 시 CFM 가중 결합, 실패 시 keypoint-only fallback.
                        from engine.divination.palm.scoring import score_palm_with_cfm
                        hand_side = req.hand or req.metrics.get("hand_side_mp") or "unknown"

                        # base64 → numpy (PIL 사용, 가벼움)
                        img_array = None
                        if req.image_base64:
                            try:
                                from PIL import Image
                                from io import BytesIO
                                import base64 as _b64
                                import numpy as _np
                                # ADR-261 fix — data URL prefix 제거
                                _b64_str = req.image_base64
                                if "," in _b64_str and _b64_str.startswith("data:"):
                                    _b64_str = _b64_str.split(",", 1)[1]
                                img_bytes = _b64.b64decode(_b64_str)
                                pil_img = Image.open(BytesIO(img_bytes)).convert("RGB")
                                img_array = _np.asarray(pil_img)
                            except Exception:
                                img_array = None

                        palm_report = await asyncio.to_thread(
                            score_palm_with_cfm, keypoints, img_array, hand_side,
                        )
                        # 결정론 점수 메타를 system prompt 주입용 블록으로 압축.
                        lines_summary = " · ".join(
                            f"{ls.name}({ls.label_ko or ls.label}/{ls.score:.2f})"
                            for ls in palm_report.lines.values()
                        )
                        cfm_used = palm_report.metadata.get("cfm_used", False)
                        adr_tag = "ADR-250 CFM 융합" if cfm_used else "ADR-160 keypoint only"
                        palm_deterministic_block = (
                            f"[손금 결정론 — {adr_tag}]\n"
                            f"  · 손 측: {palm_report.hand_side}\n"
                            f"  · 4 손금선 + 금성대 점수: {lines_summary}\n"
                            f"  · CFM 마스크 결합: {'YES (UNetCFM, F1 0.86 baseline)' if cfm_used else 'NO (image 부재 또는 모델 미가용)'}\n"
                            f"[안전 장치 — ADR-006/113] 결정론 점수만 인용. "
                            f"수명·재물·운명 단정 금지. 형태 분류 메타로만 풀이.\n"
                            f"{palm_report.disclaimer_ko}"
                        )

                        # ADR-259 — 손금 시각화 오버레이 생성 (img_array + cfm 가용 시).
                        if cfm_used and img_array is not None:
                            try:
                                from engine.divination.palm.visualization import (
                                    overlay_palm_analysis,
                                )
                                from engine.divination.palm.unet_line_extractor import (
                                    extract_palm_lines_best_available,
                                )
                                # CFM 재추론 (마스크 시각화에 필요 — palm_report에는 마스크 X)
                                cfm_viz_result = await asyncio.to_thread(
                                    extract_palm_lines_best_available, img_array,
                                )
                                line_scores_dict = {
                                    k: float(ls.score)
                                    for k, ls in palm_report.lines.items()
                                }
                                viz = await asyncio.to_thread(
                                    overlay_palm_analysis,
                                    img_array, keypoints,
                                    cfm_viz_result.mask if cfm_viz_result else None,
                                    line_scores_dict,
                                    palm_report.metadata.get("cfm_raw_metrics"),
                                )
                                palm_visualization = {
                                    "image_base64": viz.image_base64,
                                    "width": viz.width,
                                    "height": viz.height,
                                    "n_keypoints": viz.n_keypoints,
                                    "has_cfm_mask": viz.has_cfm_mask,
                                    "metadata": viz.metadata,
                                }
                            except Exception:
                                palm_visualization = None
                    except Exception:
                        pass

            # ADR-256 — LLM 실패 시 결정론 점수 + 친절 안내 반환 (502 회피).
            try:
                result = await asyncio.to_thread(
                    generate_palm_reading,
                    req.image_base64,
                    req.age,
                    req.gender,
                    req.hand,
                    req.question,
                )
            except Exception as llm_err:
                # Vision LLM 실패 → 결정론 점수 + 옥선 할미 어조 안내
                fallback_text = (
                    "허허, 오늘은 이 할미의 눈이 조금 흐려져 손금이 자세히 안 보이는구만. "
                    "잠시 후 다시 손을 펼쳐 보여주시게.\n\n"
                )
                if palm_deterministic_block:
                    fallback_text += (
                        "다만 결정론 분석은 잠시 살펴봤네:\n"
                        + palm_deterministic_block.split("\n", 1)[1].split("[안전")[0]
                    )
                fallback_text += (
                    "\n\n※ 본 결과는 참고용이며, 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다."
                )
                result = {
                    "text": fallback_text,
                    "cached": False,
                    "llm_fallback": True,
                    "llm_error": type(llm_err).__name__,
                }
            # 결정론 블록을 result에 노출 (LLM 호출자 inject 가능).
            if palm_deterministic_block and isinstance(result, dict):
                result["deterministic_block"] = palm_deterministic_block
            # ADR-259 — 시각화 오버레이 추가
            if palm_visualization and isinstance(result, dict):
                result["visualization"] = palm_visualization
            # ADR-006/094/113 단정 어휘 + ADR-115 다국어 hallucination 사후 필터링
            if isinstance(result, dict) and "text" in result:
                result["text"] = _sanitize_common_assertion_words(result["text"])
                result["text"] = _sanitize_foreign_hallucination(result["text"])
                result["text"] = _sanitize_korean_grammar_dupes(result["text"])
            return result
        except ValueError as ve:
            raise HTTPException(400, str(ve))
        except Exception as e:
            # ADR-256 최후 fallback — 그래도 502 안 내고 친절 메시지
            return {
                "text": "허허, 잠시 후 다시 시도해주시게. 이 할미의 눈이 흐려져 있어. "
                        "※ 참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다.",
                "cached": False,
                "fatal_error": type(e).__name__,
            }

    async def post_star_reading(
        self, req: StarReadingRequest
    ) -> dict[str, Any]:
        """성하 공자 별빛 풀이 — 12 황도대 결정론 일일 톤 (ADR-068).

        결정론 점성술 점수 산출만, LLM 호출 X (cost·latency 최소화).
        풀이 텍스트는 /api/llm/chat과 결합하거나 클라이언트가 결정.
        """
        try:
            from datetime import date as _date
            from engine.divination.star.scoring import compute_daily_star_reading
            from engine.safety import build_legal_footer, build_ai_generation_meta

            birth = _date.fromisoformat(req.birth)
            target = _date.fromisoformat(req.target_date) if req.target_date else _date.today()
            reading = compute_daily_star_reading(birth, target)

            return {
                "sign_key": reading.sign_key,
                "sign_label_ko": reading.sign_label_ko,
                "sign_symbol": reading.sign_symbol,
                "element_ko": reading.element_ko,
                "modality_ko": reading.modality_ko,
                "ruling_planet": reading.ruling_planet,
                "daily_tone_ko": reading.daily_tone_ko,
                "target_date": reading.target_date,
                "disclaimer": reading.disclaimer,
                "legal_notice": build_legal_footer(),
                "ai_generation": build_ai_generation_meta(model_label="deterministic-engine"),
            }
        except ValueError as ve:
            raise HTTPException(400, f"날짜 형식 오류 (YYYY-MM-DD 필요): {ve}")
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_ziwei_chart(
        self, req: ZiweiChartRequest
    ) -> dict[str, Any]:
        """자미두수 결정론 명반 산출 (ADR-010).

        결정론 안성법으로 명궁·12궁·14주성·오행국·생년사화를 산출한다.
        LLM 호출은 하지 않으며(cost·latency 최소화), 프론트가 prompt_meta를
        /api/llm/chat 시스템 프롬프트에 주입해 해석 작문을 얻는다.
        명반 배치를 LLM이 자체산출하지 않도록 결정론 결과를 강제 제공한다.
        """
        try:
            from datetime import date as _date
            from engine.divination.ziwei.scoring import (
                compute_ziwei_chart,
                format_ziwei_for_prompt,
            )
            from engine.safety import build_legal_footer, build_ai_generation_meta

            birth = _date.fromisoformat(req.birth)
            if not 0 <= req.birth_hour <= 23:
                raise ValueError(f"birth_hour must be 0..23, got {req.birth_hour}")

            chart = compute_ziwei_chart(birth, req.birth_hour, req.gender)

            return {
                "lunar_month": chart.lunar_month,
                "lunar_day": chart.lunar_day,
                "is_leap_month": chart.is_leap_month,
                "hour_branch_ko": chart.hour_branch_ko,
                "year_gan_ko": chart.year_gan_ko,
                "ming_branch_ko": chart.ming_branch_ko,
                "body_branch_ko": chart.body_branch_ko,
                "wuxing_ju_ko": chart.wuxing_ju_ko,
                "wuxing_ju_num": chart.wuxing_ju_num,
                "ziwei_branch_ko": chart.ziwei_branch_ko,
                "palaces": [
                    {
                        "key": p.key,
                        "label_ko": p.label_ko,
                        "label_hanja": p.label_hanja,
                        "alias_ko": p.alias_ko,
                        "branch_ko": p.branch_ko,
                        "branch_hanja": p.branch_hanja,
                        "main_stars_ko": list(p.main_stars_ko),
                    }
                    for p in chart.palaces
                ],
                "sihua": {
                    "school": chart.sihua_school,
                    "lu_ko": chart.sihua_lu_ko,
                    "quan_ko": chart.sihua_quan_ko,
                    "ke_ko": chart.sihua_ke_ko,
                    "ji_ko": chart.sihua_ji_ko,
                    "has_variants": chart.sihua_has_variants,
                },
                "prompt_meta": format_ziwei_for_prompt(chart),
                "disclaimer": chart.disclaimer,
                "legal_notice": build_legal_footer(),
                "ai_generation": build_ai_generation_meta(model_label="deterministic-engine"),
            }
        except ValueError as ve:
            raise HTTPException(400, f"입력 형식 오류: {ve}")
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_content_reading(
        self, req: ContentReadingRequest
    ) -> dict[str, Any]:
        """메뉴 콘텐츠 풀이 — 도메인 결정론 엔진 + LLM 결합 (ADR-069).

        char_key 'saju' + content_key 'today' 일 때:
          1. engine/saju/pillars.day_pillar() — 사용자 일진 + 오늘 일진
          2. engine/saju/ten_gods.compute_ten_gods() — 십성 관계
          3. 결정론 결과 → 시스템 프롬프트 주입
          4. BizRouter Gemini Flash Lite 작문
        """
        from datetime import date as _date
        from engine.safety import build_legal_footer, build_ai_generation_meta

        fields = req.fields or {}
        char_key = req.char_key
        content_key = req.content_key

        # ADR-071: 도메인 결정론 결과 누적 (saju + name 동시 호출 가능)
        # 사용자가 fullName + birth 모두 입력 시 사주 + 성명학 결정론 동시 인용.
        # char_key 캐릭터 단독 도메인 외에도 fields 입력 기준 누적 적용.
        deterministic_blocks: list[str] = []

        # ─── saju 결정론 (char_key='saju' + birth 입력) ───
        # ADR-069·070 후속 fix: birth 입력 받는 모든 콘텐츠에서 사주 일주 융합.
        # 이전: today/tomorrow 5개 content_key만 융합 → who-likes·heart·image·fate-one·
        #       future-fate·life-card 등 birth 받는 콘텐츠가 사주 결정론 미호출 (UI/백엔드 불일치).
        # 본 fix: birth만 입력되면 모든 char_key·content_key에서 사주 융합.
        birth_str = (fields.get("birth") or "").strip()
        wants_saju = (char_key == "saju") or (
            birth_str and char_key in ("name", "face", "palm", "dream", "hwapae", "star")
        )
        if char_key == "saju" or (wants_saju and birth_str):
            if birth_str:
                try:
                    from engine.saju.pillars import day_pillar
                    from engine.saju.ten_gods import (
                        compute_ten_gods,
                        classify_gilhyung,
                        detect_special_combinations,
                    )
                    # ADR-089: 신살 결정론 (사전학습 환각 차단 — 도화살·역마살 등 명시 산출만 인용)
                    from engine.saju.pillars import compute_pillars
                    from engine.saju.shensha import compute_shensha, SHENSHA_MEANINGS

                    birth_dt = _date.fromisoformat(birth_str)
                    today_dt = _date.today()
                    user_day_pillar = day_pillar(birth_dt.year, birth_dt.month, birth_dt.day)
                    today_pillar_data = day_pillar(today_dt.year, today_dt.month, today_dt.day)

                    # ADR-072: compute_ten_gods는 {"day":"甲子","hour":"丁卯"} 문자열 형식 받음
                    # 사용자 일간 ↔ 오늘 천간·지지 십성 산출
                    user_gz = f"{user_day_pillar.get('gan_han','')}{user_day_pillar.get('ji_han','')}"
                    today_gz = f"{today_pillar_data.get('gan_han','')}{today_pillar_data.get('ji_han','')}"
                    today_tengod_gan = ""
                    today_tengod_ji = ""
                    ten_gods_data: dict = {}
                    try:
                        if len(user_gz) >= 2 and len(today_gz) >= 2:
                            ten_gods_data = compute_ten_gods({
                                "year": user_gz, "month": user_gz, "day": user_gz, "hour": today_gz,
                            })
                            today_tengod_gan = ten_gods_data.get("hour_gan", "")
                            today_tengod_ji = ten_gods_data.get("hour_ji", "")
                    except Exception:
                        pass

                    tengod_label = (
                        f"천간 {today_tengod_gan}·지지 {today_tengod_ji}"
                        if today_tengod_gan or today_tengod_ji
                        else "(미산출)"
                    )

                    # ADR-086: 십성 메타 분류 — 사길신·사흉신 라벨 + 특수 조합
                    gan_class = classify_gilhyung(today_tengod_gan) if today_tengod_gan else None
                    ji_class = classify_gilhyung(today_tengod_ji) if today_tengod_ji else None
                    meta_label_parts = []
                    if gan_class:
                        meta_label_parts.append(f"천간 {today_tengod_gan}={gan_class}")
                    if ji_class:
                        meta_label_parts.append(f"지지 {today_tengod_ji}={ji_class}")
                    meta_label = " · ".join(meta_label_parts) if meta_label_parts else "(중립)"

                    special_combos = detect_special_combinations(ten_gods_data) if ten_gods_data else []
                    combos_label = ", ".join(special_combos) if special_combos else "(없음)"

                    # ADR-089: 신살 결정론 산출 (사용자 4기둥 + 시각 미입력 시 정오 추정)
                    shensha_result: dict = {}
                    shensha_lines: list[str] = []
                    try:
                        full_pillars = compute_pillars(birth_dt.year, birth_dt.month, birth_dt.day, 12)
                        shensha_result = compute_shensha(full_pillars)
                        for key in ("cheoneul", "munchang", "yeokma", "dohwa", "kongmang"):
                            meta = SHENSHA_MEANINGS.get(key, {})
                            label = meta.get("label", key)
                            values = shensha_result.get(key, [])
                            if values:
                                shensha_lines.append(f"{label}: {'·'.join(values)}")
                            else:
                                shensha_lines.append(f"{label}: (없음)")
                    except Exception:
                        shensha_lines = ["(신살 산출 실패)"]
                    shensha_label = " / ".join(shensha_lines)

                    deterministic_blocks.append(
                        f"[사주 결정론 — engine/saju 출력]\n"
                        f"  · 사용자 일주(日柱): {user_day_pillar.get('gan','')}{user_day_pillar.get('ji','')} "
                        f"({user_day_pillar.get('gan_han','')}{user_day_pillar.get('ji_han','')})\n"
                        f"  · 사용자 일간(日干, 본명 중심): {user_day_pillar.get('gan','')}\n"
                        f"  · 오늘 일진(今日 日辰): {today_pillar_data.get('gan','')}{today_pillar_data.get('ji','')} "
                        f"({today_pillar_data.get('gan_han','')}{today_pillar_data.get('ji_han','')})\n"
                        f"  · 일간↔오늘 십성: {tengod_label}\n"
                        f"  · 십성 메타 분류 (ADR-086): {meta_label}\n"
                        f"  · 특수 구조 조합: {combos_label}\n"
                        f"  · 신살 결정론 (ADR-089): {shensha_label}\n"
                        f"  · [지시 1] 위 메타는 명리학 통설 구조 라벨이며 길흉 단정 X (ADR-006).\n"
                        f"  · [지시 2] 신살 (천을귀인·문창귀인·역마살·도화살·공망)은 위 산출 결과에서 '(없음)' 명시된 경우 절대 언급 X. 사전학습 사주 지식 추가 금지 (ADR-010)."
                    )
                except (ValueError, ImportError, Exception):
                    deterministic_blocks.append("[사주 결정론 — 산출 실패]")

        # ─── name 결정론 (char_key='name' OR fullName/hanja 입력 시 누적) ───
        # ADR-070·071: 성명학 결정론 융합 — fullName/hanja 입력 시 모든 도메인에서 동시 인용.
        # 본 fix 이전: name·saju 2 도메인만 융합. hwapae·dream·face·palm·star는 share='name'
        # UI 입력을 받았지만 LLM 프롬프트에 성명학 결정론 결과 미주입 (UI/백엔드 불일치).
        # 본 fix: 사용자가 이름 입력한 모든 캐릭터에서 성명학 결정론 결과 자동 융합.
        full_name = (fields.get("fullName") or fields.get("currentName") or "").strip()
        hanja = (fields.get("hanja") or "").strip()
        wants_name = (char_key == "name") or (
            (full_name or hanja) and char_key in ("saju", "hwapae", "dream", "face", "palm", "star")
        )
        if wants_name and (full_name or hanja):
            try:
                from engine.divination.name.baleum import evaluate_baleum
                from engine.divination.name.scoring import score_name

                lines: list[str] = ["[성명학 결정론 — engine/divination/name 출력]"]

                if full_name:
                    try:
                        # ADR-072: BaleumReport 실 필드 = syllables·ohaeng_sequence·relations·grade·reason
                        # 이전 ADR-070 'score' 가짜 속성 fallback 0.00 LLM 주입 결손 정정
                        baleum_report = evaluate_baleum(full_name, include_jongsung=False)
                        ohaeng_seq = "·".join(getattr(baleum_report, "ohaeng_sequence", []) or [])
                        grade = getattr(baleum_report, "grade", "")
                        reason = getattr(baleum_report, "reason", "")
                        lines.append(
                            f"  · 발음 분석 (한글): {full_name}\n"
                            f"  · 음절 오행 흐름: {ohaeng_seq or '(미산출)'}\n"
                            f"  · 음 조화 등급: {grade or '(미산출)'}\n"
                            f"  · 평가 사유: {reason or '(미산출)'}\n"
                            f"  · 음 결합 결정론: 본 시스템 ADR-028 Priority 1·2 검증"
                        )
                    except Exception:
                        lines.append(f"  · 한글 이름: {full_name} (발음 분석 미산출)")

                if hanja:
                    try:
                        name_score = score_name(hanja)
                        if name_score:
                            strokes = name_score.get("strokes", {})
                            four = name_score.get("four_gyeok", {})
                            bulyong = name_score.get("bulyong", {})
                            lines.append(
                                f"  · 한자 표기: {hanja}\n"
                                f"  · 획수 (강희자전): {strokes.get('kangxi', [])}\n"
                                f"  · 4격 (원·형·이·정): {four.get('won','')}·{four.get('hyeong','')}·{four.get('i','')}·{four.get('jeong','')}\n"
                                f"  · 4격 길흉: {'모두 길격' if four.get('all_good') else '일부 흉격 또는 부분 길격'}\n"
                                f"  · 불용한자 여부: {'있음' if bulyong.get('has_bulyong') else '없음'}"
                            )
                    except Exception:
                        lines.append(f"  · 한자: {hanja} (4격·획수 산출 실패)")

                deterministic_blocks.append("\n".join(lines))
            except Exception:
                deterministic_blocks.append("[성명학 결정론 — 산출 실패]")

        # ─── ADR-135 today-hanja (오늘의 한자) ───
        if char_key == "name" and content_key == "today-hanja":
            try:
                from engine.divination.name.daily_hanja import get_daily_hanja
                r135 = get_daily_hanja()
                if r135:
                    deterministic_blocks.append(
                        f"[ADR-135 오늘의 한자 결정론]\n"
                        f"  · 날짜: {r135.date_iso} (시드: {r135.seed_int})\n"
                        f"  · 오늘의 한자: {r135.char} ({r135.hangul})\n"
                        f"  · 강희자전 획수: {r135.kangxi_strokes}\n"
                        f"  · 자원오행: {r135.resource_ohaeng or '(매핑 부재)'}\n"
                        f"  · KCI 학파 출처: {r135.kci_school_source or '(부재)'}\n"
                        f"  · 본의: {r135.kci_reason or '(부재)'}"
                    )
            except Exception:
                pass

        # ─── ADR-136 biz (상호 작명) ───
        if char_key == "name" and content_key == "biz":
            try:
                from engine.divination.name.biz_naming import compute_biz_naming
                biz_type = (fields.get("bizType") or "").strip()
                concept = (fields.get("concept") or "").strip()
                if biz_type:
                    r136 = compute_biz_naming(biz_type, concept=concept)
                    hanja_samples = ", ".join(
                        f"{h['char']}({h['hangul']})" for h in r136.recommended_hanja[:8]
                    )
                    deterministic_blocks.append(
                        f"[ADR-136 상호 작명 결정론]\n"
                        f"  · 업종: {r136.biz_type} / 컨셉: {r136.concept or '(미입력)'}\n"
                        f"  · 1차 추천 오행: {', '.join(r136.target_ohaeng_primary)}\n"
                        f"  · 2차 보조 오행: {r136.target_ohaeng_secondary or '(없음)'}\n"
                        f"  · 추천 한자 풀 ({len(r136.recommended_hanja)}자): {hanja_samples}\n"
                        f"  · 학파: {r136.school_source[:80]}"
                    )
            except Exception:
                pass

        # ─── ADR-137 pen (예명 작명) ───
        if char_key == "name" and content_key == "pen":
            try:
                from engine.divination.name.pen_naming import compute_pen_naming
                field_code = (fields.get("field") or "other").strip()
                r137 = compute_pen_naming(field_code)
                hanja_samples = ", ".join(
                    f"{h['char']}({h['hangul']})" for h in r137.recommended_hanja[:8]
                )
                deterministic_blocks.append(
                    f"[ADR-137 예명 작명 결정론]\n"
                    f"  · 활동 분야: {r137.field_label_ko}\n"
                    f"  · 추천 오행: {', '.join(r137.target_ohaeng)}\n"
                    f"  · 학파 근거: {r137.rationale}\n"
                    f"  · 추천 한자 풀 ({len(r137.recommended_hanja)}자): {hanja_samples}"
                )
            except Exception:
                pass

        # ─── ADR-138 newborn (신생아 작명) ───
        if char_key == "name" and content_key == "newborn":
            try:
                from engine.divination.name.newborn import compute_newborn_naming
                surname = (fields.get("surname") or "").strip()
                baby_birth = (fields.get("babyBirth") or "").strip()
                baby_hour = (fields.get("babyHour") or "").strip() or None
                baby_gender = (fields.get("babyGender") or "").strip() or None
                parent_wish = (fields.get("parentWish") or "").strip()
                if surname and baby_birth:
                    r138 = compute_newborn_naming(
                        surname=surname,
                        baby_birth_iso=baby_birth,
                        baby_hour_branch=baby_hour,
                        baby_gender=baby_gender,
                        parent_wish=parent_wish,
                    )
                    if r138:
                        hanja_samples = ", ".join(
                            f"{h['char']}({h['hangul']})" for h in r138.recommended_hanja[:8]
                        )
                        deterministic_blocks.append(
                            f"[ADR-138 신생아 작명 결정론]\n"
                            f"  · 성: {r138.surname} / 출생: {r138.baby_birth_iso} {r138.baby_hour or '(시각 미입력)'}\n"
                            f"  · {r138.saju_summary}\n"
                            f"  · 사주 추천 오행: {', '.join(r138.saju_recommended_ohaeng) or '(균형 양호)'}\n"
                            f"  · 추천 한자 풀 ({len(r138.recommended_hanja)}자): {hanja_samples}\n"
                            f"  · 부모 바람: {r138.parent_wish or '(미입력)'}"
                        )
            except Exception:
                pass

        # ─── ADR-139 rename (개명 추천) ───
        if char_key == "name" and content_key == "rename":
            try:
                from engine.divination.name.rename import compute_rename
                current = (fields.get("currentName") or "").strip()
                birth_iso = (fields.get("birth") or "").strip()
                hour_b = (fields.get("hourBranch") or "").strip() or None
                gender = (fields.get("gender") or "").strip() or None
                reason = (fields.get("reason") or "").strip()
                if current and birth_iso:
                    r139 = compute_rename(
                        current_name=current,
                        birth_iso=birth_iso,
                        hour_branch=hour_b,
                        gender=gender,
                        user_reason=reason,
                    )
                    if r139:
                        hanja_samples = ", ".join(
                            f"{h['char']}({h['hangul']})" for h in r139.recommended_hanja[:8]
                        )
                        deterministic_blocks.append(
                            f"[ADR-139 개명 진단 결정론]\n"
                            f"  · 현재 이름: {r139.current_name}\n"
                            f"  · 오행 충돌 진단: {r139.conflict_detail}\n"
                            f"  · 발음오행 등급: {r139.baleum_grade or '(미산출)'}\n"
                            f"  · 사주 추천 오행: {', '.join(r139.saju_recommended_ohaeng) or '(균형 양호)'}\n"
                            f"  · 추천 한자 풀 ({len(r139.recommended_hanja)}자): {hanja_samples}\n"
                            f"  · 사용자 이유: {r139.user_reason or '(미입력)'}"
                        )
            except Exception:
                pass

        # ─── palm 결정론 (ADR-074·081, char_key='palm') ───
        # ADR-081: imageB64 입력 시 Phase 2 → generate_palm_reading Vision 호출
        # ADR-074: 사진 미입력 시 학파/라벨 풀 메타만 LLM 인용
        wants_palm = char_key == "palm"
        palm_image_b64 = (fields.get("imageB64") or fields.get("image") or "").strip()
        if wants_palm:
            try:
                from engine.divination.palm.knowledge import (
                    PALM_SCHOOLS,
                    FATE_LINE_STRAIGHT, FATE_LINE_CURVED,
                    SUN_LINE_CLEAR, SUN_LINE_FAINT,
                    MERCURY_LINE_CONTINUOUS, MERCURY_LINE_FRAGMENTED,
                    MARRIAGE_LINE_SINGLE_CLEAR, MARRIAGE_LINE_MULTIPLE, MARRIAGE_LINE_FORKED,
                )
                schools_meta = " · ".join(
                    f"{s.name_short}({s.tradition},{s.publication_year})"
                    for s in PALM_SCHOOLS
                )
                if palm_image_b64:
                    # ADR-081 Phase 2: Vision 풀 호출
                    deterministic_blocks.append(
                        "[손금 결정론 Phase 2 — engine/divination/palm/reading.generate_palm_reading]\n"
                        f"  · 학파 6개: {schools_meta}\n"
                        f"  · 사진 입력 감지 (base64 길이: {len(palm_image_b64)})\n"
                        f"  · Vision 풀 호출은 별도 엔드포인트 (/api/palm/read) 사용 권장.\n"
                        f"  · 본 분기는 학파 + 라벨 풀 인용으로 LLM 작문 유도.\n"
                        f"  · 운명선·태양선·수성선·결혼선 4 보조선 결정론 라벨 적용 시 사용자에게 사진 업로드 가이드."
                    )
                else:
                    deterministic_blocks.append(
                        "[손금 결정론 — engine/divination/palm 학파·라벨 풀]\n"
                        f"  · 학파 6개: {schools_meta}\n"
                        f"  · 운명선 라벨: {FATE_LINE_STRAIGHT} | {FATE_LINE_CURVED}\n"
                        f"  · 태양선 라벨: {SUN_LINE_CLEAR} | {SUN_LINE_FAINT}\n"
                        f"  · 수성선 라벨: {MERCURY_LINE_CONTINUOUS} | {MERCURY_LINE_FRAGMENTED}\n"
                        f"  · 결혼선 라벨: {MARRIAGE_LINE_SINGLE_CLEAR} | {MARRIAGE_LINE_MULTIPLE} | {MARRIAGE_LINE_FORKED}\n"
                        f"  · 사진 미입력 시 라이브 분류 불가. 라벨 풀 인용만 허용."
                    )
            except Exception:
                deterministic_blocks.append("[손금 결정론 — 산출 실패]")

        # ─── ADR-118 토정비결 (palm/tojeong content_key + birth) ───
        if char_key == "palm" and content_key == "tojeong" and birth_str:
            try:
                from datetime import datetime as _dt_tj, date as _date_tj
                from engine.divination.tojeong import compute_tojeong_for_year, format_hexagram_for_prompt
                birth_d = _dt_tj.strptime(birth_str, "%Y-%m-%d").date()
                target_year = _date_tj.today().year
                hex_r = compute_tojeong_for_year(birth_d, target_year)
                if hex_r:
                    deterministic_blocks.append(format_hexagram_for_prompt(hex_r, target_year))
            except Exception:
                pass

        # ─── ADR-119 12지 띠 운세 (palm/zodiac content_key + birth) ───
        if char_key == "palm" and content_key == "zodiac" and birth_str:
            try:
                from datetime import datetime as _dt_zo, date as _date_zo
                from engine.divination.zodiac_ko import (
                    animal_by_year, compute_year_fortune, format_animal_for_prompt,
                )
                birth_d = _dt_zo.strptime(birth_str, "%Y-%m-%d").date()
                my_animal = animal_by_year(birth_d.year)
                target_year = _date_zo.today().year
                year_compat = compute_year_fortune(birth_d.year, target_year)
                deterministic_blocks.append(
                    format_animal_for_prompt(my_animal, target_year, year_compat)
                )
            except Exception:
                pass

        # ─── ADR-120 산통점 (palm/spirit content_key + 산가지 입력) ───
        # 사용자가 3 산가지 값 (stick1·stick2·stick3) 입력 시 결정론 산출
        if char_key == "palm" and content_key == "spirit":
            try:
                from engine.divination.santong import compute_santong_reading, format_santong_for_prompt
                # fields에서 stick1·stick2·stick3 또는 무작위 fallback
                s1 = int((fields.get("stick1") or "3").strip() or "3")
                s2 = int((fields.get("stick2") or "5").strip() or "5")
                s3 = int((fields.get("stick3") or "7").strip() or "7")
                santong_r = compute_santong_reading(s1, s2, s3)
                if santong_r:
                    deterministic_blocks.append(format_santong_for_prompt(santong_r))
            except Exception:
                pass

        # ─── ADR-121 부적 4 표준 (palm/talisman content_key + talismanType) ───
        if char_key == "palm" and content_key == "talisman":
            try:
                from engine.divination.talisman import compute_talisman_reading, format_talisman_for_prompt
                talisman_type = (fields.get("talismanType") or fields.get("type") or "hapgyeok").strip()
                talisman_r = compute_talisman_reading(talisman_type)
                if talisman_r:
                    deterministic_blocks.append(format_talisman_for_prompt(talisman_r))
            except Exception:
                pass

        # ─── ADR-158 야선 아씨 4 컨텐츠 (char_key='ya') ───
        # 속궁합·욕망·운우지정·정인 사주 결정론 + sanitize 4중 안전망.
        # ADR-006 자문 거절 정신: 결혼·이혼·외도·배우자 외모 단정 차단.
        if char_key == "ya" and content_key in ("sok-gunghap", "desire-saju", "unu-jijeong", "jeongin-saju"):
            try:
                from datetime import datetime as _dt_ya
                from engine.saju.pillars import compute_pillars as _compute_pillars_ya
                birth_str_ya = (fields.get("birth") or "").strip()
                partner_birth_str_ya = (fields.get("partnerBirth") or "").strip()

                def _ya_day_pillar(s: str) -> tuple[str, str, str, tuple[str, ...]]:
                    """birth_str → (day_gan, day_ji, day_pillar_2자, 4지지 튜플)."""
                    d = _dt_ya.strptime(s, "%Y-%m-%d").date()
                    p = _compute_pillars_ya(d.year, d.month, d.day, 12)
                    dg, dj = p["day_pillar"]["gan_han"], p["day_pillar"]["ji_han"]
                    branches = (
                        p["year_pillar"]["ji_han"],
                        p["month_pillar"]["ji_han"],
                        dj,
                        p["hour_pillar"]["ji_han"],
                    )
                    return dg, dj, dg + dj, branches

                if content_key == "sok-gunghap" and birth_str_ya and partner_birth_str_ya:
                    from engine.divination.sok_gunghap import (
                        compute_sok_gunghap, format_sok_gunghap_for_prompt,
                    )
                    _, _, self_dp, self_brs = _ya_day_pillar(birth_str_ya)
                    _, _, prt_dp, prt_brs = _ya_day_pillar(partner_birth_str_ya)
                    r_sg = compute_sok_gunghap(self_dp, prt_dp, self_brs, prt_brs)
                    if r_sg:
                        deterministic_blocks.append(format_sok_gunghap_for_prompt(r_sg))

                elif content_key == "desire-saju" and birth_str_ya:
                    from engine.divination.desire_saju import (
                        compute_desire_saju, format_desire_saju_for_prompt,
                    )
                    from engine.saju.ten_gods import compute_ten_gods as _ten_gods_ya
                    dg_y, _, _, brs_y = _ya_day_pillar(birth_str_ya)
                    # 4 천간 추출 (일간 제외 3건의 십성 계산)
                    d2 = _dt_ya.strptime(birth_str_ya, "%Y-%m-%d").date()
                    p_y = _compute_pillars_ya(d2.year, d2.month, d2.day, 12)
                    other_gans = [
                        p_y["year_pillar"]["gan_han"],
                        p_y["month_pillar"]["gan_han"],
                        p_y["hour_pillar"]["gan_han"],
                    ]
                    tgs = tuple(_ten_gods_ya(dg_y, og) for og in other_gans)
                    r_ds = compute_desire_saju(dg_y, tgs, brs_y)
                    if r_ds:
                        deterministic_blocks.append(format_desire_saju_for_prompt(r_ds))

                elif content_key == "unu-jijeong" and birth_str_ya and partner_birth_str_ya:
                    from engine.divination.unu_jijeong import (
                        compute_unu_jijeong, format_unu_jijeong_for_prompt,
                    )
                    _, self_dj, _, _ = _ya_day_pillar(birth_str_ya)
                    _, prt_dj, _, _ = _ya_day_pillar(partner_birth_str_ya)
                    r_uj = compute_unu_jijeong(self_dj, prt_dj)
                    if r_uj:
                        deterministic_blocks.append(format_unu_jijeong_for_prompt(r_uj))

                elif content_key == "jeongin-saju" and birth_str_ya:
                    from engine.divination.jeongin_saju import (
                        compute_jeongin_saju, format_jeongin_saju_for_prompt,
                    )
                    from engine.saju.ten_gods import compute_ten_gods as _ten_gods_ya2
                    dg_y, dj_y, _, _ = _ya_day_pillar(birth_str_ya)
                    d3 = _dt_ya.strptime(birth_str_ya, "%Y-%m-%d").date()
                    p_y3 = _compute_pillars_ya(d3.year, d3.month, d3.day, 12)
                    all_other_gans = [
                        p_y3["year_pillar"]["gan_han"],
                        p_y3["month_pillar"]["gan_han"],
                        p_y3["hour_pillar"]["gan_han"],
                    ]
                    tgs_all = tuple(_ten_gods_ya2(dg_y, og) for og in all_other_gans)
                    r_ji = compute_jeongin_saju(dg_y, dj_y, tgs_all)
                    if r_ji:
                        deterministic_blocks.append(format_jeongin_saju_for_prompt(r_ji))
            except Exception:
                pass

        # ─── ADR-122·123·124 조상 메시지 (palm/ancestor content_key + birth) ───
        # 천살 방위 (ADR-122) + 어휘 풀·흐름 톤 (ADR-123) + 4 권역 위령 의례 (ADR-124).
        # 한국 무속 정통 학파 (이능화 1927·한국학중앙연구원·국립민속박물관) 정합.
        # 자문 거절 정신: 망자 1인칭 빙의 화법·접신 어휘 절대 금지 (sanitize 5중).
        if char_key == "palm" and content_key == "ancestor":
            try:
                from engine.divination.ancestor import (
                    build_ancestor_prompt_injection,
                    get_cheonsal_direction,
                )
                ancestor_block_lines = [
                    "[조상 메시지 결정론 — ADR-122·123·124 정통 학파 정합]"
                ]
                # 천살 방위 (출생 연도 지지 → 풍수 방위)
                if birth_str:
                    try:
                        from datetime import date as _date_anc
                        from engine.saju.pillars import compute_pillars
                        birth_d_anc = _date_anc.fromisoformat(birth_str)
                        pillars_anc = compute_pillars(
                            birth_d_anc.year, birth_d_anc.month, birth_d_anc.day, 12
                        )
                        year_ji = pillars_anc.get("year", {}).get("ji_han", "") if isinstance(pillars_anc, dict) else ""
                        if year_ji:
                            cheonsal = get_cheonsal_direction(year_ji)
                            ancestor_block_lines.append(
                                f"  · 천살(天殺) 방위: {cheonsal['cheonsal_ji']} "
                                f"({cheonsal['direction_ko']}, {cheonsal['direction_degree']}도) "
                                f"— 삼합 {cheonsal['samhap']} 기준 정통 사주명리 십이신살."
                            )
                            ancestor_block_lines.append(
                                "  · 전통 제례 헌작·조상 묘 방위 안내용 결정론 산출 "
                                "(메트로신문 김상회 칼럼·정통 사주명리)."
                            )
                    except Exception:
                        pass
                # 어휘 풀 + 흐름 톤 + 금지 어휘 LLM 시스템 프롬프트 주입
                ancestor_block_lines.append("")
                ancestor_block_lines.append(build_ancestor_prompt_injection())
                deterministic_blocks.append("\n".join(ancestor_block_lines))
            except Exception:
                pass

        # ─── face 결정론 (ADR-075·082, char_key='face') ───
        # ADR-082: imageB64 입력 시 Phase 2 → generate_face_reading Vision 호출
        # ADR-075: 사진 미입력 시 4 학파 + 삼정 + 12궁 메타만 인용
        wants_face = char_key == "face"
        face_image_b64 = (fields.get("imageB64") or fields.get("image") or "").strip()
        if wants_face:
            try:
                from engine.divination.face.knowledge import (
                    PHYSIOGNOMY_SCHOOLS, SAMJEONG_REGIONS, TWELVE_PALACES,
                )
                schools_meta = " · ".join(s.name_ko for s in PHYSIOGNOMY_SCHOOLS)
                samjeong_meta = " · ".join(r.label_ko for r in SAMJEONG_REGIONS)
                palaces_meta = " · ".join(p.label_ko for p in TWELVE_PALACES[:6]) + " 등 12궁"
                if face_image_b64:
                    # ADR-082 Phase 2: Vision 풀 호출은 별도 엔드포인트 권장
                    deterministic_blocks.append(
                        "[관상 결정론 Phase 2 — engine/divination/face/reading.generate_face_reading]\n"
                        f"  · 학파 4개: {schools_meta}\n"
                        f"  · 삼정 (얼굴 3분할): {samjeong_meta}\n"
                        f"  · 12궁 일부: {palaces_meta}\n"
                        f"  · 사진 입력 감지 (base64 길이: {len(face_image_b64)})\n"
                        f"  · Vision 풀 호출은 별도 엔드포인트 (/api/face/read) 사용 권장.\n"
                        f"  · 단정 매핑 부재 (fate_mapping·운명 X — ADR-006)."
                    )
                else:
                    deterministic_blocks.append(
                        "[관상 결정론 — engine/divination/face 학파·구조 풀]\n"
                        f"  · 학파 4개: {schools_meta}\n"
                        f"  · 삼정 (얼굴 3분할): {samjeong_meta}\n"
                        f"  · 12궁 일부: {palaces_meta}\n"
                        f"  · 사진 미입력 시 라이브 분류 불가. 구조 인용만 허용.\n"
                        f"  · 단정 매핑 부재 (fate_mapping·운명 X — ADR-006)."
                    )
            except Exception:
                deterministic_blocks.append("[관상 결정론 — 산출 실패]")

        # ─── star compatibility 결정론 (ADR-106, char_key='star' + mySign/partnerSign 단독 OK) ───
        # 144 별자리 궁합은 birth 없이도 호출 가능 (별자리 직접 입력)
        if char_key == "star" and content_key == "compatibility":
            my_sign = (fields.get("mySign") or "").strip()
            partner_sign = (fields.get("partnerSign") or "").strip()
            if my_sign and partner_sign:
                try:
                    from engine.divination.star.compatibility import compute_compatibility
                    compat = compute_compatibility(my_sign, partner_sign)
                    if compat:
                        deterministic_blocks.append(
                            "[별자리 144 궁합 결정론 — ADR-106]\n"
                            f"  · 본인: {compat.sign1_label_ko} ({compat.element1}/{compat.modality1})\n"
                            f"  · 상대: {compat.sign2_label_ko} ({compat.element2}/{compat.modality2})\n"
                            f"  · 관계 유형: {compat.element_tone_ko}\n"
                            f"  · 모달리티 결: {compat.modality_tone_ko}\n"
                            f"  · element 호환 {compat.element_affinity_score}점 + "
                            f"modality {compat.modality_affinity_score}점 + 종합 {compat.overall_score}점\n"
                            f"  · 결혼·이별·연애 성공 단정 X (ADR-006). 흐름 톤으로만 풀이."
                        )
                except Exception:
                    pass

        # ─── star today-zodiac 결정론 (ADR-068, sign 직접 입력) ───
        if char_key == "star" and content_key == "today-zodiac":
            sign_key = (fields.get("sign") or "").strip()
            if sign_key:
                try:
                    from datetime import date as _date_today
                    from engine.divination.star.scoring import sign_by_key, daily_tone_for_sign
                    sign_obj = sign_by_key(sign_key)
                    if sign_obj:
                        tone = daily_tone_for_sign(sign_key, _date_today.today())
                        deterministic_blocks.append(
                            "[오늘의 별자리 결정론 — ADR-068]\n"
                            f"  · 별자리: {sign_obj.label_ko} {sign_obj.symbol}\n"
                            f"  · 원소: {sign_obj.element} / 양태: {sign_obj.modality}\n"
                            f"  · 지배 행성: {sign_obj.ruling_planet}\n"
                            f"  · 오늘 일일 톤: {tone}\n"
                            f"  · 운명·재물·연애 단정 X (ADR-006)."
                        )
                except Exception:
                    pass

        # ─── star east28 결정론 (ADR-107·112, birth 무관) ───
        if char_key == "star" and content_key == "east28":
            try:
                from datetime import date as _date_28
                from engine.divination.star.twenty_eight_mansions import (
                    compute_twenty_eight_mansion_reading,
                )
                m_reading = compute_twenty_eight_mansion_reading(_date_28.today())
                deterministic_blocks.append(
                    "[동양 28수 결정론 — ADR-107 한국 천상열차분야지도 정통]\n"
                    f"  · 오늘의 수: {m_reading.mansion_label_ko} ({m_reading.mansion_label_hanja})\n"
                    f"  · 소속 궁: {m_reading.palace_label_ko} — {m_reading.palace_direction_ko}·{m_reading.palace_season_ko}\n"
                    f"  · 배속 동물: {m_reading.animal_ko}\n"
                    f"  · 배속 요일: {m_reading.weekday_ko}\n"
                    f"  · 흐름 톤: {m_reading.flow_tone_ko}\n"
                    f"  · 길일·흉일·관혼상제 단정 X (ADR-006). 국보 228호 정통."
                )
            except Exception:
                pass

        # ─── star 결정론 (ADR-068·106·107·112·114, char_key='star' + birth) ───
        wants_star = char_key == "star" and bool(birth_str)
        if wants_star:
            try:
                from datetime import datetime, date as date_cls
                from engine.divination.star.scoring import compute_daily_star_reading
                birth_d = datetime.strptime(birth_str, "%Y-%m-%d").date()
                star_result = compute_daily_star_reading(birth_d, date_cls.today())
                deterministic_blocks.append(
                    "[황도대 결정론 — engine/divination/star 출력]\n"
                    f"  · 별자리: {star_result.sign_label_ko} {star_result.sign_symbol}\n"
                    f"  · 원소: {star_result.element_ko}\n"
                    f"  · 양태: {star_result.modality_ko}\n"
                    f"  · 지배 행성: {star_result.ruling_planet}\n"
                    f"  · 일일 톤: {star_result.daily_tone_ko}\n"
                    f"  · 사랑·재물·진로 단정 부재 (love_outcome·career_outcome·money_outcome X — ADR-006)."
                )

                # ADR-114: Skyfield 빅3 + 하우스 + 트랜짓 (big3·classic·love-stars·transit·saju-star)
                if content_key in ("big3", "classic", "love-stars", "transit", "saju-star"):
                    try:
                        from datetime import datetime as _dt, timezone as _tz
                        from engine.divination.star.astronomy import (
                            compute_big_three,
                            compute_houses_whole_sign,
                        )
                        # 출생시간 미입력 → Sun만 fallback
                        # 본 시스템 birth는 'YYYY-MM-DD' — 시간 미입력. 정오 12:00 UTC 가정 (Sun-only).
                        dt_utc = _dt.combine(birth_d, _dt.min.time()).replace(hour=12, tzinfo=_tz.utc)
                        # birthplace 입력 시도 — 본 시스템은 좌표 미입력, 한국 기본 (서울 37.5N, 127.0E) 가정 옵션
                        # ★ Sun-only fallback 디폴트 (위경도 미입력)
                        big3 = compute_big_three(dt_utc)
                        if big3:
                            lines = [
                                "[Skyfield 빅3 결정론 — ADR-114 NASA JPL DE440s]",
                                f"  · 태양 별자리: {big3.sun.sign_label_ko} {big3.sun.degree_in_sign:.1f}°",
                            ]
                            if big3.moon:
                                lines.append(f"  · 달 별자리: {big3.moon.sign_label_ko} {big3.moon.degree_in_sign:.1f}°")
                            else:
                                lines.append("  · 달·상승: 출생시간·장소 미입력 — 산출 X (ADR-114 fallback 의무)")
                            lines.append(
                                "  · 운명·결혼·이혼·파산·건강 단정 X (Liz Greene·Arroyo 정통)."
                            )
                            deterministic_blocks.append("\n".join(lines))
                    except Exception:
                        pass
            except Exception:
                deterministic_blocks.append("[황도대 결정론 — 산출 실패]")

        # ─── dream 결정론 (ADR-077·080, char_key='dream' + dreamText) ───
        # ADR-080: analyze_dream 풀 호출 + PersonalContext 통합
        dream_text = (fields.get("dreamText") or fields.get("dream") or "").strip()
        wants_dream = char_key == "dream" and bool(dream_text)
        if wants_dream:
            try:
                from engine.divination.dream import analyze_dream
                from engine.divination.dream_lex.personal_context import build_context_from_dict

                # PersonalContext 사용자 입력 + 사주 맥락 통합
                ctx_data = {
                    "name": full_name or None,
                    "gender": fields.get("gender") or None,
                    "occupation": fields.get("occupation") or None,
                    "marital_status": fields.get("maritalStatus") or None,
                    "is_pregnant": fields.get("isPregnant") in ("true", True, "y"),
                    "current_concerns": [
                        c.strip() for c in (fields.get("concerns") or "").split(",") if c.strip()
                    ],
                    "mbti": fields.get("mbti") or None,
                }
                # 사주 맥락 (birth 입력 시 자동 주입)
                if birth_str:
                    try:
                        from datetime import datetime as _dt_dream
                        from engine.saju.pillars import day_pillar as _dp_dream
                        b = _dt_dream.strptime(birth_str, "%Y-%m-%d").date()
                        dm_pillar = _dp_dream(b.year, b.month, b.day)
                        ctx_data["day_master"] = dm_pillar["gan_han"]
                        # 오행 매핑
                        elem_map = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
                        ctx_data["day_master_element"] = elem_map.get(dm_pillar["gan_han"], "")
                    except Exception:
                        pass

                ctx = build_context_from_dict(ctx_data)
                analysis = analyze_dream(dream_text, ctx)

                # 결정론 학파 결과 압축 (12+ 도메인 핵심 발췌)
                art_cls = analysis.get("artemidorus_class", "")
                hobson = analysis.get("hobson", {})
                tst = analysis.get("tst", {})
                wx = analysis.get("wuxing", {})
                folk = analysis.get("korean_folk", [])
                arche = analysis.get("archetypes", [])
                hvdc_idx = analysis.get("hvdc_indices", {})
                ich = analysis.get("iching", {})

                folk_names = ", ".join((f.get("symbol") or f.get("name") or "")[:20] for f in folk[:3] if isinstance(f, dict))
                arche_names = ", ".join((a.get("archetype") or a.get("name") or "")[:20] for a in arche[:3] if isinstance(a, dict))

                deterministic_blocks.append(
                    "[해몽 결정론 — engine/divination/dream + dream_lex 12+ 학파 풀 호출]\n"
                    f"  · 입력 꿈: {dream_text[:80]}{'…' if len(dream_text)>80 else ''}\n"
                    f"  · Artemidorus 분류: {art_cls or '(미분류)'}\n"
                    f"  · Hobson 기이도: {hobson.get('bizarreness_level', '미산출')}\n"
                    f"  · Revonsuo TST 위협: {tst.get('total_threats', 0)}건\n"
                    f"  · 오행 매핑 (상위): {(wx.get('counts') or {})}\n"
                    f"  · 한국 민속 매칭 (상위 3): {folk_names or '(없음)'}\n"
                    f"  · Jung 원형 (상위 3): {arche_names or '(없음)'}\n"
                    f"  · Hall-Van de Castle 지수: {hvdc_idx}\n"
                    f"  · 주역 64괘: {ich.get('hexagram_name', '(미산출)')}\n"
                    f"  · [지시 1 — ADR-094 단정 차단] '길몽'·'흉몽'·'대길'·'대흉'·'반드시'·"
                    f"'확실히' 등 단정 어휘 절대 금지. 'polarity: 길/흉'은 학파 라벨일 뿐 "
                    f"운명 단정 X (ADR-006).\n"
                    f"  · [지시 2 — ADR-095 학파 명시] 위 결정론 학파 결과를 인용 시 학파명 "
                    f"명시 의무 (예: 'Artemidorus 분류상 ...', 'Jung 원형 풀에 ...', "
                    f"'한국 민속 해몽서에 ...'). 단일 학파 단정 X — 다학파 병행 의무 (ADR-002).\n"
                    f"  · [지시 3 — ADR-096 콘텐츠 적합성] content_key='{content_key}'에 맞춰:\n"
                    f"      nightmare → '길몽' 인용 X, 위협·불안·악몽 처리 권장.\n"
                    f"      baby → 태몽 학파 (한국 민속 + Hall-Van de Castle 태몽 지수) 인용.\n"
                    f"      lucid → Stephen LaBerge 자각몽 학파 + Dormio TDI 학파 명시.\n"
                    f"      recurring → 반복 꿈 (PTSD·IRT 학파) 인용.\n"
                    f"  · [지시 4 — ADR-006 양면 해석] 매 풀이마다 강점·약점·주의 동시 명시. "
                    f"긍정 일색 풀이 (균형도 0%) 금지 — '암묵적 단정' 차단.\n"
                    f"  · 사전학습 해몽 어휘 추가 금지 (ADR-010)."
                )
            except Exception:
                deterministic_blocks.append("[해몽 결정론 — 산출 실패]")

        # ─── hwapae 결정론 (ADR-078, char_key='hwapae') ───
        wants_hwapae = char_key == "hwapae"
        if wants_hwapae:
            try:
                # 사용자 입력 카드 없으면 day-seed 결정론으로 3장 추첨
                from datetime import date as _date_hwapae
                from engine.divination.hwapae.korean import HWAPAE_CARDS, three_card_spread
                import hashlib
                seed_str = (birth_str or "anon") + "-" + str(_date_hwapae.today())
                seed_hash = int(hashlib.sha256(seed_str.encode()).hexdigest()[:8], 16)
                card_pool = list(HWAPAE_CARDS.keys())
                c0 = card_pool[(seed_hash + 0) % len(card_pool)]
                c1 = card_pool[(seed_hash + 7) % len(card_pool)]
                c2 = card_pool[(seed_hash + 14) % len(card_pool)]
                spread = three_card_spread((c0, c1, c2))
                card_meta = " · ".join(
                    f"{c.name_ko}({c.month}月)" for c in spread.cards
                )
                deterministic_blocks.append(
                    "[화패 결정론 — engine/divination/hwapae 출력]\n"
                    f"  · 3장 추첨 (seed=오늘+생일): {card_meta}\n"
                    f"  · 순서/역순/카테고리 패턴: sequential={spread.is_sequential} reverse={spread.is_reverse}\n"
                    f"  · 카테고리 우세: {spread.category_dominance or '(균형)'}\n"
                    f"  · 단정 점복 X (ADR-006). 상징·문화 콘텐츠로만 인용."
                )
            except Exception:
                deterministic_blocks.append("[화패 결정론 — 산출 실패]")

        # 결정론 블록 통합 + 사전학습 차단 지시
        if deterministic_blocks:
            deterministic_block = (
                "\n" + "\n\n".join(deterministic_blocks) +
                "\n[지시] 위 결정론 출력만 인용. "
                "60갑자·십성·한자·획수·4격·발음 명칭 사전학습 추가 X — ADR-010 사실성 분리.\n"
            )
        else:
            deterministic_block = ""

        # 7 캐릭터 페르소나 톤
        persona_tone_map = {
            "saju":   "만월 아씨 — 사주 명리학 풀이. 정중한 사극풍 어조.",
            "dream":  "몽이 도령 — 꿈 해석. 부드럽고 깊이 있는 어조.",
            "hwapae": "화선 낭자 — 화패·점복. 신비롭고 가벼운 어조.",
            "star":   "성하 공자 — 별빛 풀이. 우주적·시적 어조.",
            "face":   "운학 도사 — 관상. 사극풍 노학자 어조.",
            "palm":   "옥선 할미 — 손금. 따뜻한 할머니 어조.",
            "name":   "묵향 선생 — 작명. 학자다운 정중한 어조.",
        }
        persona = persona_tone_map.get(char_key, persona_tone_map["saju"])

        system = (
            f"당신은 한국 전통 운명학 풀이 캐릭터입니다.\n"
            f"[캐릭터] {persona}\n"
            f"[규칙]\n"
            f"- 단정적 예언 금지. 경향성·자기이해 위주.\n"
            f"- 의료·법률·금융 단정 금지 (ADR-006).\n"
            f"- 운명·재물·결혼 단정 매핑 금지.\n"
            f"- 한국어로 자연스럽게 작성. 4~6단락, 마크다운 없이.\n"
            f"- 결정론 출력이 주어지면 그 출력만 인용 (사전학습 추가 X — ADR-010 사실성 분리).\n"
            f"- ★ [사용자 입력 활용 의무] 사용자가 입력한 모든 필드를 풀이 본문에 자연스럽게 통합하라.\n"
            f"  · 이름이 있으면 응답에 호명 (예: '김준 님의 마음을…').\n"
            f"  · 상대방 이름·관계·기간·맥락 등 입력값을 일반론에 묻지 말고 구체 인용.\n"
            f"  · select 라벨(예: '짝사랑·썸', '1~3개월 전')은 그대로 본문에 녹여 사용.\n"
            f"  · 입력 미반영 = 무의미한 풀이 — 반드시 모든 입력을 응답 내 한 번 이상 언급.\n"
            f"{deterministic_block}"
        )

        # 사용자 입력 정리 — fields_meta로 select 라벨 자동 변환 + 강조
        fields_meta = _resolve_field_labels(char_key, content_key, fields)
        inputs_text = "\n".join(
            f"  · {meta['label']}: {meta['display']}" for meta in fields_meta
        ) if fields_meta else "(입력 없음)"

        # 약점 영역 강화 — content_key별 입력 인용 체크리스트.
        # LLM이 응답 작성 전에 각 입력값을 본문 어느 단락에 녹일지 명시 추적.
        # 이전 측정 결과 future-fate(20%)·fate-one(33%)·reunion-month(33%) 등에서
        # LLM이 일반론에 묻는 경향 → 체크리스트로 자가 검증 강제.
        checklist_items = []
        for meta in fields_meta:
            key = meta["key"]
            display = meta["display"]
            if key in ("birth", "gender", "saju_day_master", "saju_summary"):
                continue  # 메타 정보는 호명만, 체크리스트 X
            checklist_items.append(
                f"  □ '{display}' — 응답에 자연스럽게 인용했는가?"
            )
        checklist_block = (
            "\n[★ 자가 검증 체크리스트 — 응답 작성 후 모두 ✓ 가능해야 함]\n"
            + "\n".join(checklist_items)
            + "\n  · 미인용 항목 있으면 응답 재작성하라.\n"
        ) if checklist_items else ""

        prompt = (
            f"[메뉴 콘텐츠] char_key={char_key}, content_key={content_key}\n"
            f"[사용자 입력 — 풀이 본문에 모두 인용 의무]\n{inputs_text}\n"
            f"[요청] 위 사용자 입력을 자연스럽게 녹여 풀이 한 편 펼쳐주세요. "
            f"이름·상대·관계·기간·맥락을 일반론에 묻지 말고 구체적으로 인용하세요."
            f"{checklist_block}"
        )

        try:
            from engine.llm_sync import bizrouter_client
            client = bizrouter_client()
            # ADR-098: char_key별 모델 분리 라우팅 — dream만 Flash 업그레이드 A/B 테스트
            # DREAM_MODEL > BIZROUTER_MODEL > 기본값 순 우선순위
            default_model = os.environ.get("BIZROUTER_MODEL", "google/gemini-2.5-flash-lite")
            if char_key == "dream":
                model = os.environ.get("DREAM_MODEL", default_model)
            else:
                model = default_model
            resp = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                max_tokens=1500,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
            text = resp.choices[0].message.content or ""
            # ADR-094 강화 — dream 도메인 단정 어휘 사후 필터링.
            # system 프롬프트가 차단해도 LLM이 "길몽으로 해석될 수 있습니다" 같은
            # 가능형 우회를 자주 사용. 본 필터로 실 응답에서 직접 치환.
            if char_key == "dream":
                text = _sanitize_dream_assertion_words(text)
            # ADR-122 sanitize 5중 안전망 — ancestor (palm/ancestor) 분기 망자 1인칭·빙의·접신 차단.
            # 한국 무속 정통 학파 정합 (이능화 1927·한국학중앙연구원·국립민속박물관).
            # Skeptical Inquirer Susan Gerbic 'Grief Vampires' 콜드/핫 리딩 디지털 차단.
            if char_key == "palm" and content_key == "ancestor":
                text = _sanitize_ancestor_assertion_words(text)
            # ADR-134 sanitize 6중 안전망 — tojeong (palm/tojeong) 분기 凶事·大凶·病死 단정 차단.
            # 정통 시구의 단정 어휘를 흐름 톤으로 자동 치환 (folkency·encykorea 학파 정합).
            if char_key == "palm" and content_key == "tojeong":
                try:
                    from engine.divination.tojeong import sanitize_tojeong_verse
                    text = sanitize_tojeong_verse(text)
                except Exception:
                    pass
            # ADR-158 sanitize 7중 안전망 — 야선 아씨 4 컨텐츠 (속궁합·욕망·운우지정·정인).
            # 결혼·이혼·외도·이별·시기·배우자 외모 단정 차단.
            if char_key == "ya":
                try:
                    if content_key == "sok-gunghap":
                        from engine.divination.sok_gunghap import sanitize_sok_gunghap_text
                        text = sanitize_sok_gunghap_text(text)
                    elif content_key == "desire-saju":
                        from engine.divination.desire_saju import sanitize_desire_saju_text
                        text = sanitize_desire_saju_text(text)
                    elif content_key == "unu-jijeong":
                        from engine.divination.unu_jijeong import sanitize_unu_jijeong_text
                        text = sanitize_unu_jijeong_text(text)
                    elif content_key == "jeongin-saju":
                        from engine.divination.jeongin_saju import sanitize_jeongin_saju_text
                        text = sanitize_jeongin_saju_text(text)
                except Exception:
                    pass
            # ADR-006/094 공통 단정 어휘 사후 필터링 (모든 캐릭터).
            # 화선 낭자·운학 도사 등 hwapae/face도 system 지시 우회 빈번.
            text = _sanitize_common_assertion_words(text)
            # ADR-115 다국어 hallucination 차단 (모든 캐릭터).
            # 발견: face/reading.py 운학 도사 응답에 포르투갈어 "saudável" 침입 (2026-05-21).
            text = _sanitize_foreign_hallucination(text)
            text = _sanitize_korean_grammar_dupes(text)
            return {
                "text": text,
                "char_key": char_key,
                "content_key": content_key,
                "deterministic_used": bool(deterministic_block.strip()),
                "legal_notice": build_legal_footer(),
                "ai_generation": build_ai_generation_meta(model_label=model),
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_name_reading(
        self, req: NameReadingRequest
    ) -> dict[str, Any]:
        """묵향 선생 이름 풀이 — 텍스트 전용 LLM 호출 + 캐시."""
        try:
            from engine.divination.name.reading import generate_name_reading

            result = await asyncio.to_thread(
                generate_name_reading,
                req.fullname_ko,
                req.fullname_han,
                req.gender,
                req.birth,
                req.saju_day_master,
                req.saju_summary,
            )
            # ADR-006/094 단정 어휘 + ADR-115 다국어 hallucination 사후 필터링
            if isinstance(result, dict) and "text" in result:
                result["text"] = _sanitize_common_assertion_words(result["text"])
                result["text"] = _sanitize_foreign_hallucination(result["text"])
                result["text"] = _sanitize_korean_grammar_dupes(result["text"])
            return result
        except ValueError as ve:
            raise HTTPException(400, str(ve))
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_dream_interpret(
        self, req: DreamInterpretRequest
    ) -> dict[str, Any]:
        """해몽 v1 호환 — 내부적으로 v2 오케스트레이션 호출.

        기존 응답 키(text/rounds/critic_*/cached/analysis_summary/crisis_alert/legal_notice)
        를 그대로 유지하면서, v2 신규 키(agent_meta·rag_gate)를 추가.

        구버전 클라이언트는 기존 키만 읽고, 신버전 클라이언트는 agent_meta 활용 가능.
        """
        try:
            from engine.agents import interpret_dream_v2

            # v1 flat profile → v2 nested profile
            payload = req.model_dump()
            dream_text = payload.pop("dream_text", "") or ""
            # locale·religion·user_target_domain은 v1에 없으므로 기본값
            profile = payload  # 나머지 전부 = PersonalContext 필드

            v2_result = await interpret_dream_v2(
                dream_text,
                user_id=None,  # v1은 익명 (DB 비활성)
                profile=profile,
                locale="ko",
                religion=None,
                user_target_domain=None,
                enable_llm_agents=True,
            )

            # v1 호환 응답 형식
            return {
                "text": v2_result.get("text"),
                "rounds": v2_result.get("rounds"),
                "critic_passed": v2_result.get("critic_passed"),
                "critic_total": v2_result.get("critic_total"),
                "cached": False,  # v2는 캐시 비사용 (오케스트레이션이 더 정밀)
                "analysis_summary": v2_result.get("domain_analysis_summary"),
                "crisis_alert": v2_result.get("crisis_alert"),
                "legal_notice": v2_result.get("legal_notice"),
                # ─── v2 추가 키 (구버전 클라이언트는 무시) ───
                "agent_meta": v2_result.get("agent_meta"),
                "rag_gate": v2_result.get("rag_gate"),
                "elapsed_ms": v2_result.get("elapsed_ms"),
                "_engine_version": "v2",
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_clinical_screening(
        self, req: ClinicalScreeningRequest
    ) -> dict[str, Any]:
        """임상 척도 자가검사 — CES-D / BDI-K / STAI-K / PSQI / ISI 통합 채점.

        주어진 응답만 채점하고, 모든 결과를 risk_router로 위험도 산출.
        고위험·임상 위기 시 1393 안내 포함.
        """
        try:
            from engine.clinical import (
                score_ces_d, score_bdi_k, score_stai_k_state, score_psqi, score_isi,
                assess_clinical_risk,
            )
            from engine.clinical.irt import should_trigger_irt
            from engine.safety import build_legal_footer

            results: dict[str, Any] = {}
            if req.ces_d_responses is not None:
                results["ces_d"] = await asyncio.to_thread(
                    score_ces_d, req.ces_d_responses, req.age
                )
            if req.bdi_k_responses is not None:
                results["bdi_k"] = await asyncio.to_thread(score_bdi_k, req.bdi_k_responses)
            if req.stai_k_state_responses is not None:
                results["stai_k_state"] = await asyncio.to_thread(
                    score_stai_k_state, req.stai_k_state_responses
                )
            if req.psqi_component_scores is not None:
                results["psqi"] = await asyncio.to_thread(
                    score_psqi, req.psqi_component_scores
                )
            if req.isi_responses is not None:
                results["isi"] = await asyncio.to_thread(score_isi, req.isi_responses)

            risk = await asyncio.to_thread(
                assess_clinical_risk,
                ces_d_result=results.get("ces_d"),
                bdi_k_result=results.get("bdi_k"),
                stai_k_result=results.get("stai_k_state"),
                psqi_result=results.get("psqi"),
                isi_result=results.get("isi"),
                chronic_nightmare_weeks=req.chronic_nightmare_weeks,
                nightmare_freq_per_week=req.nightmare_freq_per_week,
            )
            irt_trigger = await asyncio.to_thread(
                should_trigger_irt,
                req.nightmare_freq_per_week,
                req.chronic_nightmare_weeks,
            )

            return {
                "scores": results,
                "risk_assessment": risk,
                "irt_trigger": irt_trigger,
                "legal_notice": build_legal_footer(
                    is_crisis=(risk["risk_level"] == "임상 위기")
                ),
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_clinical_instruments(self) -> dict[str, Any]:
        """임상 척도 문항 목록 — 프론트가 자가검사 폼을 렌더링할 때 사용."""
        try:
            from engine.clinical.ces_d import (
                CES_D_ITEMS_KO, CES_D_RESPONSE_OPTIONS,
                CES_D_CUTOFF_ADULT, CES_D_CUTOFF_SENIOR,
            )
            from engine.clinical.bdi_k import BDI_K_ITEMS_KO, BDI_K_CUTOFF
            from engine.clinical.stai_k import (
                STAI_K_STATE_ITEMS_KO, STAI_K_STATE_RESPONSE_OPTIONS, STAI_K_STATE_CUTOFF,
            )
            from engine.clinical.psqi import PSQI_COMPONENTS, PSQI_CUTOFF
            from engine.clinical.isi import ISI_ITEMS_KO
            return {
                "ces_d": {
                    "items": CES_D_ITEMS_KO,
                    "response_options": CES_D_RESPONSE_OPTIONS,
                    "cutoff_adult": CES_D_CUTOFF_ADULT,
                    "cutoff_senior": CES_D_CUTOFF_SENIOR,
                    "instrument": "CES-D 한국판 (전겸구·이민규 1992)",
                },
                "bdi_k": {
                    "items": BDI_K_ITEMS_KO,
                    "cutoff": BDI_K_CUTOFF,
                    "instrument": "BDI 한국판 (이영호·송종용 1991)",
                },
                "stai_k_state": {
                    "items": STAI_K_STATE_ITEMS_KO,
                    "response_options": STAI_K_STATE_RESPONSE_OPTIONS,
                    "cutoff": STAI_K_STATE_CUTOFF,
                    "instrument": "STAI 상태 한국판 (한덕웅·이장호·전겸구 1996)",
                },
                "psqi": {
                    "components": PSQI_COMPONENTS,
                    "cutoff": PSQI_CUTOFF,
                    "instrument": "PSQI (Buysse 1989)",
                },
                "isi": {
                    "items": ISI_ITEMS_KO,
                    "instrument": "ISI (Bastien 2001)",
                },
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_irt_rescript(self, req: IRTRescriptRequest) -> dict[str, Any]:
        """IRT Step 4 — 표적 악몽의 재각본 3안 생성."""
        try:
            self._analytics["irt_rescript_calls"] += 1
            from engine.clinical.irt import generate_rescripted_endings
            result = await asyncio.to_thread(
                generate_rescripted_endings, req.nightmare_text
            )
            return result
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_incubation_session(
        self, req: IncubationRequest
    ) -> dict[str, Any]:
        """꿈 부화 안내 — 취침 전 5단계 + 회상 가이드."""
        try:
            from engine.divination.dream_lex.incubation import (
                build_incubation_session,
                recommend_incubation,
            )
            from engine.safety import build_legal_footer

            session = await asyncio.to_thread(build_incubation_session, req.question)
            recommendation = await asyncio.to_thread(
                recommend_incubation,
                low_recall=req.low_recall,
                upcoming_decision=req.upcoming_decision,
                high_stress=req.high_stress,
                lucid_dream_practice=req.lucid_dream_practice,
            )
            return {
                "session": session,
                "recommendation": recommendation,
                "legal_notice": build_legal_footer(),
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_dream_hvdc_llm(
        self, req: HVdCLLMRequest
    ) -> dict[str, Any]:
        """LLM HVdC 자동 코딩 (Bertolini 2024). 결정론 코더와 union 병합 옵션."""
        try:
            from engine.divination.dream_lex.hvdc_llm import (
                code_dream_with_llm,
                merge_deterministic_and_llm,
            )
            from engine.divination.dream_lex.hallvandecastle import code_dream as det_code, compute_indices
            from engine.safety import detect_crisis, CRISIS_RESPONSE_KO, build_legal_footer

            crisis = detect_crisis(req.dream_text)
            if crisis["crisis_detected"]:
                return {
                    "text": CRISIS_RESPONSE_KO + build_legal_footer(is_crisis=True),
                    "crisis_alert": {
                        "severity": crisis["severity"],
                        "matched_count": len(crisis["matched_keywords"]),
                    },
                    "coding": None,
                }

            llm_result = await asyncio.to_thread(code_dream_with_llm, req.dream_text)
            coding = llm_result["coding"]
            if req.merge_with_deterministic:
                det = await asyncio.to_thread(det_code, req.dream_text)
                coding = await asyncio.to_thread(merge_deterministic_and_llm, det, coding)

            # 정서 dict의 list/int 혼합 정규화 후 indices 계산
            try:
                indices = compute_indices(coding)
            except Exception:
                indices = None

            return {
                "coding": coding,
                "indices": indices,
                "method": llm_result["method"],
                "parse_success": llm_result["parse_success"],
                "merged_with_deterministic": req.merge_with_deterministic,
                "legal_notice": build_legal_footer(),
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_lucid_program(self) -> dict[str, Any]:
        """7일 자각몽 입문 프로그램."""
        try:
            from engine.divination.dream_lex.lucid import (
                build_7day_lucid_program,
                REALITY_CHECKS_KO,
            )
            from engine.safety import build_legal_footer
            program = build_7day_lucid_program()
            return {
                "program": program,
                "all_reality_checks": REALITY_CHECKS_KO,
                "legal_notice": build_legal_footer(),
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_mood_curve(
        self, req: MoodCurveRequest
    ) -> dict[str, Any]:
        """Cartwright 7일+ mood-dream 곡선 분석.

        daily_entries가 비었고 user_id가 있으면 DB에서 자동 로드.
        """
        try:
            from engine.divination.dream_lex.cartwright import analyze_mood_dream_curve
            from engine.safety import build_legal_footer

            entries = req.daily_entries or []
            if not entries and req.user_id:
                from engine.storage import DreamDiaryRepo
                diaries = await asyncio.to_thread(
                    DreamDiaryRepo.list_recent, req.user_id, req.days, 60
                )
                entries = [
                    {
                        "date_iso": d["created_at_iso"],
                        "valence": d["valence"],
                        "vividness": d["vividness"],
                        "recall_quality": d["recall_quality"],
                        "narrative_text": d["narrative_text"],
                    }
                    for d in diaries
                ]
            result = await asyncio.to_thread(analyze_mood_dream_curve, entries)
            return {
                **result,
                "source": "db" if (req.user_id and not req.daily_entries) else "client",
                "legal_notice": build_legal_footer(),
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_myoe_long_term(
        self, req: MyoeLongTermRequest
    ) -> dict[str, Any]:
        """묘에 몽기 — 장기 일기(14일+) 반복 모티프·정서 곡선 분석.

        entries 빈 경우 user_id로 DB 자동 로드.
        """
        try:
            from engine.divination.dream_lex.myoe import analyze_long_term_diary
            from engine.safety import build_legal_footer

            entries = req.entries or []
            if not entries and req.user_id:
                from engine.storage import MyoeDiaryRepo
                entries = await asyncio.to_thread(
                    MyoeDiaryRepo.list_for_analysis, req.user_id, req.days, 60
                )
            result = await asyncio.to_thread(
                analyze_long_term_diary, entries, req.min_entries
            )
            return {
                **result,
                "source": "db" if (req.user_id and not req.entries) else "client",
                "legal_notice": build_legal_footer(),
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_myoe_diary_template(self) -> dict[str, Any]:
        """묘에 스타일 자기관찰 일지 템플릿."""
        try:
            from engine.divination.dream_lex.myoe import (
                MYOE_DIARY_FIELDS_KO, TRADITIONAL_MOTIFS, MYOE_LABEL,
            )
            return {
                "label": MYOE_LABEL,
                "diary_fields": MYOE_DIARY_FIELDS_KO,
                "traditional_motifs": list(TRADITIONAL_MOTIFS.keys()),
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_iching_divine(
        self, req: IChingDivinationRequest
    ) -> dict[str, Any]:
        """주역 64괘 점단 — 꿈 본문에서 팔괘 추출 → 괘 도출 → 길흉·메시지."""
        try:
            from engine.divination.dream_lex.iching import divine_hexagram
            from engine.safety import build_legal_footer
            result = await asyncio.to_thread(divine_hexagram, req.dream_text)
            return {**result, "legal_notice": build_legal_footer()}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_dormio_session(
        self, req: DormioSessionRequest
    ) -> dict[str, Any]:
        """Dormio TDI 세션 — N1 표적 부화 안내 + 음성 큐 + 보고 양식."""
        try:
            from engine.divination.dream_lex.dormio import build_dormio_session
            from engine.safety import build_legal_footer
            result = await asyncio.to_thread(
                build_dormio_session, req.target_topic, req.category, req.cycles
            )
            return {**result, "legal_notice": build_legal_footer()}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_dormio_synthesize(
        self, req: DormioSynthesizeRequest
    ) -> dict[str, Any]:
        """Dormio N회 미세꿈 보고들 종합 — 반복 이미지·정서 분포·예상 밖 요소."""
        try:
            from engine.divination.dream_lex.dormio import synthesize_microdream_insights
            from engine.safety import build_legal_footer
            result = await asyncio.to_thread(
                synthesize_microdream_insights, req.reports, req.target_topic
            )
            return {**result, "legal_notice": build_legal_footer()}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_ullman_group(
        self, req: UllmanGroupRequest
    ) -> dict[str, Any]:
        """Ullman 그룹 꿈 분석 — N개 페르소나 LLM 동시 호출 + 투사 집계."""
        try:
            from engine.divination.dream_lex.ullman import (
                build_ullman_session, aggregate_persona_projections, ULLMAN_SYSTEM_KO,
            )
            from engine.llm_sync import call_llm_sync
            from engine.safety import detect_crisis, CRISIS_RESPONSE_KO, build_legal_footer

            # 위기 검사
            crisis = detect_crisis(req.dream_text)
            if crisis["crisis_detected"]:
                return {
                    "text": CRISIS_RESPONSE_KO + build_legal_footer(is_crisis=True),
                    "crisis_alert": {
                        "severity": crisis["severity"],
                        "matched_count": len(crisis["matched_keywords"]),
                    },
                    "projections": [],
                }

            session = await asyncio.to_thread(
                build_ullman_session, req.dream_text, req.personas
            )
            if not session.get("ready"):
                raise HTTPException(400, session.get("error", "세션 빌드 실패"))

            # 각 페르소나에 LLM 호출 (병렬)
            async def _gen(p: dict[str, str]) -> dict[str, str]:
                try:
                    text = await asyncio.to_thread(
                        call_llm_sync,
                        user_text=p["user_message"],
                        system_prompt=ULLMAN_SYSTEM_KO,
                    )
                except Exception as e:
                    text = f"(생성 실패: {e})"
                return {
                    "persona_key": p["persona_key"],
                    "persona_name": p["persona_name"],
                    "text": text or "",
                }

            projections = await asyncio.gather(
                *(_gen(p) for p in session["persona_prompts"])
            )
            aggregate = await asyncio.to_thread(
                aggregate_persona_projections, list(projections)
            )

            return {
                "projections": list(projections),
                "aggregate": aggregate,
                "guidance": session.get("guidance"),
                "ullman_principle": session.get("ullman_principle"),
                "legal_notice": build_legal_footer(),
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, str(e))

    # ─────────────────────────── 익명 사용자 ───────────────────────────
    async def post_user_new(self) -> dict[str, Any]:
        """새 익명 사용자 생성 — 클라이언트가 user_id를 localStorage 보관."""
        try:
            from engine.storage import new_user_id, UserRepo
            uid = new_user_id()
            user = await asyncio.to_thread(UserRepo.get_or_create, uid)
            return {"user_id": uid, "created_at_iso": user.get("created_at_iso")}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_user_profile(self, req: UserProfileRequest) -> dict[str, Any]:
        """사용자 프로필 갱신 (사주·MBTI·연령 등). 갱신 시 v2 캐시 만료분 정리."""
        try:
            from engine.storage import UserRepo
            from engine.agents.orchestrator import invalidate_user_cache
            profile = {
                k: v for k, v in req.model_dump().items()
                if k != "user_id" and v is not None
            }
            user = await asyncio.to_thread(
                UserRepo.get_or_create, req.user_id, **profile
            )
            # 프로필 변경 → 캐시 만료 청소
            cache_result = await asyncio.to_thread(invalidate_user_cache, req.user_id)
            return {"user": user, "cache": cache_result}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_user_consent(self, req: ConsentRequest) -> dict[str, Any]:
        """민감정보 별도 동의 (개인정보보호법 제23조)."""
        try:
            from engine.storage import UserRepo
            await asyncio.to_thread(UserRepo.set_consent, req.user_id, req.consent)
            return {"user_id": req.user_id, "consent": req.consent}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_user_delete(self, req: UserScopedRequest) -> dict[str, Any]:
        """사용자 + 모든 데이터 삭제 (개인정보보호법 삭제권)."""
        try:
            from engine.storage import UserRepo
            result = await asyncio.to_thread(UserRepo.delete, req.user_id)
            return result
        except Exception as e:
            raise HTTPException(500, str(e))

    # ─────────────────────────── 회원가입 / 로그인 ───────────────────────────
    async def post_auth_signup(self, req: SignupRequest) -> dict[str, Any]:
        """이메일/비번 회원가입. 가입 후 user_id + 프로필 반환."""
        try:
            from engine.storage import AccountRepo, AccountError
            profile = req.model_dump(exclude={"email", "password", "nickname"})
            try:
                account = await asyncio.to_thread(
                    AccountRepo.signup,
                    req.email,
                    req.password,
                    req.nickname,
                    **profile,
                )
            except AccountError as ae:
                raise HTTPException(400, {"code": ae.code, "message": ae.message})
            return {"ok": True, "account": account}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_auth_login(self, req: LoginRequest) -> dict[str, Any]:
        """이메일/비번 로그인."""
        try:
            from engine.storage import AccountRepo, AccountError
            try:
                account = await asyncio.to_thread(
                    AccountRepo.login, req.email, req.password
                )
            except AccountError as ae:
                raise HTTPException(401, {"code": ae.code, "message": ae.message})
            return {"ok": True, "account": account}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_auth_me(self, user_id: str) -> dict[str, Any]:
        """user_id로 계정 정보 조회 (세션 복원용)."""
        try:
            from engine.storage import AccountRepo
            account = await asyncio.to_thread(AccountRepo.get_account, user_id)
            if not account:
                raise HTTPException(404, "account not found")
            return {"ok": True, "account": account}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, str(e))

    # ─────────────────────────── Schredl 일기 + 묘에 통합 ───────────────────────────
    async def post_diary_add(self, req: DiaryAddRequest) -> dict[str, Any]:
        """일기 저장. analyze=True면 dream 분석 결과도 함께 저장."""
        try:
            self._analytics["diary_add_calls"] += 1
            from engine.storage import UserRepo, DreamDiaryRepo
            from engine.safety import detect_crisis, CRISIS_RESPONSE_KO, build_legal_footer

            # 0. 위기 검사
            crisis = detect_crisis(req.narrative_text)
            if crisis["crisis_detected"]:
                return {
                    "saved": False,
                    "crisis_alert": {
                        "severity": crisis["severity"],
                        "matched_count": len(crisis["matched_keywords"]),
                    },
                    "text": CRISIS_RESPONSE_KO + build_legal_footer(is_crisis=True),
                }

            # 사용자 존재 보장
            await asyncio.to_thread(UserRepo.get_or_create, req.user_id)

            # 선택: 분석
            analysis_summary = None
            if req.analyze:
                from engine.divination.dream import analyze_dream
                from engine.divination.dream_lex.personal_context import (
                    build_context_from_dict,
                )
                user = await asyncio.to_thread(UserRepo.get, req.user_id)
                ctx = build_context_from_dict(user or {})
                analysis = await asyncio.to_thread(analyze_dream, req.narrative_text, ctx)
                # 요약만 저장 (전체 분석은 크니)
                analysis_summary = {
                    "artemidorus_class": (analysis.get("artemidorus_class") or {}).get("class"),
                    "wuxing_dominant": (analysis.get("wuxing") or {}).get("dominant_element"),
                    "folk_dominant": (analysis.get("korean_folk") or {}).get("dominant_category"),
                    "archetype_dominant": (analysis.get("archetypes") or {}).get("dominant_archetype"),
                    "bizarreness": (analysis.get("hobson") or {}).get("bizarreness_score"),
                    "cathartic_arc": (analysis.get("cathartic") or {}).get("arc_type"),
                    "hexagram": ((analysis.get("iching") or {}).get("hexagram") or {}).get("name"),
                }

            diary_id = await asyncio.to_thread(
                DreamDiaryRepo.add,
                req.user_id,
                narrative_text=req.narrative_text,
                recall_quality=req.recall_quality,
                vividness=req.vividness,
                valence=req.valence,
                lucidity=req.lucidity,
                wake_time_iso=req.wake_time_iso,
                sleep_duration_min=req.sleep_duration_min,
                core_image=req.core_image,
                felt_meaning=req.felt_meaning,
                spiritual_resonance=req.spiritual_resonance,
                next_intention=req.next_intention,
                analysis_summary=analysis_summary,
            )
            return {
                "saved": True,
                "diary_id": diary_id,
                "analysis_summary": analysis_summary,
                "legal_notice": build_legal_footer(),
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_diary_list(self, req: UserScopedRequest) -> dict[str, Any]:
        """사용자 일기 목록 (최근 30일)."""
        try:
            from engine.storage import DreamDiaryRepo
            diaries = await asyncio.to_thread(DreamDiaryRepo.list_recent, req.user_id, 30, 60)
            return {"diaries": diaries, "count": len(diaries)}
        except Exception as e:
            raise HTTPException(500, str(e))

    # ─────────────────────────── 임상 척도 영구 저장 ───────────────────────────
    async def post_clinical_log(self, req: ClinicalLogRequest) -> dict[str, Any]:
        """척도 채점 + 저장. 미저장 채점은 /api/clinical/screening 사용."""
        try:
            self._analytics["clinical_log_calls"] += 1
            from engine.storage import UserRepo, ClinicalLogRepo
            from engine.clinical import (
                score_ces_d, score_bdi_k, score_stai_k_state, score_psqi, score_isi,
            )
            from engine.safety import build_legal_footer

            await asyncio.to_thread(UserRepo.get_or_create, req.user_id)

            inst = req.instrument
            if inst == "ces_d":
                result = await asyncio.to_thread(score_ces_d, req.responses, req.age)
            elif inst == "bdi_k":
                result = await asyncio.to_thread(score_bdi_k, req.responses)
            elif inst == "stai_k_state":
                result = await asyncio.to_thread(score_stai_k_state, req.responses)
            elif inst == "psqi":
                if not req.psqi_components:
                    raise HTTPException(400, "psqi_components 필요")
                result = await asyncio.to_thread(score_psqi, req.psqi_components)
            elif inst == "isi":
                result = await asyncio.to_thread(score_isi, req.responses)
            else:
                raise HTTPException(400, f"미지원 instrument: {inst}")

            log_id = await asyncio.to_thread(
                ClinicalLogRepo.add, req.user_id, inst, result,
                req.responses if inst != "psqi" else req.psqi_components,
            )

            is_crisis = bool(result.get("suicide_alert"))
            return {
                "log_id": log_id,
                "result": result,
                "legal_notice": build_legal_footer(is_crisis=is_crisis),
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_clinical_trend(self, req: ClinicalLogRequest) -> dict[str, Any]:
        """척도 추세 (첫 측정 vs 최근)."""
        try:
            from engine.storage import ClinicalLogRepo
            from engine.safety import build_legal_footer
            trend = await asyncio.to_thread(
                ClinicalLogRepo.trend, req.user_id, req.instrument
            )
            return {**trend, "legal_notice": build_legal_footer()}
        except Exception as e:
            raise HTTPException(500, str(e))

    # ─────────────────────────── Stickgold 72h 학습 로그 ───────────────────────────
    async def post_learning_add(self, req: LearningLogRequest) -> dict[str, Any]:
        """학습/작업 로그 추가 — Stickgold dream lag 매칭용."""
        try:
            from engine.storage import UserRepo, LearningLogRepo
            await asyncio.to_thread(UserRepo.get_or_create, req.user_id)
            log_id = await asyncio.to_thread(
                LearningLogRepo.add,
                req.user_id, req.activity_text, req.domain, req.activity_at_iso,
            )
            return {"log_id": log_id}
        except Exception as e:
            raise HTTPException(500, str(e))

    # ─────────────────────────── v2 오케스트레이터 ───────────────────────────
    async def post_dream_interpret_v2(
        self, req: InterpretV2Request
    ) -> dict[str, Any]:
        """v2 통합 해석 — 14 에이전트 + 30 도메인 (PRE→ANALYZE→CORE→SYNTH→POST).

        - 사용자별 일일 비용 가드 (기본 20회/24h)
        - 위기 신호 시 익명 통계 자동 누적
        - 캐시 hit 시 비용 0
        """
        try:
            from engine.agents import interpret_dream_v2
            from engine.storage import RateLimitRepo, CrisisStatsRepo, ErrorLogRepo

            # ─── 비용 가드: 사용자별 일일 한도 ───
            daily_limit = int(os.environ.get("V2_DAILY_LIMIT_PER_USER", "20"))
            if req.user_id and req.enable_llm_agents:
                gate = await asyncio.to_thread(
                    RateLimitRepo.check_and_record,
                    req.user_id, "dream_v2",
                    daily_limit=daily_limit, window_sec=86400,
                )
                if not gate["allowed"]:
                    raise HTTPException(
                        429,
                        f"{gate['reason']}. 내일 다시 시도해주세요.",
                    )

            result = await interpret_dream_v2(
                req.dream_text,
                user_id=req.user_id,
                profile=req.profile,
                locale=req.locale,
                religion=req.religion,
                user_target_domain=req.user_target_domain,
                enable_llm_agents=req.enable_llm_agents,
            )

            # ─── 모니터링 + 위기 익명 통계 ───
            try:
                self._analytics["dream_v2_calls"] += 1
                if result.get("crisis_alert"):
                    self._analytics["dream_v2_crisis_blocked"] += 1
                    # 위기 익명 통계 누적 (사용자 ID·텍스트 X)
                    ca = result["crisis_alert"]
                    await asyncio.to_thread(
                        CrisisStatsRepo.add,
                        ca.get("severity", "unknown"),
                        ca.get("matched_count", 0),
                        "dream_v2",
                    )
                if result.get("elapsed_ms"):
                    samples = self._analytics["dream_v2_elapsed_ms_samples"]
                    samples.append(result["elapsed_ms"])
                    self._analytics["dream_v2_elapsed_ms_samples"] = samples[-50:]
                am = result.get("agent_meta") or {}
                persona_key = (am.get("persona") or {}).get("primary")
                if persona_key:
                    self._analytics["dream_v2_persona_counts"][persona_key] = (
                        self._analytics["dream_v2_persona_counts"].get(persona_key, 0) + 1
                    )
                if am.get("is_cathartic"):
                    self._analytics["dream_v2_cathartic_counts"] += 1
            except Exception:
                pass
            return result
        except HTTPException:
            raise
        except Exception as e:
            try:
                from engine.storage import ErrorLogRepo
                await asyncio.to_thread(
                    ErrorLogRepo.add, str(e)[:500], "server",
                    user_id=req.user_id, severity="error",
                )
            except Exception:
                pass
            raise HTTPException(500, str(e))

    async def post_bivalent_feedback(
        self, req: BivalentFeedbackRequest
    ) -> dict[str, Any]:
        """B4 양가 카드 사용자 선택 피드백."""
        try:
            from engine.agents import record_feedback, get_user_feedback_summary
            result = await asyncio.to_thread(
                record_feedback, req.user_id, req.chosen_source, req.polarity, req.keyword
            )
            summary = await asyncio.to_thread(get_user_feedback_summary, req.user_id)
            return {"feedback": result, "summary": summary}
        except Exception as e:
            raise HTTPException(500, str(e))

    # ─────────────────────────── 운영 엔드포인트 ───────────────────────────
    async def get_ops_error_log(self, limit: int = 50, severity: str | None = None) -> dict[str, Any]:
        """최근 N개 에러 로그 (DB 영구). 관리용."""
        try:
            from engine.storage import ErrorLogRepo
            errors = await asyncio.to_thread(ErrorLogRepo.recent, limit, severity)
            return {"count": len(errors), "errors": errors}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_ops_crisis_stats(self, days: int = 30) -> dict[str, Any]:
        """최근 N일 위기 익명 통계. PRIVACY_POLICY §5 — 사용자 ID·텍스트 X."""
        try:
            from engine.storage import CrisisStatsRepo
            stats = await asyncio.to_thread(CrisisStatsRepo.summary, days)
            return stats
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_ops_backup(self) -> dict[str, Any]:
        """수동 DB 백업 트리거 (gzip → /data/backups/, 최근 7개 보관)."""
        try:
            from engine.storage import backup_db
            return await asyncio.to_thread(backup_db, max_keep=7)
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_freud_map(self, req: dict[str, Any]) -> dict[str, Any]:
        """A8 Freud 명시몽→잠재몽 LLM 매핑."""
        try:
            from engine.agents import map_latent_dream
            from engine.safety import detect_crisis, CRISIS_RESPONSE_KO, build_legal_footer
            dream_text = req.get("dream_text", "")
            crisis = detect_crisis(dream_text)
            if crisis["crisis_detected"]:
                return {
                    "text": CRISIS_RESPONSE_KO + build_legal_footer(is_crisis=True),
                    "crisis_alert": {"severity": crisis["severity"]},
                    "mapping": None,
                }
            result = await asyncio.to_thread(
                map_latent_dream, dream_text, req.get("recent_emotions"),
            )
            return {**result, "legal_notice": build_legal_footer()}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_social_unconscious(self, days: int = 7) -> dict[str, Any]:
        """A13 소셜 무의식 — 최근 N일 전체 사용자 일기 토픽 클러스터."""
        try:
            from engine.agents import aggregate_social_unconscious
            return await asyncio.to_thread(
                aggregate_social_unconscious,
                days=days, min_users=30, min_entries=100,
            )
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_legal_terms(self) -> dict[str, Any]:
        """이용약관 텍스트."""
        try:
            from pathlib import Path
            p = Path(__file__).resolve().parent.parent / "docs" / "legal" / "TERMS_OF_SERVICE.md"
            return {"format": "markdown", "content": p.read_text(encoding="utf-8") if p.exists() else "(약관 파일 없음)"}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_legal_privacy(self) -> dict[str, Any]:
        """개인정보처리방침 텍스트."""
        try:
            from pathlib import Path
            p = Path(__file__).resolve().parent.parent / "docs" / "legal" / "PRIVACY_POLICY.md"
            return {"format": "markdown", "content": p.read_text(encoding="utf-8") if p.exists() else "(방침 파일 없음)"}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_hill_step(
        self, req: HillStepRequest
    ) -> dict[str, Any]:
        """Clara Hill 3단계 — 한 단계 실행 (LLM 호출 포함)."""
        try:
            from engine.divination.dream_lex.clara_hill import (
                build_step_prompt, ACTION_CATEGORIES_KO,
            )
            from engine.llm_sync import call_llm_sync
            from engine.safety import detect_crisis, CRISIS_RESPONSE_KO, build_legal_footer

            crisis = detect_crisis(req.dream_text)
            if crisis["crisis_detected"]:
                return {
                    "text": CRISIS_RESPONSE_KO + build_legal_footer(is_crisis=True),
                    "crisis_alert": {
                        "severity": crisis["severity"],
                        "matched_count": len(crisis["matched_keywords"]),
                    },
                    "step": req.step,
                }

            session_data = {
                "dream_text": req.dream_text,
                "exploration_responses": req.exploration_responses,
                "insight_text": req.insight_text,
            }
            prompt_info = await asyncio.to_thread(
                build_step_prompt, req.step, session_data
            )
            try:
                text = await asyncio.to_thread(
                    call_llm_sync,
                    user_text=prompt_info["user_message"],
                    system_prompt=prompt_info["system"],
                )
            except Exception as e:
                text = f"(생성 실패: {e})"

            response: dict[str, Any] = {
                "step": req.step,
                "step_name": prompt_info["step_name"],
                "text": (text or "").strip(),
                "legal_notice": build_legal_footer(),
            }
            # Step 1: 추천 프롬프트도 함께
            if req.step == 1 and "suggested_prompts" in prompt_info:
                response["suggested_prompts"] = prompt_info["suggested_prompts"]
            # Step 3: 행동 카테고리
            if req.step == 3:
                response["action_categories"] = ACTION_CATEGORIES_KO
            return response
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_translate(self, req: TranslateRequest) -> dict[str, Any]:
        """가벼운 번역 — Bizrouter LLM 호출. 짧은 텍스트(가사·해설) 용."""
        try:
            from engine.llm_sync import call_llm_sync

            if not req.text or not req.text.strip():
                return {"translation": "", "target": req.target}
            tgt = req.target
            sys_map = {
                "en": "Translate the following Korean text to natural English. Keep section "
                      "tags like [Verse], [Chorus] as is. Output only the translation, no preamble.",
                "ja": "次の韓国語を自然な日本語に翻訳してください。[Verse]、[Chorus] などの "
                      "タグはそのまま残します。翻訳本文のみ出力。",
            }
            system = sys_map.get(tgt) or sys_map["en"]
            translation = await asyncio.to_thread(
                call_llm_sync, user_text=req.text[:3000], system_prompt=system
            )
            return {"translation": (translation or "").strip(), "target": tgt}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_diag_kasi_verify(self, count: int = 100, start: str | None = None) -> dict[str, Any]:
        """KASI 음양력 API vs 본 시스템 day_pillar 정합 검증 (ADR-084).

        Args:
            count: 검증 일자 수 (기본 100, 최대 1000)
            start: 시작 일자 YYYY-MM-DD (기본 오늘부터 거꾸로)

        Returns:
            { kasi_called: bool, match: int, mismatch: int, skip: int, samples_mismatched: list }
            - 키 부재 시 kasi_called=False + match=N (graceful skip)
            - 키 등록 시 라이브 호출 + 통계 + 불일치 샘플 (개별 키 노출 X)
        """
        from datetime import date as _d, timedelta as _td, datetime as _dt
        from engine.saju.kasi_verifier import batch_verify, kasi_key_available

        count = max(1, min(int(count), 1000))
        if start:
            try:
                start_d = _dt.strptime(start, "%Y-%m-%d").date()
            except Exception:
                start_d = _d.today()
        else:
            start_d = _d.today()

        targets = [start_d - _td(days=i) for i in range(count)]
        match_n, mismatch_n, skip_n, results = batch_verify(targets)

        mismatched_samples = [
            {
                "date": str(r.target_date),
                "local": r.local_iljin_han,
                "kasi": r.kasi_iljin_han,
            }
            for r in results if r.kasi_called and not r.match
        ][:10]

        return {
            "kasi_key_available": kasi_key_available(),
            "kasi_called": any(r.kasi_called for r in results),
            "count_requested": count,
            "count_called": sum(1 for r in results if r.kasi_called),
            "match": match_n,
            "mismatch": mismatch_n,
            "skip": skip_n,
            "samples_mismatched": mismatched_samples,
            "match_rate_pct": round(100 * match_n / max(1, match_n + mismatch_n), 2) if (match_n + mismatch_n) else None,
        }

    async def post_error_log(self, payload: dict[str, Any]) -> dict[str, Any]:
        """클라이언트 에러 로그 수집 — in-memory 50개 + DB 영구."""
        try:
            err = {
                "msg": str(payload.get("msg", ""))[:300],
                "stack": str(payload.get("stack", ""))[:600],
                "url": str(payload.get("url", ""))[:200],
                "ua": str(payload.get("ua", ""))[:200],
                "at": time.time(),
            }
            self._analytics["client_errors"].append(err)
            self._analytics["client_errors"] = self._analytics["client_errors"][-50:]
            # DB 영구화
            try:
                from engine.storage import ErrorLogRepo
                await asyncio.to_thread(
                    ErrorLogRepo.add,
                    err["msg"], "client",
                    stack=err.get("stack"),
                    url=err.get("url"),
                    user_agent=err.get("ua"),
                    user_id=payload.get("user_id"),
                    severity=payload.get("severity", "error"),
                )
            except Exception:
                pass
        except Exception:
            pass
        return {"ok": True}

    async def get_analytics(self) -> dict[str, Any]:
        """가벼운 in-memory 카운터 — 어떤 MBTI/등급이 인기인지 + 비용 추정."""
        a = self._analytics
        m_total = a["cache_music_hit"] + a["cache_music_miss"]
        i_total = a["cache_image_hit"] + a["cache_image_miss"]
        critic_totals = a["image_critic_totals"]
        critic_rounds = a["image_critic_rounds"]
        # 비용 추정 (USD) — 캐시 hit는 비용 0
        # MiniMax music-2.6-free: 무료 / Bizrouter Gemini Flash Lite: ~$0.001/호출 / Nano Banana: ~$0.04/이미지
        est_cost = round(
            (a["cache_music_miss"] + a["cache_image_miss"]) * 0.001  # LLM 평균
            + a["cache_image_miss"] * 0.04  # Nano Banana 이미지
            + a["cache_music_miss"] * 0.0  # MiniMax free
            , 4)
        return {
            "mbti_top": sorted(a["mbti_counts"].items(), key=lambda x: -x[1])[:10],
            "compat_grade_top": sorted(
                a["compat_grade_counts"].items(), key=lambda x: -x[1]
            ),
            "music_calls": a["music_calls"],
            "image_calls": a["image_calls"],
            "compat_music_calls": a["compat_music_calls"],
            "compat_image_calls": a["compat_image_calls"],
            "cache_music_hit_rate": (a["cache_music_hit"] / m_total) if m_total else 0,
            "cache_image_hit_rate": (a["cache_image_hit"] / i_total) if i_total else 0,
            "image_critic_avg_total": (sum(critic_totals) / len(critic_totals)) if critic_totals else None,
            "image_critic_avg_rounds": (sum(critic_rounds) / len(critic_rounds)) if critic_rounds else None,
            "estimated_cost_usd": est_cost,
            "rate_limited_ips": len(self._rate_window),
            "client_errors_count": len(a["client_errors"]),
            "client_errors_recent": a["client_errors"][-5:],
            # v2 오케스트레이션 통계
            "dream_v2_calls": a.get("dream_v2_calls", 0),
            "dream_v2_crisis_blocked": a.get("dream_v2_crisis_blocked", 0),
            "dream_v2_cathartic_counts": a.get("dream_v2_cathartic_counts", 0),
            "dream_v2_persona_top": sorted(
                (a.get("dream_v2_persona_counts") or {}).items(), key=lambda x: -x[1]
            )[:10],
            "dream_v2_avg_elapsed_ms": (
                sum(a.get("dream_v2_elapsed_ms_samples") or [0]) /
                max(1, len(a.get("dream_v2_elapsed_ms_samples") or [1]))
            ),
            "clinical_log_calls": a.get("clinical_log_calls", 0),
            "diary_add_calls": a.get("diary_add_calls", 0),
            "irt_rescript_calls": a.get("irt_rescript_calls", 0),
        }


# === ASGI 앱 인스턴스 (uvicorn 진입점) ===

_server = PersonalityAPIServer()
app = _server.app


__all__ = ["PersonalityAPIServer", "app"]
