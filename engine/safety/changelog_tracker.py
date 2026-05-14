"""운영표준 변경 이력 추적 — §14.12 본문화.

안전 모듈 매니페스트의 변경(신규 항목 / 임계 조정 / deprecation / 규제 추가)을
시간순으로 기록해 감사 추적 가능하게 만든다. compliance_report가 현재 상태
스냅샷이라면, 본 모듈은 시간에 따른 진화 기록.

§14.12 변경 유형:
  · ADDED        — 신규 모듈/항목 추가
  · MODIFIED     — 임계값/심볼/규제 매핑 조정
  · DEPRECATED   — 사용 자제 (당장 제거 X)
  · REMOVED      — 매니페스트에서 제거
  · REGULATION_ADDED — 새 규제 앵커 추가 (GDPR Art.X 등)

§14.12 변경 사유:
  · INCIDENT     — 사고 사후 검토 결과
  · REGULATION   — 새 규제 출시 (예: EU AI Act 발효)
  · IMPROVEMENT  — 정기 회고에서 도출
  · DEPRECATION  — 더 나은 모듈로 대체

본 모듈은 in-memory 기록 (외부 영구 저장은 별도 워커가 JSONL append).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# §14.12 변경 유형
CHANGE_ADDED = "added"
CHANGE_MODIFIED = "modified"
CHANGE_DEPRECATED = "deprecated"
CHANGE_REMOVED = "removed"
CHANGE_REGULATION_ADDED = "regulation_added"

# §14.12 변경 사유
REASON_INCIDENT = "incident"
REASON_REGULATION = "regulation"
REASON_IMPROVEMENT = "improvement"
REASON_DEPRECATION = "deprecation"


@dataclass(frozen=True)
class ChangelogEntry:
    timestamp_iso: str
    change_type: str             # CHANGE_*
    standard_ref: str            # "§7.2.18" 등
    module: str                  # engine.safety.xxx
    summary: str                 # 한 줄 요약
    reason: str                  # REASON_*
    detail: str = ""             # 자유 메모
    related_incident: str = ""   # incident_id (REASON_INCIDENT일 때)
    related_pr: str = ""         # PR 번호·URL
    breaking: bool = False       # 호환성 깨짐 여부
    metadata: dict[str, Any] = field(default_factory=dict)


# ─────────────────────────── ChangelogStore ───────────────────────────

class ChangelogStore:
    """in-memory 변경 이력 저장소. thread-safe.

    영구 저장은 외부 워커가 to_jsonl_lines로 export 받아 JSONL append.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entries: list[ChangelogEntry] = []

    def record(self, entry: ChangelogEntry) -> None:
        with self._lock:
            self._entries.append(entry)

    def record_change(
        self,
        *,
        change_type: str,
        standard_ref: str,
        module: str,
        summary: str,
        reason: str,
        detail: str = "",
        related_incident: str = "",
        related_pr: str = "",
        breaking: bool = False,
        metadata: dict[str, Any] | None = None,
        now_iso: str | None = None,
    ) -> ChangelogEntry:
        """변경 1건 기록 — 호출자 편의 진입점."""
        ts = now_iso or datetime.now(timezone.utc).isoformat()
        entry = ChangelogEntry(
            timestamp_iso=ts,
            change_type=change_type,
            standard_ref=standard_ref,
            module=module,
            summary=summary,
            reason=reason,
            detail=detail,
            related_incident=related_incident,
            related_pr=related_pr,
            breaking=breaking,
            metadata=metadata or {},
        )
        self.record(entry)
        return entry

    def all(self) -> list[ChangelogEntry]:
        with self._lock:
            return list(self._entries)

    def by_change_type(self, change_type: str) -> list[ChangelogEntry]:
        with self._lock:
            return [e for e in self._entries if e.change_type == change_type]

    def by_module(self, module: str) -> list[ChangelogEntry]:
        with self._lock:
            return [e for e in self._entries if e.module == module]

    def by_reason(self, reason: str) -> list[ChangelogEntry]:
        with self._lock:
            return [e for e in self._entries if e.reason == reason]

    def by_incident(self, incident_id: str) -> list[ChangelogEntry]:
        with self._lock:
            return [e for e in self._entries
                    if e.related_incident == incident_id]

    def breaking_changes(self) -> list[ChangelogEntry]:
        with self._lock:
            return [e for e in self._entries if e.breaking]

    def since(self, iso_ts: str) -> list[ChangelogEntry]:
        """주어진 ISO timestamp 이후 항목."""
        with self._lock:
            return [e for e in self._entries
                    if e.timestamp_iso >= iso_ts]

    def reset(self) -> None:
        """테스트용 일괄 제거."""
        with self._lock:
            self._entries.clear()

    def size(self) -> int:
        with self._lock:
            return len(self._entries)


# ─────────────────────────── 직렬화 ───────────────────────────

def entry_to_dict(entry: ChangelogEntry) -> dict[str, Any]:
    return {
        "timestamp_iso": entry.timestamp_iso,
        "change_type": entry.change_type,
        "standard_ref": entry.standard_ref,
        "module": entry.module,
        "summary": entry.summary,
        "reason": entry.reason,
        "detail": entry.detail,
        "related_incident": entry.related_incident,
        "related_pr": entry.related_pr,
        "breaking": entry.breaking,
        "metadata": dict(entry.metadata),
    }


def to_jsonl_lines(entries: list[ChangelogEntry]) -> list[str]:
    """JSONL append용 라인 리스트 (각 라인 = 단일 entry JSON)."""
    import json
    return [
        json.dumps(entry_to_dict(e), ensure_ascii=False, sort_keys=True)
        for e in entries
    ]


def format_changelog_text(
    entries: list[ChangelogEntry],
    *,
    limit: int = 50,
) -> str:
    """터미널 표시용 — 최신 N건."""
    lines: list[str] = []
    lines.append(f"# Changelog ({len(entries)} entries, showing latest {limit})")
    # timestamp 역순 (최신 먼저)
    for e in sorted(entries, key=lambda x: x.timestamp_iso, reverse=True)[:limit]:
        flag = " [BREAKING]" if e.breaking else ""
        lines.append(f"- `{e.timestamp_iso}` [{e.change_type}]{flag} "
                     f"`{e.module}` ({e.standard_ref}): {e.summary}")
        if e.reason:
            lines.append(f"  · reason: {e.reason}")
        if e.related_incident:
            lines.append(f"  · incident: {e.related_incident}")
    return "\n".join(lines)


# ─────────────────────────── 모듈 수준 인스턴스 ───────────────────────────

# 운영 코드에서 직접 record_change(...) 호출하기 편하도록 글로벌 인스턴스 제공.
# 다중 프로세스 환경은 별도 Redis/DB 어댑터 필요.
DEFAULT_STORE = ChangelogStore()


def record_change(
    *,
    change_type: str,
    standard_ref: str,
    module: str,
    summary: str,
    reason: str,
    **kwargs: Any,
) -> ChangelogEntry:
    """글로벌 store에 기록 — 운영 코드용 편의 함수."""
    return DEFAULT_STORE.record_change(
        change_type=change_type,
        standard_ref=standard_ref,
        module=module,
        summary=summary,
        reason=reason,
        **kwargs,
    )


def get_default_store() -> ChangelogStore:
    return DEFAULT_STORE
