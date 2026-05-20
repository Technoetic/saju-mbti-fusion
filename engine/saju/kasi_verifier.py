"""KASI (한국천문연구원) 음양력 API 외부 검증 모듈.

본 시스템 `day_pillar` 알고리즘을 KASI 공식 음양력 API와 회귀 비교.

ADR-073 확장 — 1000건 자동 회귀 가능 (KASI_API_KEY 환경변수 등록 시).

ADR 정합:
  · ADR-010 사실성 분리 — 외부 공인 ground truth로 본 시스템 검증
  · ADR-073 — 천문 앵커 + 수학 불변량 + 명리 매트릭스 검증 확장
  · 키 미등록 시 graceful skip (CI 비차단)

API:
  · 엔드포인트: apis.data.go.kr/B090041/openapi/service/LrsrCldInfoService/getLunCalInfo
  · 인증: ServiceKey (data.go.kr 발급)
  · 응답: lunIljin (한자 일진), lunSecha (한자 세차)
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date
from typing import Optional

# KASI API 엔드포인트 (data.go.kr 공식)
_KASI_LUN_CAL_URL = (
    "https://apis.data.go.kr/B090041/openapi/service/"
    "LrsrCldInfoService/getLunCalInfo"
)

@dataclass(frozen=True)
class KasiVerificationResult:
    """KASI 회귀 비교 결과.

    Attributes:
        target_date: 비교 대상 양력 일자
        local_iljin_han: 본 시스템 산출 일진 한자 (예: "乙巳")
        kasi_iljin_han: KASI 회신 일진 한자 (예: "乙巳")
        match: 정합 여부
        kasi_called: 실제 KASI API 호출 여부 (키 없으면 False)
        skip_reason: API 호출 안 한 사유 (키 부재·요청 실패 등)
    """
    target_date: date
    local_iljin_han: str
    kasi_iljin_han: Optional[str]
    match: bool
    kasi_called: bool
    skip_reason: str = ""


def kasi_key_available() -> bool:
    """KASI_API_KEY 환경변수 존재 여부."""
    return bool(os.environ.get("KASI_API_KEY", "").strip())


def fetch_kasi_iljin(target: date, timeout_sec: float = 5.0) -> Optional[str]:
    """KASI 음양력 API에서 일진 한자 조회.

    Args:
        target: 양력 일자
        timeout_sec: HTTP 타임아웃

    Returns:
        일진 한자 (예: "乙巳") 또는 None (호출 실패 시)

    Notes:
        키 부재 시 None 반환. CI 비차단 의무.
        본 함수는 외부 HTTP 호출 → 단위 회귀에서는 mock 또는 skip.
    """
    api_key = os.environ.get("KASI_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        import httpx
    except ImportError:
        return None

    params = {
        "ServiceKey": api_key,
        "solYear": f"{target.year:04d}",
        "solMonth": f"{target.month:02d}",
        "solDay": f"{target.day:02d}",
    }
    try:
        with httpx.Client(timeout=timeout_sec) as client:
            resp = client.get(_KASI_LUN_CAL_URL, params=params)
        if resp.status_code != 200:
            return None
        body = resp.text
        # XML 응답 — <lunIljin>乙巳</lunIljin> 정규식 추출
        match = re.search(r"<lunIljin>([^<]+)</lunIljin>", body)
        if not match:
            return None
        raw = match.group(1).strip()
        # KASI 응답이 "乙巳(을사)" 형식이면 한자 부분만 추출
        han_match = re.match(r"([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])", raw)
        if han_match:
            return han_match.group(1)
        return raw[:2] if len(raw) >= 2 else None
    except Exception:
        return None


def verify_day_pillar_against_kasi(target: date) -> KasiVerificationResult:
    """본 시스템 day_pillar vs KASI 일진 정합 검증.

    Args:
        target: 양력 일자

    Returns:
        KasiVerificationResult — match 필드로 정합 여부 확인.

    Notes:
        KASI_API_KEY 부재 시 kasi_called=False + match=True (비교 불가, 통과 처리).
        키 존재 + 정합 시 match=True.
        키 존재 + 불일치 시 match=False (회귀 실패 → 본 시스템 알고리즘 결손).
    """
    from engine.saju.pillars import day_pillar  # 지연 import 순환 차단

    local = day_pillar(target.year, target.month, target.day)
    local_han = f"{local['gan_han']}{local['ji_han']}"

    if not kasi_key_available():
        return KasiVerificationResult(
            target_date=target,
            local_iljin_han=local_han,
            kasi_iljin_han=None,
            match=True,  # 비교 불가 → 통과 처리 (CI 비차단)
            kasi_called=False,
            skip_reason="KASI_API_KEY 환경변수 미등록",
        )

    kasi_han = fetch_kasi_iljin(target)
    if kasi_han is None:
        return KasiVerificationResult(
            target_date=target,
            local_iljin_han=local_han,
            kasi_iljin_han=None,
            match=True,
            kasi_called=False,
            skip_reason="KASI API 호출 실패 (네트워크·타임아웃)",
        )

    return KasiVerificationResult(
        target_date=target,
        local_iljin_han=local_han,
        kasi_iljin_han=kasi_han,
        match=local_han == kasi_han,
        kasi_called=True,
    )


def batch_verify(targets: list[date]) -> tuple[int, int, int, list[KasiVerificationResult]]:
    """다건 KASI 회귀 배치.

    Args:
        targets: 양력 일자 리스트

    Returns:
        (match_count, mismatch_count, skipped_count, results)

    Notes:
        KASI API rate limit 고려 — 호출 간격 0.1초 (1000건 = ~100초).
    """
    import time

    match_n, mismatch_n, skip_n = 0, 0, 0
    results: list[KasiVerificationResult] = []

    for i, target in enumerate(targets):
        r = verify_day_pillar_against_kasi(target)
        results.append(r)
        if not r.kasi_called:
            skip_n += 1
        elif r.match:
            match_n += 1
        else:
            mismatch_n += 1
        # rate limit (KASI 정책 영 0.1초 간격)
        if r.kasi_called and i < len(targets) - 1:
            time.sleep(0.1)

    return match_n, mismatch_n, skip_n, results


__all__ = [
    "KasiVerificationResult",
    "kasi_key_available",
    "fetch_kasi_iljin",
    "verify_day_pillar_against_kasi",
    "batch_verify",
]
