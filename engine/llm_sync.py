"""동기 LLM 호출 helper — Bizrouter 우선, Anthropic fallback.

기존 동기 explain.py 들이 라우터 추상화 없이 Anthropic 만 직접 호출했음.
이 helper 는 BIZROUTER_API_KEY 가 있으면 Bizrouter (OpenAI 호환) 사용.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache

from anthropic import Anthropic
from openai import OpenAI

from engine.llm_async import (
    BIZROUTER_DEFAULT_BASE_URL,
    BIZROUTER_DEFAULT_MODEL,
    _anthropic_enabled,
    _bizrouter_enabled,
)

_log = logging.getLogger(__name__)


_ANTHROPIC_FALLBACK_MODEL = "claude-opus-4-7"
_MAX_TOKENS = 4096


@lru_cache(maxsize=1)
def bizrouter_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ.get("BIZROUTER_API_KEY"),
        base_url=os.environ.get("BIZROUTER_BASE_URL", BIZROUTER_DEFAULT_BASE_URL),
    )


@lru_cache(maxsize=1)
def anthropic_client() -> Anthropic:
    return Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def _call_bizrouter_sync(
    user_text: str, system_prompt: str, model: str | None, max_tokens: int
) -> str:
    client = bizrouter_client()
    chosen: str = model or os.environ.get("BIZROUTER_MODEL") or BIZROUTER_DEFAULT_MODEL
    resp = client.chat.completions.create(
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


def _call_anthropic_sync(
    user_text: str,
    system_prompt: str,
    model: str | None,
    max_tokens: int,
    usage_sink: list | None = None,
) -> str:
    anthropic = anthropic_client()
    chosen = model or _ANTHROPIC_FALLBACK_MODEL
    msg = anthropic.messages.create(
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


def call_llm_sync(
    user_text: str,
    system_prompt: str,
    model: str | None = None,
    max_tokens: int = _MAX_TOKENS,
    usage_sink: list | None = None,
) -> str:
    """동기 LLM 호출. Bizrouter 우선, Anthropic fallback.

    Bizrouter 호출이 실패(외부 장애·5xx·Redis 등)하면 Anthropic 키가 있을 때
    런타임 폴백한다. 둘 다 없거나 폴백도 실패하면 원래 예외를 전파한다.

    Args:
        usage_sink: ADR-013. Anthropic 호출의 usage 객체 sink.
            Bizrouter는 OpenAI 형식이라 append 안 함.
    """
    if _bizrouter_enabled():
        try:
            return _call_bizrouter_sync(user_text, system_prompt, model, max_tokens)
        except Exception as exc:
            if not _anthropic_enabled():
                raise
            _log.warning("Bizrouter 호출 실패 → Anthropic 폴백: %s", exc, exc_info=False)
            fallback_model = model if (model and model.startswith("claude")) else None
            return _call_anthropic_sync(
                user_text, system_prompt, fallback_model, max_tokens, usage_sink=usage_sink
            )
    return _call_anthropic_sync(
        user_text, system_prompt, model, max_tokens, usage_sink=usage_sink
    )
