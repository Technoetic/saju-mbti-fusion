"""LLM 출력 안전망 — 운영표준 §7.2.21 본문화.

모든 후처리 검증을 단일 진입점으로 묶어 face_reading이 한 번에 호출.
실패 검증이 있으면 llm_fallback_router 폴백 트리거 결정.

§7.2.21 게이트 (실행 순서, 가장 빠른 실패 우선):
  1) output_token_guard   — 길이·종결·언어 drift·반복
  2) response_pii_leak    — PII 누출 (즉시 폐기 권장)
  3) persona_self_eval    — 사극풍 어휘 / 금지어
  4) response_fact_check  — 메트릭·age·gender 정합
  5) response_alignment   — 화두 주제와 응답 정렬

각 단계는 독립 평가 + 결과 수집. 최종 verdict:
  · CLEAN — 모든 게이트 통과
  · CRITICAL — PII 누출 (응답 폐기 + persona_failed)
  · WARN — 페르소나/정렬/사실 위반 (폴백 후 stub)
  · MINOR — 너무 짧음·짧은 truncation (재호출 가능)

본 모듈은 검증만 — 응답 수정 X.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# §7.2.21 게이트 결과 등급
VERDICT_CLEAN = "clean"
VERDICT_MINOR = "minor"        # 사소한 회귀 — 재호출 권장
VERDICT_WARN = "warn"          # 페르소나/정렬 — 폴백 권장
VERDICT_CRITICAL = "critical"  # PII/안전 — 응답 폐기


@dataclass(frozen=True)
class SafetyGateResult:
    verdict: str
    failures: list[str] = field(default_factory=list)  # ["pii_leak", "persona_failed", ...]
    details: dict[str, Any] = field(default_factory=dict)  # 각 게이트 raw 결과
    fallback_trigger: str = ""  # llm_fallback_router 호환

    @property
    def is_clean(self) -> bool:
        return self.verdict == VERDICT_CLEAN


# ─────────────────────────── 통합 진입점 ───────────────────────────

def run_safety_gates(
    response_text: str | None,
    *,
    question: str | None = None,
    age: int | None = None,
    gender: str | None = None,
    metrics: dict[str, Any] | None = None,
    region: str | None = None,
    lang: str = "ko",
) -> SafetyGateResult:
    """모든 후처리 게이트를 순서대로 실행.

    Args:
        response_text: LLM 응답 본문 (legal/disclosure 추가 전이 정확)
        question: 화두 본문 (alignment 검증용)
        age/gender/metrics/region: 입력 보조정보 (fact_check용)
        lang: 'ko'면 한글 비율 검사 활성화 (token_guard용)
    """
    if not response_text or not isinstance(response_text, str):
        return SafetyGateResult(
            verdict=VERDICT_CRITICAL,
            failures=["empty_response"],
            fallback_trigger="empty_response",
        )

    failures: list[str] = []
    details: dict[str, Any] = {}
    has_critical = False
    has_warn = False
    has_minor = False

    # 1) output_token_guard
    from engine.safety.output_token_guard import (
        evaluate_output, ISSUE_TOO_SHORT, ISSUE_TRUNCATED,
    )
    token_r = evaluate_output(response_text, lang=lang)
    details["token_guard"] = {
        "issues": list(token_r.issues),
        "score": getattr(token_r, "char_count", 0),
    }
    if token_r.issues:
        failures.append("token_guard")
        # short / truncated → minor (재호출 가능)
        if ISSUE_TOO_SHORT in token_r.issues or ISSUE_TRUNCATED in token_r.issues:
            has_minor = True
        else:
            has_warn = True

    # 2) response_pii_leak — PII는 즉시 critical
    from engine.safety.response_pii_leak import scan_response_pii
    pii_r = scan_response_pii(response_text)
    details["pii_leak"] = {
        "leaks": list(pii_r.leaks),
        "sample_count": len(pii_r.matched_samples),
    }
    if pii_r.leaks:
        failures.append("pii_leak")
        has_critical = True

    # 3) persona_self_eval
    from engine.safety.persona_self_eval import evaluate_persona_tone
    persona_r = evaluate_persona_tone(response_text)
    details["persona"] = {
        "passed": persona_r.passed,
        "score": persona_r.score,
        "forbidden_hits": persona_r.forbidden_hits,
        "medical_legal_hits": persona_r.medical_legal_hits,
    }
    if not persona_r.passed:
        failures.append("persona_failed")
        has_warn = True

    # 4) response_fact_check
    from engine.safety.response_fact_check import check_response
    fact_r = check_response(
        response_text,
        age=age,
        gender=gender,
        metrics=metrics,
        region=region,
    )
    details["fact_check"] = {
        "violations": list(fact_r.violations),
        "matched_terms": list(fact_r.matched_terms),
    }
    if fact_r.violations:
        failures.append("fact_mismatch")
        has_warn = True

    # 5) response_alignment
    from engine.safety.response_alignment import evaluate_alignment
    align_r = evaluate_alignment(question=question, response_text=response_text)
    details["alignment"] = {
        "topic_detected": align_r.topic_detected,
        "issues": list(align_r.issues),
        "response_has_topic": align_r.response_has_topic,
    }
    if align_r.issues:
        failures.append("alignment_failed")
        has_warn = True

    # 종합 verdict — critical > warn > minor > clean
    if has_critical:
        verdict = VERDICT_CRITICAL
        fb = "persona_failed"
    elif has_warn:
        verdict = VERDICT_WARN
        fb = "persona_failed"
    elif has_minor:
        verdict = VERDICT_MINOR
        # truncated → token_limit, short → empty_response
        if ISSUE_TRUNCATED in token_r.issues:
            fb = "token_limit"
        else:
            fb = "empty_response"
    else:
        verdict = VERDICT_CLEAN
        fb = ""

    return SafetyGateResult(
        verdict=verdict,
        failures=failures,
        details=details,
        fallback_trigger=fb,
    )


def should_fallback(result: SafetyGateResult) -> bool:
    """게이트 결과 → 폴백 필요 여부. CLEAN만 False."""
    return result.verdict != VERDICT_CLEAN


def to_trace_event(result: SafetyGateResult) -> dict[str, Any]:
    """§7.3.4 tracing extra 호환 페이로드."""
    return {
        "safety_gate_verdict": result.verdict,
        "safety_gate_failures": list(result.failures),
        "safety_gate_failure_count": len(result.failures),
        "safety_gate_fallback_trigger": result.fallback_trigger,
    }


def to_alert_payload(result: SafetyGateResult) -> dict[str, Any]:
    """§14.3 alert_router 호환 페이로드.

    CRITICAL → P0 (PII 누출 즉시 호출)
    WARN     → P1
    MINOR    → P2
    CLEAN    → P3
    """
    sev_map = {
        VERDICT_CRITICAL: "P0",
        VERDICT_WARN: "P1",
        VERDICT_MINOR: "P2",
        VERDICT_CLEAN: "P3",
    }
    return {
        "service": "output_safety_gate",
        "severity": sev_map.get(result.verdict, "P3"),
        "verdict": result.verdict,
        "failure_count": len(result.failures),
        "failures": list(result.failures),
        "fallback_trigger": result.fallback_trigger,
    }
