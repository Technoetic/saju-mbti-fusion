"""ADR-158 — 야선 아씨 욕망 사주 결정론 + sanitize.

본 모듈은 사주 십성 분포 + 도화·홍염 신살 분석으로 욕망의 결을 결정론 매핑.
ten_gods (ADR-157 KCI ART002438633 인용) + shensha (ADR-151 KCI ART003175177) 활용.

원칙 (ADR-002·006·010 정합):
  · 십성 5 카테고리 결정론 분류 — 단정 X
  · 성적·외도·문란 단정 차단 (sanitize)
  · 욕망 = 5 갈래 (권력·재물·표현·관계·자유) — 학파 단정 X
  · 면책 자동 포함
"""
from __future__ import annotations

import re
from dataclasses import dataclass


# 십성 → 욕망 5 카테고리 메타 매핑
# 학파 광범위 분류 (자평진전·삼명통회 공통 분류).
_DESIRE_BY_TENGOD = {
    "편관": "power",      # 권력·통제·도전 욕망
    "정관": "power",      # 명예·질서 욕망
    "편재": "wealth",     # 재물·확장 욕망
    "정재": "wealth",     # 안정 재정 욕망
    "식신": "expression", # 표현·창조 욕망
    "상관": "expression", # 자유 표현 욕망
    "편인": "freedom",    # 사색·독창 욕망
    "정인": "freedom",    # 학습·안정 욕망
    "비견": "self",       # 자아·독립 욕망
    "겁재": "self",       # 경쟁·성취 욕망
}

_DESIRE_LABELS_KO = {
    "power": "권력의 결 — 통제·도전·명예",
    "wealth": "재물의 결 — 확장·안정·풍요",
    "expression": "표현의 결 — 창조·자유·발산",
    "freedom": "자유의 결 — 사색·독창·학습",
    "self": "자아의 결 — 독립·성취·경쟁",
}

# 도화 지지 (子午卯酉) — 매력·사교성 메타
_DOHWA = frozenset(["子", "午", "卯", "酉"])

# 홍염살 매핑
_HONGYEOM = {
    "甲": "午", "乙": "申", "丙": "寅", "丁": "未", "戊": "辰",
    "己": "辰", "庚": "戌", "辛": "酉", "壬": "子", "癸": "申",
}


@dataclass(frozen=True)
class DesireSajuResult:
    """욕망 사주 결정론 결과.

    ★ 의도적 부재 필드 (ADR-006 단정 차단):
      - sexual_partners_count, infidelity_risk, fertility_outcome
      - financial_outcome, divorce_risk
    """
    day_gan: str
    dominant_desire: str       # 'power' | 'wealth' | 'expression' | 'freedom' | 'self'
    desire_distribution: dict  # {category: count}
    dohwa_count: int           # 도화 지지 개수 (0~4)
    hongyeom_present: bool     # 홍염살 존재
    charisma_score: int        # 매력도 메타 점수 (40~80)
    dominant_label_ko: str
    tone_ko: str               # 흐름 톤
    disclaimer: str


_DISCLAIMER = (
    "본 욕망 사주는 십성 분포 + 도화·홍염 신살 결정론 분류로, "
    "성적 단정·외도·문란 단정 X. 욕망의 결만 풀이. "
    "참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다."
)

_TONES = {
    "power": "권력의 결이 강하게 흐르는 사주 — 도전을 즐기는 흐름",
    "wealth": "재물·확장의 결이 짙은 사주 — 풍요를 향한 흐름",
    "expression": "표현·창조의 결이 강한 사주 — 자기 표현을 즐기는 흐름",
    "freedom": "자유·사색의 결이 깊은 사주 — 독창을 향한 흐름",
    "self": "자아·독립의 결이 강한 사주 — 자기를 세우는 흐름",
}


