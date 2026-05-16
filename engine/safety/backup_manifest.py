"""백업·복구 매니페스트 — 운영표준 §7.3.8 본문화.

운영 데이터(피드백 카운트·SLO 로그·모델 카드·이벤트 트레이스 등)에 대한
백업 정책·복구 절차를 표준화한다. 외부 백업 워커(rsync/restic/S3-sync)가
본 매니페스트를 소비해 어떤 자원을 어떤 RPO/RTO로 보관할지 결정.

§7.3.8 자원 유형:
  · feedback_counts — 익명 피드백 (RPO: 1h, RTO: 4h)
  · slo_logs        — JSON line 트레이스 (RPO: 5m, RTO: 1h)
  · model_card      — 정적 메타 (RPO: 24h, RTO: 24h)
  · cache           — 24h TTL — 백업 대상 아님 (BACKUP_KIND_VOLATILE)
  · governance_audit — DSR 감사 로그 (RPO: 5m, RTO: 1h, 규제 의무)

본 모듈은 실제 백업 실행은 외부 워커에 위임. 다음만 책임:
  1) 백업 대상 자원 목록과 RPO/RTO 매트릭스
  2) 복구 우선순위 (P0 > P1 > P2)
  3) 백업 무결성 검증 결과 직렬화
  4) §14.3 alert_router 호환 알람 페이로드 (백업 실패 시 P1)
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# §7.3.8 — 자원 분류
BACKUP_KIND_PERSISTENT = "persistent"   # 백업 대상
BACKUP_KIND_VOLATILE = "volatile"       # TTL 캐시 등 — 백업 X
BACKUP_KIND_AUDIT = "audit"             # 규제 의무 — 장기 보관

# §7.3.8 — 복구 우선순위
RECOVERY_PRIORITY_P0 = "P0"  # 즉시 복구 (서비스 동작 필수)
RECOVERY_PRIORITY_P1 = "P1"  # 4시간 내 (운영 측정 필수)
RECOVERY_PRIORITY_P2 = "P2"  # 24시간 내 (분석·감사용)


@dataclass(frozen=True)
class BackupResource:
    """단일 백업 대상 자원 정의.

    Attributes:
        resource_id: "feedback_counts" 등 식별자
        source_path: 백업 원본 (절대/상대 경로)
        kind: BACKUP_KIND_*
        priority: RECOVERY_PRIORITY_*
        rpo_sec: Recovery Point Objective (얼마나 자주 백업할지)
        rto_sec: Recovery Time Objective (사고 후 복구까지 허용 시간)
        encrypt_at_rest: 백업 저장 시 암호화 필요
        retention_days: 백업 보관기간 (장기 감사용은 길게)
    """
    resource_id: str
    source_path: str
    kind: str
    priority: str
    rpo_sec: int
    rto_sec: int
    encrypt_at_rest: bool
    retention_days: int


@dataclass(frozen=True)
class BackupRecord:
    """단일 백업 실행 결과 — 외부 워커가 채워 보냄."""
    resource_id: str
    started_at_epoch: float
    finished_at_epoch: float
    bytes_copied: int
    sha256: str
    ok: bool
    error: str = ""


# ─────────────────────────── face_reading 자원 매니페스트 ───────────────────────────

def get_face_reading_manifest() -> tuple[BackupResource, ...]:
    """§7.3.8 face_reading 시스템의 표준 백업 매니페스트."""
    return (
        BackupResource(
            resource_id="feedback_counts",
            source_path="step_archive/_feedback_counts.json",
            kind=BACKUP_KIND_PERSISTENT,
            priority=RECOVERY_PRIORITY_P1,
            rpo_sec=3600,
            rto_sec=14400,
            encrypt_at_rest=True,
            retention_days=365,
        ),
        BackupResource(
            resource_id="slo_logs",
            source_path="step_archive/slo_logs/",
            kind=BACKUP_KIND_PERSISTENT,
            priority=RECOVERY_PRIORITY_P1,
            rpo_sec=300,
            rto_sec=3600,
            encrypt_at_rest=True,
            retention_days=90,
        ),
        BackupResource(
            resource_id="model_card",
            source_path="step_archive/model_card.json",
            kind=BACKUP_KIND_PERSISTENT,
            priority=RECOVERY_PRIORITY_P2,
            rpo_sec=86400,
            rto_sec=86400,
            encrypt_at_rest=False,
            retention_days=730,
        ),
        BackupResource(
            resource_id="governance_audit",
            source_path="step_archive/governance_audit/",
            kind=BACKUP_KIND_AUDIT,
            priority=RECOVERY_PRIORITY_P0,
            rpo_sec=300,
            rto_sec=3600,
            encrypt_at_rest=True,
            retention_days=2555,  # 7년 (KR 개인정보보호법 §21·EU AI Act §12)
        ),
        BackupResource(
            resource_id="cache",
            source_path="step_archive/face_reading_cache/",
            kind=BACKUP_KIND_VOLATILE,
            priority=RECOVERY_PRIORITY_P2,
            rpo_sec=0,
            rto_sec=0,
            encrypt_at_rest=False,
            retention_days=0,
        ),
    )


# ─────────────────────────── 매니페스트 조회 ───────────────────────────

def list_backup_targets(
    manifest: tuple[BackupResource, ...] | None = None,
) -> list[BackupResource]:
    """실제 백업 대상만 — VOLATILE 제외."""
    manifest = manifest or get_face_reading_manifest()
    return [r for r in manifest if r.kind != BACKUP_KIND_VOLATILE]


def get_resource_by_id(
    resource_id: str,
    *,
    manifest: tuple[BackupResource, ...] | None = None,
) -> BackupResource | None:
    manifest = manifest or get_face_reading_manifest()
    for r in manifest:
        if r.resource_id == resource_id:
            return r
    return None


def list_by_priority(
    priority: str,
    *,
    manifest: tuple[BackupResource, ...] | None = None,
) -> list[BackupResource]:
    manifest = manifest or get_face_reading_manifest()
    return [r for r in manifest if r.priority == priority]


# ─────────────────────────── RPO/RTO 검증 ───────────────────────────

def is_within_rpo(
    resource: BackupResource,
    *,
    last_backup_epoch: float,
    now: float | None = None,
) -> bool:
    """마지막 백업이 RPO 안에 있는지 — False면 새 백업 즉시 필요."""
    now = now if now is not None else time.time()
    return (now - last_backup_epoch) <= resource.rpo_sec


def overdue_backups(
    last_backups: dict[str, float],
    *,
    manifest: tuple[BackupResource, ...] | None = None,
    now: float | None = None,
) -> list[BackupResource]:
    """RPO를 넘긴 자원 목록. last_backups에 키가 없으면 즉시 overdue."""
    now = now if now is not None else time.time()
    manifest = manifest or get_face_reading_manifest()
    overdue: list[BackupResource] = []
    for r in manifest:
        if r.kind == BACKUP_KIND_VOLATILE:
            continue
        last = last_backups.get(r.resource_id)
        if last is None or not is_within_rpo(r, last_backup_epoch=last, now=now):
            overdue.append(r)
    return overdue


# ─────────────────────────── 무결성 ───────────────────────────

def compute_sha256(file_path: Path) -> str:
    """파일의 SHA-256 — 백업 무결성 검증용."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_backup_record(
    record: BackupRecord,
    resource: BackupResource,
) -> list[str]:
    """단일 백업 기록 검증. 위반 없으면 빈 리스트."""
    violations: list[str] = []
    if not record.ok:
        violations.append(f"not_ok:{record.error}")
    if record.bytes_copied <= 0 and resource.kind != BACKUP_KIND_VOLATILE:
        violations.append("zero_bytes_copied")
    if not record.sha256 or len(record.sha256) != 64:
        violations.append("invalid_sha256")
    duration = record.finished_at_epoch - record.started_at_epoch
    if duration > resource.rto_sec:
        violations.append(f"duration_exceeds_rto:{duration}>{resource.rto_sec}")
    if record.resource_id != resource.resource_id:
        violations.append(f"resource_id_mismatch:{record.resource_id}!={resource.resource_id}")
    return violations


# ─────────────────────────── 알람 ───────────────────────────

def to_alert_payload(
    overdue: list[BackupResource],
    *,
    now: float | None = None,
) -> dict[str, Any]:
    """§14.3 alert_router 호환 페이로드.

    P0 자원이 overdue면 즉시 알람, P1/P2는 누적 카운트 기준.
    """
    now = now if now is not None else time.time()
    p0_overdue = [r for r in overdue if r.priority == RECOVERY_PRIORITY_P0]
    p1_overdue = [r for r in overdue if r.priority == RECOVERY_PRIORITY_P1]
    p2_overdue = [r for r in overdue if r.priority == RECOVERY_PRIORITY_P2]
    severity = "P0" if p0_overdue else ("P1" if p1_overdue else "P2")
    return {
        "service": "backup_manifest",
        "timestamp_epoch": now,
        "severity": severity,
        "p0_overdue_ids": [r.resource_id for r in p0_overdue],
        "p1_overdue_ids": [r.resource_id for r in p1_overdue],
        "p2_overdue_ids": [r.resource_id for r in p2_overdue],
        "total_overdue": len(overdue),
        "should_page_oncall": bool(p0_overdue),
    }
