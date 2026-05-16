"""engine.divination.name_strokes — 강희자전 원획수 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 변형 부수 8종 ───────────────────────────

def test_radical_variants_8_present():
    """보고서 §2 명시 변형 부수 8종 모두 매핑되어야."""
    from engine.divination.name_strokes import RADICAL_VARIANTS
    for v in ("氵", "忄", "扌", "艹", "衤", "罒", "耂"):
        assert v in RADICAL_VARIANTS
    # 月은 의도적 제외 (육변 구분 불가)


def test_radical_variant_삼수변_to_水():
    from engine.divination.name_strokes import RADICAL_VARIANTS
    assert RADICAL_VARIANTS["氵"] == ("水", 4)


def test_radical_variant_초두머리_to_艸():
    from engine.divination.name_strokes import RADICAL_VARIANTS
    assert RADICAL_VARIANTS["艹"] == ("艸", 6)


# ─────────────────────────── 보고서 §2 정확도 검증 ───────────────────────────

def test_보고서_예시_花_is_10():
    """보고서 §2 예시: 花(꽃 화)는 강희자전 10획 (필획 7 → 艹+化=艸 6 + 化 4)."""
    from engine.divination.name_strokes import kangxi_strokes, writing_strokes
    assert kangxi_strokes("花") == 10
    assert writing_strokes("花") == 7  # 일반 필획


def test_氵_보정_江():
    """江(강) — 필획 6 → 원획 7 (氵 3 → 水 4 보정)."""
    from engine.divination.name_strokes import kangxi_strokes, writing_strokes
    assert writing_strokes("江") == 6
    assert kangxi_strokes("江") == 7


def test_氵_보정_洪():
    """洪 — 氵 보정."""
    from engine.divination.name_strokes import kangxi_strokes
    assert kangxi_strokes("洪") == 10


def test_艸_보정_萬():
    """萬 — 艹 보정."""
    from engine.divination.name_strokes import kangxi_strokes
    assert kangxi_strokes("萬") == 15


# ─────────────────────────── 자원오행 ───────────────────────────

def test_resource_ohaeng_known():
    from engine.divination.name_strokes import resource_ohaeng
    assert resource_ohaeng("木") == "木"
    assert resource_ohaeng("水") == "水"
    assert resource_ohaeng("李") == "木"
    assert resource_ohaeng("金") == "金"


def test_resource_ohaeng_unknown():
    from engine.divination.name_strokes import resource_ohaeng
    assert resource_ohaeng("龘") is None
    assert resource_ohaeng("") is None


# ─────────────────────────── 미수록 처리 ───────────────────────────

def test_kangxi_strokes_unknown_returns_none():
    from engine.divination.name_strokes import kangxi_strokes
    assert kangxi_strokes("龘") is None
    assert kangxi_strokes("") is None


def test_writing_strokes_unknown_returns_none():
    from engine.divination.name_strokes import writing_strokes
    assert writing_strokes("龘") is None


# ─────────────────────────── 이름 합계 ───────────────────────────

def test_total_strokes_korean_name():
    """이성민 (李星敏) 원획 합계."""
    from engine.divination.name_strokes import total_strokes
    r = total_strokes("李星敏")
    assert r["chars"] == ["李", "星", "敏"]
    assert r["kangxi"] == [7, 9, 11]
    assert r["kangxi_total"] == 27
    assert r["missing"] == []


def test_total_strokes_with_missing():
    """미수록 한자 포함 시 missing 리스트에 표시, 합계는 알려진 것만."""
    from engine.divination.name_strokes import total_strokes
    r = total_strokes("李龘")
    assert r["kangxi"] == [7, None]
    assert "龘" in r["missing"]
    assert r["kangxi_total"] == 7  # 알려진 것만


def test_total_strokes_empty():
    from engine.divination.name_strokes import total_strokes
    r = total_strokes("")
    assert r["chars"] == []
    assert r["kangxi_total"] == 0


# ─────────────────────────── 결정론 ───────────────────────────

def test_deterministic():
    from engine.divination.name_strokes import total_strokes
    a = total_strokes("李珹旻")
    b = total_strokes("李珹旻")
    assert a == b


# ─────────────────────────── 총량 ───────────────────────────

def test_at_least_200_chars():
    """자주 쓰는 인명용 한자 200자 이상 수록."""
    from engine.divination.name_strokes import total_count
    assert total_count() >= 200


# ─────────────────────────── 성씨 정확도 (10대 성씨) ───────────────────────────

def test_top_10_surnames_present():
    from engine.divination.name_strokes import kangxi_strokes
    for s in ("李", "金", "朴", "崔", "鄭", "姜", "趙", "尹", "張", "林"):
        assert kangxi_strokes(s) is not None, f"성씨 {s} 미수록"
