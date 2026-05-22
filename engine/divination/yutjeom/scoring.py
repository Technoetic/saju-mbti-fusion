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


# ─────────────────────────── ADR-145 모(5) 별개 사위 옵션 B (125괘) ───────────────────────────

# 모(5) 별개 사위 — 윷(4)보다 한 단계 위, 한국 일부 지역·민속 변형 학파
# /domain-priorities #13 (32점) 해소 — 사용자 결단 2026-05-22
MO_SIDE = YutSide("mo", "모", 5, "다섯 걸음의 비약")

SIDES_5: tuple[YutSide, ...] = YUT_SIDES + (MO_SIDE,)  # 5사위 (도·개·걸·윷·모)


def yut_side_by_value_v5(value: int) -> YutSide | None:
    """모(5) 별개 사위 옵션 B — 값(1~5)으로 조회.

    옵션 A (디폴트 yut_side_by_value)와 달리 모(5)를 별개 사위로 반환.
    """
    if not (1 <= value <= 5):
        return None
    return SIDES_5[value - 1]


# 125괘 흐름 톤 — 모(5) 포함 5^3=125 조합
# 64괘는 _FLOW_TONES 그대로 재사용 (4사위 부분 동일)
# 추가 61괘 = 모(5) 1회 이상 포함된 조합
# 모(5) 의미: 윷(4) "도약" 위의 "비약·초월·예외" 결
#
# 매핑 순서: upper(0~4) × middle(0~4) × lower(0~4)
# hex_id_125 = upper*25 + middle*5 + lower (0~124)
_FLOW_TONES_125_EXTRA: dict[int, str] = {
    # upper=도(0), middle=도(0), lower=모(4) — hex_id 4
    4: "기초 위에 비약의 결 — 작은 시작이 큰 도약을 부르는 흐름",
    # upper=도(0), middle=개(1), lower=모(4) — hex_id 9
    9: "흐름이 비약으로 이어지는 결 — 의외의 전환",
    # upper=도(0), middle=걸(2), lower=모(4) — hex_id 14
    14: "진전 끝에 비약이 비치는 결",
    # upper=도(0), middle=윷(3), lower=모(4) — hex_id 19
    19: "도약 위의 비약 — 한 번 더 솟는 결",
    # upper=도(0), middle=모(4), lower=도(0) — hex_id 20
    20: "시작의 비약 — 처음부터 큰 결의 흐름",
    21: "비약 뒤 흐름이 차분해지는 결",
    22: "비약 뒤 진전이 이어지는 결",
    23: "비약 뒤 도약으로 가는 결",
    24: "두 번 비약 — 큰 결이 겹치는 흐름",
    # upper=개(1), middle=도(0), lower=모(4) — hex_id 29
    29: "흐름의 끝에 비약이 솟는 결",
    34: "흐름 속의 비약 — 리듬이 깨지는 듯한 결",
    39: "흐름 위 진전 + 비약 — 큰 결로 가는 흐름",
    44: "흐름 위 도약 + 비약 — 한계 너머의 결",
    45: "흐름 속에서 비약 — 갑작스러운 큰 결",
    46: "비약 뒤 차분한 흐름 — 큰 결의 여운",
    47: "비약 + 진전 — 한 단계씩 솟는 흐름",
    48: "비약 + 도약 — 두 번 솟는 결",
    49: "두 비약의 흐름 — 큰 결이 잇따르는 흐름",
    # upper=걸(2), middle=*, lower=모 / upper=걸, middle=모 — hex_id 54·59·64·69·70·71·72·73·74
    54: "진전 위에 비약이 비치는 결",
    59: "진전 + 흐름 + 비약 — 다층의 결",
    64: "진전의 진전 + 비약 — 깊은 비약의 결",
    69: "진전 + 도약 + 비약 — 큰 결의 정점",
    70: "비약이 시작을 안내하는 결",
    71: "비약 뒤 흐름 — 잔잔해지는 큰 결",
    72: "비약 + 진전 — 단단해지는 큰 결",
    73: "비약 + 도약 — 두 번 비약의 결",
    74: "비약의 진전 — 큰 결의 깊이",
    # upper=윷(3), * — hex_id 79·84·89·94·95·96·97·98·99
    79: "도약 위에 비약 — 한 단계 더 솟는 결",
    84: "도약 + 흐름 + 비약 — 큰 결의 리듬",
    89: "도약 + 진전 + 비약 — 거대한 결의 도약",
    94: "도약 + 도약 + 비약 — 한계를 넘는 결",
    95: "비약이 도약을 부르는 결",
    96: "비약 뒤 도약 + 흐름 — 큰 결의 정착",
    97: "비약 + 도약 + 진전 — 큰 결의 다지기",
    98: "비약 + 두 도약 — 정점의 결",
    99: "비약 + 도약 + 비약 — 더 큰 결로",
    # upper=모(4), middle=*, lower=* — hex_id 100~124
    100: "비약 + 시작 + 시작 — 큰 결이 작은 결로 가지치는 흐름",
    101: "비약 뒤 시작 + 흐름 — 큰 결이 잔잔해지는 결",
    102: "비약 + 시작 + 진전 — 큰 결의 단계 밟기",
    103: "비약 + 시작 + 도약 — 큰 결의 다시 솟는 결",
    104: "비약 + 시작 + 비약 — 두 비약을 잇는 흐름",
    105: "비약 + 흐름 + 시작 — 큰 결의 평탄",
    106: "비약 + 두 흐름 — 큰 결이 흐름에 녹는 결",
    107: "비약 + 흐름 + 진전 — 큰 결의 진행",
    108: "비약 + 흐름 + 도약 — 큰 결의 재도약",
    109: "비약 + 흐름 + 비약 — 비약을 잇는 결",
    110: "비약 + 진전 + 시작 — 큰 결의 새 출발",
    111: "비약 + 진전 + 흐름 — 큰 결의 안정",
    112: "비약 + 두 진전 — 큰 결의 단단함",
    113: "비약 + 진전 + 도약 — 큰 결의 정점 진입",
    114: "비약 + 진전 + 비약 — 큰 결의 거듭",
    115: "비약 + 도약 + 시작 — 큰 결의 새 시작",
    116: "비약 + 도약 + 흐름 — 큰 결의 흐름 잇기",
    117: "비약 + 도약 + 진전 — 큰 결의 깊이",
    118: "비약 + 두 도약 — 정점 위 정점의 결",
    119: "비약 + 도약 + 비약 — 비약 위 비약의 결",
    120: "두 비약 + 시작 — 큰 결의 다음 사이클",
    121: "두 비약 + 흐름 — 큰 결의 잔잔한 끝",
    122: "두 비약 + 진전 — 큰 결의 다지기",
    123: "두 비약 + 도약 — 큰 결의 도약",
    124: "세 비약 — 정점의 정점, 결의 결의 결",
}


