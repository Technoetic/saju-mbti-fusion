"""ADR-046 백엔드 import smoke — ADR-039·040 도메인 서브폴더 정합 검증."""


def test_divination_subpackages():
    """5 도메인 서브패키지 import (ADR-039)."""
    import engine.divination.name
    import engine.divination.face
    import engine.divination.palm
    import engine.divination.hwapae
    import engine.divination.saju_mbti
    import engine.divination.dream
    import engine.divination.dream_lex


def test_name_modules():
    """name 16 모듈 import."""
    from engine.divination.name import (
        aesthetic, baleum, bulyong, dueum, eumyang,
        gaeja, gaemyeong, hangul_hanja, reading,
        saju_ohaeng, saju_school, scoring,
        sibling_preference, strokes, unihan, uniqueness,
    )


def test_face_modules():
    """face 4 모듈 import."""
    from engine.divination.face import reading, scoring, shape, feature_classifier


def test_palm_modules():
    """palm 2 모듈 import."""
    from engine.divination.palm import reading, scoring


def test_hwapae_modules():
    """hwapae 2 모듈 import."""
    from engine.divination.hwapae import core, korean


def test_saju_mbti():
    """saju_mbti.predictor (ADR-039 + ADR-014)."""
    from engine.divination.saju_mbti import predictor


def test_safety_categories():
    """9 카테고리 서브패키지 (ADR-040)."""
    import engine.safety.crisis
    import engine.safety.gdpr
    import engine.safety.slo
    import engine.safety.audit
    import engine.safety.input_guards
    import engine.safety.incident
    import engine.safety.llm
    import engine.safety.photo
    import engine.safety.misc


def test_safety_re_exports():
    """engine.safety 4 핵심 함수 re-export (ADR-040 호환)."""
    from engine.safety import (
        detect_crisis,
        CRISIS_RESPONSE_KO,
        EMERGENCY_HOTLINES_KR,
        build_legal_footer,
    )
    assert callable(detect_crisis)
    assert callable(build_legal_footer)
    assert isinstance(CRISIS_RESPONSE_KO, str)
    assert isinstance(EMERGENCY_HOTLINES_KR, (dict, list))


def test_saju_core():
    """engine.saju 핵심 모듈 import."""
    from engine.saju import myeong, alias, explain, calendar, pillars, mbti_compat_v2


def test_web_server():
    """web.server import (모든 importer 정상)."""
    import web.server
