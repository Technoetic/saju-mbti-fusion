"""ADR-106 — 12 별자리 144 궁합 매트릭스 (결정론).

본 모듈은 ADR-005·068·010 정합 — 결정론 점수 산출만, LLM 작문 분리.

영역:
  · 12 × 12 = 144 별자리 조합 궁합 점수
  · 4 element (불·흙·바람·물) × 3 modality (활동·고정·변동) 표준 매트릭스
  · 점성술 정통 동기·이질 element 관계 (Liz Greene·Stephen Arroyo 학파 인용)

원칙 (ADR-002·006·010·015 정합):
  · 단정적 예언 차단 — "결혼 가능" 단정 X, 흐름 톤만
  · 4 element 표준 분류 (학파 단일 강요 X — 점성술 보편 분류)
  · 사용자 입력 무관 결정론 (별자리 키 2개 입력 → 동일 결과)
  · 옵션 A 디폴트 (element 호환도) + 옵션 B 명시 시 modality 추가 분석

면책:
  · 의료·법률·금융 의사결정 단독 근거 X
  · 결혼·이혼·이별 단정 X (ADR-006)
"""

from __future__ import annotations

from dataclasses import dataclass

from .scoring import ZODIAC_SIGNS, sign_by_key


# ─────────────────────────── element 호환 매트릭스 ───────────────────────────

# 4 element × 4 element = 16 조합. 점성술 표준 (Liz Greene 1976 "Saturn",
# Stephen Arroyo 1975 "Astrology, Psychology, and the Four Elements" 정통):
#   · 동일 element: 깊은 공명 (resonant)
#   · 보완 element (fire-air / earth-water): 활발한 교류 (complementary)
#   · 이질 element (fire-water / fire-earth / air-earth / air-water): 마찰 또는 학습
ELEMENT_AFFINITY_SCORE: dict[tuple[str, str], int] = {
    # 동일 element — 깊은 공명 (85점)
    ("fire", "fire"):   85,
    ("earth", "earth"): 85,
    ("air", "air"):     85,
    ("water", "water"): 85,
    # 보완 element — 활발한 교류 (75점)
    ("fire", "air"):    75,
    ("air", "fire"):    75,
    ("earth", "water"): 75,
    ("water", "earth"): 75,
    # 이질 element — 마찰·학습 (55점)
    ("fire", "earth"):  55,
    ("earth", "fire"):  55,
    ("fire", "water"):  45,
    ("water", "fire"):  45,
    ("air", "earth"):   55,
    ("earth", "air"):   55,
    ("air", "water"):   50,
    ("water", "air"):   50,
}

ELEMENT_AFFINITY_TONE_KO: dict[str, str] = {
    "resonant":      "깊은 공명 — 같은 결의 흐름",
    "complementary": "활발한 교류 — 서로를 일깨우는 결",
    "frictional":    "마찰의 결 — 차이가 학습이 되는 흐름",
}


def _element_relation_type(e1: str, e2: str) -> str:
    """element 조합 → 관계 유형 키."""
    if e1 == e2:
        return "resonant"
    if {e1, e2} in ({"fire", "air"}, {"earth", "water"}):
        return "complementary"
    return "frictional"


# ─────────────────────────── modality 호환 매트릭스 ───────────────────────────

# 3 modality × 3 modality = 9 조합 (옵션 B — 정밀 분석 시):
#   · 동일 modality: 동조 또는 충돌 (강도 높음)
#   · 인접 modality (cardinal-fixed / fixed-mutable / mutable-cardinal): 보완
MODALITY_AFFINITY_SCORE: dict[tuple[str, str], int] = {
    ("cardinal", "cardinal"): 70,  # 둘 다 주도 → 결정 충돌 가능
    ("fixed", "fixed"):       70,  # 둘 다 고집 → 깊은 결속 또는 정체
    ("mutable", "mutable"):   75,  # 둘 다 적응 → 유연한 흐름
    ("cardinal", "fixed"):    72,
    ("fixed", "cardinal"):    72,
    ("fixed", "mutable"):     70,
    ("mutable", "fixed"):     70,
    ("mutable", "cardinal"):  73,
    ("cardinal", "mutable"):  73,
}

