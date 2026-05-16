"""engine.divination.name_eumyang — 음양 조화 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 기본 변환 ───────────────────────────

def test_stroke_to_eumyang_odd_is_yang():
    from engine.divination.name_eumyang import stroke_to_eumyang, YANG
    for n in (1, 3, 5, 7, 9, 11, 13):
        assert stroke_to_eumyang(n) == YANG


def test_stroke_to_eumyang_even_is_eum():
    from engine.divination.name_eumyang import stroke_to_eumyang, EUM
    for n in (2, 4, 6, 8, 10, 12):
        assert stroke_to_eumyang(n) == EUM


# ─────────────────────────── 평가 ───────────────────────────

def test_evaluate_balanced_mix():
    """7-9-11 → 양-양-양 BAD."""
    from engine.divination.name_eumyang import evaluate_eumyang, GRADE_BAD
    r = evaluate_eumyang([7, 9, 11])
    assert r.grade == GRADE_BAD
    assert r.pattern == "양-양-양"


def test_evaluate_all_eum_bad():
    """6-8-10 → 음-음-음 BAD."""
    from engine.divination.name_eumyang import evaluate_eumyang, GRADE_BAD
    r = evaluate_eumyang([6, 8, 10])
    assert r.grade == GRADE_BAD
    assert r.pattern == "음-음-음"


def test_evaluate_mixed_good():
    """7-8-9 → 양-음-양 GOOD."""
    from engine.divination.name_eumyang import evaluate_eumyang, GRADE_GOOD
    r = evaluate_eumyang([7, 8, 9])
    assert r.grade == GRADE_GOOD
    assert r.pattern == "양-음-양"


def test_evaluate_eum_yang_yang():
    """8-7-9 → 음-양-양 GOOD."""
    from engine.divination.name_eumyang import evaluate_eumyang, GRADE_GOOD
    r = evaluate_eumyang([8, 7, 9])
    assert r.grade == GRADE_GOOD


def test_evaluate_counts():
    from engine.divination.name_eumyang import evaluate_eumyang
    r = evaluate_eumyang([7, 8, 9])
    assert r.yang_count == 2
    assert r.eum_count == 1


def test_evaluate_empty():
    from engine.divination.name_eumyang import evaluate_eumyang, GRADE_NEUTRAL
    r = evaluate_eumyang([])
    assert r.grade == GRADE_NEUTRAL


# ─────────────────────────── 외자 (2자) ───────────────────────────

def test_evaluate_two_strokes_mixed():
    """성+외자: 7-8 → 양-음 GOOD."""
    from engine.divination.name_eumyang import evaluate_eumyang, GRADE_GOOD
    r = evaluate_eumyang([7, 8])
    assert r.grade == GRADE_GOOD


def test_evaluate_two_strokes_same_bad():
    """7-9 → 양-양 BAD."""
    from engine.divination.name_eumyang import evaluate_eumyang, GRADE_BAD
    r = evaluate_eumyang([7, 9])
    assert r.grade == GRADE_BAD


# ─────────────────────────── is_balanced ───────────────────────────

def test_is_balanced_shortcut():
    from engine.divination.name_eumyang import is_balanced
    assert is_balanced([7, 8, 9]) is True
    assert is_balanced([7, 9, 11]) is False


# ─────────────────────────── 결정론 ───────────────────────────

def test_deterministic():
    from engine.divination.name_eumyang import evaluate_eumyang
    a = evaluate_eumyang([7, 9, 11])
    b = evaluate_eumyang([7, 9, 11])
    assert a.pattern == b.pattern
    assert a.grade == b.grade


# ─────────────────────────── 직렬화 ───────────────────────────

def test_report_to_dict():
    from engine.divination.name_eumyang import evaluate_eumyang, report_to_dict
    d = report_to_dict(evaluate_eumyang([7, 8, 9]))
    for k in ("pattern", "sequence", "yang_count", "eum_count", "grade", "reason"):
        assert k in d


# ─────────────────────────── 실제 이름 예시 ───────────────────────────

def test_이성민_yang_yang_yang():
    """이성민(李 7 / 星 9 / 敏 11) → 모두 홀수 → 음양 BAD."""
    from engine.divination.name_eumyang import evaluate_eumyang, GRADE_BAD
    r = evaluate_eumyang([7, 9, 11])
    assert r.grade == GRADE_BAD
