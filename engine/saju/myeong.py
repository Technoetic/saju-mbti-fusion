"""성명학 (姓名學) 결정론적 분석.

3개 축:
  1. 음령오행 (音靈五行) — 한글 자음 → 5원소
  2. 자원오행 (字源五行) — 한자 부수 (Phase A 에서는 음령만, 자원은 후속)
  3. 수리오격 (數理五格) — 5격의 획수 → 81 운수 매핑

사주 보완도:
  사주의 강한/약한 오행과 이름 오행 분포 비교 → -10 ~ +10 점수
"""

from __future__ import annotations

from typing import Any

# 한글 자음 (초성) → 음령오행
_INITIAL_WUXING = {
    "ㄱ": "목", "ㅋ": "목", "ㄲ": "목",
    "ㄴ": "화", "ㄷ": "화", "ㄹ": "화", "ㅌ": "화", "ㄸ": "화",
    "ㅇ": "토", "ㅎ": "토",
    "ㅅ": "금", "ㅈ": "금", "ㅊ": "금", "ㅆ": "금", "ㅉ": "금",
    "ㅁ": "수", "ㅂ": "수", "ㅍ": "수", "ㅃ": "수",
}

# 81 수리오격 운수 (대운/길흉) — 한국 표준 (약식, 핵심만)
# 길: 좋은 운, 흉: 나쁜 운, 평: 보통
# https://ko.wikipedia.org/wiki/성명학 표준
_SUSU_FORTUNE: dict[int, dict[str, str]] = {
    1: {"label": "길", "name": "기본운", "desc": "만물의 시작, 명예와 부귀"},
    2: {"label": "흉", "name": "분리운", "desc": "분리·고독·약함"},
    3: {"label": "길", "name": "성형운", "desc": "지덕겸비, 명예"},
    4: {"label": "흉", "name": "부정운", "desc": "파괴·실패"},
    5: {"label": "길", "name": "정성운", "desc": "복덕·중심"},
    6: {"label": "길", "name": "계승운", "desc": "안정·계승"},
    7: {"label": "길", "name": "독립운", "desc": "강건·독립"},
    8: {"label": "길", "name": "발달운", "desc": "끈기·성취"},
    9: {"label": "흉", "name": "궁박운", "desc": "고난·역경"},
    10: {"label": "흉", "name": "공허운", "desc": "공허·허무"},
    11: {"label": "길", "name": "신성운", "desc": "재흥·번영"},
    12: {"label": "흉", "name": "박약운", "desc": "박약·고독"},
    13: {"label": "길", "name": "지모운", "desc": "지혜·명석"},
    14: {"label": "흉", "name": "이산운", "desc": "이별·파괴"},
    15: {"label": "길", "name": "통솔운", "desc": "복덕·통솔"},
    16: {"label": "길", "name": "덕망운", "desc": "덕망·재물"},
    17: {"label": "길", "name": "건창운", "desc": "권위·돌파"},
    18: {"label": "길", "name": "발전운", "desc": "의지·성공"},
    19: {"label": "흉", "name": "성패격", "desc": "성패가 갈리는 격동의 운"},
    20: {"label": "흉", "name": "공허격", "desc": "이상주의적 허무·실속 부족"},
    21: {"label": "길", "name": "두령운", "desc": "수령·번영"},
    22: {"label": "흉", "name": "박약운", "desc": "허약·중절"},
    23: {"label": "길", "name": "공명운", "desc": "공명·통솔"},
    24: {"label": "길", "name": "축재운", "desc": "재물·후덕"},
    25: {"label": "길", "name": "안전운", "desc": "안전·자영"},
    26: {"label": "흉", "name": "영웅운", "desc": "변괴·파란"},
    27: {"label": "흉", "name": "중절운", "desc": "비방·실패"},
    28: {"label": "흉", "name": "조난운", "desc": "조난·고독"},
    29: {"label": "길", "name": "성공운", "desc": "재능·성공"},
    30: {"label": "평", "name": "부몽운", "desc": "길흉 반반"},
    31: {"label": "길", "name": "흥가운", "desc": "지덕·통솔"},
    32: {"label": "길", "name": "요행운", "desc": "요행·번영"},
    33: {"label": "길", "name": "승천운", "desc": "권위·왕성"},
    34: {"label": "흉", "name": "변란운", "desc": "변란·파괴"},
    35: {"label": "길", "name": "평범운", "desc": "온화·평순"},
    36: {"label": "흉", "name": "파란운", "desc": "파란·풍파"},
    37: {"label": "길", "name": "정치운", "desc": "권위·신용"},
    38: {"label": "평", "name": "문예운", "desc": "예술·온유"},
    39: {"label": "길", "name": "장성운", "desc": "장성·부귀"},
    40: {"label": "흉", "name": "변동운", "desc": "변동·득실"},
    41: {"label": "길", "name": "고명운", "desc": "고명·덕망"},
    42: {"label": "흉", "name": "고행운", "desc": "고행·실의"},
    43: {"label": "흉", "name": "성쇠운", "desc": "산재·표류"},
    44: {"label": "흉", "name": "파괴운", "desc": "파산·역경"},
    45: {"label": "길", "name": "현달운", "desc": "현달·도덕"},
    46: {"label": "흉", "name": "허무운", "desc": "허무·고독"},
    47: {"label": "길", "name": "출세운", "desc": "출세·복덕"},
    48: {"label": "길", "name": "유덕운", "desc": "유덕·지덕"},
    49: {"label": "평", "name": "변재운", "desc": "변동·길흉반반"},
    50: {"label": "흉", "name": "부몽운", "desc": "성패·길흉"},
    51: {"label": "평", "name": "성쇠운", "desc": "성쇠·평범"},
    52: {"label": "길", "name": "신앙운", "desc": "신용·발전"},
    53: {"label": "흉", "name": "내허운", "desc": "외화내빈"},
    54: {"label": "흉", "name": "신고운", "desc": "신고·실패"},
    55: {"label": "평", "name": "미달운", "desc": "외길내흉"},
    56: {"label": "흉", "name": "변동운", "desc": "변동·실의"},
    57: {"label": "길", "name": "노력운", "desc": "노력·성공"},
    58: {"label": "평", "name": "후복운", "desc": "선난후행"},
    59: {"label": "흉", "name": "재화운", "desc": "재화·실의"},
    60: {"label": "흉", "name": "동요운", "desc": "동요·실패"},
    61: {"label": "길", "name": "재리운", "desc": "재리·번영"},
    62: {"label": "흉", "name": "고독운", "desc": "고독·쇠퇴"},
    63: {"label": "길", "name": "길상운", "desc": "융창·길상"},
    64: {"label": "흉", "name": "파산운", "desc": "파산·이산"},
    65: {"label": "길", "name": "흥가운", "desc": "흥가·휘덕"},
    66: {"label": "흉", "name": "쇠망운", "desc": "쇠망·고독"},
    67: {"label": "길", "name": "통달운", "desc": "통달·번영"},
    68: {"label": "길", "name": "발명운", "desc": "발명·재지"},
    69: {"label": "흉", "name": "종말운", "desc": "종말·궁박"},
    70: {"label": "흉", "name": "공허운", "desc": "공허·암흑"},
    71: {"label": "평", "name": "견실운", "desc": "겉길속흉"},
    72: {"label": "흉", "name": "후고운", "desc": "선락후고"},
    73: {"label": "길", "name": "평길운", "desc": "평길·무난"},
    74: {"label": "흉", "name": "우매운", "desc": "우매·실의"},
    75: {"label": "평", "name": "정수운", "desc": "수절·온건"},
    76: {"label": "흉", "name": "선난운", "desc": "선난후악"},
    77: {"label": "평", "name": "전후운", "desc": "전길후흉"},
    78: {"label": "평", "name": "전후운", "desc": "전반행운"},
    79: {"label": "흉", "name": "종극운", "desc": "종극·절망"},
    80: {"label": "흉", "name": "종결운", "desc": "종결·은퇴"},
    81: {"label": "길", "name": "환원운", "desc": "1로 환원, 만물의 시작"},
}


