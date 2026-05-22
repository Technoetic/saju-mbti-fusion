"""ADR-147 회귀 — /domain-priorities Stale 4건 영속 보장.

Stale 정정의 코드 정합 상태를 회귀로 영구 보장. 사일런트 회귀 차단.

대상:
  · #7 palm Vision Opus 4.7 — ADR-143으로 이미 영속 (test_vision_opus47_policy.py)
  · #8 name 발음오행 학파 분기 — ADR-129로 이미 영속 (test_name_baleum_unhae_option.py)
  · #9 hwapae KCI 인용 — 본 ADR로 신규 영속 (HWAPAE_KCI_CITATIONS 상수)
  · #10 star 분 단위 트랜짓 — 본 ADR로 신규 영속 (datetime 정밀 검증)
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from engine.divination.hwapae.korean import HWAPAE_KCI_CITATIONS
from engine.divination.star.astronomy import compute_planet_position


class TestHwapaeKciCitationsPersistence:
    """#9 hwapae KCI 인용 영속 보장."""

    def test_at_least_three_kci_citations(self):
        """KCI 인용 최소 3건 영속 (모듈 주석 line 86-88 → 코드 상수)."""
        assert len(HWAPAE_KCI_CITATIONS) >= 3

    def test_2013_kwon_signifier_present(self):
        """권현주 (2013) 시니피에 분석 KCI FI001859666 영속."""
        match = [c for c in HWAPAE_KCI_CITATIONS if c.kci_id == "FI001859666"]
        assert len(match) == 1
        c = match[0]
        assert "2013" in c.authors_ko
        assert "권현주" in c.authors_ko
        assert "시니피에" in c.title_ko or "signifier" in c.title_ko.lower()

    def test_2017_kwon_remediation_present(self):
        """권현주 (2017) 재매개 분석 KCI FI002241673 영속."""
        match = [c for c in HWAPAE_KCI_CITATIONS if c.kci_id == "FI002241673"]
        assert len(match) == 1
        assert "재매개" in match[0].title_ko

    def test_2022_sogang_present(self):
        """서강대 (2022) 화투 변천 KCI FI002874136 영속."""
        match = [c for c in HWAPAE_KCI_CITATIONS if c.kci_id == "FI002874136"]
        assert len(match) == 1
        assert "서강" in match[0].authors_ko

    def test_all_have_kci_id_format(self):
        """모든 인용이 KCI 식별번호 형식 (FI*) 보장."""
        for c in HWAPAE_KCI_CITATIONS:
            assert c.kci_id.startswith("FI"), f"{c.kci_id}: KCI 식별번호 형식 위반"
            assert len(c.kci_id) >= 10, f"{c.kci_id}: 너무 짧음"

    def test_all_have_topic_focus(self):
        """모든 인용에 활용 영역 명시."""
        for c in HWAPAE_KCI_CITATIONS:
            assert c.topic_focus and len(c.topic_focus) >= 5


class TestStarMinutePrecisionPersistence:
    """#10 star 분 단위 트랜짓 영속 보장."""

    def test_30_minute_difference_reflected(self):
        """30분 차이가 행성 황경에 반영됨 (분 단위 미지원 시 동일값)."""
        dt1 = datetime(2026, 5, 23, 10, 0, 0, tzinfo=timezone.utc)
        dt2 = datetime(2026, 5, 23, 10, 30, 0, tzinfo=timezone.utc)
        r1 = compute_planet_position("moon", dt1)
        r2 = compute_planet_position("moon", dt2)
        assert r1 is not None and r2 is not None
        assert r1.ecliptic_longitude_deg != r2.ecliptic_longitude_deg, (
            "30분 차이 미반영 — 일 단위만 지원되는 stale 회귀 위험"
        )

    def test_second_precision_reflected(self):
        """초 단위 차이도 반영됨 (분 단위 정밀의 상한 보장)."""
        dt1 = datetime(2026, 5, 23, 10, 30, 0, tzinfo=timezone.utc)
        dt2 = datetime(2026, 5, 23, 10, 30, 45, tzinfo=timezone.utc)
        r1 = compute_planet_position("moon", dt1)
        r2 = compute_planet_position("moon", dt2)
        assert r1 is not None and r2 is not None
        assert r1.ecliptic_longitude_deg != r2.ecliptic_longitude_deg

    def test_moon_moves_within_expected_range(self):
        """달 30분 이동은 약 0.27도 (1시간 ~0.5도) — 천체역학 정합."""
        dt1 = datetime(2026, 5, 23, 10, 0, 0, tzinfo=timezone.utc)
        dt2 = datetime(2026, 5, 23, 10, 30, 0, tzinfo=timezone.utc)
        r1 = compute_planet_position("moon", dt1)
        r2 = compute_planet_position("moon", dt2)
        assert r1 is not None and r2 is not None
        diff = abs(r2.ecliptic_longitude_deg - r1.ecliptic_longitude_deg)
        # 달 평균 이동 속도: 13°/일 = 0.27°/30분
        assert 0.1 < diff < 0.5, (
            f"달 30분 이동 {diff}° (예상 0.27°) — 천체역학 부정합"
        )

    def test_sun_one_hour_difference(self):
        """태양 1시간 차이도 정밀 반영 (태양 ~0.04°/시간)."""
        dt1 = datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc)
        dt2 = datetime(2026, 5, 23, 13, 0, 0, tzinfo=timezone.utc)
        r1 = compute_planet_position("sun", dt1)
        r2 = compute_planet_position("sun", dt2)
        assert r1 is not None and r2 is not None
        assert r1.ecliptic_longitude_deg != r2.ecliptic_longitude_deg


class TestStalePersistenceMetaAssertion:
    """ADR-147 종합 — Stale 4건 회귀 영속 체인 검증."""

    @pytest.mark.parametrize("module_name,test_path", [
        ("#7 palm Vision Opus 4.7", "tests/regression/test_vision_opus47_policy.py"),
        ("#8 name 발음오행 학파 분기", "tests/regression/test_name_baleum_unhae_option.py"),
        ("#9 hwapae KCI 인용", "tests/regression/test_stale_persistence.py"),  # 본 파일
        ("#10 star 분 단위", "tests/regression/test_stale_persistence.py"),  # 본 파일
    ])
    def test_regression_file_exists(self, module_name, test_path):
        """4개 Stale 영속 회귀 파일 존재 보장."""
        from pathlib import Path
        path = Path(test_path)
        assert path.exists(), (
            f"{module_name}: 영속 회귀 파일 누락 {test_path}"
        )
