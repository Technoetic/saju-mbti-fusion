"""ADR-061 — 표시광고법 정확도 표기 자동 검사.

한국 표시·광고의 공정화에 관한 법률(표시광고법)은 과학적·객관적 근거 없는
"정확도 X%·과학적 증명·100% 적중" 같은 표현을 부당한 광고로 규정.
운세·관상·작명 SaaS는 본질상 정확도 표기 불가하므로, 마케팅 카피·UI 텍스트에서
이런 표현을 자동 차단 의무.

근거:
  - 표시광고법 §3 (부당한 표시·광고) 1호: 거짓·과장 표시·광고 금지
  - 한국공정거래위원회: 효과·성능 등 객관적 근거 의무

원칙 (ADR-006 정합):
  · 본 모듈은 결정론 키워드 검사 — 법률 판정 X
  · 변호사 검토 보조 도구 — 최종 광고 사용 결정은 사용자 의무
  · "운세 정확도 95%" 같은 명백 위반만 차단, 미묘 표현은 경고 (사용자 검토)
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# ─────────────────────────── 금지 패턴 (정확도·성능 단정) ───────────────────────────

# 명확한 정확도 표기 — 즉시 차단 (REJECT)
_FORBIDDEN_PATTERNS = (
    # 정확도/적중률 % 표기
    re.compile(r"정확도\s*\d+\s*%"),
    re.compile(r"적중률\s*\d+\s*%"),
    re.compile(r"accuracy\s*\d+\s*%", re.IGNORECASE),
    re.compile(r"\d+\s*%\s*정확"),
    re.compile(r"\d+\s*%\s*적중"),
    # 100% 단정
    re.compile(r"100\s*%\s*(정확|적중|보장|맞)"),
    # 과학적 증명 단정
    re.compile(r"과학적\s*(으로\s*)?(증명|입증|검증)"),
    re.compile(r"scientifically\s+proven", re.IGNORECASE),
    # 의료 효과 단정 (ADR-006 강화)
    re.compile(r"(우울|불안|질병)\s*(치료|완치|예방)"),
    re.compile(r"의학적\s*효과"),
)

# 경고 패턴 — 사용자 검토 의무 (WARN)
_WARN_PATTERNS = (
    # 일반 "정확" 어휘 (수치 없이) — 컨텍스트 의존
    re.compile(r"가장\s*정확"),
    re.compile(r"매우\s*정확"),
    re.compile(r"완벽\s*(한|히)\s*맞"),
    # 보장 어휘
    re.compile(r"반드시\s*(맞|적중|좋|성공)"),
    re.compile(r"확실\s*(히\s*)?(맞|적중)"),
)


@dataclass(frozen=True)
class AdvertisingViolation:
    """단일 위반 발견.

    Attributes:
        severity: 'REJECT' (명확 위반) | 'WARN' (사용자 검토)
        pattern: 매칭된 패턴 설명
        matched_text: 실 매칭 텍스트
        position: 원문 시작 인덱스
        legal_basis: 법령 근거 (예: "표시광고법 §3 1호")
    """
    severity: str
    pattern: str
    matched_text: str
    position: int
    legal_basis: str


def check_advertising_copy(text: str) -> list[AdvertisingViolation]:
    """마케팅 카피·UI 텍스트의 표시광고법 위반 검사.

    Args:
        text: 검사할 카피 (마케팅 페이지·푸터·약관·UI 라벨 등)

    Returns:
        위반 목록. 빈 리스트면 통과.
    """
    if not text:
        return []

    violations: list[AdvertisingViolation] = []

    for pat in _FORBIDDEN_PATTERNS:
        for m in pat.finditer(text):
            violations.append(AdvertisingViolation(
                severity="REJECT",
                pattern=pat.pattern,
                matched_text=m.group(0),
                position=m.start(),
                legal_basis="표시광고법 §3 1호 (거짓·과장 표시·광고 금지)",
            ))

    for pat in _WARN_PATTERNS:
        for m in pat.finditer(text):
            violations.append(AdvertisingViolation(
                severity="WARN",
                pattern=pat.pattern,
                matched_text=m.group(0),
                position=m.start(),
                legal_basis="표시광고법 §3 (변호사 검토 권고)",
            ))

    # 위치 순 정렬
    violations.sort(key=lambda v: v.position)
    return violations


def is_compliant(text: str) -> bool:
    """REJECT 위반이 없으면 True. WARN만 있으면 True (사용자 검토 후 결정)."""
    return not any(v.severity == "REJECT" for v in check_advertising_copy(text))


def format_violations_report(violations: list[AdvertisingViolation]) -> str:
    """위반 보고서 한국어 — 마케팅 팀·변호사 검토용."""
    if not violations:
        return "위반 없음 — 표시광고법 정합 (단 본 검사는 결정론 키워드 기반, 변호사 최종 검토 권고)."

    lines = [f"표시광고법 위반 {len(violations)}건 발견:"]
    for v in violations:
        lines.append(
            f"  [{v.severity}] '{v.matched_text}' (위치 {v.position}) — {v.legal_basis}"
        )
    lines.append("\n※ 본 검사는 결정론 키워드 기반. 변호사 최종 검토 의무 (ADR-006).")
    return "\n".join(lines)


__all__ = [
    "AdvertisingViolation",
    "check_advertising_copy",
    "is_compliant",
    "format_violations_report",
]
