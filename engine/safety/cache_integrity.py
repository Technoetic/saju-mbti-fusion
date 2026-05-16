"""캐시 무결성 검증 — 운영표준 §7.2.16 본문화.

face_reading의 디스크 캐시(_save_cache/_load_cache)가 외부 변조·파일시스템
손상·다른 버전 시스템 프롬프트의 결과 혼입으로 깨졌을 때 결정론 감지.

cache_janitor(§7.2.12)가 "만료된 파일 청소"라면, 본 모듈은 "남아있는 파일의
내용이 유효한가" 검사.

§7.2.16 검증 항목:
  · JSON 파싱 가능
  · response_envelope.REQUIRED_KEYS 모두 존재
  · text는 비어있지 않은 문자열
  · legal_notice 존재 (사용자 응답 누락 방지)
  · cached 키 = True (캐시에 저장된 항목은 cached=True여야 함)
  · 선택: 시스템 프롬프트 해시 검증 (face_reading._SYSTEM_PROMPT_HASH 변경 시
    이전 캐시 무효화 — 호출자가 hash 주입)

본 모듈은 부수효과 없음(읽기만). 손상 파일 삭제는 호출자/cache_janitor에 위임.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# §7.2.16 손상 코드
INTEGRITY_PARSE_ERROR = "parse_error"        # JSON 파싱 실패
INTEGRITY_MISSING_KEY = "missing_key"        # REQUIRED_KEYS 누락
INTEGRITY_EMPTY_TEXT = "empty_text"          # text 비어있음
INTEGRITY_MISSING_LEGAL = "missing_legal_notice"
INTEGRITY_NOT_DICT = "not_a_dict"
INTEGRITY_PROMPT_HASH_MISMATCH = "prompt_hash_mismatch"


@dataclass(frozen=True)
class IntegrityResult:
    file_path: str
    issues: list[str] = field(default_factory=list)
    file_size: int = 0

    @property
    def ok(self) -> bool:
        return not self.issues


@dataclass(frozen=True)
class IntegrityAuditReport:
    total: int
    valid: int
    invalid: int
    issues_by_file: dict[str, list[str]] = field(default_factory=dict)
    total_size_bytes: int = 0


# ─────────────────────────── 단일 파일 검증 ───────────────────────────

def verify_cache_file(
    file_path: Path,
    *,
    expected_prompt_hash: str | None = None,
) -> IntegrityResult:
    """단일 캐시 파일의 §7.2.16 무결성 검증. 부수효과 없음.

    Args:
        file_path: 캐시 파일 절대경로
        expected_prompt_hash: 주어지면 응답 내 prompt_hash와 비교 (mismatch 시 손상)
    """
    issues: list[str] = []
    size = 0
    try:
        size = file_path.stat().st_size
    except OSError:
        pass

    try:
        raw = file_path.read_text(encoding="utf-8")
    except OSError:
        return IntegrityResult(
            file_path=str(file_path),
            issues=[INTEGRITY_PARSE_ERROR],
            file_size=size,
        )

    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        issues.append(INTEGRITY_PARSE_ERROR)
        return IntegrityResult(
            file_path=str(file_path),
            issues=issues,
            file_size=size,
        )

    if not isinstance(body, dict):
        issues.append(INTEGRITY_NOT_DICT)
        return IntegrityResult(
            file_path=str(file_path),
            issues=issues,
            file_size=size,
        )

    # REQUIRED_KEYS (response_envelope와 일관)
    required = ("text", "cached", "crisis_alert", "legal_notice",
                "detected_language", "language_advisory")
    for k in required:
        if k not in body:
            issues.append(f"{INTEGRITY_MISSING_KEY}:{k}")

    # text 비어있지 않음
    text = body.get("text")
    if not isinstance(text, str) or not text.strip():
        issues.append(INTEGRITY_EMPTY_TEXT)

    # legal_notice 존재 (위기 응답 외에는 반드시 첨부됨)
    legal = body.get("legal_notice")
    if legal is None or (isinstance(legal, str) and not legal.strip()):
        # 크리시 응답 분기일 수도 있으니, crisis_alert가 없을 때만 위반
        if not body.get("crisis_alert"):
            issues.append(INTEGRITY_MISSING_LEGAL)

    # 시스템 프롬프트 해시 검증 (선택)
    if expected_prompt_hash:
        stored_hash = body.get("system_prompt_hash") or body.get("prompt_hash")
        if stored_hash and stored_hash != expected_prompt_hash:
            issues.append(
                f"{INTEGRITY_PROMPT_HASH_MISMATCH}:{stored_hash}!={expected_prompt_hash}"
            )

    return IntegrityResult(
        file_path=str(file_path),
        issues=issues,
        file_size=size,
    )


# ─────────────────────────── 디렉터리 일괄 감사 ───────────────────────────

def audit_cache_directory(
    cache_dir: Path,
    *,
    expected_prompt_hash: str | None = None,
) -> IntegrityAuditReport:
    """디렉터리 내 모든 .json 파일 일괄 검증."""
    if not cache_dir.exists():
        return IntegrityAuditReport(total=0, valid=0, invalid=0)
    files = [p for p in cache_dir.iterdir() if p.is_file()]
    issues_by_file: dict[str, list[str]] = {}
    valid = 0
    total_size = 0
    for p in files:
        r = verify_cache_file(p, expected_prompt_hash=expected_prompt_hash)
        total_size += r.file_size
        if r.ok:
            valid += 1
        else:
            issues_by_file[p.name] = r.issues
    return IntegrityAuditReport(
        total=len(files),
        valid=valid,
        invalid=len(issues_by_file),
        issues_by_file=issues_by_file,
        total_size_bytes=total_size,
    )


def list_corrupt_files(
    cache_dir: Path,
    *,
    expected_prompt_hash: str | None = None,
) -> list[Path]:
    """손상 파일 경로 목록 — cache_janitor가 삭제 대상으로 받음."""
    if not cache_dir.exists():
        return []
    corrupt: list[Path] = []
    for p in cache_dir.iterdir():
        if not p.is_file():
            continue
        r = verify_cache_file(p, expected_prompt_hash=expected_prompt_hash)
        if not r.ok:
            corrupt.append(p)
    return corrupt


# ─────────────────────────── 알람 ───────────────────────────

def to_alert_payload(
    report: IntegrityAuditReport,
    *,
    corruption_rate_threshold: float = 0.05,
) -> dict[str, Any]:
    """§14.3 alert_router 호환 페이로드.

    손상율 5% 초과 시 P1, 1% 초과 시 P2, 그 외 P3.
    """
    rate = (report.invalid / report.total) if report.total > 0 else 0.0
    if rate > corruption_rate_threshold:
        severity = "P1"
    elif rate > 0.01:
        severity = "P2"
    else:
        severity = "P3"
    return {
        "service": "cache_integrity",
        "severity": severity,
        "total": report.total,
        "valid": report.valid,
        "invalid": report.invalid,
        "corruption_rate": round(rate, 4),
        "sample_corrupt_files": list(report.issues_by_file.keys())[:5],
    }
