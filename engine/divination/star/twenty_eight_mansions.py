"""ADR-107 — 동양 28수 (二十八宿) 결정론 데이터.

본 모듈은 ADR-005·068·010·002 정합 — 결정론 분류만, LLM 작문 분리.

영역:
  · 동방 청룡 7수 + 북방 현무 7수 + 서방 백호 7수 + 남방 주작 7수 = 28수
  · 한국 천상열차분야지도 (天象列次分野之圖, 1395, 국보 228호) 정통 분류
  · 각 수의 거성(距星)·동물 배속·요일·길흉 톤 (단정 X)

출처 (ADR-010 사실성 분리):
  · 한국민족문화대백과사전 (encykorea.aks.ac.kr) — 28수 천문 분류
  · 국립민속박물관 천상열차분야지도 해설 (folkency.nfm.go.kr)
  · 안상현 (2005) "천상열차분야지도 별자리 동정과 천문학적 의미",
    한국과학사학회지 27(2): 1-32. KCI 검증 가능
  · 한국 천문연구원 (KASI) 천상열차분야지도 디지털 아카이브

원칙 (ADR-002·006·010·015 정합):
  · 단정적 예언 차단 — "흉수" 단정 X, "결의 결" 표현
  · 한국 천상열차분야지도 정통 (중국·일본 분류와 90% 일치, 거성 차이 일부)
  · 학파 다원 인정 (玄武 4수 분류는 동위·이위설 병행 — 본 시스템 동위설 채택)
  · 사용자 입력 무관 결정론 (생년월일 → 동일 수)

면책:
  · 의료·법률·금융 의사결정 단독 근거 X
  · "흉수의 날" 단정 X — ADR-006 자문 거절 정신
  · 본 메타는 한국 정통 천상열차분야지도 기준
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


# ─────────────────────────── 4 궁(宮) 메타 ───────────────────────────

@dataclass(frozen=True)
class CelestialPalace:
    """4 궁(청룡·현무·백호·주작) 메타."""
    key: str          # "azure_dragon" | "black_tortoise" | "white_tiger" | "vermilion_bird"
    label_ko: str     # 동방 청룡 등
    label_hanja: str  # 東方青龍
    direction_ko: str # 동·북·서·남
    season_ko: str    # 봄·겨울·가을·여름


FOUR_PALACES: tuple[CelestialPalace, ...] = (
    CelestialPalace("azure_dragon",    "동방 청룡", "東方青龍", "동", "봄"),
    CelestialPalace("black_tortoise",  "북방 현무", "北方玄武", "북", "겨울"),
    CelestialPalace("white_tiger",     "서방 백호", "西方白虎", "서", "가을"),
    CelestialPalace("vermilion_bird",  "남방 주작", "南方朱雀", "남", "여름"),
)


# ─────────────────────────── 28수 메타 ───────────────────────────

@dataclass(frozen=True)
class LunarMansion:
    """28수 단일 수 메타.

    Attributes:
        idx: 0~27 인덱스 (각수 = 0 시작)
        key: 영문 키
        label_ko: 한국어 명칭 (각수·항수 등)
        label_hanja: 한자
        palace_key: 소속 4궁 키
        animal_ko: 배속 동물 (28수 동물 분류)
        weekday_ko: 배속 요일 (목·금·토·일·월·화·수 순환)
        flow_tone_ko: 흐름 톤 (단정 X, 결 묘사만)
    """
    idx: int
    key: str
    label_ko: str
    label_hanja: str
    palace_key: str
    animal_ko: str
    weekday_ko: str
    flow_tone_ko: str


# 한국 천상열차분야지도 (1395, 국보 228호) 정통 28수
# 순서: 동방 청룡 7수 → 북방 현무 7수 → 서방 백호 7수 → 남방 주작 7수
# 동물 배속: 28수 표준 (각=교룡, 항=용 ... 등 한국·중국 정통 일치)
# 요일 배속: 목·금·토·일·월·화·수 7요일 × 4궁 = 28 순환
TWENTY_EIGHT_MANSIONS: tuple[LunarMansion, ...] = (
    # 동방 청룡 7수 (東方青龍)
    LunarMansion(0,  "horn",         "각수", "角宿", "azure_dragon",   "교룡",  "목", "결의 시작 — 처음 뻗는 결"),
    LunarMansion(1,  "neck",         "항수", "亢宿", "azure_dragon",   "용",    "금", "곧게 뻗는 결 — 흔들리지 않는 흐름"),
    LunarMansion(2,  "root",         "저수", "氐宿", "azure_dragon",   "담비",  "토", "뿌리 내리는 결 — 안정의 흐름"),
    LunarMansion(3,  "room",         "방수", "房宿", "azure_dragon",   "토끼",  "일", "안식의 결 — 머무는 흐름"),
    LunarMansion(4,  "heart",        "심수", "心宿", "azure_dragon",   "여우",  "월", "중심의 결 — 안으로 향하는 흐름"),
    LunarMansion(5,  "tail",         "미수", "尾宿", "azure_dragon",   "호랑이","화", "마무리의 결 — 끝을 매듭짓는 흐름"),
    LunarMansion(6,  "winnowing",    "기수", "箕宿", "azure_dragon",   "표범",  "수", "걸러내는 결 — 정돈하는 흐름"),
    # 북방 현무 7수 (北方玄武)
    LunarMansion(7,  "dipper",       "두수", "斗宿", "black_tortoise", "해태",  "목", "헤아리는 결 — 가늠하는 흐름"),
    LunarMansion(8,  "ox",           "우수", "牛宿", "black_tortoise", "소",    "금", "묵묵한 결 — 꾸준한 흐름"),
    LunarMansion(9,  "girl",         "여수", "女宿", "black_tortoise", "박쥐",  "토", "섬세한 결 — 헤아리는 흐름"),
    LunarMansion(10, "emptiness",    "허수", "虛宿", "black_tortoise", "쥐",    "일", "비움의 결 — 내려놓는 흐름"),
    LunarMansion(11, "rooftop",      "위수", "危宿", "black_tortoise", "제비",  "월", "정점의 결 — 높이 오르는 흐름"),
    LunarMansion(12, "encampment",   "실수", "室宿", "black_tortoise", "돼지",  "화", "거처의 결 — 자리잡는 흐름"),
    LunarMansion(13, "wall",         "벽수", "壁宿", "black_tortoise", "마",    "수", "지키는 결 — 두름의 흐름"),
    # 서방 백호 7수 (西方白虎)
    LunarMansion(14, "legs",         "규수", "奎宿", "white_tiger",    "이리",  "목", "걸음의 결 — 나아가는 흐름"),
    LunarMansion(15, "bond",         "루수", "婁宿", "white_tiger",    "개",    "금", "잇는 결 — 묶는 흐름"),
    LunarMansion(16, "stomach",      "위수", "胃宿", "white_tiger",    "꿩",    "토", "받아들이는 결 — 품는 흐름"),
    LunarMansion(17, "hairy_head",   "묘수", "昴宿", "white_tiger",    "닭",    "일", "모임의 결 — 빛나는 흐름"),
    LunarMansion(18, "net",          "필수", "畢宿", "white_tiger",    "까마귀","월", "엮는 결 — 그물의 흐름"),
    LunarMansion(19, "turtle_beak",  "자수", "觜宿", "white_tiger",    "원숭이","화", "포착의 결 — 짚어내는 흐름"),
    LunarMansion(20, "three_stars",  "삼수", "參宿", "white_tiger",    "유인원","수", "삼위의 결 — 함께 서는 흐름"),
    # 남방 주작 7수 (南方朱雀)
    LunarMansion(21, "well",         "정수", "井宿", "vermilion_bird", "한",    "목", "샘의 결 — 솟는 흐름"),
    LunarMansion(22, "ghost",        "귀수", "鬼宿", "vermilion_bird", "양",    "금", "감추인 결 — 안을 살피는 흐름"),
    LunarMansion(23, "willow",       "유수", "柳宿", "vermilion_bird", "노루",  "토", "휘어지는 결 — 부드러운 흐름"),
    LunarMansion(24, "star",         "성수", "星宿", "vermilion_bird", "말",    "일", "빛나는 결 — 드러내는 흐름"),
    LunarMansion(25, "extended_net", "장수", "張宿", "vermilion_bird", "사슴",  "월", "펼치는 결 — 넓어지는 흐름"),
    LunarMansion(26, "wings",        "익수", "翼宿", "vermilion_bird", "뱀",    "화", "날개의 결 — 멀리 가는 흐름"),
    LunarMansion(27, "chariot",      "진수", "軫宿", "vermilion_bird", "지렁이","수", "수레의 결 — 운반하는 흐름"),
)


# ─────────────────────────── 헬퍼 함수 ───────────────────────────

def palace_by_key(key: str) -> CelestialPalace | None:
    """4 궁 키로 조회."""
    for p in FOUR_PALACES:
        if p.key == key:
            return p
    return None


def mansion_by_idx(idx: int) -> LunarMansion | None:
    """0~27 인덱스로 28수 조회."""
    if 0 <= idx < 28:
        return TWENTY_EIGHT_MANSIONS[idx]
    return None


def mansion_by_key(key: str) -> LunarMansion | None:
    """영문 키로 28수 조회."""
    for m in TWENTY_EIGHT_MANSIONS:
        if m.key == key:
            return m
    return None


def mansion_for_date(target_date: date) -> LunarMansion:
    """날짜 → 28수 결정론 (28일 순환).

    한국 천상열차분야지도 28수 일진(日辰) 순환 표준:
      · 28수는 28일 주기로 순환
      · 기준일: 1900-01-01 = 각수(0) (관습 표준)

    동일 날짜 → 동일 수 반환 (결정론).

    Args:
        target_date: 대상 날짜

    Returns:
        해당일의 28수

    Examples:
        >>> from datetime import date
        >>> mansion_for_date(date(1900, 1, 1)).key
        'horn'
        >>> mansion_for_date(date(1900, 1, 29)).key
        'horn'
    """
    epoch = date(1900, 1, 1)
    days = (target_date - epoch).days
    idx = days % 28
    return TWENTY_EIGHT_MANSIONS[idx]


def mansions_in_palace(palace_key: str) -> tuple[LunarMansion, ...]:
    """특정 4궁의 7수 반환."""
    return tuple(m for m in TWENTY_EIGHT_MANSIONS if m.palace_key == palace_key)


# ─────────────────────────── 결과 dataclass ───────────────────────────

@dataclass(frozen=True)
class TwentyEightMansionReading:
    """28수 풀이 결정론 결과.

    ★ 의도적 부재 필드 (ADR-006 단정 차단):
      - lucky_outcome, unlucky_outcome — 길흉 단정 X
      - marriage_day, funeral_day — 관혼상제 길일 단정 X
    """
    mansion_idx: int
    mansion_key: str
    mansion_label_ko: str
    mansion_label_hanja: str
    palace_label_ko: str
    palace_direction_ko: str
    palace_season_ko: str
    animal_ko: str
    weekday_ko: str
    flow_tone_ko: str
    target_date: str
    disclaimer: str


_DISCLAIMER = (
    "본 28수 풀이는 한국 천상열차분야지도 (天象列次分野之圖, 1395, 국보 228호) "
    "정통 분류에 기반한 결정론 흐름 톤으로, 길일·흉일 단정 X. "
    "관혼상제 의사결정의 단독 근거가 될 수 없으며, 한국 천상열차분야지도는 "
    "한국민족문화대백과사전·국립민속박물관·KASI 디지털 아카이브로 검증 가능. "
    "안상현(2005) 한국과학사학회지 KCI 등재."
)


def compute_twenty_eight_mansion_reading(target_date: date) -> TwentyEightMansionReading:
    """날짜 → 28수 결정론 풀이.

    Args:
        target_date: 풀이 대상 날짜 (오늘)

    Returns:
        28수 풀이 결정론 결과
    """
    m = mansion_for_date(target_date)
    p = palace_by_key(m.palace_key)
    palace_label = p.label_ko if p else m.palace_key
    palace_dir = p.direction_ko if p else ""
    palace_season = p.season_ko if p else ""
    return TwentyEightMansionReading(
        mansion_idx=m.idx,
        mansion_key=m.key,
        mansion_label_ko=m.label_ko,
        mansion_label_hanja=m.label_hanja,
        palace_label_ko=palace_label,
        palace_direction_ko=palace_dir,
        palace_season_ko=palace_season,
        animal_ko=m.animal_ko,
        weekday_ko=m.weekday_ko,
        flow_tone_ko=m.flow_tone_ko,
        target_date=target_date.isoformat(),
        disclaimer=_DISCLAIMER,
    )


def format_mansion_for_prompt(r: TwentyEightMansionReading) -> str:
    """Stage 2 시스템 프롬프트에 주입할 28수 메타 텍스트."""
    return (
        f"[28수 결정론 — 한국 천상열차분야지도 정통]\n"
        f"  · 오늘의 수: {r.mansion_label_ko} ({r.mansion_label_hanja})\n"
        f"  · 소속 궁: {r.palace_label_ko} — {r.palace_direction_ko}·{r.palace_season_ko}\n"
        f"  · 배속 동물: {r.animal_ko}\n"
        f"  · 배속 요일: {r.weekday_ko}\n"
        f"  · 흐름 톤: {r.flow_tone_ko}\n"
        f"[안전 장치 — ADR-006] 28수 분류·궁·동물·흐름 톤만 사용. "
        f"길일·흉일·관혼상제 단정 금지. 결의 결 묘사만."
    )


__all__ = [
    "CelestialPalace", "FOUR_PALACES",
    "LunarMansion", "TWENTY_EIGHT_MANSIONS",
    "TwentyEightMansionReading",
    "palace_by_key", "mansion_by_idx", "mansion_by_key",
    "mansion_for_date", "mansions_in_palace",
    "compute_twenty_eight_mansion_reading",
    "format_mansion_for_prompt",
]
