"""CLI 공통 베이스 — 클래스 지향 + 비동기 main 지원."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from abc import ABC, abstractmethod
from typing import Any


class BaseCLI(ABC):
    """모든 라이브러리 CLI 의 공통 베이스.

    하위 클래스는 다음을 구현:
    - prog_name: CLI 명
    - build_parser(): argparse 설정
    - run_async(args): 비동기 본 로직 → JSON 직렬화 가능 dict
    """

    prog_name: str = "personality"

    @abstractmethod
    def build_parser(self) -> argparse.ArgumentParser: ...

    @abstractmethod
    async def run_async(self, args: argparse.Namespace) -> dict[str, Any]: ...

    def run(self, argv: list[str] | None = None) -> int:
        """동기 진입점 — asyncio.run 으로 run_async 호출."""
        parser = self.build_parser()
        args = parser.parse_args(argv)
        try:
            payload = asyncio.run(self.run_async(args))
        except Exception as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        sys.stdout.buffer.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        sys.stdout.write("\n")
        return 0
