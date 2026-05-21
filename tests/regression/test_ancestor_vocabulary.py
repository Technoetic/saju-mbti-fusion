"""ADR-123 ancestor 어휘 풀 + sanitize 5중 안전망 회귀.

학술 근거: 이능화 1927·한국학중앙연구원·국립민속박물관·Skeptical Inquirer.
"""
from __future__ import annotations

from engine.divination.ancestor.vocabulary import (
    ANCESTOR_FLOW_TONE_VOCAB,
    RECOMMENDED_FLOW_TONES,
    build_ancestor_prompt_injection,
)


class TestAncestorVocabulary:
    """정통 학파 10 어휘 풀 (이능화·한국학중앙연구원·국립민속박물관)."""

    def test_orthodox_vocab_10(self) -> None:
        """10건 정통 어휘 영속화."""
        assert len(ANCESTOR_FLOW_TONE_VOCAB) == 10
        expected = {
            "효(孝)", "근원의 결", "인연의 흐름", "내리사랑",
            "뿌리", "수호", "보살핌", "음덕(陰德)",
            "선대의 자취", "보이지 않는 이끌림",
        }
        assert ANCESTOR_FLOW_TONE_VOCAB == expected

    def test_three_recommended_flow_tones(self) -> None:
        """보고서 §3.2 명시 3 표준 흐름 톤."""
        assert len(RECOMMENDED_FLOW_TONES) == 3
        for tone in RECOMMENDED_FLOW_TONES:
            # 한국 전통 추모 정서 핵심 어휘 1+ 포함 의무
            assert any(
                kw in tone for kw in ["인연", "근원", "뿌리", "결", "선대"]
            )


class TestAncestorPromptInjection:
    """LLM 시스템 프롬프트 주입 — 금지 어휘 명시."""

    def test_injection_contains_orthodox_vocab(self) -> None:
        """주입 텍스트에 10 어휘 풀 포함."""
        injection = build_ancestor_prompt_injection()
        for vocab in ANCESTOR_FLOW_TONE_VOCAB:
            assert vocab in injection

    def test_injection_forbids_assertion(self) -> None:
        """주입 텍스트에 금지 어휘 명시 — 망자 1인칭·접신·빙의."""
        injection = build_ancestor_prompt_injection()
        # 자문 거절 정신 의무 — Grief Vampire 차단
        for forbidden in ["빙의", "접신", "신내림", "채널링", "사망 원인 단정",
                          "전생", "윤회", "업보", "저승사자"]:
            assert forbidden in injection

    def test_injection_three_tones_present(self) -> None:
        """3 흐름 톤 예문 모두 주입."""
        injection = build_ancestor_prompt_injection()
        for tone in RECOMMENDED_FLOW_TONES:
            assert tone in injection


# === sanitize 5중 안전망 회귀 ===


def test_sanitize_ancestor_replaces_chaeneun():
    """채널링 어휘 차단."""
    from web.server import _sanitize_ancestor_assertion_words
    result = _sanitize_ancestor_assertion_words("채널링을 통해 메시지를 받습니다.")
    assert "채널링" not in result
    assert "추모의 결" in result


def test_sanitize_ancestor_replaces_bingeui():
    """빙의 어휘 차단."""
    from web.server import _sanitize_ancestor_assertion_words
    result = _sanitize_ancestor_assertion_words("빙의된 무당이 말합니다.")
    assert "빙의" not in result


def test_sanitize_ancestor_replaces_jeobsin():
    """접신 어휘 차단."""
    from web.server import _sanitize_ancestor_assertion_words
    result = _sanitize_ancestor_assertion_words("접신한 영매가 전합니다.")
    assert "접신" not in result


def test_sanitize_ancestor_replaces_sinnaerim():
    """신내림 어휘 차단."""
    from web.server import _sanitize_ancestor_assertion_words
    result = _sanitize_ancestor_assertion_words("신내림을 받은 무당이.")
    assert "신내림" not in result


