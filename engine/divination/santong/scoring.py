"""ADR-120 — 한국 정통 산통점 결정론.

본 모듈은 ADR-002·006·010·112 정합.

영역:
  · 산통점 (算筒占) 8 산가지 메타
  · 8 산가지 × 3회 뽑기 = 512 점괘
  · 결정론 결합: 3회 뽑기 sum (3~24)으로 22 점괘 그룹화 (단순화)

출처:
  · 이능화 (1927) "조선무속고" — 한국 무속 점복 집대성
  · 국립민속박물관 산통점 표제
"""

from __future__ import annotations

from dataclasses import dataclass


# ─────────────────────────── 8 산가지 메타 ───────────────────────────

@dataclass(frozen=True)
class SantongStick:
    """산통점 8 산가지 단일 메타.

    Attributes:
        idx: 1~8
        label_ko: 한국어 명
        symbol_hanja: 한자 상징
        flow_tone_ko: 흐름 톤
    """
    idx: int
    label_ko: str
    symbol_hanja: str
    flow_tone_ko: str


SANTONG_STICKS: tuple[SantongStick, ...] = (
    SantongStick(1, "일",   "一", "시작의 결"),
    SantongStick(2, "이",   "二", "두 갈래의 결"),
    SantongStick(3, "삼",   "三", "삼위의 결"),
    SantongStick(4, "사",   "四", "안정의 결"),
    SantongStick(5, "오",   "五", "중심의 결"),
    SantongStick(6, "육",   "六", "여섯 갈래의 결"),
    SantongStick(7, "칠",   "七", "이어지는 결"),
    SantongStick(8, "팔",   "八", "완성의 결"),
)


def stick_by_value(value: int) -> SantongStick | None:
    """1~8 산가지 조회."""
    if 1 <= value <= 8:
        return SANTONG_STICKS[value - 1]
    return None


# ─────────────────────────── 22 점괘 그룹 (sum 3~24) ───────────────────────────

# 3회 뽑기 sum 범위: 3 (1+1+1) ~ 24 (8+8+8) = 22 그룹
# 단정 차단 — 흐름 톤만
_GROUP_TONES: tuple[str, ...] = (
    "안에서 안으로 — 가장 정적인 결",     # sum=3
    "잔잔한 시작의 결",                    # sum=4
    "준비의 결",                            # sum=5
    "차근차근의 결",                        # sum=6
    "쌓이는 결",                            # sum=7
    "정돈의 결",                            # sum=8
    "단계의 결",                            # sum=9
    "교류의 결",                            # sum=10
    "안정의 결",                            # sum=11
    "균형의 결",                            # sum=12
    "전환의 결",                            # sum=13
    "도약의 결",                            # sum=14
    "기운이 모이는 결",                     # sum=15
    "탄력의 결",                            # sum=16
    "확장의 결",                            # sum=17
    "결단의 결",                            # sum=18
    "기세의 결",                            # sum=19
    "성과의 결",                            # sum=20
    "성숙의 결",                            # sum=21
    "완성으로의 결",                        # sum=22
    "정점의 결",                            # sum=23
    "큰 흐름의 매듭",                       # sum=24
)


# ─────────────────────────── 결과 dataclass ───────────────────────────

@dataclass(frozen=True)
class SantongResult:
    """산통점 결정론 결과.

    ★ 의도적 부재 필드 (ADR-006):
      - lucky_outcome, unlucky_outcome — 길흉 단정 X
    """
    stick1: SantongStick
    stick2: SantongStick
    stick3: SantongStick
    sum_value: int
    label_ko: str  # "일·이·삼" 형식
    flow_tone_ko: str
    disclaimer: str


_DISCLAIMER = (
    "본 산통점은 한국 정통 무속 점복 (이능화 1927 조선무속고 + 국립민속박물관) "
    "결정론 흐름 톤으로, 길일·흉일·관혼상제 단정 X. "
    "참고용이며 의료·법률·금융 의사결정 단독 근거 X."
)


def compute_santong_reading(stick1_value: int, stick2_value: int, stick3_value: int) -> SantongResult | None:
    """3 산가지 뽑기 → 산통점 결정론.

    Args:
        stick1_value, stick2_value, stick3_value: 1~8 산가지 값

    Returns:
        SantongResult 또는 None

    Examples:
        >>> r = compute_santong_reading(1, 2, 3)
        >>> r.label_ko
        '일·이·삼'
        >>> r.sum_value
        6
    """
    s1 = stick_by_value(stick1_value)
    s2 = stick_by_value(stick2_value)
    s3 = stick_by_value(stick3_value)
    if s1 is None or s2 is None or s3 is None:
        return None

    sum_value = stick1_value + stick2_value + stick3_value
    # sum 3 → index 0 ... sum 24 → index 21
    tone = _GROUP_TONES[sum_value - 3]
    label = f"{s1.label_ko}·{s2.label_ko}·{s3.label_ko}"

    return SantongResult(
        stick1=s1,
        stick2=s2,
        stick3=s3,
        sum_value=sum_value,
        label_ko=label,
        flow_tone_ko=tone,
        disclaimer=_DISCLAIMER,
    )


def format_santong_for_prompt(r: SantongResult) -> str:
    """Stage 2 시스템 프롬프트 주입용 산통점 메타."""
    return (
        f"[산통점 결정론 — 한국 정통 무속 (이능화 1927)]\n"
        f"  · 뽑힌 산가지: {r.label_ko} ({r.stick1.symbol_hanja}·{r.stick2.symbol_hanja}·{r.stick3.symbol_hanja})\n"
        f"  · 합: {r.sum_value} (3~24)\n"
        f"  · 흐름 톤: {r.flow_tone_ko}\n"
        f"[안전 장치 — ADR-006] 길일·흉일·관혼상제·재정 단정 금지. 흐름 톤만.\n"
        f"{r.disclaimer}"
    )


__all__ = [
    "SantongStick", "SANTONG_STICKS", "stick_by_value",
    "SantongResult",
    "compute_santong_reading",
    "format_santong_for_prompt",
]
