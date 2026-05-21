"""ADR-134 회귀 — 토정비결 11괘 시구 본문화 + sanitize 6중 안전망.

학술 근거:
  - 한국학중앙연구원 한국민족문화대백과사전 E0059207 (토정비결 표제)
  - 국립민속박물관 한국민속대백과사전 detail/5167 (144괘 4언 시구·1564 원본)
  - 보고서 「한국 토정비결 144괘 정통 시구 학술 출처」 §2.1·§4·§6 본문 명시
"""
from __future__ import annotations

from engine.divination.tojeong import (
    SIXTY_FOUR_TOJEONG,
    TOJEONG_FLOW_TONE_SUBSTITUTIONS,
    TOJEONG_FORBIDDEN_WORDS,
    hexagram_by_id,
    sanitize_tojeong_verse,
)


# 보고서 §6 verses_144 JSON 11괘 (label_ko → 시구 메타)
EXPECTED_11_VERSES = {
    "111": {"hanja": "東風解凍 春日和暢", "hangeul": "동풍해동 춘일화창", "confidence": "HIGH"},
    "123": {"hanja": "昏夜得燭", "hangeul": "혼야득촉", "confidence": "MEDIUM"},
    "811": {"hanja": "前進通達之意", "hangeul": "전진통달지의", "confidence": "MEDIUM"},
    "812": {"hanja": "有順通達不傷其身之意", "hangeul": "유순통달불상기신지의", "confidence": "MEDIUM"},
    "813": {"hanja": "有吉通達必有亨通之意", "hangeul": "유길통달필유형통지의", "confidence": "MEDIUM"},
    "821": {"hanja": "心高有通達之意", "hangeul": "심고유통달지의", "confidence": "MEDIUM"},
    "822": {"hanja": "有吉必有光明之意", "hangeul": "유길필유광명지의", "confidence": "MEDIUM"},
    "831": {"hanja": "正心正道之意", "hangeul": "정심정도지의", "confidence": "MEDIUM"},
    "832": {"hanja": "有事必中之意", "hangeul": "유사필중지의", "confidence": "MEDIUM"},
    "833": {"hanja": "無咎安靜之意", "hangeul": "무구안정지의", "confidence": "MEDIUM"},
    "863": {"hanja": "進達榮貴之意", "hangeul": "진달영귀지의", "confidence": "HIGH"},
}


# ──────────── 11괘 시구 본문화 ────────────


class TestVersesBodyText:
    """11괘 시구 본문화 검증."""

    def test_all_11_verses_present(self):
        """11괘 시구 모두 본문화."""
        labeled = {h.label_ko: h for h in SIXTY_FOUR_TOJEONG}
        for label, expected in EXPECTED_11_VERSES.items():
            assert label in labeled
            hexagram = labeled[label]
            assert hexagram.verse_hanja == expected["hanja"]
            assert hexagram.verse_hangeul == expected["hangeul"]
            assert hexagram.confidence == expected["confidence"]

    def test_133_verses_empty(self):
        """11괘 외 133괘는 시구 부재 (정직 한계)."""
        labeled = {h.label_ko: h for h in SIXTY_FOUR_TOJEONG}
        count_empty = 0
        for label, hexagram in labeled.items():
            if label not in EXPECTED_11_VERSES:
                assert hexagram.verse_hanja == ""
                assert hexagram.verse_hangeul == ""
                assert hexagram.confidence == "NONE"
                count_empty += 1
        # 144 - 11 = 133 부재
        assert count_empty == 133

    def test_verse_111_high_confidence(self):
        """괘 111 — 한국학중앙연구원 인증본 HIGH."""
        labeled = {h.label_ko: h for h in SIXTY_FOUR_TOJEONG}
        h111 = labeled["111"]
        assert h111.confidence == "HIGH"
        assert "한국학중앙연구원" in h111.source_school

    def test_verse_meaning_present(self):
        """11괘 모두 시구 의미(verse_meaning) 본문화."""
        labeled = {h.label_ko: h for h in SIXTY_FOUR_TOJEONG}
        for label in EXPECTED_11_VERSES.keys():
            hexagram = labeled[label]
            assert hexagram.verse_meaning != ""
            assert len(hexagram.verse_meaning) > 5

    def test_source_school_present(self):
        """11괘 모두 학파 출처 명시 (ADR-010)."""
        labeled = {h.label_ko: h for h in SIXTY_FOUR_TOJEONG}
        for label in EXPECTED_11_VERSES.keys():
            hexagram = labeled[label]
            assert "토정 정통" in hexagram.source_school


