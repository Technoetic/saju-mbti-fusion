"""ADR-158 — 야선 아씨 정인 사주 결정론 + sanitize.

본 모듈은 일지(배우자궁) + 정관·정인 십성 분석으로 "진짜 인연의 결" 결정론 매핑.
ten_gods (ADR-157 KCI 인용) 활용.

원칙 (ADR-002·006·010 정합):
  · 일지 = 배우자궁 (자평진전·삼명통회 공통 분류)
  · 정관·정인 분포 → 인연의 안정성 메타
  · 배우자 외모·나이·직업·만나는 시기 단정 차단 (sanitize)
  · 면책 자동 포함
"""
from __future__ import annotations

import re
from dataclasses import dataclass


# 일지 오행 → 배우자 성향 메타 (학파 광범위)
_JI_PARTNER_TONE = {
    "子": "흐르는 결 — 깊고 조용한 성향",
    "丑": "다지는 결 — 묵묵하고 책임감 있는 성향",
    "寅": "뻗는 결 — 활동적이고 진취적인 성향",
    "卯": "유연한 결 — 부드럽고 섬세한 성향",
    "辰": "쌓는 결 — 폭이 넓고 포용력 있는 성향",
    "巳": "밝은 결 — 명석하고 표현이 빛나는 성향",
    "午": "타오르는 결 — 열정적이고 직선적인 성향",
    "未": "익어가는 결 — 부드럽고 정이 깊은 성향",
    "申": "맺는 결 — 결단력 있고 명확한 성향",
    "酉": "정련된 결 — 예리하고 깔끔한 성향",
    "戌": "지키는 결 — 충직하고 보수적인 성향",
    "亥": "감추인 결 — 사색적이고 내면이 깊은 성향",
}

# 정관·정인 강도 → 인연 안정성 메타
def _stability_label(jeongkwan_count: int, jeongin_count: int) -> str:
    total = jeongkwan_count + jeongin_count
    if total >= 3:
        return "안정의 결 — 정관·정인이 짙어 인연이 든든한 결"
    if total == 2:
        return "균형의 결 — 정관·정인이 적절히 분포한 결"
    if total == 1:
        return "탐색의 결 — 정관·정인이 가벼워 흐름을 살피는 결"
    return "자유의 결 — 정관·정인 부재로 인연이 자유로운 결"


@dataclass(frozen=True)
class JeonginSajuResult:
    """정인 사주 결정론 결과.

    ★ 의도적 부재 필드 (ADR-006 단정 차단):
      - partner_age, partner_occupation, partner_appearance
      - exact_meeting_date, marriage_date, child_count
    """
    day_gan: str
    day_ji: str                      # 배우자궁
    day_ji_tone_ko: str              # 배우자궁 성향 메타
    jeongkwan_count: int             # 사주 내 정관 개수
    jeongin_count: int               # 사주 내 정인 개수
    stability_label_ko: str
    has_jeongkwan_in_day: bool       # 일지에 정관 (안정 인연)
    has_jeongin_in_day: bool         # 일지에 정인 (학습·도움 인연)
    tone_ko: str
    disclaimer: str


_DISCLAIMER = (
    "본 정인 사주는 일지(배우자궁) + 정관·정인 분포 결정론 분류로, "
    "배우자 외모·나이·직업·만나는 시기 단정 X. 인연의 결만 풀이. "
    "참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다."
)


