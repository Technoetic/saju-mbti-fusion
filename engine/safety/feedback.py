"""사용자 피드백 수집기 — 운영표준 §7.2.7 본문화.

풀이 본문 해시(앞 8자)에만 키잉되는 익명 카운트.
사용자 UID·풀이 본문·이미지는 어디에도 저장하지 않는다.

저장 형식 (단일 JSON 파일):
  {
    "<reading_hash>": {
      "accuracy_yes": int,
      "accuracy_no": int,
      "satisfaction_yes": int,
      "satisfaction_no": int,
      "regenerate_count": int,
      "first_seen": <unix_ts>,
      "last_updated": <unix_ts>
    },
    ...
  }

원칙 (§7.2.7):
  · 익명 카운트만 — UID·본문·이미지 미저장
  · RLHF 입력으로 사용하지 않음 — 분기별 운영 책임자 검토용
  · 모델 학습·재학습 입력 미사용

피드백 종류:
  - accuracy: 맞다 / 맞지 않다 (2지선다)
  - satisfaction: 좋아요 / 싫어요 (2지선다)
  - regenerate: 동일 화두로 재호출 (≥15%면 §7.3.1 절차 발동)
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from threading import Lock
from typing import Any

# 저장 위치 — 캐시와 같은 디렉토리지만 별도 파일
_FEEDBACK_FILE = (
    Path(__file__).resolve().parent.parent.parent
    / "step_archive"
    / "face_reading_cache"
    / "_feedback_counts.json"
)
_FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)

_LOCK = Lock()


def reading_hash(text: str, length: int = 8) -> str:
    """풀이 본문의 SHA256 앞 N자 — 익명 카운트 키.

    같은 풀이 텍스트면 같은 키. UID·이미지 정보 일절 없음.
    """
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def _load_counts() -> dict[str, Any]:
    """저장된 카운트 로드 — 파일 부재/손상 시 빈 dict."""
    if not _FEEDBACK_FILE.exists():
        return {}
    try:
        return json.loads(_FEEDBACK_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_counts(counts: dict[str, Any]) -> None:
    """저장 — 원자적 쓰기 (임시 파일 → rename)."""
    tmp = _FEEDBACK_FILE.with_suffix(".tmp")
    try:
        tmp.write_text(
            json.dumps(counts, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        tmp.replace(_FEEDBACK_FILE)
    except OSError:
        pass


_VALID_KINDS = frozenset([
    "accuracy_yes",
    "accuracy_no",
    "satisfaction_yes",
    "satisfaction_no",
    "regenerate_count",
])


def record_feedback(reading_text: str, kind: str) -> bool:
    """익명 피드백 1회 기록.

    Args:
        reading_text: 풀이 본문. 해시 앞 8자만 키로 저장.
        kind: 'accuracy_yes' / 'accuracy_no' / 'satisfaction_yes' /
              'satisfaction_no' / 'regenerate_count' 중 하나.

    Returns:
        True 기록 성공, False 무효 kind.
    """
    if kind not in _VALID_KINDS:
        return False
    if not reading_text:
        return False
    key = reading_hash(reading_text)
    if not key:
        return False
    now = time.time()
    with _LOCK:
        counts = _load_counts()
        entry = counts.setdefault(key, {
            "accuracy_yes": 0,
            "accuracy_no": 0,
            "satisfaction_yes": 0,
            "satisfaction_no": 0,
            "regenerate_count": 0,
            "first_seen": now,
            "last_updated": now,
        })
        entry[kind] = int(entry.get(kind, 0)) + 1
        entry["last_updated"] = now
        _save_counts(counts)
    return True


def get_aggregate_stats() -> dict[str, Any]:
    """전체 누적 통계 — 분기별 운영 책임자 검토용 (§7.2.7).

    개별 풀이 키는 노출하지 않고 합계만 반환.
    """
    counts = _load_counts()
    total: dict[str, Any] = {
        "total_readings_with_feedback": len(counts),
        "accuracy_yes": 0,
        "accuracy_no": 0,
        "satisfaction_yes": 0,
        "satisfaction_no": 0,
        "regenerate_count": 0,
    }
    for entry in counts.values():
        for k in ("accuracy_yes", "accuracy_no",
                  "satisfaction_yes", "satisfaction_no",
                  "regenerate_count"):
            total[k] += int(entry.get(k, 0))
    # 비율 계산 — §7.3.2 SLO 측정원
    a_total = total["accuracy_yes"] + total["accuracy_no"]
    s_total = total["satisfaction_yes"] + total["satisfaction_no"]
    total["accuracy_rate"] = (
        total["accuracy_yes"] / a_total if a_total else None
    )
    total["satisfaction_rate"] = (
        total["satisfaction_yes"] / s_total if s_total else None
    )
    return total


def get_reading_counts(reading_text: str) -> dict[str, int] | None:
    """특정 풀이 본문의 누적 카운트 — 클라이언트 즉시 피드백 후 갱신 표시용.

    Returns: None if 키 없음, 카운트 dict otherwise.
    """
    key = reading_hash(reading_text)
    if not key:
        return None
    counts = _load_counts()
    entry = counts.get(key)
    if not entry:
        return None
    return {
        "accuracy_yes": int(entry.get("accuracy_yes", 0)),
        "accuracy_no": int(entry.get("accuracy_no", 0)),
        "satisfaction_yes": int(entry.get("satisfaction_yes", 0)),
        "satisfaction_no": int(entry.get("satisfaction_no", 0)),
        "regenerate_count": int(entry.get("regenerate_count", 0)),
    }
