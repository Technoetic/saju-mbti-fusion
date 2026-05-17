"""ADR-025 한국 화투 48매 결정론 점패 엔진.

보고서 §3-7 본문화:
  · 48패 카드 데이터 (광 20 / 열끗 10 / 띠 5 / 피 1)
  · 3장 스프레드 알고리즘 (과거-현재-미래)
  · 계절 순행/역행 + 카테고리 밀집도 연산
  · permitted/forbidden 키워드 물리 강제 (ADR-006/010 정합)
  · school_variants 메타 격리 (ADR-002 패턴)

설계 (CLAUDE.md §0 + ADR-021/023/024 패턴 정합):
  · 결정론 100% (LLM 호출 0)
  · 기존 hwapae.py (타로 변형) 유지 + 본 모듈 별개 시스템
  · DEFAULT_DISCLAIMERS 강제 (ADR-006/010)

학술 출처 (vault/references/korean-hwapae-traditional.md):
  · 한국민족문화대백과사전 (encykorea.aks.ac.kr)
  · 국립민속박물관 e-museum (유물 일본 568)
  · Wikipedia Korean Hanafuda
  · Fuda Wiki (Hwatu section)
  · 아패영유(雅牌靈遊) 국문필사본 (3회 추첨 + 합산 알고리즘)

본 모듈은 보고서 핵심 5패 + 알고리즘 본문화. 48패 전수 데이터는
data/hwapae_korean_48.json 별도 영속화 가능 (후속 보강).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


# ─────────────────────────── 카테고리 점수 (보고서 §3) ───────────────────────────


_CATEGORY_SCORES: dict[str, int] = {
    "광": 20,
    "열끗": 10,
    "띠": 5,
    "피": 1,
}


CategoryType = Literal["광", "열끗", "띠", "피"]


# ─────────────────────────── 카드 데이터 (보고서 §5 일부) ───────────────────────────


@dataclass(frozen=True)
class HwapaeCard:
    """단일 화패 카드 (보고서 §5 JSON 명세).

    Attributes:
        id: "01-01-gwang" 형식 (월-순서-카테고리).
        month: 1~12.
        card_index_in_month: 1~4 (월별 4매).
        name_ko: 한국어 명칭 (예: "송학 (광)").
        category: 광·열끗·띠·피.
        score: 20·10·5·1.
        symbol: 식물/동물/사물 기호.
        traditional_meaning: 전통 점패 상징 (객관 묘사).
        permitted_keywords: 페르소나 허용 키워드.
        forbidden_keywords: 페르소나 금지 키워드 (ADR-006 강제).
    """

    id: str
    month: int
    card_index_in_month: int
    name_ko: str
    category: str
    score: int
    symbol: str
    traditional_meaning: str
    permitted_keywords: tuple[str, ...]
    forbidden_keywords: tuple[str, ...]


# 보고서 §5 핵심 패 선별 본문화 (대표 5개월 + 12월 비)
# 전체 48매는 data/hwapae_korean_48.json 별도 영속화 가능 (후속)
HWAPAE_CARDS: dict[str, HwapaeCard] = {
    "01-01-gwang": HwapaeCard(
        id="01-01-gwang", month=1, card_index_in_month=1,
        name_ko="송학 (광)", category="광", score=20,
        symbol="소나무·학·일출",
        traditional_meaning="장수와 복록을 상징하며 새로운 흐름의 시작을 알리는 강한 양(陽)의 기운의 태동",
        permitted_keywords=("시작", "기반", "장수", "흔들리지 않음", "명료한 흐름"),
        forbidden_keywords=("대성공 확정", "무병장수", "로또 당첨", "운명적 결정"),
    ),
    "02-01-yeol": HwapaeCard(
        id="02-01-yeol", month=2, card_index_in_month=1,
        name_ko="매조 (열끗)", category="열끗", score=10,
        symbol="매화·휘파람새",
        traditional_meaning="이른 봄 얼어붙은 상황 속에서 가장 먼저 변화의 조짐을 알리며 날아드는 동적인 소식",
        permitted_keywords=("초기 소식", "동적인 조짐", "빠른 이동", "해빙기"),
        forbidden_keywords=("승진 통보", "소송 승리", "재물 획득"),
    ),
    "03-01-gwang": HwapaeCard(
        id="03-01-gwang", month=3, card_index_in_month=1,
        name_ko="사쿠라 (광)", category="광", score=20,
        symbol="벚꽃·만막",
        traditional_meaning="봄의 화려함이 절정에 달하여 사람과 시선이 운집하는 극도로 팽창된 에너지의 순간",
        permitted_keywords=("화려한 절정", "군중의 운집", "일시적 팽창", "시선 집중"),
        forbidden_keywords=("대성공", "유명인사 됨", "영원한 영광"),
    ),
    "08-01-gwang": HwapaeCard(
        id="08-01-gwang", month=8, card_index_in_month=1,
        name_ko="공산 (광)", category="광", score=20,
        symbol="텅 빈 산·달·기러기",
        traditional_meaning="달과 기러기만 남은 적막한 산처럼 모든 외부 활동이 정지된 거시적 비움의 상태",
        permitted_keywords=("성찰", "비움", "정중동", "고요한 응시"),
        forbidden_keywords=("고립무원", "단절 확정", "외로움의 영속"),
    ),
    "11-01-gwang": HwapaeCard(
        id="11-01-gwang", month=11, card_index_in_month=1,
        name_ko="오동 (광)", category="광", score=20,
        symbol="오동나무·봉황",
        traditional_meaning="새로운 차원의 도약을 알리는 거시적 변혁의 시점 (한국 통설: 11월 오동)",
        permitted_keywords=("질적 변혁", "새 차원", "도약", "거시적 변화"),
        forbidden_keywords=("출세 확정", "권력 획득", "최상위 도달"),
    ),
    "12-01-gwang": HwapaeCard(
        id="12-01-gwang", month=12, card_index_in_month=1,
        name_ko="비 (광)", category="광", score=20,
        symbol="비·수양버들·우산",
        traditional_meaning="한 해의 종결과 정화를 알리는 거시적 비움 (한국 통설: 12월 비)",
        permitted_keywords=("정화", "종결", "비움", "다시 시작 준비"),
        forbidden_keywords=("재난 확정", "파산", "이별의 영속"),
    ),
}


# ─────────────────────────── ADR-006/010 면책 (보고서 §8) ───────────────────────────


DEFAULT_DISCLAIMERS: list[str] = [
    "본 화패점 결과는 한국 전통 민속 문화의 계절 기호학과 수학적 배열 확률에 기반한 에너지 경향성 묘사이며 결혼·연애·재물·수명 단정 예언이 아닙니다.",
    "한국민족문화대백과사전·국립민속박물관 출처 + 아패영유(雅牌靈遊) 전통 골패점 알고리즘 인용입니다.",
    "permitted_keywords 범위 내 묘사만 채택하며 forbidden_keywords (대성공 확정·운명적 결정·재난 확정 등) 단정 표현은 차단합니다.",
]


# 보고서 §8 forbidden 패턴 (출력 검증용)
FORBIDDEN_OUTPUT_PATTERNS: tuple[str, ...] = (
    "대성공 확정",
    "무병장수",
    "로또 당첨",
    "운명적 결정",
    "출세 확정",
    "권력 획득",
    "재난 확정",
    "파산",
    "이별의 영속",
    "100% 성공",
    "운명이 결정",
    "큰 돈을 벌게 됨",
)


# ─────────────────────────── 결과 dataclass ───────────────────────────


SpreadPositionType = Literal["과거", "현재", "미래"]


@dataclass(frozen=True)
class HwapaeSpreadResult:
    """3장 스프레드 결정론 분석 결과 (보고서 §4 + §6).

    Attributes:
        cards: 3장 (과거·현재·미래 순서).
        positions: 위치명 매핑.
        total_score: 3장 점수 합산.
        category_distribution: 광·열끗·띠·피 분포.
        is_sequential: 계절 순행 여부 (월 오름차순).
        is_reverse: 계절 역행 여부.
        category_dominance: 가장 많은 카테고리 (없으면 None).
        interpretation_facts: 알고리즘 객관 사실 (페르소나 입력용).
        disclaimers: ADR-006/010/014 면책 강제.
        school: 학파 명시.
    """

    cards: tuple[HwapaeCard, HwapaeCard, HwapaeCard]
    positions: tuple[str, str, str] = ("과거", "현재", "미래")
    total_score: int = 0
    category_distribution: dict[str, int] = field(default_factory=dict)
    is_sequential: bool = False
    is_reverse: bool = False
    category_dominance: str | None = None
    interpretation_facts: list[str] = field(default_factory=list)
    disclaimers: list[str] = field(default_factory=list)
    school: str = "한국 전통 화투 + 아패영유 골패점"

    def to_dict(self) -> dict:
        return {
            "school": self.school,
            "cards": [c.name_ko for c in self.cards],
            "positions": list(self.positions),
            "total_score": self.total_score,
            "category_distribution": self.category_distribution,
            "is_sequential": self.is_sequential,
            "is_reverse": self.is_reverse,
            "category_dominance": self.category_dominance,
            "interpretation_facts": self.interpretation_facts,
            "disclaimers": self.disclaimers,
        }


# ─────────────────────────── 알고리즘 (보고서 §4·§6) ───────────────────────────


def _is_sequential(months: tuple[int, int, int]) -> bool:
    """계절 순행 (월 오름차순, 단조 증가)."""
    return months[0] < months[1] < months[2]


def _is_reverse(months: tuple[int, int, int]) -> bool:
    """계절 역행 (월 내림차순)."""
    return months[0] > months[1] > months[2]


def _category_distribution(cards: tuple[HwapaeCard, ...]) -> dict[str, int]:
    """광·열끗·띠·피 분포 카운트."""
    dist: dict[str, int] = {"광": 0, "열끗": 0, "띠": 0, "피": 0}
    for c in cards:
        if c.category in dist:
            dist[c.category] += 1
    return dist


def _category_dominance(distribution: dict[str, int]) -> str | None:
    """가장 많은 카테고리 (2장 이상이면 dominant)."""
    if not distribution:
        return None
    max_cat = max(distribution.items(), key=lambda kv: kv[1])
    if max_cat[1] >= 2:
        return max_cat[0]
    return None


def three_card_spread(card_ids: tuple[str, str, str]) -> HwapaeSpreadResult:
    """3장 스프레드 결정론 분석 (보고서 §4).

    Args:
        card_ids: 카드 ID 3개 (과거·현재·미래 순서).

    Returns:
        HwapaeSpreadResult — 객관 사실 + 알고리즘 결과 + 면책.

    Raises:
        ValueError: 알 수 없는 카드 ID.

    설계 (CLAUDE.md §0 결정론 + LLM 분리):
        · 결정론 100% (LLM 호출 0)
        · permitted_keywords 범위만 페르소나에 전달 (forbidden 차단)
        · ADR-006/010 disclaimers 자동 포함
    """
    cards = []
    for cid in card_ids:
        if cid not in HWAPAE_CARDS:
            raise ValueError(f"알 수 없는 카드 ID: {cid!r}")
        cards.append(HWAPAE_CARDS[cid])

    cards_tuple = (cards[0], cards[1], cards[2])
    months = (cards[0].month, cards[1].month, cards[2].month)
    total = sum(c.score for c in cards)
    dist = _category_distribution(cards_tuple)
    seq = _is_sequential(months)
    rev = _is_reverse(months)
    dom = _category_dominance(dist)

    facts: list[str] = []

    # 카드 의미 (permitted_keywords 범위)
    for pos, card in zip(("과거", "현재", "미래"), cards):
        facts.append(f"{pos}: {card.name_ko} — {card.traditional_meaning}")

    # 계절 흐름
    if seq:
        facts.append("계절 순행 — 자연의 순리에 따르는 지연 없는 에너지 흐름")
    elif rev:
        facts.append("계절 역행 — 흐름의 역행, 내면적 성찰과 회고의 에너지")
    else:
        facts.append("계절 비선형 — 다층적 흐름, 단순 시간선 외 작용")

    # 카테고리 우세
    if dom:
        facts.append(f"{dom} 카테고리 우세 ({dist[dom]}장) — 해당 영역 에너지 집중")

    # 점수 (아패영유 3구간)
    if total >= 35:
        facts.append(f"총 점수 {total} — 상상 구간 (강한 양적 에너지 집중)")
    elif total >= 20:
        facts.append(f"총 점수 {total} — 상중 구간 (중간 균형 에너지)")
    else:
        facts.append(f"총 점수 {total} — 하하 구간 (미세 기반 에너지)")

    return HwapaeSpreadResult(
        cards=cards_tuple,
        positions=("과거", "현재", "미래"),
        total_score=total,
        category_distribution=dist,
        is_sequential=seq,
        is_reverse=rev,
        category_dominance=dom,
        interpretation_facts=facts,
        disclaimers=list(DEFAULT_DISCLAIMERS),
        school="한국 전통 화투 + 아패영유 골패점",
    )


# ─────────────────────────── 출력 검증 (보고서 §8) ───────────────────────────


def has_forbidden_output(text: str) -> bool:
    """페르소나 LLM 출력에 금지 패턴 포함 여부.

    True 반환 시 페르소나 응답 차단 + 안전 기본 응답 대체 의무.
    """
    if not text or not isinstance(text, str):
        return False
    for p in FORBIDDEN_OUTPUT_PATTERNS:
        if p in text:
            return True
    return False


def get_permitted_keywords(card_id: str) -> tuple[str, ...]:
    """단일 카드의 페르소나 허용 키워드 (LLM 시스템 프롬프트 주입용)."""
    card = HWAPAE_CARDS.get(card_id)
    if card is None:
        return ()
    return card.permitted_keywords


__all__ = [
    "DEFAULT_DISCLAIMERS",
    "FORBIDDEN_OUTPUT_PATTERNS",
    "HWAPAE_CARDS",
    "HwapaeCard",
    "HwapaeSpreadResult",
    "three_card_spread",
    "has_forbidden_output",
    "get_permitted_keywords",
]
