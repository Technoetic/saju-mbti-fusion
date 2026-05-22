"""ADR-094 supplement 회귀 — dream 시스템 프롬프트의 '길몽/흉몽' 학파 컨텍스트 화이트리스트.

기존 회귀 (test_dream_directive_strengthening · test_dream_system_prompt_strengthening)는
'길몽'·'흉몽' 등 단정 어휘가 시스템 프롬프트에 "차단 명시 의무"로 박혀 있는지 검증.

본 회귀는 그 차단을 너무 엄격히 해석한 LLM이 학파 분류 라벨 인용까지
못 하는 사례를 방지 — /domain-priorities #3 (49점) 결손 해소.

화이트리스트 룰:
  ✅ "한국민간에서는 길의 결로 분류됩니다" — 학파 명시 + 흐름 톤
  ❌ "이 꿈은 길몽입니다" — 운명 단정

회귀 검증: 시스템 프롬프트에 학파 컨텍스트 허용 룰이 박혀 있는지.
"""
from __future__ import annotations

from engine.divination.dream import DREAM_SYSTEM


class TestSchoolContextWhitelist:
    """학파 분류 컨텍스트 화이트리스트 룰 박힘."""

    def test_supplement_marker_present(self):
        """ADR-094 supplement 마커 박힘 (화이트리스트 룰 시작 신호)."""
        assert "ADR-094 supplement" in DREAM_SYSTEM, (
            "ADR-094 supplement 마커 누락 — 화이트리스트 룰 부재 의미"
        )

    def test_school_context_allowance_explicit(self):
        """학파 컨텍스트 허용 명시 — '학파 분류 컨텍스트 허용' 키워드."""
        assert "학파 분류 컨텍스트 허용" in DREAM_SYSTEM, (
            "학파 컨텍스트 허용 명시 누락 — LLM이 과보수적으로 차단할 위험"
        )

    def test_school_name_obligation(self):
        """길몽/흉몽 사용 시 학파 이름 동반 의무 명시."""
        # 룰: '학파 이름과 함께' 패턴
        assert "학파 이름과 함께" in DREAM_SYSTEM, (
            "학파 이름 동반 의무 룰 누락"
        )

    def test_school_example_korean_folk(self):
        """학파 예시 — 한국민간 인용 형식 명시."""
        assert "한국민간에서는" in DREAM_SYSTEM, (
            "한국민간 학파 예시 누락 — LLM 학습 지표"
        )
        assert "길의 결" in DREAM_SYSTEM or "길의 결로 분류" in DREAM_SYSTEM, (
            "흐름 톤 예시 ('길의 결') 누락"
        )

    def test_school_example_jugong(self):
        """학파 예시 — 주공해몽 인용 형식 명시."""
        assert "주공해몽" in DREAM_SYSTEM, (
            "주공해몽 학파 예시 누락"
        )

    def test_assertion_form_explicitly_banned(self):
        """단정형 '이 꿈은 길몽입니다' 명시 금지."""
        assert "이 꿈은 길몽입니다" in DREAM_SYSTEM, (
            "단정형 금지 예시 명시 누락 — LLM 학습 지표"
        )
        # 절대 X 또는 단정 회피 명시
        assert "절대 X" in DREAM_SYSTEM or "단정형 금지" in DREAM_SYSTEM


class TestExistingRulesPreserved:
    """기존 절대 금지 어휘 룰 보존 (무회귀)."""

    def test_absolute_banned_words_still_present(self):
        """반드시·확실히·대길·대흉은 여전히 절대 금지."""
        # 본 supplement 후에도 절대 금지 어휘는 유지
        for word in ["반드시", "확실히", "대길", "대흉"]:
            assert word in DREAM_SYSTEM, (
                f"절대 금지 어휘 '{word}' 누락 — supplement가 기존 룰 깨뜨림"
            )

    def test_adr_094_marker_still_present(self):
        """ADR-094 단정 차단 룰 마커 보존."""
        assert "ADR-094 단정 차단" in DREAM_SYSTEM

    def test_polarity_label_disclaimer_present(self):
        """polarity 라벨 단정 X 명시 유지."""
        assert "polarity" in DREAM_SYSTEM
        assert "운명 단정 X" in DREAM_SYSTEM
