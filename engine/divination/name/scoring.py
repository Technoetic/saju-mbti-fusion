"""성명학 81수리 + 4격(원·형·이·정) 결정론 점수 엔진.

보고서 §2 본문화:
  · 채구봉 81수원도 — 1~81 각 수의 길흉
  · 4격 산출 공식:
    - 원격(元格) = 이름 첫자 + 이름 끝자 획수 (초년운)
    - 형격(亨格) = 성씨 + 이름 첫자 (청년운)
    - 이격(利格) = 성씨 + 이름 끝자 (장년운)
    - 정격(貞格) = 성씨 + 이름 전체 (말년운)
  · 2자 성명(성1+이름1)이나 복성 처리 — 빈 자리에 가상 수 1 대입

⚠️ 본 81수리 분류는 정통 성명학 통설 기준이며, 학파별 미세 차이 존재.
   응답에 길흉 표시는 "참고용 — 절대적 판단 아님" 명시 필수.

운영표준:
  · 결정론 (재현성)
  · LLM 무관
  · 응답 envelope에 정량 점수 노출
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ─────────────────────────── 81수원도 ───────────────────────────
# 채구봉 81수원도 — 통설 기준 4단계 길흉 분류
# GOOD = 길수 (대길·길)
# NEUTRAL = 평수 (반길반흉)
# BAD = 흉수
# VARIES = 사주·성별에 따라 길흉 갈림 (참고용으로 NEUTRAL 처리)

GOOD = "good"            # 길(吉)
NEUTRAL = "neutral"      # 평(平)
BAD = "bad"              # 흉(凶)

# 81수 분류 — 통설 기준
# 1~81 인덱스가 그 수의 길흉. 81 초과는 % 81 으로 환산 (전통적 처리).
_SU81_TABLE: dict[int, str] = {
    1: GOOD,   2: BAD,    3: GOOD,   4: BAD,    5: GOOD,
    6: GOOD,   7: GOOD,   8: GOOD,   9: BAD,    10: BAD,
    11: GOOD,  12: BAD,   13: GOOD,  14: BAD,   15: GOOD,
    16: GOOD,  17: GOOD,  18: GOOD,  19: BAD,   20: BAD,
    21: GOOD,  22: BAD,   23: GOOD,  24: GOOD,  25: GOOD,
    26: BAD,   27: NEUTRAL, 28: BAD, 29: GOOD,  30: NEUTRAL,
    31: GOOD,  32: GOOD,  33: GOOD,  34: BAD,   35: GOOD,
    36: BAD,   37: GOOD,  38: NEUTRAL, 39: GOOD, 40: NEUTRAL,
    41: GOOD,  42: BAD,   43: BAD,   44: BAD,   45: GOOD,
    46: BAD,   47: GOOD,  48: GOOD,  49: NEUTRAL, 50: NEUTRAL,
    51: NEUTRAL, 52: GOOD, 53: NEUTRAL, 54: BAD,  55: NEUTRAL,
    56: BAD,   57: GOOD,  58: NEUTRAL, 59: BAD,  60: BAD,
    61: GOOD,  62: BAD,   63: GOOD,  64: BAD,   65: GOOD,
    66: BAD,   67: GOOD,  68: GOOD,  69: BAD,   70: BAD,
    71: NEUTRAL, 72: NEUTRAL, 73: NEUTRAL, 74: BAD, 75: NEUTRAL,
    76: BAD,   77: NEUTRAL, 78: NEUTRAL, 79: BAD, 80: BAD,
    81: GOOD,
}


# 81수 의미 라벨 — 사용자 노출용 짧은 설명 (1~81 전체 수록).
# 채구봉 81수원도 통설 기준. 학파별 미세 차이 있을 수 있음.
_SU81_LABEL: dict[int, str] = {
    # ── 1~20 ──
    1: "태초·시작", 2: "분리·고독", 3: "삼재·재능", 4: "파괴·곤란", 5: "오복·복덕",
    6: "안정·풍요", 7: "강건·발전", 8: "근면·성취", 9: "비참·역경", 10: "공허·종말",
    11: "재흥·새출발", 12: "박약·고독", 13: "지모·재능", 14: "이산·고독", 15: "복수·온건",
    16: "덕망·재복", 17: "강건·의지", 18: "철석·강건", 19: "고난·역경", 20: "단명·허망",
    # ── 21~40 ──
    21: "두령·자립", 22: "중절·박약", 23: "혁신·왕성", 24: "재산·축적", 25: "안전·강건",
    26: "변동·파란", 27: "중절·평이", 28: "조난·이별", 29: "성공·승진", 30: "성패·반길반흉",
    31: "지덕·번영", 32: "행운·온건", 33: "왕성·발전", 34: "파멸·번뇌", 35: "평화·온건",
    36: "파란·고난", 37: "정치·인덕", 38: "유약·평이", 39: "장수·부귀", 40: "변동·평이",
    # ── 41~60 ──
    41: "고명·덕망", 42: "고행·박약", 43: "산재·박약", 44: "파산·역경", 45: "순조·발전",
    46: "고난·재난", 47: "전개·성공", 48: "유덕·고관", 49: "변괴·반길반흉", 50: "성패·반길반흉",
    51: "성쇠·반길반흉", 52: "선견·달관", 53: "내외부조화·평이", 54: "절망·고독", 55: "외화내빈·평이",
    56: "변동·고난", 57: "노력·결실", 58: "후영·평이", 59: "재난·실의", 60: "동요·암흑",
    # ── 61~81 ──
    61: "영화·부귀", 62: "쇠퇴·고독", 63: "순성·길상", 64: "침체·고독", 65: "흥가·축복",
    66: "내외부조화", 67: "통달·만사형통", 68: "발명·연구", 69: "정체·박약", 70: "공허·박약",
    71: "양면·평이", 72: "후난·평이", 73: "평길·평이", 74: "우매·박약", 75: "평순·평이",
    76: "선후·박약", 77: "낙수·평이", 78: "선후·평이", 79: "부정·박약", 80: "종결·박약",
    81: "환원·만물환원",
}


@dataclass(frozen=True)
class SuResult:
    """단일 수의 평가."""
    su: int                   # 1~81 (또는 환산 전 원수)
    grade: str                # GOOD / NEUTRAL / BAD
    label: str = ""           # 짧은 의미


@dataclass(frozen=True)
class FourGyeokReport:
    """4격(원·형·이·정) 종합 리포트."""
    won_gyeok: SuResult       # 원격 (초년)
    hyeong_gyeok: SuResult    # 형격 (청년)
    i_gyeok: SuResult         # 이격 (장년)
    jeong_gyeok: SuResult     # 정격 (말년)
    all_good: bool            # 4격 모두 길수 여부
    bad_count: int            # 흉수 개수
    summary_grade: str        # 종합 등급 (good/neutral/bad)


# ─────────────────────────── 공통 ───────────────────────────

def normalize_su(n: int) -> int:
    """81 초과는 81로 나눈 나머지 처리. 0은 81로 환산."""
    if n <= 0:
        return 1
    n = n % 81
    return 81 if n == 0 else n


def eval_su(n: int) -> SuResult:
    """단일 수의 81수 길흉 평가."""
    norm = normalize_su(n)
    grade = _SU81_TABLE.get(norm, NEUTRAL)
    label = _SU81_LABEL.get(norm, "")
    return SuResult(su=norm, grade=grade, label=label)


def is_good(n: int) -> bool:
    return eval_su(n).grade == GOOD


# ─────────────────────────── 4격 계산 ───────────────────────────

def calc_four_gyeok(
    surname_strokes: list[int],
    given_strokes: list[int],
) -> FourGyeokReport:
    """4격 산출 — 원·형·이·정.

    Args:
        surname_strokes: 성씨 글자별 원획수 (보통 1자, 복성이면 2자)
        given_strokes: 이름 글자별 원획수 (보통 2자, 외자이면 1자)

    Returns:
        FourGyeokReport — 4격 평가 + 종합.

    예외 처리 (보고서 §2 명시):
      · 외자 이름(이름 1자) → 빈 자리에 가상 수 1 대입
      · 복성(성 2자) → 두 글자 합으로 성격(姓格) 처리
    """
    # 성 합계
    sn_total = sum(surname_strokes) if surname_strokes else 0
    # 이름 — 외자면 가상 수 1 추가
    gn = list(given_strokes) if given_strokes else []
    if len(gn) == 0:
        gn = [1, 1]  # 이름 전무 시 가상 1, 1
    elif len(gn) == 1:
        gn = gn + [1]  # 외자 — 마지막에 가상 수 1

    # 원격 = 이름 첫자 + 이름 끝자
    won = gn[0] + gn[-1]
    # 형격 = 성 + 이름 첫자
    hyeong = sn_total + gn[0]
    # 이격 = 성 + 이름 끝자
    i_g = sn_total + gn[-1]
    # 정격 = 성 + 이름 전체
    jeong = sn_total + sum(gn)

    won_r = eval_su(won)
    hyeong_r = eval_su(hyeong)
    i_r = eval_su(i_g)
    jeong_r = eval_su(jeong)

    grades = [won_r.grade, hyeong_r.grade, i_r.grade, jeong_r.grade]
    bad_count = sum(1 for g in grades if g == BAD)
    good_count = sum(1 for g in grades if g == GOOD)
    all_good = bad_count == 0 and good_count == 4

    if bad_count == 0 and good_count >= 3:
        summary = GOOD
    elif bad_count >= 2:
        summary = BAD
    else:
        summary = NEUTRAL

    return FourGyeokReport(
        won_gyeok=won_r,
        hyeong_gyeok=hyeong_r,
        i_gyeok=i_r,
        jeong_gyeok=jeong_r,
        all_good=all_good,
        bad_count=bad_count,
        summary_grade=summary,
    )


def report_to_dict(report: FourGyeokReport) -> dict[str, Any]:
    """JSON 직렬화 가능 dict."""
    def _s(r: SuResult) -> dict[str, Any]:
        return {"su": r.su, "grade": r.grade, "label": r.label}
    return {
        "won_gyeok": _s(report.won_gyeok),
        "hyeong_gyeok": _s(report.hyeong_gyeok),
        "i_gyeok": _s(report.i_gyeok),
        "jeong_gyeok": _s(report.jeong_gyeok),
        "all_good": report.all_good,
        "bad_count": report.bad_count,
        "summary_grade": report.summary_grade,
    }


# ─────────────────────────── 통합 진입점 ───────────────────────────

def score_name(name_hanja: str) -> dict[str, Any] | None:
    """이름 한자 → 4격 점수 + 불용한자 진단 통합 리포트.

    Args:
        name_hanja: 성+이름 한자 (예: "李珹旻")

    Returns:
        {
            "name": "李珹旻",
            "strokes": {chars, kangxi, missing, ...},
            "four_gyeok": {won/hyeong/i/jeong, all_good, ...},
            "bulyong": {has_bulyong, matched, severity, ...},
            "scoring_status": "ok" | "incomplete" (missing 있으면 incomplete)
        }
        한자 문자열 자체가 비어있으면 None.
    """
    from engine.divination.name.strokes import total_strokes
    from engine.divination.name.bulyong import diagnose_name

    chars = [c for c in (name_hanja or "") if c.strip()]
    if not chars:
        return None

    strokes = total_strokes(name_hanja)
    bulyong = diagnose_name(name_hanja)

    # 보통 첫 글자가 성씨 (1자 가정 — 복성은 별도 명시 호출 필요)
    surname_strokes_raw = [strokes["kangxi"][0]] if strokes["kangxi"] else []
    given_strokes_raw = strokes["kangxi"][1:] if len(strokes["kangxi"]) > 1 else []

    # None(미수록) 제거
    surname_strokes = [s for s in surname_strokes_raw if s is not None]
    given_strokes = [s for s in given_strokes_raw if s is not None]

    four_gyeok_dict = None
    scoring_status = "incomplete"

    if surname_strokes and given_strokes:
        report = calc_four_gyeok(surname_strokes, given_strokes)
        four_gyeok_dict = report_to_dict(report)
        scoring_status = "incomplete" if strokes["missing"] else "ok"

    return {
        "name": name_hanja,
        "strokes": strokes,
        "four_gyeok": four_gyeok_dict,
        "bulyong": bulyong,
        "scoring_status": scoring_status,
    }
