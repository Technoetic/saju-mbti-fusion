"""engine.divination.name_scoring — 81수리 + 4격 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 81수 정규화 ───────────────────────────

def test_normalize_under_81():
    from engine.divination.name_scoring import normalize_su
    assert normalize_su(1) == 1
    assert normalize_su(45) == 45
    assert normalize_su(81) == 81


def test_normalize_over_81():
    from engine.divination.name_scoring import normalize_su
    # 82 → 1, 100 → 19, 162 → 81
    assert normalize_su(82) == 1
    assert normalize_su(100) == 19
    assert normalize_su(162) == 81


def test_normalize_zero_and_negative():
    from engine.divination.name_scoring import normalize_su
    assert normalize_su(0) == 1
    assert normalize_su(-5) == 1


# ─────────────────────────── eval_su ───────────────────────────

def test_eval_su_good():
    from engine.divination.name_scoring import eval_su, GOOD
    # 통설상 길수 — 1, 3, 5, 7, 8, 11, 13, 15, 16, 17, 18, 21, 23, 24, 25, 29, 31~
    for n in (1, 3, 5, 7, 8, 11, 13, 15, 16, 21, 23, 24, 25, 31, 33, 81):
        assert eval_su(n).grade == GOOD, f"{n} should be GOOD"


def test_eval_su_bad():
    from engine.divination.name_scoring import eval_su, BAD
    for n in (2, 4, 9, 10, 12, 14, 19, 20, 22, 26, 34, 36, 42, 43, 44, 46):
        assert eval_su(n).grade == BAD, f"{n} should be BAD"


def test_eval_su_with_label():
    """주요 수에는 라벨이 붙어있어야."""
    from engine.divination.name_scoring import eval_su
    r = eval_su(81)
    assert r.label  # 비어있지 않음


def test_is_good_shortcut():
    from engine.divination.name_scoring import is_good
    assert is_good(1) is True
    assert is_good(2) is False
    assert is_good(81) is True


# ─────────────────────────── 4격 계산 — 표준 3자 성명 ───────────────────────────

def test_four_gyeok_standard_name():
    """이성민(李 7 / 星 9 / 敏 11) — 4격 산출 검증."""
    from engine.divination.name_scoring import calc_four_gyeok
    r = calc_four_gyeok([7], [9, 11])
    # 원격 = 9 + 11 = 20
    # 형격 = 7 + 9 = 16
    # 이격 = 7 + 11 = 18
    # 정격 = 7 + 9 + 11 = 27
    assert r.won_gyeok.su == 20
    assert r.hyeong_gyeok.su == 16
    assert r.i_gyeok.su == 18
    assert r.jeong_gyeok.su == 27


def test_four_gyeok_all_good_name():
    """7-8-8 → 원15(GOOD)·형15(GOOD)·이15(GOOD)·정23(GOOD)."""
    from engine.divination.name_scoring import calc_four_gyeok
    r = calc_four_gyeok([7], [8, 8])
    assert r.won_gyeok.su == 16
    assert r.hyeong_gyeok.su == 15
    assert r.i_gyeok.su == 15
    assert r.jeong_gyeok.su == 23
    assert r.all_good is True
    assert r.bad_count == 0


# ─────────────────────────── 외자 처리 ───────────────────────────

def test_four_gyeok_single_given_name():
    """이성(李 7 / 星 9) — 외자. 빈 자리에 가상 수 1 대입.
    원격 = 9 + 1 = 10
    형격 = 7 + 9 = 16
    이격 = 7 + 1 = 8
    정격 = 7 + 9 + 1 = 17
    """
    from engine.divination.name_scoring import calc_four_gyeok
    r = calc_four_gyeok([7], [9])
    assert r.won_gyeok.su == 10
    assert r.hyeong_gyeok.su == 16
    assert r.i_gyeok.su == 8
    assert r.jeong_gyeok.su == 17


def test_four_gyeok_double_surname():
    """복성 (성 2자) — 합으로 처리.
    제갈(諸 16 / 葛 13) + 공(空 8) — 외자.
    성 합 = 29
    원격 = 8 + 1 = 9
    형격 = 29 + 8 = 37
    이격 = 29 + 1 = 30
    정격 = 29 + 8 + 1 = 38
    """
    from engine.divination.name_scoring import calc_four_gyeok
    r = calc_four_gyeok([16, 13], [8])
    assert r.hyeong_gyeok.su == 37
    assert r.jeong_gyeok.su == 38


# ─────────────────────────── 종합 평가 ───────────────────────────

def test_summary_grade_good():
    """4격 모두 길수 → summary good."""
    from engine.divination.name_scoring import calc_four_gyeok
    r = calc_four_gyeok([7], [8, 8])  # 16/15/15/23 모두 GOOD
    assert r.summary_grade == "good"


def test_summary_grade_bad_when_2_or_more_bad():
    """2개 이상 흉수 → summary bad."""
    from engine.divination.name_scoring import calc_four_gyeok
    # 4-4 → 원8(GOOD) / 형8(GOOD) / 이8(GOOD) / 정12(BAD)
    # 다른 조합 — 2개 BAD 만들기:
    # 성 4, 이름 4, 4 → 원8(GOOD), 형8(GOOD), 이8(GOOD), 정12(BAD)
    # 1 BAD only → neutral
    # 4 + [9, 10] → 원19(BAD), 형13(GOOD), 이14(BAD), 정23(GOOD) — 2 BAD
    r = calc_four_gyeok([4], [9, 10])
    assert r.bad_count >= 2
    assert r.summary_grade == "bad"


# ─────────────────────────── report_to_dict ───────────────────────────

def test_report_to_dict_has_all_keys():
    from engine.divination.name_scoring import calc_four_gyeok, report_to_dict
    r = calc_four_gyeok([7], [9, 11])
    d = report_to_dict(r)
    for k in ("won_gyeok", "hyeong_gyeok", "i_gyeok", "jeong_gyeok",
              "all_good", "bad_count", "summary_grade"):
        assert k in d
    for g in ("won_gyeok", "hyeong_gyeok", "i_gyeok", "jeong_gyeok"):
        assert "su" in d[g]
        assert "grade" in d[g]


# ─────────────────────────── 통합 진입점 score_name ───────────────────────────

def test_score_name_full_integration():
    """이성민(李星敏) — strokes + four_gyeok + bulyong 통합."""
    from engine.divination.name_scoring import score_name
    r = score_name("李星敏")
    assert r is not None
    # 획수
    assert r["strokes"]["kangxi"] == [7, 9, 11]
    assert r["strokes"]["kangxi_total"] == 27
    # 4격
    assert r["four_gyeok"]["jeong_gyeok"]["su"] == 27
    # 불용
    assert r["bulyong"]["has_bulyong"] is True
    assert r["bulyong"]["bulyong_count"] == 2  # 星 + 敏
    # 점수 상태
    assert r["scoring_status"] == "ok"


def test_score_name_clean_no_bulyong():
    """이재훈 (李在勳) — 좋은 한자만. 불용 없음."""
    from engine.divination.name_scoring import score_name
    r = score_name("李珹旻")
    assert r["bulyong"]["has_bulyong"] is False
    assert r["four_gyeok"] is not None


def test_score_name_with_missing_returns_incomplete():
    """미수록 한자 포함 시 incomplete."""
    from engine.divination.name_scoring import score_name
    r = score_name("李龘")
    assert r["scoring_status"] == "incomplete"
    assert "龘" in r["strokes"]["missing"]


def test_score_name_empty():
    from engine.divination.name_scoring import score_name
    assert score_name("") is None
    assert score_name(None) is None  # type: ignore[arg-type]


# ─────────────────────────── 결정론 ───────────────────────────

def test_deterministic():
    from engine.divination.name_scoring import score_name
    a = score_name("李星敏")
    b = score_name("李星敏")
    assert a == b


# ─────────────────────────── 81수 분류 일관성 ───────────────────────────

def test_81_grades_covered():
    """1~81 모든 수가 GOOD/NEUTRAL/BAD 중 하나로 분류."""
    from engine.divination.name_scoring import eval_su, GOOD, NEUTRAL, BAD
    for n in range(1, 82):
        r = eval_su(n)
        assert r.grade in (GOOD, NEUTRAL, BAD), f"{n} no grade"


def test_보고서_핵심_길수_길수성():
    """보고서·통설이 강조하는 핵심 길수 (1, 3, 5, 6, 7, 8, 11, 13, 15, 16, 21, 23, 24, 25)."""
    from engine.divination.name_scoring import is_good
    for n in (1, 3, 5, 6, 7, 8, 11, 13, 15, 16, 21, 23, 24, 25):
        assert is_good(n), f"{n} should be GOOD per 통설"
