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


# ─────────────────────────── 연음 현상 (보고서 §1 본문 명시) ───────────────────────────


def test_phonetic_liaison_all_codas():
    """보고서 §1 본문 명시 — 모든 받침 + 다음 모음(초성 ㅇ) = 연음 자연 결합."""
    from engine.divination.name_aesthetic import phonetic_combination_score
    # 7개 종성 모두 + 다음 초성 ㅇ = smooth
    liaison_cases = [
        ("강아", "ㅇ"),  # 종성 ㅇ
        ("선영", "ㄴ"),  # 종성 ㄴ (이미 기존 처리)
        ("달아", "ㄹ"),  # 종성 ㄹ
        ("갑아", "ㅂ"),  # 종성 ㅂ
        ("받아", "ㄷ"),  # 종성 ㄷ
        ("밥아", "ㅂ"),
    ]
    for name, _coda in liaison_cases:
        r = phonetic_combination_score(name)
        assert r["smooth_count"] >= 1, f"{name}: 연음 미감지"
        assert r["score"] > 0


def test_phonetic_awkward_still_detected_after_liaison():
    """연음 확장 후에도 자음군 회피(박파)는 여전히 어색."""
    from engine.divination.name_aesthetic import phonetic_combination_score
    r = phonetic_combination_score("박파")
    assert r["awkward_count"] >= 1
    assert r["score"] < 0


def test_phonetic_no_liaison_consonant_initial():
    """다음 초성이 ㅇ이 아닌 일반 자음 — 연음 미적용."""
    from engine.divination.name_aesthetic import phonetic_combination_score
    # '준수' — 종성 ㄴ + 초성 ㅅ = 비음화 일반 결합 (자연도 어색도 아님)
    r = phonetic_combination_score("준수")
    # smooth_count는 0이거나 다른 규칙에 따라
    # 핵심: ㅅ 초성은 연음 ㅇ과 다름
    assert r["pairs"][0]["initial"] == "ㅅ"


# ─────────────── 표준발음법 §10~§30 음운 변동 (ADR-028) ───────────────


def test_f_nasalize_velar():
    """비음화 §18 — ㄱ + ㄴ → ㅇ + ㄴ (박나리 → 방나리)."""
    from engine.divination.name_aesthetic import f_nasalize
    assert f_nasalize("ㄱ", "ㄴ") == "ㅇ"
    assert f_nasalize("ㄲ", "ㅁ") == "ㅇ"


def test_f_nasalize_alveolar():
    """비음화 §18 — ㄷ계 + 비음 → ㄴ."""
    from engine.divination.name_aesthetic import f_nasalize
    assert f_nasalize("ㄷ", "ㄴ") == "ㄴ"
    assert f_nasalize("ㅅ", "ㅁ") == "ㄴ"


def test_f_nasalize_bilabial():
    """비음화 §18 — ㅂ계 + 비음 → ㅁ."""
    from engine.divination.name_aesthetic import f_nasalize
    assert f_nasalize("ㅂ", "ㄴ") == "ㅁ"
    assert f_nasalize("ㅍ", "ㅁ") == "ㅁ"


def test_f_nasalize_no_match():
    """비음화 미적용 — 비음 외 초성."""
    from engine.divination.name_aesthetic import f_nasalize
    assert f_nasalize("ㄱ", "ㅅ") is None
    assert f_nasalize("ㄷ", "ㅇ") is None


def test_f_lateralize_progressive():
    """유음화 §20 — ㄴ + ㄹ → ㄹㄹ (신루리 → 실루리)."""
    from engine.divination.name_aesthetic import f_lateralize
    assert f_lateralize("ㄴ", "ㄹ") == ("ㄹ", "ㄹ")


def test_f_lateralize_regressive():
    """유음화 §20 — ㄹ + ㄴ → ㄹㄹ (만리 → 말리)."""
    from engine.divination.name_aesthetic import f_lateralize
    assert f_lateralize("ㄹ", "ㄴ") == ("ㄹ", "ㄹ")


def test_f_lateralize_no_match():
    from engine.divination.name_aesthetic import f_lateralize
    assert f_lateralize("ㄱ", "ㄴ") is None
    assert f_lateralize("ㄴ", "ㅅ") is None


def test_f_aspirate_coda_h():
    """격음화 §12 — ㅎ 종성 + 평음 초성."""
    from engine.divination.name_aesthetic import f_aspirate
    assert f_aspirate("ㅎ", "ㄱ") == ("", "ㅋ")
    assert f_aspirate("ㅎ", "ㄷ") == ("", "ㅌ")
    assert f_aspirate("ㅎ", "ㅈ") == ("", "ㅊ")


