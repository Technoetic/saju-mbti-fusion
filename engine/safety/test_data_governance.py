"""engine.safety.data_governance — §7.3.3 데이터 거버넌스 회귀 테스트."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _full_consent() -> dict[str, bool]:
    return {
        "processing": True,
        "storage": True,
        "training": True,
        "third_party_sharing": True,
    }


def _today_iso() -> str:
    return date.today().strftime("%Y-%m-%d")


def _mk(
    case_id: str = "GS-001",
    source: str = "consented_user_upload",
    license: str = "INTERNAL",
    collected_at: str | None = None,
    consent: dict[str, bool] | None = None,
    retention_days: int = 30,
    subject_age_bucket: str = "30s",
    region: str = "KR",
    notes: str = "",
    tags: tuple[str, ...] = (),
):
    from engine.safety.data_governance import DataProvenance
    return DataProvenance(
        case_id=case_id,
        source=source,
        license=license,
        collected_at=collected_at or _today_iso(),
        consent=consent or _full_consent(),
        retention_days=retention_days,
        subject_age_bucket=subject_age_bucket,
        region=region,
        notes=notes,
        tags=tags,
    )


# ─────────────────────────── 합법 출처 ───────────────────────────

def test_licit_source_full_consent_passes():
    from engine.safety.data_governance import validate_provenance
    assert validate_provenance(_mk()) == []


def test_illicit_source_blocked():
    from engine.safety.data_governance import validate_provenance
    v = validate_provenance(_mk(source="social_media_scraping"))
    assert any("illicit_source" in x for x in v)


def test_unknown_source_blocked():
    from engine.safety.data_governance import validate_provenance
    v = validate_provenance(_mk(source="random_string"))
    assert any("unknown_source" in x for x in v)


# ─────────────────────────── 동의 ───────────────────────────

def test_missing_consent_fields_detected():
    from engine.safety.data_governance import validate_provenance
    v = validate_provenance(_mk(consent={"processing": True}))  # 3개 누락
    assert any("missing_consent_fields" in x for x in v)


def test_denied_consent_detected():
    from engine.safety.data_governance import validate_provenance
    bad = _full_consent()
    bad["training"] = False
    v = validate_provenance(_mk(consent=bad))
    assert any("denied_consent" in x for x in v)


def test_synthetic_data_consent_exempt():
    """합성 얼굴은 동의 불필요 — denied_consent 검출되어도 안 됨."""
    from engine.safety.data_governance import validate_provenance
    bad = _full_consent()
    bad["training"] = False
    v = validate_provenance(_mk(source="synthetic_generated", consent=bad))
    assert not any("denied_consent" in x for x in v)


def test_public_domain_consent_exempt():
    from engine.safety.data_governance import validate_provenance
    bad = _full_consent()
    bad["storage"] = False
    v = validate_provenance(_mk(source="public_domain_dataset", consent=bad))
    assert not any("denied_consent" in x for x in v)


# ─────────────────────────── 보존기간 ───────────────────────────

def test_retention_days_non_positive_blocked():
    from engine.safety.data_governance import validate_provenance
    v = validate_provenance(_mk(retention_days=0))
    assert "retention_days_non_positive" in v


def test_retention_exceeds_max_blocked():
    """consented_user_upload는 90일 한도."""
    from engine.safety.data_governance import validate_provenance
    v = validate_provenance(_mk(retention_days=91))
    assert any("retention_exceeds_max" in x for x in v)


def test_synthetic_long_retention_allowed():
    """합성은 사실상 무기한 허용."""
    from engine.safety.data_governance import validate_provenance
    v = validate_provenance(_mk(source="synthetic_generated", retention_days=10000))
    assert not any("retention_exceeds_max" in x for x in v)


# ─────────────────────────── 미성년자 ───────────────────────────

def test_minor_subject_blocked():
    from engine.safety.data_governance import validate_provenance
    for age in ("minor", "teen", "<18", "child"):
        v = validate_provenance(_mk(subject_age_bucket=age))
        assert any("minor_subject" in x for x in v), f"{age} 차단 실패"


def test_adult_age_bucket_passes():
    from engine.safety.data_governance import validate_provenance
    for age in ("20s", "30s", "40s", "60s+"):
        v = validate_provenance(_mk(subject_age_bucket=age))
        assert not any("minor_subject" in x for x in v)


# ─────────────────────────── 날짜·라이선스 ───────────────────────────

def test_invalid_collected_at_format_blocked():
    from engine.safety.data_governance import validate_provenance
    v = validate_provenance(_mk(collected_at="2026/05/15"))  # 슬래시 형식
    assert any("invalid_collected_at" in x for x in v)


def test_missing_license_blocked():
    from engine.safety.data_governance import validate_provenance
    v = validate_provenance(_mk(license=""))
    assert "missing_license" in v


# ─────────────────────────── 만료 ───────────────────────────

def test_is_expired_future_returns_false():
    from engine.safety.data_governance import is_expired
    p = _mk(retention_days=30, collected_at=_today_iso())
    assert is_expired(p) is False


def test_is_expired_past_returns_true():
    from engine.safety.data_governance import is_expired
    past = (date.today() - timedelta(days=100)).strftime("%Y-%m-%d")
    p = _mk(retention_days=30, collected_at=past)
    assert is_expired(p) is True


def test_days_until_expiry_positive_for_future():
    from engine.safety.data_governance import days_until_expiry
    p = _mk(retention_days=30, collected_at=_today_iso())
    assert days_until_expiry(p) >= 29  # 약간의 경계 오차 허용


def test_days_until_expiry_negative_for_past():
    from engine.safety.data_governance import days_until_expiry
    past = (date.today() - timedelta(days=100)).strftime("%Y-%m-%d")
    p = _mk(retention_days=30, collected_at=past)
    assert days_until_expiry(p) < 0


def test_is_eligible_for_regression_requires_no_violation_and_not_expired():
    from engine.safety.data_governance import is_eligible_for_regression
    # 정상 케이스
    assert is_eligible_for_regression(_mk()) is True
    # 위반 있으면 부적격
    assert is_eligible_for_regression(_mk(source="leaked_dataset")) is False
    # 만료되었으면 부적격
    past = (date.today() - timedelta(days=200)).strftime("%Y-%m-%d")
    assert is_eligible_for_regression(_mk(retention_days=30, collected_at=past)) is False


# ─────────────────────────── 셋 감사 ───────────────────────────

def test_audit_dataset_aggregates():
    from engine.safety.data_governance import audit_dataset
    items = [
        _mk(case_id="GS-001", source="consented_user_upload", region="KR"),
        _mk(case_id="GS-002", source="consented_user_upload", region="KR"),
        _mk(case_id="GS-003", source="synthetic_generated", region="US-CA", retention_days=1000),
        _mk(case_id="GS-004", source="leaked_dataset", region="EU"),  # 위반
    ]
    r = audit_dataset(items)
    assert r["total"] == 4
    assert r["eligible"] == 3  # leaked 제외
    assert "GS-004" in r["violations_by_case"]
    assert r["source_distribution"]["consented_user_upload"] == 2
    assert r["region_distribution"]["KR"] == 2


def test_audit_dataset_detects_expiring_soon():
    """만료 30일 이내 케이스가 expiring_soon에 포함."""
    from engine.safety.data_governance import audit_dataset
    # 80일 전 수집 + 90일 보존 → 10일 후 만료
    soon = (date.today() - timedelta(days=80)).strftime("%Y-%m-%d")
    items = [
        _mk(case_id="GS-100", collected_at=soon, retention_days=90),
        _mk(case_id="GS-101"),  # 오늘 + 30일 → 30일 후 만료(경계)
    ]
    r = audit_dataset(items)
    assert "GS-100" in r["expiring_soon"]


def test_audit_dataset_empty():
    from engine.safety.data_governance import audit_dataset
    r = audit_dataset([])
    assert r["total"] == 0
    assert r["eligible"] == 0
    assert r["violations_by_case"] == {}


# ─────────────────────────── 상수 무결성 ───────────────────────────

def test_licit_and_illicit_sources_are_disjoint():
    from engine.safety.data_governance import LICIT_SOURCES, ILLICIT_SOURCES
    assert LICIT_SOURCES.isdisjoint(ILLICIT_SOURCES)


def test_required_consent_fields_count():
    from engine.safety.data_governance import REQUIRED_CONSENT_FIELDS
    assert len(REQUIRED_CONSENT_FIELDS) == 4
    assert "processing" in REQUIRED_CONSENT_FIELDS
    assert "third_party_sharing" in REQUIRED_CONSENT_FIELDS


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_data_governance():
    import engine.safety as safety
    assert hasattr(safety, "DataProvenance")
    assert hasattr(safety, "validate_provenance")
    assert hasattr(safety, "is_eligible_for_regression")
    assert hasattr(safety, "audit_dataset")
    assert hasattr(safety, "LICIT_SOURCES")
