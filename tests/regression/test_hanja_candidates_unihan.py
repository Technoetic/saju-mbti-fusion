"""한자 후보(candidates_by_ko) — Unihan 9,932자 보강 회귀.

배경: 기존 candidates_by_ko()는 하드코딩 HANJA_LIST(394자)만 써서
대법원 인명용 한자 96%가 후보에서 누락됐다(예: 攸/유). Unihan 풀로 보강 후
(a) 攸가 후보로 나오고 (b) 기존 하드코딩 후보는 보존되며 (c) 각 후보가
획수를 갖는지 검증한다.
"""
from engine.saju.hanja_data import candidates_by_ko, lookup_han


def _hans(ko):
    return [c["han"] for c in candidates_by_ko(ko)]


def test_yu_includes_attribute_char():
    """攸(유)가 후보에 포함된다 — 본 버그의 직접 재현."""
    cands = candidates_by_ko("유")
    hans = [c["han"] for c in cands]
    assert "攸" in hans, f"攸 누락: {hans[:20]}"
    entry = next(c for c in cands if c["han"] == "攸")
    assert entry["strokes"] == 7
    assert entry["ko"] == "유"


def test_yu_pool_is_rich():
    """유 후보가 하드코딩 7자보다 대폭 풍부해진다 (Unihan 보강)."""
    assert len(candidates_by_ko("유")) >= 50


def test_hardcoded_candidates_preserved():
    """기존 하드코딩 후보가 보존된다 (회귀 방지)."""
    yu = _hans("유")
    for h in ["柳", "有", "裕", "悠"]:  # HANJA_LIST에 있던 유 한자
        assert h in yu, f"하드코딩 후보 {h} 유실"


def test_every_candidate_has_strokes():
    """모든 후보는 획수를 갖는다 (작명 계산 가능 조건)."""
    for ko in ["유", "민", "서", "준"]:
        for c in candidates_by_ko(ko):
            assert c.get("strokes"), f"{ko}/{c['han']} 획수 없음"


def test_common_syllables_expanded():
    """자주 쓰는 인명 음절이 모두 확장된다."""
    for ko, minimum in [("민", 20), ("서", 30), ("지", 40), ("우", 40)]:
        n = len(candidates_by_ko(ko))
        assert n >= minimum, f"{ko}: {n}자 (기대 ≥{minimum})"


def test_no_duplicate_hans():
    """후보에 중복 한자가 없다 (하드코딩+Unihan 병합 시 dedup)."""
    for ko in ["유", "민", "준"]:
        hans = _hans(ko)
        assert len(hans) == len(set(hans)), f"{ko} 중복: {hans}"


def test_lookup_han_falls_back_to_unihan():
    """lookup_han이 하드코딩에 없는 한자도 Unihan으로 조회한다."""
    e = lookup_han("攸")
    assert e is not None
    assert e["strokes"] == 7
    assert e["ko"] == "유"


def test_empty_input():
    assert candidates_by_ko("") == []
    assert candidates_by_ko("   ") == []