MODALITY_RELATION_TONE_KO: dict[tuple[str, str], str] = {
    ("cardinal", "cardinal"): "둘 다 주도하려는 결 — 결정 방향 합의가 흐름의 관건",
    ("fixed", "fixed"):       "둘 다 지속하려는 결 — 결속이 깊으나 변화 수용이 흐름의 관건",
    ("mutable", "mutable"):   "둘 다 적응하려는 결 — 유연하나 결단을 누가 내리는지가 관건",
    ("cardinal", "fixed"):    "주도와 지속의 결 — 시작과 안정의 보완",
    ("fixed", "cardinal"):    "지속과 주도의 결 — 안정과 시작의 보완",
    ("fixed", "mutable"):     "지속과 적응의 결 — 안정과 유연의 보완",
    ("mutable", "fixed"):     "적응과 지속의 결 — 유연과 안정의 보완",
    ("mutable", "cardinal"): "적응과 주도의 결 — 유연과 시작의 보완",
    ("cardinal", "mutable"): "주도와 적응의 결 — 시작과 유연의 보완",
}


# ─────────────────────────── 144 궁합 결과 dataclass ───────────────────────────

@dataclass(frozen=True)
class ZodiacCompatibility:
    """별자리 2개 조합 궁합 결정론 결과.

    ★ 의도적 부재 필드 (ADR-006 단정 차단):
      - marriage_outcome, breakup_risk — 결혼·이별 단정 X
      - sex_compatibility — 성적 단정 X
      - financial_outcome — 재정 단정 X
    """
    sign1_key: str
    sign1_label_ko: str
    sign2_key: str
    sign2_label_ko: str
    element1: str
    element2: str
    modality1: str
    modality2: str
    element_affinity_score: int   # 45~85
    modality_affinity_score: int  # 70~75 (옵션 B)
    relation_type: str            # "resonant" | "complementary" | "frictional"
    element_tone_ko: str
    modality_tone_ko: str
    overall_score: int            # element 70% + modality 30% 가중
    disclaimer: str


_DISCLAIMER = (
    "본 별자리 궁합은 점성술 element·modality 결정론 분류로, "
    "결혼·이별·연애 성공 단정 X. 4 element 분류는 점성술 보편 표준 "
    "(Liz Greene 1976·Stephen Arroyo 1975 정통). "
    "본 점수는 참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다."
)


def compute_compatibility(sign1_key: str, sign2_key: str) -> ZodiacCompatibility | None:
    """두 별자리 → 144 매트릭스 궁합 점수.

    동일 입력 → 동일 결과 (결정론). 별자리 키 잘못 시 None.

    Args:
        sign1_key: 첫 번째 별자리 영문 키 (aries~pisces)
        sign2_key: 두 번째 별자리 영문 키

    Returns:
        ZodiacCompatibility 또는 None (잘못된 키)

    Examples:
        >>> r = compute_compatibility("aries", "leo")
        >>> r.relation_type
        'resonant'
        >>> r.overall_score
        81
    """
    s1 = sign_by_key(sign1_key)
    s2 = sign_by_key(sign2_key)
    if s1 is None or s2 is None:
        return None

    element_score = ELEMENT_AFFINITY_SCORE.get((s1.element, s2.element), 50)
    modality_score = MODALITY_AFFINITY_SCORE.get((s1.modality, s2.modality), 70)
    relation_type = _element_relation_type(s1.element, s2.element)
    element_tone = ELEMENT_AFFINITY_TONE_KO[relation_type]
    modality_tone = MODALITY_RELATION_TONE_KO.get(
        (s1.modality, s2.modality), "두 결의 만남"
    )
    overall = round(element_score * 0.7 + modality_score * 0.3)

    return ZodiacCompatibility(
        sign1_key=s1.key,
        sign1_label_ko=s1.label_ko,
        sign2_key=s2.key,
        sign2_label_ko=s2.label_ko,
        element1=s1.element,
        element2=s2.element,
        modality1=s1.modality,
        modality2=s2.modality,
        element_affinity_score=element_score,
        modality_affinity_score=modality_score,
        relation_type=relation_type,
        element_tone_ko=element_tone,
        modality_tone_ko=modality_tone,
        overall_score=overall,
        disclaimer=_DISCLAIMER,
    )


