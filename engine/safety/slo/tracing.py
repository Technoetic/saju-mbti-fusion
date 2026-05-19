"""구조화 로깅·트레이싱 — 운영표준 §7.3.4 본문화.

face_reading 요청·응답을 단일 JSON 라인으로 stdout에 기록.
PII는 자동 마스킹·해싱 (uid_hash, question_hash) 후 저장.

목적:
  · SLO 측정 (응답 지연·crisis 비율·error_code 분포)
  · 인시던트 추적 (decision_branch별 카운트)
  · §7.2.7 피드백 누적 통계의 데이터원

원칙 (§7.3.4):
  · 본문(원본 question, 풀이 text) 절대 미저장
  · UID·이메일·전화·주민번호 마스킹 또는 해싱
  · stdout JSON line — Railway/GCP/AWS 어디서나 수집 가능
"""

from __future__ import annotations

import json
import sys
import time
from typing import Any

from engine.safety.gdpr.pii import hash_uid, hash_question, mask_pii


def _now_ms() -> int:
    return int(time.time() * 1000)


def emit_face_reading_event(
    *,
    event_type: str,
    request_started_at_ms: int,
    region: str | None = None,
    lang: str | None = None,
    detected_language: str | None = None,
    age: int | None = None,
    gender: str | None = None,
    question: str | None = None,
    uid: str | None = None,
    error_code: str | None = None,
    crisis_detected: bool = False,
    cached: bool = False,
    text_length: int | None = None,
    metrics_keys: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """단일 face_reading 요청 이벤트를 stdout JSON line으로 emit.

    Args:
        event_type: 'request_completed' / 'crisis_blocked' / 'err_rejected' / 'cached_hit' 등
        request_started_at_ms: 요청 진입 시각 (epoch ms)
        region, lang, detected_language: 라우팅 메타
        age, gender: 보조 정보 (gender는 그대로 — 민감하지 않음)
        question: 원본 화두 (저장 X, 해시·길이만 추출)
        uid: 사용자 식별자 (저장 X, hash_uid만)
        error_code: §7.2.1 ERR_/WARN_ 코드
        crisis_detected: 위기 신호 분기 진입 여부
        cached: 캐시 히트 여부
        text_length: 응답 본문 길이 (검열 X, 길이만)
        metrics_keys: 메트릭 사용된 키 목록 (값 X, 키 이름만)
        extra: 추가 정보 (이미 PII-safe해야 함)
    """
    now = _now_ms()
    event: dict[str, Any] = {
        "ts_ms": now,
        "event": event_type,
        "elapsed_ms": now - request_started_at_ms,
        "service": "face_reading",
    }
    if region:
        event["region"] = region
    if lang:
        event["lang"] = lang
    if detected_language:
        event["detected_language"] = detected_language
    if age is not None:
        event["age_bucket"] = _age_to_bucket(age)
    if gender:
        event["gender"] = gender
    if uid:
        event["uid_hash"] = hash_uid(uid)
    if question:
        event["question_hash"] = hash_question(question)
        event["question_len"] = len(question)
    if error_code:
        event["error_code"] = error_code
    if crisis_detected:
        event["crisis_detected"] = True
    if cached:
        event["cached"] = True
    if text_length is not None:
        event["text_len"] = text_length
    if metrics_keys is not None:
        event["metrics_keys"] = sorted(metrics_keys)
    if extra:
        # extra 내용도 마스킹 — 본문·이메일·전화 자동 가림
        event["extra"] = _sanitize_extra(extra)

    line = json.dumps(event, ensure_ascii=False, sort_keys=True)
    print(line, flush=True, file=sys.stdout)


def _age_to_bucket(age: int) -> str:
    """나이를 버킷으로 — 개별 나이 노출 회피 + 통계 활용 가능."""
    if age < 18:
        return "minor"
    if age < 30:
        return "20s"
    if age < 40:
        return "30s"
    if age < 50:
        return "40s"
    if age < 60:
        return "50s"
    if age < 70:
        return "60s"
    return "70+"


def _sanitize_extra(extra: dict[str, Any]) -> dict[str, Any]:
    """extra dict의 문자열 값에 mask_pii 적용 (재귀 1단계)."""
    out: dict[str, Any] = {}
    for k, v in extra.items():
        if isinstance(v, str):
            out[k] = mask_pii(v)
        elif isinstance(v, (int, float, bool)) or v is None:
            out[k] = v
        elif isinstance(v, dict):
            out[k] = {
                ik: (mask_pii(iv) if isinstance(iv, str) else iv)
                for ik, iv in v.items()
            }
        else:
            out[k] = str(v)[:100]  # 알 수 없는 타입은 100자로 절단
    return out


# ─────────────────────────── 컨텍스트 매니저 헬퍼 ───────────────────────────

class FaceReadingTrace:
    """with 문으로 요청 진입~종료를 자동 기록.

    예시:
        with FaceReadingTrace(uid='user-123', region='US-CA') as tr:
            ... 풀이 처리 ...
            tr.set(error_code='ERR_FACE_NOT_DETECTED', text_length=42)
    """

    def __init__(self, **initial: Any) -> None:
        self._fields: dict[str, Any] = dict(initial)
        self._started: int = _now_ms()
        self._emitted: bool = False

    def set(self, **fields: Any) -> None:
        """필드 추가/갱신. emit 직전에 호출."""
        self._fields.update(fields)

    def emit(self, event_type: str = "request_completed") -> None:
        """수동 emit. with 종료 시 자동 호출됨."""
        if self._emitted:
            return
        self._emitted = True
        emit_face_reading_event(
            event_type=event_type,
            request_started_at_ms=self._started,
            **self._fields,
        )

    def __enter__(self) -> "FaceReadingTrace":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            # 예외 타입은 extra에 넣어 emit 함수 시그니처와 호환
            extra = self._fields.setdefault("extra", {})
            extra["exception"] = exc_type.__name__
            self.emit("request_failed")
        else:
            self.emit()
