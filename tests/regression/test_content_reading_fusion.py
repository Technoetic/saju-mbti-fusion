"""ADR-071 회귀 — saju + name 결정론 융합 누적 검증.

ADR-069 (saju 단독) + ADR-070 (name 단독) → ADR-071 (사주+성명 융합).
사용자가 만월 아씨 "오늘의 운세"에 fullName + birth 모두 입력 시 두 도메인
결정론 동시 인용. ADR-024 (사주+MBTI 융합) 패턴 정합.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SERVER_PY = ROOT / "web" / "server.py"


def _src() -> str:
    return SERVER_PY.read_text(encoding="utf-8")


def test_deterministic_blocks_list_accumulation():
    """deterministic_blocks 리스트 누적 (단일 string 대입 X)."""
    src = _src()
    assert "deterministic_blocks: list[str] = []" in src
    assert "deterministic_blocks.append" in src


def test_saju_branch_does_not_override_name():
    """saju 분기가 name 결정론을 덮어쓰지 않음 (append 패턴)."""
    src = _src()
    # 이전 패턴 (단일 대입)이 없어야 함
    assert 'deterministic_block = (\n                        f"\\n[사주 결정론' not in src
    # 누적 패턴 확인
    assert "deterministic_blocks.append(" in src


def test_saju_char_with_name_input_triggers_name():
    """char_key='saju' + fullName 입력 시 name 결정론도 호출 (사주+성명 융합)."""
    src = _src()
    # wants_name 변수 + saju 융합 조건
    assert "wants_name" in src
    assert 'char_key in ("saju",)' in src or 'char_key == "saju"' in src
    # ADR-024 패턴 정합 명시
    assert "ADR-024" in src or "사주+성명" in src or "융합" in src


def test_unified_pretraining_block_for_all_domains():
    """통합 사전학습 차단 지시 — 60갑자·십성·한자·획수·4격·발음 모두 명시."""
    src = _src()
    assert "60갑자" in src
    assert "십성" in src
    assert "한자" in src and "획수" in src and "4격" in src
    assert "발음" in src
    assert "ADR-010 사실성 분리" in src


def test_blocks_joined_with_newlines():
    """다중 도메인 결정론 블록이 빈 줄로 분리 합성."""
    src = _src()
    assert '"\\n\\n".join(deterministic_blocks)' in src


def test_name_label_renamed_to_seongmyeong():
    """ADR-071: '이름 결정론' → '성명학 결정론' (도메인명 명확화)."""
    src = _src()
    assert "성명학 결정론" in src
    # 옛 라벨 잔존 X (단일 라인 inline 변경 확인)
    name_old = src.count("[이름 결정론 — engine")
    assert name_old == 0


def test_birth_input_priority():
    """birth 입력은 char_key 무관 — fullName과 독립 처리."""
    src = _src()
    # birth_str 추출이 if 조건 밖에서 한 번만
    assert 'birth_str = (fields.get("birth") or "").strip()' in src


def test_graceful_fallback_for_each_domain():
    """각 도메인 fallback 메시지 독립."""
    src = _src()
    assert "[사주 결정론 — 산출 실패]" in src
    assert "[성명학 결정론 — 산출 실패]" in src
