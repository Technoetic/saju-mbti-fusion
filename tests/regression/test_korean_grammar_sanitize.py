"""ADR-117 회귀 — 한국어 응답 어미·단어 중복 정정 검증.

발견 사례 (2026-05-22 face 실 어진 라이브 검증):
- "평평한한" (어미 한 중복)
- "차분한한" (동일)
- "콧방울 들린 콧방울이로세" (단어 중복)
- "이마 넓음 평평함한" (조사·어미 깨짐)

본 검증:
1. 어미 중복 (X한한·X함한) 정정
2. 단어 중복 (콧방울 들린 콧방울) 정정
3. 조사 깨짐 (X음 평평함한) 정정
4. 정상 한국어 미변경
"""

from web.server import _sanitize_korean_grammar_dupes


# ─────────────────────────── 어미 중복 정정 (X한한 → X한) ───────────────────────────

def test_block_pyongpyong_double():
    """'평평한한' → '평평한'."""
    text = "이마는 넓은 평평한한 결에 주름은 없음이로구먼"
    out = _sanitize_korean_grammar_dupes(text)
    assert "평평한한" not in out
    assert "평평한" in out


def test_block_chabun_double():
    """'차분한한' → '차분한'."""
    text = "눈은 보통 차분한한 결이로다"
    out = _sanitize_korean_grammar_dupes(text)
    assert "차분한한" not in out
    assert "차분한" in out


def test_block_multiple_double_emi():
    """여러 어미 중복 동시 정정."""
    text = "평평한한 결, 차분한한 시선, 또렷한한 빛"
    out = _sanitize_korean_grammar_dupes(text)
    assert "평평한한" not in out
    assert "차분한한" not in out
    assert "또렷한한" not in out
    assert out.count("평평한") == 1
    assert out.count("차분한") == 1


# ─────────────────────────── 함한 → 함 정정 ───────────────────────────

def test_block_ham_han():
    """'X함한' → 'X함'."""
    text = "이마 넓음 평평함한 결"
    out = _sanitize_korean_grammar_dupes(text)
    # '평평함한' → '평평한' (위 어미 정정 패턴 + 'X음 평평함한' → 'X은 평평한')
    assert "함한" not in out


def test_block_eum_pyongpyong_ham_han():
    """'X음 평평함한' → 'X은 평평한' (조사 + 어미 정합)."""
    text = "이마 넓음 평평함한 결"
    out = _sanitize_korean_grammar_dupes(text)
    assert "넓음 평평함한" not in out
    # '넓은 평평한'으로 정정
    assert "넓은 평평한" in out


# ─────────────────────────── 단어 중복 정정 ───────────────────────────

def test_block_word_dupe_kotbangul():
    """'콧방울 들린 콧방울' → 단어 중복 제거."""
    text = "코는 콧대 곧은, 콧방울 들린 콧방울이로세"
    out = _sanitize_korean_grammar_dupes(text)
    # 후위 '콧방울' 중복 제거됨 (정확한 형태는 정규식에 따라 다름)
    # 핵심: '콧방울 들린 콧방울' 패턴 자체가 사라짐
    assert "콧방울 들린 콧방울" not in out


def test_word_dupe_kotbangul_full():
    """라이브 실 사례 — '콧방울 들린 콧방울이로세' 완전 차단."""
    text = "코는 콧대 곧은, 콧방울 들린 콧방울이로세."
    out = _sanitize_korean_grammar_dupes(text)
    # 전체 패턴 사라짐
    assert "콧방울 들린 콧방울" not in out


def test_word_dupe_preserved_normal():
    """정상 한국어에서 같은 단어 2회 정상 사용은 보존 (긴 거리)."""
    text = "그대의 이마는 넓다. 이마 옆 광대뼈도 살집 있다."
    out = _sanitize_korean_grammar_dupes(text)
    # 긴 거리 (마침표 + 새 문장)는 정상 한국어
    assert out.count("이마") == 2


# ─────────────────────────── 정상 한국어 보존 ───────────────────────────

def test_normal_korean_unchanged():
    """정상 한국어 미변경."""
    text = "그대의 얼굴은 균형 잡힌 인상이로다. 허허."
    out = _sanitize_korean_grammar_dupes(text)
    assert out == text


def test_single_pyongpyong_preserved():
    """단일 '평평한' 보존."""
    text = "이마는 넓고 평평한 결이로다"
    out = _sanitize_korean_grammar_dupes(text)
    assert out == text


def test_palace_terms_preserved():
    """12궁·삼정 한자 라벨 보존."""
    text = "상정(上停·이마)·중정(中停·코)·하정(下停·턱) 결정론 인용"
    out = _sanitize_korean_grammar_dupes(text)
    assert "上停" in out
    assert "中停" in out
    assert "下停" in out


def test_hanja_preserved():
    """한자 보존 (사주·점성술 결정론 인용)."""
    text = "경진(庚辰) 일주 + 황소자리 24.4° + 묘수(昴宿)"
    out = _sanitize_korean_grammar_dupes(text)
    assert "庚辰" in out
    assert "황소자리" in out
    assert "昴宿" in out


# ─────────────────────────── face 실 어진 라이브 사례 ───────────────────────────

def test_real_sejong_response():
    """세종대왕 어진 라이브 응답 정정."""
    text = (
        "허허, 자, 보시게. 전체 윤곽은 긴 타원형에 대칭 결이로세. "
        "기색은 맑은이로다. 이마는 넓은 평평한한 결에 주름은 없음이로구먼. "
        "눈썹은 짙은 곧은하고, 눈은 보통 차분한한 결이로다."
    )
    out = _sanitize_korean_grammar_dupes(text)
    assert "평평한한" not in out
    assert "차분한한" not in out
    # 자연 보존
    assert "허허" in out
    assert "기색은 맑은이로다" in out
    assert "이마는 넓은" in out


# ─────────────────────────── 빈 입력 ───────────────────────────

def test_empty_text():
    """빈 텍스트 → 빈 텍스트."""
    assert _sanitize_korean_grammar_dupes("") == ""
    assert _sanitize_korean_grammar_dupes(None) is None  # type: ignore
