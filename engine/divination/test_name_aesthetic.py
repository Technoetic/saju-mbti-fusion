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


# ─────────────────────────── 음운 결합 (보고서 §1) ───────────────────────────


def test_jamo_decomposition():
    """한글 음절 → (초성, 중성, 종성) 분해."""
    from engine.divination.name_aesthetic import _decompose_jamo
    # '준' = ㅈ + ㅜ + ㄴ
    assert _decompose_jamo("준") == ("ㅈ", "ㅜ", "ㄴ")
    # '서' = ㅅ + ㅓ (종성 없음)
    assert _decompose_jamo("서") == ("ㅅ", "ㅓ", "")
    # 비한글 음절
    assert _decompose_jamo("A") is None


def test_phonetic_combination_smooth():
    """ㄴ 받침 + ㅇ → 자연 결합 (보고서 §1 예시)."""
    from engine.divination.name_aesthetic import phonetic_combination_score
    # '선영' — 선(종성 ㄴ) + 영(초성 ㅇ) = 자연
    result = phonetic_combination_score("선영")
    assert result["smooth_count"] >= 1
    assert result["awkward_count"] == 0
    assert result["score"] > 0


def test_phonetic_combination_awkward():
    """ㄱ 받침 + ㅍ → 자음군 회피 위반 (보고서 §1 예시)."""
    from engine.divination.name_aesthetic import phonetic_combination_score
    # '박파' — 박(종성 ㄱ) + 파(초성 ㅍ) = 어색
    result = phonetic_combination_score("박파")
    assert result["awkward_count"] >= 1
    assert result["score"] < 0


def test_phonetic_combination_single_syllable():
    """1음절 — 결합 평가 불가, score 0."""
    from engine.divination.name_aesthetic import phonetic_combination_score
    result = phonetic_combination_score("준")
    assert result["score"] == 0.0
    assert len(result["pairs"]) == 0


def test_phonetic_combination_score_normalized():
    """모든 점수 [-1.0, 1.0] 범위."""
    from engine.divination.name_aesthetic import phonetic_combination_score
    for name in ["선영", "박파", "이준", "서아", "준수"]:
        result = phonetic_combination_score(name)
        assert -1.0 <= result["score"] <= 1.0


def test_phonetic_combination_rationale_includes_disclaimer():
    """음운 결합 사용자 출력 면책 의무."""
    from engine.divination.name_aesthetic import phonetic_combination_score
    result = phonetic_combination_score("선영")
    assert "추천 정렬 가점" in result["rationale"]
    assert "길흉" in result["rationale"] or "절대 기준이 아닙니다" in result["rationale"]


def test_phonetic_combination_rationale_no_causal():
    """음운 결합 출력에 인과 예언 없음."""
    from engine.divination.name_aesthetic import phonetic_combination_score
    forbidden = ["단명", "운명", "길흉을 결정", "운세"]
    for name in ["선영", "박파", "이준"]:
        result = phonetic_combination_score(name)
        for word in forbidden:
            assert word not in result["rationale"]


def test_phonetic_normalize_coda():
    """복합 종성 → 표준 7자음 정규화."""
    from engine.divination.name_aesthetic import _normalize_coda
    # ㅍ → ㅂ (표준발음법 제8항)
    assert _normalize_coda("ㅍ") == "ㅂ"
    # ㅋ → ㄱ
    assert _normalize_coda("ㅋ") == "ㄱ"
    # ㄴ 그대로
    assert _normalize_coda("ㄴ") == "ㄴ"
    # 빈 종성
    assert _normalize_coda("") == ""


def test_phonetic_deterministic():
    """같은 입력 → 같은 결과."""
    from engine.divination.name_aesthetic import phonetic_combination_score
    r1 = phonetic_combination_score("선영")
    r2 = phonetic_combination_score("선영")
    assert r1["score"] == r2["score"]
    assert r1["smooth_count"] == r2["smooth_count"]


# ─────────────────────────── 위치별 음절 (보고서 §2 본문 명시) ───────────────────────────


def test_male_top_end_syllable_is_jun():
    """남자 끝 음절 1위는 보고서 §2 본문 명시대로 '준'."""
    from engine.divination.name_aesthetic import get_top_positional_syllables
    top = get_top_positional_syllables("male", "end", 1)
    assert top[0][0] == "준"


def test_female_top_end_syllables():
    """여자 끝 음절 상위 2개 — '아', '윤' (보고서 §2 본문 명시)."""
    from engine.divination.name_aesthetic import get_top_positional_syllables
    top = get_top_positional_syllables("female", "end", 2)
    top_syllables = {item[0] for item in top}
    assert top_syllables == {"아", "윤"}


def test_position_match_jun_ending():
    """'이준' (준으로 끝남) → 끝 음절 점수 1.0 (남자 끝 1위)."""
    from engine.divination.name_aesthetic import position_match_score
    r = position_match_score("이준", gender="male")
    assert r["end_syllable"] == "준"
    assert r["end_score"] == 1.0


def test_position_match_uncommon():
    """비인기 시작·끝 음절 → 낮은 점수."""
    from engine.divination.name_aesthetic import position_match_score
    r = position_match_score("괴짜", gender="male")
    assert r["combined_score"] < 0.3


def test_position_match_single_syllable():
    """1음절 → 위치 평가 불가."""
    from engine.divination.name_aesthetic import position_match_score
    r = position_match_score("준", gender="male")
    assert r["combined_score"] == 0.0


def test_position_score_normalized():
    """위치 점수 모두 [0.0, 1.0]."""
    from engine.divination.name_aesthetic import position_match_score
    for name in ["이준", "서아", "박파", "괴짜"]:
        for gender in ["male", "female"]:
            r = position_match_score(name, gender=gender)
            assert 0.0 <= r["start_score"] <= 1.0
            assert 0.0 <= r["end_score"] <= 1.0
            assert 0.0 <= r["combined_score"] <= 1.0


def test_position_rationale_includes_disclaimer():
    """위치 점수 출력 면책 의무."""
    from engine.divination.name_aesthetic import position_match_score
    r = position_match_score("이준", gender="male")
    assert "추천 정렬 가점" in r["rationale"]
    assert "절대 기준이 아닙니다" in r["rationale"]


def test_position_match_gender_split():
    """'이준' (남자 끝 1위) vs '이준' (여자 분류) — 남자 점수 ↑."""
    from engine.divination.name_aesthetic import position_match_score
    male_r = position_match_score("이준", gender="male")
    female_r = position_match_score("이준", gender="female")
    # '준'은 여자 끝 음절 통계에 없음
    assert male_r["end_score"] > female_r["end_score"]
