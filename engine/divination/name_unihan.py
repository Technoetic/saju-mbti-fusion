"""Unihan 기반 한자 자동 매핑 — 보고서 §4 9,389자 풀 확장 본문화.

data/korean_hanja_unihan.json에서 8,525자 (한국어 음을 가진 한자) 로드:
  · char: 한자
  · hangul: 한국어 음 (대표 1자)
  · kangxi_strokes: 강희자전 원획수
  · radical: 부수 번호 (1~214)
  · resource_ohaeng: 자원오행 (자동 매핑 41%, 나머지 빈 문자열)

지연 로딩 — 처음 호출 시에만 JSON 파싱. 메모리 ~5MB.

호환성:
  · name_strokes (수동 250자) — 우선순위
  · name_unihan (자동 8525자) — fallback

운영표준:
  · 결정론 (재현성)
  · LLM 무관
  · JSON 손실·미수록 시 None 반환 (예외 X)
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


# 데이터 경로 — engine/ 기준 부모 디렉토리의 data/
_DATA_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "korean_hanja_unihan.json"
)


@lru_cache(maxsize=1)
def _load_db() -> dict[str, dict[str, Any]]:
    """JSON 로드. 파일 없으면 빈 dict.

    Returns:
        {"星": {"hangul": "성", "kangxi_strokes": 9, "radical": 72,
                 "resource_ohaeng": "화"}, ...}
    """
    if not _DATA_PATH.exists():
        return {}
    try:
        raw = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return {}
        return {entry["char"]: entry for entry in raw if "char" in entry}
    except Exception:
        return {}


@lru_cache(maxsize=1)
def _build_hangul_index() -> dict[str, list[str]]:
    """{"성": ["星","城","誠",...], ...} 역인덱스. 한 번만 계산."""
    db = _load_db()
    out: dict[str, list[str]] = {}
    for char, entry in db.items():
        hangul = entry.get("hangul", "")
        if not hangul:
            continue
        out.setdefault(hangul, []).append(char)
    return out


# ─────────────────────────── Public API ───────────────────────────

def kangxi_strokes(char: str) -> int | None:
    """단일 한자의 강희자전 원획수. 미수록 시 None."""
    if not isinstance(char, str) or not char:
        return None
    entry = _load_db().get(char)
    if entry is None:
        return None
    val = entry.get("kangxi_strokes")
    return int(val) if isinstance(val, (int, float)) else None


def hangul_of(char: str) -> str | None:
    """단일 한자의 한국어 음 (대표 1자). 미수록 시 None."""
    if not isinstance(char, str) or not char:
        return None
    entry = _load_db().get(char)
    return entry.get("hangul") if entry else None


def radical_of(char: str) -> int | None:
    """단일 한자의 부수 번호 (1~214). 미수록 시 None."""
    if not isinstance(char, str) or not char:
        return None
    entry = _load_db().get(char)
    val = entry.get("radical") if entry else None
    return int(val) if isinstance(val, (int, float)) and val > 0 else None


def resource_ohaeng(char: str) -> str | None:
    """단일 한자의 자원오행. 미수록·미정 시 None."""
    if not isinstance(char, str) or not char:
        return None
    entry = _load_db().get(char)
    if entry is None:
        return None
    val = entry.get("resource_ohaeng", "")
    return val if val else None


def get_candidates_by_hangul(syllable: str) -> list[str]:
    """단일 한글 음 → 해당 음을 가진 한자 후보 리스트.

    Unihan에서 추출된 모든 한자 — 대법원 인명용 풀 자체는 별도 검증 필요.
    """
    if not syllable:
        return []
    return list(_build_hangul_index().get(syllable, []))


def total_chars() -> int:
    return len(_load_db())


def total_with_ohaeng() -> int:
    """자원오행이 매핑된 한자 수 (부수 기반)."""
    return sum(1 for e in _load_db().values() if e.get("resource_ohaeng"))


def is_loaded() -> bool:
    return bool(_load_db())
