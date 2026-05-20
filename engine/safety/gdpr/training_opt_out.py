"""ADR-062 — RLHF·모델 학습 거부 권리 (opt-out) 영속 결정론.

KISA 생성형 AI 개인정보 처리 안내서 + GDPR Art.21 (이의 제기 권리) 정합.
사용자가 본인 풀이 텍스트의 학습 활용을 거부한 후 토글 상태를 영속 보관.

원칙:
  · 본 시스템 ADR-010 사실성 분리 — 풀이 텍스트 학습 미사용 정책 (디폴트)
  · 본 모듈은 사용자가 명시적으로 거부 의사 표명 시 영속 기록 + 검증
  · UI는 본 모듈의 API를 호출, 토글 상태를 사용자 설정 화면에 반영

저장:
  step_archive/training_opt_out/{user_hash}.json
  - 사용자 식별은 SHA256 해시 (UID·이름 원본 저장 X — ADR-010 정합)
  - 토글 변경 이력 추적 (audit log)
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path


# 저장 위치 — face_reading_cache·feedback와 동일 디렉토리
_OPT_OUT_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "step_archive"
    / "training_opt_out"
)
_OPT_OUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class OptOutRecord:
    """단일 사용자 학습 거부 기록.

    Attributes:
        user_hash: 사용자 식별 해시 (SHA256 앞 16자)
        opted_out: 거부 토글 상태
        first_set: 최초 설정 시각 (unix)
        last_updated: 마지막 변경 시각
        change_log: 토글 변경 이력 (list of (timestamp, new_state))
    """
    user_hash: str
    opted_out: bool
    first_set: float
    last_updated: float
    change_log: list[tuple[float, bool]] = field(default_factory=list)


def user_hash(user_id: str, length: int = 16) -> str:
    """사용자 식별자 해시 — UID·이름 원본 저장 차단.

    Args:
        user_id: 사용자 식별자 (이메일·UID·세션 키 등)
        length: 해시 앞 N자 (기본 16)
    """
    if not user_id:
        return ""
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:length]


def _record_path(uhash: str) -> Path:
    return _OPT_OUT_DIR / f"{uhash}.json"


def _load_record(uhash: str) -> OptOutRecord | None:
    p = _record_path(uhash)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return OptOutRecord(
            user_hash=data["user_hash"],
            opted_out=bool(data["opted_out"]),
            first_set=float(data["first_set"]),
            last_updated=float(data["last_updated"]),
            change_log=[(float(t), bool(s)) for t, s in data.get("change_log", [])],
        )
    except (json.JSONDecodeError, OSError, KeyError, TypeError, ValueError):
        return None


def _save_record(record: OptOutRecord) -> None:
    p = _record_path(record.user_hash)
    tmp = p.with_suffix(".tmp")
    try:
        tmp.write_text(
            json.dumps({
                "user_hash": record.user_hash,
                "opted_out": record.opted_out,
                "first_set": record.first_set,
                "last_updated": record.last_updated,
                "change_log": list(record.change_log),
            }, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        tmp.replace(p)
    except OSError:
        pass


def set_opt_out(user_id: str, opted_out: bool) -> OptOutRecord:
    """사용자 opt-out 토글 설정·변경.

    Args:
        user_id: 사용자 식별자 (해시화되어 저장)
        opted_out: True면 학습 거부, False면 허용

    Returns:
        저장된 OptOutRecord
    """
    uhash = user_hash(user_id)
    if not uhash:
        raise ValueError("user_id is empty")

    now = time.time()
    existing = _load_record(uhash)

    if existing is None:
        record = OptOutRecord(
            user_hash=uhash,
            opted_out=opted_out,
            first_set=now,
            last_updated=now,
            change_log=[(now, opted_out)],
        )
    else:
        new_log = list(existing.change_log)
        if existing.opted_out != opted_out:
            new_log.append((now, opted_out))
        record = OptOutRecord(
            user_hash=uhash,
            opted_out=opted_out,
            first_set=existing.first_set,
            last_updated=now,
            change_log=new_log,
        )

    _save_record(record)
    return record


def is_opted_out(user_id: str) -> bool:
    """본 사용자의 학습 거부 여부. 미설정 사용자는 False (디폴트 허용)."""
    uhash = user_hash(user_id)
    if not uhash:
        return False
    record = _load_record(uhash)
    return record.opted_out if record else False


def get_record(user_id: str) -> OptOutRecord | None:
    """사용자 opt-out 기록 조회 (DSR 응답 시 사용)."""
    uhash = user_hash(user_id)
    if not uhash:
        return None
    return _load_record(uhash)


def get_aggregate_stats() -> dict[str, int]:
    """전체 opt-out 통계 — 분기별 운영 책임자 검토용 (PII 미포함)."""
    total = 0
    opted_out = 0
    for p in _OPT_OUT_DIR.iterdir():
        if not p.is_file() or p.suffix != ".json":
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            total += 1
            if bool(data.get("opted_out")):
                opted_out += 1
        except (json.JSONDecodeError, OSError):
            continue
    return {
        "total_users_with_preference": total,
        "opted_out_count": opted_out,
        "opted_in_count": total - opted_out,
    }


__all__ = [
    "OptOutRecord",
    "user_hash",
    "set_opt_out",
    "is_opted_out",
    "get_record",
    "get_aggregate_stats",
]
