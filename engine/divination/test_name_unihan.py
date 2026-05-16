"""engine.divination.name_unihan — Unihan 자동 매핑 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 데이터 로드 ───────────────────────────

def test_db_loaded():
    from engine.divination.name_unihan import is_loaded, total_chars
    assert is_loaded() is True
    assert total_chars() >= 8000


def test_with_ohaeng_count():
    """자원오행 자동 매핑 — 부수 기반으로 일부."""
    from engine.divination.name_unihan import total_with_ohaeng, total_chars
    matched = total_with_ohaeng()
    total = total_chars()
    # 30~60% 사이 자동 매핑되어야
    assert 0.30 <= matched / total <= 0.70


# ─────────────────────────── 강희자전 원획 ───────────────────────────

def test_kangxi_strokes_known():
    from engine.divination.name_unihan import kangxi_strokes
    assert kangxi_strokes("星") == 9
    assert kangxi_strokes("李") == 7
    assert kangxi_strokes("金") == 8


def test_kangxi_strokes_unknown():
    from engine.divination.name_unihan import kangxi_strokes
    assert kangxi_strokes("龘") is None  # 흔치 않은 한자도 있을 수 있음
    assert kangxi_strokes("") is None
    assert kangxi_strokes(None) is None  # type: ignore[arg-type]


# ─────────────────────────── 한국어 음 ───────────────────────────

def test_hangul_of():
    from engine.divination.name_unihan import hangul_of
    assert hangul_of("星") == "성"
    assert hangul_of("金") in ("금", "김")  # 다음(多音)
    assert hangul_of("李") == "리"  # 두음법칙 전 원음


def test_hangul_of_unknown():
    from engine.divination.name_unihan import hangul_of
    assert hangul_of("") is None


# ─────────────────────────── 부수 ───────────────────────────

def test_radical_of():
    from engine.divination.name_unihan import radical_of
    # 星 부수 = 72 (日)
    assert radical_of("星") == 72
    # 木 부수 = 75 (木 자기 자신)
    assert radical_of("木") == 75


# ─────────────────────────── 자원오행 (부수 기반) ───────────────────────────

def test_ohaeng_wood():
    """木 부수 한자 — 자원오행 木."""
    from engine.divination.name_unihan import resource_ohaeng
    # 林은 木 부수
    assert resource_ohaeng("林") == "목"


def test_ohaeng_water():
    """水/雨 부수 한자."""
    from engine.divination.name_unihan import resource_ohaeng
    assert resource_ohaeng("水") == "수"


def test_ohaeng_manual_override():
    """수동 보정 한자 (李·金 등)."""
    from engine.divination.name_unihan import resource_ohaeng
    assert resource_ohaeng("李") == "목"
    assert resource_ohaeng("金") == "금"


# ─────────────────────────── 한글 → 한자 후보 ───────────────────────────

def test_get_candidates_seong():
    """'성' 음 한자 후보."""
    from engine.divination.name_unihan import get_candidates_by_hangul
    c = get_candidates_by_hangul("성")
    assert "星" in c
    assert "誠" in c
    assert "城" in c
    # Unihan은 더 많은 한자 — 20+ 자
    assert len(c) >= 10


def test_get_candidates_empty():
    from engine.divination.name_unihan import get_candidates_by_hangul
    assert get_candidates_by_hangul("쀍") == []
    assert get_candidates_by_hangul("") == []


# ─────────────────────────── name_strokes fallback ───────────────────────────

def test_name_strokes_fallback_to_unihan():
    """수동 표 미수록 한자 → Unihan에서 매핑."""
    from engine.divination.name_strokes import kangxi_strokes
    # 鴻(기러기 홍) — 수동 표 미수록일 수 있음
    val = kangxi_strokes("鴻")
    assert val is not None
    assert val > 0


def test_name_strokes_manual_priority():
    """수동 표가 있으면 우선 — 花는 보정된 10획."""
    from engine.divination.name_strokes import kangxi_strokes
    assert kangxi_strokes("花") == 10  # Unihan은 7이지만 수동 표 우선


# ─────────────────────────── 결정론 ───────────────────────────

def test_deterministic():
    from engine.divination.name_unihan import kangxi_strokes, get_candidates_by_hangul
    assert kangxi_strokes("星") == kangxi_strokes("星")
    assert get_candidates_by_hangul("성") == get_candidates_by_hangul("성")