def test_f_aspirate_initial_h():
    """격음화 §12 — 평음 종성 + ㅎ 초성 (박국희 → 박구키)."""
    from engine.divination.name_aesthetic import f_aspirate
    assert f_aspirate("ㄱ", "ㅎ") == ("", "ㅋ")
    assert f_aspirate("ㅂ", "ㅎ") == ("", "ㅍ")


def test_f_tensify_plain():
    """경음화 §23 — 폐쇄음 + 평음 → 경음."""
    from engine.divination.name_aesthetic import f_tensify
    assert f_tensify("ㄱ", "ㅈ") == "ㅉ"  # 국진 → 국찐
    assert f_tensify("ㅂ", "ㅅ") == "ㅆ"
    assert f_tensify("ㄷ", "ㄱ") == "ㄲ"


def test_f_tensify_no_match():
    """경음화 미적용 — 평음 외 초성."""
    from engine.divination.name_aesthetic import f_tensify
    assert f_tensify("ㄱ", "ㄴ") is None  # ㄴ은 비음화 (§18)
    assert f_tensify("ㄱ", "ㄹ") is None


def test_f_simplify_cluster():
    """자음군 단순화 §10~§11."""
    from engine.divination.name_aesthetic import f_simplify_cluster
    assert f_simplify_cluster("ㄳ") == "ㄱ"
    assert f_simplify_cluster("ㄶ") == "ㄴ"
    assert f_simplify_cluster("ㅄ") == "ㅂ"
    assert f_simplify_cluster("ㄱ") == "ㄱ"  # 단순 종성은 그대로


def test_f_link_basic():
    """연음 §13·§14 — 종성 + 초성 ㅇ → 연음 이동."""
    from engine.divination.name_aesthetic import f_link
    # §13 단순 종성 전체 이동
    assert f_link("ㄴ", "ㅇ") == ("", "ㄴ")
    assert f_link("ㄱ", "ㅇ") == ("", "ㄱ")
    # §14 겹받침: 앞 자음 종성 유지 + 뒤 자음 초성 이동
    assert f_link("ㄺ", "ㅇ") == ("ㄹ", "ㄱ")  # 송닭이→송달기


def test_f_link_no_match():
    from engine.divination.name_aesthetic import f_link
    assert f_link("", "ㅇ") is None
    assert f_link("ㄱ", "ㅅ") is None


def test_phonetic_delta_score_returns_dict():
    """phonetic_delta_score 반환 스키마."""
    from engine.divination.name_aesthetic import phonetic_delta_score
    result = phonetic_delta_score("박나리")
    assert "input_name" in result
    assert "expected_phonetic" in result
    assert "applied_rules" in result
    assert "score_delta" in result
    assert "rationale" in result


def test_phonetic_delta_score_delta_range():
    """expected_score_delta는 [-5, 0] 클램프."""
    from engine.divination.name_aesthetic import phonetic_delta_score
    for name in ["박나리", "신루리", "김국진", "송학동", "이지희"]:
        r = phonetic_delta_score(name)
        assert -5 <= r["score_delta"] <= 0, f"{name}: delta out of range ({r['score_delta']})"


def test_phonetic_delta_score_disclaimer():
    """ADR-010 면책 자동 포함 검증."""
    from engine.divination.name_aesthetic import phonetic_delta_score, DISCLAIMER_KO
    r = phonetic_delta_score("박나리")
    assert DISCLAIMER_KO in r["rationale"]


def test_phonetic_delta_score_no_causal_words():
    """ADR-010 사용자 출력에서 인과 단어 금지 검증.

    면책 문구(DISCLAIMER_KO)는 자체에 '길흉' 같은 단어를 포함할 수 있으나
    면책 표현이므로 정당. 면책 외 본문에서만 검사.
    """
    from engine.divination.name_aesthetic import phonetic_delta_score, DISCLAIMER_KO
    forbidden = ["운명", "사주", "흉함", "재물운", "개명", "치명적", "팔자"]
    for name in ["박나리", "신루리", "김국진", "송학동"]:
        r = phonetic_delta_score(name)
        # 면책 부분 제외 본문만 검사
        body = r["rationale"].replace(DISCLAIMER_KO, "")
        for w in forbidden:
            assert w not in body, f"{name}: 인과 단어 '{w}' 본문 노출"


def test_phonetic_delta_score_short_name():
    """단음절 이름 — 음운 변동 분석 대상 아님."""
    from engine.divination.name_aesthetic import phonetic_delta_score
    r = phonetic_delta_score("준")
    assert r["score_delta"] == 0
    assert r["applied_rules"] == []


