"""ADR-063 회귀 — 관상학 통설 지식 DB 검증.

본 시스템 face/knowledge.py가 학파 메타·삼정·12궁·한국 고유 통설을 영속화하되
ADR-002·006·010·015 정합 의무 자동 검증.
"""

from engine.divination.face.knowledge import (
    PHYSIOGNOMY_SCHOOLS,
    SAMJEONG_REGIONS,
    TWELVE_PALACES,
    KOREAN_FOLK_SCHOOLS,
    get_school_by_key,
    get_palace_by_key,
    format_schools_metadata_for_prompt,
    format_korean_folk_for_prompt,
)


def test_four_schools_present():
    """4 학파 메타 영속 (마의·유장·달마·신상)."""
    keys = {s.key for s in PHYSIOGNOMY_SCHOOLS}
    assert keys == {"maui", "yujang", "dalma", "sinsang"}


def test_schools_have_verified_urls():
    """모든 학파 1차 출처 URL 명시 (Phase B 검증 통과 출처)."""
    for s in PHYSIOGNOMY_SCHOOLS:
        assert s.primary_source_url.startswith("http")
        assert s.primary_source_url


def test_schools_adr_002_note_required():
    """ADR-002 정합 — 학파 차이 명시 의무."""
    for s in PHYSIOGNOMY_SCHOOLS:
        assert s.adr_002_note  # 빈 문자열 금지


def test_samjeong_options_a_and_b():
    """삼정 — 중국(옵션 A) + 한국(옵션 B) 병행 명시 (ADR-015)."""
    for r in SAMJEONG_REGIONS:
        assert r.chinese_school_emphasis
        assert r.korean_school_emphasis


def test_hajeong_korean_priority():
    """한국 통설 하정 우위 명시 (보고서 §3.1)."""
    hajeong = next(r for r in SAMJEONG_REGIONS if r.key == "hajeong")
    assert "한국" in hajeong.korean_school_emphasis
    assert "우위" in hajeong.korean_school_emphasis or "최고" in hajeong.korean_school_emphasis


def test_twelve_palaces_complete():
    """12궁 12개 모두 영속."""
    assert len(TWELVE_PALACES) == 12
    keys = {p.key for p in TWELVE_PALACES}
    expected = {
        "myeong", "gwanrok", "jaebaek", "jeontaek", "hyeongje", "nobok",
        "cheocheop", "janyeo", "jilek", "cheoni", "bokdeok", "bumo",
    }
    assert keys == expected


def test_twelve_palaces_no_fate_mapping_field():
    """ADR-006 — 12궁에 fate_mapping 필드 부재 (운명 단정 차단)."""
    for p in TWELVE_PALACES:
        # dataclass 필드 명시 확인
        assert hasattr(p, "anatomical_region")
        assert not hasattr(p, "fate_mapping")  # ★ 운명 매핑 금지


def test_korean_folk_three_items():
    """한국 고유 통설 3건 (하정·눈5할·비복순)."""
    assert len(KOREAN_FOLK_SCHOOLS) == 3
    keys = {k.key for k in KOREAN_FOLK_SCHOOLS}
    assert keys == {"hajeong-superiority", "eye-five-tenths", "biboksun-form"}


def test_biboksun_adr_006_safety_explicit():
    """★ 비복순 '패가망신' 운명 단정 차단 명시 (ADR-006)."""
    biboksun = next(k for k in KOREAN_FOLK_SCHOOLS if k.key == "biboksun-form")
    safety = biboksun.adr_006_safety_note
    # 채택 X 명시 + 형태 명칭만 허용 명시
    assert "패가망신" in safety  # 보고서 원문 언급
    assert "채택 X" in safety or "금지" in safety
    assert "형태" in safety or "명칭" in safety


def test_all_korean_folk_have_safety_notes():
    """모든 한국 고유 통설에 ADR-006 안전 장치 명시 의무."""
    for k in KOREAN_FOLK_SCHOOLS:
        assert k.adr_006_safety_note
        assert "운명" in k.adr_006_safety_note or "단정" in k.adr_006_safety_note


def test_get_school_by_key():
    """학파 조회 헬퍼."""
    maui = get_school_by_key("maui")
    assert maui is not None
    assert maui.name_ko == "마의상법"
    assert get_school_by_key("nonexistent") is None


def test_get_palace_by_key():
    """12궁 조회 헬퍼."""
    myeong = get_palace_by_key("myeong")
    assert myeong is not None
    assert myeong.label_ko == "명궁"
    assert get_palace_by_key("nonexistent") is None


def test_prompt_metadata_has_safety_clause():
    """Stage 2 프롬프트 주입 텍스트에 ADR-006 안전 절 자동 포함."""
    text = format_schools_metadata_for_prompt()
    assert "ADR-006" in text
    assert "운명" in text
    assert "금지" in text


def test_prompt_folk_warns_biboksun():
    """한국 고유 통설 프롬프트에 비복순 단정 차단 경고 자동 포함."""
    text = format_korean_folk_for_prompt()
    assert "비복순" in text or "패가망신" in text
    assert "금지" in text or "차단" in text


def test_dalma_philosophy_aligns_adr_006():
    """달마상법 (심상 철학) — ADR-006 정신 정합 명시."""
    dalma = get_school_by_key("dalma")
    assert dalma is not None
    assert "심상" in dalma.philosophical_core or "내면" in dalma.philosophical_core
