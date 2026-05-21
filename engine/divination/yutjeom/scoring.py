"""ADR-112 — 한국 정통 윷점 64괘 결정론.

본 모듈은 ADR-002·006·010·015 정합 — 결정론 매핑만, LLM 작문 분리.

영역:
  · 4사위 (도·개·걸·윷) × 3회 조합 = 4^3 = 64괘
  · 상괘·중괘·하괘 순서 결합
  · 각 괘의 결의 흐름 톤 (단정 X)

출처 (ADR-010 사실성 분리):
  · 국립민속박물관 디지털 아카이브 윷점 (사점, 柶占書)
    유물번호 PS0100200100109517400000 (folkency.nfm.go.kr)
  · 이능화 (1927) "조선무속고(朝鮮巫俗考)", 잡지 『계명(啓明)』
    서영대 역주, 창비 2008, ISBN 9788936471391
  · 한국민족문화대백과사전 (encykorea.aks.ac.kr) 윷점 표제

원칙 (ADR-002·006·010·015 정합):
  · 단정적 예언 차단 — 길흉 단정 X, 결의 결 묘사만
  · 한국 민속 정통 (국립 기관 출처)
  · 동일 입력 (3사위) → 동일 괘 결정론
  · 모(윷과 동일 취급) 단일화 — 4사위 표준

면책:
  · 의료·법률·금융 의사결정 단독 근거 X
  · ADR-006 자문 거절 정신
  · 본 모듈은 한국 정통 민속 점복 — 78장 카드 시스템과 직교
"""

from __future__ import annotations

from dataclasses import dataclass


# ─────────────────────────── 4사위 (도·개·걸·윷) ───────────────────────────

@dataclass(frozen=True)
class YutSide:
    """윷가락 4사위.

    Attributes:
        key: 영문 키
        label_ko: 한국어 명칭
        value: 점수 (도=1, 개=2, 걸=3, 윷=4)
        meaning_ko: 사위 의미

    Note:
        모(5)는 본 모듈에서 윷(4)과 동일하게 단일화 처리.
        ADR-010 단일 사위 표준 — 64괘 결정론 유지.
    """
    key: str
    label_ko: str
    value: int
    meaning_ko: str


YUT_SIDES: tuple[YutSide, ...] = (
    YutSide("do",  "도", 1, "한 걸음의 시작"),
    YutSide("gae", "개", 2, "두 걸음의 흐름"),
    YutSide("geol","걸", 3, "세 걸음의 진전"),
    YutSide("yut", "윷", 4, "네 걸음의 도약"),
)


def yut_side_by_value(value: int) -> YutSide | None:
    """사위 값(1~4)으로 조회. 5(모)는 4(윷)로 단일화."""
    if value == 5:
        value = 4
    if not (1 <= value <= 4):
        return None
    return YUT_SIDES[value - 1]


# ─────────────────────────── 64괘 결정론 매핑 ───────────────────────────

@dataclass(frozen=True)
class YutHexagram:
    """윷점 64괘 (상·중·하 3사위 결합).

    Attributes:
        hex_id: 0~63 결정론 ID
        upper: 상괘 사위 키 (do·gae·geol·yut)
        middle: 중괘 사위 키
        lower: 하괘 사위 키
        label_ko: 64괘 명칭 (예: "도도도", "도개걸")
        flow_tone_ko: 흐름 톤 (단정 X, 결 묘사만)
    """
    hex_id: int
    upper: str
    middle: str
    lower: str
    label_ko: str
    flow_tone_ko: str


# 64괘 흐름 톤 — 단정 X, 결의 결만 (ADR-006 정신)
# 한국 민속 정통 윷점 점괘책의 길흉 표현을 흐름 톤으로 순화
_FLOW_TONES: tuple[str, ...] = (
    # 0~7: 도-도-* (시작-시작-*)
    "기초가 다져지는 결",
    "차분히 시작하는 흐름",
    "조심스러운 출발의 결",
    "신중한 디딤의 흐름",
    "시작의 결 — 안으로 다지는 흐름",
    "잔잔한 시작의 결",
    "준비가 무르익는 흐름",
    "안에서 안으로의 결",
    # 8~15: 도-개-* (시작-흐름-*)
    "한 걸음에서 두 걸음으로의 결",
    "차근차근의 결",
    "쌓여가는 흐름",
    "정리되는 결",
    "단계를 밟는 결",
    "여유 있는 흐름",
    "교류의 결이 깊어지는 흐름",
    "안정으로 가는 결",
    # 16~23: 도-걸-* (시작-진전-*)
    "도약의 결이 비치는 시점",
    "기운이 모이는 결",
    "탄력을 받는 흐름",
    "결단의 결",
    "전환의 결",
    "흐름이 빨라지는 결",
    "외부와 연결되는 흐름",
    "확장의 결",
    # 24~31: 도-윷-* (시작-도약-*)
    "큰 흐름이 다가오는 결",
    "준비된 도약의 결",
    "잠재된 힘이 펼쳐지는 흐름",
    "기회의 결",
    "기운이 솟는 결",
    "도약 후의 균형의 결",
    "넓어지는 흐름",
    "깊어지는 결",
    # 32~39: 개-* (흐름-*)
    "흐름이 이어지는 결",
    "꾸준한 결",
    "유연한 흐름",
    "조정의 결",
    "리듬의 결",
    "균형의 결",
    "교차의 결",
    "변화의 흐름",
    # 40~47: 걸-* (진전-*)
    "전진하는 결",
    "결의 결단",
    "추진력의 흐름",
    "방향이 잡히는 결",
    "외부의 도움을 받는 결",
    "협력의 흐름",
    "기세가 강해지는 결",
    "도전의 결",
    # 48~55: 윷-도/개/걸-* (도약-*)
    "결의 정점에서 안정으로",
    "도약 후 다시 흐름으로",
    "결실을 다지는 결",
    "성과를 정리하는 흐름",
    "결의 결과 — 안에서 다지는 결",
    "다음 흐름을 준비하는 결",
    "성숙의 결",
    "완성으로 향하는 흐름",
    # 56~63: 윷-윷-* (도약-도약-*)
    "큰 결의 흐름",
    "정점의 결",
    "완성의 결이 비치는 흐름",
    "결과를 거두는 결",
    "성취의 결",
    "결의 결 — 다음 사이클로",
    "전체가 어우러지는 결",
    "큰 흐름의 매듭",
)


