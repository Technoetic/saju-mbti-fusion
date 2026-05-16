"""engine.divination.name_bulyong — 불용한자 DB 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 기본 조회 ───────────────────────────

def test_is_bulyong_known():
    from engine.divination.name_bulyong import is_bulyong
    # 보고서 §1 명시
    assert is_bulyong("星") is True
    assert is_bulyong("吉") is True
    assert is_bulyong("極") is True
    assert is_bulyong("錦") is True
    assert is_bulyong("敏") is True


def test_is_bulyong_unknown():
    from engine.divination.name_bulyong import is_bulyong
    assert is_bulyong("珹") is False
    assert is_bulyong("旻") is False
    assert is_bulyong("仁") is False
    assert is_bulyong("智") is False


def test_is_bulyong_empty_or_none():
    from engine.divination.name_bulyong import is_bulyong
    assert is_bulyong("") is False
    assert is_bulyong(" ") is False


def test_get_entry_with_reason():
    from engine.divination.name_bulyong import get_entry
    e = get_entry("星")
    assert e is not None
    assert e.char == "星"
    assert "단명" in e.reason or "고독" in e.reason
    assert e.source


def test_get_entry_unknown_returns_none():
    from engine.divination.name_bulyong import get_entry
    assert get_entry("珹") is None


# ─────────────────────────── 카테고리 ───────────────────────────

def test_categories_present():
    from engine.divination.name_bulyong import (
        list_by_category, CATEGORY_CELESTIAL, CATEGORY_DEATH,
        CATEGORY_TEMPER, CATEGORY_NUMBER,
    )
    # 천기(天/地/月/星) 카테고리에 최소 4개
    cel = list_by_category(CATEGORY_CELESTIAL)
    chars = {e.char for e in cel}
    assert "星" in chars
    assert "天" in chars
    assert "地" in chars
    assert "月" in chars

    # 죽음 카테고리
    death = list_by_category(CATEGORY_DEATH)
    assert any(e.char == "死" for e in death)


def test_celestial_is_star():
    """星은 천기 카테고리."""
    from engine.divination.name_bulyong import get_entry, CATEGORY_CELESTIAL
    assert get_entry("星").category == CATEGORY_CELESTIAL


def test_敏_is_temper():
    """敏(민첩할 민)은 성정 극단 — 인간관계 불화."""
    from engine.divination.name_bulyong import get_entry, CATEGORY_TEMPER
    assert get_entry("敏").category == CATEGORY_TEMPER


def test_吉_is_fortune_reverse():
    """吉(길할 길) — 좋은 글자가 역효과."""
    from engine.divination.name_bulyong import get_entry, CATEGORY_FORTUNE
    assert get_entry("吉").category == CATEGORY_FORTUNE


# ─────────────────────────── 이름 스캔 ───────────────────────────

def test_scan_name_clean():
    from engine.divination.name_bulyong import scan_name
    assert scan_name("李珹旻") == []  # 좋은 한자만


def test_scan_name_one_bulyong():
    from engine.divination.name_bulyong import scan_name
    r = scan_name("李星敏")
    chars = [e.char for e in r]
    assert "星" in chars
    assert "敏" in chars
    assert len(r) == 2


def test_scan_name_with_korean_and_space_ignored():
    """한글·공백은 무시, 한자만 검사."""
    from engine.divination.name_bulyong import scan_name
    r = scan_name("이 성민 星敏")
    chars = [e.char for e in r]
    assert "星" in chars
    assert "敏" in chars


def test_scan_name_duplicates():
    """같은 글자 두 번이면 두 항목."""
    from engine.divination.name_bulyong import scan_name
    r = scan_name("星星")
    assert len(r) == 2


def test_scan_name_non_string():
    from engine.divination.name_bulyong import scan_name
    assert scan_name(None) == []  # type: ignore[arg-type]
    assert scan_name(123) == []  # type: ignore[arg-type]


# ─────────────────────────── diagnose_name ───────────────────────────

def test_diagnose_clean_name():
    from engine.divination.name_bulyong import diagnose_name
    d = diagnose_name("李珹旻")
    assert d["has_bulyong"] is False
    assert d["bulyong_count"] == 0
    assert d["severity"] == "none"
    assert d["matched"] == []


def test_diagnose_one_bulyong_minor():
    from engine.divination.name_bulyong import diagnose_name
    d = diagnose_name("李星")
    assert d["has_bulyong"] is True
    assert d["bulyong_count"] == 1
    assert d["severity"] == "minor"
    assert d["matched"][0]["char"] == "星"


def test_diagnose_two_bulyong_major():
    from engine.divination.name_bulyong import diagnose_name
    d = diagnose_name("李星敏")
    assert d["bulyong_count"] == 2
    assert d["severity"] == "major"


def test_diagnose_severe():
    from engine.divination.name_bulyong import diagnose_name
    d = diagnose_name("星敏吉天")  # 4개
    assert d["bulyong_count"] >= 3
    assert d["severity"] == "severe"


def test_diagnose_includes_reason():
    """진단 결과에 흉화 사유가 포함되어 사용자에게 노출 가능."""
    from engine.divination.name_bulyong import diagnose_name
    d = diagnose_name("星")
    m = d["matched"][0]
    assert "char" in m and "category" in m and "reason" in m and "source" in m
    assert len(m["reason"]) > 0


# ─────────────────────────── 결정론 ───────────────────────────

def test_deterministic_same_input_same_output():
    from engine.divination.name_bulyong import diagnose_name
    a = diagnose_name("李星敏")
    b = diagnose_name("李星敏")
    assert a == b


# ─────────────────────────── 총량 ───────────────────────────

def test_total_count_at_least_70():
    """프론트 80자 + 보고서 12자 통합으로 70자 이상."""
    from engine.divination.name_bulyong import total_count
    assert total_count() >= 70


def test_all_entries_have_reason():
    from engine.divination.name_bulyong import all_entries
    for e in all_entries():
        assert e.char and e.category and e.reason
