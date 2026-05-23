"""ADR-207 - 사용자 분석 이력 타임라인 메타데이터.

같은 사용자의 다회 분석을 시계열 dict로 보관. 사용자 재방문 시 "변화 추적"
가능. 익명 식별자 기반 (개인정보 X — PII 차단).

ADR 정합:
  - ADR-006 자문 거절 (이력은 형태 변화 추적만 — 운명 매핑 X)
  - ADR-010 사실성 분리 (각 entry의 출처·시각 명시)
  - ADR-007 PII 보호 (사용자 식별자는 hash 익명)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TimelineEntry:
    """단일 분석 이력 entry."""
    timestamp_iso: str
    domain: str         # 'face' | 'palm' | 'name' | 'dream' | 'hwapae'
    top_label: str      # 가장 두드러진 라벨 (운명 단정 X)
    palace_score_summary: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class TimelineReport:
    """사용자 익명 타임라인 보고."""
    anon_id: str        # SHA-256 24자 truncate
    entries: tuple[TimelineEntry, ...]
    entry_count: int
    domains_used: tuple[str, ...]
    most_recent_iso: str
    description_ko: str


def anonymize_user_id(raw_user_id: str) -> str:
    """사용자 식별자 → SHA-256 24자 익명 ID."""
    if not raw_user_id:
        return ""
    h = hashlib.sha256(raw_user_id.encode("utf-8")).hexdigest()
    return h[:24]


def build_timeline(
    raw_user_id: str,
    entries: list[dict[str, Any]],
) -> TimelineReport:
    """사용자 ID + entries → 익명 타임라인 보고.

    Args:
        raw_user_id: 사용자 원본 식별자 (이메일·UUID 등). 즉시 hash.
        entries: 각 dict {timestamp_iso, domain, top_label, palace_score_summary}.

    Returns:
        TimelineReport — anon_id + 시계열 entries.
    """
    anon = anonymize_user_id(raw_user_id)

    valid_entries: list[TimelineEntry] = []
    domains_seen: set[str] = set()
    for e in entries:
        if not isinstance(e, dict):
            continue
        ts = e.get("timestamp_iso")
        domain = e.get("domain")
        top_label = e.get("top_label") or ""
        scores = e.get("palace_score_summary") or {}
        if not isinstance(ts, str) or not isinstance(domain, str):
            continue
        valid_entries.append(TimelineEntry(
            timestamp_iso=ts,
            domain=domain,
            top_label=str(top_label),
            palace_score_summary={
                k: float(v) for k, v in scores.items()
                if isinstance(v, (int, float))
            },
        ))
        domains_seen.add(domain)

    # 시간 역순 정렬 (최신 우선)
    valid_entries.sort(key=lambda x: x.timestamp_iso, reverse=True)

    most_recent = valid_entries[0].timestamp_iso if valid_entries else ""
    n = len(valid_entries)

    if n == 0:
        desc = "아직 분석 이력이 없습니다."
    elif n == 1:
        desc = f"첫 분석 ({most_recent}). 다음 분석 시 변화를 추적할 수 있습니다."
    else:
        desc = (
            f"{n}회 분석 이력 ({', '.join(sorted(domains_seen))} 도메인). "
            f"최신 분석 {most_recent}. 시간에 따른 형태 변화를 추적할 수 있습니다 — "
            f"운명 변화가 아닌 측정 변동성입니다."
        )

    return TimelineReport(
        anon_id=anon,
        entries=tuple(valid_entries),
        entry_count=n,
        domains_used=tuple(sorted(domains_seen)),
        most_recent_iso=most_recent,
        description_ko=desc,
    )


def compute_score_drift(
    entries: list[TimelineEntry],
    palace_key: str,
) -> float | None:
    """특정 12궁의 점수 변동성 (표준편차) — 측정 변동 표시.

    Args:
        entries: TimelineEntry 리스트 (2건 이상이어야 의미 있음).
        palace_key: 12궁 키 (jaebaek, gwanrok 등).

    Returns:
        표준편차 (float) — 2건 미만이면 None.
    """
    scores = [
        e.palace_score_summary.get(palace_key)
        for e in entries
        if palace_key in e.palace_score_summary
    ]
    scores = [s for s in scores if isinstance(s, (int, float))]
    if len(scores) < 2:
        return None
    mean = sum(scores) / len(scores)
    var = sum((s - mean) ** 2 for s in scores) / len(scores)
    return round(var ** 0.5, 4)
