"""데이터 거버넌스 — 운영표준 §7.3.3 본문화.

골든 셋·평가셋·캐시 등 시스템이 보관하는 모든 사용자 얼굴 데이터에 대해
출처(provenance)·동의(consent)·라이선스(license)·보존기한(retention)을
구조화 메타데이터로 표준화한다.

핵심 원칙:
  · GDPR Art.7 / EU AI Act §10(5) — 생체정보 수집 시 명시적 동의 기록
  · 한국 개인정보보호법 §15·§22 — 동의 항목·보유기간·파기 기준 명시
  · §7.3.3.1 합법 출처(LICIT_SOURCES) — 그 외 데이터는 회귀 금지

§5.1 골든 셋이 21건이라도 한 건당 출처/동의가 결여되면 회귀에서 배제해야 한다.
본 모듈은 그 검증 로직을 단일 진입점으로 제공한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any


# §7.3.3.1 — 합법 출처 7종. 회귀·평가·튜닝에 사용 가능한 데이터 출처는 이 목록으로 제한.
LICIT_SOURCES = {
    "consented_user_upload",     # 동의서 받은 사용자 업로드
    "internal_employee_test",    # 사내 직원 테스트 (사내 IRB 통과)
    "synthetic_generated",       # 모델 생성 합성 얼굴 (StyleGAN 등)
    "public_domain_dataset",     # 공개 도메인 (CC0)
    "cc_by_dataset",             # CC-BY 등 학술 라이선스
    "research_partner_signed",   # 연구 파트너 NDA 체결분
    "regulator_provided",        # 규제기관 제공 테스트셋
}

# §7.3.3.2 — 금지 출처. 발견 시 즉시 격리.
ILLICIT_SOURCES = {
    "social_media_scraping",     # 동의 없는 SNS 크롤링
    "leaked_dataset",            # 유출 데이터셋
    "ip_camera_capture",         # 무동의 CCTV/IP카메라 캡처
    "minor_without_guardian",    # 미성년자 보호자 동의 없음
    "unknown",                   # 출처 불명 — 합법성 입증 책임 보유자에게
}

# §7.3.3.3 — 동의 항목. 골든 셋 한 건당 최소 이 4개 항목이 명시되어야 함.
REQUIRED_CONSENT_FIELDS = ("processing", "storage", "training", "third_party_sharing")

# §7.3.3.4 — 보존기간 최대치 (일). 생체정보는 KR개인정보법상 최단보관 원칙.
MAX_RETENTION_DAYS = {
    "consented_user_upload": 90,
    "internal_employee_test": 365,
    "synthetic_generated": 36500,  # 합성은 사실상 무기한 가능 (100년)
    "public_domain_dataset": 36500,
    "cc_by_dataset": 36500,
    "research_partner_signed": 730,
    "regulator_provided": 365,
}


@dataclass(frozen=True)
class DataProvenance:
    """단일 골든 셋 케이스의 §7.3.3 거버넌스 메타데이터.

    Attributes:
        case_id: 골든 셋 식별자 (예: "GS-021").
        source: §7.3.3.1 LICIT_SOURCES 중 하나.
        license: SPDX 라이선스 식별자 또는 사내 라벨 ("INTERNAL").
        collected_at: 수집일 (ISO 8601 YYYY-MM-DD).
        consent: 항목별 동의 여부 — REQUIRED_CONSENT_FIELDS 4개 키 필수.
        retention_days: 보유기간(일). MAX_RETENTION_DAYS[source] 이하여야 함.
        subject_age_bucket: 데이터 주체 연령대 ("20s", "30s", ...). 미성년자(minor)는 금지.
        region: 데이터 주체 거주 지역 (BCP-47-region; KR/US-CA/EU/...).
        notes: 자유 메모 (예: NDA 번호, 동의서 보관 위치).
    """
    case_id: str
    source: str
    license: str
    collected_at: str
    consent: dict[str, bool]
    retention_days: int
    subject_age_bucket: str
    region: str
    notes: str = ""
    # 평가셋 등 추가 라벨
    tags: tuple[str, ...] = field(default_factory=tuple)


# ─────────────────────────── 검증 ───────────────────────────

def validate_provenance(p: DataProvenance) -> list[str]:
    """단일 케이스의 §7.3.3 거버넌스 위반 사항을 모두 수집해 반환.

    위반 없으면 빈 리스트. 호출자는 회귀 진입 전 이 결과를 점검해
    하나라도 위반이 있으면 해당 케이스를 셋에서 배제한다.
    """
    violations: list[str] = []

    # 출처 검사
    if p.source in ILLICIT_SOURCES:
        violations.append(f"illicit_source:{p.source}")
    elif p.source not in LICIT_SOURCES:
        violations.append(f"unknown_source:{p.source}")

    # 동의 항목 누락 검사
    missing = [k for k in REQUIRED_CONSENT_FIELDS if k not in p.consent]
    if missing:
        violations.append(f"missing_consent_fields:{','.join(missing)}")
    # 필수 동의 항목 중 False 발견
    denied = [k for k in REQUIRED_CONSENT_FIELDS
              if k in p.consent and p.consent[k] is False]
    # synthetic_generated / public_domain은 동의 자체가 무의미하므로 면제
    if denied and p.source not in {"synthetic_generated", "public_domain_dataset"}:
        violations.append(f"denied_consent:{','.join(denied)}")

    # 보존기간 검사
    max_days = MAX_RETENTION_DAYS.get(p.source, 0)
    if p.retention_days <= 0:
        violations.append("retention_days_non_positive")
    elif max_days and p.retention_days > max_days:
        violations.append(
            f"retention_exceeds_max:{p.retention_days}>{max_days}"
        )

    # 미성년자 차단
    age = (p.subject_age_bucket or "").strip().lower()
    if age in ("minor", "teen", "<18", "child", "kid"):
        violations.append(f"minor_subject:{age}")

    # 수집일 형식
    try:
        datetime.strptime(p.collected_at, "%Y-%m-%d")
    except ValueError:
        violations.append(f"invalid_collected_at:{p.collected_at}")

    # 라이선스 — 공란 금지
    if not (p.license or "").strip():
        violations.append("missing_license")

    return violations


def is_eligible_for_regression(p: DataProvenance) -> bool:
    """회귀 셋에 포함해도 되는지 — 위반 없고 보존기간 잔존 시 True."""
    if validate_provenance(p):
        return False
    return not is_expired(p)


# ─────────────────────────── 보존기간 ───────────────────────────

def is_expired(p: DataProvenance, *, today: date | None = None) -> bool:
    """수집일+보존기간을 오늘과 비교해 만료 여부 반환."""
    today = today or date.today()
    try:
        collected = datetime.strptime(p.collected_at, "%Y-%m-%d").date()
    except ValueError:
        return True  # 잘못된 형식은 만료 취급 (보수적)
    expiry = collected + timedelta(days=p.retention_days)
    return today > expiry


def days_until_expiry(p: DataProvenance, *, today: date | None = None) -> int:
    """만료까지 남은 일수. 이미 만료면 음수."""
    today = today or date.today()
    try:
        collected = datetime.strptime(p.collected_at, "%Y-%m-%d").date()
    except ValueError:
        return -1
    expiry = collected + timedelta(days=p.retention_days)
    return (expiry - today).days


# ─────────────────────────── 셋 단위 거버넌스 보고서 ───────────────────────────

def audit_dataset(items: list[DataProvenance]) -> dict[str, Any]:
    """골든 셋·평가셋의 거버넌스 일괄 감사.

    Returns:
        {
            "total": N,
            "eligible": M,                       # 회귀 가능
            "violations_by_case": {case_id: [...]},
            "expiring_soon": [case_id, ...],     # 30일 내 만료
            "source_distribution": {source: count},
            "region_distribution": {region: count},
        }
    """
    eligible = 0
    violations_by_case: dict[str, list[str]] = {}
    expiring_soon: list[str] = []
    sources: dict[str, int] = {}
    regions: dict[str, int] = {}

    for p in items:
        sources[p.source] = sources.get(p.source, 0) + 1
        regions[p.region] = regions.get(p.region, 0) + 1
        v = validate_provenance(p)
        if v:
            violations_by_case[p.case_id] = v
        if is_eligible_for_regression(p):
            eligible += 1
        days = days_until_expiry(p)
        if 0 <= days <= 30:
            expiring_soon.append(p.case_id)

    return {
        "total": len(items),
        "eligible": eligible,
        "violations_by_case": violations_by_case,
        "expiring_soon": expiring_soon,
        "source_distribution": sources,
        "region_distribution": regions,
    }
