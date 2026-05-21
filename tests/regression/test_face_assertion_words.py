"""ADR-116 회귀 — face 운학 도사 단정 어휘 확장 차단 검증.

발견 사례 (2026-05-21 face 7 카드 라이브 검증):
- past-life 응답에 "길흉화복" 단어 누설
- feng-shui 응답에 "대운·금전수" 단어 누설

본 검증:
1. 단독 명사 형태 단정 어휘 (공백 미결합) 차단
2. 사용자 질문 echo 시에도 차단 동작
3. 운학 도사 운명 매핑 어휘 (길흉화복·대운·금전수·길운·흉운) 차단
4. 기존 단정 부사 + palm 어휘 미회귀
"""

from web.server import _sanitize_common_assertion_words


# ─────────────────────────── face 신규 단정 어휘 차단 (ADR-116) ───────────────────────────

def test_block_gilhyung_hwabok():
    """길흉화복 차단 (past-life 라이브 누설 사례)."""
    text = "흉상인지 길상인지, 길흉화복을 알고 싶어 하시는 마음을 헤아려 보겠습니다."
    out = _sanitize_common_assertion_words(text)
    assert "길흉화복" not in out
    assert "삶의 결의 흐름" in out


def test_block_daeun():
    """대운 차단 (feng-shui 라이브 누설)."""
    text = "그대에게 대운이 다가오는 시기로다"
    out = _sanitize_common_assertion_words(text)
    assert "대운" not in out
    assert "큰 흐름" in out


def test_block_geumjeonsu():
    """금전수 차단 (feng-shui 라이브 누설)."""
    text = "그대의 사주에 금전수가 깊으니"
    out = _sanitize_common_assertion_words(text)
    assert "금전수" not in out
    assert "재물의 결" in out


def test_block_jaemulsu_jaemulbok():
    """재물수·재물복 차단."""
    text1 = "재물수가 흐르는 시기"
    text2 = "재물복이 있는 분"
    out1 = _sanitize_common_assertion_words(text1)
    out2 = _sanitize_common_assertion_words(text2)
    assert "재물수" not in out1
    assert "재물복" not in out2


def test_block_gilun_hyungun():
    """길운·흉운 차단."""
    text = "올해는 길운이 흐르고, 내년은 흉운이 다가오니"
    out = _sanitize_common_assertion_words(text)
    assert "길운" not in out
    assert "흉운" not in out
    assert "좋은 흐름" in out
    assert "어려운 시기의 결" in out


def test_block_hakmunbok():
    """학문복 차단."""
    text = "학문복이 깊은 분"
    out = _sanitize_common_assertion_words(text)
    assert "학문복" not in out
    assert "배움의 결" in out


def test_block_gwanun():
    """관운 차단."""
    text = "관운이 트이는 시기"
    out = _sanitize_common_assertion_words(text)
    assert "관운" not in out
    assert "공직·직장의 결" in out


def test_block_hyungsang_ira():
    """흉상이라/길상이라 차단."""
    text1 = "그대는 흉상이라 하옵니다"
    text2 = "이 분은 길상이라 보입니다"
    out1 = _sanitize_common_assertion_words(text1)
    out2 = _sanitize_common_assertion_words(text2)
    assert "흉상이라" not in out1
    assert "길상이라" not in out2


def test_block_hyung_makeul():
    """흉을 막 차단 (feng-shui 라이브 사례)."""
    text = "풍수로 흉을 막을 수 있습니다"
    out = _sanitize_common_assertion_words(text)
    assert "흉을 막" not in out
    assert "어려움을 다스리" in out


def test_block_runmyung_fixed():
    """'운명은 늘 고정' 차단 (feng-shui 라이브 사례)."""
    text = "운명은 늘 고정된 것이 아니니"
    out = _sanitize_common_assertion_words(text)
    assert "운명은 늘 고정" not in out
    assert "흐름은 늘 변화" in out


# ─────────────────────────── 사용자 질문 echo 시에도 차단 ───────────────────────────

def test_user_question_echo_blocked():
    """LLM이 사용자 '길흉화복' 질문을 echo해도 차단."""
    text = "'제 관상이 흉상인지 길상인지 알고 싶어요. 길흉화복을 풀어주세요'하시는 마음"
    out = _sanitize_common_assertion_words(text)
    assert "길흉화복" not in out


def test_user_question_dae_un_echo_blocked():
    """LLM이 사용자 '대운·금전수' echo해도 차단."""
    text = "'대운·금전수 알려주세요' 하시며"
    out = _sanitize_common_assertion_words(text)
    assert "대운" not in out
    assert "금전수" not in out


# ─────────────────────────── 기존 단정 부사 + palm 어휘 미회귀 ───────────────────────────

def test_legacy_assertion_adverbs_preserved():
    """기존 단정 부사 (반드시·확실히·100%·절대·틀림없이) 차단 유지."""
    text = "반드시 그렇고, 확실히 100% 절대 틀림없이 일어납니다"
    out = _sanitize_common_assertion_words(text)
    assert "반드시" not in out
    assert "확실히" not in out
    assert "100%" not in out
    assert "절대 " not in out
    assert "틀림없이" not in out


def test_palm_assertion_preserved():
    """ADR-113 palm 어휘 (이혼·재혼·우울증·정신질환) 차단 유지."""
    text = "이혼할 운명이며 재혼할 가능성. 우울증·정신질환 위험"
    out = _sanitize_common_assertion_words(text)
    assert "이혼할" not in out
    assert "재혼할" not in out
    assert "우울증" not in out
    assert "정신질환" not in out


def test_dameong_bulhang_preserved():
    """단명할·불행한 말년 차단 유지 (ADR-113)."""
    text = "단명할 관상이며 불행한 말년"
    out = _sanitize_common_assertion_words(text)
    assert "단명할" not in out
    assert "불행한 말년" not in out


# ─────────────────────────── 정상 한국어 보존 ───────────────────────────

def test_normal_korean_preserved():
    """정상 한국어 문장 변경 X."""
    text = "그대의 얼굴은 균형 잡힌 인상이로다. 허허."
    out = _sanitize_common_assertion_words(text)
    assert out == text


def test_face_response_realistic():
    """face 라이브 실 사례 — 단정 어휘 모두 차단."""
    text = (
        "흉상이라 하여 너무 낙심 마시라. 운명은 늘 고정된 것이 아니니, "
        "지혜롭게 대처하면 길운을 열 수도 있는 법이오. "
        "대운·금전수 알려주세요 하시며..."
    )
    out = _sanitize_common_assertion_words(text)
    # 모든 단정 어휘 차단
    assert "흉상이라" not in out
    assert "운명은 늘 고정" not in out
    assert "길운" not in out
    assert "대운" not in out
    assert "금전수" not in out
    # 대체 어휘 정합
    assert "어려운 시기의 결" not in out  # 'feng-shui'에서 '흉운' 아닌 '흉상' 차단만
    assert "큰 흐름" in out
    assert "재물의 결" in out
