"""ADR-119 — 한국 12지신 띠별 운세 + 12×12 궁합 매트릭스.

본 모듈은 ADR-002·006·010·015 정합.

영역:
  · 12지신 (子丑寅卯辰巳午未申酉戌亥) 메타
  · 정통 궁합 분류 (삼합·육합·육해·원진살)
  · 12×12 = 144 매트릭스 결정론 점수
  · 매년 12지 운세 (점치는 해 干支 × 본인 띠)

출처 (ADR-010 사실성 분리):
  · 한국학중앙연구원 한국민족문화대백과사전 (encykorea.aks.ac.kr) 12지신 표제
  · 정통 삼합三合: 申子辰 (水) / 巳酉丑 (金) / 寅午戌 (火) / 亥卯未 (木)
  · 정통 육합六合: 子丑·寅亥·卯戌·辰酉·巳申·午未
  · 정통 육해六害: 子未·丑午·寅巳·卯辰·申亥·酉戌
  · 정통 원진살元辰煞: 子未·丑午·寅酉·卯申·辰亥·巳戌

원칙:
  · 단정적 예언 차단 — "이혼·파산·사망" 단정 X
  · 한국 정통 단일 학파 (삼합·육합·육해·원진살) — ADR-002 정합
  · 동일 입력 → 동일 궁합 결정론

면책:
  · 의료·법률·금융 단독 근거 X
  · 결혼·이혼 단정 X — 흐름 톤만
"""

from __future__ import annotations

from dataclasses import dataclass


# ─────────────────────────── 12지신 메타 ───────────────────────────

@dataclass(frozen=True)
class ZodiacAnimal:
    """12지신 단일 띠 메타.

    Attributes:
        idx: 0~11 (子=0)
        key: 영문 키
        label_ko: 한국어 명 (쥐·소·호랑이 ...)
        hanja: 한자 (子·丑·寅 ...)
        element: 오행 (수·토·목·목·토·화·화·토·금·금·토·수)
        season: 계절 (겨울·환절기·봄·봄·환절기·여름·여름·환절기·가을·가을·환절기·겨울)
        hour_range: 시각 범위 (예: "23~01시")
    """
    idx: int
    key: str
    label_ko: str
    hanja: str
    element: str
    season: str
    hour_range: str


# 한국 정통 12지신 메타 (천간 12지지 표준)
ZODIAC_ANIMALS: tuple[ZodiacAnimal, ...] = (
    ZodiacAnimal(0,  "ja",  "쥐",   "子", "수", "겨울",   "23~01시"),
    ZodiacAnimal(1,  "chuk","소",   "丑", "토", "환절기", "01~03시"),
    ZodiacAnimal(2,  "in",  "호랑이","寅", "목", "봄",     "03~05시"),
    ZodiacAnimal(3,  "myo", "토끼", "卯", "목", "봄",     "05~07시"),
    ZodiacAnimal(4,  "jin", "용",   "辰", "토", "환절기", "07~09시"),
    ZodiacAnimal(5,  "sa",  "뱀",   "巳", "화", "여름",   "09~11시"),
    ZodiacAnimal(6,  "o",   "말",   "午", "화", "여름",   "11~13시"),
    ZodiacAnimal(7,  "mi",  "양",   "未", "토", "환절기", "13~15시"),
    ZodiacAnimal(8,  "sin", "원숭이","申", "금", "가을",   "15~17시"),
    ZodiacAnimal(9,  "yu",  "닭",   "酉", "금", "가을",   "17~19시"),
    ZodiacAnimal(10, "sul", "개",   "戌", "토", "환절기", "19~21시"),
    ZodiacAnimal(11, "hae", "돼지", "亥", "수", "겨울",   "21~23시"),
)


def animal_by_year(year: int) -> ZodiacAnimal:
    """양력 년도 → 12지 띠.

    기준: 1900년 = 子 (쥐), 1901년 = 丑 (소), ...
    실 한국 정통은 음력 정월 초하루 기준이나, 본 시스템은 양력 단순화.
    """
    idx = (year - 1900) % 12
    return ZODIAC_ANIMALS[idx]


def animal_by_key(key: str) -> ZodiacAnimal | None:
    """영문 키 (ja·chuk·in·myo 등)로 조회."""
    for a in ZODIAC_ANIMALS:
        if a.key == key:
            return a
    return None


def animal_by_idx(idx: int) -> ZodiacAnimal | None:
    """0~11 idx로 조회."""
    if 0 <= idx < 12:
        return ZODIAC_ANIMALS[idx]
    return None


# ─────────────────────────── 12×12 궁합 매트릭스 ───────────────────────────

# 정통 삼합三合 — 가장 강한 결합 (90점)
_SAMHAP: frozenset[frozenset[int]] = frozenset({
    frozenset({8, 0, 4}),   # 申子辰 (水)
    frozenset({5, 9, 1}),   # 巳酉丑 (金)
    frozenset({2, 6, 10}),  # 寅午戌 (火)
    frozenset({11, 3, 7}),  # 亥卯未 (木)
})

# 정통 육합六合 — 두 띠의 안정 결합 (85점)
_YUKHAP: frozenset[frozenset[int]] = frozenset({
    frozenset({0, 1}),   # 子丑
    frozenset({2, 11}),  # 寅亥
    frozenset({3, 10}),  # 卯戌
    frozenset({4, 9}),   # 辰酉
    frozenset({5, 8}),   # 巳申
    frozenset({6, 7}),   # 午未
})