def compatibility_matrix_summary() -> dict[str, int]:
    """144 조합 전체 매트릭스 통계 (회귀 테스트용).

    Returns:
        총 조합 수·관계 유형별 카운트
    """
    counts: dict[str, int] = {"resonant": 0, "complementary": 0, "frictional": 0, "total": 0}
    for s1 in ZODIAC_SIGNS:
        for s2 in ZODIAC_SIGNS:
            rt = _element_relation_type(s1.element, s2.element)
            counts[rt] += 1
            counts["total"] += 1
    return counts


def compatibility_score_distribution() -> dict[str, float]:
    """ADR-153 (2026-05-23) — 144 매트릭스 overall_score 분포 통계.

    /domain-priorities #16 (점수 22) 합성 베이스라인 확장.
    운영 데이터 누적 시 비교 기준.

    Returns:
        {
          "min": float,
          "max": float,
          "mean": float,
          "median": float,
          "stdev": float,
          "p25": float,  # 1사분위
          "p75": float,  # 3사분위
        }
    """
    import statistics

    scores: list[int] = []
    for s1 in ZODIAC_SIGNS:
        for s2 in ZODIAC_SIGNS:
            r = compute_compatibility(s1.key, s2.key)
            if r is not None:
                scores.append(r.overall_score)

    if not scores:
        return {"min": 0.0, "max": 0.0, "mean": 0.0, "median": 0.0, "stdev": 0.0, "p25": 0.0, "p75": 0.0}

    sorted_scores = sorted(scores)
    n = len(sorted_scores)
    return {
        "min": float(min(scores)),
        "max": float(max(scores)),
        "mean": round(statistics.mean(scores), 2),
        "median": round(statistics.median(scores), 2),
        "stdev": round(statistics.pstdev(scores), 2),
        "p25": float(sorted_scores[n // 4]),
        "p75": float(sorted_scores[3 * n // 4]),
    }


def format_compatibility_for_prompt(r: ZodiacCompatibility) -> str:
    """Stage 2 시스템 프롬프트에 주입할 궁합 메타 텍스트."""
    return (
        f"[별자리 궁합 결정론]\n"
        f"  · 본인: {r.sign1_label_ko} ({r.element1}/{r.modality1})\n"
        f"  · 상대: {r.sign2_label_ko} ({r.element2}/{r.modality2})\n"
        f"  · 관계 유형: {r.element_tone_ko}\n"
        f"  · 모달리티 결: {r.modality_tone_ko}\n"
        f"  · element 호환도: {r.element_affinity_score}점 / "
        f"modality 호환도: {r.modality_affinity_score}점 / "
        f"종합: {r.overall_score}점\n"
        f"[안전 장치 — ADR-006] element·modality 결정론 점수만 사용. "
        f"결혼·이별·연애 성공·재정 단정 금지. 흐름 톤으로만 풀이."
    )


__all__ = [
    "ELEMENT_AFFINITY_SCORE", "ELEMENT_AFFINITY_TONE_KO",
    "MODALITY_AFFINITY_SCORE", "MODALITY_RELATION_TONE_KO",
    "ZodiacCompatibility",
    "compute_compatibility",
    "compatibility_matrix_summary",
    "compatibility_score_distribution",
    "format_compatibility_for_prompt",
]
