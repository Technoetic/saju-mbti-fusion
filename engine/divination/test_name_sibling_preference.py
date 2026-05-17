"""engine.divination.name_sibling_preference — 회귀 테스트.

ADR-010 사실성 분리 원칙 검증 포함:
  · 사용자 메시지에 인과적 흉화 표현 없음
  · 의료·법률 자문 면책 포함
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 데이터 무결성 ───────────────────────────


def test_data_loads():
    from engine.divination.name_sibling_preference import total_entries, lookup
    assert total_entries() == 125
    # 백중숙계 4자 모두 등록
    assert lookup("伯") is not None
    assert lookup("仲") is not None
    assert lookup("叔") is not None
    assert lookup("季") is not None


def test_baekjungsukgye_categories():
    """伯·仲·叔·季의 카테고리 매핑이 호칭 위계와 일치."""
    from engine.divination.name_sibling_preference import (
        lookup,
        CATEGORY_FIRSTBORN, CATEGORY_MIDDLEBORN, CATEGORY_LASTBORN,
    )
    assert lookup("伯").category == CATEGORY_FIRSTBORN
    assert lookup("仲").category == CATEGORY_MIDDLEBORN
    assert lookup("叔").category == CATEGORY_MIDDLEBORN
    assert lookup("季").category == CATEGORY_LASTBORN


# ─────────────────────────── 기본 매칭 ───────────────────────────


def test_firstborn_uses_firstborn_char_pass():
    """장남이 '元'(으뜸) 사용 → 적합."""
    from engine.divination.name_sibling_preference import diagnose_char
    d = diagnose_char("元", "firstborn")
    assert d.is_match is True
    assert d.severity is None


def test_middleborn_uses_firstborn_char_fail():
    """차남이 '甲'(천간 첫째) 사용 → 부적합 STRONG."""
    from engine.divination.name_sibling_preference import diagnose_char, SEVERITY_STRONG
    d = diagnose_char("甲", "middleborn", gender="male")
    assert d.is_match is False
    assert d.severity == SEVERITY_STRONG


def test_firstborn_uses_lastborn_char_fail():
    """장남이 '季'(막내) 사용 → 부적합."""
    from engine.divination.name_sibling_preference import diagnose_char, SEVERITY_STRONG
    d = diagnose_char("季", "firstborn")
    assert d.is_match is False
    assert d.severity == SEVERITY_STRONG


def test_lastborn_uses_lastborn_char_pass():
    """막내가 '季' 사용 → 적합."""
    from engine.divination.name_sibling_preference import diagnose_char
    d = diagnose_char("季", "lastborn")
    assert d.is_match is True


def test_unknown_char_pass():
    """DB 미등록 한자 → 부적합 아님."""
    from engine.divination.name_sibling_preference import diagnose_char
    d = diagnose_char("仁", "middleborn")
    assert d.is_match is True
    assert d.entry is None


# ─────────────────────────── 외동 정책 (1-D) ───────────────────────────


def test_only_child_uses_pass_glyph_match():
    """외동이 '壹' 사용 → 적합 (외동 전용 길자)."""
    from engine.divination.name_sibling_preference import diagnose_char
    d = diagnose_char("壹", "only_child")
    assert d.is_match is True


def test_sibling_uses_only_child_pass_glyph_fail():
    """다자녀 가정에서 '壹' 사용 → 부적합."""
    from engine.divination.name_sibling_preference import diagnose_char
    d = diagnose_char("壹", "firstborn")
    assert d.is_match is False


def test_only_child_uses_hard_block_glyph_fail():
    """외동이라도 '孤'(고아) 사용 → 부적합 (hard_block_always)."""
    from engine.divination.name_sibling_preference import diagnose_char, SEVERITY_STRONG
    d = diagnose_char("孤", "only_child")
    assert d.is_match is False
    assert d.severity == SEVERITY_STRONG


def test_only_child_skips_sibling_categories():
    """외동은 형제 호칭 카테고리(firstborn/lastborn/middleborn) 자체가 비적용 — 통과."""
    from engine.divination.name_sibling_preference import diagnose_char
    # 외동이 firstborn 한자 '元'을 사용해도 통과
    d = diagnose_char("元", "only_child")
    assert d.is_match is True
    # 외동이 lastborn 한자 '季'를 사용해도 통과
    d2 = diagnose_char("季", "only_child")
    assert d2.is_match is True


# ─────────────────────────── 현대 가정 예외 ───────────────────────────


def test_eldest_sister_with_older_brother_downcast():
    """여성 + 위에 오빠 1명 → firstborn에서 middleborn으로 downcast.

    이 경우 firstborn 전용 한자 '元' 사용 시 부적합으로 바뀌어야 함.
    """
    from engine.divination.name_sibling_preference import diagnose_char
    # 일반 firstborn 여성 → 適合
    d_normal = diagnose_char("元", "firstborn", gender="female")
    assert d_normal.is_match is True
    # 큰누나 (위 오빠 있음) → 不適合
    d_eldest_sister = diagnose_char(
        "元", "firstborn",
        gender="female",
        has_older_brother_as_female=True,
    )
    assert d_eldest_sister.is_match is False
    assert "eldest_sister_with_older_brother" in d_eldest_sister.applied_exceptions


def test_twin_severity_softened():
    """쌍둥이의 경우 STRONG → WEAK로 1단계 완화."""
    from engine.divination.name_sibling_preference import (
        diagnose_char, SEVERITY_STRONG, SEVERITY_WEAK,
    )
    # 일반 차남이 '甲' 사용 → STRONG
    d_normal = diagnose_char("甲", "middleborn", gender="male")
    assert d_normal.severity == SEVERITY_STRONG
    # 쌍둥이 차남(쌍둥이 둘째)이 '甲' 사용 → WEAK
    d_twin = diagnose_char("甲", "middleborn", gender="male", is_twin=True)
    assert d_twin.severity == SEVERITY_WEAK
    assert "twin_severity_softened" in d_twin.applied_exceptions


def test_adopted_uses_legal_order_flag():
    """입양아: 입력 sibling_order(호적 서열)를 그대로 신뢰, 플래그 표시."""
    from engine.divination.name_sibling_preference import diagnose_char
    d = diagnose_char("元", "firstborn", is_adopted=True)
    assert d.is_match is True
    assert "adopted_uses_legal_order" in d.applied_exceptions


def test_blended_cohabiting_flag():
    """재혼+이복 동거 플래그 표시."""
    from engine.divination.name_sibling_preference import diagnose_char
    d = diagnose_char("元", "firstborn", is_blended_cohabiting=True)
    assert "blended_cohabiting" in d.applied_exceptions


# ─────────────────────────── ADR-010 사실성 분리 검증 ───────────────────────────


def test_user_message_no_causal_harm():
    """사용자 메시지에 인과적 흉화 표현이 없는지 검증."""
    from engine.divination.name_sibling_preference import diagnose_char
    forbidden = [
        "단명", "요절", "사망", "혈관", "관절", "신체 훼손",
        "관재구설", "감금", "법적 분쟁",
        "이혼", "과부", "파경",
        "기운 역행", "우주적", "파동",
    ]
    # 차남이 '甲' 사용 → STRONG 부적합 케이스
    d = diagnose_char("甲", "middleborn", gender="male")
    msg = d.user_message
    for word in forbidden:
        assert word not in msg, f"금지 표현 '{word}'가 메시지에 포함됨: {msg}"


def test_user_message_contains_disclaimer():
    """STRONG 부적합 메시지에 의료·법률 면책 포함."""
    from engine.divination.name_sibling_preference import diagnose_char
    d = diagnose_char("甲", "middleborn", gender="male")
    assert "참고용" in d.user_message
    assert "의료·법률 자문이 아닙니다" in d.user_message


# ─────────────────────────── 이름 단위 진단 ───────────────────────────


def test_diagnose_name_all_pass():
    """장남 + 일반 한자 → 부적합 없음."""
    from engine.divination.name_sibling_preference import diagnose_name
    out = diagnose_name("仁智", "firstborn")
    assert out["any_mismatch"] is False
    assert "부적합 표시가 없습니다" in out["summary"]


def test_diagnose_name_with_strong_mismatch():
    """차남 + '甲' 포함 이름 → any_strong_mismatch True."""
    from engine.divination.name_sibling_preference import diagnose_name
    out = diagnose_name("甲秀", "middleborn", gender="male")
    assert out["any_strong_mismatch"] is True


def test_diagnose_name_summary_no_causal_harm():
    """이름 요약 문구에도 인과 표현 금지."""
    from engine.divination.name_sibling_preference import diagnose_name
    forbidden = ["단명", "요절", "사망", "이혼", "관재"]
    for so in ("firstborn", "middleborn", "lastborn", "only_child"):
        out = diagnose_name("甲季孤", so, gender="male")
        for w in forbidden:
            assert w not in out["summary"], f"{so} summary: {out['summary']}"