def compute_jeongin_saju(
    day_gan: str,
    day_ji: str,
    ten_gods: tuple[str, ...],
    ten_gods_at_day_ji: tuple[str, ...] = (),
) -> JeonginSajuResult | None:
    """일주 + 사주 십성 → 정인 사주 결정론.

    Args:
        day_gan: 일간 ('庚' 등 1자)
        day_ji: 일지 ('午' 등 1자)
        ten_gods: 사주 전체 십성 풀 (['편재', '정관', '식신', '정인'] 등)
        ten_gods_at_day_ji: 일지 자체의 장간 십성 (선택)

    Returns:
        JeonginSajuResult 또는 None
    """
    if not isinstance(day_gan, str) or len(day_gan) != 1:
        return None
    if not isinstance(day_ji, str) or len(day_ji) != 1:
        return None
    if day_ji not in _JI_PARTNER_TONE:
        return None

    jk = sum(1 for tg in ten_gods if tg == "정관")
    ji = sum(1 for tg in ten_gods if tg == "정인")
    label = _stability_label(jk, ji)
    has_jk_day = "정관" in ten_gods_at_day_ji
    has_ji_day = "정인" in ten_gods_at_day_ji

    tone = (
        f"{_JI_PARTNER_TONE[day_ji]} / {label}"
    )

    return JeonginSajuResult(
        day_gan=day_gan,
        day_ji=day_ji,
        day_ji_tone_ko=_JI_PARTNER_TONE[day_ji],
        jeongkwan_count=jk,
        jeongin_count=ji,
        stability_label_ko=label,
        has_jeongkwan_in_day=has_jk_day,
        has_jeongin_in_day=has_ji_day,
        tone_ko=tone,
        disclaimer=_DISCLAIMER,
    )


def format_jeongin_saju_for_prompt(r: JeonginSajuResult) -> str:
    """Stage 2 프롬프트 주입."""
    return (
        f"[정인 사주 결정론 — 일지 + 정관·정인 분포]\n"
        f"  · 일간: {r.day_gan} / 일지(배우자궁): {r.day_ji}\n"
        f"  · 배우자궁 성향: {r.day_ji_tone_ko}\n"
        f"  · 정관 {r.jeongkwan_count}개 / 정인 {r.jeongin_count}개\n"
        f"  · 인연 안정성: {r.stability_label_ko}\n"
        f"  · 일지 정관: {'있음' if r.has_jeongkwan_in_day else '없음'} / "
        f"일지 정인: {'있음' if r.has_jeongin_in_day else '없음'}\n"
        f"  · 흐름 톤: {r.tone_ko}\n"
        f"[안전 장치 — ADR-006] 일지·십성 결정론만 사용. "
        f"배우자 외모·나이·직업·만나는 시기·자녀 수 단정 금지. 인연의 결로만 풀이.\n"
        f"{r.disclaimer}"
    )


# ─────────────────────────── ADR-158 sanitize — 배우자 단정 차단 ───────────────────────────

_BANNED_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\d+살\s*차이", "나이 차이는 흐름의 결"),
    (r"\d+살\s*연상", "나이 차이는 두 분 흐름"),
    (r"\d+살\s*연하", "나이 차이는 두 분 흐름"),
    (r"키\s*\d+\s*센티", "외형은 단정 X"),
    (r"키\s*\d+\s*cm", "외형은 단정 X"),
    (r"의사\s*직업", "직업은 단정 X"),
    (r"변호사\s*직업", "직업은 단정 X"),
    (r"교사\s*직업", "직업은 단정 X"),
    (r"\d+년\s*안에\s*만나", "흐름이 가까워질 결"),
    (r"올\s*해\s*안에\s*결혼", "결혼은 두 분 선택의 결"),
    (r"내년에\s*결혼할\s*것", "결혼은 두 분 선택"),
    (r"반드시\s*결혼", "결혼은 두 분 선택의 결"),
    (r"확실히\s*만나", "흐름이 닿을 결"),
    (r"평생\s*독신", "혼자의 결은 본인 선택"),
    (r"\d+명의?\s*자녀", "자녀 수는 단정 X"),
    (r"운명\s*의\s*상대", "흐름이 닿는 분"),
    (r"천생연분", "흐름이 닿는 결"),
    (r"외모는\s*반드시", "외모는 단정 X"),
)


def sanitize_jeongin_saju_text(text: str) -> str:
    """ADR-158 — 정인 사주 LLM 응답 sanitize."""
    if not isinstance(text, str) or not text:
        return text or ""
    out = text
    for pat, replacement in _BANNED_PATTERNS:
        out = re.sub(pat, replacement, out)
    return out


__all__ = [
    "JeonginSajuResult",
    "compute_jeongin_saju",
    "format_jeongin_saju_for_prompt",
    "sanitize_jeongin_saju_text",
]
