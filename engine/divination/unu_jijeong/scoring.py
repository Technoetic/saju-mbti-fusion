"""ADR-158 — 야선 아씨 운우지정 결정론 + sanitize.

두 사주의 일주 + 현재 연도(세운) 기준 합·충 시기 분석.
sok_gunghap는 정적 궁합, 본 모듈은 시기 흐름 (동적).

원칙 (ADR-002·006·010 정합):
  · 합·충 결정론만 — 관계 종료·이별 시기 단정 X
  · "보름 안에 만남" 등 구체 시점 단정 차단 (sanitize)
  · 현재 흐름의 결만 풀이 — 미래 인과 예언 X
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date


_JI_LIST = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

_YUKHAP = {
    frozenset(["子", "丑"]): "土",
    frozenset(["寅", "亥"]): "木",
    frozenset(["卯", "戌"]): "火",
    frozenset(["辰", "酉"]): "金",
    frozenset(["巳", "申"]): "水",
    frozenset(["午", "未"]): "火",
}
_YUKCHUNG = {
    frozenset(["子", "午"]), frozenset(["丑", "未"]),
    frozenset(["寅", "申"]), frozenset(["卯", "酉"]),
    frozenset(["辰", "戌"]), frozenset(["巳", "亥"]),
}

_SAMHAP = (
    frozenset(["申", "子", "辰"]),  # 水局
    frozenset(["寅", "午", "戌"]),  # 火局
    frozenset(["巳", "酉", "丑"]),  # 金局
    frozenset(["亥", "卯", "未"]),  # 木局
)


@dataclass(frozen=True)
class UnuJijeongResult:
    """운우지정 결정론 결과.

    ★ 의도적 부재 필드 (ADR-006 단정 차단):
      - exact_meeting_date, breakup_date, marriage_date
      - sexual_event_date, fertility_date
    """
    self_day_ji: str
    partner_day_ji: str
    current_year_ji: str       # 현재 연도 세운 지지
    static_relation: str       # 두 일지 정적 관계
    sewoon_self_rel: str       # 본인 일지 × 세운 관계
    sewoon_partner_rel: str    # 상대 일지 × 세운 관계
    flow_phase: str            # 'gathering' | 'flowing' | 'pausing' | 'shifting'
    intensity_score: int       # 40~80 (흐름 강도)
    tone_ko: str
    disclaimer: str


_DISCLAIMER = (
    "본 운우지정은 두 사주 일지 + 현재 세운 합·충 결정론 분류로, "
    "관계 종료·이별 시기·결혼 시점 단정 X. 흐름의 결만 풀이. "
    "참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다."
)


def _pair_relation(j1: str, j2: str) -> str:
    """두 지지 관계 분류."""
    pair = frozenset([j1, j2])
    if pair in _YUKHAP:
        return f"六合({_YUKHAP[pair]})"
    if pair in _YUKCHUNG:
        return "六冲"
    # 삼합 일부 (2자 매칭) — 약합
    for triple in _SAMHAP:
        if pair < triple:
            return "三合 약합"
    if j1 == j2:
        return "동지지"
    return "중립"


def _year_to_ji(year: int) -> str:
    """연도 → 세운 지지 (자=1900, 12 주기)."""
    return _JI_LIST[(year - 1900) % 12]


def _flow_phase(static: str, self_sw: str, partner_sw: str) -> str:
    """흐름 단계 분류."""
    union = f"{static}|{self_sw}|{partner_sw}"
    if "六合" in static and ("六合" in self_sw or "六合" in partner_sw):
        return "gathering"  # 모이는 결
    if "六冲" in self_sw or "六冲" in partner_sw:
        return "shifting"   # 전환의 결
    if "六合" in self_sw or "六合" in partner_sw:
        return "flowing"    # 흐르는 결
    if static in ("동지지", "중립") and "六合" not in union:
        return "pausing"    # 잠시 머무는 결
    return "flowing"


def _intensity(static: str, self_sw: str, partner_sw: str) -> int:
    """흐름 강도 (40~80)."""
    score = 50
    for rel in (static, self_sw, partner_sw):
        if "六合" in rel:
            score += 10
        elif "六冲" in rel:
            score += 8  # 충도 강도 높음 (긴장)
        elif "三合" in rel:
            score += 6
    return max(40, min(80, score))


_TONES = {
    "gathering": "구름이 모이는 결 — 두 흐름이 한 자리로 흐르는 결",
    "flowing": "흐르는 결 — 강물처럼 자연스러운 결",
    "pausing": "잠시 머무는 결 — 흐름이 고요해지는 결",
    "shifting": "전환의 결 — 흐름이 방향을 바꾸는 결",
}


def compute_unu_jijeong(
    self_day_ji: str,
    partner_day_ji: str,
    target_year: int | None = None,
) -> UnuJijeongResult | None:
    """두 사주 일지 + 현재 세운 → 운우지정 결정론.

    Args:
        self_day_ji: 본인 일주 지지 ('午' 등 1자)
        partner_day_ji: 상대 일주 지지
        target_year: 점치는 연도 (디폴트: 현재 연도)
    """
    if self_day_ji not in _JI_LIST or partner_day_ji not in _JI_LIST:
        return None
    year = target_year if target_year else date.today().year
    if not (1900 <= year <= 2200):
        return None

    sewoon_ji = _year_to_ji(year)
    static = _pair_relation(self_day_ji, partner_day_ji)
    self_sw = _pair_relation(self_day_ji, sewoon_ji)
    partner_sw = _pair_relation(partner_day_ji, sewoon_ji)
    phase = _flow_phase(static, self_sw, partner_sw)
    intensity = _intensity(static, self_sw, partner_sw)

    return UnuJijeongResult(
        self_day_ji=self_day_ji,
        partner_day_ji=partner_day_ji,
        current_year_ji=sewoon_ji,
        static_relation=static,
        sewoon_self_rel=self_sw,
        sewoon_partner_rel=partner_sw,
        flow_phase=phase,
        intensity_score=intensity,
        tone_ko=_TONES[phase],
        disclaimer=_DISCLAIMER,
    )


def format_unu_jijeong_for_prompt(r: UnuJijeongResult) -> str:
    """Stage 2 프롬프트 주입."""
    return (
        f"[운우지정 결정론 — 두 일지 + 세운 합충]\n"
        f"  · 본인 일지: {r.self_day_ji} / 상대 일지: {r.partner_day_ji}\n"
        f"  · 현재 세운: {r.current_year_ji}\n"
        f"  · 정적 관계: {r.static_relation}\n"
        f"  · 세운 본인: {r.sewoon_self_rel} / 세운 상대: {r.sewoon_partner_rel}\n"
        f"  · 흐름 단계: {r.flow_phase}\n"
        f"  · 강도 메타: {r.intensity_score}점\n"
        f"  · 흐름 톤: {r.tone_ko}\n"
        f"[안전 장치 — ADR-006] 합충 결정론만 사용. 관계 종료·이별·결혼 시점 단정 금지. "
        f"흐름의 결로만 풀이.\n"
        f"{r.disclaimer}"
    )


# ─────────────────────────── ADR-158 sanitize — 시기 단정 차단 ───────────────────────────

_BANNED_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"보름\s*안에", "가까운 흐름에서"),
    (r"한\s*달\s*안에\s*만나", "흐름이 가까워지는 결"),
    (r"\d+\s*개월\s*안에\s*결혼", "결혼은 두 분 선택의 결"),
    (r"\d+\s*주\s*안에\s*이별", "흐름의 결은 두 분 선택"),
    (r"\d+\s*일\s*안에\s*헤어", "관계의 결은 두 분 선택"),
    (r"올\s*해\s*안에\s*결혼", "결혼은 흐름의 결"),
    (r"내년에\s*반드시\s*결혼", "결혼은 두 분 선택"),
    (r"이별할\s*것", "흐름의 결은 두 분 선택"),
    (r"헤어질\s*것", "관계 흐름은 두 분 선택"),
    (r"파국\s*맞", "흐름의 결을 마주"),
    (r"운명\s*적\s*만남", "흐름이 닿는 만남"),
    (r"반드시\s*만나", "흐름이 닿을 결"),
    (r"100%\s*결혼", "결혼은 두 분 선택"),
    (r"임신\s*할\s*것", "흐름의 결"),
)


def sanitize_unu_jijeong_text(text: str) -> str:
    """ADR-158 — 운우지정 LLM 응답 sanitize."""
    if not isinstance(text, str) or not text:
        return text or ""
    out = text
    for pat, replacement in _BANNED_PATTERNS:
        out = re.sub(pat, replacement, out)
    return out


__all__ = [
    "UnuJijeongResult",
    "compute_unu_jijeong",
    "format_unu_jijeong_for_prompt",
    "sanitize_unu_jijeong_text",
]
