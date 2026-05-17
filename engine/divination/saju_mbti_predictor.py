"""사주 → MBTI 4축 경향성 추정 — ADR-014 예외 결정.

본 모듈은 [[ADR-014]] 사용자 명시 예외 결정에 의함. ADR-002 (학파 회피
단순 오행 카운팅) 정신 유지 + ADR-010 (사실성 분리 — 단정 회피·면책 의무)
정신 유지.

매핑은 본 시스템 자체 규칙. 학설 권위 가장 X. 학파 인용 0.

⚠️ 사용 정책 (ADR-014 의무):
  · 16유형 단정 영구 금지
  · 4축 모두 단정 누적도 금지
  · 학설·연구 권위 인용 금지
  · 예측 정확도 표시 금지
  · 사용자 출력 면책 의무

본 모듈은 4축 경향성 dict만 반환. 사용자 출력 표현은 호출자(만월 아씨
페르소나 또는 explain.py)가 "결이 비치는구먼" 형식으로 변환해야 함.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass


# ─────────────────────────── 상수 ───────────────────────────

# MBTI 4축
AXIS_EI = "E_I"  # 외향 vs 내향
AXIS_SN = "S_N"  # 감각 vs 직관
AXIS_TF = "T_F"  # 사고 vs 감정
AXIS_JP = "J_P"  # 판단 vs 인식

# 4축 결과 라벨
LABEL_E = "E"
LABEL_I = "I"
LABEL_S = "S"
LABEL_N = "N"
LABEL_T = "T"
LABEL_F = "F"
LABEL_J = "J"
LABEL_P = "P"
LABEL_UNCERTAIN = "미정"

# 천간 음양 (양간 / 음간)
_YANG_GAN = frozenset("甲丙戊庚壬")
_YIN_GAN = frozenset("乙丁己辛癸")

# 지지 음양
_YANG_JI = frozenset("子寅辰午申戌")
_YIN_JI = frozenset("丑卯巳未酉亥")

# 오행 라벨 (한글 — 본 프로젝트 wuxing_dist 출력 형식)
OHAENG_MOK = "목"
OHAENG_HWA = "화"
OHAENG_TO = "토"
OHAENG_GEUM = "금"
OHAENG_SU = "수"


@dataclass(frozen=True)
class MbtiTendency:
    """4축 경향성. 각 축은 라벨 1개 또는 "미정".

    Attributes:
        ei: "E" / "I" / "미정"
        sn: "S" / "N" / "미정"
        tf: "T" / "F" / "미정"
        jp: "J" / "P" / "미정"
        reasons: 각 축 결정 근거 (사용자 면책 + 투명성)
    """
    ei: str
    sn: str
    tf: str
    jp: str
    reasons: dict[str, str]

    def as_label(self) -> str:
        """4축 라벨 결합 (단정 X — 미정 포함). 예: 'E-N-미정-J'."""
        return f"{self.ei}-{self.sn}-{self.tf}-{self.jp}"

    def uncertain_count(self) -> int:
        return sum(1 for x in (self.ei, self.sn, self.tf, self.jp) if x == LABEL_UNCERTAIN)


# ─────────────────────────── 음양 비율 ───────────────────────────


def _yang_ratio(pillars_str: dict[str, str]) -> float:
    """4기둥 8글자 중 양 비율.

    Args:
        pillars_str: {"year": "庚午", "month": "壬午", "day": "乙巳", "hour": "癸未"}

    Returns:
        0.0~1.0 양 비율. 8글자 중 양에 해당하는 글자 수 / 8.
    """
    yang_count = 0
    total = 0
    for key in ("year", "month", "day", "hour"):
        pillar = pillars_str.get(key, "")
        if len(pillar) != 2:
            continue
        gan, ji = pillar[0], pillar[1]
        if gan in _YANG_GAN:
            yang_count += 1
        elif gan in _YIN_GAN:
            pass  # 음으로 카운트 (yang_count 증가 X)
        total += 1
        if ji in _YANG_JI:
            yang_count += 1
        elif ji in _YIN_JI:
            pass
        total += 1
    if total == 0:
        return 0.5  # 데이터 없으면 중간값
    return yang_count / total


# ─────────────────────────── 각 축 매핑 ───────────────────────────


def _map_ei(yang_ratio: float) -> tuple[str, str]:
    """E vs I — 음양 비율 기반."""
    if yang_ratio >= 0.55:
        return LABEL_E, f"양 비율 {yang_ratio:.2f} ≥ 0.55"
    if yang_ratio <= 0.45:
        return LABEL_I, f"양 비율 {yang_ratio:.2f} ≤ 0.45"
    return LABEL_UNCERTAIN, f"양 비율 {yang_ratio:.2f} (0.45~0.55 사이)"


def _map_sn(wuxing: dict[str, float]) -> tuple[str, str]:
    """S vs N — 오행 분포 기반.

    土+金 우세 → S (감각·현실), 木+水 우세 → N (직관·추상).
    """
    total = sum(wuxing.values()) or 1.0
    sn_s = (wuxing.get(OHAENG_TO, 0) + wuxing.get(OHAENG_GEUM, 0)) / total
    sn_n = (wuxing.get(OHAENG_MOK, 0) + wuxing.get(OHAENG_SU, 0)) / total
    if sn_s >= 0.4 and sn_s > sn_n:
        return LABEL_S, f"土+金 비율 {sn_s:.2f} ≥ 0.4 (감각 우세)"
    if sn_n >= 0.4 and sn_n > sn_s:
        return LABEL_N, f"木+水 비율 {sn_n:.2f} ≥ 0.4 (직관 우세)"
    return LABEL_UNCERTAIN, f"土+金={sn_s:.2f} / 木+水={sn_n:.2f} (균형)"


def _map_tf(wuxing: dict[str, float], day_master_han: str) -> tuple[str, str]:
    """T vs F — 金 비중 + 일간 음양 결합.

    金 우세 + 양간 → T (사고·논리), 火/水 우세 + 음간 → F (감정·공감).
    """
    total = sum(wuxing.values()) or 1.0
    geum_ratio = wuxing.get(OHAENG_GEUM, 0) / total
    fire_water = (wuxing.get(OHAENG_HWA, 0) + wuxing.get(OHAENG_SU, 0)) / total
    is_yang = day_master_han in _YANG_GAN
    is_yin = day_master_han in _YIN_GAN
    if geum_ratio >= 0.25 and is_yang:
        return LABEL_T, f"金 {geum_ratio:.2f} + 양간 {day_master_han} (사고 우세)"
    if fire_water >= 0.4 and is_yin:
        return LABEL_F, f"火+水 {fire_water:.2f} + 음간 {day_master_han} (감정 우세)"
    return LABEL_UNCERTAIN, f"金={geum_ratio:.2f} / 火+水={fire_water:.2f} / 일간={day_master_han}"


def _map_jp(wuxing: dict[str, float]) -> tuple[str, str]:
    """J vs P — 오행 분포 표준편차.

    낮음 (균형) → J (안정·계획), 높음 (편중) → P (유연·즉흥).
    """
    values = [wuxing.get(k, 0) for k in (OHAENG_MOK, OHAENG_HWA, OHAENG_TO, OHAENG_GEUM, OHAENG_SU)]
    if sum(values) == 0:
        return LABEL_UNCERTAIN, "오행 분포 데이터 없음"
    stdev = statistics.pstdev(values)
    if stdev < 0.5:
        return LABEL_J, f"오행 표준편차 {stdev:.2f} < 0.5 (균형 = 안정)"
    if stdev > 1.0:
        return LABEL_P, f"오행 표준편차 {stdev:.2f} > 1.0 (편중 = 유연)"
    return LABEL_UNCERTAIN, f"오행 표준편차 {stdev:.2f} (0.5~1.0 사이)"


# ─────────────────────────── 메인 진입 ───────────────────────────


def derive_mbti_tendency(saju: dict) -> MbtiTendency:
    """사주 dict에서 MBTI 4축 경향성 추정.

    Args:
        saju: 본 프로젝트 사주 dict. 다음 키 사용:
            - "year" / "month" / "day" / "hour": "庚午" 형식 4기둥
              (또는 saju["pillars"]에 같은 구조)
            - "wuxing_dist": {"목": 1.5, "화": 2.0, ...}
            - "day_master_han" 또는 "day_master": 일간 한자

    Returns:
        MbtiTendency — 4축 라벨 + 결정 근거. 단정 회피를 위해 각 축이
        "미정"이 될 수 있음 (ADR-014 규칙).

    면책:
        본 함수 출력은 본 시스템 자체 매핑이며 정통 명리학·심리학
        진단이 아님. 사용자 출력 시 면책 의무 (ADR-014).
    """
    # 4기둥 추출 — 직접 키 또는 pillars 서브 dict
    pillars_str = {
        "year": saju.get("year") or saju.get("pillars", {}).get("year", ""),
        "month": saju.get("month") or saju.get("pillars", {}).get("month", ""),
        "day": saju.get("day") or saju.get("pillars", {}).get("day", ""),
        "hour": saju.get("hour") or saju.get("pillars", {}).get("hour", ""),
    }

    wuxing = saju.get("wuxing_dist", {}) or {}
    day_master_han = saju.get("day_master_han") or saju.get("day_master", "") or ""
    # day_master가 한글이면 한자 변환 시도 (예: "을" → "乙")
    _GAN_KO_TO_HAN = dict(zip("갑을병정무기경신임계", "甲乙丙丁戊己庚辛壬癸"))
    if day_master_han in _GAN_KO_TO_HAN:
        day_master_han = _GAN_KO_TO_HAN[day_master_han]

    yang_ratio = _yang_ratio(pillars_str)
    ei, ei_reason = _map_ei(yang_ratio)
    sn, sn_reason = _map_sn(wuxing)
    tf, tf_reason = _map_tf(wuxing, day_master_han)
    jp, jp_reason = _map_jp(wuxing)

    return MbtiTendency(
        ei=ei,
        sn=sn,
        tf=tf,
        jp=jp,
        reasons={
            AXIS_EI: ei_reason,
            AXIS_SN: sn_reason,
            AXIS_TF: tf_reason,
            AXIS_JP: jp_reason,
        },
    )


# ─────────────────────────── 사용자 출력 헬퍼 (면책 내장) ───────────────────────────


# 페르소나 출력용 텍스트 — "결이 비치는구먼" 형식
_AXIS_DESCRIPTIONS = {
    LABEL_E: "외향(E)의 결",
    LABEL_I: "내향(I)의 기운",
    LABEL_S: "감각(S)의 결",
    LABEL_N: "직관(N)의 기운",
    LABEL_T: "사고(T)의 결",
    LABEL_F: "감정(F)의 기운",
    LABEL_J: "판단(J)의 결",
    LABEL_P: "인식(P)의 기운",
}

DISCLAIMER_KO = (
    "본 시스템의 자체 매핑이며 정통 명리학·심리학 진단이 아닙니다. "
    "MBTI 검사를 대체하지 않습니다."
)


def format_tendency_for_persona(tendency: MbtiTendency) -> str:
    """만월 아씨 페르소나 출력용 경향성 문장.

    ADR-014 의무:
      · 16유형 단정 금지 (4축 라벨만)
      · "결이 비치는구먼" 경향성 표현
      · 면책 의무
    """
    parts: list[str] = []
    for axis_label in (tendency.ei, tendency.sn, tendency.tf, tendency.jp):
        if axis_label == LABEL_UNCERTAIN:
            continue
        desc = _AXIS_DESCRIPTIONS.get(axis_label)
        if desc:
            parts.append(desc)

    if not parts:
        return (
            "사주에서 MBTI 4축의 결이 어느 한쪽으로 또렷이 기울지 않는구먼. "
            "그대 본인이 알고 계신 MBTI를 들려주시게."
        )

    bullets = "이 비치고 ".join(parts) + "이 흐르는구먼"
    return (
        f"그대의 사주를 보니, {bullets}. "
        "그대 본인이 알고 계신 MBTI와 견주어 보시게. "
        f"({DISCLAIMER_KO})"
    )
