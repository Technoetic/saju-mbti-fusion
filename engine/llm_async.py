"""비동기 LLM 호출 helper.

기본 라우터: Bizrouter (OpenAI 호환, Gemini 2.5 Flash Lite).
fallback: AsyncAnthropic (BIZROUTER_API_KEY 미설정 시).

설정:
- BIZROUTER_API_KEY: Bizrouter API 키 (있으면 자동 사용)
- BIZROUTER_BASE_URL: 기본값 "https://api.bizrouter.ai/v1"
- BIZROUTER_MODEL: 기본값 "google/gemini-2.5-flash-lite"
- ANTHROPIC_API_KEY: fallback 용
"""

from __future__ import annotations

import os
import re
from functools import lru_cache

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

# === Bizrouter 기본값 ===

BIZROUTER_DEFAULT_BASE_URL = "https://api.bizrouter.ai/v1"
BIZROUTER_DEFAULT_MODEL = "google/gemini-2.5-flash-lite"

# === Anthropic fallback ===

_ANTHROPIC_FALLBACK_MODEL = "claude-opus-4-7"
_MAX_TOKENS = 4096


def _bizrouter_enabled() -> bool:
    return bool(os.environ.get("BIZROUTER_API_KEY"))


@lru_cache(maxsize=1)
def bizrouter_async_client() -> AsyncOpenAI:
    """Bizrouter OpenAI 호환 비동기 클라이언트."""
    return AsyncOpenAI(
        api_key=os.environ.get("BIZROUTER_API_KEY"),
        base_url=os.environ.get("BIZROUTER_BASE_URL", BIZROUTER_DEFAULT_BASE_URL),
    )


@lru_cache(maxsize=1)
def anthropic_async_client() -> AsyncAnthropic:
    """Anthropic fallback 비동기 클라이언트."""
    return AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


# 하위 호환: 기존 코드가 import 하던 이름
def async_client():
    """기본 라우터 클라이언트. Bizrouter 활성 시 OpenAI 호환, 아니면 Anthropic."""
    if _bizrouter_enabled():
        return bizrouter_async_client()
    return anthropic_async_client()


_SECTION_PAT = re.compile(r"^##\s+(.+?)$", re.MULTILINE)


def split_sections(raw: str) -> dict[str, str]:
    matches = list(_SECTION_PAT.finditer(raw))
    sections: dict[str, str] = {}
    for i, m in enumerate(matches):
        name = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        sections[name] = raw[start:end].strip()
    return sections


def extract_summary(raw: str) -> str:
    sections = split_sections(raw)
    s = sections.get("요약", "").strip()
    if s:
        return s
    return raw.split("##")[0].strip() if raw.startswith("##") else raw[:200]


async def _call_bizrouter_async(
    user_text: str,
    system_prompt: str,
    model: str | None,
    max_tokens: int,
) -> str:
    client = bizrouter_async_client()
    chosen = model or os.environ.get("BIZROUTER_MODEL", BIZROUTER_DEFAULT_MODEL)
    resp = await client.chat.completions.create(
        model=chosen,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
    )
    if not resp.choices:
        raise ValueError("empty model response")
    content = resp.choices[0].message.content
    if not content:
        raise ValueError("empty model response")
    return content


async def _call_anthropic_async(
    user_text: str,
    system_prompt: str,
    model: str | None,
    max_tokens: int,
    usage_sink: list | None = None,
) -> str:
    client = anthropic_async_client()
    chosen = model or _ANTHROPIC_FALLBACK_MODEL
    msg = await client.messages.create(
        model=chosen,
        max_tokens=max_tokens,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_text}],
    )
    text = next(
        (
            getattr(b, "text", None)
            for b in msg.content
            if getattr(b, "type", "") == "text"
        ),
        None,
    )
    if not text:
        raise ValueError("empty model response")
    if usage_sink is not None:
        usage_sink.append(getattr(msg, "usage", None))
    return text


async def call_llm_async(
    user_text: str,
    system_prompt: str,
    model: str | None = None,
    max_tokens: int = _MAX_TOKENS,
    usage_sink: list | None = None,
) -> str:
    """비동기 LLM 호출 → raw 텍스트.

    Bizrouter (BIZROUTER_API_KEY 설정 시) 우선, 아니면 Anthropic fallback.
    `model=None` 이면 라우터별 기본 모델 사용 (Bizrouter: gemini-2.5-flash-lite).

    Args:
        usage_sink: ADR-013. Anthropic 호출의 usage 객체 sink.
            Bizrouter는 OpenAI 형식이라 append 안 함.
    """
    if _bizrouter_enabled():
        return await _call_bizrouter_async(user_text, system_prompt, model, max_tokens)
    return await _call_anthropic_async(user_text, system_prompt, model, max_tokens, usage_sink=usage_sink)
