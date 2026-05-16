"""engine.divination.name_hangul_hanja — 한글음→한자 사전 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 매니페스트 ───────────────────────────

def test_total_syllables_at_least_240():
    from engine.divination.name_hangul_hanja import total_syllables
    assert total_syllables() >= 240


def test_total_hanja_at_least_1000():
    """프론트 한글음_한자 사전 이식 — 1000+ 한자."""
    from engine.divination.name_hangul_hanja import total_hanja
    assert total_hanja() >= 1000


def test_common_surnames_present():
    """10대 한국 성씨 음절 모두 수록."""
    from engine.divination.name_hangul_hanja import HANGUL_HANJA_MAP
    for s in ("김", "이", "박", "최", "정", "강", "조", "윤", "장", "임"):
        assert s in HANGUL_HANJA_MAP
        assert len(HANGUL_HANJA_MAP[s]) > 0


def test_common_given_syllables():
    from engine.divination.name_hangul_hanja import HANGUL_HANJA_MAP
    for s in ("성", "민", "재", "훈", "현", "지", "수", "은", "혜"):
        assert s in HANGUL_HANJA_MAP


# ─────────────────────────── 단일 음절 조회 ───────────────────────────

def test_get_candidates_known():
    from engine.divination.name_hangul_hanja import get_candidates
    c = get_candidates("성")
    assert "誠" in c
    assert "城" in c
    assert "聖" in c


def test_get_candidates_unknown():
    from engine.divination.name_hangul_hanja import get_candidates
    assert get_candidates("쀍") == []  # 존재하지 않는 음절
    assert get_candidates("") == []


def test_get_candidates_two_dueum_expansion():
    """두음법칙 자동 적용 — '유' → ['유', '류'] 후보."""
    from engine.divination.name_hangul_hanja import get_candidates
    c = get_candidates("유")
    # '유' 후보 + '류' 후보 모두 포함되어야
    assert "兪" in c or "裕" in c  # '유' 자체 후보
    # '류'의 후보(柳·劉·流)도 포함
    assert "柳" in c or "劉" in c or "流" in c


def test_get_candidates_no_duplicates():
    """중복 한자 제거."""
    from engine.divination.name_hangul_hanja import get_candidates
    c = get_candidates("성")
    assert len(c) == len(set(c))


# ─────────────────────────── 복성 ───────────────────────────

def test_double_surnames_known():
    """주요 복성."""
    from engine.divination.name_hangul_hanja import is_double_surname
    assert is_double_surname("남궁수") is True
    assert is_double_surname("황보영") is True
    assert is_double_surname("제갈공") is True
    assert is_double_surname("이성민") is False


def test_double_surnames_short_name():
    from engine.divination.name_hangul_hanja import is_double_surname
    assert is_double_surname("이") is False
    assert is_double_surname("") is False


# ─────────────────────────── 결정론 ───────────────────────────

def test_deterministic():
    from engine.divination.name_hangul_hanja import get_candidates
    a = get_candidates("성")
    b = get_candidates("성")
    assert a == b


# ─────────────────────────── name_gaeja와 통합 ───────────────────────────

def test_gaeja_works_with_real_dict():
    """name_gaeja가 본 사전으로 정상 동작."""
    from engine.divination.name_gaeja import find_gaeja_candidates
    from engine.divination.name_hangul_hanja import HANGUL_HANJA_MAP
    r = find_gaeja_candidates(
        surname_hanja="李",
        surname_korean="이",
        given_korean="성민",
        candidate_pool=HANGUL_HANJA_MAP,
        target_ohaeng="金",
        top_n=5,
    )
    assert r.total_combinations > 0
