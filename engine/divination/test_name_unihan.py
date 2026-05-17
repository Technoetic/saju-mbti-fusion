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


# ─────────────────────────── KCI 학설 매핑 (옵션 C, ADR-027) ───────────────────────────

def test_kci_total_count():
    """ADR-027 본문화 — KCI 학설 매핑 94자."""
    from engine.divination.name_unihan import total_with_kci
    assert total_with_kci() == 94


def test_kci_osang_mapping():
    """오상(五常) 5자 KCI 매핑 — 仁→목, 義→금, 禮→화, 智→수, 信→토."""
    from engine.divination.name_unihan import resource_ohaeng_kci
    assert resource_ohaeng_kci("仁") == "목"
    assert resource_ohaeng_kci("義") == "금"
    assert resource_ohaeng_kci("禮") == "화"
    assert resource_ohaeng_kci("信") == "토"


def test_kci_season_mapping():
    """계절 4자 KCI 매핑 — 春→목, 夏→화, 秋→금, 冬→수."""
    from engine.divination.name_unihan import resource_ohaeng_kci
    assert resource_ohaeng_kci("春") == "목"
    assert resource_ohaeng_kci("夏") == "화"
    assert resource_ohaeng_kci("秋") == "금"
    assert resource_ohaeng_kci("冬") == "수"


def test_kci_direction_mapping():
    """방위 4자 KCI 매핑 — 東→목, 南→화, 西→금, 北→수."""
    from engine.divination.name_unihan import resource_ohaeng_kci
    assert resource_ohaeng_kci("東") == "목"
    assert resource_ohaeng_kci("南") == "화"
    assert resource_ohaeng_kci("西") == "금"
    assert resource_ohaeng_kci("北") == "수"


def test_kci_unknown_returns_none():
    """KCI 미수록 한자는 None."""
    from engine.divination.name_unihan import resource_ohaeng_kci
    # 林은 KCI 94자에 없음 (radical 자동 매핑만 보유)
    assert resource_ohaeng_kci("林") is None
    assert resource_ohaeng_kci("") is None


def test_kci_reason_and_source():
    """KCI 매핑은 reason + school_source 동반 (ADR-010 사실성 분리)."""
    from engine.divination.name_unihan import kci_reason, kci_school_source
    # 仁: 목 (오상)
    r = kci_reason("仁")
    s = kci_school_source("仁")
    assert r is not None and "오상" in r and "목" in r
    assert s is not None and ("김기승" in s or "이재승" in s or "김만태" in s)


def test_kci_reason_missing():
    """KCI 미수록은 reason도 None."""
    from engine.divination.name_unihan import kci_reason, kci_school_source
    assert kci_reason("林") is None
    assert kci_school_source("林") is None


def test_preferred_ohaeng_kci_priority():
    """preferred_ohaeng — KCI 매핑 있으면 우선, 없으면 부수 매핑."""
    from engine.divination.name_unihan import preferred_ohaeng, resource_ohaeng
    # 仁: 부수=수(부수 9 사람) vs KCI=목(오상) → KCI 우선
    assert preferred_ohaeng("仁") == "목"
    # 林: KCI 없음, 부수 매핑(목) → 부수 매핑
    assert preferred_ohaeng("林") == "목"
    # 한자 미수록
    assert preferred_ohaeng("쀍") is None


def test_kci_conflict_with_radical_documented():
    """옵션 A 부수 vs 옵션 C KCI 충돌 6건 — 명시 보존."""
    from engine.divination.name_unihan import resource_ohaeng, resource_ohaeng_kci
    # 보고서 §6 disputed 영역과 별개로, 본문화 시 충돌 검출된 6자
    conflicts = ["仁", "信", "誠", "春", "暗", "作"]
    for c in conflicts:
        radical = resource_ohaeng(c)
        kci = resource_ohaeng_kci(c)
        assert radical is not None, f"{c}: 부수 매핑 부재"
        assert kci is not None, f"{c}: KCI 매핑 부재"
        assert radical != kci, f"{c}: 충돌 없음 (radical={radical}, kci={kci})"


def test_kci_deterministic():
    """KCI 조회 결정론."""
    from engine.divination.name_unihan import resource_ohaeng_kci, kci_reason
    assert resource_ohaeng_kci("禮") == resource_ohaeng_kci("禮")
    assert kci_reason("禮") == kci_reason("禮")


def test_kci_school_source_format():
    """학파 출처 표기 일관성 — '이름(연도)' 패턴."""
    from engine.divination.name_unihan import _load_db
    db = _load_db()
    valid_authors = {"김기승", "이재승", "김만태"}
    kci_entries = [e for e in db.values() if e.get("resource_ohaeng_kci")]
    assert len(kci_entries) == 94
    for e in kci_entries:
        s = e.get("kci_school_source", "")
        # 학파 이름 최소 1건 포함
        assert any(a in s for a in valid_authors), f"{e['char']}: 학파 출처 누락 ({s!r})"


def test_kci_ohaeng_valid_korean():
    """KCI 자원오행은 한글 1자 (목·화·토·금·수)."""
    from engine.divination.name_unihan import _load_db
    valid = {"목", "화", "토", "금", "수"}
    db = _load_db()
    for e in db.values():
        kci = e.get("resource_ohaeng_kci", "")
        if kci:
            assert kci in valid, f"{e['char']}: 비표준 KCI 값 ({kci!r})"


# ─────────────────────────── ADR-010 사용자 출력 면책 ───────────────────────────

def test_kci_disclosure_pattern():
    """KCI 매핑 사용 시 학파 이견 명시 자동 검증.

    사용자 출력 단에서 KCI 매핑을 표시할 때 학파 출처 + 부수 매핑 충돌
    여부 동반 노출 가능한지 데이터 보유 확인 (실 출력은 web/ 단에서).
    """
    from engine.divination.name_unihan import (
        resource_ohaeng_kci, kci_school_source, resource_ohaeng,
    )
    # 仁 — 충돌자: 사용자 출력에 두 매핑 동시 노출 가능
    kci = resource_ohaeng_kci("仁")
    radical = resource_ohaeng("仁")
    source = kci_school_source("仁")
    assert kci == "목"
    assert radical == "수"
    assert source  # 학파 출처 존재 → 사용자에게 학파 명시 가능
