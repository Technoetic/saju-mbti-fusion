"""engine.divination.name_aesthetic — 회귀 테스트.

ADR-016 부분 채택. 보고서 §2 인기 이름 빈도 기반.
ADR-010 사실성 분리 적용 (학술 인용 가짜 부분 미채택).
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 데이터 로드 ───────────────────────────


def test_data_loads():
    from engine.divination.name_aesthetic import total_syllables
    assert total_syllables("male") > 0
    assert total_syllables("female") > 0
    assert total_syllables("neutral") > 0


def test_top_syllables_male():
    """남자 1위 음절은 보고서 §2.1에 따라 '준'."""
    from engine.divination.name_aesthetic import get_top_syllables
    top = get_top_syllables("male", 1)
    assert top[0][0] == "준"


def test_top_syllables_female():
    """여자 1위 음절은 보고서 §2.2에 따라 '서'."""
    from engine.divination.name_aesthetic import get_top_syllables
    top = get_top_syllables("female", 1)
    assert top[0][0] == "서"


# ─────────────────────────── 점수 산출 ───────────────────────────


def test_popular_male_name_high_score():
    """'준' 음절 포함 남자 이름 → 높은 점수."""
    from engine.divination.name_aesthetic import aesthetic_score
    r = aesthetic_score("이준", gender="male")
    assert r.score > 0.5  # 1위 음절 포함


def test_popular_female_name_high_score():
    from engine.divination.name_aesthetic import aesthetic_score
    r = aesthetic_score("서아", gender="female")
    assert r.score > 0.5


def test_uncommon_name_low_score():
    """인기 통계에 없는 음절 → 0점."""
    from engine.divination.name_aesthetic import aesthetic_score
    r = aesthetic_score("괴짜", gender="male")
    assert r.score == 0.0


def test_score_normalized_0_to_1():
    """모든 점수는 0.0~1.0 범위."""
    from engine.divination.name_aesthetic import aesthetic_score
    for name in ["이준", "서아", "민준", "괴짜", "ㄱㄴ", ""]:
        for gender in ["male", "female", "neutral"]:
            r = aesthetic_score(name, gender=gender)
            assert 0.0 <= r.score <= 1.0


def test_empty_name_zero_score():
    from engine.divination.name_aesthetic import aesthetic_score
    r = aesthetic_score("", gender="male")
    assert r.score == 0.0


def test_non_korean_chars_ignored():
    """한글 외 문자는 점수 계산에서 제외."""
    from engine.divination.name_aesthetic import aesthetic_score
    r1 = aesthetic_score("이준", gender="male")
    r2 = aesthetic_score("이준ABC", gender="male")
    # 한글 음절은 같으므로 평균 점수 동일
    assert r1.score == r2.score


# ─────────────────────────── ADR-016 사용자 출력 의무 ───────────────────────────


def test_rationale_includes_disclaimer():
    """사용자 출력 rationale에 면책 의무 포함."""
    from engine.divination.name_aesthetic import aesthetic_score
    r = aesthetic_score("이준", gender="male")
    assert "추천 정렬 가점" in r.rationale
    assert "길흉" in r.rationale or "절대 기준이 아닙니다" in r.rationale


def test_rationale_no_causal_predictions():
    """사용자 출력에 인과 예언 표현 없음."""
    from engine.divination.name_aesthetic import aesthetic_score
    forbidden = ["단명", "요절", "큰 부자", "흉상", "길상", "운명을 결정"]
    for name in ["이준", "서아", "괴짜", "민준"]:
        r = aesthetic_score(name, gender="male")
        for word in forbidden:
            assert word not in r.rationale, f"인과 예언 표현 발견 '{word}' in '{r.rationale}'"


def test_rationale_no_absolute_assertions():
    """'어감이 좋다/나쁘다' 단정 금지."""
    from engine.divination.name_aesthetic import aesthetic_score
    forbidden = ["어감이 좋습니다", "어감이 나쁩니다", "이름이 좋습니다", "예언합니다"]
    for name in ["이준", "서아", "괴짜"]:
        r = aesthetic_score(name, gender="male")
        for word in forbidden:
            assert word not in r.rationale


# ─────────────────────────── 결정론 ───────────────────────────


def test_deterministic():
    """같은 입력 → 같은 결과."""
    from engine.divination.name_aesthetic import aesthetic_score
    r1 = aesthetic_score("이준", gender="male")
    r2 = aesthetic_score("이준", gender="male")
    assert r1.score == r2.score
    assert r1.rationale == r2.rationale


def test_gender_differentiation():
    """남자 인기 음절 → 남자 점수 > 여자 점수."""
    from engine.divination.name_aesthetic import aesthetic_score
    # '준'은 남자 압도적 1위, 여자에는 없음
    male = aesthetic_score("준수", gender="male")
    female = aesthetic_score("준수", gender="female")
    assert male.score > female.score