def compute_desire_saju(
    day_gan: str,
    ten_gods: tuple[str, ...],
    branches: tuple[str, ...],
) -> DesireSajuResult | None:
    """사주 십성 + 지지 → 욕망 결정론.

    Args:
        day_gan: 일간 ('庚' 등 1자 한자)
        ten_gods: 4기둥 십성 (['편관', '정재', '식신', '비견'] 등 — 일간 제외 3개 또는 4개)
        branches: 4기둥 지지 (['子', '午', '卯', '酉'] 등)

    Returns:
        DesireSajuResult 또는 None
    """
    if not isinstance(day_gan, str) or len(day_gan) != 1:
        return None
    if not ten_gods or not branches:
        return None

    # 욕망 카테고리 분포
    distribution: dict = {"power": 0, "wealth": 0, "expression": 0, "freedom": 0, "self": 0}
    for tg in ten_gods:
        cat = _DESIRE_BY_TENGOD.get(tg)
        if cat:
            distribution[cat] += 1

    # 지배 욕망 (최다 카테고리)
    dominant = max(distribution.items(), key=lambda x: x[1])[0]

    # 도화·홍염 카운트
    dohwa = sum(1 for b in branches if b in _DOHWA)
    hongyeom_target = _HONGYEOM.get(day_gan)
    hongyeom = hongyeom_target in branches if hongyeom_target else False

    # 매력도 점수: 베이스 50 + 도화 5/개 + 홍염 5
    charisma = 50 + dohwa * 5 + (5 if hongyeom else 0)
    charisma = max(40, min(80, charisma))

    return DesireSajuResult(
        day_gan=day_gan,
        dominant_desire=dominant,
        desire_distribution=distribution,
        dohwa_count=dohwa,
        hongyeom_present=hongyeom,
        charisma_score=charisma,
        dominant_label_ko=_DESIRE_LABELS_KO[dominant],
        tone_ko=_TONES[dominant],
        disclaimer=_DISCLAIMER,
    )


def format_desire_saju_for_prompt(r: DesireSajuResult) -> str:
    """Stage 2 프롬프트 주입용."""
    dist_str = ", ".join(f"{k}={v}" for k, v in r.desire_distribution.items() if v > 0)
    return (
        f"[욕망 사주 결정론 — 십성 분포 + 도화·홍염]\n"
        f"  · 일간: {r.day_gan}\n"
        f"  · 지배 욕망: {r.dominant_label_ko}\n"
        f"  · 5 갈래 분포: {dist_str}\n"
        f"  · 도화 지지: {r.dohwa_count}개 / 홍염살: {'있음' if r.hongyeom_present else '없음'}\n"
        f"  · 매력도 메타: {r.charisma_score}점\n"
        f"  · 흐름 톤: {r.tone_ko}\n"
        f"[안전 장치 — ADR-006] 십성·도화·홍염 결정론만 사용. "
        f"성적·외도·문란·결혼 횟수 단정 금지. 욕망의 결로만 풀이.\n"
        f"{r.disclaimer}"
    )


# ─────────────────────────── ADR-158 sanitize — 욕망 단정 차단 ───────────────────────────

_BANNED_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"문란\s*한", "표현이 자유로운"),
    (r"바람둥이", "교류가 활발한"),
    (r"외도\s*할\s*것", "마음의 결은 본인 선택"),
    (r"바람\s*피울\s*것", "마음의 결은 본인 선택"),
    (r"성적\s*으로\s*문란", "관계의 결이 자유로운"),
    (r"성욕\s*이\s*강해", "표현 욕구가 강한"),
    (r"여러\s*사람과\s*잠", "관계의 결이 다양한"),
    (r"100%\s*외도", "외도는 단정 X"),
    (r"반드시\s*바람", "마음은 본인 선택"),
    (r"색정\s*에\s*빠질", "감정의 결이 깊어질"),
    (r"음란", "표현이 강한"),
    (r"방탕", "표현이 자유로운"),
)


def sanitize_desire_saju_text(text: str) -> str:
    """ADR-158 — 욕망 사주 LLM 응답 sanitize."""
    if not isinstance(text, str) or not text:
        return text or ""
    out = text
    for pat, replacement in _BANNED_PATTERNS:
        out = re.sub(pat, replacement, out)
    return out


__all__ = [
    "DesireSajuResult",
    "compute_desire_saju",
    "format_desire_saju_for_prompt",
    "sanitize_desire_saju_text",
]
