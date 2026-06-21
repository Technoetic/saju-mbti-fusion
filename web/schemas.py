"""웹 API 요청 모델 (Pydantic BaseModel).

PersonalityAPIServer 핸들러가 사용하는 요청 스키마 정의.
server.py 에서 분리 (구조 리팩터링 2026-06-21) — 동작·필드 불변.
도메인 순서: 사주 → 콘텐츠/도메인 → 임상/IRT → 꿈 → 사용자/인증 → 미디어 → 점술.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

# === 사주 ===


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
