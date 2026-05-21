"""ADR-125 본문화 회귀 — 작명학 한자 자원오행 보고서 §6 9 한자 KCI 매핑.

학술 근거: 이재승·김만태 KCI 학설 + 김기승 정통 작명학.
"""
from __future__ import annotations

from engine.divination.name.unihan import (
    kci_confidence,
    kci_reason,
    kci_school_source,
    preferred_ohaeng,
    resource_ohaeng_kci,
)


# 보고서 §6 라인 172~213 YAML 표본 — 9 한자 KCI 매핑
EXPECTED_9_HANJA = {
    "田": {"ohaeng": "토", "confidence": "MEDIUM"},
    "澈": {"ohaeng": "수", "confidence": "HIGH"},
    "鐵": {"ohaeng": "금", "confidence": "HIGH"},
    "綴": {"ohaeng": "목", "confidence": "LOW"},
    "標": {"ohaeng": "목", "confidence": "HIGH"},
    "飄": {"ohaeng": "목", "confidence": "LOW"},
    "詠": {"ohaeng": "화", "confidence": "LOW"},
    "心": {"ohaeng": "화", "confidence": "LOW"},
    "光": {"ohaeng": "화", "confidence": "HIGH"},
}


class TestKci9HanjaMapping:
    """보고서 §6 9 한자 KCI 매핑 본문화 회귀."""

    def test_all_9_hanja_kci_ohaeng(self):
        """9 한자 모두 KCI 자원오행 매핑 영속화."""
        for char, expected in EXPECTED_9_HANJA.items():
            actual = resource_ohaeng_kci(char)
            assert actual == expected["ohaeng"], (
                f"{char}: 기대 {expected['ohaeng']}, 실제 {actual}"
            )

    def test_all_9_hanja_kci_confidence(self):
        """9 한자 모두 신뢰도 단계 명시."""
        for char, expected in EXPECTED_9_HANJA.items():
            actual = kci_confidence(char)
            assert actual == expected["confidence"], (
                f"{char}: 기대 신뢰도 {expected['confidence']}, 실제 {actual}"
            )

    def test_all_9_hanja_kci_reason(self):
        """9 한자 모두 자원·본의 형태론 추적 사유 명시 (ADR-010)."""
        for char in EXPECTED_9_HANJA.keys():
            reason = kci_reason(char)
            assert reason is not None, f"{char}: kci_reason 부재"
            assert len(reason) > 10, f"{char}: kci_reason 너무 짧음: {reason}"

    def test_all_9_hanja_kci_school_source(self):
        """9 한자 모두 학파 출처 명시 (ADR-010)."""
        for char in EXPECTED_9_HANJA.keys():
            source = kci_school_source(char)
            assert source is not None, f"{char}: kci_school_source 부재"
            # 학파 명칭 1+ 포함
            assert any(
                school in source
                for school in ["이재승", "김기승", "김만태", "한국학중앙연구원", "AKS"]
            ), f"{char}: 정통 학파 출처 미명시: {source}"

    def test_preferred_ohaeng_uses_kci(self):
        """preferred_ohaeng는 KCI 매핑 우선 사용 (옵션 C)."""
        # 田: radical_auto = None, kci = 토 → preferred = 토
        assert preferred_ohaeng("田") == "토"
        # 綴: radical_auto = None, kci = 목 → preferred = 목
        assert preferred_ohaeng("綴") == "목"
        # 鐵: radical_auto = 금, kci = 금 → preferred = 금 (일치)
        assert preferred_ohaeng("鐵") == "금"


class TestKci9HanjaDeterministic:
    """결정론 보장."""

    def test_deterministic_same_input(self):
        """동일 입력 동일 출력."""
        for char in EXPECTED_9_HANJA.keys():
            r1 = resource_ohaeng_kci(char)
            r2 = resource_ohaeng_kci(char)
            assert r1 == r2

    def test_invalid_input_returns_none(self):
        """잘못된 입력 None 반환."""
        assert resource_ohaeng_kci("") is None
        assert resource_ohaeng_kci("미수록한자") is None
        assert kci_confidence("") is None

    def test_low_confidence_hanja_warning(self):
        """LOW 신뢰도 한자는 사용자 출력에서 경고 의무."""
        low_hanja = [c for c, e in EXPECTED_9_HANJA.items() if e["confidence"] == "LOW"]
        # 綴·飄·詠·心 4건
        assert len(low_hanja) == 4
        for char in low_hanja:
            # 신뢰도 LOW + kci_reason에 학파 분기 또는 신중 키워드 포함
            reason = kci_reason(char) or ""
            assert any(
                kw in reason
                for kw in ["분기", "신중", "혼용", "분쟁", "주의", "이견", "충돌", "사용 주의"]
            ), f"{char} LOW 신뢰도 — kci_reason에 분기/신중 표시 부재: {reason}"
