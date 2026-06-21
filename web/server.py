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


from web.handlers.saju import SajuHandlersMixin
from web.handlers.domain import DomainHandlersMixin
from web.handlers.dream import DreamHandlersMixin
from web.handlers.palmface import PalmFaceHandlersMixin
from web.handlers.clinical import ClinicalHandlersMixin
from web.handlers.user import UserHandlersMixin
from web.handlers.ops import OpsHandlersMixin

# === 요청 모델 (web/schemas.py 로 분리 — 구조 리팩터링 2026-06-21) ===
from web.schemas import (  # noqa: E402
    AssessAllRequest,
    BivalentFeedbackRequest,
    ClinicalLogRequest,
    ClinicalScreeningRequest,
    ConsentRequest,
    ContentReadingRequest,
    DiaryAddRequest,
    DormioSessionRequest,
    DormioSynthesizeRequest,
    DreamInterpretRequest,
    FaceReadingRequest,
    HillStepRequest,
    HVdCLLMRequest,
    HwapaeCard,
    HwapaeReadingRequest,
    IChingDivinationRequest,
    IChingRequest,
    IncubationRequest,
    InterpretV2Request,
    IRTRescriptRequest,
    LearningLogRequest,
    LLMChatRequest,
    LoginRequest,
    LucidProgramRequest,
    MoodCurveRequest,
    MyoeLongTermRequest,
    NameReadingRequest,
    PalmReadingRequest,
    SajuAskRequest,
    SajuCompatBatchRequest,
    SajuCompatMusicRequest,
    SajuCompatPerson,
    SajuCompatRequest,
    SajuExplainRequest,
    SajuFusionRequest,
    SajuImageRequest,
    SajuMusicRequest,
    SajuMyeongRequest,
    SajuRequest,
    SignupRequest,
    StarReadingRequest,
    TarotRequest,
    TranslateRequest,
    UllmanGroupRequest,
    UserProfileRequest,
    UserScopedRequest,
)


# === API 서버 클래스 ===


class PersonalityAPIServer(
    SajuHandlersMixin,
    DomainHandlersMixin,
    DreamHandlersMixin,
    PalmFaceHandlersMixin,
    ClinicalHandlersMixin,
    UserHandlersMixin,
    OpsHandlersMixin,
):
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
        self.app.post("/api/hwapae/reading")(self.post_hwapae_reading)
        self.app.post("/api/saju/webtoon")(self.post_saju_webtoon)
        self.app.post("/api/face/reading")(self.post_face_reading)
        self.app.post("/api/palm/reading")(self.post_palm_reading)
        self.app.get("/api/palm/diagnostics")(self.get_palm_diagnostics)
        self.app.post("/api/star/reading")(self.post_star_reading)
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

_server = PersonalityAPIServer()
app = _server.app


__all__ = ["PersonalityAPIServer", "app"]
