"""crisis_detector 다국어 확장 회귀 테스트 — 영어·일본어.

40차에서 발견된 한계 (한국어만 지원) 보강.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 한국어 회귀 (변경 없음) ───────────────────────────

def test_korean_direct_suicide():
    from engine.safety import detect_crisis
    r = detect_crisis("죽고 싶다")
    assert r["crisis_detected"] is True
    assert r["severity"] in ("direct", "planning")


# ─────────────────────────── 영어 위기 키워드 ───────────────────────────

def test_english_want_to_die():
    from engine.safety import detect_crisis
    r = detect_crisis("I want to die")
    assert r["crisis_detected"] is True


def test_english_kill_myself():
    from engine.safety import detect_crisis
    r = detect_crisis("I want to kill myself")
    assert r["crisis_detected"] is True


def test_english_suicidal():
    from engine.safety import detect_crisis
    r = detect_crisis("I'm suicidal")
    assert r["crisis_detected"] is True


def test_english_no_reason_to_live():
    """간접 표현."""
    from engine.safety import detect_crisis
    r = detect_crisis("there is no reason to live anymore")
    assert r["crisis_detected"] is True
    assert r["severity"] == "indirect"


def test_english_case_insensitive():
    """대소문자 무관."""
    from engine.safety import detect_crisis
    assert detect_crisis("I WANT TO DIE")["crisis_detected"] is True
    assert detect_crisis("Want To Die")["crisis_detected"] is True


def test_english_dream_context_filtered():
    """'In my dream I want to die' → 꿈 컨텍스트 false positive 회피."""
    from engine.safety import detect_crisis
    r = detect_crisis("In my dream I want to die from heights")
    assert r["crisis_detected"] is False
    assert "want to die" in r["filtered_false_positives"]


def test_english_movie_context_filtered():
    """'In the movie character wants to die' → 미디어 인용 false positive."""
    from engine.safety import detect_crisis
    r = detect_crisis("In the movie character wants to die")
    # 매칭됐다면 부정 컨텍스트로 필터링되어야
    if r["matched_keywords"]:
        assert r["crisis_detected"] is False


def test_english_safe_text():
    """안전한 영어 텍스트는 위기 미감지."""
    from engine.safety import detect_crisis
    r = detect_crisis("I had a wonderful day today")
    assert r["crisis_detected"] is False


# ─────────────────────────── 일본어 위기 키워드 ───────────────────────────

def test_japanese_shinitai():
    from engine.safety import detect_crisis
    r = detect_crisis("死にたい")
    assert r["crisis_detected"] is True


def test_japanese_jisatsu():
    from engine.safety import detect_crisis
    r = detect_crisis("自殺を考えています")
    assert r["crisis_detected"] is True


def test_japanese_kieta():
    from engine.safety import detect_crisis
    r = detect_crisis("消えたい")
    assert r["crisis_detected"] is True


def test_japanese_indirect():
    """間接 — '生きる意味がない'."""
    from engine.safety import detect_crisis
    r = detect_crisis("もう生きる意味がない")
    assert r["crisis_detected"] is True


def test_japanese_safe_text():
    from engine.safety import detect_crisis
    r = detect_crisis("今日は良い天気です")
    assert r["crisis_detected"] is False


# ─────────────────────────── 혼합 / 통합 ───────────────────────────

def test_mixed_korean_english():
    """한·영 혼합 텍스트도 어느 한쪽 키워드 매칭이면 감지."""
    from engine.safety import detect_crisis
    r = detect_crisis("I want to die. 정말 너무 힘들어요.")
    assert r["crisis_detected"] is True


def test_planning_keyword_english():
    """행동·계획 신호 — suicide note."""
    from engine.safety import detect_crisis
    r = detect_crisis("I wrote a suicide note last night")
    assert r["crisis_detected"] is True
    assert r["severity"] == "planning"


# ─────────────────────────── 일본어 자해 (§5.2.7 보강) ───────────────────────────

def test_japanese_selfharm_rlsk():
    from engine.safety import detect_crisis
    r = detect_crisis("リスカしてしまった")
    assert r["crisis_detected"] is True


def test_japanese_overdose():
    from engine.safety import detect_crisis
    r = detect_crisis("薬を一気に飲みたい")
    assert r["crisis_detected"] is True


def test_japanese_planning_train():
    from engine.safety import detect_crisis
    r = detect_crisis("電車に飛び込もうかと考えている")
    assert r["crisis_detected"] is True
    assert r["severity"] == "planning"


# ─────────────────────────── 중국어 위기 (§5.2.7 신규) ───────────────────────────

def test_chinese_simplified_suicide():
    from engine.safety import detect_crisis
    r = detect_crisis("我想自杀")
    assert r["crisis_detected"] is True


def test_chinese_traditional_suicide():
    from engine.safety import detect_crisis
    r = detect_crisis("我想自殺")
    assert r["crisis_detected"] is True


def test_chinese_want_to_die():
    from engine.safety import detect_crisis
    r = detect_crisis("我想死")
    assert r["crisis_detected"] is True


def test_chinese_cant_live():
    from engine.safety import detect_crisis
    r = detect_crisis("我活不下去了")
    assert r["crisis_detected"] is True


def test_chinese_self_harm():
    from engine.safety import detect_crisis
    r = detect_crisis("我想自残")
    assert r["crisis_detected"] is True


def test_chinese_indirect_no_hope():
    from engine.safety import detect_crisis
    r = detect_crisis("生活没有希望了")
    assert r["crisis_detected"] is True
    assert r["severity"] == "indirect"


def test_chinese_planning_yishu():
    """행동·계획 — 遗书."""
    from engine.safety import detect_crisis
    r = detect_crisis("我写好遗书了")
    assert r["crisis_detected"] is True
    assert r["severity"] == "planning"


def test_chinese_jump_from_building():
    from engine.safety import detect_crisis
    r = detect_crisis("从楼上跳下去")
    assert r["crisis_detected"] is True
    assert r["severity"] == "planning"


# ─────────────────────────── 4언어 평등 ───────────────────────────

def test_all_4_languages_can_detect():
    """ko/en/ja/zh 모두 직접 위기 표현은 감지되어야 함."""
    from engine.safety import detect_crisis
    samples = {
        "ko": "죽고 싶어요",
        "en": "I want to die",
        "ja": "死にたい",
        "zh": "我想死",
    }
    for lang, text in samples.items():
        r = detect_crisis(text)
        assert r["crisis_detected"] is True, f"{lang}: {text}"
