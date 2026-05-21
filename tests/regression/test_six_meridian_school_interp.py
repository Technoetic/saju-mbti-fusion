"""ADR-103 회귀 — 육경형(六經形) 메타 + 다학파 해석 컨텍스트.

ADR-102 경계 명확화 핵심 회귀:
- 학파 라벨 (태양형·봉안 등) = knowledge.py 메타에만 격리
- classify_* 함수 출력 = 인체계측 용어만 (ADR-102 유지)

출처 (Phase 1 라이브 검증):
- PMC10568153 East Asian Medical Knowledge & Donguibogam
- hyungsang.or.kr 형상의학회 공식
- DBpia NODE11235666 마의상법 번역 난점
"""

from engine.divination.face.knowledge import (
    SIX_MERIDIAN_TYPES,
    FACE_SCHOOL_INTERPRETATIONS,
    get_six_meridian_by_key,
    get_school_interpretation_by_feature,
    format_school_interpretations_for_prompt,
)
from engine.divination.face.feature_classifier import (
    EYE_CANTHAL_UPSLANT,
    EYE_CANTHAL_NORMAL,
    EYE_CANTHAL_DOWNSLANT,
    classify_eye_canthal_tilt,
)


# ─────────────────────────────────────────────────────────────
# ① SIX_MERIDIAN_TYPES 무결성 (4 육경형)
# ─────────────────────────────────────────────────────────────


def test_six_meridian_4_types_exist():
    """태양형·태음형·소양형·소음형 4 육경형 존재 (보고서 §3.2)."""
    keys = {t.key for t in SIX_MERIDIAN_TYPES}
    assert keys == {"taeyang", "taeeum", "soyang", "soeum"}


def test_six_meridian_name_ko_no_school_label_pollution():
    """name_ko는 메타 풀에만 있음. 분류 함수 출력에는 노출 X (ADR-102)."""
    for t in SIX_MERIDIAN_TYPES:
        assert "형" in t.name_ko  # 학파 명칭


def test_six_meridian_anthropometric_label_no_school_terms():
    """★ anthropometric_label은 인체계측 용어만 (ADR-102 정합)."""
    for t in SIX_MERIDIAN_TYPES:
        # 학파 라벨 한자 노출 X
        assert "太陽" not in t.anthropometric_label
        assert "태양" not in t.anthropometric_label
        assert "鳳眼" not in t.anthropometric_label
        # 영문 인체계측 용어만 사용
        assert "_" in t.anthropometric_label  # snake_case 영문


def test_six_meridian_adr_006_safety_note_required():
    """모든 육경형 adr_006_safety_note 의무 — 질환 단정 차단."""
    for t in SIX_MERIDIAN_TYPES:
        assert "방광염" in t.adr_006_safety_note  # 질환 단정 차단 명시
        assert "운명" in t.adr_006_safety_note
        assert "ADR-006" in t.adr_006_safety_note


def test_six_meridian_primary_source_hyungsang():
    """primary_source는 형상의학회 (라이브 검증 통과)."""
    for t in SIX_MERIDIAN_TYPES:
        assert "hyungsang" in t.primary_source_url


def test_six_meridian_mediclassics_secondary_only():
    """mediclassics.kr는 secondary로만 사용 (LOW 검증)."""
    for t in SIX_MERIDIAN_TYPES:
        assert "mediclassics" in t.secondary_source_url
        # primary는 mediclassics 아님
        assert "mediclassics" not in t.primary_source_url


def test_get_six_meridian_by_key():
    """key 조회 함수."""
    t = get_six_meridian_by_key("taeyang")
    assert t is not None
    assert t.name_ko == "태양형"
    assert get_six_meridian_by_key("nonexistent") is None


# ─────────────────────────────────────────────────────────────
# ② FACE_SCHOOL_INTERPRETATIONS 무결성 (다학파 해석)
# ─────────────────────────────────────────────────────────────


def test_school_interp_3_features():
    """upturned_eye·square_jaw·prominent_nose 3 형태 해석 메타."""
    keys = {i.feature_key for i in FACE_SCHOOL_INTERPRETATIONS}
    assert keys == {"upturned_eye", "square_jaw", "prominent_nose"}


def test_school_interp_maui_hyungsang_dual_school():
    """각 형태당 마의상법·형상의학 2 학파 병행 (ADR-002)."""
    for interp in FACE_SCHOOL_INTERPRETATIONS:
        assert "maui" in interp.school_interpretations
        assert "hyungsang" in interp.school_interpretations