def _decompose_hangul(ch: str) -> str | None:
    """한글 음절 → 초성 1자. 한글이 아니면 None."""
    code = ord(ch)
    if 0xAC00 <= code <= 0xD7A3:
        cho_idx = (code - 0xAC00) // (21 * 28)
        cho_table = [
            "ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ", "ㅅ",
            "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
        ]
        return cho_table[cho_idx]
    return None


def initial_wuxing(name_ko: str) -> list[str]:
    """이름 (한글) → 각 글자의 음령오행."""
    out = []
    for ch in name_ko:
        cho = _decompose_hangul(ch)
        if cho:
            out.append(_INITIAL_WUXING.get(cho, "?"))
    return out


def initial_wuxing_dist(name_ko: str) -> dict[str, int]:
    """이름의 음령오행 카운트."""
    counts = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}
    for wx in initial_wuxing(name_ko):
        if wx in counts:
            counts[wx] += 1
    return counts


def _stroke_of_han(ch: str) -> int:
    """한자 1글자 → 강희자전 획수 (hanja_data 사전 lookup)."""
    from .hanja_data import lookup_han

    entry = lookup_han(ch)
    return entry["strokes"] if entry else 10  # 사전 없으면 10획 fallback


def _wuxing_of_han(ch: str) -> str:
    """한자 1글자 → 자원오행."""
    from .hanja_data import lookup_han

    entry = lookup_han(ch)
    return entry["wuxing"] if entry else "?"


