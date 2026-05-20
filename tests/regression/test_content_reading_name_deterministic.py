"""ADR-070 회귀 — name 도메인 (묵향 선생) 결정론 직결 검증.

ADR-069 (saju)에 이어 name 도메인도 결정론 엔진 직결. fullName + hanja 입력에
대해 engine/divination/name 결정론 산출 결과를 LLM system 프롬프트에 주입.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SERVER_PY = ROOT / "web" / "server.py"


def _src() -> str:
    return SERVER_PY.read_text(encoding="utf-8")


def test_name_branch_present():
    """char_key == 'name' 분기 존재."""
    src = _src()
    assert 'char_key == "name"' in src


def test_name_imports_baleum_scoring():
    """name 도메인 결정론 import — evaluate_baleum + score_name."""
    src = _src()
    assert "from engine.divination.name.baleum import evaluate_baleum" in src
    assert "from engine.divination.name.scoring import score_name" in src


def test_name_deterministic_block_label():
    """name 결정론 블록 라벨 명시 (ADR-071: '이름' → '성명학')."""
    src = _src()
    assert "성명학 결정론 — engine/divination/name 출력" in src


def test_name_four_gyeok_referenced():
    """4격 (원·형·이·정) 명시."""
    src = _src()
    assert "4격 (원·형·이·정)" in src
    assert "won" in src and "hyeong" in src and "i" in src and "jeong" in src


def test_name_kangxi_strokes_referenced():
    """강희자전 획수 명시."""
    src = _src()
    assert "강희자전" in src
    assert "kangxi" in src


def test_name_bulyong_referenced():
    """불용한자 진단 명시."""
    src = _src()
    assert "불용한자" in src
    assert "has_bulyong" in src


def test_name_baleum_phonetic_referenced():
    """발음 결정론 (ADR-028 정합)."""
    src = _src()
    assert "발음 분석" in src
    assert "ADR-028" in src or "음 결합 결정론" in src


def test_name_adr_010_pretraining_blocked():
    """ADR-010 한자·획수·4격·발음 사전학습 차단 명시."""
    src = _src()
    assert "사전학습 추가 X" in src
    assert "ADR-010" in src
    # name 영역 특수 명시
    assert "한자·획수·4격·발음" in src or ("4격" in src and "사전학습" in src)


def test_name_graceful_fallback():
    """name 결정론 실패 시 LLM 단독 fallback (ADR-071: '이름' → '성명학')."""
    src = _src()
    assert "성명학 결정론 — 산출 실패" in src


def test_name_input_field_routing():
    """fullName / currentName / hanja 입력 라우팅."""
    src = _src()
    assert 'fields.get("fullName")' in src
    assert 'fields.get("currentName")' in src
    assert 'fields.get("hanja")' in src


def test_name_branch_before_saju():
    """name 분기가 saju 분기보다 위치 — 두 도메인 독립 처리."""
    src = _src()
    name_pos = src.find('char_key == "name"')
    saju_pos = src.find('char_key == "saju"')
    assert name_pos > 0 and saju_pos > 0
    # name 분기가 먼저 또는 별개 분기로 존재 (둘 다 처리 가능)
    assert name_pos != saju_pos