def _hex_id_125(upper_idx: int, middle_idx: int, lower_idx: int) -> int:
    """5사위 hex_id 계산 — upper*25 + middle*5 + lower (0~124)."""
    return upper_idx * 25 + middle_idx * 5 + lower_idx


def _hex_id_64(upper_idx: int, middle_idx: int, lower_idx: int) -> int:
    """4사위 hex_id 계산 — upper*16 + middle*4 + lower (0~63)."""
    return upper_idx * 16 + middle_idx * 4 + lower_idx


def _generate_125_hexagrams() -> tuple[YutHexagram, ...]:
    """125괘 자동 생성 — 5사위 (도·개·걸·윷·모) 3중 조합.

    모(5) 포함 안 한 조합 = 64괘 흐름 톤 재사용.
    모(5) 포함 조합 = _FLOW_TONES_125_EXTRA에서 신규 톤.
    """
    sides = SIDES_5
    result = []
    for upper_idx, upper in enumerate(sides):
        for middle_idx, middle in enumerate(sides):
            for lower_idx, lower in enumerate(sides):
                hex_id_125 = _hex_id_125(upper_idx, middle_idx, lower_idx)
                label = f"{upper.label_ko}{middle.label_ko}{lower.label_ko}"
                # 모(idx=4) 포함 여부 검사
                if 4 in (upper_idx, middle_idx, lower_idx):
                    # 신규 톤 (없으면 fallback)
                    tone = _FLOW_TONES_125_EXTRA.get(hex_id_125, "비약의 결 — 큰 흐름")
                else:
                    # 64괘 재사용 (4사위 조합)
                    hex_id_64 = _hex_id_64(upper_idx, middle_idx, lower_idx)
                    tone = _FLOW_TONES[hex_id_64]
                result.append(YutHexagram(
                    hex_id=hex_id_125,
                    upper=upper.key,
                    middle=middle.key,
                    lower=lower.key,
                    label_ko=label,
                    flow_tone_ko=tone,
                ))
    return tuple(result)


