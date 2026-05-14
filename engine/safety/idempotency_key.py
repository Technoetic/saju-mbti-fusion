"""멱등 키 관리자 — 운영표준 §7.2.14 본문화.

face_reading 캐시는 24시간 결과 재사용이지만, 같은 사진+화두를 사용자가
즉시 재전송하거나 네트워크 재시도하는 경우 동시 in-flight 요청이 LLM을
중복 호출해 비용·SLO 회귀를 일으킬 수 있다.

본 모듈은 짧은 윈도우(기본 60초)에 같은 멱등 키로 들어온 요청을 단일 결과로
조정한다. 캐시(_hash_payload)와는 별개의 in-flight 레이어.

§7.2.14 정책:
  · 멱등 키 = sha256(image_b64 + question + uid)[:24]
  · 윈도우 = 60s (네트워크 재시도 흔한 폭)
  · 키 충돌 시: 결과를 in-flight 슬롯에 단일 등록, 후속 호출자는 동일 결과 수신
  · 만료 자동 청소 (in-memory dict)

본 모듈은 단일 프로세스용. 다중 워커 환경은 외부 Redis-SETNX 어댑터 필요.
"""

from __future__ import annotations

import hashlib
import threading
import time
from dataclasses import dataclass
from typing import Any


# §7.2.14 윈도우
DEFAULT_WINDOW_SEC = 60

# §7.2.14 멱등 키 상태
SLOT_PENDING = "pending"     # 진행 중 (다른 호출자 대기)
SLOT_RESOLVED = "resolved"   # 결과 수신 완료
SLOT_FAILED = "failed"       # 실패 (재시도 가능)


@dataclass
class IdempotencySlot:
    """단일 멱등 슬롯 — 동시 요청 조정용.

    Attributes:
        key: 멱등 키
        created_at: 슬롯 생성 시각
        state: pending/resolved/failed
        result: 결과 dict (state=resolved일 때)
        error: 에러 메시지 (state=failed일 때)
    """
    key: str
    created_at: float
    state: str = SLOT_PENDING
    result: Any = None
    error: str = ""


# ─────────────────────────── 키 생성 ───────────────────────────

def compute_idempotency_key(
    *,
    image_b64: str | None,
    question: str | None,
    uid: str | None,
    extra: str = "",
) -> str:
    """결정론 멱등 키 — 같은 입력은 같은 키.

    Args:
        image_b64: 사진 (없으면 빈 문자열로 처리)
        question: 화두
        uid: 사용자 식별자 (uid 없는 익명도 키 생성 가능 — 같은 익명 사용자라면
            같은 키가 나오므로 uid 없음=충돌 위험 증가, 호출자 책임)
        extra: 추가 차원 (예: lang/region)
    """
    h = hashlib.sha256()
    h.update((image_b64 or "").encode("utf-8")[:1_000_000])  # 1MB 상한
    h.update(b"\x00")
    h.update((question or "").encode("utf-8"))
    h.update(b"\x00")
    h.update((uid or "").encode("utf-8"))
    h.update(b"\x00")
    h.update(extra.encode("utf-8"))
    return h.hexdigest()[:24]


# ─────────────────────────── 슬롯 관리자 ───────────────────────────

class IdempotencyManager:
    """단일 프로세스 in-memory 슬롯 관리자.

    멀티스레드 안전 (RLock). 다중 워커 분산은 외부 Redis 등 별도 백엔드 필요.
    """

    def __init__(self, window_sec: int = DEFAULT_WINDOW_SEC) -> None:
        self._window_sec = window_sec
        self._slots: dict[str, IdempotencySlot] = {}
        self._lock = threading.RLock()

    def _now(self) -> float:
        return time.time()

    def _is_expired(self, slot: IdempotencySlot, *, now: float | None = None) -> bool:
        now = now if now is not None else self._now()
        return (now - slot.created_at) > self._window_sec

    def claim(self, key: str, *, now: float | None = None) -> tuple[bool, IdempotencySlot]:
        """슬롯 선점 시도.

        Returns:
            (claimed, slot):
              · claimed=True  — 호출자가 LLM 실행 책임
              · claimed=False — 기존 슬롯 진행 중·완료, 호출자는 slot.result 대기/사용
        """
        now = now if now is not None else self._now()
        with self._lock:
            existing = self._slots.get(key)
            if existing is not None and not self._is_expired(existing, now=now):
                return False, existing
            # 만료된 슬롯은 새 슬롯으로 덮어씀
            new_slot = IdempotencySlot(
                key=key,
                created_at=now,
                state=SLOT_PENDING,
            )
            self._slots[key] = new_slot
            return True, new_slot

    def resolve(self, key: str, result: Any) -> None:
        """LLM 실행 책임자가 결과를 슬롯에 등록."""
        with self._lock:
            slot = self._slots.get(key)
            if slot is None:
                return
            slot.state = SLOT_RESOLVED
            slot.result = result

    def fail(self, key: str, error: str) -> None:
        """실행 실패 — 후속 호출자가 재시도 가능하도록 표시."""
        with self._lock:
            slot = self._slots.get(key)
            if slot is None:
                return
            slot.state = SLOT_FAILED
            slot.error = error

    def get(self, key: str) -> IdempotencySlot | None:
        with self._lock:
            return self._slots.get(key)

    def purge_expired(self, *, now: float | None = None) -> int:
        """만료 슬롯 제거. 반환: 삭제된 슬롯 수."""
        now = now if now is not None else self._now()
        with self._lock:
            stale = [k for k, s in self._slots.items() if self._is_expired(s, now=now)]
            for k in stale:
                del self._slots[k]
            return len(stale)

    def size(self) -> int:
        with self._lock:
            return len(self._slots)

    def reset(self) -> None:
        """테스트용 — 모든 슬롯 제거."""
        with self._lock:
            self._slots.clear()


# ─────────────────────────── 트레이스 페이로드 ───────────────────────────

def to_trace_event(
    *,
    key: str,
    claimed: bool,
    slot_state: str,
) -> dict[str, Any]:
    """§7.3.4 tracing extra 호환 페이로드."""
    return {
        "idempotency_key": key,
        "idempotency_claimed": claimed,  # True면 LLM 실행자, False면 동시 대기
        "idempotency_slot_state": slot_state,
    }
