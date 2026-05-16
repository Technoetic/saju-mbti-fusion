"""9 시스템 통합 facade.

배포 환경(사주 단독)에서는 engine.core (9-시스템 facade) 가 의존하는
다른 도메인 (mbti/bigfive/...) 폴더가 없을 수 있으므로 optional import.
"""

__version__ = "1.1.0"

try:
    from engine.core import EngineConfig, EngineResult, PersonalityEngine

    _CORE_AVAILABLE = True
except ImportError:
    PersonalityEngine = None  # type: ignore
    EngineConfig = None  # type: ignore
    EngineResult = None  # type: ignore
    _CORE_AVAILABLE = False

from engine.cli_base import BaseCLI
from engine.llm_async import (
    BIZROUTER_DEFAULT_BASE_URL,
    BIZROUTER_DEFAULT_MODEL,
    anthropic_async_client,
    async_client,
    bizrouter_async_client,
    call_llm_async,
    extract_summary,
    split_sections,
)
from engine.llm_sync import anthropic_client, bizrouter_client, call_llm_sync

__all__ = [
    "PersonalityEngine",
    "EngineConfig",
    "EngineResult",
    "async_client",
    "call_llm_async",
    "call_llm_sync",
    "bizrouter_async_client",
    "anthropic_async_client",
    "bizrouter_client",
    "anthropic_client",
    "split_sections",
    "extract_summary",
    "BIZROUTER_DEFAULT_BASE_URL",
    "BIZROUTER_DEFAULT_MODEL",
    "BaseCLI",
    "__version__",
]
