"""ADR-109 회귀 — 한자어 §26 ㄹ받침 + 평음 경음화 검증.

영역:
  · §23 (폐쇄음 종성 + 평음) — 기존 동작 보존
  · §26 (한자어 ㄹ + 평음 ㄷ·ㅅ·ㅈ) — 신규
  · 고유어 ㄹ + 평음 → 경음화 X (한자어 한정)

출처:
  · 표준 발음법 (1988 문교부 고시 제88-2호) §23·§26
  · 신지영(2010) "한국어 자음의 변별 자질" 한국언어학회
"""

from engine.divination.name.aesthetic import f_tensify


# ─────────────────────────── §23 기존 동작 보존 ───────────────────────────

def test_velar_coda_plain_initial_section_23():
    """§23 — ㄱ 종성 + ㅈ 초성 → ㅉ."""
    assert f_tensify("ㄱ", "ㅈ") == "ㅉ"


def test_alveolar_coda_section_23():
    """§23 — ㄷ 종성 + ㅂ 초성 → ㅃ."""
    assert f_tensify("ㄷ", "ㅂ") == "ㅃ"


def test_bilabial_coda_section_23():
    """§23 — ㅂ 종성 + ㅅ 초성 → ㅆ."""
    assert f_tensify("ㅂ", "ㅅ") == "ㅆ"


def test_non_plain_initial_no_change():
    """평음이 아닌 초성 → 변화 없음."""
    assert f_tensify("ㄱ", "ㅎ") is None
    assert f_tensify("ㄱ", "ㄴ") is None
    assert f_tensify("ㄱ", "ㅁ") is None


# ─────────────────────────── §26 한자어 ㄹ + 평음 경음화 ───────────────────────────

def test_sino_korean_l_plus_d_to_dd():
    """§26 — 한자어 ㄹ + ㄷ → ㄸ (결단[결딴])."""
    assert f_tensify("ㄹ", "ㄷ", is_sino_korean=True) == "ㄸ"


def test_sino_korean_l_plus_s_to_ss():
    """§26 — 한자어 ㄹ + ㅅ → ㅆ (발생[발쌩])."""
    assert f_tensify("ㄹ", "ㅅ", is_sino_korean=True) == "ㅆ"


def test_sino_korean_l_plus_j_to_jj():
    """§26 — 한자어 ㄹ + ㅈ → ㅉ (일정[일쩡])."""
    assert f_tensify("ㄹ", "ㅈ", is_sino_korean=True) == "ㅉ"


# ─────────────────────────── §26 고유어는 미적용 ───────────────────────────

def test_native_korean_l_no_tensification():
    """고유어 ㄹ 받침 + 평음 → 경음화 X (예: 들다, 살다)."""
    assert f_tensify("ㄹ", "ㄷ", is_sino_korean=False) is None
    assert f_tensify("ㄹ", "ㅅ", is_sino_korean=False) is None
    assert f_tensify("ㄹ", "ㅈ", is_sino_korean=False) is None


def test_default_is_native_korean():
    """is_sino_korean 미지정 시 고유어 처리 (기존 호환)."""
    assert f_tensify("ㄹ", "ㄷ") is None
    assert f_tensify("ㄹ", "ㅈ") is None


# ─────────────────────────── §26은 ㄱ·ㅂ에 미적용 ───────────────────────────

def test_sino_korean_l_plus_g_no_tensification():
    """한자어 ㄹ + ㄱ → 경음화 X (§26은 ㄷ·ㅅ·ㅈ만)."""
    # 발견(發見)[발견], 결과(結果)[결과] — ㄱ은 §26 대상 아님
    assert f_tensify("ㄹ", "ㄱ", is_sino_korean=True) is None


def test_sino_korean_l_plus_b_no_tensification():
    """한자어 ㄹ + ㅂ → 경음화 X (§26은 ㄷ·ㅅ·ㅈ만)."""
    # 절벽(絶壁)[절벽] — ㅂ은 §26 대상 아님
    assert f_tensify("ㄹ", "ㅂ", is_sino_korean=True) is None


# ─────────────────────────── §23과 §26 분리 ───────────────────────────

def test_section_23_not_affected_by_sino_korean_flag():
    """§23 폐쇄음 종성 + 평음은 sino_korean 무관."""
    # ㄱ + ㅈ → ㅉ (한자어 여부 무관)
    assert f_tensify("ㄱ", "ㅈ", is_sino_korean=True) == "ㅉ"
    assert f_tensify("ㄱ", "ㅈ", is_sino_korean=False) == "ㅉ"