def test_sanitize_ancestor_replaces_yeongan():
    """영안·망자의 목소리 어휘 차단."""
    from web.server import _sanitize_ancestor_assertion_words
    result = _sanitize_ancestor_assertion_words("영안이 트인 무당이 망자의 목소리를 전합니다.")
    assert "영안" not in result
    assert "망자의 목소리" not in result


def test_sanitize_ancestor_replaces_first_person_bingeui():
    """1인칭 망자 빙의 화법 차단 — '내가 너를 늘 지켜보고 있다'."""
    from web.server import _sanitize_ancestor_assertion_words
    result = _sanitize_ancestor_assertion_words("내가 너를 늘 지켜보고 있다 라고 하십니다.")
    assert "내가 너를 늘 지켜보고 있다" not in result
    assert "선대의 결이 따뜻하게 비추는 흐름" in result


def test_sanitize_ancestor_replaces_grandpa_speak():
    """1인칭 망자 빙의 화법 차단 — '네 할아버지가 지금 내게 말하기를'."""
    from web.server import _sanitize_ancestor_assertion_words
    result = _sanitize_ancestor_assertion_words("네 할아버지가 지금 내게 말하기를 조심하라 합니다.")
    assert "네 할아버지가 지금 내게 말하기를" not in result


def test_sanitize_ancestor_replaces_behind_spirit():
    """1인칭 망자 빙의 화법 차단 — '네 뒤에 영혼이 서 있다'."""
    from web.server import _sanitize_ancestor_assertion_words
    result = _sanitize_ancestor_assertion_words("네 뒤에 영혼이 서 있다 보입니다.")
    assert "네 뒤에 영혼이 서 있다" not in result


def test_sanitize_ancestor_replaces_drowning_death_assertion():
    """사망 원인 단정 차단 — '억울하게 물에 빠져 죽은 조상'."""
    from web.server import _sanitize_ancestor_assertion_words
    result = _sanitize_ancestor_assertion_words("억울하게 물에 빠져 죽은 조상이 노했습니다.")
    assert "억울하게 물에 빠져 죽은 조상" not in result


def test_sanitize_ancestor_replaces_disease_cause():
    """사망 원인 단정 차단 — '위장병으로 고통받다 돌아가신 조상의 원한'."""
    from web.server import _sanitize_ancestor_assertion_words
    result = _sanitize_ancestor_assertion_words("위장병으로 고통받다 돌아가신 조상의 원한이.")
    assert "위장병으로 고통받다 돌아가신 조상의 원한" not in result


def test_sanitize_ancestor_replaces_karma():
    """전생 업보 단정 차단."""
    from web.server import _sanitize_ancestor_assertion_words
    result = _sanitize_ancestor_assertion_words("전생에 지은 씻을 수 없는 업보 때문입니다.")
    assert "전생에 지은 씻을 수 없는 업보" not in result


def test_sanitize_ancestor_replaces_hell():
    """지옥 단정 차단."""
    from web.server import _sanitize_ancestor_assertion_words
    result = _sanitize_ancestor_assertion_words("지옥불에 떨어진 영혼의 외침입니다.")
    assert "지옥불에 떨어진 영혼의 외침" not in result


def test_sanitize_ancestor_preserves_orthodox_tone():
    """정통 추모 어휘는 보존 — 효·근원의 결·인연·뿌리."""
    from web.server import _sanitize_ancestor_assertion_words
    orthodox = "선대로부터 길게 이어져 온 인연의 결이 당신의 앞길에 평안을 기원합니다."
    result = _sanitize_ancestor_assertion_words(orthodox)
    assert result == orthodox  # 변경 없음 (정통 어휘만)


def test_sanitize_ancestor_empty_string():
    """빈 입력 처리."""
    from web.server import _sanitize_ancestor_assertion_words
    assert _sanitize_ancestor_assertion_words("") == ""
