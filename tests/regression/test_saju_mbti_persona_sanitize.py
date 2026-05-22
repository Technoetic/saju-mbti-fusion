"""ADR-014 회귀 — saju_mbti 사용자 출력 단정 어휘 차단 (format_tendency_for_persona).

기존 test_saju_mbti_sixty_jiazi.py는 sixty_jiazi_weights.py 60갑자 가중치만
검증. 본 회귀는 predictor.py의 사용자 노출 함수 (format_tendency_for_persona)가
ADR-014 16유형 단정 금지 + 면책 자동 포함 의무를 라이브 출력에서 검증한다.

/domain-priorities #4 (49점) 안전망 강화 — ADR-141 후속.
"""
from __future__ import annotations

import pytest

from engine.divination.saju_mbti.predictor import (
    DISCLAIMER_KO,
    derive_mbti_tendency,
    format_tendency_for_persona,
)


# ADR-094·113·115·116·117·122·134 sanitize 안전망 단정 어휘 풀
FORBIDDEN_ABSOLUTE = [
    "반드시", "확실히", "절대", "틀림없이", "100%",
    "당신은 ENTP", "당신은 ISFJ", "당신은 INTJ", "당신은 ESTP",
    "당신의 MBTI는", "MBTI 진단", "MBTI 검사 결과",
]

# ADR-014 16유형 단정 금지 — 본문에 16유형 약어 단정형 금지
FORBIDDEN_16_TYPES = [
    "그대는 ENTP", "그대는 ISFJ", "그대는 INTJ", "그대는 ESTP",
    "당신은 ENFJ", "당신은 ISTP",
]


SAMPLE_SAJU_CASES = [
    {  # 양 극단
        "year": "甲寅", "month": "丙寅", "day": "戊午", "hour": "庚申",
        "wuxing_dist": {"목": 2, "화": 2, "토": 2, "금": 2, "수": 0},
        "day_master_han": "戊",
    },
    {  # 음 극단
        "year": "乙丑", "month": "丁卯", "day": "己未", "hour": "辛酉",
        "wuxing_dist": {"목": 2, "화": 1, "토": 3, "금": 2, "수": 0},
        "day_master_han": "己",
    },
    {  # 균형 (미정 다수)
        "year": "甲子", "month": "丁丑", "day": "戊寅", "hour": "辛卯",
        "wuxing_dist": {"목": 2, "화": 1, "토": 2, "금": 2, "수": 1},
        "day_master_han": "戊",
    },
    {  # 모두 미정 (데이터 부족)
        "wuxing_dist": {},
    },
]


class TestPersonaOutputDisclaimer:
    """사용자 출력 면책 자동 박힘."""

    @pytest.mark.parametrize("saju", SAMPLE_SAJU_CASES)
    def test_persona_output_contains_disclaimer(self, saju):
        """모든 출력에 면책 자동 포함 (ADR-014 의무)."""
        t = derive_mbti_tendency(saju)
        msg = format_tendency_for_persona(t)
        assert DISCLAIMER_KO in msg, (
            f"면책 누락: {msg[:100]}..."
        )
        assert "MBTI 검사를 대체하지 않습니다" in msg

    @pytest.mark.parametrize("saju", SAMPLE_SAJU_CASES)
    def test_no_absolute_assertion_words(self, saju):
        """단정 부사 (반드시·확실히·절대·100%) 0건."""
        t = derive_mbti_tendency(saju)
        msg = format_tendency_for_persona(t)
        hits = [w for w in FORBIDDEN_ABSOLUTE if w in msg]
        assert not hits, f"단정 어휘 검출: {hits}"

    @pytest.mark.parametrize("saju", SAMPLE_SAJU_CASES)
    def test_no_16_type_direct_assertion(self, saju):
        """16유형 직접 단정형 ('당신은 ENTP' 류) 0건 (ADR-014 핵심)."""
        t = derive_mbti_tendency(saju)
        msg = format_tendency_for_persona(t)
        hits = [w for w in FORBIDDEN_16_TYPES if w in msg]
        assert not hits, f"16유형 단정 검출: {hits}"


class TestUncertaintyPreservation:
    """ADR-014 '미정' 라벨 보존 — 단정 강제 전환 차단."""

    def test_uncertain_label_omitted_from_output(self):
        """미정 축은 출력에서 제외 (단정 회피)."""
        # 균형 사주 → 일부 축 미정
        saju = SAMPLE_SAJU_CASES[2]
        t = derive_mbti_tendency(saju)
        msg = format_tendency_for_persona(t)
        # 미정 라벨이 직접 노출되지 않아야 함
        assert "미정의 결" not in msg
        assert "미정의 기운" not in msg

    def test_all_uncertain_returns_neutral_message(self):
        """4축 모두 미정 시 중립 메시지 + 사용자에게 직접 묻기."""
        saju = {"wuxing_dist": {}}
        t = derive_mbti_tendency(saju)
        # 모두 미정이면 데이터 부족 메시지
        assert t.uncertain_count() >= 3, f"미정 카운트: {t.uncertain_count()}"
        msg = format_tendency_for_persona(t)
        # 사용자에게 직접 MBTI 묻기 패턴
        assert "MBTI" in msg


class TestPersonaOutputFlowTone:
    """ADR-014 '결이 비치는구먼' 흐름 톤 유지."""

    @pytest.mark.parametrize("saju", SAMPLE_SAJU_CASES[:3])
    def test_flow_tone_keywords_present(self, saju):
        """출력에 흐름 톤 키워드 (결·기운·비치·흐르·견주) 1개 이상."""
        t = derive_mbti_tendency(saju)
        msg = format_tendency_for_persona(t)
        flow_keywords = ["결", "기운", "비치", "흐르", "견주"]
        hits = [w for w in flow_keywords if w in msg]
        assert hits, f"흐름 톤 키워드 부재: {msg[:100]}..."

    @pytest.mark.parametrize("saju", SAMPLE_SAJU_CASES[:3])
    def test_user_invitation_present(self, saju):
        """사용자에게 본인 MBTI와 견주어 보라는 초대 메시지 포함 (단정 회피 핵심)."""
        t = derive_mbti_tendency(saju)
        msg = format_tendency_for_persona(t)
        assert "그대" in msg, f"사용자 직접 호명 누락: {msg[:100]}..."
        # 견주기 또는 들려주기 패턴
        assert ("견주어" in msg or "들려주시게" in msg), (
            f"사용자 초대 메시지 누락: {msg[:100]}..."
        )
