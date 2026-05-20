"""ADR-089 회귀 — server.py saju 분기 신살 결정론 wire-up + 사전학습 차단.

직전 라이브 평가 결손 회복: LLM이 "도화살" 사전학습 환각 → 결정론 산출만 인용 강제.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SERVER_PY = ROOT / "web" / "server.py"


def _src() -> str:
    return SERVER_PY.read_text(encoding="utf-8")


# ── ① server.py wire-up ────────────────────────────


def test_imports_compute_shensha():
    """server.py가 compute_shensha + SHENSHA_MEANINGS import."""
    src = _src()
    assert "from engine.saju.shensha import compute_shensha, SHENSHA_MEANINGS" in src


def test_imports_compute_pillars_for_4_pillars():
    """compute_pillars import (사용자 4기둥 신살 산출용)."""
    src = _src()
    assert "from engine.saju.pillars import compute_pillars" in src


def test_shensha_block_in_deterministic():
    """결정론 블록에 '신살 결정론 (ADR-089)' 명시."""
    src = _src()
    assert "신살 결정론 (ADR-089)" in src


def test_shensha_iterates_all_5_keys():
    """5 신살 모두 반복 (cheoneul·munchang·yeokma·dohwa·kongmang)."""
    src = _src()
    assert '"cheoneul"' in src
    assert '"munchang"' in src
    assert '"yeokma"' in src
    assert '"dohwa"' in src
    assert '"kongmang"' in src


def test_shensha_none_marker_present():
    """신살 부재 시 '(없음)' 명시."""
    src = _src()
    assert '"(없음)"' in src


def test_pretraining_block_directive_2():
    """[지시 2] 사전학습 차단 명시 — 도화살·역마살 등 명시 X 시 언급 금지."""
    src = _src()
    assert "[지시 2]" in src
    assert "사전학습 사주 지식 추가 금지" in src
    assert "ADR-010" in src


def test_directive_lists_5_shensha_names():
    """지시 2가 5 신살 이름 명시 (LLM이 어떤 용어 차단 대상인지 명확)."""
    src = _src()
    assert "천을귀인" in src
    assert "문창귀인" in src
    assert "역마살" in src
    assert "도화살" in src
    assert "공망" in src


def test_shensha_fallback_on_exception():
    """예외 시 '(신살 산출 실패)' fallback."""
    src = _src()
    assert "(신살 산출 실패)" in src


# ── ② 결정론 엔진 직접 호출 회귀 ─────────────────────


def test_shensha_live_call_user_case():
    """라이브 사례 (1990-05-15 庚辰 일주, 정오 시각) 신살 산출."""
    from engine.saju.pillars import compute_pillars
    from engine.saju.shensha import compute_shensha

    pillars = compute_pillars(1990, 5, 15, 12)
    result = compute_shensha(pillars)
    # 5 키 모두 존재
    assert set(result.keys()) == {"cheoneul", "munchang", "yeokma", "dohwa", "kongmang"}
    # 사용자 사례 (KASI 정합 庚辰 일주, 정오 = 庚午 시) 도화살 부재
    assert result["dohwa"] == [], (
        f"사용자 사례에 도화살 부재여야 함: {result['dohwa']}"
    )


def test_shensha_meanings_complete():
    """SHENSHA_MEANINGS 5 신살 라벨 + 한 줄 의미 모두 정합."""
    from engine.saju.shensha import SHENSHA_MEANINGS
    for key in ("cheoneul", "munchang", "yeokma", "dohwa", "kongmang"):
        assert key in SHENSHA_MEANINGS
        assert "label" in SHENSHA_MEANINGS[key]
        assert "summary" in SHENSHA_MEANINGS[key]


def test_dohwa_meaning_label():
    """도화살 라벨이 'dohwa' → '도화살'로 매핑."""
    from engine.saju.shensha import SHENSHA_MEANINGS
    assert SHENSHA_MEANINGS["dohwa"]["label"] == "도화살"
    assert SHENSHA_MEANINGS["yeokma"]["label"] == "역마살"


# ── ③ ADR-010 사실성 분리 강화 ──────────────────────


def test_shensha_only_outputs_explicit_results():
    """compute_shensha 결과가 명시 산출만 회신 (사전학습 X)."""
    from engine.saju.pillars import compute_pillars
    from engine.saju.shensha import compute_shensha

    # 1990-05-15 12시 — 도화살 부재 사례
    p1 = compute_pillars(1990, 5, 15, 12)
    r1 = compute_shensha(p1)
    assert isinstance(r1["dohwa"], list)
    assert isinstance(r1["yeokma"], list)
    assert isinstance(r1["kongmang"], list)