# 정통 육해六害 — 마찰의 결 (55점)
_YUKHAE: frozenset[frozenset[int]] = frozenset({
    frozenset({0, 7}),   # 子未
    frozenset({1, 6}),   # 丑午
    frozenset({2, 5}),   # 寅巳
    frozenset({3, 4}),   # 卯辰
    frozenset({8, 11}),  # 申亥
    frozenset({9, 10}),  # 酉戌
})

# 정통 원진살元辰煞 — 가장 어려운 결 (45점)
_WONJINSAL: frozenset[frozenset[int]] = frozenset({
    frozenset({0, 7}),   # 子未 (육해와 중복 — 원진살 우선)
    frozenset({1, 6}),   # 丑午
    frozenset({2, 9}),   # 寅酉
    frozenset({3, 8}),   # 卯申
    frozenset({4, 11}),  # 辰亥
    frozenset({5, 10}),  # 巳戌
})


@dataclass(frozen=True)
class ZodiacCompatibility:
    """띠 궁합 결정론 결과.

    ★ 의도적 부재 필드 (ADR-006):
      - marriage_outcome, breakup_risk — 결혼·이별 단정 X
    """
    animal1_label: str
    animal2_label: str
    relation_type: str  # "삼합" | "육합" | "육해" | "원진살" | "보통"
    score: int          # 45~90
    flow_tone_ko: str
    disclaimer: str


_RELATION_TONES: dict[str, str] = {
    "삼합": "삼합三合 — 가장 깊은 공명의 결",
    "육합": "육합六合 — 안정의 결",
    "육해": "육해六害 — 마찰이 학습이 되는 결",
    "원진살": "원진살元辰煞 — 차이가 큰 결",
    "보통": "보통의 결 — 평이한 흐름",
    "동일": "동일 띠 — 같은 결의 흐름",
}


_DISCLAIMER = (
    "본 띠 궁합은 한국 정통 12지 매트릭스 (삼합·육합·육해·원진살) 결정론 "
    "흐름 톤으로, 결혼·이별·연애 성공 단정 X. 참고용이며 의료·법률·금융 "
    "의사결정 단독 근거 X. 한국학중앙연구원 정통 분류."
)


def compute_animal_compatibility(animal1_key: str, animal2_key: str) -> ZodiacCompatibility | None:
    """두 띠 → 144 매트릭스 궁합 결정론.

    Args:
        animal1_key: 첫 띠 영문 키 (ja·chuk·in·myo·jin·sa·o·mi·sin·yu·sul·hae)
        animal2_key: 둘째 띠 영문 키

    Returns:
        ZodiacCompatibility 또는 None
    """
    a1 = animal_by_key(animal1_key)
    a2 = animal_by_key(animal2_key)
    if a1 is None or a2 is None:
        return None

    pair = frozenset({a1.idx, a2.idx})

    # 동일 띠 (자기 자신) — 별도 처리
    if a1.idx == a2.idx:
        relation = "동일"
        score = 75
    # 분류 우선순위: 삼합 > 육합 > 원진살 > 육해 > 보통
    # ★ 삼합은 두 띠 모두 삼합 그룹에 속해야 함 (pair 길이 2 의무)
    elif any(pair.issubset(s) and len(pair) == 2 for s in _SAMHAP):
        relation = "삼합"
        score = 90
    elif pair in _YUKHAP:
        relation = "육합"
        score = 85
    elif pair in _WONJINSAL:
        relation = "원진살"
        score = 45
    elif pair in _YUKHAE:
        relation = "육해"
        score = 55
    else:
        relation = "보통"
        score = 70

    return ZodiacCompatibility(
        animal1_label=f"{a1.label_ko}띠({a1.hanja})",
        animal2_label=f"{a2.label_ko}띠({a2.hanja})",
        relation_type=relation,
        score=score,
        flow_tone_ko=_RELATION_TONES[relation],
        disclaimer=_DISCLAIMER,
    )


def compute_year_fortune(birth_year: int, target_year: int) -> ZodiacCompatibility | None:
    """본인 띠 + 점치는 해 띠 → 매년 운세 결정론.

    Args:
        birth_year: 생년 (예: 1990)
        target_year: 점치는 해 (예: 2026)

    Returns:
        ZodiacCompatibility (animal1=본인 띠, animal2=올해 띠)
    """
    my_animal = animal_by_year(birth_year)
    year_animal = animal_by_year(target_year)
    return compute_animal_compatibility(my_animal.key, year_animal.key)


def format_animal_for_prompt(a: ZodiacAnimal, target_year: int | None = None,
                              compat: ZodiacCompatibility | None = None) -> str:
    """Stage 2 시스템 프롬프트 주입용 띠 메타."""
    lines = [
        "[12지신 띠 결정론 — ADR-119]",
        f"  · 띠: {a.label_ko}띠 ({a.hanja})",
        f"  · 오행: {a.element} / 계절: {a.season}",
        f"  · 시각 영역: {a.hour_range}",
    ]
    if compat:
        lines.extend([
            f"  · 올해 띠와의 관계: {compat.relation_type} ({compat.flow_tone_ko})",
            f"  · 매트릭스 점수: {compat.score}점 (삼합 90·육합 85·보통 70·육해 55·원진살 45)",
        ])
    if target_year:
        lines.append(f"  · 점치는 해: {target_year}년")
    lines.append(
        "[안전 장치 — ADR-006] 결혼·이별·연애 성공·재정 단정 금지. 흐름 톤만."
    )
    return "\n".join(lines)


__all__ = [
    "ZodiacAnimal", "ZODIAC_ANIMALS",
    "ZodiacCompatibility",
    "animal_by_year", "animal_by_key", "animal_by_idx",
    "compute_animal_compatibility", "compute_year_fortune",
    "format_animal_for_prompt",
]
