"""다중 LLM 폴백 라우터 — 운영표준 §7.2.11 본문화.

Primary(Google Gemini Vision) → Secondary(Anthropic Claude Vision) →
Tertiary(deterministic stub)의 3단계 폴백 정책을 결정한다.

본 모듈은 실제 LLM 호출은 수행하지 않는다. 다음만 결정:
  · 호출 순서 (primary first, 또는 region에 따라 secondary first)
  · 각 호출의 timeout / max_tokens
  · 응답 부적격(빈 문자열·페르소나 톤 실패) 시 다음 단계 시도 여부
  · 최종 실패 시 deterministic stub 응답으로 fallback

§7.2.11 폴백 트리거:
  1) 네트워크 예외 (timeout / connection error / 5xx)
  2) 응답 빈 문자열 또는 토큰 한도 초과
  3) persona_self_eval.passed == False (페르소나 회귀)
  4) jailbreak_defense가 LLM 응답에서 금지 카테고리를 추가로 검출

지역 가중치:
  · KR/JP/CN  — Gemini 우선 (한국어 quality 좋음)
  · EU/UK     — Claude 우선 (Anthropic EU DPA)
  · US-CA/IL  — Gemini 우선
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# §7.2.11 — 백엔드 식별자
BACKEND_GEMINI = "gemini_vision"
BACKEND_CLAUDE = "claude_vision"
BACKEND_STUB = "deterministic_stub"

# 지역별 우선순위 — Anthropic은 EU에 dedicated DPA 있어 EU 트래픽은 Claude 우선.
_PREFERENCE_BY_REGION = {
    "EU": (BACKEND_CLAUDE, BACKEND_GEMINI),
    "DE": (BACKEND_CLAUDE, BACKEND_GEMINI),
    "FR": (BACKEND_CLAUDE, BACKEND_GEMINI),
    "UK": (BACKEND_CLAUDE, BACKEND_GEMINI),
    "GB": (BACKEND_CLAUDE, BACKEND_GEMINI),
    "KR": (BACKEND_GEMINI, BACKEND_CLAUDE),
    "JP": (BACKEND_GEMINI, BACKEND_CLAUDE),
    "CN": (BACKEND_GEMINI, BACKEND_CLAUDE),
    "US-CA": (BACKEND_GEMINI, BACKEND_CLAUDE),
    "US-IL": (BACKEND_GEMINI, BACKEND_CLAUDE),
}
_DEFAULT_PREFERENCE = (BACKEND_GEMINI, BACKEND_CLAUDE)


# §7.2.11 — 단계별 시간 예산 (ms). 합계가 SLO p99 < 8000ms 안에 들어가야.
_BUDGETS_MS = {
    BACKEND_GEMINI: {"timeout_ms": 4000, "max_tokens": 3000},
    BACKEND_CLAUDE: {"timeout_ms": 4000, "max_tokens": 3000},
    BACKEND_STUB: {"timeout_ms": 50, "max_tokens": 0},
}


@dataclass(frozen=True)
class LLMCallPlan:
    """단일 LLM 호출의 시간/토큰 예산 + 백엔드."""
    backend: str
    timeout_ms: int
    max_tokens: int
    is_fallback: bool = False  # primary가 아닌가
    is_last_resort: bool = False  # stub인가


@dataclass
class FallbackDecision:
    """plan_llm_calls 산출물 — 외부 호출자가 순서대로 시도."""
    plans: list[LLMCallPlan] = field(default_factory=list)
    region_preference: tuple[str, str] = _DEFAULT_PREFERENCE


# ─────────────────────────── 1) 폴백 트리거 ───────────────────────────

# 폴백 사유 enum
TRIGGER_NETWORK_ERROR = "network_error"
TRIGGER_EMPTY_RESPONSE = "empty_response"
TRIGGER_TOKEN_LIMIT = "token_limit"
TRIGGER_PERSONA_FAILED = "persona_failed"
TRIGGER_JAILBREAK_LEAK = "jailbreak_leak"
TRIGGER_NONE = ""


def classify_failure(
    *,
    exception: Exception | None = None,
    response_text: str | None = None,
    persona_passed: bool | None = None,
    jailbreak_categories: list[str] | None = None,
) -> str:
    """단일 LLM 호출 결과를 받아 폴백 트리거 분류. TRIGGER_NONE이면 응답 사용 가능.

    Args:
        exception: 네트워크/timeout 예외. None이면 정상.
        response_text: LLM 응답 본문 (None이거나 빈 문자열이면 폴백).
        persona_passed: persona_self_eval 결과. False면 폴백.
        jailbreak_categories: LLM 응답에서 검출된 jailbreak 카테고리. 있으면 폴백.
    """
    if exception is not None:
        return TRIGGER_NETWORK_ERROR
    if response_text is None or not response_text.strip():
        return TRIGGER_EMPTY_RESPONSE
    if response_text.endswith("..."):
        # 일반적 LLM 토큰 한도 truncation 표시 — 보수적으로 폴백
        return TRIGGER_TOKEN_LIMIT
    if persona_passed is False:
        return TRIGGER_PERSONA_FAILED
    if jailbreak_categories:
        return TRIGGER_JAILBREAK_LEAK
    return TRIGGER_NONE


def should_fallback(trigger: str) -> bool:
    return trigger != TRIGGER_NONE


# ─────────────────────────── 2) 계획 ───────────────────────────

def get_region_preference(region: str | None) -> tuple[str, str]:
    """region → (primary_backend, secondary_backend) 튜플."""
    if not region:
        return _DEFAULT_PREFERENCE
    return _PREFERENCE_BY_REGION.get(region.strip().upper(), _DEFAULT_PREFERENCE)


def plan_llm_calls(
    *,
    region: str | None = None,
    include_stub: bool = True,
) -> FallbackDecision:
    """3단계 호출 계획. 외부 호출자가 plans를 순회하며 시도.

    Args:
        region: 지역별 backend 가중치 적용.
        include_stub: 최종 stub fallback 포함 여부. False면 2단계만.

    Returns:
        FallbackDecision — plans 리스트 (primary, secondary, [stub]).
    """
    primary, secondary = get_region_preference(region)
    plans: list[LLMCallPlan] = []

    pb = _BUDGETS_MS[primary]
    plans.append(LLMCallPlan(
        backend=primary,
        timeout_ms=pb["timeout_ms"],
        max_tokens=pb["max_tokens"],
        is_fallback=False,
    ))

    sb = _BUDGETS_MS[secondary]
    plans.append(LLMCallPlan(
        backend=secondary,
        timeout_ms=sb["timeout_ms"],
        max_tokens=sb["max_tokens"],
        is_fallback=True,
    ))

    if include_stub:
        stb = _BUDGETS_MS[BACKEND_STUB]
        plans.append(LLMCallPlan(
            backend=BACKEND_STUB,
            timeout_ms=stb["timeout_ms"],
            max_tokens=stb["max_tokens"],
            is_fallback=True,
            is_last_resort=True,
        ))

    return FallbackDecision(plans=plans, region_preference=(primary, secondary))


# ─────────────────────────── 3) 결정론 stub 응답 ───────────────────────────

# §7.2.11 — 모든 LLM이 실패했을 때 사용자에게 돌려보낼 최소 안전 응답.
# 페르소나 톤 통과(encouraged_hits ≥ 3) + 면책 호환.
_STUB_RESPONSE_KO = (
    "허허, 그대, 자네의 상을 살피려 하였으나 이 늙은이의 결이 흐려 짚지 못하였네. "
    "잠시 뒤 다시 부탁하시게나. 이 늙은이가 곧 본 자리로 돌아옴이로세."
)

_STUB_RESPONSE_EN = (
    "We could not complete your reading right now. Please try again shortly."
)

_STUB_RESPONSE_JA = (
    "ただいま鑑定がうまくいきませんでした。しばらく経ってから再度お試しください。"
)

_STUB_RESPONSE_ZH = (
    "本次解读暂时无法完成,请稍后再试。"
)

_STUB_BY_LANG = {
    "ko": _STUB_RESPONSE_KO,
    "en": _STUB_RESPONSE_EN,
    "ja": _STUB_RESPONSE_JA,
    "zh": _STUB_RESPONSE_ZH,
}


def deterministic_stub_response(lang: str = "ko") -> str:
    """모든 LLM 실패 시의 최소 안전 응답. 4언어 지원."""
    return _STUB_BY_LANG.get(lang, _STUB_RESPONSE_EN)


# ─────────────────────────── 4) 추적 페이로드 ───────────────────────────

def to_trace_event(
    *,
    backend: str,
    trigger: str,
    attempt_index: int,
    elapsed_ms: int,
) -> dict[str, Any]:
    """§7.3.4 tracing extra 호환 페이로드.

    호출자가 emit_face_reading_event(extra=...)로 그대로 전달.
    """
    return {
        "llm_backend": backend,
        "llm_fallback_trigger": trigger,
        "llm_attempt_index": attempt_index,
        "llm_elapsed_ms": elapsed_ms,
        "llm_used_fallback": attempt_index > 0,
    }
