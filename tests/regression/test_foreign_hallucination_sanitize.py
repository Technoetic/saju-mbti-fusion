"""ADR-115 회귀 — 한국어 응답 중 다국어 hallucination 차단 검증.

발견 사례 (2026-05-21 face 길상·흉상 라이브 검증):
- 운학 도사 응답에 포르투갈어 'saudável' (건강한) 침입
- "세로로 길게 뻗은 saudável 균형을 이루고 있구먼"

본 검증:
1. 악센트 부호 라틴 단어 (포르투갈어·스페인어·프랑스어·독일어) 제거
2. ASCII 영문 식별자 (ADR·KCI·PMID·MBTI·Sun·element 등) 보존
3. 공백 정리
"""

from web.server import _sanitize_foreign_hallucination


# ─────────────────────────── 발견 사례 차단 ───────────────────────────

def test_block_portuguese_saudavel():
    """포르투갈어 'saudável' 차단 (face 라이브 검증 실 사례)."""
    text = "그대의 얼굴은 세로로 길게 뻗은 saudável 균형을 이루고 있구먼"
    out = _sanitize_foreign_hallucination(text)
    assert "saudável" not in out
    # 한국어 흐름 보존
    assert "세로로 길게 뻗은" in out
    assert "균형을 이루고 있구먼" in out


def test_block_french_elegant():
    """프랑스어 'élégant' 차단."""
    text = "그대의 모습은 élégant 자태로 비치는구나"
    out = _sanitize_foreign_hallucination(text)
    assert "élégant" not in out
    assert "그대의 모습은" in out


def test_block_spanish_senor():
    """스페인어 'señor' 차단."""
    text = "이 señor의 풍모가 깊으시군"
    out = _sanitize_foreign_hallucination(text)
    assert "señor" not in out


def test_block_german_schon():
    """독일어 'schön' 차단."""
    text = "정말 schön 한 인상이로다"
    out = _sanitize_foreign_hallucination(text)
    assert "schön" not in out


# ─────────────────────────── ASCII 영문 식별자 보존 ───────────────────────────

def test_preserve_adr_identifier():
    """ADR 식별자 보존."""
    text = "ADR-006 자문 거절 정신상 단정 차단합니다."
    out = _sanitize_foreign_hallucination(text)
    assert "ADR-006" in out


def test_preserve_kci_pmid():
    """KCI·PMID 출처 식별자 보존."""
    text = "KCI 등재 + PMID 7986776 검증 통과한 출처입니다."
    out = _sanitize_foreign_hallucination(text)
    assert "KCI" in out
    assert "PMID" in out
    assert "7986776" in out


def test_preserve_mbti_terms():
    """MBTI 영문 식별자 보존."""
    text = "MBTI 16유형 중 INTJ·ENTP 등 단정 X"
    out = _sanitize_foreign_hallucination(text)
    assert "MBTI" in out
    assert "INTJ" in out
    assert "ENTP" in out


def test_preserve_astrology_terms():
    """점성술 영문 식별자 보존 (Sun·Moon·element 등)."""
    text = "Sun·Moon·Ascendant 빅3 — element·modality 매트릭스"
    out = _sanitize_foreign_hallucination(text)
    assert "Sun" in out
    assert "Moon" in out
    assert "Ascendant" in out
    assert "element" in out
    assert "modality" in out


def test_preserve_eu_ai_act():
    """EU AI Act 식별자 보존 (면책 텍스트 의무)."""
    text = "EU AI Act §50 의무 고지 — AI 시스템에 의해 생성된 콘텐츠입니다."
    out = _sanitize_foreign_hallucination(text)
    assert "EU AI Act" in out


# ─────────────────────────── 공백·문장 흐름 보존 ───────────────────────────

def test_consecutive_spaces_cleanup():
    """차단 후 연속 공백 정리."""
    text = "그대는 saudável 한 인상이로다."
    out = _sanitize_foreign_hallucination(text)
    # 연속 공백 없음
    assert "  " not in out
    assert "그대는" in out
    assert "한 인상이로다" in out


def test_punctuation_attachment():
    """문장 부호 앞 공백 제거."""
    text = "그대 모습은 schön ."
    out = _sanitize_foreign_hallucination(text)
    # ' .' 형태 자연 정리
    assert " ." not in out or out.endswith(".")


# ─────────────────────────── 빈 입력 ───────────────────────────

def test_empty_text():
    """빈 텍스트 → 빈 텍스트."""
    assert _sanitize_foreign_hallucination("") == ""
    assert _sanitize_foreign_hallucination(None) is None  # type: ignore


# ─────────────────────────── 순수 한국어 + 한자 보존 ───────────────────────────

def test_pure_korean_unchanged():
    """순수 한국어는 변경 X."""
    text = "그대의 얼굴은 균형 잡힌 인상이로다. 허허."
    out = _sanitize_foreign_hallucination(text)
    assert out == text


def test_korean_with_hanja_preserved():
    """한국어 + 한자 (上停·中停·下停 등) 보존."""
    text = "상정(上停·이마)·중정(中停·코)·하정(下停·턱) 결정론 인용"
    out = _sanitize_foreign_hallucination(text)
    assert "上停" in out
    assert "中停" in out
    assert "下停" in out


# ─────────────────────────── 혼합 케이스 ───────────────────────────

def test_mixed_korean_foreign_ascii():
    """한국어 + 포르투갈어 hallucination + ASCII 영문 식별자 — 외래만 제거."""
    text = "ADR-006 정신상 saudável (포르투갈어 침입) 차단합니다. KCI 출처 보존."
    out = _sanitize_foreign_hallucination(text)
    assert "saudável" not in out
    assert "ADR-006" in out
    assert "KCI" in out
    assert "차단합니다" in out


def test_real_face_response_excerpt():
    """face 라이브 검증 실 사례 — 운학 도사 응답에 saudável 침입."""
    text = (
        "허허, 이 늙은이가 보시겠네. "
        "그대의 얼굴 윤곽은 긴 타원형이라, 세로로 길게 뻗은 saudável 균형을 이루고 있구먼. "
        "좌우가 대칭적이니 겉으로 보기에는 단정한 인상이로다."
    )
    out = _sanitize_foreign_hallucination(text)
    assert "saudável" not in out
    # 한국어 문장 자연 보존
    assert "허허" in out
    assert "이 늙은이가 보시겠네" in out
    assert "긴 타원형이라" in out
    assert "균형을 이루고 있구먼" in out
    assert "단정한 인상이로다" in out
