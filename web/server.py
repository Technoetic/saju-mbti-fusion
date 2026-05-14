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

from fastapi import FastAPI, HTTPException
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
    """운학 도사 얼굴 풀이 요청 — 사진(base64) + 보조 정보."""

    image_base64: str  # data URL 또는 raw base64. 1024px 이하 권장.
    age: int | None = None
    gender: str | None = None  # 'M' / 'F' / 자유 문자열
    question: str | None = None  # 화두


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

        # GET "/" 직접 처리 — StaticFiles mount보다 먼저 등록되어야 catch.
        # 새 배포마다 사용자 브라우저가 옛 HTML을 캐싱해 깨지는 사고 방지.
        from fastapi.responses import FileResponse

        @self.app.get("/", include_in_schema=False)
        async def serve_index_no_cache():
            front_dir = Path(__file__).resolve().parent.parent / "front"
            index_path = front_dir / "index.html"
            if not index_path.exists():
                index_path = Path(__file__).resolve().parent / "index.html"
            return FileResponse(
                str(index_path),
                media_type="text/html; charset=utf-8",
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
        self.app.post("/api/face/reading")(self.post_face_reading)
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
        bizrouter_model = os.environ.get(
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

    async def post_hwapae_reading(
        self, req: HwapaeReadingRequest
    ) -> dict[str, Any]:
        """화선 낭자 화패 풀이 — critic 루프 + 캐시 적용 백엔드 에이전트."""
        try:
            from engine.divination.hwapae import generate_hwapae_reading

            cards = [c.model_dump() for c in req.cards]
            result = await asyncio.to_thread(
                generate_hwapae_reading,
                req.question,
                cards,
                req.category,
                req.menu_label,
            )
            return result
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_face_reading(
        self, req: FaceReadingRequest
    ) -> dict[str, Any]:
        """운학 도사 얼굴 풀이 — Gemini Vision 멀티모달 호출 + 캐시."""
        try:
            from engine.divination.face_reading import generate_face_reading

            result = await asyncio.to_thread(
                generate_face_reading,
                req.image_base64,
                req.age,
                req.gender,
                req.question,
            )
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
