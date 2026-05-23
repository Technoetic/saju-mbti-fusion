"""ADR-158 회귀 — 야선 아씨 4 컨텐츠 결정론 + sanitize 7중 안전망.

대상:
  · sok_gunghap (속궁합)
  · desire_saju (욕망 사주)
  · unu_jijeong (운우지정)
  · jeongin_saju (정인 사주)

각 4 컨텐츠:
  · 결정론 compute_X 산출 정합
  · format_X_for_prompt 시스템 프롬프트 메타 영속
  · sanitize_X_text 단정 어휘 차단 (결혼·이혼·외도·배우자 외모 등)
"""
from __future__ import annotations


# ─────────────────────────── sok_gunghap (속궁합) ───────────────────────────


class TestSokGunghap:
    def test_basic_compute(self):
        from engine.divination.sok_gunghap import compute_sok_gunghap
        r = compute_sok_gunghap("庚午", "丁卯")
        assert r is not None
        assert 45 <= r.overall_score <= 85
        assert r.relation_type in ("deep_resonance", "complementary", "frictional_learning")

    def test_with_branches_dohwa(self):
        from engine.divination.sok_gunghap import compute_sok_gunghap
        r = compute_sok_gunghap(
            "庚午", "丁卯",
            self_branches=("子", "午", "卯", "酉"),
            partner_branches=("子", "午", "卯", "酉"),
        )
        assert r.dohwa_count >= 4  # 4 도화 지지 모두 일치

    def test_invalid_input(self):
        from engine.divination.sok_gunghap import compute_sok_gunghap
        assert compute_sok_gunghap("invalid", "丁卯") is None
        assert compute_sok_gunghap("庚午", "xx") is None

    def test_format_for_prompt_includes_disclaimer(self):
        from engine.divination.sok_gunghap import compute_sok_gunghap, format_sok_gunghap_for_prompt
        r = compute_sok_gunghap("甲子", "己未")
        txt = format_sok_gunghap_for_prompt(r)
        assert "ADR-006" in txt
        assert "결혼" in txt or "이혼" in txt or "단정" in txt

    def test_sanitize_blocks_marriage_certainty(self):
        from engine.divination.sok_gunghap import sanitize_sok_gunghap_text
        out = sanitize_sok_gunghap_text("두 분은 반드시 결혼할 것이며 100% 궁합입니다.")
        assert "반드시 결혼" not in out
        assert "100% 궁합" not in out

    def test_sanitize_blocks_divorce(self):
        from engine.divination.sok_gunghap import sanitize_sok_gunghap_text
        out = sanitize_sok_gunghap_text("이혼할 것이고 헤어질 것이외다.")
        assert "이혼할 것" not in out
        assert "헤어질 것" not in out

    def test_sanitize_blocks_cheating(self):
        from engine.divination.sok_gunghap import sanitize_sok_gunghap_text
        out = sanitize_sok_gunghap_text("바람 피울 것이며 외도할 것입니다.")
        assert "바람 피울 것" not in out
        assert "외도할 것" not in out


# ─────────────────────────── desire_saju (욕망 사주) ───────────────────────────


class TestDesireSaju:
    def test_basic_compute(self):
        from engine.divination.desire_saju import compute_desire_saju
        r = compute_desire_saju(
            "庚", ("편관", "정재", "식신"), ("子", "午", "卯", "酉"),
        )
        assert r is not None
        assert r.dominant_desire in ("power", "wealth", "expression", "freedom", "self")
        assert r.charisma_score >= 40

    def test_dohwa_full_max_charisma(self):
        from engine.divination.desire_saju import compute_desire_saju
        r = compute_desire_saju(
            "庚", ("편관",), ("子", "午", "卯", "酉"),
        )
        assert r.dohwa_count == 4
        assert r.charisma_score >= 70  # 50 + 4*5 + 홍염 보너스

    def test_invalid_input(self):
        from engine.divination.desire_saju import compute_desire_saju
        assert compute_desire_saju("", (), ()) is None

    def test_format_includes_disclaimer(self):
        from engine.divination.desire_saju import compute_desire_saju, format_desire_saju_for_prompt
        r = compute_desire_saju("甲", ("정관",), ("子",))
        txt = format_desire_saju_for_prompt(r)
        assert "ADR-006" in txt

    def test_sanitize_blocks_promiscuity(self):
        from engine.divination.desire_saju import sanitize_desire_saju_text
        out = sanitize_desire_saju_text("이 분은 문란한 성격이며 바람둥이입니다.")
        assert "문란한" not in out
        assert "바람둥이" not in out

    def test_sanitize_blocks_sexual_assertion(self):
        from engine.divination.desire_saju import sanitize_desire_saju_text
        out = sanitize_desire_saju_text("성욕이 강해 여러 사람과 잠자리합니다.")
        assert "성욕이 강해" not in out
        assert "여러 사람과 잠" not in out


# ─────────────────────────── unu_jijeong (운우지정) ───────────────────────────


