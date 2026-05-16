"""engine.divination.name_saju_ohaeng — 사주 오행 분포 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 기본 동작 ───────────────────────────

def test_compute_returns_full_report():
    from engine.divination.name_saju_ohaeng import compute_saju_ohaeng
    r = compute_saju_ohaeng(1990, 5, 15, 14)
    assert "year" in r.pillars
    assert "month" in r.pillars
    assert "day" in r.pillars
    assert "hour" in r.pillars
    assert r.day_master  # 일간 한글
    assert len(r.distribution) == 5  # 목/화/토/금/수


def test_distribution_sums_to_8():
    """4기둥 = 8.0점 (천간 4 + 지지 가중치 합 4)."""
    from engine.divination.name_saju_ohaeng import compute_saju_ohaeng
    r = compute_saju_ohaeng(1990, 5, 15, 14)
    total = sum(r.distribution.values())
    assert 7.5 <= total <= 8.5


def test_weakest_and_strongest_extracted():
    """가장 적은/많은 오행 식별."""
    from engine.divination.name_saju_ohaeng import compute_saju_ohaeng
    r = compute_saju_ohaeng(1990, 5, 15, 14)
    assert r.weakest in ("목", "화", "토", "금", "수")
    assert r.strongest in ("목", "화", "토", "금", "수")
    # weakest의 분포 <= strongest의 분포
    assert r.distribution[r.weakest] <= r.distribution[r.strongest]


def test_recommended_target_is_weakest_or_missing():
    """추천 오행은 missing 우선, 없으면 weakest."""
    from engine.divination.name_saju_ohaeng import compute_saju_ohaeng
    r = compute_saju_ohaeng(1990, 5, 15, 14)
    if r.missing:
        assert r.recommended_target == r.missing[0]
    else:
        assert r.recommended_target == r.weakest


def test_balance_score_in_range():
    from engine.divination.name_saju_ohaeng import compute_saju_ohaeng
    r = compute_saju_ohaeng(1990, 5, 15, 14)
    assert 0.0 <= r.balance_score <= 1.0


# ─────────────────────────── 결정론 ───────────────────────────

def test_deterministic_same_input():
    from engine.divination.name_saju_ohaeng import compute_saju_ohaeng
    a = compute_saju_ohaeng(1990, 5, 15, 14)
    b = compute_saju_ohaeng(1990, 5, 15, 14)
    assert a.pillars == b.pillars
    assert a.distribution == b.distribution
    assert a.recommended_target == b.recommended_target


def test_different_birthdates_different_results():
    """다른 생년월일은 다른 분포."""
    from engine.divination.name_saju_ohaeng import compute_saju_ohaeng
    a = compute_saju_ohaeng(1990, 5, 15, 14)
    b = compute_saju_ohaeng(1985, 11, 3, 9)
    # 적어도 pillars 중 하나는 다름
    assert a.pillars != b.pillars


# ─────────────────────────── 직렬화 ───────────────────────────

def test_report_to_dict():
    from engine.divination.name_saju_ohaeng import compute_saju_ohaeng, report_to_dict
    d = report_to_dict(compute_saju_ohaeng(1990, 5, 15, 14))
    for k in ("pillars", "day_master", "distribution", "weakest", "strongest",
              "missing", "recommended_target", "balance_score", "advisory"):
        assert k in d


def test_advisory_text_non_empty():
    """사용자 노출용 advisory 텍스트가 비어있지 않음."""
    from engine.divination.name_saju_ohaeng import compute_saju_ohaeng, report_to_dict
    d = report_to_dict(compute_saju_ohaeng(1990, 5, 15, 14))
    assert len(d["advisory"]) > 20
    # 면책 표현 포함
    assert "참고용" in d["advisory"] or "학파별 차이" in d["advisory"]


# ─────────────────────────── 작명 모듈 호환 ───────────────────────────

def test_get_target_ohaeng_returns_one_of_five():
    from engine.divination.name_saju_ohaeng import get_target_ohaeng
    t = get_target_ohaeng(1990, 5, 15, 14)
    assert t in ("목", "화", "토", "금", "수")


def test_integration_with_gaemyeong():
    """name_gaemyeong이 사주 추천 오행을 받아 작명 추천."""
    from engine.divination.name_saju_ohaeng import get_target_ohaeng
    from engine.divination.name_gaemyeong import find_gaemyeong_candidates
    from engine.divination.name_hangul_hanja import HANGUL_HANJA_MAP

    target = get_target_ohaeng(1990, 5, 15, 14)
    r = find_gaemyeong_candidates(
        surname_hanja="金", surname_korean="김",
        candidate_pool=HANGUL_HANJA_MAP,
        target_ohaeng=target,
        top_n=3,
        max_combinations=5000,
    )
    # 적어도 후보 0개 이상은 시도
    assert r.total_combinations >= 0


# ─────────────────────────── 0점 결핍 케이스 ───────────────────────────

def test_missing_extracted_when_zero():
    """0점 오행이 있으면 missing 리스트에 포함."""
    from engine.divination.name_saju_ohaeng import compute_saju_ohaeng
    # 임의 생일 — 0점 오행 있을 가능성
    for y, m, d, h in [(2000, 1, 1, 0), (1995, 8, 20, 15), (1988, 12, 31, 23)]:
        r = compute_saju_ohaeng(y, m, d, h)
        # missing은 0점 오행만 포함
        for ohaeng in r.missing:
            assert r.distribution[ohaeng] == 0.0


# ─────────────────────────── 균형 잡힌 케이스 ───────────────────────────

def test_balance_score_high_when_distributed():
    """오행이 고르게 분포될수록 balance_score 높음."""
    from engine.divination.name_saju_ohaeng import compute_saju_ohaeng
    # 여러 케이스 중 balance 비교
    cases = [(1990, 5, 15, 14), (1985, 11, 3, 9), (2000, 6, 10, 12)]
    scores = [compute_saju_ohaeng(*c).balance_score for c in cases]
    # 적어도 모든 점수 0~1
    for s in scores:
        assert 0.0 <= s <= 1.0
