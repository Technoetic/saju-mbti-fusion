"""ADR-080 회귀 — dream 도메인 analyze_dream 풀 호출 + PersonalContext 통합.

ADR-077 학파 메타만 → ADR-080 analyze_dream 12+ 도메인 풀 호출.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SERVER_PY = ROOT / "web" / "server.py"


def _src() -> str:
    return SERVER_PY.read_text(encoding="utf-8")


# ── ① server.py 통합 정합 ──────────────────────────


def test_dream_imports_analyze_dream():
    """server.py가 analyze_dream 풀 호출."""
    src = _src()
    assert "from engine.divination.dream import analyze_dream" in src


def test_dream_imports_personal_context():
    """server.py가 PersonalContext 빌더 import."""
    src = _src()
    assert "from engine.divination.dream_lex.personal_context import build_context_from_dict" in src


def test_dream_builds_context_from_fields():
    """dream 분기가 사용자 입력 + 사주 맥락 ctx 빌드."""
    src = _src()
    assert "ctx_data = {" in src
    assert "ctx = build_context_from_dict(ctx_data)" in src


def test_dream_calls_analyze_dream():
    """dream 분기가 analyze_dream(dream_text, ctx) 호출."""
    src = _src()
    assert "analysis = analyze_dream(dream_text, ctx)" in src


def test_dream_includes_saju_context_when_birth():
    """birth 입력 시 day_pillar로 ctx_data['day_master'] 자동 주입."""
    src = _src()
    assert 'ctx_data["day_master"]' in src
    assert "from engine.saju.pillars import day_pillar as _dp_dream" in src


def test_dream_block_includes_12_domains():
    """dream 블록이 12+ 도메인 결과 인용."""
    src = _src()
    assert "Artemidorus" in src
    assert "Hobson 기이도" in src
    assert "Revonsuo TST 위협" in src
    assert "오행 매핑" in src
    assert "한국 민속" in src
    assert "Jung 원형" in src
    assert "Hall-Van de Castle" in src
    assert "주역 64괘" in src


# ── ② analyze_dream 라이브 호출 회귀 ───────────────────


def test_analyze_dream_returns_30_domains():
    """analyze_dream이 30개 도메인 결정론 결과 반환."""
    from engine.divination.dream import analyze_dream
    from engine.divination.dream_lex.personal_context import PersonalContext
    ctx = PersonalContext(gender="M")
    result = analyze_dream("하늘을 나는 꿈", ctx)
    assert len(result) >= 28
    # 핵심 학파 키 확인
    assert "artemidorus_class" in result
    assert "hobson" in result
    assert "tst" in result
    assert "wuxing" in result
    assert "korean_folk" in result
    assert "archetypes" in result
    assert "hvdc" in result
    assert "iching" in result


def test_personal_context_saju_fields():
    """PersonalContext 사주 통합 필드 정합."""
    from engine.divination.dream_lex.personal_context import PersonalContext
    import dataclasses
    fields = {f.name for f in dataclasses.fields(PersonalContext)}
    # 사주 통합 필드 6개
    assert "day_master" in fields
    assert "day_master_element" in fields
    assert "yongsin" in fields
    assert "current_daewoon_element" in fields
    assert "saju_summary" in fields
    assert "mbti" in fields


def test_build_context_from_dict_default_safe():
    """build_context_from_dict 빈 dict 안전."""
    from engine.divination.dream_lex.personal_context import build_context_from_dict
    ctx = build_context_from_dict({})
    assert ctx.name is None
    assert ctx.current_concerns == []


def test_build_context_with_saju_data():
    """build_context_from_dict 사주 데이터 정합 통합."""
    from engine.divination.dream_lex.personal_context import build_context_from_dict
    ctx = build_context_from_dict({
        "name": "홍길동",
        "gender": "M",
        "day_master": "乙",
        "day_master_element": "木",
        "mbti": "INTJ",
    })
    assert ctx.name == "홍길동"
    assert ctx.day_master == "乙"
    assert ctx.day_master_element == "木"
    assert ctx.mbti == "INTJ"


# ── ③ 도메인 가중치 규칙 ────────────────────────────


def test_context_weighting_rules_count():
    """CONTEXT_WEIGHTING_RULES 5개 (임신·사업가·학생·미혼·노년)."""
    from engine.divination.dream_lex.personal_context import CONTEXT_WEIGHTING_RULES
    assert len(CONTEXT_WEIGHTING_RULES) == 5


def test_pregnant_context_boost():
    """임신 시 태몽 가중 규칙 존재."""
    from engine.divination.dream_lex.personal_context import CONTEXT_WEIGHTING_RULES
    boosts = [r["boost"] for r in CONTEXT_WEIGHTING_RULES]
    assert any("태몽" in b for b in boosts)
