"""engine.divination.name_dueum — 두음법칙 매핑 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 보고서 §4 명시 예시 ───────────────────────────

def test_보고서_예시_柳_류_to_유():
    """柳(버들 류) — 두음법칙으로 '유'로 등록."""
    from engine.divination.name_dueum import apply_dueum
    assert apply_dueum("류") == "유"


def test_보고서_예시_羅_라_to_나():
    from engine.divination.name_dueum import apply_dueum
    assert apply_dueum("라") == "나"


# ─────────────────────────── ㄹ → ㅇ ───────────────────────────

def test_ra_series_to_na():
    from engine.divination.name_dueum import apply_dueum
    assert apply_dueum("라") == "나"
    assert apply_dueum("락") == "낙"
    assert apply_dueum("람") == "남"
    assert apply_dueum("랑") == "낭"


def test_ryu_series_to_yu():
    from engine.divination.name_dueum import apply_dueum
    assert apply_dueum("류") == "유"
    assert apply_dueum("리") == "이"
    assert apply_dueum("림") == "임"
    assert apply_dueum("립") == "입"


def test_lyo_series_to_yo():
    from engine.divination.name_dueum import apply_dueum
    assert apply_dueum("료") == "요"
    assert apply_dueum("룡") == "용"


def test_ryeo_series_to_yeo():
    from engine.divination.name_dueum import apply_dueum
    assert apply_dueum("려") == "여"
    assert apply_dueum("련") == "연"
    assert apply_dueum("렬") == "열"
    assert apply_dueum("령") == "영"


# ─────────────────────────── ㄴ → ㅇ ───────────────────────────

def test_n_yi_to_i():
    from engine.divination.name_dueum import apply_dueum
    assert apply_dueum("니") == "이"
    assert apply_dueum("녀") == "여"
    assert apply_dueum("녕") == "영"


# ─────────────────────────── 변환 대상 아닌 음절 ───────────────────────────

def test_non_target_passthrough():
    from engine.divination.name_dueum import apply_dueum
    # ㄱ/ㅁ/ㅅ 등 시작은 그대로
    assert apply_dueum("김") == "김"
    assert apply_dueum("박") == "박"
    assert apply_dueum("성") == "성"
    # 모음으로 시작 — 그대로
    assert apply_dueum("이") == "이"
    assert apply_dueum("아") == "아"


def test_empty_or_none_safe():
    from engine.divination.name_dueum import apply_dueum
    assert apply_dueum("") == ""
    assert apply_dueum(None) == ""  # type: ignore[arg-type]


# ─────────────────────────── 역매핑 ───────────────────────────

def test_reverse_dueum_yi_to_three_origins():
    """'이' → ['이', '리', '니'] — 두음 표기에서 원음 후보."""
    from engine.divination.name_dueum import reverse_dueum
    c = reverse_dueum("이")
    assert "이" in c
    assert "리" in c
    assert "니" in c


def test_reverse_dueum_na_to_ra():
    """'나' → ['나', '라']."""
    from engine.divination.name_dueum import reverse_dueum
    c = reverse_dueum("나")
    assert "나" in c
    assert "라" in c


def test_reverse_dueum_no_change():
    """'김' → ['김']만."""
    from engine.divination.name_dueum import reverse_dueum
    assert reverse_dueum("김") == ["김"]


# ─────────────────────────── is_dueum_target ───────────────────────────

def test_is_dueum_target():
    from engine.divination.name_dueum import is_dueum_target
    assert is_dueum_target("류") is True
    assert is_dueum_target("라") is True
    assert is_dueum_target("니") is True
    assert is_dueum_target("김") is False
    assert is_dueum_target("이") is False  # 이미 두음 적용된 표기


# ─────────────────────────── 검색 정규화 ───────────────────────────

def test_normalize_for_search():
    """원음·두음 어느 쪽으로 입력해도 같은 키로 정규화."""
    from engine.divination.name_dueum import normalize_for_search
    # '류'와 '유' 둘 다 '유'로 정규화
    assert normalize_for_search("류") == "유"
    assert normalize_for_search("유") == "유"
    # '리'와 '이' 둘 다 '이'로
    assert normalize_for_search("리") == "이"
    assert normalize_for_search("이") == "이"


def test_expand_search_candidates_yi():
    """'유' 입력 시 ['유', '류'] 모두 후보로."""
    from engine.divination.name_dueum import expand_search_candidates
    c = expand_search_candidates("유")
    assert "유" in c
    assert "류" in c


def test_expand_search_candidates_yu_from_origin():
    """'류' 입력 시 ['류', '유'] 모두."""
    from engine.divination.name_dueum import expand_search_candidates
    c = expand_search_candidates("류")
    assert "류" in c
    assert "유" in c


def test_expand_search_candidates_yi_full():
    """'이' → ['이', '리', '니'] 3개."""
    from engine.divination.name_dueum import expand_search_candidates
    c = expand_search_candidates("이")
    assert set(c) >= {"이", "리", "니"}


# ─────────────────────────── 결정론 ───────────────────────────

def test_deterministic():
    from engine.divination.name_dueum import apply_dueum
    assert apply_dueum("류") == apply_dueum("류")


def test_total_mappings_at_least_30():
    """매핑이 ㄹ+ㄴ 합쳐 30개 이상."""
    from engine.divination.name_dueum import total_mappings
    assert total_mappings() >= 30
