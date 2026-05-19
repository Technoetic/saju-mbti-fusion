"""ADR-046 백엔드 데이터 로드 smoke — ADR-041 path level 수정 검증."""
import json


def test_aesthetic_data():
    """name/aesthetic_syllable_freq.json 로드."""
    from engine.divination.name.aesthetic import _DATA_PATH
    d = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    assert isinstance(d, dict)
    assert len(d) > 0


def test_unihan_data():
    """hanja/korean_hanja_unihan.json 로드 — 9389+자."""
    from engine.divination.name.unihan import _DATA_PATH
    d = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    assert isinstance(d, (dict, list))
    assert len(d) >= 9389


def test_surname_data():
    """hanja/korean_surname_frequency.json 로드."""
    from engine.divination.name.uniqueness import _SURNAME_PATH
    d = json.loads(_SURNAME_PATH.read_text(encoding="utf-8"))
    assert isinstance(d, (dict, list))
    assert len(d) > 0


def test_palm_rules():
    """palm/scoring_rules.json 로드."""
    from engine.divination.palm.scoring import _RULES_PATH
    d = json.loads(_RULES_PATH.read_text(encoding="utf-8"))
    assert isinstance(d, (dict, list))


def test_twelve_stages():
    """saju/twelve_stages_mapping.json 로드 (ADR-031)."""
    from engine.saju.twelve_stages import _DATA_PATH
    d = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    assert isinstance(d, (dict, list))
    assert len(d) >= 9  # 10 천간 또는 12 운성


def test_sibling_preference():
    """name/sibling_preference.json 로드."""
    from engine.divination.name.sibling_preference import _DATA_PATH
    d = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    assert isinstance(d, (dict, list))
