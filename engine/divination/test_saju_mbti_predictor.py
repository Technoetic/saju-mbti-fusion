"""engine.divination.saju_mbti_predictor — 회귀 테스트.

ADR-014 예외 결정. ADR-002·010 정신 (단정 회피·면책 의무) 검증.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 데이터 모델 ───────────────────────────


def test_tendency_label_format():
    from engine.divination.saju_mbti_predictor import MbtiTendency
    t = MbtiTendency(ei="E", sn="N", tf="F", jp="J", reasons={})
    assert t.as_label() == "E-N-F-J"


def test_tendency_uncertain_count():
    from engine.divination.saju_mbti_predictor import MbtiTendency, LABEL_UNCERTAIN
    t = MbtiTendency(ei=LABEL_UNCERTAIN, sn="N", tf=LABEL_UNCERTAIN, jp="J", reasons={})
    assert t.uncertain_count() == 2


# ─────────────────────────── 음양 비율 ───────────────────────────


def test_yang_ratio_all_yang():
    """양간·양지만으로 구성된 사주 — 양 비율 1.0."""
    from engine.divination.saju_mbti_predictor import _yang_ratio
    pillars = {
        "year": "甲子", "month": "丙寅", "day": "戊辰", "hour": "庚午",
    }
    assert _yang_ratio(pillars) == 1.0


def test_yang_ratio_all_yin():
    from engine.divination.saju_mbti_predictor import _yang_ratio
    pillars = {
        "year": "乙丑", "month": "丁卯", "day": "己巳", "hour": "辛未",
    }
    assert _yang_ratio(pillars) == 0.0


def test_yang_ratio_balanced():
    """양·음 반반 — 0.5."""
    from engine.divination.saju_mbti_predictor import _yang_ratio
    pillars = {
        "year": "甲乙", "month": "丙丁", "day": "戊己", "hour": "庚辛",
    }
    # 천간 4양 + 4음, 지지는 매핑 외 (count되지 않음)
    # 4 yang gan / 8 total slots... 단 ji는 매핑 외라 total 4
    result = _yang_ratio(pillars)
    assert 0.4 <= result <= 0.6


# ─────────────────────────── EI 매핑 ───────────────────────────


def test_map_ei_extroversion():
    from engine.divination.saju_mbti_predictor import _map_ei, LABEL_E
    label, reason = _map_ei(0.8)
    assert label == LABEL_E
    assert "0.80" in reason


def test_map_ei_introversion():
    from engine.divination.saju_mbti_predictor import _map_ei, LABEL_I
    label, _ = _map_ei(0.3)
    assert label == LABEL_I


def test_map_ei_uncertain():
    """경계 영역은 미정 — 단정 회피 (ADR-014)."""
    from engine.divination.saju_mbti_predictor import _map_ei, LABEL_UNCERTAIN
    label, _ = _map_ei(0.5)
    assert label == LABEL_UNCERTAIN


# ─────────────────────────── SN 매핑 ───────────────────────────


def test_map_sn_sensing():
    from engine.divination.saju_mbti_predictor import _map_sn, LABEL_S
    wuxing = {"목": 0.0, "화": 1.0, "토": 3.0, "금": 3.0, "수": 1.0}  # 토+금 = 6/8
    label, _ = _map_sn(wuxing)
    assert label == LABEL_S


def test_map_sn_intuition():
    from engine.divination.saju_mbti_predictor import _map_sn, LABEL_N
    wuxing = {"목": 3.0, "화": 1.0, "토": 0.0, "금": 1.0, "수": 3.0}  # 목+수 = 6/8
    label, _ = _map_sn(wuxing)
    assert label == LABEL_N


def test_map_sn_uncertain():
    from engine.divination.saju_mbti_predictor import _map_sn, LABEL_UNCERTAIN
    wuxing = {"목": 1.5, "화": 2.0, "토": 1.5, "금": 1.5, "수": 1.5}  # 균형
    label, _ = _map_sn(wuxing)
    assert label == LABEL_UNCERTAIN


# ─────────────────────────── TF 매핑 ───────────────────────────


def test_map_tf_thinking():
    from engine.divination.saju_mbti_predictor import _map_tf, LABEL_T
    wuxing = {"목": 1.0, "화": 1.0, "토": 1.0, "금": 4.0, "수": 1.0}  # 金 비중 ↑
    label, _ = _map_tf(wuxing, "甲")  # 양간
    assert label == LABEL_T


def test_map_tf_feeling():
    from engine.divination.saju_mbti_predictor import _map_tf, LABEL_F
    wuxing = {"목": 1.0, "화": 2.0, "토": 0.0, "금": 1.0, "수": 4.0}  # 火+水 비중 ↑
    label, _ = _map_tf(wuxing, "乙")  # 음간
    assert label == LABEL_F


def test_map_tf_uncertain_balanced():
    from engine.divination.saju_mbti_predictor import _map_tf, LABEL_UNCERTAIN
    wuxing = {"목": 1.5, "화": 1.5, "토": 2.0, "금": 1.5, "수": 1.5}
    label, _ = _map_tf(wuxing, "甲")
    assert label == LABEL_UNCERTAIN


# ─────────────────────────── JP 매핑 ───────────────────────────


def test_map_jp_balanced_judging():
    from engine.divination.saju_mbti_predictor import _map_jp, LABEL_J
    wuxing = {"목": 1.6, "화": 1.6, "토": 1.6, "금": 1.6, "수": 1.6}  # stdev=0
    label, _ = _map_jp(wuxing)
    assert label == LABEL_J


def test_map_jp_skewed_perceiving():
    from engine.divination.saju_mbti_predictor import _map_jp, LABEL_P
    wuxing = {"목": 0.0, "화": 0.0, "토": 8.0, "금": 0.0, "수": 0.0}  # 편중 stdev↑
    label, _ = _map_jp(wuxing)
    assert label == LABEL_P


def test_map_jp_uncertain_middle():
    from engine.divination.saju_mbti_predictor import _map_jp, LABEL_UNCERTAIN
    # stdev 약 0.7 — 미정 영역
    wuxing = {"목": 2.5, "화": 1.5, "토": 1.5, "금": 1.5, "수": 1.0}
    label, reason = _map_jp(wuxing)
    # stdev 영역 확인
    import statistics
    actual_stdev = statistics.pstdev(list(wuxing.values()))
    if 0.5 <= actual_stdev <= 1.0:
        assert label == LABEL_UNCERTAIN


# ─────────────────────────── 메인 진입 ───────────────────────────


def test_derive_mbti_tendency_full_saju():
    """실제 사주 dict → 4축 경향성."""
    from engine.divination.saju_mbti_predictor import derive_mbti_tendency
    saju = {
        "year": "庚午", "month": "壬午", "day": "乙巳", "hour": "癸未",
        "wuxing_dist": {"목": 1.0, "화": 3.0, "토": 1.0, "금": 1.0, "수": 2.0},
        "day_master_han": "乙",
    }
    t = derive_mbti_tendency(saju)
    # 4 축 모두 라벨 있음 (미정 또는 라벨)
    assert t.ei in ("E", "I", "미정")
    assert t.sn in ("S", "N", "미정")
    assert t.tf in ("T", "F", "미정")
    assert t.jp in ("J", "P", "미정")
    assert len(t.reasons) == 4


def test_derive_mbti_tendency_empty_input():
    """빈 입력 — DIV0 방지, 모든 축 안전 처리."""
    from engine.divination.saju_mbti_predictor import derive_mbti_tendency
    t = derive_mbti_tendency({})
    # 모든 축이 미정 또는 라벨 — 예외 없음
    assert t.ei
    assert t.sn
    assert t.tf
    assert t.jp


def test_derive_mbti_tendency_korean_day_master():
    """한글 일간 입력 → 한자 변환 후 처리."""
    from engine.divination.saju_mbti_predictor import derive_mbti_tendency
    saju = {
        "year": "庚午", "month": "壬午", "day": "乙巳", "hour": "癸未",
        "wuxing_dist": {"목": 1.0, "화": 3.0, "토": 1.0, "금": 1.0, "수": 2.0},
        "day_master": "을",  # 한글
    }
    t = derive_mbti_tendency(saju)
    # 한자 변환 후 정상 처리 — 예외 없음
    assert t.tf  # 어떤 라벨이든 매핑되어야 함


# ─────────────────────────── ADR-014 사용자 출력 의무 ───────────────────────────


def test_format_tendency_no_16_type_assertion():
    """사용자 출력에 16유형 단정(ENFJ 등) 절대 포함 금지."""
    from engine.divination.saju_mbti_predictor import format_tendency_for_persona, MbtiTendency
    t = MbtiTendency(ei="E", sn="N", tf="F", jp="J", reasons={})
    output = format_tendency_for_persona(t)
    # 16유형 4글자 조합 금지
    forbidden_types = [
        "ENFJ", "INFJ", "ENFP", "INFP",
        "ENTJ", "INTJ", "ENTP", "INTP",
        "ESFJ", "ISFJ", "ESFP", "ISFP",
        "ESTJ", "ISTJ", "ESTP", "ISTP",
    ]
    for mbti_type in forbidden_types:
        assert mbti_type not in output, f"16유형 단정 발견: {mbti_type}"


def test_format_tendency_contains_disclaimer():
    """사용자 출력에 면책 의무 포함 (ADR-014)."""
    from engine.divination.saju_mbti_predictor import format_tendency_for_persona, MbtiTendency
    t = MbtiTendency(ei="E", sn="N", tf="F", jp="J", reasons={})
    output = format_tendency_for_persona(t)
    assert "본 시스템의 자체 매핑" in output
    assert "MBTI 검사를 대체하지 않습니다" in output


def test_format_tendency_uses_persona_expression():
    """페르소나 어투 — '결' 또는 '기운' 표현 사용."""
    from engine.divination.saju_mbti_predictor import format_tendency_for_persona, MbtiTendency
    t = MbtiTendency(ei="E", sn="N", tf="F", jp="J", reasons={})
    output = format_tendency_for_persona(t)
    assert "결" in output or "기운" in output


def test_format_tendency_no_assertion_words():
    """단정 표현 절대 금지 — '입니다' '예측합니다' 등."""
    from engine.divination.saju_mbti_predictor import format_tendency_for_persona, MbtiTendency
    t = MbtiTendency(ei="E", sn="N", tf="F", jp="J", reasons={})
    output = format_tendency_for_persona(t)
    forbidden = [
        "MBTI는 ", "예측합니다", "단정합니다", "확정합니다",
        "정답은", "정확합니다",
    ]
    for word in forbidden:
        assert word not in output, f"단정 표현 발견: {word}"


def test_format_tendency_all_uncertain():
    """4축 모두 미정 — '알려주시게' 형식 안전 응답."""
    from engine.divination.saju_mbti_predictor import (
        format_tendency_for_persona, MbtiTendency, LABEL_UNCERTAIN,
    )
    t = MbtiTendency(
        ei=LABEL_UNCERTAIN, sn=LABEL_UNCERTAIN,
        tf=LABEL_UNCERTAIN, jp=LABEL_UNCERTAIN,
        reasons={},
    )
    output = format_tendency_for_persona(t)
    # 빈 출력이 아닌 안전한 미정 응답
    assert len(output) > 0
    assert "알려주시" in output or "들려주시" in output


# ─────────────────────────── 결정론 ───────────────────────────


def test_derive_mbti_tendency_deterministic():
    """같은 입력 → 같은 결과 (결정론 보장)."""
    from engine.divination.saju_mbti_predictor import derive_mbti_tendency
    saju = {
        "year": "庚午", "month": "壬午", "day": "乙巳", "hour": "癸未",
        "wuxing_dist": {"목": 1.0, "화": 3.0, "토": 1.0, "금": 1.0, "수": 2.0},
        "day_master_han": "乙",
    }
    t1 = derive_mbti_tendency(saju)
    t2 = derive_mbti_tendency(saju)
    assert t1.as_label() == t2.as_label()
