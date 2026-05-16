"""법적 면책 다국어 — §7.2.10 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_build_legal_footer_default_korean():
    """기본 lang 미지정 → 한국어."""
    from engine.safety import build_legal_footer
    f = build_legal_footer()
    assert "[안내]" in f
    assert "1393" in f


def test_build_legal_footer_english():
    from engine.safety import build_legal_footer
    f = build_legal_footer(lang="en")
    assert "[Notice]" in f
    assert "988" in f
    assert "Samaritans" in f


def test_build_legal_footer_japanese():
    from engine.safety import build_legal_footer
    f = build_legal_footer(lang="ja")
    assert "[ご案内]" in f
    assert "0120-279-338" in f


def test_build_legal_footer_chinese():
    from engine.safety import build_legal_footer
    f = build_legal_footer(lang="zh")
    assert "[提示]" in f
    assert "010-82951332" in f


def test_build_legal_footer_bcp47_locale():
    """BCP-47 로케일 → 언어 코드 추출."""
    from engine.safety import build_legal_footer
    assert "Notice" in build_legal_footer(lang="en-US")
    assert "Notice" in build_legal_footer(lang="en-GB")
    assert "ご案内" in build_legal_footer(lang="ja-JP")
    assert "提示" in build_legal_footer(lang="zh-CN")
    assert "안내" in build_legal_footer(lang="ko-KR")


def test_build_legal_footer_unknown_lang_falls_back_to_korean():
    from engine.safety import build_legal_footer
    f = build_legal_footer(lang="xx")
    assert "[안내]" in f


def test_crisis_footer_english():
    from engine.safety import build_legal_footer
    f = build_legal_footer(is_crisis=True, lang="en")
    assert "[Important]" in f
    assert "988" in f
    assert "911" in f or "112" in f or "999" in f


def test_crisis_footer_japanese():
    from engine.safety import build_legal_footer
    f = build_legal_footer(is_crisis=True, lang="ja")
    assert "[重要]" in f
    assert "0120-279-338" in f
    assert "119" in f


def test_crisis_footer_chinese():
    from engine.safety import build_legal_footer
    f = build_legal_footer(is_crisis=True, lang="zh")
    assert "[重要]" in f
    assert "010-82951332" in f
    assert "120" in f or "110" in f


def test_crisis_footer_korean_existing_behavior():
    """기존 한국어 위기 푸터 동작 유지."""
    from engine.safety import build_legal_footer
    f = build_legal_footer(is_crisis=True)
    assert "[중요]" in f
    assert "1393" in f


def test_data_notice_only_korean():
    """데이터 처리 안내는 한국어에만 부착 (정책상 한국 PIPA 기준)."""
    from engine.safety import build_legal_footer
    ko_with = build_legal_footer(include_data_notice=True, lang="ko")
    ko_without = build_legal_footer(include_data_notice=False, lang="ko")
    en_with = build_legal_footer(include_data_notice=True, lang="en")
    assert len(ko_with) > len(ko_without)
    # 영어는 data_notice 무시
    en_without = build_legal_footer(include_data_notice=False, lang="en")
    assert en_with == en_without
