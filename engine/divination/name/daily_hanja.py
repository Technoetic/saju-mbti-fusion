"""ADR-135 — 오늘의 한자 결정론 산출 (today-hanja 카드).

본 모듈은 ADR-002·006·010 정합:
  · 날짜 기반 결정론 시드 — 동일 날짜 → 동일 한자
  · 9,932자 풀 중 자원오행 KCI 매핑된 한자 우선 (ADR-027·125)
  · 일반 사용자에게 단정 X — "추천 활용"만 안내

학파 출처 (ADR-026·125):
  · 대법원 인명용 한자 9,932자 풀
  · 이재승·김만태 KCI 자원오행 매핑

결정론 보장:
  · 시드 = year * 10000 + month * 100 + day (8자리 정수)
  · O(1) 룩업 — 사전 빌드 풀에서 인덱스 산출
  · LLM 무관 — 라이브 BizRouter 비용 0
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date as _date
from functools import lru_cache
from typing import Optional

from engine.divination.name.unihan import (
    _load_db,
    hangul_of,
    kangxi_strokes,
    kci_reason,
    kci_school_source,
    radical_of,
    resource_ohaeng_kci,
)


@dataclass(frozen=True)
class DailyHanjaResult:
    """오늘의 한자 결정론 산출 결과.

    Attributes:
        date_iso: 날짜 ISO 형식 'YYYY-MM-DD'
        char: 한자 1자
        hangul: 한국어 음
        kangxi_strokes: 강희자전 획수
        radical: 부수 번호 (1~214) 또는 None
        resource_ohaeng: 자원오행 (목·화·토·금·수) 또는 None
        kci_reason: KCI 학파 본의 추적 사유 또는 빈 문자열
        kci_school_source: KCI 학파 출처 또는 빈 문자열
        seed_int: 결정론 시드 정수
        disclaimer: 면책 의무
    """
    date_iso: str
    char: str
    hangul: str
    kangxi_strokes: int
    radical: Optional[int]
    resource_ohaeng: Optional[str]
    kci_reason: str
    kci_school_source: str
    seed_int: int
    disclaimer: str


@lru_cache(maxsize=1)
def _kci_pool() -> tuple[str, ...]:
    """KCI 매핑된 한자 풀 — ADR-027·125 정합.

    Returns:
        KCI 자원오행 매핑이 있는 한자 튜플 (정렬됨).
        본 시스템 영속화 시점에 103자 (ADR-027 94자 + ADR-125 9자).
    """
    db = _load_db()
    pool = []
    for char, entry in db.items():
        if entry.get("resource_ohaeng_kci"):
            pool.append(char)
    return tuple(sorted(pool))


@lru_cache(maxsize=1)
def _full_pool() -> tuple[str, ...]:
    """전체 인명용 한자 풀 (한국어 음 + 부수가 있는 한자만).

    Returns:
        9,932자 중 hangul + radical 둘 다 본문화된 한자 (안전 폴백).
    """
    db = _load_db()
    pool = []
    for char, entry in db.items():
        if entry.get("hangul") and entry.get("radical"):
            pool.append(char)
    return tuple(sorted(pool))


def _seed_from_date(d: _date) -> int:
    """날짜 → 결정론 시드 정수.

    YYYYMMDD 형식 8자리 정수. 동일 날짜 → 동일 시드.
    """
    return d.year * 10000 + d.month * 100 + d.day


def _index_from_seed(seed_int: int, pool_size: int) -> int:
    """결정론 시드 → 풀 인덱스 (0~pool_size-1).

    SHA-256 해시 → 정수 모듈로 (UUID 회피·결정론 보장).
    """
    h = hashlib.sha256(str(seed_int).encode("utf-8")).hexdigest()
    return int(h, 16) % pool_size


def get_daily_hanja(target_date: Optional[_date] = None) -> Optional[DailyHanjaResult]:
    """오늘의 한자 결정론 산출.

    Args:
        target_date: 대상 날짜. None이면 오늘 (date.today()).

    Returns:
        DailyHanjaResult 또는 None (풀 부재 시).

    학파 우선순위:
      1. KCI 매핑 한자 풀 (자원오행·학파 출처 명시) — 우선
      2. 전체 9,932자 풀 (자원오행 부재) — 폴백

    결정론 보장:
      - 동일 날짜 입력 → 동일 한자 (시드 = YYYYMMDD)
      - LRU 캐시 — 1회 풀 빌드 후 O(1) 룩업
    """
    if target_date is None:
        target_date = _date.today()

    seed_int = _seed_from_date(target_date)

    # 1차: KCI 매핑 한자 풀 (학파 출처 명시)
    kci_pool = _kci_pool()
    if kci_pool:
        idx = _index_from_seed(seed_int, len(kci_pool))
        char = kci_pool[idx]
    else:
        # 폴백: 전체 한자 풀
        full_pool = _full_pool()
        if not full_pool:
            return None
        idx = _index_from_seed(seed_int, len(full_pool))
        char = full_pool[idx]

    return DailyHanjaResult(
        date_iso=target_date.isoformat(),
        char=char,
        hangul=hangul_of(char) or "",
        kangxi_strokes=kangxi_strokes(char) or 0,
        radical=radical_of(char),
        resource_ohaeng=resource_ohaeng_kci(char),
        kci_reason=kci_reason(char) or "",
        kci_school_source=kci_school_source(char) or "",
        seed_int=seed_int,
        disclaimer=(
            "참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다."
        ),
    )


__all__ = ["DailyHanjaResult", "get_daily_hanja"]
