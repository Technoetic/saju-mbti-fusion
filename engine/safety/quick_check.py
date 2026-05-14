"""빠른 점검 진입점 — 운영표준 §7.3.5 본문화.

운영자가 한 함수로 시스템 상태를 점검할 수 있는 단일 진입점.
외부 모니터링(Datadog/Grafana)이 정전된 상황에서도 SSH 접속만으로
즉시 핵심 지표를 확인할 수 있게 한다.

진단 묶음:
  · SLO 윈도우 — 최근 N분의 crisis/err/cache_hit/p95/p99
  · 안전 모듈 가용성 — crisis_detector, legal_notice, pii, regulation 임포트
  · 캐시 디렉터리 — 존재·크기·최신 파일 timestamp
  · 골든 셋 거버넌스 — 가상 케이스 통과율 (실제 셋은 외부 주입)
  · 알람 라우터 정합성 — P0/P1 분류가 예상대로 동작

결과는 dict로 반환하고 status는 "OK" / "WARN" / "CRITICAL" 3단계.
"""

from __future__ import annotations

import importlib
import time
from pathlib import Path
from typing import Any


def _check_safety_imports() -> dict[str, Any]:
    """안전 모듈 임포트 가능 여부 — 배포 직후 가장 빠른 헬스체크."""
    required = [
        "engine.safety.crisis_detector",
        "engine.safety.legal_notice",
        "engine.safety.pii",
        "engine.safety.regulation",
        "engine.safety.crisis_resources",
        "engine.safety.language",
        "engine.safety.tracing",
        "engine.safety.slo",
        "engine.safety.photo_guide",
        "engine.safety.data_governance",
        "engine.safety.consent_screen",
        "engine.safety.alert_router",
        "engine.safety.emotion_disclosure",
        "engine.safety.rollback_trigger",
        "engine.safety.rights_information",
        "engine.safety.dsr_processor",
        "engine.safety.model_card",
        "engine.safety.jailbreak_defense",
        "engine.safety.canary_guard",
        "engine.safety.persona_self_eval",
        "engine.safety.llm_fallback_router",
        "engine.safety.cache_janitor",
        "engine.safety.backup_manifest",
        "engine.safety.shadow_eval",
        "engine.safety.response_envelope",
        "engine.safety.output_token_guard",
        "engine.safety.idempotency_key",
        "engine.safety.response_fact_check",
        "engine.safety.input_sanitizer",
        "engine.safety.cache_integrity",
        "engine.safety.cost_guard",
        "engine.safety.response_pii_leak",
        "engine.safety.rate_limiter",
        "engine.safety.response_alignment",
        "engine.safety.output_safety_gate",
        "engine.safety.request_pipeline",
        "engine.safety.cache_key_resolver",
    ]
    missing: list[str] = []
    for m in required:
        try:
            importlib.import_module(m)
        except Exception:
            missing.append(m)
    return {
        "checked": len(required),
        "missing": missing,
        "ok": not missing,
    }


def _check_cache_dir(cache_dir: Path | None = None) -> dict[str, Any]:
    """캐시 디렉터리 상태 — 존재, 파일 수, 가장 오래된/최신 파일 epoch."""
    if cache_dir is None:
        cache_dir = Path(__file__).resolve().parent.parent.parent / "step_archive" / "face_reading_cache"
    if not cache_dir.exists():
        return {"exists": False, "file_count": 0, "ok": False}
    files = [p for p in cache_dir.iterdir() if p.is_file()]
    if not files:
        return {"exists": True, "file_count": 0, "ok": True}
    mtimes = [p.stat().st_mtime for p in files]
    return {
        "exists": True,
        "file_count": len(files),
        "oldest_mtime": min(mtimes),
        "newest_mtime": max(mtimes),
        "ok": True,
    }


def _check_slo_window(events: list[dict[str, Any]] | None) -> dict[str, Any]:
    """SLO 윈도우 점검. events 미주입 시 compute_slo만 호출 가능한지 확인."""
    from engine.safety.slo import compute_slo
    if events is None:
        # 모듈 자체 동작만 확인
        s = compute_slo([])
        return {
            "callable": True,
            "request_count": s["request_count"],
            "violations": s["slo_violations"],
        }
    s = compute_slo(events)
    return {
        "callable": True,
        "request_count": s["request_count"],
        "crisis_rate": s["crisis_rate"],
        "err_rate": s["err_rate"],
        "cache_hit_rate": s["cache_hit_rate"],
        "p95_ms": s["latency_ms"]["p95"],
        "p99_ms": s["latency_ms"]["p99"],
        "violations": s["slo_violations"],
    }


def _check_alert_router_consistency() -> dict[str, Any]:
    """알람 라우터 분류 표가 변형되지 않았는지 확인."""
    from engine.safety.alert_router import classify_event, classify_slo_violation, P0, P1, P2
    samples = {
        "crisis_block_failed": (classify_event("crisis_block_failed"), P0),
        "slo_p95_text": (classify_slo_violation("p95=6500ms > 5000ms"), P1),
        "slo_cache_text": (classify_slo_violation("cache_hit_rate=0.05 < 0.10"), P2),
    }
    mismatches = {k: v for k, (v, expected) in samples.items() if v != expected}
    return {
        "samples_checked": len(samples),
        "mismatches": mismatches,
        "ok": not mismatches,
    }


