# -*- coding: utf-8 -*-
"""engine.saju.twelve_stages — 회귀 테스트 (ADR-031).

자동 생성 30쌍 + 120 전수 검증 + ADR-010 면책 + 결정론.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ───────────────────── 데이터 로드 ─────────────────────


def test_data_loads():
    from engine.saju.twelve_stages import is_loaded, total_mappings, total_stems
    assert is_loaded()
    assert total_mappings() == 120
    assert total_stems() == 10


def test_stages_list():
    from engine.saju.twelve_stages import list_stages, STAGES
    assert list_stages() == STAGES
    assert len(STAGES) == 12
    expected = ("장생", "목욕", "관대", "건록", "제왕", "쇠", "병", "사", "묘", "절", "태", "양")
    assert STAGES == expected


# ───────────────────── 양순 음역 검증 ─────────────────────


def test_yang_stems_start_jangsaeng():
    """양간 5개의 장생 위치 — 보고서 §3.2 양순음역."""
    from engine.saju.twelve_stages import get_twelve_stage
    # 甲(목): 亥에서 장생
    assert get_twelve_stage("甲", "亥") == "장생"
    # 丙(화): 寅에서 장생
    assert get_twelve_stage("丙", "寅") == "장생"
    # 庚(금): 巳에서 장생
    assert get_twelve_stage("庚", "巳") == "장생"
    # 壬(수): 申에서 장생
    assert get_twelve_stage("壬", "申") == "장생"


def test_eum_stems_start_jangsaeng():
    """음간 5개의 장생 위치 — 보고서 §3.2 양순음역 (역행)."""
    from engine.saju.twelve_stages import get_twelve_stage
    # 乙(목): 午에서 장생 (甲의 사지)
    assert get_twelve_stage("乙", "午") == "장생"
    # 丁(화): 酉에서 장생 (丙의 사지)
    assert get_twelve_stage("丁", "酉") == "장생"
    # 辛(금): 子에서 장생 (庚의 사지)
    assert get_twelve_stage("辛", "子") == "장생"
    # 癸(수): 卯에서 장생 (壬의 사지)
    assert get_twelve_stage("癸", "卯") == "장생"


# ───────────────────── 화토동궁 검증 ─────────────────────


def test_hwato_dongung_yang():
    """화토동궁 — 戊(양토)는 丙(양화)과 동일 궤적."""
    from engine.saju.twelve_stages import get_twelve_stage
    # 戊의 장생 = 寅 (丙과 동일)
    assert get_twelve_stage("戊", "寅") == "장생"
    assert get_twelve_stage("戊", "巳") == "건록"
    assert get_twelve_stage("戊", "午") == "제왕"
    # 丙·戊 완전 일치 검증
    for branch in ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]:
        assert get_twelve_stage("戊", branch) == get_twelve_stage("丙", branch)


def test_hwato_dongung_eum():
    """화토동궁 — 己(음토)는 丁(음화)과 동일 궤적."""
    from engine.saju.twelve_stages import get_twelve_stage
    assert get_twelve_stage("己", "酉") == "장생"
    # 丁·己 완전 일치
    for branch in ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]:
        assert get_twelve_stage("己", branch) == get_twelve_stage("丁", branch)


# ───────────────────── 12 cycle 검증 ─────────────────────


def test_each_stem_has_12_stages():
    """각 천간 12 지지 매핑 + 모든 12 stages 1번씩 등장."""
    from engine.saju.twelve_stages import get_twelve_stage, STAGES
    GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    JI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    for stem in GAN:
        stages = []
        for br in JI:
            s = get_twelve_stage(stem, br)
            assert s is not None
            stages.append(s)
        # 모든 12 stages가 정확히 1번씩 등장
        assert sorted(stages) == sorted(STAGES), f"{stem}: 중복/누락 {stages}"


# ───────────────────── 보고서 §4 회귀 30쌍 (자동 생성) ─────────────────────


def _load_regression():
    import json
    p = Path(__file__).resolve().parent.parent.parent / "data" / "twelve_stages_regression.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def test_regression_data_loads():
    """30쌍 자동 생성 회귀 데이터 로드 검증."""
    data = _load_regression()
    assert data["adr"] == "ADR-031"
    assert len(data["tests"]) == 30


def test_regression_30_pass():
    """30 자동 생성 샘플 모두 PASS (120 매핑 정합성)."""
    from engine.saju.twelve_stages import get_twelve_stage
    data = _load_regression()
    for t in data["tests"]:
        got = get_twelve_stage(t["day_stem"], t["branch"])
        assert got == t["expected_stage"], (
            f"{t['id']}: {t['day_stem']}+{t['branch']} "
            f"expected={t['expected_stage']} got={got}"
        )


# ───────────────────── 4주 종합 ─────────────────────


def test_four_pillars_eval():
    """4주(년·월·일·시) 십이운성 종합 평가."""
    from engine.saju.twelve_stages import evaluate_four_pillars_stages
    # 일간 甲 + 4주 지지
    r = evaluate_four_pillars_stages("甲", "亥", "子", "丑", "寅")
    assert r["year_stage"] == "장생"
    assert r["month_stage"] == "목욕"
    assert r["day_stage"] == "관대"
    assert r["hour_stage"] == "건록"


# ───────────────────── ADR-010 면책 ─────────────────────


def test_rationale_includes_school():
    """rationale에 학파 명시 (ADR-002 옵션 B + ADR-015)."""
    from engine.saju.twelve_stages import get_twelve_stage_with_rationale
    r = get_twelve_stage_with_rationale("甲", "亥")
    assert r is not None
    assert "자평진전" in r.rationale
    assert "양순음역" in r.rationale or "화토동궁" in r.rationale


def test_rationale_includes_disclaimer():
    """rationale에 ADR-010 면책 자동 포함."""
    from engine.saju.twelve_stages import get_twelve_stage_with_rationale
    r = get_twelve_stage_with_rationale("壬", "子")
    assert r is not None
    assert "인과관계" in r.rationale
    assert "타 학파" in r.rationale or "이견" in r.rationale


def test_rationale_no_causal_words():
    """ADR-010 사용자 출력 인과 단정 금지."""
    from engine.saju.twelve_stages import get_twelve_stage_with_rationale
    forbidden = ["반드시", "확정", "예언", "고독·단명", "무조건"]
    for stem in ["甲", "丙", "戊", "庚", "壬"]:
        for branch in ["子", "卯", "午", "酉"]:
            r = get_twelve_stage_with_rationale(stem, branch)
            assert r is not None
            for w in forbidden:
                assert w not in r.rationale, f"{stem}+{branch}: 인과 단어 '{w}' 노출"


def test_invalid_input_returns_none():
    """잘못된 입력 → None (예외 X)."""
    from engine.saju.twelve_stages import get_twelve_stage
    assert get_twelve_stage("", "亥") is None
    assert get_twelve_stage("甲", "") is None
    assert get_twelve_stage("X", "亥") is None
    assert get_twelve_stage("甲", "Y") is None


def test_validators():
    from engine.saju.twelve_stages import is_valid_stem, is_valid_branch
    assert is_valid_stem("甲")
    assert is_valid_stem("癸")
    assert not is_valid_stem("X")
    assert is_valid_branch("子")
    assert is_valid_branch("亥")
    assert not is_valid_branch("Y")


# ───────────────────── 결정론 ─────────────────────


def test_deterministic():
    """동일 입력 → 동일 출력 (ADR-001)."""
    from engine.saju.twelve_stages import get_twelve_stage, get_twelve_stage_with_rationale
    for stem in ["甲", "乙", "壬", "癸"]:
        for branch in ["子", "午", "亥"]:
            r1 = get_twelve_stage(stem, branch)
            r2 = get_twelve_stage(stem, branch)
            assert r1 == r2
            w1 = get_twelve_stage_with_rationale(stem, branch)
            w2 = get_twelve_stage_with_rationale(stem, branch)
            assert w1 == w2


# ───────────────────── KCI 학술 출처 ─────────────────────


def test_kci_sources():
    """KCI 학술 출처 노출 가능."""
    from engine.saju.twelve_stages import kci_sources
    sources = kci_sources()
    assert "NODE10738496" in sources
    assert "NODE08998998" in sources
    assert "최산태" in sources["NODE10738496"] or "김만태" in sources["NODE10738496"]
    assert "김계성" in sources["NODE08998998"]
