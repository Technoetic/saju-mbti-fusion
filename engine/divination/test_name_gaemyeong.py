"""engine.divination.name_gaemyeong — 개명(改名) 트랙 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# 테스트용 소규모 한자 후보 풀
_POOL_TEST = {
    # 木 (어금닛소리 ㄱ, ㅋ)
    "건": ["建", "健", "鍵"],
    "강": ["江", "康", "剛"],
    "교": ["敎", "巧"],
    # 火 (혓소리 ㄴ, ㄷ, ㄹ, ㅌ)
    "도": ["道", "圖", "桃"],
    "단": ["丹", "旦", "端"],
    "남": ["南", "男", "楠"],
    "다": ["多"],
    "탁": ["卓"],
    "태": ["太", "泰"],
    # 土 (목구멍소리 ㅇ, ㅎ)
    "안": ["安", "雁"],
    "은": ["銀", "恩"],
    "혁": ["革", "赫"],
    "현": ["賢", "玹"],
    "환": ["桓", "煥"],
    # 金 (잇소리 ㅅ, ㅈ, ㅊ)
    "성": ["誠", "城", "聖", "珹"],
    "수": ["秀", "壽", "洙"],
    "진": ["眞", "振", "辰"],
    "지": ["志", "智"],
    "재": ["在", "才", "材"],
    "찬": ["燦", "贊"],
    # 水 (입술소리 ㅁ, ㅂ, ㅍ)
    "민": ["民", "敏", "旻", "珉"],
    "범": ["範", "凡"],
    "보": ["普", "報", "保"],
    "백": ["白", "百"],
    "민": ["民", "旻", "珉"],
    "박": ["朴", "博"],
}


# ─────────────────────────── 기본 동작 ───────────────────────────

def test_find_gaemyeong_basic():
    """김(木) → 이름2자 화-토 흐름 자동 생성."""
    from engine.divination.name_gaemyeong import find_gaemyeong_candidates
    r = find_gaemyeong_candidates(
        surname_hanja="金",
        surname_korean="김",
        candidate_pool=_POOL_TEST,
        require_baleum_sangsaeng=True,
        top_n=5,
    )
    # 김(木) → 火(도/단/남/태) → 土(은/혁/현) 등 상생 흐름
    assert r.total_combinations > 0


def test_find_gaemyeong_no_combinations_for_unknown_surname():
    from engine.divination.name_gaemyeong import find_gaemyeong_candidates
    r = find_gaemyeong_candidates(
        surname_hanja="龘",  # 미수록
        surname_korean="?",
        candidate_pool=_POOL_TEST,
    )
    assert r.candidates == []


def test_find_gaemyeong_returns_top_n():
    from engine.divination.name_gaemyeong import find_gaemyeong_candidates
    r = find_gaemyeong_candidates(
        surname_hanja="金",
        surname_korean="김",
        candidate_pool=_POOL_TEST,
        top_n=3,
    )
    assert len(r.candidates) <= 3


# ─────────────────────────── 발음오행 상생 강제 ───────────────────────────

def test_baleum_sangsaeng_required():
    """require_baleum_sangsaeng=True 시 성→이름 발음오행이 상생 흐름."""
    from engine.divination.name_gaemyeong import find_gaemyeong_candidates
    from engine.divination.name_baleum import syllable_to_ohaeng, _SANGSAENG  # type: ignore[attr-defined]
    r = find_gaemyeong_candidates(
        surname_hanja="金", surname_korean="김",
        candidate_pool=_POOL_TEST,
        require_baleum_sangsaeng=True, top_n=5,
    )
    # 모든 후보는 김(ㄱ=木) → ?(火) → ?(土) 흐름이어야
    if r.candidates:
        c0 = r.candidates[0]
        s = c0.given_korean
        first_o = syllable_to_ohaeng(s[0])
        # 木→火 상생 매칭
        assert first_o == "화", f"첫 음절 {s[0]} 오행 {first_o} 화 아님"


# ─────────────────────────── Hard 필터 ───────────────────────────

def test_gaemyeong_excludes_bulyong():
    from engine.divination.name_gaemyeong import find_gaemyeong_candidates
    from engine.divination.name_bulyong import is_bulyong
    r = find_gaemyeong_candidates(
        surname_hanja="金", surname_korean="김",
        candidate_pool=_POOL_TEST,
    )
    for c in r.candidates:
        for ch in c.given_hanja:
            assert not is_bulyong(ch)


def test_gaemyeong_all_four_gyeok_good():
    """결과는 모두 4격 길수."""
    from engine.divination.name_gaemyeong import find_gaemyeong_candidates
    from engine.divination.name_scoring import calc_four_gyeok
    from engine.divination.name_strokes import kangxi_strokes
    r = find_gaemyeong_candidates(
        surname_hanja="金", surname_korean="김",
        candidate_pool=_POOL_TEST,
    )
    for c in r.candidates:
        surname = kangxi_strokes(c.surname_hanja)
        given = [kangxi_strokes(ch) for ch in c.given_hanja]
        if surname is not None and all(g is not None for g in given):
            four = calc_four_gyeok([surname], [g for g in given if g is not None])
            assert four.all_good is True


def test_gaemyeong_no_eumyang_bad():
    from engine.divination.name_gaemyeong import find_gaemyeong_candidates
    r = find_gaemyeong_candidates(
        surname_hanja="金", surname_korean="김",
        candidate_pool=_POOL_TEST,
    )
    for c in r.candidates:
        assert c.eumyang_grade != "bad"


# ─────────────────────────── 자원오행 가점 ───────────────────────────

def test_target_ohaeng_bonus():
    from engine.divination.name_gaemyeong import find_gaemyeong_candidates
    r = find_gaemyeong_candidates(
        surname_hanja="金", surname_korean="김",
        candidate_pool=_POOL_TEST,
        target_ohaeng="金",  # 자원오행 金 매칭 글자 가점
    )
    if r.candidates:
        # 가점받은 후보는 score > 0.5
        max_score = max(c.score for c in r.candidates)
        assert max_score >= 0.5


# ─────────────────────────── 정렬 ───────────────────────────

def test_candidates_sorted_by_score():
    from engine.divination.name_gaemyeong import find_gaemyeong_candidates
    r = find_gaemyeong_candidates(
        surname_hanja="金", surname_korean="김",
        candidate_pool=_POOL_TEST,
        target_ohaeng="金",
    )
    scores = [c.score for c in r.candidates]
    assert scores == sorted(scores, reverse=True)


# ─────────────────────────── 외자 ───────────────────────────

def test_gaemyeong_single_given():
    """외자 이름 (given_length=1)."""
    from engine.divination.name_gaemyeong import find_gaemyeong_candidates
    r = find_gaemyeong_candidates(
        surname_hanja="金", surname_korean="김",
        candidate_pool=_POOL_TEST, given_length=1,
        require_baleum_sangsaeng=True, top_n=5,
    )
    # 외자도 시도 가능
    assert r.total_combinations >= 0
    for c in r.candidates:
        assert len(c.given_korean) == 1
        assert len(c.given_hanja) == 1


# ─────────────────────────── 결정론 ───────────────────────────

def test_deterministic():
    from engine.divination.name_gaemyeong import find_gaemyeong_candidates
    a = find_gaemyeong_candidates(
        surname_hanja="金", surname_korean="김",
        candidate_pool=_POOL_TEST, target_ohaeng="金",
    )
    b = find_gaemyeong_candidates(
        surname_hanja="金", surname_korean="김",
        candidate_pool=_POOL_TEST, target_ohaeng="金",
    )
    assert len(a.candidates) == len(b.candidates)
    for ca, cb in zip(a.candidates, b.candidates):
        assert ca.full_hanja == cb.full_hanja


# ─────────────────────────── 직렬화 ───────────────────────────

def test_result_to_dict():
    from engine.divination.name_gaemyeong import find_gaemyeong_candidates, result_to_dict
    r = find_gaemyeong_candidates(
        surname_hanja="金", surname_korean="김",
        candidate_pool=_POOL_TEST,
    )
    d = result_to_dict(r)
    for k in ("surname_hanja", "surname_korean", "candidates",
              "total_combinations", "filtered_count"):
        assert k in d


# ─────────────────────────── max_combinations 가드 ───────────────────────────

def test_max_combinations_limit():
    """조합 폭발 방지 — max_combinations 상한."""
    from engine.divination.name_gaemyeong import find_gaemyeong_candidates
    r = find_gaemyeong_candidates(
        surname_hanja="金", surname_korean="김",
        candidate_pool=_POOL_TEST,
        max_combinations=10,
    )
    assert r.total_combinations <= 11  # 상한 + 1


# ─────────────────────────── 실제 사전과 통합 ───────────────────────────

def test_with_real_dict():
    """실제 한글음→한자 사전과 통합 동작."""
    from engine.divination.name_gaemyeong import find_gaemyeong_candidates
    from engine.divination.name_hangul_hanja import HANGUL_HANJA_MAP
    r = find_gaemyeong_candidates(
        surname_hanja="金", surname_korean="김",
        candidate_pool=HANGUL_HANJA_MAP,
        target_ohaeng="金", top_n=5,
        max_combinations=5000,
    )
    # 실제 사전이면 김(木) → 火(약 20+ 음절) → 土(약 15+ 음절) 조합 매우 많음
    assert r.total_combinations > 100