ONE_HUNDRED_TWENTY_FIVE_HEXAGRAMS: tuple[YutHexagram, ...] = _generate_125_hexagrams()


# ─────────────────────────── 결정론 함수 ───────────────────────────

def compute_yut_hexagram(
    upper_value: int,
    middle_value: int,
    lower_value: int,
    school: str = "folkmuseum",
) -> YutHexagram | None:
    """3사위 → 윷괘 결정론 (학파 옵션).

    Args:
        upper_value: 상괘 사위 값 (1~4 또는 1~5)
        middle_value: 중괘 사위 값
        lower_value: 하괘 사위 값
        school: 학파 옵션.
            - "folkmuseum" (디폴트): 국립민속박물관·이능화 정통 — 4사위 64괘.
              모(5) 입력 시 윷(4)로 단일화 (ADR-112 기존 동작 보존).
            - "mo_separate" (옵션 B, ADR-145): 모(5) 별개 사위 학파 — 5사위 125괘.

    Returns:
        YutHexagram 또는 None (잘못된 입력).

    Examples:
        >>> # 디폴트 — 64괘
        >>> r = compute_yut_hexagram(1, 1, 1)
        >>> r.hex_id
        0
        >>> r = compute_yut_hexagram(5, 5, 5)  # 모 단일화 → 윷윷윷
        >>> r.label_ko
        '윷윷윷'
        >>> # 옵션 B — 125괘
        >>> r = compute_yut_hexagram(5, 5, 5, school="mo_separate")
        >>> r.label_ko
        '모모모'
        >>> r.hex_id
        124
    """
    if school == "mo_separate":
        # 5사위 (모 별개)
        if not all(1 <= v <= 5 for v in (upper_value, middle_value, lower_value)):
            return None
        u_idx = upper_value - 1
        m_idx = middle_value - 1
        l_idx = lower_value - 1
        hex_id = _hex_id_125(u_idx, m_idx, l_idx)
        return ONE_HUNDRED_TWENTY_FIVE_HEXAGRAMS[hex_id]

    if school not in ("folkmuseum", "mo_separate"):
        return None

    # 디폴트 — 4사위 64괘 (모는 윷으로 단일화)
    u = yut_side_by_value(upper_value)
    m = yut_side_by_value(middle_value)
    l = yut_side_by_value(lower_value)
    if u is None or m is None or l is None:
        return None
    upper_idx = u.value - 1
    middle_idx = m.value - 1
    lower_idx = l.value - 1
    hex_id = _hex_id_64(upper_idx, middle_idx, lower_idx)
    return SIXTY_FOUR_HEXAGRAMS[hex_id]


def hexagram_by_id(hex_id: int, school: str = "folkmuseum") -> YutHexagram | None:
    """ID로 윷괘 조회 (학파 옵션).

    Args:
        hex_id: 0~63 (folkmuseum) 또는 0~124 (mo_separate).
        school: "folkmuseum" (64괘) 또는 "mo_separate" (125괘).
    """
    if school == "mo_separate":
        if 0 <= hex_id < 125:
            return ONE_HUNDRED_TWENTY_FIVE_HEXAGRAMS[hex_id]
        return None
    if school != "folkmuseum":
        return None
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
    # ADR-145 모(5) 별개 사위 옵션 B
    "MO_SIDE", "SIDES_5", "yut_side_by_value_v5",
    "ONE_HUNDRED_TWENTY_FIVE_HEXAGRAMS",
]
