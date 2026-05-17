"""Anthropic prompt cache 적중률 측정.

Anthropic API `messages.create()` 응답의 `usage` 객체에서 다음 필드를 추출:
  · input_tokens                — 비캐시 입력 토큰
  · cache_creation_input_tokens — 캐시 기록 (1.25x 단가)
  · cache_read_input_tokens     — 캐시 적중 (0.1x 단가)
  · output_tokens               — 출력 토큰

본 프로젝트는 face_reading / palm_reading / name_reading / saju explain / llm_sync /
llm_async에서 `cache_control: ephemeral`을 system 프롬프트에 일관 적용 중이나,
**적중률 측정 없음**. 본 모듈은 응답을 받은 LLM 호출자가 한 줄로 telemetry를
emit 할 수 있게 한다.

ADR-010 사실성 분리 원칙 적용 — 적중률 단정 없이, 측정값 그대로 반환.

reports/llm-token-caching.md 4차 검토 적용. SLO 시스템(kpi_dashboard
cache_hit_rate)은 L4 응답 캐시 적중률이며 본 모듈은 L2 (Anthropic prompt
cache) 적중률 — 다른 계층임.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PromptCacheUsage:
    """단일 API 호출의 prompt cache 사용량.

    Attributes:
        input_tokens: 비캐시 입력 토큰 (일반 단가).
        cache_creation_input_tokens: 캐시 기록 토큰 (1.25x 단가). 0이면 캐시 기록 없음.
        cache_read_input_tokens: 캐시 적중 토큰 (0.1x 단가). 0이면 캐시 미스 또는 cache_control 미적용.
        output_tokens: 출력 토큰.
        cache_hit: cache_read_input_tokens > 0 이면 True.
        savings_ratio: 캐시로 절약된 토큰 비율 (0.0~1.0). 분모는 총 입력 토큰.
    """

    input_tokens: int
    cache_creation_input_tokens: int
    cache_read_input_tokens: int
    output_tokens: int

    @property
    def cache_hit(self) -> bool:
        return self.cache_read_input_tokens > 0

    @property
    def total_input_tokens(self) -> int:
        return (
            self.input_tokens
            + self.cache_creation_input_tokens
            + self.cache_read_input_tokens
        )

    @property
    def savings_ratio(self) -> float:
        """캐시 적중 비율. 분모가 0이면 0.0 반환 (DIV0 방지)."""
        denom = self.total_input_tokens
        if denom <= 0:
            return 0.0
        return self.cache_read_input_tokens / denom


def extract_usage(usage: Any) -> PromptCacheUsage:
    """Anthropic SDK `Message.usage` 객체 또는 동등 dict에서 안전하게 추출.

    Anthropic SDK는 `Usage` Pydantic 모델 또는 호환 dict를 반환한다.
    필드 부재 시 0으로 기본값 처리 (이전 SDK 버전 호환).

    Bizrouter(OpenAI 호환) 응답은 usage 형식이 다름 (prompt_tokens·completion_tokens)
    → 별도 처리. 본 함수는 Anthropic 형식만 지원.
    """

    def _get(name: str) -> int:
        if usage is None:
            return 0
        # Pydantic 모델 또는 dict 양쪽 지원
        val = getattr(usage, name, None)
        if val is None and isinstance(usage, dict):
            val = usage.get(name)
        if val is None:
            return 0
        try:
            return int(val)
        except (TypeError, ValueError):
            return 0

    return PromptCacheUsage(
        input_tokens=_get("input_tokens"),
        cache_creation_input_tokens=_get("cache_creation_input_tokens"),
        cache_read_input_tokens=_get("cache_read_input_tokens"),
        output_tokens=_get("output_tokens"),
    )


def summarize(usage: PromptCacheUsage) -> dict[str, Any]:
    """SLO 시스템·로그용 평탄화된 dict.

    kpi_dashboard / quick_check 등 기존 측정 모듈에서 그대로 emit 가능한 형식.
    """
    return {
        "input_tokens": usage.input_tokens,
        "cache_creation_input_tokens": usage.cache_creation_input_tokens,
        "cache_read_input_tokens": usage.cache_read_input_tokens,
        "output_tokens": usage.output_tokens,
        "total_input_tokens": usage.total_input_tokens,
        "prompt_cache_hit": usage.cache_hit,
        "prompt_cache_savings_ratio": round(usage.savings_ratio, 4),
    }
