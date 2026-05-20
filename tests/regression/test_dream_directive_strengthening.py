"""ADR-094·095·096 회귀 — dream 도메인 단정 차단 + 학파 명시 + 콘텐츠 적합성.

라이브 7 콘텐츠 평가 결과:
- '길몽' 단정 5/7 콘텐츠 출현 (ADR-006 위반)
- 균형도 0~25% (3건 완전 긍정 편향)
- 학파 명시 0/7 (ADR-002 위반)

본 ADR로 dream 분기 system 프롬프트 강화.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SERVER_PY = ROOT / "web" / "server.py"


def _src() -> str:
    return SERVER_PY.read_text(encoding="utf-8")


# ── ① ADR-094 단정 차단 ─────────────────────────────


def test_adr_094_directive_present():
    """[지시 1 — ADR-094] 단정 차단 명시."""
    src = _src()
    assert "ADR-094" in src
    assert "[지시 1 — ADR-094 단정 차단]" in src


def test_dream_banned_words_listed():
    """길몽·흉몽·대길·대흉·반드시·확실히 명시 차단."""
    src = _src()
    # 각 어휘 따로 검증 (긴 문자열 정확 매칭 의존 X)
    for word in ["길몽", "흉몽", "대길", "대흉", "반드시", "확실히"]:
        assert word in src, f"단정 차단 어휘 누락: {word}"


def test_polarity_label_disclaimer():
    """polarity: 길/흉은 학파 라벨일 뿐 운명 단정 X 명시."""
    src = _src()
    assert "polarity: 길/흉" in src
    assert "운명 단정 X" in src
    assert "ADR-006" in src


# ── ② ADR-095 학파 명시 ───────────────────────────


def test_adr_095_directive_present():
    """[지시 2 — ADR-095] 학파 명시 의무."""
    src = _src()
    assert "ADR-095" in src
    assert "[지시 2 — ADR-095 학파 명시]" in src


def test_multi_school_examples_listed():
    """학파 명시 예시 (Artemidorus·Jung·한국 민속) 인용."""
    src = _src()
    assert "Artemidorus 분류상" in src
    assert "Jung 원형" in src
    assert "한국 민속 해몽서" in src


def test_multi_school_obligation():
    """단일 학파 단정 X — 다학파 병행 의무 (ADR-002)."""
    src = _src()
    assert "단일 학파 단정 X" in src
    assert "다학파 병행 의무" in src
    assert "ADR-002" in src


# ── ③ ADR-096 콘텐츠 적합성 ──────────────────────


def test_adr_096_directive_present():
    """[지시 3 — ADR-096] 콘텐츠 적합성 명시."""
    src = _src()
    assert "ADR-096" in src
    assert "[지시 3 — ADR-096 콘텐츠 적합성]" in src


def test_nightmare_no_gilmong():
    """nightmare 콘텐츠는 '길몽' 인용 X 명시."""
    src = _src()
    assert "nightmare → '길몽' 인용 X" in src
    assert "위협·불안·악몽 처리 권장" in src


def test_baby_taemong_schools():
    """baby 콘텐츠는 태몽 학파 (한국 민속 + Hall-Van de Castle) 인용."""
    src = _src()
    assert "baby → 태몽 학파" in src
    assert "Hall-Van de Castle 태몽 지수" in src


def test_lucid_dormio_laberge():
    """lucid 콘텐츠는 Stephen LaBerge + Dormio TDI 학파 명시."""
    src = _src()
    assert "Stephen LaBerge 자각몽" in src
    assert "Dormio TDI" in src


def test_recurring_ptsd_irt():
    """recurring 콘텐츠는 PTSD·IRT 학파 명시."""
    src = _src()
    assert "recurring → 반복 꿈" in src
    assert "PTSD·IRT" in src


# ── ④ 양면 해석 강화 ──────────────────────


def test_adr_096_balance_directive():
    """[지시 4 — ADR-006 양면 해석] 강점·약점·주의 동시 명시 의무."""
    src = _src()
    assert "[지시 4 — ADR-006 양면 해석]" in src
    assert "강점·약점·주의 동시 명시" in src
    assert "긍정 일색 풀이" in src
    assert "암묵적 단정" in src


def test_pretraining_block_dream():
    """사전학습 해몽 어휘 추가 금지 (ADR-010)."""
    src = _src()
    assert "사전학습 해몽 어휘 추가 금지" in src


# ── ⑤ 결정론 엔진 정합 ───────────────────


def test_korean_folk_polarity_data_integrity():
    """korean_folk.py polarity 데이터 영속 유지 (학파 분류 자체는 유지)."""
    from engine.divination.dream_lex.korean_folk import KOREAN_FOLK_CATEGORIES
    # 데이터셋 유지 — 본 ADR은 LLM 인용만 차단
    assert isinstance(KOREAN_FOLK_CATEGORIES, dict)
    assert len(KOREAN_FOLK_CATEGORIES) > 0


def test_dream_analyze_returns_30_domains():
    """analyze_dream 30 학파 결과 반환 (학파 명시 의무 충족 가능)."""
    from engine.divination.dream import analyze_dream
    from engine.divination.dream_lex.personal_context import PersonalContext
    result = analyze_dream("하늘을 나는 꿈", PersonalContext())
    assert len(result) >= 28
