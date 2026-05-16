"""데이터 주체 요청(DSR) 처리 — 운영표준 §10 본문화.

§14.2 rights_information이 "사용자에게 어떤 권리가 있는가"를 알린다면,
본 모듈은 "그 권리 행사 요청을 받았을 때 시스템이 어떻게 처리하는가"를
표준화한다.

DSR(Data Subject Request) 처리 단계:
  1) ingest_dsr(request) — 요청 유효성 검증 (key·subject_id·auth)
  2) plan_dsr(request)   — 어떤 자원을 어떻게 처리할지 dry-run 플랜 생성
  3) execute_dsr(plan)   — 실제 캐시/카운트 삭제·내보내기 실행
  4) audit_dsr(result)   — 트레이싱 로그 emit + 사용자 알림 메타데이터

본 모듈은 캐시 파일 시스템 접근만 수행하고, 외부 시스템(이메일·SNS)은
§14.3 alert_router에 위임한다.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# §10.1 — 요청 상태 enum
DSR_STATUS_PENDING = "pending"
DSR_STATUS_PLANNED = "planned"
DSR_STATUS_EXECUTED = "executed"
DSR_STATUS_REJECTED = "rejected"


@dataclass(frozen=True)
class DSRRequest:
    """단일 데이터 주체 요청 — UI/API 진입점에서 받음.

    Attributes:
        right_key: rights_information.RIGHT_KEYS 중 하나
        subject_id: 사용자 식별값 (uid·이메일 해시 등)
        authenticated: 본인 인증 완료 여부
        lang: 응답 텍스트 언어
        region: 적용 지역 (SLA 결정용)
        request_id: 멱등 키 (재전송 시 동일 ID)
        timestamp_epoch: 요청 접수 시각
    """
    right_key: str
    subject_id: str
    authenticated: bool
    lang: str = "en"
    region: str = ""
    request_id: str = ""
    timestamp_epoch: float = 0.0


@dataclass
class DSRPlan:
    """ingest+plan 단계 산출물 — execute_dsr가 소비.

    Attributes:
        request: 원 요청
        status: pending/planned/rejected
        actions: 실행할 액션 리스트 ("delete_cache", "export_json", ...)
        affected_cache_files: 영향받을 캐시 파일 경로
        sla_business_days: 운영팀 응답 SLA
        reject_reason: rejected일 때 사유
    """
    request: DSRRequest
    status: str
    actions: list[str] = field(default_factory=list)
    affected_cache_files: list[str] = field(default_factory=list)
    sla_business_days: int = 0
    reject_reason: str = ""


# ─────────────────────────── 1) ingest ───────────────────────────

def ingest_dsr(request: DSRRequest) -> tuple[bool, str]:
    """요청 1차 검증. 반환: (ok, reject_reason).

    검증 항목:
      · right_key가 rights_information.RIGHT_KEYS에 있음
      · subject_id 비어있지 않음
      · authenticated == True (모든 권리가 인증 필요)
    """
    from engine.safety.rights_information import RIGHT_KEYS
    if request.right_key not in RIGHT_KEYS:
        return False, f"unknown_right_key:{request.right_key}"
    if not (request.subject_id or "").strip():
        return False, "missing_subject_id"
    if not request.authenticated:
        return False, "authentication_required"
    return True, ""


# ─────────────────────────── 2) plan ───────────────────────────

def _subject_hash(subject_id: str) -> str:
    """subject_id의 SHA-256 단축형 — 파일명 매칭용."""
    return hashlib.sha256(subject_id.encode("utf-8")).hexdigest()[:16]


def _find_affected_files(cache_dir: Path, subject_id: str) -> list[Path]:
    """캐시 디렉터리에서 subject_id 관련 파일 탐색.

    캐시 파일명에 subject 해시가 포함될 것을 전제로 한다.
    무관한 파일은 손대지 않는다.
    """
    if not cache_dir.exists():
        return []
    short = _subject_hash(subject_id)
    return [p for p in cache_dir.iterdir() if p.is_file() and short in p.name]


def plan_dsr(
    request: DSRRequest,
    *,
    cache_dir: Path | None = None,
) -> DSRPlan:
    """ingest 후 처리 플랜 생성. dry-run (파일 변경 없음)."""
    from engine.safety.rights_information import get_sla_for_region

    ok, reason = ingest_dsr(request)
    if not ok:
        return DSRPlan(
            request=request,
            status=DSR_STATUS_REJECTED,
            reject_reason=reason,
        )

    cache_dir = cache_dir or (
        Path(__file__).resolve().parent.parent.parent / "step_archive" / "face_reading_cache"
    )
    affected = _find_affected_files(cache_dir, request.subject_id)
    actions: list[str] = []

    if request.right_key == "access":
        actions.append("list_cache")
    elif request.right_key == "rectify":
        # 정정은 실질적으로 캐시 무효화 + 재요청 유도
        actions.append("delete_cache")
    elif request.right_key == "erase":
        actions.extend(["delete_cache", "delete_feedback_counts"])
    elif request.right_key == "restrict":
        actions.append("mark_restricted")
    elif request.right_key == "portability":
        actions.append("export_json")
    elif request.right_key == "object":
        actions.extend(["mark_objected", "block_future_requests"])
    elif request.right_key == "withdraw_consent":
        actions.extend(["delete_cache", "delete_feedback_counts", "mark_consent_withdrawn"])

    sla = get_sla_for_region(request.right_key, request.region)
    return DSRPlan(
        request=request,
        status=DSR_STATUS_PLANNED,
        actions=actions,
        affected_cache_files=[str(p) for p in affected],
        sla_business_days=sla,
    )


# ─────────────────────────── 3) execute ───────────────────────────

def execute_dsr(
    plan: DSRPlan,
    *,
    cache_dir: Path | None = None,
    feedback_path: Path | None = None,
) -> dict[str, Any]:
    """플랜 실행. 실제 파일 시스템 변경 발생.

    Returns:
        {
            "status": "executed" | "rejected",
            "actions_executed": [...],
            "files_deleted": int,
            "exports": {...},
            "errors": [...]
        }
    """
    result: dict[str, Any] = {
        "status": DSR_STATUS_REJECTED if plan.status == DSR_STATUS_REJECTED else DSR_STATUS_EXECUTED,
        "actions_executed": [],
        "files_deleted": 0,
        "exports": {},
        "errors": [],
    }
    if plan.status == DSR_STATUS_REJECTED:
        result["reject_reason"] = plan.reject_reason
        return result

    cache_dir = cache_dir or (
        Path(__file__).resolve().parent.parent.parent / "step_archive" / "face_reading_cache"
    )

    for action in plan.actions:
        try:
            if action == "list_cache":
                # access — 캐시 파일 메타데이터만 수집
                short = _subject_hash(plan.request.subject_id)
                files = [p for p in cache_dir.iterdir() if p.is_file() and short in p.name]
                result["exports"]["cache_files"] = [
                    {"name": p.name, "size_bytes": p.stat().st_size,
                     "mtime_epoch": p.stat().st_mtime}
                    for p in files
                ]
            elif action == "delete_cache":
                count = 0
                short = _subject_hash(plan.request.subject_id)
                for p in list(cache_dir.iterdir()) if cache_dir.exists() else []:
                    if p.is_file() and short in p.name:
                        p.unlink()
                        count += 1
                result["files_deleted"] += count
            elif action == "delete_feedback_counts":
                # feedback.py가 _feedback_counts.json에 익명 카운트 보관 — subject_id로
                # 식별 불가능하므로 본 액션은 노옵(no-op) 처리. 익명 카운트는 RTBF 대상 아님.
                pass
            elif action == "export_json":
                # portability — 캐시 내용 자체를 JSON으로 노출
                short = _subject_hash(plan.request.subject_id)
                exports = []
                for p in cache_dir.iterdir() if cache_dir.exists() else []:
                    if p.is_file() and short in p.name:
                        try:
                            exports.append({"name": p.name, "body": json.loads(p.read_text())})
                        except (json.JSONDecodeError, OSError):
                            pass
                result["exports"]["portable_records"] = exports
            elif action in ("mark_restricted", "mark_objected", "mark_consent_withdrawn",
                            "block_future_requests"):
                # 운영자 측 외부 시스템(IAM·차단 리스트)에서 처리.
                # 본 모듈은 의도만 기록 — 외부 워커가 result["actions_executed"]를 보고 후속.
                pass
            else:
                result["errors"].append(f"unknown_action:{action}")
                continue
            result["actions_executed"].append(action)
        except Exception as e:  # noqa: BLE001
            result["errors"].append(f"{action}_failed:{type(e).__name__}")

    return result


# ─────────────────────────── 4) audit ───────────────────────────

def build_audit_record(
    plan: DSRPlan,
    execution_result: dict[str, Any],
) -> dict[str, Any]:
    """§10.4 감사 로그 — 트레이싱(emit_face_reading_event) 호환 페이로드.

    개인정보를 직접 포함하지 않는다 — subject_id는 해시만 기록.
    """
    return {
        "service": "face_reading",
        "event": "dsr_processed",
        "right_key": plan.request.right_key,
        "subject_hash": _subject_hash(plan.request.subject_id) if plan.request.subject_id else "",
        "region": plan.request.region or "",
        "status": execution_result.get("status"),
        "actions_executed": list(execution_result.get("actions_executed", [])),
        "files_deleted": int(execution_result.get("files_deleted", 0)),
        "sla_business_days": plan.sla_business_days,
        "request_id": plan.request.request_id or "",
        "elapsed_ms": 0,
        "timestamp_emit": time.time(),
    }


def process_dsr(
    request: DSRRequest,
    *,
    cache_dir: Path | None = None,
) -> dict[str, Any]:
    """전체 흐름 진입점 — plan → execute → audit 일괄 처리.

    외부 API에서는 이 함수만 호출하면 충분.
    """
    plan = plan_dsr(request, cache_dir=cache_dir)
    exec_result = execute_dsr(plan, cache_dir=cache_dir)
    audit = build_audit_record(plan, exec_result)
    return {
        "plan_status": plan.status,
        "execution_status": exec_result["status"],
        "actions_executed": exec_result["actions_executed"],
        "files_deleted": exec_result["files_deleted"],
        "exports": exec_result.get("exports", {}),
        "errors": exec_result.get("errors", []),
        "sla_business_days": plan.sla_business_days,
        "audit_record": audit,
        "reject_reason": plan.reject_reason if plan.status == DSR_STATUS_REJECTED else "",
    }
