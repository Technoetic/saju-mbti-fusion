"""ADR-091 회귀 — 궁합 성명학 융합 LLM 인용 강화.

ADR-090 단정 차단 후 결정론 산출은 성명학 융합 완전 활성이나 LLM 본문 인용 약함.
본 ADR-091로 5번째 섹션 (Naming Resonance) 추가 + 지시 강화.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
EXPLAIN_PY = ROOT / "engine" / "saju" / "interpret" / "explain.py"


def _src() -> str:
    return EXPLAIN_PY.read_text(encoding="utf-8")


def test_name_block_label_renamed():
    """name_block 라벨이 '성명학 음령오행 결합'으로 명확화."""
    src = _src()
    assert "성명학 음령오행 결합" in src
    assert "ADR-071 융합 패턴" in src


def test_has_name_flow_flag():
    """has_name_flow 플래그 존재 (조건부 5섹션 활성)."""
    src = _src()
    assert "has_name_flow = bool" in src


def test_adr_091_directive_present():
    """[ADR-091] 지시 명시 — 5번째 섹션 작성 의무."""
    src = _src()
    assert "[ADR-091]" in src
    assert "5번째 섹션" in src
    assert "Naming Resonance" in src


def test_directive_states_naming_required_when_name_flow():
    """지시문에 '사주 단독 풀이 X' + '사주+성명학 융합 의무' 명시."""
    src = _src()
    assert "사주 단독 풀이 X" in src
    assert "사주+성명학 융합 의무" in src
    assert "ADR-071" in src or "ADR-091" in src


def test_section_5_conditional_block():
    """### 5. Naming Resonance 섹션이 has_name_flow 조건부 활성."""
    src = _src()
    assert "### 5. Naming Resonance" in src
    assert "두 이름의 음령오행 결합" in src


def test_section_5_states_label_quotation():
    """5번째 섹션 명세에 '상생·상극 라벨 직접 인용 의무' 명시."""
    src = _src()
    assert "상생·상극 라벨 직접 인용 의무" in src


def test_section_count_dynamic():
    """작성 형식이 has_name_flow에 따라 4 또는 5 섹션."""
    src = _src()
    assert "{'5' if has_name_flow else '4'} 섹션" in src


def test_naming_resonance_micro_vibration_phrase():
    """5섹션 명세에 '미세 진동' 비유 명시 (관계 양면 표현)."""
    src = _src()
    assert "미세 진동" in src


def test_existing_sections_1_to_4_preserved():
    """기존 1~4 섹션 보존."""
    src = _src()
    assert "Core Resonance (핵심 공명)" in src
    assert "Daily Rhythm (일상 리듬)" in src
    assert "Friction Points (갈등 지점)" in src
    assert "Growth Together (함께 성장)" in src


# ── ② 결정론 산출 정합 검증 ────────────────────


def test_analyze_compat_returns_name_flow_when_myeong_present():
    """analyze_compat이 myeong 입력 시 name_flow 활성."""
    from engine.saju.compat import analyze_compat
    saju_a = {"day": "辛未", "wuxing_dist": {"금": 2, "토": 1}}
    saju_b = {"day": "丁卯", "wuxing_dist": {"화": 2, "목": 1}}
    myeong_a = {"combined_wuxing_dist": {"목": 1, "토": 1, "수": 1}}
    myeong_b = {"combined_wuxing_dist": {"토": 1, "화": 1, "금": 1}}
    result = analyze_compat(saju_a, saju_b, myeong_a=myeong_a, myeong_b=myeong_b)
    assert result.get("name_flow") is not None
    name = result["name_flow"]
    assert "positive" in name
    assert "negative" in name
    assert len(name["positive"]) + len(name["negative"]) > 0


def test_analyze_compat_name_flow_none_without_myeong():
    """myeong 미입력 시 name_flow None."""
    from engine.saju.compat import analyze_compat
    result = analyze_compat(
        {"day": "辛未", "wuxing_dist": {"금": 1}},
        {"day": "丁卯", "wuxing_dist": {"화": 1}},
    )
    assert result.get("name_flow") is None


# ── ③ ADR 정합 ────────────────────


def test_directive_lists_all_relevant_adrs():
    """지시문에 ADR-006·010·014·091 모두 명시."""
    src = _src()
    assert "ADR-006" in src
    assert "ADR-010" in src
    assert "ADR-014" in src
    assert "ADR-091" in src


def test_no_score_grade_in_user_prompt():
    """ADR-090 정합 유지 — 종합 점수·등급 prompt 부재."""
    src = _src()
    # ADR-091 정정 후에도 ADR-090 정합 유지
    assert "종합 점수:" not in src or "ADR-090" in src
    assert "점수·등급 단정 X" in src
