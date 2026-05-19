"""engine.safety.misc.language — §7.2.3 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── detect_language ───────────────────────────

def test_detect_korean():
    from engine.safety.misc.language import detect_language
    assert detect_language("올해 운이 어떨까요") == "ko"
    assert detect_language("안녕하세요") == "ko"


def test_detect_english():
    from engine.safety.misc.language import detect_language
    assert detect_language("What is my fortune this year") == "en"
    assert detect_language("Hello, how are you?") == "en"


def test_detect_japanese_with_hiragana():
    from engine.safety.misc.language import detect_language
    assert detect_language("今年の運勢はどうですか") == "ja"
    assert detect_language("こんにちは") == "ja"


def test_detect_japanese_with_katakana():
    """가타카나만 있어도 일본어로 감지."""
    from engine.safety.misc.language import detect_language
    assert detect_language("カタカナテスト") == "ja"


def test_detect_chinese_no_kana():
    """한자만 (가나·한글 없음) → 중국어."""
    from engine.safety.misc.language import detect_language
    assert detect_language("今年运势如何") == "zh"
    assert detect_language("你好") == "zh"


def test_detect_korean_mixed_with_english():
    """한·영 혼합에서 한글 30% 이상이면 한국어."""
    from engine.safety.misc.language import detect_language
    # 한글 위주 + 영어 약간
    assert detect_language("올해 fortune이 어떨까요") == "ko"


def test_detect_empty():
    from engine.safety.misc.language import detect_language
    assert detect_language("") == "other"
    assert detect_language("12345 !@#$") == "other"


def test_detect_other_for_emoji_only():
    from engine.safety.misc.language import detect_language
    assert detect_language("🙏✨💫") == "other"


def test_japanese_priority_over_chinese():
    """일본어 한자 + 가나 1자 → 일본어 (한자만 카운트하면 중국어로 잘못 판정 가능)."""
    from engine.safety.misc.language import detect_language
    # 한자가 더 많지만 가나가 1자라도 있으면 일본어
    assert detect_language("健康と幸せ") == "ja"


# ─────────────────────────── get_language_advisory ───────────────────────────

def test_advisory_korean_returns_none():
    """한국어는 안내 불필요."""
    from engine.safety.misc.language import get_language_advisory
    assert get_language_advisory("ko") is None
    assert get_language_advisory("") is None


def test_advisory_english():
    from engine.safety.misc.language import get_language_advisory
    msg = get_language_advisory("en")
    assert msg is not None
    assert "Korean" in msg


def test_advisory_japanese():
    from engine.safety.misc.language import get_language_advisory
    msg = get_language_advisory("ja")
    assert msg is not None
    assert "韓国語" in msg


def test_advisory_chinese():
    from engine.safety.misc.language import get_language_advisory
    msg = get_language_advisory("zh")
    assert msg is not None
    assert "韩文" in msg


def test_advisory_other():
    from engine.safety.misc.language import get_language_advisory
    msg = get_language_advisory("other")
    assert msg is not None


def test_engine_safety_exports_language():
    import engine.safety as safety
    assert hasattr(safety, "detect_language")
    assert hasattr(safety, "get_language_advisory")
