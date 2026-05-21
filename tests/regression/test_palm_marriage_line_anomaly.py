"""ADR-113 회귀 — 결혼선 Grade IV 이상치 감지 + 정량 임계값 + 단정 어휘 확장 검증.

영역:
  · line_count >= 4: Cannon 1994 Grade IV 이상치 격리 (결혼·이혼 hard-block)
  · 정량 분포 (길이 P25·Median·P75, 개수 분포)
  · PubMed 7986776 출처 자동 포함
  · 단정 어휘 차단 확장 (이혼·재혼·우울증·정신질환)

출처:
  · Cannon M et al. (1994) PMID 7986776 — 조현병 환자군 배타적 발현
  · Berr C (1992) PMID 1479321 — 85세 이상 표본
  · Bornholdt L (2015) PMID 26734989 — 노화 백색선 증가
"""

from engine.divination.palm.knowledge import (
    MARRIAGE_LINE_ABSENT,
    MARRIAGE_LINE_SINGLE_CLEAR,
    MARRIAGE_LINE_MULTIPLE,
    MARRIAGE_LINE_ANOMALY_HIGH_DENSITY,
    classify_marriage_line,
    get_marriage_line_normal_distribution,
)


# ─────────────────────────── ADR-113 Grade IV 이상치 격리 ───────────────────────────

def test_line_count_4_triggers_anomaly():
    """line_count=4 → Grade IV 이상치 격리 (Cannon 1994 PMID 7986776)."""
    r = classify_marriage_line(line_count=4, length_cm=None)
    assert r is not None
    assert r.shape_type == MARRIAGE_LINE_ANOMALY_HIGH_DENSITY


def test_line_count_5_triggers_anomaly():
    """line_count=5도 이상치 격리."""
    r = classify_marriage_line(line_count=5, length_cm=None)
    assert r is not None
    assert r.shape_type == MARRIAGE_LINE_ANOMALY_HIGH_DENSITY


def test_line_count_10_triggers_anomaly():
    """극단 다수 (10개)도 이상치."""
    r = classify_marriage_line(line_count=10, length_cm=None)
    assert r is not None
    assert r.shape_type == MARRIAGE_LINE_ANOMALY_HIGH_DENSITY


def test_anomaly_blocks_marriage_mapping():
    """이상치는 결혼·이혼 매핑 hard-block 면책 명시."""
    r = classify_marriage_line(line_count=4, length_cm=None)
    assert r is not None
    assert "결혼·이혼·연애 관계 매핑" in r.disclaimer
    assert "영구 차단" in r.disclaimer or "차단" in r.disclaimer
    assert "Cannon" in r.disclaimer or "7986776" in r.disclaimer


def test_anomaly_source_url_pubmed():
    """이상치 source_url은 PubMed 7986776."""
    r = classify_marriage_line(line_count=4, length_cm=None)
    assert r is not None
    assert "7986776" in r.source_url


# ─────────────────────────── 정상 범위 (line_count 0~3) ───────────────────────────

def test_line_count_0_absent():
    """0개 → 부재 (5% 빈도)."""
    r = classify_marriage_line(line_count=0, length_cm=None)
    assert r is not None
    assert r.shape_type == MARRIAGE_LINE_ABSENT


def test_line_count_1_single_clear():
    """1개 → 단일 (최빈 45%)."""
    r = classify_marriage_line(line_count=1, length_cm=0.7)
    assert r is not None
    assert r.shape_type == MARRIAGE_LINE_SINGLE_CLEAR


def test_line_count_2_multiple():
    """2개 → 다선 (35% 빈도)."""
    r = classify_marriage_line(line_count=2, length_cm=0.5)
    assert r is not None
    assert r.shape_type == MARRIAGE_LINE_MULTIPLE


def test_line_count_3_still_normal():
    """3개도 정상 변이 (15% 빈도, 보고서 §5.2)."""
    r = classify_marriage_line(line_count=3, length_cm=0.5)
    assert r is not None
    assert r.shape_type == MARRIAGE_LINE_MULTIPLE
    # 이상치 분류 아님 확인
    assert r.shape_type != MARRIAGE_LINE_ANOMALY_HIGH_DENSITY


# ─────────────────────────── 정량 분포 조회 ───────────────────────────

def test_normal_distribution_length_mm():
    """결혼선 길이 분포 — P25=4·Median=7·P75=9·이상치 15mm+."""
    d = get_marriage_line_normal_distribution()
    assert d["length_mm"]["p25"] == 4.0
    assert d["length_mm"]["median"] == 7.0
    assert d["length_mm"]["p75"] == 9.0
    assert d["length_mm"]["anomaly_threshold_mm"] == 15.0


def test_normal_distribution_count_distribution():
    """결혼선 개수 분포 — 0개 5%·1개 45%·2개 35%·3개+ 15%."""
    d = get_marriage_line_normal_distribution()
    pct = d["count_distribution_pct"]
    assert pct[0] == 5.0
    assert pct[1] == 45.0
    assert pct[2] == 35.0
    assert pct[3] == 15.0
    # 합계 100
    assert sum(pct.values()) == 100.0


def test_normal_distribution_anomaly_threshold():
    """이상치 최소 개수 = 4 (Cannon 1994 Grade IV)."""
    d = get_marriage_line_normal_distribution()
    assert d["anomaly_min_count"] == 4


def test_normal_distribution_source_pmid():
    """출처 PMID 7986776 명시."""
    d = get_marriage_line_normal_distribution()
    assert d["source_pmid"] == "7986776"
    assert d["source_year"] == 1994
    assert "Cannon" in d["source_first_author"]


# ─────────────────────────── 결정론 ───────────────────────────

def test_anomaly_deterministic():
    """동일 입력 → 동일 결과."""
    r1 = classify_marriage_line(line_count=5, length_cm=None)
    r2 = classify_marriage_line(line_count=5, length_cm=None)
    assert r1 == r2


# ─────────────────────────── 단정 어휘 차단 (palm 확장) ───────────────────────────

def test_sanitize_palm_assertion_words():
    """ADR-113 — palm 단정 어휘 차단 (이혼·재혼·우울증·정신질환)."""
    from web.server import _sanitize_common_assertion_words

    # 이혼·재혼·우울증·정신질환 어휘 차단 확인
    text = "당신은 이혼할 운명입니다."
    sanitized = _sanitize_common_assertion_words(text)
    assert "이혼할" not in sanitized
    assert "관계 변화" in sanitized


def test_sanitize_psychiatric_terms():
    """정신질환·우울증 단정 차단."""
    from web.server import _sanitize_common_assertion_words

    text = "이 손금은 우울증의 표현입니다."
    sanitized = _sanitize_common_assertion_words(text)
    assert "우울증" not in sanitized
    assert "감정의 결" in sanitized


def test_sanitize_legacy_words_preserved():
    """기존 단정 어휘 차단 동작 보존 (반드시·확실히·100%)."""
    from web.server import _sanitize_common_assertion_words

    text = "반드시 그러할 것입니다. 확실히 100% 옳습니다."
    sanitized = _sanitize_common_assertion_words(text)
    assert "반드시" not in sanitized
    assert "확실히" not in sanitized
    assert "100%" not in sanitized
