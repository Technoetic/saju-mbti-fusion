"""ADR-150 회귀 — 외부 결단 2건 (#20·#22) 결단 지원 자료 영속 메타 보장.

본 AI가 결단 자체는 불가하나 결단 지원 자료는 영속 가능.
회귀로 자료 영속 파일 존재 + ADR 마커 + 핵심 키워드 보장.

대상:
  · #20 palm ML 학습 데이터셋 후보 매트릭스 + 사용자 결단 가이드
  · #22 hwapae 사업 차별화 매트릭스 + 마케팅 메시지 5종
"""
from __future__ import annotations

from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent / "vault"
ADR_FILE = VAULT_ROOT / "decisions" / "ADR-150-external-decisions-support-brief.md"
BRIEF_FILE = VAULT_ROOT / "reports" / "external-decisions-brief-2026-05-23.md"


class TestADR150FileExists:
    """ADR-150 영속 파일 존재 메타 보장."""

    def test_adr_file_exists(self):
        assert ADR_FILE.exists(), f"ADR-150 파일 누락: {ADR_FILE}"

    def test_brief_file_exists(self):
        assert BRIEF_FILE.exists(), f"외부 결단 안내 파일 누락: {BRIEF_FILE}"


class TestADR150PalmDatasetContent:
    """#20 palm ML 데이터셋 결단 자료 영속 (vault 무시 — 본 AI 메타만 검증)."""

    def test_palm_dataset_candidates_present(self):
        """팔름 데이터셋 후보 매트릭스 영속 (#20)."""
        src = ADR_FILE.read_text(encoding="utf-8")
        # 11k Hands 핵심 후보 명시 (학술 fair use)
        assert "11k Hands" in src
        assert "11,076" in src or "11076" in src
        assert "fair use" in src.lower() or "학술" in src

    def test_palm_brief_includes_url(self):
        """안내 보고서에 11k Hands 공식 URL 명시."""
        src = BRIEF_FILE.read_text(encoding="utf-8")
        assert "https://sites.google.com/view/11khands" in src

    def test_palm_kaggle_alternatives_present(self):
        """Kaggle 대안 데이터셋 후보 명시."""
        src = ADR_FILE.read_text(encoding="utf-8")
        assert "Kaggle" in src


class TestADR150HwapaeMarketingContent:
    """#22 hwapae 마케팅 자료 영속."""

    def test_differentiation_matrix_present(self):
        """한국 화투 vs 일본 하나후다 차별화 매트릭스 5축 영속."""
        src = ADR_FILE.read_text(encoding="utf-8")
        # 5 차원 모두 명시
        for dim in ["재질", "색상", "체계", "현지화", "콘텐츠"]:
            assert dim in src, f"차별화 차원 '{dim}' 누락"

    def test_marketing_messages_5_present(self):
        """마케팅 메시지 5종 후보 영속."""
        src = ADR_FILE.read_text(encoding="utf-8")
        # 5 메시지 마커 (**1.**, **2.** 등)
        for i in ["1.", "2.", "3.", "4.", "5."]:
            assert f"**{i}" in src, f"메시지 #{i} 마커 누락"

    def test_korean_independence_message(self):
        """1950년대 한국 정착 학파 메시지 영속 (정통성 핵심)."""
        src = ADR_FILE.read_text(encoding="utf-8")
        assert "1950년대" in src
        assert "광·끗·피·띠" in src or "광끗피띠" in src

    def test_kci_citations_referenced(self):
        """ADR-147에서 영속한 KCI 인용 3건 참조 (정합)."""
        src = ADR_FILE.read_text(encoding="utf-8")
        assert "권현주 2013" in src or "권현주" in src
        # 서강대 인용도
        assert "서강대" in src


class TestADR150SafetyCompliance:
    """ADR-006 자문 거절 + ADR-010 사실성 분리 정합."""

    def test_no_assertion_words_in_marketing_messages(self):
        """마케팅 메시지 5종 본문에 단정 어휘 0건.

        ADR-094 단정 부사 (반드시·확실히·100%·절대) 만 검사.
        ADR-006 회피 컨텍스트 표현 (예: "사망 단정 X")은 정합 영역으로 허용.
        """
        src = ADR_FILE.read_text(encoding="utf-8")
        message_lines = [ln for ln in src.split("\n") if ln.strip().startswith(">")]
        message_text = "\n".join(message_lines)
        # 단정 부사만 검사 (절대 어휘 — 사용 시 회피 컨텍스트도 불가)
        forbidden = ["반드시", "확실히", "100%", "절대"]
        for w in forbidden:
            assert w not in message_text, (
                f"마케팅 메시지에 단정 부사 '{w}' 검출 — ADR-094 위반"
            )

    def test_disclaimer_present(self):
        """면책 명시 (본 ADR 메모 자체)."""
        src = ADR_FILE.read_text(encoding="utf-8")
        assert "참고용" in src
        assert "의료·법률·금융" in src or "단독 근거" in src

    def test_adr_006_marker_present(self):
        """ADR-006 자문 거절 마커 영속."""
        src = ADR_FILE.read_text(encoding="utf-8")
        assert "ADR-006" in src
