"""통합 요청 파이프라인 — 운영표준 §7.2.22 본문화.

face_reading 요청을 처리하기 전 단계의 모든 사전 게이트를 한 줄로 검사:
  1) rate_limiter — uid 분당/시간당 한도
  2) cost_guard   — 일/월 LLM 비용 한도
  3) input_sanitizer — 화두 본문 정제 + injection 제거
  4) jailbreak_defense — 페르소나 우회·금지 자문 유도 차단
  5) idempotency_key — 동시 in-flight 중복 차단
  6) crisis_detector — 위기 신호 결정론 차단 (기존 face_reading에 있음)

각 단계의 결과를 PipelineDecision으로 합쳐 반환. 호출자는:
  · decision.allowed == True → LLM 호출 진행
  · decision.allowed == False → decision.fallback_response를 사용자에게 직접 반환

본 모듈은 LLM 호출 자체는 하지 않는다. face_reading.generate_face_reading의
"호출 전 사전 점검" 통합 계층.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# §7.2.22 차단 사유 코드
BLOCK_RATE_LIMITED = "rate_limited"
BLOCK_COST_EXHAUSTED = "cost_exhausted"
BLOCK_JAILBREAK = "jailbreak"
BLOCK_INPUT_EMPTY = "input_empty_after_sanitize"


@dataclass(frozen=True)
class PipelineDecision:
    """파이프라인 통합 결정.

    Attributes:
        allowed: True면 LLM 호출 진행, False면 fallback_response 직접 응답
        block_reason: 차단 사유 (allowed=False일 때)
        sanitized_question: 정제된 화두 본문
        idempotency_key: 멱등 키
        idempotency_claimed: 호출자가 LLM 실행 책임자인지
        fallback_response: 차단 시 사용자에게 보일 텍스트 + 메타
        details: 각 단계의 raw 결과
    """
    allowed: bool
    block_reason: str = ""
    sanitized_question: str = ""
    idempotency_key: str = ""
    idempotency_claimed: bool = False
    fallback_response: dict[str, Any] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)


# ─────────────────────────── 통합 진입점 ───────────────────────────

def preflight(
    *,
    image_b64: str | None,
    question: str | None,
    uid: str | None,
    region: str | None = None,
    lang: str = "ko",
    rate_limiter: Any = None,         # RateLimiter 인스턴스 (생략 시 검사 안 함)
    cost_tracker: Any = None,         # CostTracker 인스턴스
    idempotency_manager: Any = None,  # IdempotencyManager 인스턴스
    now: float | None = None,
) -> PipelineDecision:
    """face_reading 호출 직전 사전 점검 — 차단 사유 1개라도 있으면 LLM 호출 차단.

    호출자는 decision.allowed에 따라 분기하면 충분. idempotency_manager가
    주입되었으면 호출자가 slot에 resolve/fail 해야 한다.
    """
    details: dict[str, Any] = {}

    # 1) rate_limiter — uid가 있어야 의미 있음
    if rate_limiter is not None and uid:
        rl_result = rate_limiter.acquire(uid, now=now)
        details["rate_limit"] = {
            "status": rl_result.status,
            "minute_count": rl_result.minute_count,
            "breached_window": rl_result.breached_window,
        }
        if rl_result.status == "limited":
            from engine.safety.legal_notice import build_legal_footer
            from engine.safety.input_sanitizer import sanitize_question
            sanitized = sanitize_question(question)
            return PipelineDecision(
                allowed=False,
                block_reason=BLOCK_RATE_LIMITED,
                sanitized_question=sanitized.text,
                details=details,
                fallback_response={
                    "text": _rate_limited_message(rl_result.retry_after_sec, lang)
                            + build_legal_footer(is_crisis=False, lang=lang),
                    "cached": False,
                    "crisis_alert": None,
                    "error_code": "RATE_LIMITED",
                    "retry_after_sec": rl_result.retry_after_sec,
                },
            )

    # 2) cost_guard
    if cost_tracker is not None:
        cost_status = cost_tracker.status(now=now)
        details["cost"] = {
            "severity": cost_status.severity,
            "daily_percent": cost_status.daily_percent,
            "monthly_percent": cost_status.monthly_percent,
        }
        if cost_status.severity == "exhausted":
            from engine.safety.llm_fallback_router import deterministic_stub_response
            from engine.safety.legal_notice import build_legal_footer
            return PipelineDecision(
                allowed=False,
                block_reason=BLOCK_COST_EXHAUSTED,
                details=details,
                fallback_response={
                    "text": deterministic_stub_response(lang)
                            + build_legal_footer(is_crisis=False, lang=lang),
                    "cached": False,
                    "crisis_alert": None,
                    "error_code": "COST_EXHAUSTED",
                },
            )

    # 3) input_sanitizer
    from engine.safety.input_sanitizer import sanitize_question, to_trace_event
    sanitized = sanitize_question(question)
    details["sanitize"] = to_trace_event(sanitized)

    # question이 처음에 있었는데 정제 후 비면 의심 (injection-only)
    if (question or "").strip() and not sanitized.text:
        from engine.safety.legal_notice import build_legal_footer
        return PipelineDecision(
            allowed=False,
            block_reason=BLOCK_INPUT_EMPTY,
            sanitized_question="",
            details=details,
            fallback_response={
                "text": _empty_after_sanitize_message(lang)
                        + build_legal_footer(is_crisis=False, lang=lang),
                "cached": False,
                "crisis_alert": None,
                "error_code": "INPUT_INVALID",
            },
        )

    # 4) jailbreak_defense (정제된 화두 기준)
    from engine.safety.jailbreak_defense import detect_jailbreak, build_jailbreak_response
    jb_hits = detect_jailbreak(sanitized.text)
    if jb_hits:
        jb = build_jailbreak_response(jb_hits, lang=lang)
        from engine.safety.legal_notice import build_legal_footer
        details["jailbreak"] = {
            "categories": list(jb["categories"]),
            "primary": jb["primary_category"],
        }
        return PipelineDecision(
            allowed=False,
            block_reason=BLOCK_JAILBREAK,
            sanitized_question=sanitized.text,
            details=details,
            fallback_response={
                "text": jb["text"] + build_legal_footer(is_crisis=False, lang=lang),
                "cached": False,
                "crisis_alert": None,
                "error_code": jb["primary_category"],
                "jailbreak_categories": list(jb["categories"]),
            },
        )

    # 5) idempotency_key
    idem_key = ""
    idem_claimed = False
    if idempotency_manager is not None:
        from engine.safety.idempotency_key import compute_idempotency_key
        idem_key = compute_idempotency_key(
            image_b64=image_b64,
            question=sanitized.text,
            uid=uid or "",
            extra=f"{region}:{lang}",
        )
        idem_claimed, _slot = idempotency_manager.claim(idem_key, now=now)
        details["idempotency"] = {
            "key": idem_key,
            "claimed": idem_claimed,
        }

    return PipelineDecision(
        allowed=True,
        sanitized_question=sanitized.text,
        idempotency_key=idem_key,
        idempotency_claimed=idem_claimed,
        details=details,
    )


# ─────────────────────────── 차단 메시지 (사극풍 ko / 평이 en) ───────────────────────────

def _rate_limited_message(retry_after_sec: float, lang: str) -> str:
    if lang == "ko":
        return (
            f"허허, 이 늙은이가 오늘은 그대를 너무 자주 만났구먼. "
            f"잠시 {int(retry_after_sec)}초쯤 쉬었다가 다시 부탁하시게."
        )
    return (
        f"You have made many requests in a short time. "
        f"Please try again in about {int(retry_after_sec)} seconds."
    )


def _empty_after_sanitize_message(lang: str) -> str:
    if lang == "ko":
        return "허허, 화두가 비어 보이는구먼. 다시 한 번 정성껏 적어주시게."
    return "Your question appears empty after cleaning. Please rephrase."


# ─────────────────────────── tracing ───────────────────────────

def to_trace_event(decision: PipelineDecision) -> dict[str, Any]:
    """§7.3.4 tracing extra 호환 페이로드."""
    return {
        "pipeline_allowed": decision.allowed,
        "pipeline_block_reason": decision.block_reason,
        "pipeline_idempotency_claimed": decision.idempotency_claimed,
    }
