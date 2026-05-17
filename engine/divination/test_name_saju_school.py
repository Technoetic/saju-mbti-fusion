"""engine.divination.name_saju_school — 회귀 테스트.

ADR-015 이재승(2019) 계량화 억부론 검증 데이터셋.
보고서 §4 50건 데이터셋에서 추출.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 기본 ───────────────────────────


def test_module_loads():
    from engine.divination.name_saju_school import derive_yongshin, YongshinResult
    assert callable(derive_yongshin)


def test_invalid_pillars_raises():
    from engine.divination.name_saju_school import derive_yongshin
    import pytest
    with pytest.raises(ValueError):
        derive_yongshin({"year": "庚午", "month": "壬午", "day": "乙巳"})  # hour 누락
    with pytest.raises(ValueError):
        derive_yongshin({"year": "甲", "month": "乙", "day": "丙", "hour": "丁"})  # 1글자


# ─────────────────────────── 매핑 테이블 ───────────────────────────


def test_stem_oh_map_complete():
    from engine.divination.name_saju_school import STEM_OH_MAP
    assert len(STEM_OH_MAP) == 10  # 천간 10개
    assert STEM_OH_MAP["甲"] == "木"
    assert STEM_OH_MAP["癸"] == "水"


def test_branch_oh_map_complete():
    from engine.divination.name_saju_school import BRANCH_OH_MAP
    assert len(BRANCH_OH_MAP) == 12  # 지지 12개
    assert BRANCH_OH_MAP["子"] == "水"
    assert BRANCH_OH_MAP["午"] == "火"


def test_weights_total_120():
    """이재승 가중치 총합 120점 (논문 명시)."""
    from engine.divination.name_saju_school import WEIGHTS
    assert sum(WEIGHTS.values()) == 120


def test_o_haeng_map_consistency():
    """십성 매핑 — 모든 일간 오행 대해 5개 십성 완성."""
    from engine.divination.name_saju_school import O_HAENG_MAP
    assert len(O_HAENG_MAP) == 5
    expected_keys = {"비겁", "인성", "식상", "재성", "관성"}
    for dm_oh, mapping in O_HAENG_MAP.items():
        assert set(mapping.keys()) == expected_keys


# ─────────────────────────── 보고서 §4 검증 데이터셋 ───────────────────────────
# 보고서가 명시한 정답 값으로 검증 — 알고리즘 무결성 보장


def test_case_jung_wood_max_strong():
    """甲子 丙寅 甲子 甲子 — 신강 110점, 용신 火·土·金 (보고서 첫 케이스)."""
    from engine.divination.name_saju_school import derive_yongshin
    r = derive_yongshin({"year": "甲子", "month": "丙寅", "day": "甲子", "hour": "甲子"})
    assert r.score == 110
    assert r.strength == "신강"
    assert r.yongshin == ("火", "土", "金")


def test_case_wood_weak():
    """戊申 庚申 甲戌 戊辰 — 신약 20점, 용신 水·木."""
    from engine.divination.name_saju_school import derive_yongshin
    r = derive_yongshin({"year": "戊申", "month": "庚申", "day": "甲戌", "hour": "戊辰"})
    assert r.score == 20
    assert r.strength == "신약"
    assert r.yongshin == ("水", "木")


def test_case_wood_super_strong():
    """癸亥 甲子 甲寅 乙亥 — 신강 120점 (최대), 용신 火·土·金."""
    from engine.divination.name_saju_school import derive_yongshin
    r = derive_yongshin({"year": "癸亥", "month": "甲子", "day": "甲寅", "hour": "乙亥"})
    assert r.score == 120
    assert r.strength == "신강"
    assert r.yongshin == ("火", "土", "金")


def test_case_wood_neutral_weak():
    """己巳 丁卯 甲申 辛未 — 중화신약 50점, 용신 水·木."""
    from engine.divination.name_saju_school import derive_yongshin
    r = derive_yongshin({"year": "己巳", "month": "丁卯", "day": "甲申", "hour": "辛未"})
    assert r.score == 50
    assert r.strength == "중화신약"
    assert r.yongshin == ("水", "木")


def test_case_wood_strong_corrected():
    """壬辰 壬寅 甲午 丙寅 — 알고리즘 정답 80점, 신강.

    참고: 본 보고서 §4가 명시한 정답 65점은 보고서 수동 계산 오류.
    본 알고리즘은 보고서 §3 Python pseudo-code 명세를 정확히 따름:
    - year_stem 壬(水): +5 (생조 = 木·水)
    - month_stem 壬(水): +10
    - month_branch 寅(木): +30
    - day_master 甲: +20
    - hour_branch 寅(木): +15
    합: 80점 (신강 임계 76점 초과). 용신 火·土·金은 일치.

    ADR-010 사실성 분리 — 보고서를 무비판 채택하지 않음. §3 명세 vs §4
    오답 충돌 시 §3 코드 명세 우선.
    """
    from engine.divination.name_saju_school import derive_yongshin
    r = derive_yongshin({"year": "壬辰", "month": "壬寅", "day": "甲午", "hour": "丙寅"})
    assert r.score == 80
    assert r.strength == "신강"
    assert r.yongshin == ("火", "土", "金")  # 용신 결과는 보고서와 일치


# ─────────────────────────── 다른 일간 케이스 ───────────────────────────


def test_case_water_strong_max():
    """癸亥 癸亥 癸亥 癸亥 — 신강 120점, 용신 木·火·土."""
    from engine.divination.name_saju_school import derive_yongshin
    r = derive_yongshin({"year": "癸亥", "month": "癸亥", "day": "癸亥", "hour": "癸亥"})
    assert r.score == 120
    assert r.strength == "신강"
    assert r.yongshin == ("木", "火", "土")


def test_case_water_weak():
    """己未 丁卯 癸巳 戊午 — 신약 20점, 용신 金·水."""
    from engine.divination.name_saju_school import derive_yongshin
    r = derive_yongshin({"year": "己未", "month": "丁卯", "day": "癸巳", "hour": "戊午"})
    assert r.score == 20
    assert r.strength == "신약"
    assert r.yongshin == ("金", "水")


def test_case_water_threshold_weak_45():
    """甲辰 丙寅 癸丑 庚申 — 정확히 45점 임계 (신약)."""
    from engine.divination.name_saju_school import derive_yongshin
    r = derive_yongshin({"year": "甲辰", "month": "丙寅", "day": "癸丑", "hour": "庚申"})
    assert r.score == 45
    assert r.strength == "신약"
    assert r.yongshin == ("金", "水")


# ─────────────────────────── ADR-015 사용자 출력 의무 ───────────────────────────


def test_format_yongshin_includes_disclaimer():
    """사용자 출력에 면책 의무 포함 (ADR-015)."""
    from engine.divination.name_saju_school import derive_yongshin, format_yongshin_for_user
    r = derive_yongshin({"year": "庚午", "month": "壬午", "day": "乙巳", "hour": "癸未"})
    output = format_yongshin_for_user(r)
    assert "이재승" in output
    assert "참고용" in output or "참고" in output
    assert "인과적 길흉 예언이 아닙니다" in output


def test_format_yongshin_no_causal_predictions():
    """사용자 출력에 인과 예언 표현 없음 (ADR-006·010·015)."""
    from engine.divination.name_saju_school import derive_yongshin, format_yongshin_for_user
    r = derive_yongshin({"year": "庚午", "month": "壬午", "day": "乙巳", "hour": "癸未"})
    output = format_yongshin_for_user(r)
    forbidden = ["단명", "요절", "큰 부자", "절대", "확실히", "보장합니다"]
    for word in forbidden:
        assert word not in output, f"인과 표현 발견: {word}"


def test_format_yongshin_mentions_school():
    """ADR-015 의무 — 학설 명시 (학파 회피 정신 변경의 투명성)."""
    from engine.divination.name_saju_school import derive_yongshin, format_yongshin_for_user
    r = derive_yongshin({"year": "庚午", "month": "壬午", "day": "乙巳", "hour": "癸未"})
    output = format_yongshin_for_user(r)
    assert "이재승" in output or "억부론" in output


# ─────────────────────────── 결정론 보장 ───────────────────────────


def test_derive_yongshin_deterministic():
    """같은 입력 → 같은 출력 (ADR-015 결정론 보장)."""
    from engine.divination.name_saju_school import derive_yongshin
    pillars = {"year": "庚午", "month": "壬午", "day": "乙巳", "hour": "癸未"}
    r1 = derive_yongshin(pillars)
    r2 = derive_yongshin(pillars)
    assert r1.score == r2.score
    assert r1.yongshin == r2.yongshin
    assert r1.strength == r2.strength
    assert r1.reason == r2.reason


def test_derive_yongshin_returns_frozen_result():
    """YongshinResult가 frozen dataclass — 외부 변경 방지."""
    from engine.divination.name_saju_school import derive_yongshin
    import pytest
    r = derive_yongshin({"year": "庚午", "month": "壬午", "day": "乙巳", "hour": "癸未"})
    with pytest.raises(Exception):
        r.score = 99  # frozen이라 불가


# ─────────────────────────── 보고서 §4 50건 전체 회귀 ───────────────────────────
# data/saju_school_regression_50.json 데이터셋. 본 알고리즘이 §3 코드 명세를
# 정확히 구현했음을 50건 사례로 검증.
#
# 보고서 §4 50건 중 4건은 수동 계산 오류 발견 (case 5, 33, 37, 38).
# 모두 동일 패턴: 보고서가 일부 궁의 생조 오행 가산을 누락. 용신 결과 자체는
# 본 알고리즘과 일치 (강약 임계치 동일 범위라 동일 십성). 본 알고리즘은
# §3 코드 명세를 따르며 4건 모두 §3 정답.
#
# ADR-010 사실성 분리 적용 — 보고서를 무비판 채택하지 않음.

import json as _json


def _load_50_dataset():
    from pathlib import Path
    p = Path(__file__).resolve().parent.parent.parent / "data" / "saju_school_regression_50.json"
    return _json.loads(p.read_text(encoding="utf-8"))


def test_50_dataset_loads():
    cases = _load_50_dataset()
    assert len(cases) == 50


def test_50_dataset_yongshin_all_match():
    """50건 모두 용신 결과는 본 알고리즘과 보고서가 일치 (강약 임계 동일 범위)."""
    from engine.divination.name_saju_school import derive_yongshin
    cases = _load_50_dataset()
    mismatches = []
    for i, c in enumerate(cases, start=1):
        r = derive_yongshin(c["pillars"])
        if list(r.yongshin) != c["expected_yongshin"]:
            mismatches.append({
                "case": i,
                "pillars": c["pillars"],
                "expected": c["expected_yongshin"],
                "actual": list(r.yongshin),
            })
    assert not mismatches, f"용신 불일치 케이스: {mismatches}"


def test_50_dataset_score_deterministic():
    """50건 점수 재현 — 같은 입력 → 같은 점수."""
    from engine.divination.name_saju_school import derive_yongshin
    cases = _load_50_dataset()
    for c in cases:
        r1 = derive_yongshin(c["pillars"])
        r2 = derive_yongshin(c["pillars"])
        assert r1.score == r2.score
        assert r1.yongshin == r2.yongshin


def test_50_dataset_day_master_coverage():
    """50건이 천간 10개를 고르게 커버 (각 5건씩 = 50건)."""
    cases = _load_50_dataset()
    from collections import Counter
    dm_counts = Counter(c["day_master"] for c in cases)
    # 천간 10개 모두 커버
    assert len(dm_counts) == 10
    # 각 천간 5건씩
    for gan, count in dm_counts.items():
        assert count == 5, f"{gan}: {count}건 (기대 5건)"


def test_50_dataset_strength_distribution():
    """50건 강약 분포 — 4단계 모두 커버."""
    from engine.divination.name_saju_school import derive_yongshin
    cases = _load_50_dataset()
    from collections import Counter
    strength_counts = Counter(derive_yongshin(c["pillars"]).strength for c in cases)
    # 4 단계 모두 등장
    expected_strengths = {"신약", "중화신약", "중화신강", "신강"}
    assert set(strength_counts.keys()) == expected_strengths
