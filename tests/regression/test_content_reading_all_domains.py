"""ADR-074·075·076·077·078 회귀 — palm·face·star·dream·hwapae 결정론 직결.

ADR-071 사주+성명 융합 패턴을 5 도메인 전체로 확장.
char_key 매칭 시 각 도메인 결정론 엔진 호출 + 누적 패턴 정합.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SERVER_PY = ROOT / "web" / "server.py"


def _src() -> str:
    """server.py + web/handlers/*.py + web/schemas.py 합본.

    핸들러 본문이 web/handlers/*.py Mixin 으로 물리 분리되고
    Request 모델이 web/schemas.py 로 이동된 구조 리팩터링 이후에도
    핸들러 코드 문자열 grep 이 통과하도록 소스 전체를 합쳐서 반환한다.
    """
    parts = [SERVER_PY.read_text(encoding="utf-8")]
    schemas_py = ROOT / "web" / "schemas.py"
    if schemas_py.is_file():
        parts.append(schemas_py.read_text(encoding="utf-8"))
    handlers_dir = ROOT / "web" / "handlers"
    if handlers_dir.is_dir():
        for p in sorted(handlers_dir.glob("*.py")):
            parts.append(p.read_text(encoding="utf-8"))
    return "\n".join(parts)


# ── ADR-074 palm ────────────────────────────────────────────


def test_palm_branch_exists():
    """char_key='palm' 분기 + knowledge.py import."""
    src = _src()
    assert "wants_palm = char_key == \"palm\"" in src
    assert "from engine.divination.palm.knowledge import" in src
    assert "PALM_SCHOOLS" in src


def test_palm_block_includes_labels():
    """palm 블록에 4 보조선 라벨 명시."""
    src = _src()
    assert "FATE_LINE_STRAIGHT" in src
    assert "SUN_LINE_CLEAR" in src
    assert "MERCURY_LINE_CONTINUOUS" in src
    assert "MARRIAGE_LINE_SINGLE_CLEAR" in src


def test_palm_states_photo_requirement():
    """palm 블록이 사진 미입력 시 분류 불가 명시."""
    src = _src()
    assert "사진 미입력 시 라이브 분류 불가" in src


# ── ADR-075 face ────────────────────────────────────────────


def test_face_branch_exists():
    """char_key='face' 분기 + knowledge.py import."""
    src = _src()
    assert "wants_face = char_key == \"face\"" in src
    assert "from engine.divination.face.knowledge import" in src


def test_face_block_includes_structure():
    """face 블록에 학파·삼정·12궁 명시."""
    src = _src()
    assert "PHYSIOGNOMY_SCHOOLS" in src
    assert "SAMJEONG_REGIONS" in src
    assert "TWELVE_PALACES" in src


def test_face_real_attr_names():
    """face dataclass 실 필드 사용 (name_ko·label_ko)."""
    src = _src()
    assert "s.name_ko for s in PHYSIOGNOMY_SCHOOLS" in src
    assert "r.label_ko for r in SAMJEONG_REGIONS" in src
    assert "p.label_ko for p in TWELVE_PALACES" in src


def test_face_states_fate_mapping_absent():
    """face 블록이 단정 매핑 부재 명시 (ADR-006)."""
    src = _src()
    assert "단정 매핑 부재" in src or "fate_mapping" in src


# ── ADR-076 star ────────────────────────────────────────────


def test_star_branch_exists():
    """char_key='star' + birth 분기."""
    src = _src()
    assert "wants_star = char_key == \"star\" and bool(birth_str)" in src
    assert "from engine.divination.star.scoring import compute_daily_star_reading" in src


def test_star_block_real_fields():
    """star DailyStarReading 실 필드 (sign_label_ko·element_ko·modality_ko·daily_tone_ko)."""
    src = _src()
    assert "star_result.sign_label_ko" in src
    assert "star_result.element_ko" in src
    assert "star_result.modality_ko" in src
    assert "star_result.daily_tone_ko" in src


def test_star_outcome_absence_stated():
    """star 블록이 사랑·재물·진로 단정 부재 명시."""
    src = _src()
    assert "love_outcome" in src
    assert "career_outcome" in src
    assert "money_outcome" in src


# ── ADR-077 dream ───────────────────────────────────────────


def test_dream_branch_exists():
    """char_key='dream' + dreamText 분기."""
    src = _src()
    assert "wants_dream = char_key == \"dream\" and bool(dream_text)" in src
    assert "fields.get(\"dreamText\")" in src


def test_dream_block_includes_schools():
    """dream 블록에 12+ 도메인 학파 메타 (ADR-080 analyze_dream 풀 호출 결과)."""
    src = _src()
    # ADR-080 통합 후 analyze_dream 12+ 도메인 결과 인용 (학파 메타 → 결정론 결과)
    assert "Artemidorus" in src
    assert "Jung 원형" in src
    assert "Hobson 기이도" in src
    assert "한국 민속" in src or "korean_folk" in src
    assert "주역 64괘" in src


def test_dream_states_multi_school_obligation():
    """단일 학파 강요 X (ADR-002) 명시."""
    src = _src()
    assert "단일 학파 강요 X" in src or "다학파 병행" in src
    assert "ADR-002" in src


# ── ADR-078 hwapae ──────────────────────────────────────────


def test_hwapae_branch_exists():
    """char_key='hwapae' 분기."""
    src = _src()
    assert "wants_hwapae = char_key == \"hwapae\"" in src
    assert "from engine.divination.hwapae.korean import HWAPAE_CARDS, three_card_spread" in src


def test_hwapae_uses_day_seed():
    """hwapae 3장 추첨이 seed 결정론 (생일+오늘 hash) 사용."""
    src = _src()
    assert "hashlib.sha256" in src
    assert "three_card_spread((c0, c1, c2))" in src


def test_hwapae_real_field_category_dominance():
    """hwapae HwapaeSpreadResult 실 필드 (category_dominance, not dominant_category)."""
    src = _src()
    assert "spread.category_dominance" in src
    assert "spread.is_sequential" in src
    assert "spread.is_reverse" in src


# ── 통합: 누적 패턴 정합 ────────────────────────────────────


def test_all_5_domains_use_append():
    """5 신규 도메인 모두 append 누적 패턴 (단일 대입 X)."""
    src = _src()
    assert src.count("deterministic_blocks.append") >= 7  # saju + name + 5 신규 + fallback들


def test_all_5_domains_fallback_messages():
    """각 도메인 산출 실패 시 fallback 메시지 독립."""
    src = _src()
    assert "[손금 결정론 — 산출 실패]" in src
    assert "[관상 결정론 — 산출 실패]" in src
    assert "[황도대 결정론 — 산출 실패]" in src
    assert "[해몽 결정론 — 산출 실패]" in src
    assert "[화패 결정론 — 산출 실패]" in src


# ── 결정론 엔진 직접 호출 회귀 ──────────────────────────────


def test_palm_schools_loadable():
    """palm PALM_SCHOOLS 6개 풀 라이브."""
    from engine.divination.palm.knowledge import PALM_SCHOOLS
    assert len(PALM_SCHOOLS) == 6


def test_face_schools_loadable():
    """face PHYSIOGNOMY_SCHOOLS 4개 + SAMJEONG_REGIONS 3개 + TWELVE_PALACES 12개."""
    from engine.divination.face.knowledge import (
        PHYSIOGNOMY_SCHOOLS, SAMJEONG_REGIONS, TWELVE_PALACES,
    )
    assert len(PHYSIOGNOMY_SCHOOLS) == 4
    assert len(SAMJEONG_REGIONS) == 3
    assert len(TWELVE_PALACES) == 12


def test_star_live_call():
    """star compute_daily_star_reading 라이브 호출."""
    from datetime import date
    from engine.divination.star.scoring import compute_daily_star_reading
    r = compute_daily_star_reading(date(1990, 5, 15), date(2026, 5, 20))
    assert r.sign_label_ko  # "황소자리"
    assert r.element_ko     # "흙"
    assert r.daily_tone_ko  # 톤 명시


def test_hwapae_live_call():
    """hwapae three_card_spread 라이브 호출."""
    from engine.divination.hwapae.korean import HWAPAE_CARDS, three_card_spread
    assert len(HWAPAE_CARDS) >= 3  # 최소 3장 (three_card_spread 호출 가능)
    keys = list(HWAPAE_CARDS.keys())
    spread = three_card_spread((keys[0], keys[1], keys[2]))
    assert hasattr(spread, "category_dominance")
    assert hasattr(spread, "is_sequential")
