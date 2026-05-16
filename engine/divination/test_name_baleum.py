"""engine.divination.name_baleum — 발음오행 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 초성 추출 ───────────────────────────

def test_extract_chosung():
    from engine.divination.name_baleum import extract_chosung
    assert extract_chosung("이") == "ㅇ"
    assert extract_chosung("성") == "ㅅ"
    assert extract_chosung("민") == "ㅁ"
    assert extract_chosung("김") == "ㄱ"
    assert extract_chosung("박") == "ㅂ"
    assert extract_chosung("최") == "ㅊ"


def test_extract_chosung_non_hangul():
    from engine.divination.name_baleum import extract_chosung
    assert extract_chosung("A") == ""
    assert extract_chosung("") == ""
    assert extract_chosung("李") == ""  # 한자도 빈


# ─────────────────────────── 초성 → 오행 ───────────────────────────

def test_chosung_wood():
    from engine.divination.name_baleum import chosung_to_ohaeng, WOOD
    assert chosung_to_ohaeng("ㄱ") == WOOD
    assert chosung_to_ohaeng("ㅋ") == WOOD


def test_chosung_fire():
    from engine.divination.name_baleum import chosung_to_ohaeng, FIRE
    assert chosung_to_ohaeng("ㄴ") == FIRE
    assert chosung_to_ohaeng("ㄷ") == FIRE
    assert chosung_to_ohaeng("ㄹ") == FIRE
    assert chosung_to_ohaeng("ㅌ") == FIRE


def test_chosung_earth():
    from engine.divination.name_baleum import chosung_to_ohaeng, EARTH
    assert chosung_to_ohaeng("ㅇ") == EARTH
    assert chosung_to_ohaeng("ㅎ") == EARTH


def test_chosung_metal():
    from engine.divination.name_baleum import chosung_to_ohaeng, METAL
    assert chosung_to_ohaeng("ㅅ") == METAL
    assert chosung_to_ohaeng("ㅈ") == METAL
    assert chosung_to_ohaeng("ㅊ") == METAL


def test_chosung_water():
    from engine.divination.name_baleum import chosung_to_ohaeng, WATER
    assert chosung_to_ohaeng("ㅁ") == WATER
    assert chosung_to_ohaeng("ㅂ") == WATER
    assert chosung_to_ohaeng("ㅍ") == WATER


# ─────────────────────────── 음절 → 오행 ───────────────────────────

def test_syllable_to_ohaeng():
    from engine.divination.name_baleum import syllable_to_ohaeng, EARTH, METAL, WATER
    assert syllable_to_ohaeng("이") == EARTH
    assert syllable_to_ohaeng("성") == METAL
    assert syllable_to_ohaeng("민") == WATER


# ─────────────────────────── 상생·상극 관계 ───────────────────────────

def test_relation_sangsaeng_forward():
    """木→火 상생."""
    from engine.divination.name_baleum import relation, WOOD, FIRE
    assert relation(WOOD, FIRE) == "sangsaeng"


def test_relation_sangsaeng_chain():
    """五行 상생 사슬: 木→火→土→金→水→木."""
    from engine.divination.name_baleum import relation, WOOD, FIRE, EARTH, METAL, WATER
    assert relation(WOOD, FIRE) == "sangsaeng"
    assert relation(FIRE, EARTH) == "sangsaeng"
    assert relation(EARTH, METAL) == "sangsaeng"
    assert relation(METAL, WATER) == "sangsaeng"
    assert relation(WATER, WOOD) == "sangsaeng"


def test_relation_sanggeuk():
    """五行 상극: 木→土, 火→金, 土→水, 金→木, 水→火."""
    from engine.divination.name_baleum import relation, WOOD, FIRE, EARTH, METAL, WATER
    assert relation(WOOD, EARTH) == "sanggeuk"
    assert relation(FIRE, METAL) == "sanggeuk"
    assert relation(WATER, FIRE) == "sanggeuk"


def test_relation_bihwa():
    from engine.divination.name_baleum import relation, WOOD
    assert relation(WOOD, WOOD) == "bihwa"


# ─────────────────────────── 이름 평가 ───────────────────────────

def test_evaluate_이성민_metal_earth_water():
    """이성민 — ㅇ(土) → ㅅ(金) → ㅁ(水) — 모두 상생 GOOD."""
    from engine.divination.name_baleum import evaluate_baleum, EARTH, METAL, WATER, GRADE_GOOD
    r = evaluate_baleum("이성민")
    assert r.ohaeng_sequence == [EARTH, METAL, WATER]
    assert r.grade == GRADE_GOOD


def test_evaluate_김민수_wood_water_metal():
    """김민수 — ㄱ(木) → ㅁ(水) → ㅅ(金).
    木-水 상생(반대 방향 - 水→木이 상생, 木→水는 sangsaeng_reverse) — 상생 X
    水-金 sangsaeng_reverse (金→水 상생).
    상극 없음 → NEUTRAL.
    """
    from engine.divination.name_baleum import evaluate_baleum, GRADE_NEUTRAL
    r = evaluate_baleum("김민수")
    assert r.grade == GRADE_NEUTRAL


def test_evaluate_sanggeuk_bad():
    """ㄱ(木) → ㅇ(土) → ... — 木→土 상극."""
    from engine.divination.name_baleum import evaluate_baleum, GRADE_BAD
    r = evaluate_baleum("강안")
    assert r.grade == GRADE_BAD


def test_evaluate_empty():
    from engine.divination.name_baleum import evaluate_baleum, GRADE_NEUTRAL
    r = evaluate_baleum("")
    assert r.grade == GRADE_NEUTRAL


def test_evaluate_single_syllable():
    from engine.divination.name_baleum import evaluate_baleum, GRADE_NEUTRAL
    r = evaluate_baleum("이")
    assert r.grade == GRADE_NEUTRAL


# ─────────────────────────── 결정론 ───────────────────────────

def test_deterministic():
    from engine.divination.name_baleum import evaluate_baleum
    a = evaluate_baleum("이성민")
    b = evaluate_baleum("이성민")
    assert a.grade == b.grade


# ─────────────────────────── 직렬화 ───────────────────────────

def test_report_to_dict():
    from engine.divination.name_baleum import evaluate_baleum, report_to_dict
    d = report_to_dict(evaluate_baleum("이성민"))
    for k in ("syllables", "ohaeng_sequence", "relations", "grade", "reason"):
        assert k in d


# ─────────────────────────── 종성(받침) 보강 ───────────────────────────

def test_extract_jongsung():
    """종성 추출 — 받침 있는 음절."""
    from engine.divination.name_baleum import extract_jongsung
    assert extract_jongsung("성") == "ㅇ"
    assert extract_jongsung("민") == "ㄴ"
    assert extract_jongsung("김") == "ㅁ"
    assert extract_jongsung("박") == "ㄱ"


def test_extract_jongsung_no_batchim():
    """받침 없으면 빈 문자열."""
    from engine.divination.name_baleum import extract_jongsung
    assert extract_jongsung("이") == ""
    assert extract_jongsung("아") == ""
    assert extract_jongsung("나") == ""


def test_extract_jongsung_complex_batchim():
    """겹받침은 대표 자음으로 정규화."""
    from engine.divination.name_baleum import extract_jongsung
    # 닭(ㄺ → ㄹ), 값(ㅄ → ㅂ)
    assert extract_jongsung("닭") == "ㄹ"
    assert extract_jongsung("값") == "ㅂ"


def test_jongsung_to_ohaeng():
    """종성 → 오행 매핑."""
    from engine.divination.name_baleum import jongsung_to_ohaeng, EARTH, FIRE, WATER
    assert jongsung_to_ohaeng("ㅇ") == EARTH
    assert jongsung_to_ohaeng("ㄴ") == FIRE
    assert jongsung_to_ohaeng("ㅁ") == WATER
    assert jongsung_to_ohaeng("") == ""


def test_syllable_to_ohaeng_pair():
    """음절 → (초성, 종성) 오행 페어."""
    from engine.divination.name_baleum import syllable_to_ohaeng_pair
    # 성: ㅅ(金) + ㅇ(土)
    assert syllable_to_ohaeng_pair("성") == ("금", "토")
    # 이: ㅇ(土) + 받침 없음
    assert syllable_to_ohaeng_pair("이") == ("토", "")
    # 민: ㅁ(水) + ㄴ(火)
    assert syllable_to_ohaeng_pair("민") == ("수", "화")


def test_evaluate_with_jongsung_extends_sequence():
    """include_jongsung=True면 시퀀스 길이가 확장됨."""
    from engine.divination.name_baleum import evaluate_baleum
    r_no = evaluate_baleum("이성민", include_jongsung=False)
    r_with = evaluate_baleum("이성민", include_jongsung=True)
    # 이=받침X, 성=ㅇ받침, 민=ㄴ받침 → 종성 2개 추가 = 시퀀스 5
    assert len(r_no.ohaeng_sequence) == 3
    assert len(r_with.ohaeng_sequence) == 5


def test_evaluate_with_jongsung_이성민():
    """이성민 종성 포함: 토(이) → 금(ㅅ) → 토(ㅇ) → 수(ㅁ) → 화(ㄴ).
    토→금 상생, 금→토 sangsaeng_reverse, 토→수 상극!
    → BAD 등급.
    """
    from engine.divination.name_baleum import evaluate_baleum, GRADE_BAD
    r = evaluate_baleum("이성민", include_jongsung=True)
    # 상극이 들어가야
    assert any("sanggeuk" in rel for rel in r.relations)
    assert r.grade == GRADE_BAD
