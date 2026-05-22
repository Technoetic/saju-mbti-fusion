"""ADR-134 supplement 회귀 — tojeong 144 흐름 톤 고유성·가독성.

기존 ADR-134 회귀는 11괘 정통 시구 영역만 다룸. 본 회귀는 나머지 133괘
(흐름 톤만 부착) 의 출력 품질을 보장:
  · 144 흐름 톤 모두 고유 (중복 0건)
  · '결의 결의 결' 5중첩 패턴 금지 (가독성)

/domain-priorities #1 (52점) 부분 해소 — 학파 출처는 외부 의존이지만
흐름 톤 가독성은 본 AI 단독 처리 영역.
"""
from __future__ import annotations

from collections import Counter

from engine.divination.tojeong.scoring import SIXTY_FOUR_TOJEONG


class TestFlowToneUniqueness:
    """144 흐름 톤 고유성 보장."""

    def test_total_count_144(self):
        """총 144괘 확보."""
        assert len(SIXTY_FOUR_TOJEONG) == 144

    def test_all_flow_tones_unique(self):
        """144 흐름 톤 모두 고유 — 중복 0건."""
        tones = [h.flow_tone_ko for h in SIXTY_FOUR_TOJEONG]
        c = Counter(tones)
        dups = {tone: n for tone, n in c.items() if n > 1}
        assert not dups, f"흐름 톤 중복: {dups}"

    def test_no_empty_flow_tone(self):
        """모든 괘에 흐름 톤 비어있지 않음."""
        empty = [h.label_ko for h in SIXTY_FOUR_TOJEONG if not h.flow_tone_ko.strip()]
        assert not empty, f"빈 흐름 톤: {empty}"


class TestFlowToneReadability:
    """가독성 패턴 — '결의 결의 결' 5중첩 차단."""

    def test_no_multiple_geuie_pattern(self):
        """한 톤 안에 '결의'가 2회 이상 등장하지 않음."""
        bad = [
            (h.label_ko, h.flow_tone_ko)
            for h in SIXTY_FOUR_TOJEONG
            if h.flow_tone_ko.count("결의") >= 2
        ]
        assert not bad, f"'결의' 2회+ 톤: {bad[:5]}"

    def test_no_geuie_geuie_ending(self):
        """톤이 '결의 결'로 끝나지 않음 (5중첩 패턴 차단)."""
        bad = [
            (h.label_ko, h.flow_tone_ko)
            for h in SIXTY_FOUR_TOJEONG
            if h.flow_tone_ko.endswith("결의 결")
        ]
        assert not bad, f"'결의 결' 종료 톤: {bad[:5]}"

    def test_geuie_word_frequency_reasonable(self):
        """'결의' 단어 전체 빈도 25회 미만 (가독성 기준)."""
        # 기존 66회 → 본 작업으로 19회. 안전 마진으로 25회 임계.
        total = sum(h.flow_tone_ko.count("결의") for h in SIXTY_FOUR_TOJEONG)
        assert total < 25, f"'결의' 단어 {total}회 (목표: <25)"
