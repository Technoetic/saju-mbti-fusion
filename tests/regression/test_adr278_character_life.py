"""ADR-278 — 관상 성격·인생 흐름 풀이 (경향 어조) 회귀.

(a) 복합형도 기질 매핑 보유 (b) 삼정 시기론 인생 흐름 생성 (c) 운명필터가
경향 어조는 통과·단정/예언/ADR-006영역은 차단 (d) Stage 2 dict에 life_flow 주입.
"""
from engine.divination.face.knowledge import (
    get_five_shape_trait,
    SAMJEONG_PERIODS,
    format_samjeong_periods_for_prompt,
)
from engine.divination.face.reading import _postprocess_remove_fate_mapping


# (a) 복합형 기질 — ADR-277은 None이었으나 ADR-278에서 보강
def test_composite_now_has_trait():
    t = get_five_shape_trait("복합형")
    assert t is not None
    assert "균형" in t.keyword or "중용" in t.keyword
    assert t.strength.strip() and t.caution.strip()


def test_all_six_shapes_have_trait():
    for shape in ["목형", "화형", "토형", "금형", "수형", "복합형"]:
        assert get_five_shape_trait(shape) is not None, shape


# (b) 삼정 시기론
def test_samjeong_periods_defined():
    assert set(SAMJEONG_PERIODS) == {"상정", "중정", "하정"}
    assert "초년" in SAMJEONG_PERIODS["상정"].period
    assert "중년" in SAMJEONG_PERIODS["중정"].period
    assert "말년" in SAMJEONG_PERIODS["하정"].period


def test_life_flow_high_vs_low():
    """점수 ≥0.5 → 도드라짐, <0.5 → 차분히 다짐 (양면)."""
    out = format_samjeong_periods_for_prompt({"상정": 0.0, "중정": 1.0, "하정": 0.0})
    assert out is not None
    assert "중년" in out and "도드라진다" in out  # 중정 1.0
    assert "초년" in out and "다지는" in out       # 상정 0.0


def test_life_flow_gradient_tone_only():
    """인생 흐름은 경향 어조 — 단정·예언 어휘 없음."""
    out = format_samjeong_periods_for_prompt({"상정": 0.8, "중정": 0.8, "하정": 0.8})
    assert out is not None
    # 안내(※) 줄은 금지어를 '예시로' 포함하므로 본문(시기 해석)만 검사
    body = "
".join(l for l in out.split("
") if not l.strip().startswith("※"))
    for banned in ["할 것이다", "운이 온다", "틀림없", "반드시"]:
        assert banned not in body


def test_life_flow_empty():
    assert format_samjeong_periods_for_prompt({}) is None


# (c) 운명필터 — 경향 통과 / 단정·예언·금지영역 차단
def test_filter_passes_gradient():
    line = "전통 관상에서 중정이 강하면 중년의 활동력이 도드라진다고 봅니다"
    assert line in _postprocess_remove_fate_mapping(line)


def test_filter_passes_initial_period_gradient():
    line = "초년의 기운과 복록의 결이 밝다고 보는 경향이 있습니다"
    assert line in _postprocess_remove_fate_mapping(line)


def test_filter_blocks_prophecy():
    line = "중년에 큰 재물운이 트일 것이로세"
    assert line not in _postprocess_remove_fate_mapping(line)


def test_filter_blocks_fate_word_even_with_gradient():
    """fate_word(관록·재물운 등 ADR-006 영역)는 경향 어조여도 차단."""
    line = "전통 관상에서 그대는 관록이 두텁다고 봅니다"
    assert line not in _postprocess_remove_fate_mapping(line)


def test_filter_blocks_sasang():
    line = "그대는 태양인의 기질로 봅니다"
    assert line not in _postprocess_remove_fate_mapping(line)


# (d) Stage 2 dict 주입
def test_life_flow_injected_into_stage2():
    from engine.divination.face.reading import _build_deterministic_scores_summary

    palace = {
        "samjeong": {
            "sangjeong": {"label_ko": "상정", "score": 0.0},
            "jungjeong": {"label_ko": "중정", "score": 1.0},
            "hajeong": {"label_ko": "하정", "score": 0.0},
        }
    }
    out = _build_deterministic_scores_summary(palace_scores=palace, face_shape=None)
    assert "life_flow" in out
    assert "중년" in out["life_flow"]
