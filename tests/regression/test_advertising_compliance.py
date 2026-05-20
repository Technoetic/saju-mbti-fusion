"""ADR-061 회귀 — 표시광고법 정확도 키워드 검사 검증."""

from engine.safety.gdpr.advertising_compliance import (
    check_advertising_copy,
    is_compliant,
    format_violations_report,
)


def test_clean_copy_passes():
    """위반 없는 카피는 통과."""
    text = "월하몽 사주는 전통 명리학에 기반한 풀이를 제공합니다."
    assert check_advertising_copy(text) == []
    assert is_compliant(text)


def test_accuracy_percentage_blocked():
    """정확도 X% 명시 — 즉시 REJECT."""
    text = "본 시스템은 정확도 95% 사주 풀이를 제공합니다."
    violations = check_advertising_copy(text)
    assert len(violations) >= 1
    assert any(v.severity == "REJECT" for v in violations)
    assert not is_compliant(text)


def test_100_percent_guarantee_blocked():
    """100% 단정 — REJECT."""
    text = "100% 적중하는 운세!"
    violations = check_advertising_copy(text)
    assert any(v.severity == "REJECT" for v in violations)


def test_scientific_proof_claim_blocked():
    """과학적 증명 단정 — REJECT."""
    text = "본 분석은 과학적으로 증명된 방법입니다."
    violations = check_advertising_copy(text)
    assert any(v.severity == "REJECT" for v in violations)


def test_medical_claim_blocked_adr006():
    """의료 효과 단정 — REJECT (ADR-006 강화)."""
    text = "본 풀이는 우울 치료에 효과적입니다."
    violations = check_advertising_copy(text)
    assert any(v.severity == "REJECT" for v in violations)


def test_warn_pattern_passes_compliance():
    """WARN 패턴은 위반 보고하나 is_compliant True (사용자 검토)."""
    text = "가장 정확한 사주 풀이"
    violations = check_advertising_copy(text)
    assert len(violations) >= 1
    assert all(v.severity == "WARN" for v in violations)
    assert is_compliant(text)  # WARN만 있으면 통과


def test_legal_basis_documented():
    """위반 발견 시 법령 근거 명시 의무."""
    text = "정확도 100%"
    violations = check_advertising_copy(text)
    for v in violations:
        assert "표시광고법" in v.legal_basis


def test_format_report_human_readable():
    """포맷 보고서가 한국어 + 변호사 검토 권고 포함."""
    text = "100% 정확한 사주"
    violations = check_advertising_copy(text)
    report = format_violations_report(violations)
    assert "위반" in report
    assert "변호사" in report  # ADR-006 정합


def test_format_report_clean_text():
    """위반 없을 때도 변호사 검토 권고 명시."""
    text = "월하몽 사주"
    report = format_violations_report(check_advertising_copy(text))
    assert "위반 없음" in report
    assert "변호사" in report


def test_position_sorted():
    """여러 위반 발견 시 원문 위치 순 정렬."""
    text = "100% 적중! 그리고 정확도 95% 보장!"
    violations = check_advertising_copy(text)
    positions = [v.position for v in violations]
    assert positions == sorted(positions)