class TestUnuJijeong:
    def test_basic_compute(self):
        from engine.divination.unu_jijeong import compute_unu_jijeong
        r = compute_unu_jijeong("午", "未", target_year=2026)
        assert r is not None
        assert r.static_relation == "六合(火)"
        assert 40 <= r.intensity_score <= 80

    def test_invalid_input(self):
        from engine.divination.unu_jijeong import compute_unu_jijeong
        assert compute_unu_jijeong("X", "未") is None
        assert compute_unu_jijeong("午", "未", target_year=1800) is None

    def test_format_includes_disclaimer(self):
        from engine.divination.unu_jijeong import compute_unu_jijeong, format_unu_jijeong_for_prompt
        r = compute_unu_jijeong("子", "午", target_year=2026)
        txt = format_unu_jijeong_for_prompt(r)
        assert "ADR-006" in txt

    def test_sanitize_blocks_timing(self):
        from engine.divination.unu_jijeong import sanitize_unu_jijeong_text
        out = sanitize_unu_jijeong_text("보름 안에 결혼할 것이며 한 달 안에 만날 것이외다.")
        assert "보름 안에" not in out
        assert "한 달 안에 만나" not in out

    def test_sanitize_blocks_breakup_timing(self):
        from engine.divination.unu_jijeong import sanitize_unu_jijeong_text
        out = sanitize_unu_jijeong_text("3개월 안에 결혼하고 2주 안에 이별할 것.")
        assert "3개월 안에 결혼" not in out
        assert "2주 안에 이별" not in out

    def test_sanitize_blocks_destiny_words(self):
        from engine.divination.unu_jijeong import sanitize_unu_jijeong_text
        out = sanitize_unu_jijeong_text("운명적 만남이며 100% 결혼할 것.")
        assert "운명적 만남" not in out
        assert "100% 결혼" not in out


# ─────────────────────────── jeongin_saju (정인 사주) ───────────────────────────


class TestJeonginSaju:
    def test_basic_compute(self):
        from engine.divination.jeongin_saju import compute_jeongin_saju
        r = compute_jeongin_saju(
            "庚", "午",
            ten_gods=("편재", "정관", "식신", "정인"),
            ten_gods_at_day_ji=("정관",),
        )
        assert r is not None
        assert r.jeongkwan_count == 1
        assert r.jeongin_count == 1
        assert r.has_jeongkwan_in_day is True

    def test_invalid_input(self):
        from engine.divination.jeongin_saju import compute_jeongin_saju
        assert compute_jeongin_saju("", "午", (), ()) is None
        assert compute_jeongin_saju("庚", "X", (), ()) is None

    def test_format_includes_disclaimer(self):
        from engine.divination.jeongin_saju import compute_jeongin_saju, format_jeongin_saju_for_prompt
        r = compute_jeongin_saju("甲", "子", ("정관",))
        txt = format_jeongin_saju_for_prompt(r)
        assert "ADR-006" in txt

    def test_sanitize_blocks_appearance(self):
        from engine.divination.jeongin_saju import sanitize_jeongin_saju_text
        out = sanitize_jeongin_saju_text("키 180cm 의사 직업의 5살 연상.")
        assert "180" not in out or "cm" not in out
        assert "의사 직업" not in out
        assert "5살 연상" not in out

    def test_sanitize_blocks_timing(self):
        from engine.divination.jeongin_saju import sanitize_jeongin_saju_text
        out = sanitize_jeongin_saju_text("올해 안에 결혼할 것이며 운명의 상대입니다.")
        assert "올 해 안에 결혼" not in out and "올해 안에 결혼" not in out
        assert "운명의 상대" not in out

    def test_sanitize_blocks_child_count(self):
        from engine.divination.jeongin_saju import sanitize_jeongin_saju_text
        out = sanitize_jeongin_saju_text("자녀는 2명이며 평생 독신은 X.")
        assert "2명의 자녀" not in out and "2명 자녀" not in out
        assert "평생 독신" not in out


# ─────────────────────────── web/server.py 7중 sanitize 통합 ───────────────────────────


class TestServerSanitize7Layer:
    """ADR-158 sanitize 7중 안전망 분기 영속."""

    def test_server_has_ya_sanitize_branch(self):
        from pathlib import Path
        src = Path("web/server.py").read_text(encoding="utf-8")
        assert "ADR-158 sanitize 7중 안전망" in src
        assert "char_key == \"ya\"" in src
        # 4 컨텐츠 sanitize import 분기
        assert "sanitize_sok_gunghap_text" in src
        assert "sanitize_desire_saju_text" in src
        assert "sanitize_unu_jijeong_text" in src
        assert "sanitize_jeongin_saju_text" in src

    def test_server_has_ya_compute_branch(self):
        from pathlib import Path
        src = Path("web/server.py").read_text(encoding="utf-8")
        assert "ADR-158 야선 아씨 4 컨텐츠" in src
        assert "compute_sok_gunghap" in src
        assert "compute_desire_saju" in src
        assert "compute_unu_jijeong" in src
        assert "compute_jeongin_saju" in src