def test_school_interp_each_has_adr_006_warning():
    """각 학파 해석에 adr_006_warning 의무 (운명·질환 단정 차단)."""
    for interp in FACE_SCHOOL_INTERPRETATIONS:
        for s in interp.school_interpretations.values():
            assert "adr_006_warning" in s
            assert "X" in s["adr_006_warning"] or "단정 X" in s["adr_006_warning"]


def test_school_interp_source_url_required():
    """각 학파 해석에 source_url 의무 (ADR-010)."""
    for interp in FACE_SCHOOL_INTERPRETATIONS:
        for s in interp.school_interpretations.values():
            assert "source_url" in s
            assert s["source_url"].startswith("https://")


def test_school_interp_anthropometric_name_no_school_label():
    """anthropometric_name은 인체계측 용어 (학파 라벨 노출 X, ADR-102)."""
    for interp in FACE_SCHOOL_INTERPRETATIONS:
        # "봉안"·"태양형"·"현담비" 등 학파 라벨이 anthropometric_name에 노출되면 안 됨
        assert "봉안" not in interp.anthropometric_name
        assert "태양형" not in interp.anthropometric_name
        assert "현담비" not in interp.anthropometric_name


def test_get_school_interpretation_by_feature():
    """feature_key 조회 함수."""
    interp = get_school_interpretation_by_feature("upturned_eye")
    assert interp is not None
    assert interp.anthropometric_name == "외안각 상행형"
    assert get_school_interpretation_by_feature("nonexistent") is None


# ─────────────────────────────────────────────────────────────
# ③ format_school_interpretations_for_prompt (Stage 2 프롬프트 주입)
# ─────────────────────────────────────────────────────────────


def test_format_prompt_includes_school_labels():
    """Stage 2 프롬프트에 학파 라벨 포함 (메타 풀 → 프롬프트 격리 OK)."""
    text = format_school_interpretations_for_prompt("upturned_eye")
    assert text is not None
    assert "봉안" in text  # 마의상법 학파 라벨
    assert "태양형" in text  # 형상의학 학파 라벨


def test_format_prompt_includes_adr_warnings():
    """프롬프트에 ADR-002 다학파 + ADR-006 단정 차단 명시."""
    text = format_school_interpretations_for_prompt("upturned_eye")
    assert text is not None
    assert "ADR-002" in text
    assert "ADR-006" in text


def test_format_prompt_none_for_unknown_feature():
    """미존재 feature_key → None."""
    assert format_school_interpretations_for_prompt("nonexistent") is None


# ─────────────────────────────────────────────────────────────
# ④ ★ ADR-102 경계 회귀 — classify_* 출력은 학파 라벨 X
# ─────────────────────────────────────────────────────────────


def test_classify_canthal_tilt_no_school_label_in_output():
    """★ ADR-102 핵심 회귀 — classify_eye_canthal_tilt 출력은 인체계측 용어만."""
    r = classify_eye_canthal_tilt(12.0)
    assert r is not None
    # 학파 라벨 노출 X
    assert "봉안" not in r.tilt_type
    assert "태양형" not in r.tilt_type
    assert "삼백안" not in r.tilt_type
    # 인체계측 용어만
    assert r.tilt_type == EYE_CANTHAL_UPSLANT
    assert r.tilt_type == "외안각 상행형"


def test_eye_canthal_constants_no_school_pollution():
    """EYE_CANTHAL_* 상수에 학파 라벨 침투 X (ADR-102 유지)."""
    assert "봉안" not in EYE_CANTHAL_UPSLANT
    assert "태양형" not in EYE_CANTHAL_UPSLANT
    assert "현담비" not in EYE_CANTHAL_NORMAL
    assert "삼백안" not in EYE_CANTHAL_DOWNSLANT


def test_six_meridian_anthropometric_label_matches_classify_output_layer():
    """SixMeridianType.anthropometric_label은 classify_* 출력층 매핑용 (snake_case 영문)."""
    for t in SIX_MERIDIAN_TYPES:
        # snake_case 영문 — 분류 함수 출력 매핑 가능
        assert t.anthropometric_label.islower() or "_" in t.anthropometric_label
        # 한국어/한자 학파 라벨 X
        for school_term in ["태양", "태음", "소양", "소음", "鳳眼", "봉안"]:
            assert school_term not in t.anthropometric_label