def _stroke_of_hangul(ch: str) -> int:
    """한글 1글자 → 자모 획수 합 (강희자전 한글 획수 표준 — 한국성명학 관행).

    초성·중성·종성 자모 각각의 표준 획수.
    """
    code = ord(ch)
    if not (0xAC00 <= code <= 0xD7A3):
        return 0

    cho_strokes = {
        "ㄱ": 2, "ㄲ": 4, "ㄴ": 2, "ㄷ": 3, "ㄸ": 6, "ㄹ": 5, "ㅁ": 4,
        "ㅂ": 4, "ㅃ": 8, "ㅅ": 2, "ㅆ": 4, "ㅇ": 1, "ㅈ": 3, "ㅉ": 6,
        "ㅊ": 4, "ㅋ": 3, "ㅌ": 4, "ㅍ": 4, "ㅎ": 3,
    }
    jung_strokes = {
        "ㅏ": 2, "ㅐ": 3, "ㅑ": 3, "ㅒ": 4, "ㅓ": 2, "ㅔ": 3, "ㅕ": 3,
        "ㅖ": 4, "ㅗ": 2, "ㅘ": 4, "ㅙ": 5, "ㅚ": 3, "ㅛ": 3, "ㅜ": 2,
        "ㅝ": 4, "ㅞ": 5, "ㅟ": 3, "ㅠ": 3, "ㅡ": 1, "ㅢ": 2, "ㅣ": 1,
    }
    jong_strokes = {
        "": 0, "ㄱ": 2, "ㄲ": 4, "ㄳ": 4, "ㄴ": 2, "ㄵ": 5, "ㄶ": 5,
        "ㄷ": 3, "ㄹ": 5, "ㄺ": 7, "ㄻ": 9, "ㄼ": 9, "ㄽ": 7, "ㄾ": 9,
        "ㄿ": 9, "ㅀ": 8, "ㅁ": 4, "ㅂ": 4, "ㅄ": 6, "ㅅ": 2, "ㅆ": 4,
        "ㅇ": 1, "ㅈ": 3, "ㅊ": 4, "ㅋ": 3, "ㅌ": 4, "ㅍ": 4, "ㅎ": 3,
    }

    cho_table = list("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ")
    jung_table = list("ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ")
    jong_table = [""] + list(
        "ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"
    )

    offset = code - 0xAC00
    cho = cho_table[offset // (21 * 28)]
    jung = jung_table[(offset % (21 * 28)) // 28]
    jong = jong_table[offset % 28]

    return (
        cho_strokes.get(cho, 0)
        + jung_strokes.get(jung, 0)
        + jong_strokes.get(jong, 0)
    )


def stroke_count(name_ko: str, name_han: str | None = None) -> list[int]:
    """이름 각 글자의 획수. 한자가 있으면 한자 우선."""
    if name_han and len(name_han) == len(name_ko):
        return [_stroke_of_han(ch) for ch in name_han]
    return [_stroke_of_hangul(ch) for ch in name_ko]


def five_grids(strokes: list[int]) -> dict[str, int]:
    """한국식 4격 (원·형·이·정).

    설계도 §2.1 한국식 4격 (가성 제외):
      strokes = [성, 이름1, 이름2] 3글자 기준.
      - 원격(元格) = 이름 첫자 + 이름 끝자 (초년운, 20세 이전)
      - 형격(亨格) = 성씨 + 이름 첫자 (중년운, 20~40대)
      - 이격(利格) = 성씨 + 이름 끝자 (말년운, 40대~)
      - 정격(貞格) = 성씨 + 이름 전체 합 (총운, 일생)

    2글자 (성+이름1) 또는 4글자 이상은 단순화.
    """
    if len(strokes) == 3:
        s, n1, n2 = strokes
        return {
            "원격": n1 + n2,
            "형격": s + n1,
            "이격": s + n2,
            "정격": s + n1 + n2,
        }
    if len(strokes) == 2:
        s, n1 = strokes
        # 외자 이름 — 원격은 이름 자체, 형격=성+이름, 이격=성+이름, 정격=총합
        return {
            "원격": n1,
            "형격": s + n1,
            "이격": s + n1,
            "정격": s + n1,
        }
    if len(strokes) >= 4:
        s = strokes[0]
        rest = strokes[1:]
        return {
            "원격": rest[0] + rest[-1],
            "형격": s + rest[0],
            "이격": s + rest[-1],
            "정격": sum(strokes),
        }
    return {"원격": 0, "형격": 0, "이격": 0, "정격": 0}


def grid_fortune(grids: dict[str, int]) -> dict[str, dict]:
    """5격 → 81 운수 매핑."""
    out = {}
    for grid_name, num in grids.items():
        n = ((num - 1) % 81) + 1 if num > 0 else 0
        out[grid_name] = {"number": num, "mod81": n, **_SUSU_FORTUNE.get(n, {"label": "?", "name": "?", "desc": ""})}
    return out


def saju_complement_score(
    saju_wuxing: dict[str, float], name_wuxing_dist: dict[str, int]
) -> dict[str, Any]:
    """사주 약한 오행을 이름이 얼마나 보강하는지 점수화 (-10 ~ +10).

    로직:
      - 사주의 약한 오행 (점수 < 평균) 을 이름이 채우면 +
      - 사주의 강한 오행 (점수 > 평균) 을 이름이 더 강화하면 -
    """
    if not saju_wuxing:
        return {"score": 0, "reason": "사주 오행 데이터 없음"}

    avg = sum(saju_wuxing.values()) / len(saju_wuxing)
    weak = [k for k, v in saju_wuxing.items() if v < avg]
    strong = [k for k, v in saju_wuxing.items() if v > avg]

    score = 0
    contributions = []
    for wx, n in name_wuxing_dist.items():
        if n == 0:
            continue
        if wx in weak:
            delta = 2 * n
            score += delta
            contributions.append(f"+{delta} ({wx}: 약한 기운 보강 ×{n})")
        elif wx in strong:
            delta = -1 * n
            score += delta
            contributions.append(f"{delta} ({wx}: 강한 기운 과잉 ×{n})")
        else:
            contributions.append(f"+0 ({wx}: 평균 ×{n})")

    score = max(-10, min(10, score))
    grade = "길" if score >= 4 else ("평" if score >= 0 else "흉")
    return {
        "score": score,
        "grade": grade,
        "reason": "; ".join(contributions),
        "weak": weak,
        "strong": strong,
    }


def analyze_name(
    name_ko: str,
    saju_wuxing: dict[str, float] | None = None,
    name_han: str | None = None,
) -> dict[str, Any]:
    """성명학 종합 분석.

    Args:
        name_ko: 한글 이름 (성 포함, 예: "홍길동")
        saju_wuxing: 사주 오행 분포 dict (보완도 계산용)
        name_han: 한자 이름 (선택)

    Returns:
        {
          "name_ko": str,
          "name_han": str|None,
          "wuxing_per_char": list[str],
          "wuxing_dist": dict[str,int],
          "strokes": list[int],
          "grids": dict[str,dict],   # 5격 + 81운수
          "complement": dict,        # 사주 보완도
          "summary": str,
        }
    """
    if not name_ko or not name_ko.strip():
        raise ValueError("이름은 필수 입력입니다")

    name_ko = name_ko.strip()
    wuxing_chars = initial_wuxing(name_ko)  # 음령오행 (한글 자음)
    wuxing_dist = initial_wuxing_dist(name_ko)
    strokes = stroke_count(name_ko, name_han)
    grids = five_grids(strokes)
    grid_for = grid_fortune(grids)

    # 자원오행 (한자 부수) — 한자 입력 시
    wuxing_han_chars: list[str] = []
    wuxing_han_dist: dict[str, int] = {}
    if name_han and len(name_han) == len(name_ko):
        wuxing_han_chars = [_wuxing_of_han(ch) for ch in name_han]
        wuxing_han_dist = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}
        for w in wuxing_han_chars:
            if w in wuxing_han_dist:
                wuxing_han_dist[w] += 1

    # 보완도 — 한자가 있으면 음령 + 자원 결합 분포 사용
    combined_dist = dict(wuxing_dist)
    if wuxing_han_dist:
        for k, v in wuxing_han_dist.items():
            combined_dist[k] = combined_dist.get(k, 0) + v

    complement = {}
    if saju_wuxing:
        complement = saju_complement_score(saju_wuxing, combined_dist)

    # 요약 라인
    pillars_summary = (
        f"음령오행 {'/'.join(wuxing_chars)} → "
        f"{dict((k,v) for k,v in wuxing_dist.items() if v)}"
    )
    if wuxing_han_chars:
        pillars_summary += (
            f". 자원오행 {'/'.join(wuxing_han_chars)} → "
            f"{dict((k,v) for k,v in wuxing_han_dist.items() if v)}"
        )
    main_fortune = grid_for.get("형격", {})
    fortune_summary = (
        f"형격(중년운) {main_fortune.get('number',0)}획 "
        f"({main_fortune.get('label','?')}: {main_fortune.get('name','')})"
    )
    summary = f"{pillars_summary}. {fortune_summary}"
    if complement:
        summary += f". 사주 보완 {complement['score']:+d} ({complement['grade']})"

    return {
        "name_ko": name_ko,
        "name_han": name_han,
        "wuxing_per_char": wuxing_chars,  # 음령
        "wuxing_dist": wuxing_dist,
        "wuxing_han_per_char": wuxing_han_chars,  # 자원
        "wuxing_han_dist": wuxing_han_dist,
        "combined_wuxing_dist": combined_dist,
        "strokes": strokes,
        "grids": grid_for,
        "complement": complement,
        "summary": summary,
    }


__all__ = [
    "initial_wuxing",
    "initial_wuxing_dist",
    "stroke_count",
    "five_grids",
    "grid_fortune",
    "saju_complement_score",
    "analyze_name",
]
