"""ADR-097 회귀 — engine/divination/dream.py DREAM_SYSTEM 직접 정정.

라이브 평가 결과 server.py user 프롬프트 지시 (ADR-094·095·096)만으로 효과 부족.
LLM은 system 프롬프트 (DREAM_SYSTEM)을 더 강하게 준수 → DREAM_SYSTEM 자체에 강화.
"""


def test_dream_system_loaded():
    """DREAM_SYSTEM 모듈 로드 정합."""
    from engine.divination.dream import DREAM_SYSTEM
    assert isinstance(DREAM_SYSTEM, str)
    assert len(DREAM_SYSTEM) > 1500


# ── ADR-094 단정 차단 ──────────────────────────


def test_adr_094_block_in_system_prompt():
    """[ADR-094 단정 차단 — 절대] 시스템 프롬프트에 명시."""
    from engine.divination.dream import DREAM_SYSTEM
    assert "ADR-094" in DREAM_SYSTEM


def test_banned_words_listed_in_system():
    """길몽·흉몽·대길·대흉·반드시·확실히 6 어휘 차단 명시."""
    from engine.divination.dream import DREAM_SYSTEM
    for word in ["길몽", "흉몽", "대길", "대흉", "반드시", "확실히"]:
        assert word in DREAM_SYSTEM, f"단정 어휘 누락: {word}"


def test_polarity_disclaimer_in_system():
    """polarity:'길'/'흉' 라벨은 학파 분류일 뿐 운명 단정 X 명시."""
    from engine.divination.dream import DREAM_SYSTEM
    assert "polarity" in DREAM_SYSTEM
    assert "운명 단정 X" in DREAM_SYSTEM


# ── ADR-095 학파 명시 ──────────────────────────


def test_adr_095_school_quotation_obligation():
    """[ADR-095 학파 명시 의무] system 프롬프트에 명시."""
    from engine.divination.dream import DREAM_SYSTEM
    assert "ADR-095" in DREAM_SYSTEM
    assert "학파 명시 의무" in DREAM_SYSTEM


def test_school_examples_in_system():
    """학파 예시 명시 (아르테미도로스·융·홉슨·주역·동의보감)."""
    from engine.divination.dream import DREAM_SYSTEM
    examples = ["아르테미도로스", "융 원형", "한국 민간", "홉슨", "주역", "동의보감"]
    for example in examples:
        assert example in DREAM_SYSTEM, f"학파 예시 누락: {example}"


def test_min_2_schools_obligation():
    """학파 최소 2개 이상 명시 의무."""
    from engine.divination.dream import DREAM_SYSTEM
    assert "최소 2개 이상" in DREAM_SYSTEM or "학파 2+" in DREAM_SYSTEM
    assert "ADR-002" in DREAM_SYSTEM


# ── ADR-096 양면 해석 + 콘텐츠 적합성 ────────


def test_adr_096_dual_interpretation():
    """[ADR-096 양면 해석 의무] system 프롬프트 강화."""
    from engine.divination.dream import DREAM_SYSTEM
    assert "ADR-096" in DREAM_SYSTEM
    assert "양면 해석" in DREAM_SYSTEM


def test_each_paragraph_balance():
    """매 단락마다 강점·약점 동시 명시."""
    from engine.divination.dream import DREAM_SYSTEM
    assert "강점·기회" in DREAM_SYSTEM
    assert "약점·주의" in DREAM_SYSTEM
    assert "긍정 일색 풀이 금지" in DREAM_SYSTEM


def test_content_key_fitness_in_system():
    """content_key별 콘텐츠 적합성 명시."""
    from engine.divination.dream import DREAM_SYSTEM
    assert "content_key" in DREAM_SYSTEM
    assert "nightmare" in DREAM_SYSTEM
    assert "baby" in DREAM_SYSTEM
    assert "lucid" in DREAM_SYSTEM
    assert "recurring" in DREAM_SYSTEM


def test_nightmare_no_gilmong_in_system():
    """nightmare → '길몽' 절대 X 명시 (system 프롬프트)."""
    from engine.divination.dream import DREAM_SYSTEM
    assert "nightmare" in DREAM_SYSTEM
    # nightmare 라인에 '길몽' 차단 명시
    nightmare_section = DREAM_SYSTEM[DREAM_SYSTEM.index("nightmare"):]
    nightmare_line = nightmare_section.split("\n")[0]
    assert "'길몽' 절대 X" in nightmare_line or "길몽" in nightmare_line


def test_baby_taemong_schools_in_system():
    """baby → 태몽 학파 (한국 민속 + HvdC + 융 어머니 원형)."""
    from engine.divination.dream import DREAM_SYSTEM
    assert "태몽 학파" in DREAM_SYSTEM
    assert "HvdC 태몽 지수" in DREAM_SYSTEM


def test_lucid_laberge_dormio_in_system():
    """lucid → Stephen LaBerge + Dormio TDI."""
    from engine.divination.dream import DREAM_SYSTEM
    assert "Stephen LaBerge" in DREAM_SYSTEM
    assert "Dormio TDI" in DREAM_SYSTEM


def test_recurring_ptsd_irt_in_system():
    """recurring → PTSD·IRT 학파."""
    from engine.divination.dream import DREAM_SYSTEM
    assert "recurring" in DREAM_SYSTEM
    assert "PTSD·IRT" in DREAM_SYSTEM


# ── 기존 정합 유지 ──────────────────────


def test_existing_rules_preserved():
    """기존 시스템 프롬프트 핵심 규칙 보존."""
    from engine.divination.dream import DREAM_SYSTEM
    # 기존 핵심
    assert "해몽가" in DREAM_SYSTEM
    assert "한국어 존댓말" in DREAM_SYSTEM
    assert "단정적 예언 금지" in DREAM_SYSTEM
    assert "도메인 사실 블록" in DREAM_SYSTEM
    assert "다축 해석" in DREAM_SYSTEM


def test_28_domain_toolbox_preserved():
    """28 도메인 도구상자 명시 유지."""
    from engine.divination.dream import DREAM_SYSTEM
    assert "28 도메인 도구상자" in DREAM_SYSTEM
    assert "아르테미도로스" in DREAM_SYSTEM
    assert "황제내경" in DREAM_SYSTEM


def test_writing_format_preserved():
    """1200~1800자 작성 형식 유지."""
    from engine.divination.dream import DREAM_SYSTEM
    assert "1200~1800자" in DREAM_SYSTEM