class TestTojeongIntegrity:
    """144괘 풀 무결성."""

    def test_total_144_hexagrams(self):
        """144괘 완전 풀."""
        assert len(SIXTY_FOUR_TOJEONG) == 144

    def test_hex_id_consecutive(self):
        """hex_id 0~143 연속."""
        for i, hexagram in enumerate(SIXTY_FOUR_TOJEONG):
            assert hexagram.hex_id == i

    def test_hexagram_by_id_works(self):
        """hexagram_by_id 통합."""
        h0 = hexagram_by_id(0)
        assert h0 is not None
        assert h0.label_ko == "111"
        assert h0.verse_hanja == "東風解凍 春日和暢"

    def test_hexagram_by_id_out_of_range(self):
        """범위 외 None."""
        assert hexagram_by_id(-1) is None
        assert hexagram_by_id(144) is None


# ──────────── sanitize 6중 안전망 ────────────


class TestSanitizeForbidden:
    """6 단정 어휘 차단 + 흐름 톤 치환."""

    def test_hyungsa_replaced(self):
        """凶事 → 어려운 흐름의 결."""
        result = sanitize_tojeong_verse("올해는 凶事가 다가옵니다")
        assert "凶事" not in result
        assert "어려운 흐름의 결" in result

    def test_daehyung_replaced(self):
        """大凶 → 매우 어려운 흐름의 결."""
        result = sanitize_tojeong_verse("大凶의 운수")
        assert "大凶" not in result
        assert "매우 어려운" in result

    def test_byeongsa_replaced(self):
        """病死 → 건강 유의."""
        result = sanitize_tojeong_verse("病死가 우려된다")
        assert "病死" not in result
        assert "건강 유의" in result

    def test_korean_ihon_replaced(self):
        """이혼 → 관계의 변화."""
        result = sanitize_tojeong_verse("이혼의 흐름")
        assert "이혼" not in result
        assert "관계의 변화" in result

    def test_korean_samang_replaced(self):
        """사망 → 주의와 대비."""
        result = sanitize_tojeong_verse("사망의 위험")
        assert "사망" not in result
        assert "주의와 대비" in result

    def test_korean_jaeang_replaced(self):
        """재앙 → 신중함."""
        result = sanitize_tojeong_verse("재앙이 닥친다")
        assert "재앙" not in result
        assert "신중함" in result


class TestSanitizePositive:
    """긍정 시구 → 흐름 톤 치환."""

    def test_daegil_replaced(self):
        """大吉 → 큰 흐름의 결."""
        result = sanitize_tojeong_verse("大吉의 운수")
        assert "大吉" not in result
        assert "큰 흐름의 결" in result

    def test_hyungtong_replaced(self):
        """亨通 → 형통한 흐름의 결."""
        result = sanitize_tojeong_verse("올해는 亨通한 운")
        assert "亨通" not in result
        assert "형통한 흐름" in result

    def test_tongdal_replaced(self):
        """通達 → 순조롭게 뜻이 통하는."""
        result = sanitize_tojeong_verse("通達의 운")
        assert "通達" not in result
        assert "순조롭게 뜻이 통하는" in result


class TestSanitizeSafety:
    """ADR-006 정합 + 결정론."""

    def test_empty_string(self):
        """빈 입력 그대로."""
        assert sanitize_tojeong_verse("") == ""

    def test_normal_text_unchanged(self):
        """단정 어휘 없는 텍스트 변경 없음."""
        normal = "올해는 평안한 흐름의 결을 보입니다"
        assert sanitize_tojeong_verse(normal) == normal

    def test_deterministic(self):
        """동일 입력 동일 출력."""
        text = "凶事와 大凶의 흐름"
        r1 = sanitize_tojeong_verse(text)
        r2 = sanitize_tojeong_verse(text)
        assert r1 == r2

    def test_forbidden_words_pool_size(self):
        """6 차단 어휘 풀 영속화."""
        assert len(TOJEONG_FORBIDDEN_WORDS) == 6
        for word in ["凶事", "大凶", "病死", "이혼", "사망", "재앙"]:
            assert word in TOJEONG_FORBIDDEN_WORDS

    def test_substitutions_pool_size(self):
        """10 치환 매핑 풀 영속화 (6 차단 + 4 긍정)."""
        # 차단 6건 + 긍정 치환 4건 (大吉·亨通·通達·吉운) = 10
        assert len(TOJEONG_FLOW_TONE_SUBSTITUTIONS) == 10


class TestSanitizeIntegrationWithVerses:
    """11괘 시구 자체에 단정 어휘 부재 검증 (ADR-006)."""

    def test_no_forbidden_in_verse_meaning(self):
        """11괘 시구 의미에 단정 어휘 부재."""
        for hexagram in SIXTY_FOUR_TOJEONG:
            if hexagram.verse_meaning:
                for forbidden in ["이혼", "사망", "재앙"]:
                    assert forbidden not in hexagram.verse_meaning, (
                        f"{hexagram.label_ko} 시구에 단정 어휘 '{forbidden}' 포함"
                    )
