"""발음오행(發音五行) — 보고서 §3 본문화.

훈민정음 해례본 합자 원리 기준 한글 자음의 5음 매핑:
  · ㄱ, ㅋ           → 木 (어금닛소리, 牙音)
  · ㄴ, ㄷ, ㄹ, ㅌ   → 火 (혓소리, 舌音)
  · ㅇ, ㅎ           → 土 (목구멍소리, 喉音)
  · ㅅ, ㅈ, ㅊ       → 金 (잇소리, 齒音)
  · ㅁ, ㅂ, ㅍ       → 水 (입술소리, 脣音)

발음오행 검증:
  · 성-이름1-이름2 초성 흐름이 상생 흐름이면 길
    상생: 木→火→土→金→水→木
  · 상극: 木↔土, 火↔金, 土↔水, 金↔木, 水↔火
  · 같은 오행 연속(比和)은 무난, 상극 연속은 흉
"""

from __future__ import annotations

from dataclasses import dataclass


# 오행
WOOD = "목"   # 木
FIRE = "화"   # 火
EARTH = "토"  # 土
METAL = "금"  # 金
WATER = "수"  # 水


# 초성 → 오행 매핑 (훈민정음 해례본 합자 원리)
_INITIAL_TO_OHAENG: dict[str, str] = {
    "ㄱ": WOOD, "ㅋ": WOOD, "ㄲ": WOOD,
    "ㄴ": FIRE, "ㄷ": FIRE, "ㄹ": FIRE, "ㅌ": FIRE, "ㄸ": FIRE,
    "ㅇ": EARTH, "ㅎ": EARTH,
    "ㅅ": METAL, "ㅈ": METAL, "ㅊ": METAL, "ㅆ": METAL, "ㅉ": METAL,
    "ㅁ": WATER, "ㅂ": WATER, "ㅍ": WATER, "ㅃ": WATER,
}


# ─────────────────────────── 한글 초성 추출 ───────────────────────────

# 한글 음절은 유니코드 0xAC00 ~ 0xD7A3 범위
# 초성 = (음절 - 0xAC00) / 588
_HANGUL_BASE = 0xAC00
_CHOSUNG_LIST = [
    "ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ", "ㅅ",
    "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
]


def extract_chosung(syllable: str) -> str:
    """한글 음절에서 초성 1개 추출. 한글 아니면 빈 문자열."""
    if not isinstance(syllable, str) or len(syllable) == 0:
        return ""
    code = ord(syllable[0])
    if _HANGUL_BASE <= code <= 0xD7A3:
        idx = (code - _HANGUL_BASE) // 588
        if 0 <= idx < len(_CHOSUNG_LIST):
            return _CHOSUNG_LIST[idx]
    return ""


def chosung_to_ohaeng(chosung: str) -> str:
    """초성 → 오행. 매핑 없으면 빈 문자열."""
    return _INITIAL_TO_OHAENG.get(chosung, "")


def syllable_to_ohaeng(syllable: str) -> str:
    """한글 음절 → 발음오행."""
    return chosung_to_ohaeng(extract_chosung(syllable))


# ─────────────────────────── 상생·상극 ───────────────────────────

# 상생: 木→火→土→金→水→木 (시계방향)
_SANGSAENG: dict[str, str] = {
    WOOD: FIRE,
    FIRE: EARTH,
    EARTH: METAL,
    METAL: WATER,
    WATER: WOOD,
}

# 상극: 木→土→水→火→金→木
_SANGGEUK: dict[str, str] = {
    WOOD: EARTH,
    EARTH: WATER,
    WATER: FIRE,
    FIRE: METAL,
    METAL: WOOD,
}


def relation(a: str, b: str) -> str:
    """두 오행의 관계.

    Returns:
        "sangsaeng" — a → b 상생 (a가 b를 낳음)
        "sanggeuk"  — a → b 상극 (a가 b를 이김)
        "bihwa"     — a == b (비화, 같은 오행)
        ""          — 미정의
    """
    if not a or not b:
        return ""
    if a == b:
        return "bihwa"
    if _SANGSAENG.get(a) == b:
        return "sangsaeng"
    if _SANGGEUK.get(a) == b:
        return "sanggeuk"
    # 역방향
    if _SANGSAENG.get(b) == a:
        return "sangsaeng_reverse"  # b가 a를 낳음
    if _SANGGEUK.get(b) == a:
        return "sanggeuk_reverse"
    return ""


# ─────────────────────────── 평가 ───────────────────────────

GRADE_GOOD = "good"        # 상생 흐름
GRADE_NEUTRAL = "neutral"  # 비화 혼합
GRADE_BAD = "bad"          # 상극 포함


@dataclass(frozen=True)
class BaleumReport:
    syllables: list[str]
    ohaeng_sequence: list[str]
    relations: list[str]      # 연속 2글자 관계
    grade: str
    reason: str = ""


def evaluate_baleum(name_korean: str) -> BaleumReport:
    """한글 이름 전체의 발음오행 평가.

    Args:
        name_korean: 성+이름 한글 (예: "이성민"). 공백 무시.

    Returns:
        BaleumReport — 오행 시퀀스 + 인접 관계 + 종합 등급.

    평가 기준:
      · 인접 두 글자 모두 상생 → GOOD
      · 비화(같음) 또는 상생 혼합 → NEUTRAL
      · 상극 한 번이라도 등장 → BAD
    """
    syllables = [c for c in (name_korean or "") if c.strip()]
    ohaeng_seq = [syllable_to_ohaeng(s) for s in syllables]

    if len(ohaeng_seq) < 2:
        return BaleumReport(
            syllables=syllables,
            ohaeng_sequence=ohaeng_seq,
            relations=[],
            grade=GRADE_NEUTRAL,
            reason="음절 수 부족",
        )

    rels: list[str] = []
    for i in range(len(ohaeng_seq) - 1):
        rels.append(relation(ohaeng_seq[i], ohaeng_seq[i + 1]))

    has_geuk = any("sanggeuk" in r for r in rels)
    all_saeng = all(r == "sangsaeng" for r in rels) and len(rels) > 0

    if has_geuk:
        grade = GRADE_BAD
        reason = "상극(相剋) 흐름 — 발음 기운이 충돌"
    elif all_saeng:
        grade = GRADE_GOOD
        reason = "상생(相生) 흐름 — 발음 기운이 순환"
    else:
        grade = GRADE_NEUTRAL
        reason = "비화·상생 혼합 — 무난"

    return BaleumReport(
        syllables=syllables,
        ohaeng_sequence=ohaeng_seq,
        relations=rels,
        grade=grade,
        reason=reason,
    )


def report_to_dict(report: BaleumReport) -> dict:
    return {
        "syllables": list(report.syllables),
        "ohaeng_sequence": list(report.ohaeng_sequence),
        "relations": list(report.relations),
        "grade": report.grade,
        "reason": report.reason,
    }
