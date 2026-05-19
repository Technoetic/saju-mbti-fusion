"""LLM 운영 출력 샘플러 — 백그라운드 fire-and-forget 로깅.

ADR-005 Supplement 2~7: 운명 매핑 어휘 모니터링 의무 이행.
사용자 영향 0 — 실패 시 silent, 비동기 없음 (동기 I/O, 1% 샘플링).

출력 경로: step_archive/llm_output_samples/<YYYY-MM-DD>.jsonl
운명 어휘 발견 시 카운터 증가 (step_archive/llm_output_samples/fate_counter.json).
"""

from __future__ import annotations

import json
import random
import re
import time
from datetime import date
from pathlib import Path
from typing import Optional

# ─── 운명 매핑 어휘 패턴 (ADR-005 Supplement 2~7 준수) ───────────────────────
_FATE_VOCAB_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?:초년|중년|말년)[\s\S]{0,20}(?:복록|운|기운|길|흉)"),
    re.compile(r"(?:대운|금전수|직장운|재물운|학문복|재물복|관록운|애정운)"),
    re.compile(r"(?:될\s*것이로세|의\s*운이\s*있(?:다|도다|겠도다|구먼))"),
    re.compile(r"(?:마의상법|신상전편|달마상법|유장상법)"),
    re.compile(r"(?:태양인|태음인|소양인|소음인|사상체질|사상의학)"),
]

# ─── 샘플 저장 디렉토리 ────────────────────────────────────────────────────────
_SAMPLE_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "step_archive"
    / "llm_output_samples"
)


def _ensure_dir() -> Path:
    """샘플 디렉토리 생성 (첫 호출 시)."""
    _SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    return _SAMPLE_DIR


def _count_fate_vocab(text: str) -> int:
    """운명 매핑 어휘 패턴 매치 수 반환."""
    total = 0
    for pat in _FATE_VOCAB_PATTERNS:
        total += len(pat.findall(text))
    return total


def _increment_fate_counter(hits: int) -> None:
    """fate_counter.json에 누적 카운터 업데이트."""
    try:
        counter_path = _ensure_dir() / "fate_counter.json"
        if counter_path.exists():
            with counter_path.open(encoding="utf-8") as f:
                data: dict = json.load(f)
        else:
            data = {"total_samples": 0, "total_fate_hits": 0, "first_seen": str(date.today())}
        data["total_samples"] = data.get("total_samples", 0) + 1
        data["total_fate_hits"] = data.get("total_fate_hits", 0) + hits
        data["last_seen"] = str(date.today())
        with counter_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass  # silent — 운영 영향 0


def sample_llm_output(
    domain: str,
    text: str,
    sampling_rate: float = 0.01,
    _force: bool = False,
) -> None:
    """LLM 출력 텍스트를 샘플링하여 JSONL에 저장.

    Args:
        domain: 도메인 구분 (예: "face_reading", "palm_reading").
        text: LLM 생성 출력 텍스트.
        sampling_rate: 샘플링 비율 (기본 1%).
        _force: 테스트용 — True이면 sampling_rate 무시하고 항상 저장.
    """
    if not text:
        return  # 빈 텍스트 무시

    try:
        if not _force and random.random() >= sampling_rate:
            return  # 샘플링 제외

        fate_hits = _count_fate_vocab(text)
        entry = {
            "ts": time.time(),
            "date": str(date.today()),
            "domain": domain,
            "text_len": len(text),
            "fate_vocab_hits": fate_hits,
            # 텍스트 앞 120자만 저장 (PII 최소화, 운명 어휘 발생 위치 확인용)
            "text_preview": text[:120],
        }

        today_path = _ensure_dir() / f"{date.today()}.jsonl"
        with today_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        if fate_hits > 0:
            _increment_fate_counter(fate_hits)

    except Exception:
        pass  # silent — 운영 영향 0
