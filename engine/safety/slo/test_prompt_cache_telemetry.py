"""engine.safety.slo.prompt_cache_telemetry — 회귀 테스트.

ADR-010 사실성 분리 적용 + reports/llm-token-caching.md L2 측정.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── PromptCacheUsage 기본 ───────────────────────────


def test_cache_hit_when_read_positive():
    from engine.safety.slo.prompt_cache_telemetry import PromptCacheUsage
    u = PromptCacheUsage(
        input_tokens=100,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=500,
        output_tokens=200,
    )
    assert u.cache_hit is True


def test_cache_miss_when_read_zero():
    from engine.safety.slo.prompt_cache_telemetry import PromptCacheUsage
    u = PromptCacheUsage(
        input_tokens=600,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=0,
        output_tokens=200,
    )
    assert u.cache_hit is False


def test_total_input_sums_three_fields():
    from engine.safety.slo.prompt_cache_telemetry import PromptCacheUsage
    u = PromptCacheUsage(
        input_tokens=100,
        cache_creation_input_tokens=200,
        cache_read_input_tokens=300,
        output_tokens=400,
    )
    assert u.total_input_tokens == 600
    # output_tokens는 input 합산에 포함 안 됨


def test_savings_ratio_calculation():
    """500 cache_read / 600 total_input = 0.833…"""
    from engine.safety.slo.prompt_cache_telemetry import PromptCacheUsage
    u = PromptCacheUsage(
        input_tokens=100,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=500,
        output_tokens=200,
    )
    assert 0.83 < u.savings_ratio < 0.84


def test_savings_ratio_zero_when_no_tokens():
    """입력 토큰이 0이면 DIV0 방지로 0.0 반환."""
    from engine.safety.slo.prompt_cache_telemetry import PromptCacheUsage
    u = PromptCacheUsage(0, 0, 0, 0)
    assert u.savings_ratio == 0.0


# ─────────────────────────── extract_usage ───────────────────────────


def test_extract_from_dict():
    from engine.safety.slo.prompt_cache_telemetry import extract_usage
    usage_dict = {
        "input_tokens": 100,
        "cache_creation_input_tokens": 50,
        "cache_read_input_tokens": 800,
        "output_tokens": 150,
    }
    u = extract_usage(usage_dict)
    assert u.input_tokens == 100
    assert u.cache_creation_input_tokens == 50
    assert u.cache_read_input_tokens == 800
    assert u.output_tokens == 150
    assert u.cache_hit is True


def test_extract_from_object():
    """Anthropic SDK Pydantic 모델 호환 — 속성 접근."""
    from engine.safety.slo.prompt_cache_telemetry import extract_usage

    class FakeUsage:
        input_tokens = 200
        cache_creation_input_tokens = 0
        cache_read_input_tokens = 0
        output_tokens = 300
        # cache_creation·read 필드 부재 케이스 (이전 SDK)

    u = extract_usage(FakeUsage())
    assert u.input_tokens == 200
    assert u.output_tokens == 300


def test_extract_handles_missing_fields():
    """일부 필드 부재 시 0으로 기본값 처리."""
    from engine.safety.slo.prompt_cache_telemetry import extract_usage
    u = extract_usage({"input_tokens": 100, "output_tokens": 50})
    assert u.input_tokens == 100
    assert u.cache_creation_input_tokens == 0
    assert u.cache_read_input_tokens == 0
    assert u.output_tokens == 50


def test_extract_handles_none():
    """usage가 None인 경우 모두 0."""
    from engine.safety.slo.prompt_cache_telemetry import extract_usage
    u = extract_usage(None)
    assert u.total_input_tokens == 0
    assert u.cache_hit is False
    assert u.savings_ratio == 0.0


def test_extract_handles_invalid_value():
    """문자열·None 등 비정수 값은 0으로."""
    from engine.safety.slo.prompt_cache_telemetry import extract_usage
    u = extract_usage({
        "input_tokens": "not-a-number",
        "cache_read_input_tokens": None,
        "output_tokens": 100,
    })
    assert u.input_tokens == 0
    assert u.cache_read_input_tokens == 0
    assert u.output_tokens == 100


# ─────────────────────────── summarize ───────────────────────────


def test_summarize_returns_flat_dict():
    from engine.safety.slo.prompt_cache_telemetry import PromptCacheUsage, summarize
    u = PromptCacheUsage(100, 50, 500, 200)
    s = summarize(u)
    assert s["input_tokens"] == 100
    assert s["cache_creation_input_tokens"] == 50
    assert s["cache_read_input_tokens"] == 500
    assert s["output_tokens"] == 200
    assert s["total_input_tokens"] == 650
    assert s["prompt_cache_hit"] is True
    assert isinstance(s["prompt_cache_savings_ratio"], float)
    assert 0.76 < s["prompt_cache_savings_ratio"] < 0.78


def test_summarize_cache_miss():
    from engine.safety.slo.prompt_cache_telemetry import PromptCacheUsage, summarize
    u = PromptCacheUsage(600, 0, 0, 200)
    s = summarize(u)
    assert s["prompt_cache_hit"] is False
    assert s["prompt_cache_savings_ratio"] == 0.0