def _generate_64_hexagrams() -> tuple[YutHexagram, ...]:
    """64괘 자동 생성 — 도(0)~윷(3) 3중 조합.

    hex_id = upper*16 + middle*4 + lower (0~63)
    """
    sides = YUT_SIDES
    result = []
    for upper_idx, upper in enumerate(sides):
        for middle_idx, middle in enumerate(sides):
            for lower_idx, lower in enumerate(sides):
                hex_id = upper_idx * 16 + middle_idx * 4 + lower_idx
                label = f"{upper.label_ko}{middle.label_ko}{lower.label_ko}"
                tone = _FLOW_TONES[hex_id]
                result.append(YutHexagram(
                    hex_id=hex_id,
                    upper=upper.key,
                    middle=middle.key,
                    lower=lower.key,
                    label_ko=label,
                    flow_tone_ko=tone,
                ))
    return tuple(result)


SIXTY_FOUR_HEXAGRAMS: tuple[YutHexagram, ...] = _generate_64_hexagrams()


# ─────────────────────────── 결정론 함수 ───────────────────────────

def compute_yut_hexagram(upper_value: int, middle_value: int, lower_value: int) -> YutHexagram | None:
    """3사위 → 64괘 결정론.

    Args:
        upper_value: 상괘 사위 값 (1~4, 5는 4로 단일화)
        middle_value: 중괘 사위 값 (1~4)
        lower_value: 하괘 사위 값 (1~4)

    Returns:
        YutHexagram 또는 None (잘못된 입력)

    Examples:
        >>> r = compute_yut_hexagram(1, 1, 1)  # 도-도-도
        >>> r.hex_id
        0
        >>> r.label_ko
        '도도도'
        >>> r = compute_yut_hexagram(4, 4, 4)  # 윷-윷-윷
        >>> r.hex_id
        63
        >>> r.label_ko
        '윷윷윷'
    """
    u = yut_side_by_value(upper_value)
    m = yut_side_by_value(middle_value)
    l = yut_side_by_value(lower_value)
    if u is None or m is None or l is None:
        return None

    upper_idx = u.value - 1
    middle_idx = m.value - 1
    lower_idx = l.value - 1
    hex_id = upper_idx * 16 + middle_idx * 4 + lower_idx
    return SIXTY_FOUR_HEXAGRAMS[hex_id]


def hexagram_by_id(hex_id: int) -> YutHexagram | None:
    """0~63 ID로 64괘 조회."""
    if 0 <= hex_id < 64:
        return SIXTY_FOUR_HEXAGRAMS[hex_id]
    return None


# ─────────────────────────── 면책 + 프롬프트 포맷 ───────────────────────────

_DISCLAIMER = (
    "본 윷점은 한국 정통 민속 점복 (국립민속박물관 PS0100200100109517400000 + "
    "이능화 1927 조선무속고 ISBN 9788936471391) 기반 결정론 흐름 톤으로, "
    "길흉 단정 X. 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다. "
    "본 모듈은 한국 민속 정통 — 서양 78장 타로와 직교."
)


def format_hexagram_for_prompt(r: YutHexagram) -> str:
    """Stage 2 시스템 프롬프트에 주입할 윷괘 메타 텍스트."""
    return (
        f"[윷점 64괘 결정론 — 한국 정통 민속]\n"
        f"  · 괘 ID: {r.hex_id} / 64\n"
        f"  · 괘 명: {r.label_ko}\n"
        f"  · 사위 조합: {r.upper}-{r.middle}-{r.lower}\n"
        f"  · 흐름 톤: {r.flow_tone_ko}\n"
        f"[안전 장치 — ADR-006] 윷괘 분류·흐름 톤만 사용. "
        f"길흉·관혼상제·재정 단정 금지. 결의 결 묘사만.\n"
        f"{_DISCLAIMER}"
    )


__all__ = [
    "YutSide", "YUT_SIDES", "yut_side_by_value",
    "YutHexagram", "SIXTY_FOUR_HEXAGRAMS",
    "compute_yut_hexagram", "hexagram_by_id",
    "format_hexagram_for_prompt",
]