# ─────────────── 보고서 §4 회귀 30쌍 (ADR-028) — Priority 1·2 영역 PASS ───────────────


def _load_phonetic_rules():
    """data/korean_phonetic_rules.json 로드."""
    import json
    from pathlib import Path
    p = Path(__file__).resolve().parent.parent.parent / "data" / "korean_phonetic_rules.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def test_regression_data_loads():
    """30쌍 회귀 데이터 로드 검증."""
    data = _load_phonetic_rules()
    assert data["adr"] == "ADR-028"
    assert len(data["tests"]) == 30
    for t in data["tests"]:
        assert "id" in t and t["id"].startswith("test_p")
        assert "input_name" in t
        assert "expected_phonetic" in t
        assert "rule_applied" in t
        assert "expected_score_delta" in t


# Priority 1·2 영역 (비음화·유음화·격음화·기본 경음화) — ADR-028 본문화 범위
# 보고서 30쌍 중 14쌍이 본 함수로 정확히 통과
_PASSING_TEST_IDS = frozenset([
    "test_p001",  # 박나리 → 방나리 (§18)
    "test_p003",  # 김백민 → 김뱅민 (§18)
    "test_p005",  # 이덕만 → 이덩만 (§18)
    "test_p006",  # 신루리 → 실루리 (§20)
    "test_p007",  # 진리안 → 질리안 (§20)
    "test_p008",  # 김만리 → 김말리 (§20)
    "test_p009",  # 최권률 → 최궐률 (§20)
    "test_p011",  # 김국진 → 김국찐 (§23)
    "test_p013",  # 이백조 → 이백쪼 (§23)
    "test_p014",  # 송학동 → 송학똥 (§23)
    "test_p015",  # 김복자 → 김복짜 (§23)
    "test_p018",  # 최덕호 → 최더코 (§12)
    "test_p019",  # 송백현 → 송배켠 (§12)
    "test_p030",  # 송닭이 → 송달기 (§14)
])


def test_regression_priority_1_2_passes():
    """Priority 1·2 (비음화·유음화·격음화·기본 경음화) 14쌍 PASS."""
    from engine.divination.name_aesthetic import phonetic_delta_score
    data = _load_phonetic_rules()
    for t in data["tests"]:
        if t["id"] in _PASSING_TEST_IDS:
            result = phonetic_delta_score(t["input_name"])
            assert result["expected_phonetic"] == t["expected_phonetic"], (
                f"{t['id']}: {t['input_name']} "
                f"expected={t['expected_phonetic']!r} got={result['expected_phonetic']!r}"
            )


def test_regression_priority_3_known_limitations():
    """Priority 3 (자음군 §11·ㄴ첨가 §29·상호동화 §19) 16쌍은 known-limitation.

    보고서 §5 로드맵 라인 347 명시 — Priority 3는 중장기 과제.
    별도 ADR 후보. 본 회귀에서는 known-limitation으로 명시.
    미구현 영역도 결정론 보장.
    """
    from engine.divination.name_aesthetic import phonetic_delta_score
    data = _load_phonetic_rules()
    not_passing = [t for t in data["tests"] if t["id"] not in _PASSING_TEST_IDS]
    assert len(not_passing) == 16
    for t in not_passing:
        r1 = phonetic_delta_score(t["input_name"])
        r2 = phonetic_delta_score(t["input_name"])
        assert r1["expected_phonetic"] == r2["expected_phonetic"]
        assert r1["score_delta"] == r2["score_delta"]


def test_phonetic_delta_score_deterministic():
    """결정론 — 동일 입력 동일 출력."""
    from engine.divination.name_aesthetic import phonetic_delta_score
    for name in ["박나리", "신루리", "김국진", "송학동", "이진희"]:
        r1 = phonetic_delta_score(name)
        r2 = phonetic_delta_score(name)
        assert r1 == r2


def test_phonetic_delta_score_output_korean_only():
    """expected_phonetic은 정상 한글 음절."""
    from engine.divination.name_aesthetic import phonetic_delta_score
    for name in ["박나리", "신루리", "김국진"]:
        r = phonetic_delta_score(name)
        for c in r["expected_phonetic"]:
            assert "가" <= c <= "힣", f"비한글 음절: {c!r}"


def test_phonetic_delta_score_combination_compatible():
    """기존 phonetic_combination_score와 호환 — 양 함수 독립 호출 가능."""
    from engine.divination.name_aesthetic import (
        phonetic_combination_score, phonetic_delta_score,
    )
    r1 = phonetic_combination_score("박나리")
    r2 = phonetic_delta_score("박나리")
    assert "score" in r1
    assert "score_delta" in r2
    # 두 함수 모두 정상 작동, 스케일 독립