def _check_rollback_policy_consistency() -> dict[str, Any]:
    """롤백 정책 표 일관성 — 핵심 키 3건 확인."""
    from engine.safety.rollback_trigger import classify_rollback_policy, AUTO, APPROVAL, NEVER
    expected = {
        "crisis_block_failed": AUTO,
        "slo_violation:p95": APPROVAL,
        "golden_set_regression": NEVER,
    }
    mismatches = {k: classify_rollback_policy(k) for k, v in expected.items()
                  if classify_rollback_policy(k) != v}
    return {
        "samples_checked": len(expected),
        "mismatches": mismatches,
        "ok": not mismatches,
    }


def _check_emotion_disclosure_regions() -> dict[str, Any]:
    """EU AI Act §50(3) 의무 지역 매핑 일관성."""
    from engine.safety.emotion_disclosure import (
        is_emotion_disclosure_required,
        is_emotion_disclosure_recommended,
    )
    checks = {
        "DE_required": is_emotion_disclosure_required("DE"),
        "EU_required": is_emotion_disclosure_required("EU"),
        "KR_not_required": not is_emotion_disclosure_required("KR"),
        "UK_recommended": is_emotion_disclosure_recommended("UK"),
        "JP_not_recommended": not is_emotion_disclosure_recommended("JP"),
    }
    failed = [k for k, v in checks.items() if not v]
    return {
        "checks": len(checks),
        "failed": failed,
        "ok": not failed,
    }


# ─────────────────────────── 결과 등급 ───────────────────────────

def _aggregate_status(sections: dict[str, dict[str, Any]]) -> str:
    """모든 섹션의 ok 플래그·violations로 OK/WARN/CRITICAL 결정."""
    safety = sections.get("safety_imports", {})
    if safety and not safety.get("ok"):
        return "CRITICAL"  # 안전 모듈 임포트 실패는 즉시 CRITICAL
    alert = sections.get("alert_router", {})
    if alert and not alert.get("ok"):
        return "CRITICAL"  # 알람 라우터가 망가지면 사고 통보 불가능
    rollback = sections.get("rollback_policy", {})
    if rollback and not rollback.get("ok"):
        return "CRITICAL"  # 롤백 정책 표 손상도 동일
    slo = sections.get("slo_window", {})
    if slo and slo.get("violations"):
        return "WARN"
    emotion = sections.get("emotion_disclosure", {})
    if emotion and not emotion.get("ok"):
        return "WARN"
    cache = sections.get("cache_dir", {})
    if cache and cache.get("exists") is False:
        return "WARN"
    return "OK"


# ─────────────────────────── Public API ───────────────────────────

def run_quick_check(
    *,
    events: list[dict[str, Any]] | None = None,
    cache_dir: Path | None = None,
) -> dict[str, Any]:
    """전체 빠른 점검을 실행하고 dict로 결과 반환.

    Args:
        events: SLO 윈도우 점검에 사용할 face_reading 이벤트 목록.
                None이면 모듈 가용성만 확인.
        cache_dir: 점검할 캐시 경로 override (테스트용).

    Returns:
        {
            "timestamp_epoch": float,
            "status": "OK" | "WARN" | "CRITICAL",
            "sections": {
                "safety_imports": {...},
                "cache_dir": {...},
                "slo_window": {...},
                "alert_router": {...},
                "rollback_policy": {...},
                "emotion_disclosure": {...},
            },
        }
    """
    sections = {
        "safety_imports": _check_safety_imports(),
        "cache_dir": _check_cache_dir(cache_dir),
        "slo_window": _check_slo_window(events),
        "alert_router": _check_alert_router_consistency(),
        "rollback_policy": _check_rollback_policy_consistency(),
        "emotion_disclosure": _check_emotion_disclosure_regions(),
    }
    return {
        "timestamp_epoch": time.time(),
        "status": _aggregate_status(sections),
        "sections": sections,
    }


def format_quick_check_text(report: dict[str, Any]) -> str:
    """CLI 표시용 사람-읽기 가능 텍스트. SSH 셸에서 한눈에 보기 위함."""
    lines: list[str] = []
    status = report.get("status", "?")
    sym = {"OK": "OK", "WARN": "WARN", "CRITICAL": "CRITICAL"}.get(status, status)
    lines.append(f"[face_reading quick_check] STATUS={sym}")
    lines.append(f"timestamp_epoch={report.get('timestamp_epoch')}")
    sections = report.get("sections", {}) or {}
    for name, body in sections.items():
        ok = body.get("ok", body.get("ok"))
        lines.append(f"  [{name}] ok={ok}")
        for k, v in body.items():
            if k == "ok":
                continue
            # 길이 제한 — SSH 한 줄
            sv = str(v)
            if len(sv) > 120:
                sv = sv[:117] + "..."
            lines.append(f"      {k}: {sv}")
    return "\n".join(lines)
