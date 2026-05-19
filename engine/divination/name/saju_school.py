"""사주 용신 옵션 B — 이재승(2019) 계량화 억부론 (ADR-015).

KCI 등재 논문 채택:
  이재승 (2019). 사주명조의 計量化를 통한 성명학적 用神法 고찰.
  동방문화와 사상 제6권, pp.99-133.

ADR-002 옵션 A(단순 오행 카운팅)는 디폴트 유지. 본 모듈은 추가 정보용.

⚠️ 사용 정책 (ADR-015):
  · 단일 학파 채택 — 학파 회피 정신 변경 (옵션 B 한정)
  · 합충형해파·외격·종격 등 동적 변화 미반영 (의도된 설계 제약)
  · 인과 예언 X — 참고용 정보 면책 의무
  · 사용자 출력에 학설 명시 의무

본 모듈은 결정론 함수만. 사용자 출력 텍스트 생성은 호출자가 담당.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


class PillarsDict(TypedDict):
    """4기둥 입력 — 각 값은 '庚午' 같은 2글자 한자."""
    year: str
    month: str
    day: str
    hour: str


# ─────────────────────────── 매핑 테이블 ───────────────────────────

# 천간 오행
STEM_OH_MAP: dict[str, str] = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

# 지지 오행
BRANCH_OH_MAP: dict[str, str] = {
    "子": "水", "亥": "水",
    "丑": "土", "辰": "土", "未": "土", "戌": "土",
    "寅": "木", "卯": "木",
    "巳": "火", "午": "火",
    "申": "金", "酉": "金",
}

# 십성 매핑 — 일간 오행 → {비겁·인성·식상·재성·관성}
O_HAENG_MAP: dict[str, dict[str, str]] = {
    "木": {"비겁": "木", "인성": "水", "식상": "火", "재성": "土", "관성": "金"},
    "火": {"비겁": "火", "인성": "木", "식상": "土", "재성": "金", "관성": "水"},
    "土": {"비겁": "土", "인성": "火", "식상": "金", "재성": "水", "관성": "木"},
    "金": {"비겁": "金", "인성": "土", "식상": "水", "재성": "木", "관성": "火"},
    "水": {"비겁": "水", "인성": "金", "식상": "木", "재성": "火", "관성": "土"},
}

# 각 궁(위치)별 억부 역량 가중치 — 이재승(2019) 논문 기준 총합 120점
WEIGHTS: dict[str, int] = {
    "year_stem": 5,
    "year_branch": 9,
    "month_stem": 10,
    "month_branch": 30,
    "day_master": 20,
    "day_branch": 21,
    "hour_stem": 10,
    "hour_branch": 15,
}

# 강약 단계
STRENGTH_WEAK = "신약"
STRENGTH_NEUTRAL_WEAK = "중화신약"
STRENGTH_NEUTRAL_STRONG = "중화신강"
STRENGTH_STRONG = "신강"

# 임계치 (총점 120점 기준 — 이재승 2019)
THRESHOLD_WEAK = 45
THRESHOLD_NEUTRAL = 60
THRESHOLD_NEUTRAL_STRONG = 75


@dataclass(frozen=True)
class YongshinResult:
    """용신 도출 결과.

    Attributes:
        yongshin: 용신 오행 리스트 (1~3개). 신약 시 인성+비겁, 신강 시 식상+재성+관성.
        score: 일간 생조 역량 총점 (0~120).
        strength: 강약 단계 (신약/중화신약/중화신강/신강).
        reason: 추론 근거 텍스트 (사용자 노출 가능, 면책 의무).
        details: 각 궁별 점수 누적 내역 (디버깅용).
        day_master: 일간 한자 (예: '乙').
        day_master_oh: 일간 오행 (예: '木').
    """
    yongshin: tuple[str, ...]
    score: int
    strength: str
    reason: str
    details: tuple[str, ...]
    day_master: str
    day_master_oh: str


# ─────────────────────────── 메인 진입 ───────────────────────────


def derive_yongshin(pillars: PillarsDict) -> YongshinResult:
    """이재승 계량화 억부론 기반 용신 도출.

    Args:
        pillars: 4기둥 dict — {"year": "庚午", "month": "壬午", ...}
            각 값은 천간 1글자 + 지지 1글자 = 2글자 한자.

    Returns:
        YongshinResult — 용신 + 점수 + 강약 + 근거.

    Raises:
        KeyError: 입력 한자가 천간·지지 매핑 테이블에 없을 때.
        ValueError: 입력 형식 오류 (4기둥 누락 등).

    면책 (ADR-015):
        본 함수 출력은 이재승(2019) 학설 기준. 합충형해파·외격·종격 등
        명리학 동적 변화는 반영하지 않음 (의도된 설계 제약).
        사용자 출력 시 학설 명시 + 인과 예언 거부 의무.
    """
    # 1. 기둥 파싱
    for key in ("year", "month", "day", "hour"):
        if key not in pillars or len(pillars[key]) != 2:
            raise ValueError(f"pillars['{key}'] must be 2-char hanja, got: {pillars.get(key)!r}")

    year_stem, year_branch = pillars["year"][0], pillars["year"][1]
    month_stem, month_branch = pillars["month"][0], pillars["month"][1]
    day_stem, day_branch = pillars["day"][0], pillars["day"][1]
    hour_stem, hour_branch = pillars["hour"][0], pillars["hour"][1]

    # 2. 일간 식별 및 오행
    day_master = day_stem
    if day_master not in STEM_OH_MAP:
        raise KeyError(f"day_master not recognized: {day_master!r}")
    dm_oh = STEM_OH_MAP[day_master]

    # 3. 생조 오행 (비겁 + 인성) — 일간을 돕는 세력
    support = {O_HAENG_MAP[dm_oh]["비겁"], O_HAENG_MAP[dm_oh]["인성"]}

    # 4. 8궁 점수 계산
    score = 0
    details: list[str] = []

    # 천간 평가 (year_stem · month_stem · hour_stem) — day_master 제외 (별도 가산)
    stem_evaluations = [
        ("year_stem", year_stem),
        ("month_stem", month_stem),
        ("hour_stem", hour_stem),
    ]
    for pos, char in stem_evaluations:
        oh = STEM_OH_MAP.get(char)
        if oh and oh in support:
            score += WEIGHTS[pos]
            details.append(f"{pos}({char}/{oh}): +{WEIGHTS[pos]}")

    # 지지 평가 (4지지)
    branch_evaluations = [
        ("year_branch", year_branch),
        ("month_branch", month_branch),
        ("day_branch", day_branch),
        ("hour_branch", hour_branch),
    ]
    for pos, char in branch_evaluations:
        oh = BRANCH_OH_MAP.get(char)
        if oh and oh in support:
            score += WEIGHTS[pos]
            details.append(f"{pos}({char}/{oh}): +{WEIGHTS[pos]}")

    # 일간 자신은 비겁이므로 고정 20점
    score += WEIGHTS["day_master"]
    details.append(f"day_master({day_master}/{dm_oh}): +{WEIGHTS['day_master']}")

    # 5. 강약 판정 및 용신 도출
    if score <= THRESHOLD_WEAK:
        strength = STRENGTH_WEAK
        yongshin = (O_HAENG_MAP[dm_oh]["인성"], O_HAENG_MAP[dm_oh]["비겁"])
        reason = (
            f"일간 생조 역량 {score}점({THRESHOLD_WEAK}점 이하). "
            f"신약 판정으로 기운을 돕는 인성({yongshin[0]})과 비겁({yongshin[1]})을 용신으로 채택함."
        )
    elif score <= THRESHOLD_NEUTRAL:
        strength = STRENGTH_NEUTRAL_WEAK
        yongshin = (O_HAENG_MAP[dm_oh]["인성"], O_HAENG_MAP[dm_oh]["비겁"])
        reason = (
            f"일간 생조 역량 {score}점({THRESHOLD_WEAK+1}~{THRESHOLD_NEUTRAL}점 사이). "
            f"중화신약 판정으로 기운을 돕는 인성({yongshin[0]})과 비겁({yongshin[1]})을 우선 용신으로 채택함."
        )
    elif score <= THRESHOLD_NEUTRAL_STRONG:
        strength = STRENGTH_NEUTRAL_STRONG
        yongshin = (
            O_HAENG_MAP[dm_oh]["식상"],
            O_HAENG_MAP[dm_oh]["재성"],
            O_HAENG_MAP[dm_oh]["관성"],
        )
        reason = (
            f"일간 생조 역량 {score}점({THRESHOLD_NEUTRAL+1}~{THRESHOLD_NEUTRAL_STRONG}점 사이). "
            f"중화신강 판정으로 기운을 덜어내는 식상({yongshin[0]}), 재성({yongshin[1]}), 관성({yongshin[2]}) 중 보완을 위해 채택함."
        )
    else:
        strength = STRENGTH_STRONG
        yongshin = (
            O_HAENG_MAP[dm_oh]["식상"],
            O_HAENG_MAP[dm_oh]["재성"],
            O_HAENG_MAP[dm_oh]["관성"],
        )
        reason = (
            f"일간 생조 역량 {score}점({THRESHOLD_NEUTRAL_STRONG+1}점 이상). "
            f"신강 판정으로 강한 기운을 설기하거나 극제하는 식상({yongshin[0]}), 재성({yongshin[1]}), 관성({yongshin[2]})을 용신으로 채택함."
        )

    return YongshinResult(
        yongshin=yongshin,
        score=score,
        strength=strength,
        reason=reason,
        details=tuple(details),
        day_master=day_master,
        day_master_oh=dm_oh,
    )


# ─────────────────────────── 사용자 출력 면책 ───────────────────────────


DISCLAIMER_KO = (
    "본 결과는 이재승(2019) 계량화 억부론 학설을 채택한 참고용 정보입니다. "
    "합충형해파 등 명리학 동적 변화는 반영하지 않으며, 인과적 길흉 예언이 아닙니다."
)


def format_yongshin_for_user(result: YongshinResult) -> str:
    """사용자 노출용 출력 — 면책 자동 포함 (ADR-015 의무)."""
    yongshin_str = "·".join(result.yongshin)
    return (
        f"이재승 억부론 기준 용신: {yongshin_str} "
        f"(일간 {result.day_master_oh}, 역량 {result.score}점, {result.strength})\n"
        f"{result.reason}\n\n"
        f"※ {DISCLAIMER_KO}"
    )
