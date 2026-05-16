"""9 시스템 통합 진입점 — 동기 + 비동기 클래스 facade."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class EngineConfig:
    """Engine 설정."""

    enable_llm: bool = False  # LLM 해석 자동 호출
    parallel: bool = True  # 비동기 병렬 호출
    timeout_sec: float = 120.0


@dataclass
class EngineResult:
    """assess_all() 반환 — 시스템별 결과 + fusion."""

    saju: dict[str, Any] | None = None
    mbti: dict[str, Any] | None = None
    bigfive: dict[str, Any] | None = None
    enneagram: dict[str, Any] | None = None
    hexaco: dict[str, Any] | None = None
    disc: dict[str, Any] | None = None
    tarot: dict[str, Any] | None = None
    iching: dict[str, Any] | None = None
    fusion: dict[str, Any] | None = None
    interpretations: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "saju": self.saju,
            "mbti": self.mbti,
            "bigfive": self.bigfive,
            "enneagram": self.enneagram,
            "hexaco": self.hexaco,
            "disc": self.disc,
            "tarot": self.tarot,
            "iching": self.iching,
            "fusion": self.fusion,
            "interpretations": dict(self.interpretations),
        }

    def systems(self) -> list[str]:
        return [
            k
            for k in (
                "saju",
                "mbti",
                "bigfive",
                "enneagram",
                "hexaco",
                "disc",
                "tarot",
                "iching",
                "fusion",
            )
            if getattr(self, k)
        ]


class PersonalityEngine:
    """9 시스템 단일 진입점.

    동기/비동기 메서드 모두 제공:
    - 동기: assess_saju(), assess_mbti(), assess_all() 등
    - 비동기: assess_saju_async(), assess_all_async() (병렬 처리)
    """

    def __init__(self, config: EngineConfig | None = None):
        self.config = config or EngineConfig()

    # === 동기 ===

    def assess_saju(
        self,
        dt_local: datetime,
        tz: str = "Asia/Seoul",
        longitude: float = 126.978,
        latitude: float = 37.5665,
        gender: str | None = None,
        is_lunar: bool = False,
        is_leap_month: bool = False,
        time_unknown: bool = False,
    ) -> dict[str, Any]:
        from saju import read, BirthInfo

        bi = BirthInfo(
            dt_local=dt_local,
            tz=tz,
            longitude=longitude,
            latitude=latitude,
            is_lunar=is_lunar,
            is_leap_month=is_leap_month,
            time_unknown=time_unknown,
            gender=gender,
            raw="",
        )
        return read(bi).to_dict()

    def assess_mbti(self, text: str) -> dict[str, Any]:
        from mbti.input.nl_parser import parse_to_answers
        from mbti import assess

        return assess(parse_to_answers(text)).to_dict()

    def assess_bigfive(self, text: str) -> dict[str, Any]:
        from bigfive.input.nl_parser import parse_to_answers
        from bigfive import assess

        return assess(parse_to_answers(text)).to_dict()

    def assess_enneagram(self, text: str) -> dict[str, Any]:
        from enneagram.input.nl_parser import parse_to_answers
        from enneagram import assess

        return assess(parse_to_answers(text)).to_dict()

    def assess_hexaco(self, text: str) -> dict[str, Any]:
        from hexaco.input.nl_parser import parse_to_answers
        from hexaco import assess

        return assess(parse_to_answers(text)).to_dict()

    def assess_disc(self, text: str) -> dict[str, Any]:
        from disc.input.nl_parser import parse_to_answers
        from disc import assess

        return assess(parse_to_answers(text)).to_dict()

    def cast_tarot(
        self, question: str, spread: str = "three", seed: int | None = None
    ) -> dict[str, Any]:
        from tarot import read

        return read(question, spread, seed).to_dict()

    def cast_iching(self, question: str, seed: int | None = None) -> dict[str, Any]:
        from iching import read

        return read(question, seed).to_dict()

    def fuse(self, **systems) -> dict[str, Any]:
        from fusion import fuse as _fuse

        return _fuse(**systems).to_dict()

    # === 비동기 ===

    async def assess_saju_async(self, **kwargs) -> dict[str, Any]:
        return await asyncio.to_thread(self.assess_saju, **kwargs)

    async def _nl_assess_async(self, lib_name: str, text: str) -> dict[str, Any]:
        """비동기 nl_parser 가 있으면 직접 await, 없으면 to_thread fallback."""
        import importlib

        nl_module = importlib.import_module(f"{lib_name}.input.nl_parser")
        parse_async = getattr(nl_module, "parse_to_answers_async", None)
        if parse_async is not None:
            answers = await parse_async(text)
        else:
            parse_sync = nl_module.parse_to_answers
            answers = await asyncio.to_thread(parse_sync, text)

        assess_module = importlib.import_module(lib_name)
        profile = await asyncio.to_thread(assess_module.assess, answers)
        return profile.to_dict()

    async def assess_mbti_async(self, text: str) -> dict[str, Any]:
        return await self._nl_assess_async("mbti", text)

    async def assess_bigfive_async(self, text: str) -> dict[str, Any]:
        return await self._nl_assess_async("bigfive", text)

    async def assess_enneagram_async(self, text: str) -> dict[str, Any]:
        return await self._nl_assess_async("enneagram", text)

    async def assess_hexaco_async(self, text: str) -> dict[str, Any]:
        return await self._nl_assess_async("hexaco", text)

    async def assess_disc_async(self, text: str) -> dict[str, Any]:
        return await self._nl_assess_async("disc", text)

    async def cast_tarot_async(
        self, question: str, spread: str = "three", seed: int | None = None
    ) -> dict[str, Any]:
        return await asyncio.to_thread(self.cast_tarot, question, spread, seed)

    async def cast_iching_async(
        self, question: str, seed: int | None = None
    ) -> dict[str, Any]:
        return await asyncio.to_thread(self.cast_iching, question, seed)

    # === 통합 ===

    async def assess_all_async(
        self,
        nl_text: str | None = None,
        saju_kwargs: dict | None = None,
        oracle_question: str | None = None,
        oracle_seed: int | None = None,
    ) -> EngineResult:
        """모든 가능한 시스템을 병렬 실행 → EngineResult."""
        result = EngineResult()
        tasks: dict[str, asyncio.Task] = {}

        if saju_kwargs:
            tasks["saju"] = asyncio.create_task(self.assess_saju_async(**saju_kwargs))

        if nl_text:
            for name in ("mbti", "bigfive", "enneagram", "hexaco", "disc"):
                method = getattr(self, f"assess_{name}_async")
                tasks[name] = asyncio.create_task(method(nl_text))

        if oracle_question:
            tasks["tarot"] = asyncio.create_task(
                self.cast_tarot_async(oracle_question, "three", oracle_seed)
            )
            tasks["iching"] = asyncio.create_task(
                self.cast_iching_async(oracle_question, oracle_seed)
            )

        for name, task in tasks.items():
            try:
                value = await asyncio.wait_for(task, timeout=self.config.timeout_sec)
                setattr(result, name, value)
            except Exception:
                # 한 시스템 실패해도 나머지는 진행
                continue

        # fusion (성격 시스템들 통합)
        fusion_inputs = {
            k: getattr(result, k)
            for k in ("saju", "mbti", "bigfive", "enneagram", "hexaco", "disc")
            if getattr(result, k) is not None
        }
        if len(fusion_inputs) >= 2:
            from fusion import fuse as _fuse

            result.fusion = _fuse(**fusion_inputs).to_dict()

        return result

    def assess_all(self, **kwargs) -> EngineResult:
        """assess_all_async 동기 wrapper (asyncio.run)."""
        return asyncio.run(self.assess_all_async(**kwargs))
