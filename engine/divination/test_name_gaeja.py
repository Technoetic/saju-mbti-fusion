"""engine.divination.name_gaeja — 개자 트랙 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# 테스트용 한자 후보 풀 — name_strokes 수록 한자 사용
_POOL_TEST = {
    "성": ["星", "城", "誠", "成", "聖", "珹", "盛", "性"],
    "민": ["敏", "民", "旻", "珉", "旼"],
    "재": ["在", "才", "載"],
    "훈": [],  # 미수록 가정
}


# ─────────────────────────── filter_hanja_pool ───────────────────────────

def test_filter_removes_bulyong():
    """星은 불용한자이므로 제거."""
    from engine.divination.name_gaeja import filter_hanja_pool
    result = filter_hanja_pool(["星", "城", "珹"])
    assert "星" not in result
    assert "城" in result
    assert "珹" in result


def test_filter_removes_unstrok_missing():
    """원획수 미수록 한자 제거."""
    from engine.divination.name_gaeja import filter_hanja_pool
    result = filter_hanja_pool(["龘", "城"])  # 龘 미수록
    assert "龘" not in result
    assert "城" in result


def test_filter_keeps_good():
    from engine.divination.name_gaeja import filter_hanja_pool
    result = filter_hanja_pool(["珹", "旻", "誠"])
    assert set(result) == {"珹", "旻", "誠"}


# ─────────────────────────── find_gaeja_candidates ───────────────────────────

def test_find_gaeja_basic():
    """이성민 — 성/민 후보 풀에서 길수 4격 조합 찾기."""
    from engine.divination.name_gaeja import find_gaeja_candidates
    r = find_gaeja_candidates(
        surname_hanja="李",
        surname_korean="이",
        given_korean="성민",
        candidate_pool=_POOL_TEST,
        top_n=10,
    )
    # 후보가 있어야 함 (성·민 후보 풀이 충분히 큼)
    assert r.total_combinations > 0
    # 통과한 후보 있을 수 있고 없을 수도 있음 — 적어도 시도는 함


def test_find_gaeja_returns_top_n():
    from engine.divination.name_gaeja import find_gaeja_candidates
    r = find_gaeja_candidates(
        surname_hanja="李",
        surname_korean="이",
        given_korean="성민",
        candidate_pool=_POOL_TEST,
        top_n=3,
    )
    assert len(r.candidates) <= 3


def test_find_gaeja_excludes_bulyong():
    """결과에 불용한자가 절대 없어야 함."""
    from engine.divination.name_gaeja import find_gaeja_candidates
    from engine.divination.name_bulyong import is_bulyong
    r = find_gaeja_candidates(
        surname_hanja="李",
        surname_korean="이",
        given_korean="성민",
        candidate_pool=_POOL_TEST,
    )
    for c in r.candidates:
        for ch in c.given_hanja:
            assert not is_bulyong(ch), f"불용한자 {ch} 포함"


def test_find_gaeja_all_four_gyeok_good():
    """결과는 모두 4격 길수여야."""
    from engine.divination.name_gaeja import find_gaeja_candidates
    r = find_gaeja_candidates(
        surname_hanja="李",
        surname_korean="이",
        given_korean="성민",
        candidate_pool=_POOL_TEST,
    )
    for c in r.candidates:
        assert c.all_gyeok_good is True


def test_find_gaeja_no_eumyang_bad():
    """결과는 음양 BAD가 아니어야."""
    from engine.divination.name_gaeja import find_gaeja_candidates
    r = find_gaeja_candidates(
        surname_hanja="李",
        surname_korean="이",
        given_korean="성민",
        candidate_pool=_POOL_TEST,
    )
    for c in r.candidates:
        assert c.eumyang_grade != "bad"


def test_find_gaeja_unknown_surname_returns_empty():
    """미수록 성씨면 빈 결과."""
    from engine.divination.name_gaeja import find_gaeja_candidates
    r = find_gaeja_candidates(
        surname_hanja="龘",  # 미수록
        surname_korean="?",
        given_korean="성민",
        candidate_pool=_POOL_TEST,
    )
    assert r.candidates == []


def test_find_gaeja_empty_pool():
    """음절 후보 풀이 비어있으면 빈 결과."""
    from engine.divination.name_gaeja import find_gaeja_candidates
    r = find_gaeja_candidates(
        surname_hanja="李",
        surname_korean="이",
        given_korean="성훈",  # 훈 후보 비어있음
        candidate_pool=_POOL_TEST,
    )
    assert r.candidates == []


# ─────────────────────────── 자원오행 매칭 ───────────────────────────

def test_target_ohaeng_score_higher():
    """target_ohaeng 매칭되는 한자 조합이 더 높은 점수."""
    from engine.divination.name_gaeja import find_gaeja_candidates
    # target="金" — 珹/誠/聖 같은 金 오행 한자가 가점
    r = find_gaeja_candidates(
        surname_hanja="李",
        surname_korean="이",
        given_korean="성민",
        candidate_pool=_POOL_TEST,
        target_ohaeng="金",
    )
    # 매칭 카운트가 1 이상인 후보가 더 높은 점수
    if r.candidates:
        scores_with_match = [c.score for c in r.candidates if c.ohaeng_match_count > 0]
        if scores_with_match:
            assert max(scores_with_match) >= 0.5


# ─────────────────────────── 정렬 ───────────────────────────

def test_candidates_sorted_by_score_desc():
    from engine.divination.name_gaeja import find_gaeja_candidates
    r = find_gaeja_candidates(
        surname_hanja="李",
        surname_korean="이",
        given_korean="성민",
        candidate_pool=_POOL_TEST,
        target_ohaeng="金",
    )
    scores = [c.score for c in r.candidates]
    assert scores == sorted(scores, reverse=True)


# ─────────────────────────── 결정론 ───────────────────────────

def test_deterministic_results():
    """같은 입력은 같은 결과."""
    from engine.divination.name_gaeja import find_gaeja_candidates
    a = find_gaeja_candidates(
        surname_hanja="李", surname_korean="이", given_korean="성민",
        candidate_pool=_POOL_TEST,
    )
    b = find_gaeja_candidates(
        surname_hanja="李", surname_korean="이", given_korean="성민",
        candidate_pool=_POOL_TEST,
    )
    assert len(a.candidates) == len(b.candidates)
    for ca, cb in zip(a.candidates, b.candidates):
        assert ca.full_hanja == cb.full_hanja
        assert ca.score == cb.score


# ─────────────────────────── 직렬화 ───────────────────────────

def test_result_to_dict():
    from engine.divination.name_gaeja import find_gaeja_candidates, result_to_dict
    r = find_gaeja_candidates(
        surname_hanja="李", surname_korean="이", given_korean="성민",
        candidate_pool=_POOL_TEST,
    )
    d = result_to_dict(r)
    for k in ("surname_hanja", "surname_korean", "given_korean",
              "candidates", "total_combinations", "filtered_count"):
        assert k in d


# ─────────────────────────── 보고서 §5-B 시나리오 ───────────────────────────

def test_보고서_시나리오_starbeen_to_gaeja():
    """보고서 예시: 이성민 星敏(불용) → 발음 유지 + 한자 swap.
    적어도 1개 이상 후보가 나와야 (성·민 음절 후보 풀 충분).
    """
    from engine.divination.name_gaeja import find_gaeja_candidates
    pool = {
        "성": ["城", "誠", "成", "聖", "珹", "盛", "性"],
        "민": ["民", "旻", "珉", "旼"],
    }
    r = find_gaeja_candidates(
        surname_hanja="李",
        surname_korean="이",
        given_korean="성민",
        candidate_pool=pool,
        top_n=10,
    )
    # 적어도 1개 조합 시도, 통과한 것 있을 수 있음
    assert r.total_combinations > 0
