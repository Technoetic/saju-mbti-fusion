"""ADR-024 A8/A9 MBTI 16×16 호환 매트릭스 v2 — 결정론 4단계 알고리즘.

보고서 §5 + §6 본문화:
  · 기본 5점 → S/N 동기화 → Socionics 관계 → Keirsey 상보성 → 정규화 [1,9]
  · 256 전수 대칭 매트릭스 (대칭 고려 시 136 고유 조합) 결정론 산출
  · Jung·Myers·Keirsey·Socionics 결합 학파 명시
  · DEFAULT_DISCLAIMERS 강제 (ADR-006/010/014 정합)

설계 (CLAUDE.md §0 + ADR-021/023 패턴 정합):
  · 결정론 100% — LLM 호출 0
  · compat.py 라인 8 "간이" 32 엔트리와 별개 모듈 (호환 유지)
  · ADR-014 경계 명확화 — 입력은 사용자 명시 두 MBTI (사주→MBTI 단정 X)
  · 학파 명시 학설로 자기실현적 예언 회피

학술 근거 (vault/references/jung-myers-keirsey-socionics.md):
  · Carl Jung 《Psychologische Typen》(1921)
  · Isabel Briggs Myers 《Gifts Differing》(1980)
  · David Keirsey 《Please Understand Me II》(1998) ISBN 9781885705020
  · Aushra Augusta Socionics 14 Intertype Relations
  · 윤호균·이선희 (2000) "부부의 MBTI성격유형의 유사성과 의사소통 및 결혼만족도의 관계"
  · 공성숙 (2010) "부부클리닉 방문부부의 MBTI 성격유형과 결혼만족도" KoreaMed
"""

from __future__ import annotations

from dataclasses import dataclass


# ─────────────────────────── MBTI 16 유형 ───────────────────────────


_VALID_TYPES: frozenset[str] = frozenset({
    "INTJ", "INTP", "ENTJ", "ENTP",
    "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ",
    "ISTP", "ISFP", "ESTP", "ESFP",
})


# ─────────────────────────── Socionics Dual (짝) 관계 8쌍 ───────────────────────────
# 보고서 §3.3.b: 주기능 = 상대 열등기능, E/I 다르되 J/P 공유


_DUAL_PAIRS: frozenset[frozenset[str]] = frozenset({
    frozenset({"INTJ", "ESFP"}),
    frozenset({"INTP", "ESFJ"}),
    frozenset({"ENTJ", "ISFP"}),
    frozenset({"ENTP", "ISFJ"}),
    frozenset({"INFJ", "ESTP"}),
    frozenset({"INFP", "ESTJ"}),
    frozenset({"ENFJ", "ISTP"}),
    frozenset({"ENFP", "ISTJ"}),
})


# ─────────────────────────── Mirror (거울) 관계 — 동일 쿼드라 ───────────────────────────
# 보고서 §3.3.a: 동일 인지기능 4종 + 주/부 위계 교차 역전. 동일 쿼드라.


_MIRROR_PAIRS: frozenset[frozenset[str]] = frozenset({
    # Alpha quadra (Ne, Si, Fe, Ti)
    frozenset({"INTP", "ENTP"}),
    frozenset({"ISFJ", "ESFJ"}),
    # Beta quadra (Se, Ni, Fe, Ti)  → MBTI에서는 ENFJ/INFJ/ESTP/ISTP
    frozenset({"INFJ", "ENFJ"}),
    frozenset({"ISTP", "ESTP"}),
    # Gamma quadra (Ne, Si, Fi, Te) → INFP/ENFP/ISTJ/ESTJ
    frozenset({"INFP", "ENFP"}),
    frozenset({"ISTJ", "ESTJ"}),
    # Delta quadra (Se, Ni, Fi, Te) → INTJ/ENTJ/ISFP/ESFP
    frozenset({"INTJ", "ENTJ"}),
    frozenset({"ISFP", "ESFP"}),
})


# ─────────────────────────── Activation (활동) 관계 ───────────────────────────
# 보고서 §5.1 2단계: Dual과 인지기능 공유, E/I 태도만 동일


_ACTIVATION_PAIRS: frozenset[frozenset[str]] = frozenset({
    frozenset({"INTP", "ENFJ"}),
    frozenset({"INFP", "ENTJ"}),
    frozenset({"ISTP", "ESFJ"}),
    frozenset({"ISFP", "ESTJ"}),
    frozenset({"INTJ", "ENFP"}),
    frozenset({"INFJ", "ENTP"}),
    frozenset({"ISTJ", "ESFP"}),
    frozenset({"ISFJ", "ESTP"}),
})


# ─────────────────────────── Conflict (갈등) 관계 — 스택 완전 불일치 ───────────────────────────
# 보고서 §3.3.c + §5.1: 주기능이 상대 PoLR 타격


_CONFLICT_PAIRS: frozenset[frozenset[str]] = frozenset({
    frozenset({"INTJ", "ESFJ"}),
    frozenset({"INTP", "ESFP"}),
    frozenset({"ENTJ", "ISFJ"}),
    frozenset({"ENTP", "ISFP"}),
    frozenset({"INFJ", "ESTJ"}),
    frozenset({"INFP", "ESTP"}),
    frozenset({"ENFJ", "ISTJ"}),
    frozenset({"ENFP", "ISTP"}),
})


# ─────────────────────────── Super-Ego (초자아) 관계 ───────────────────────────


_SUPER_EGO_PAIRS: frozenset[frozenset[str]] = frozenset({
    frozenset({"INTJ", "ESFP"}) ^ frozenset({"INTJ", "ESFP"}),  # placeholder (Dual로 처리됨)
    # 초자아 = 같은 클럽 다른 쿼드라 (인지기능 역방향)
    frozenset({"INTP", "ISFP"}),
    frozenset({"ENTP", "ESFP"}),
    frozenset({"INTJ", "ISFJ"}),
    frozenset({"ENTJ", "ESFJ"}),
    frozenset({"INFP", "ISTP"}),
    frozenset({"ENFP", "ESTP"}),
    frozenset({"INFJ", "ISTJ"}),
    frozenset({"ENFJ", "ESTJ"}),
}) - {frozenset()}


# ─────────────────────────── ADR-006/010/014 면책 ───────────────────────────


DEFAULT_DISCLAIMERS: list[str] = [
    "본 호환 점수는 융(Jung)의 인지기능 스택 이론 및 Socionics 관계론에 기반한 학술적 추정치이며 결혼·연애 결정 자문이 아닙니다.",
    "MBTI는 자기보고식 검사로 학계 재현성·구성 타당도 논쟁이 있습니다 (NEO-PI-R·Big5 대비).",
    "실제 대인 관계는 자아존중감·의사소통 노력·환경 변수 등 다중 요인의 영향을 받으며 본 지표를 맹신해서는 안 됩니다.",
]


# ─────────────────────────── 결과 dataclass ───────────────────────────


@dataclass(frozen=True)
class MBTICompatResult:
    """MBTI 16×16 호환 점수 결정론 결과 (ADR-024).

    Attributes:
        score: 1~9 정수.
        type_a: 입력 MBTI A.
        type_b: 입력 MBTI B.
        relationship_type: dual·activation·mirror·identity·super_ego·conflict·complementary·neutral.
        base: 기본 점수 (5).
        sn_bonus: S/N 동기화 가중치 (+2 또는 -1).
        socionics_bonus: Socionics 관계 가중치 (+4·+3·+2·+1·-2·-4).
        keirsey_bonus: NT-NF 결합 보너스 (0 또는 +1).
        disclaimers: ADR-006/010/014 강제 면책.
        school: 명시 학파.
    """

    score: int
    type_a: str
    type_b: str
    relationship_type: str
    base: int
    sn_bonus: int
    socionics_bonus: int
    keirsey_bonus: int
    disclaimers: list[str]
    school: str = "Jung 인지기능 + Socionics 관계론 + Keirsey 기질"

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "type_a": self.type_a,
            "type_b": self.type_b,
            "relationship_type": self.relationship_type,
            "components": {
                "base": self.base,
                "sn_bonus": self.sn_bonus,
                "socionics_bonus": self.socionics_bonus,
                "keirsey_bonus": self.keirsey_bonus,
            },
            "school": self.school,
            "disclaimers": self.disclaimers,
        }


# ─────────────────────────── 입력 정규화 ───────────────────────────


def _normalize(t: str) -> str:
    """MBTI 유형 정규화 (대문자·공백 제거)."""
    if not isinstance(t, str):
        return ""
    return t.upper().strip()


def is_valid_mbti(t: str) -> bool:
    """16 유형 중 하나인지 검증."""
    return _normalize(t) in _VALID_TYPES


# ─────────────────────────── 관계 분류 ───────────────────────────


def classify_relationship(a: str, b: str) -> str:
    """두 MBTI 유형 → Socionics 관계명 (보고서 §3.3 + §5.1).

    우선순위: identity → dual → activation → mirror → conflict → super_ego → neutral.
    """
    a, b = _normalize(a), _normalize(b)
    if a == b and a in _VALID_TYPES:
        return "identity"

    pair = frozenset({a, b})
    if pair in _DUAL_PAIRS:
        return "dual"
    if pair in _ACTIVATION_PAIRS:
        return "activation"
    if pair in _MIRROR_PAIRS:
        return "mirror"
    if pair in _CONFLICT_PAIRS:
        return "conflict"
    if pair in _SUPER_EGO_PAIRS:
        return "super_ego"
    return "neutral"


# ─────────────────────────── 4단계 점수 알고리즘 (보고서 §5.1) ───────────────────────────


def _compute_sn_bonus(a: str, b: str) -> int:
    """1단계 — S/N 축 동기화 가중치 (윤호균·이선희 2000).

    공유 시 +2, 다르면 -1.
    """
    sn_a = "S" if "S" in a else ("N" if "N" in a else None)
    sn_b = "S" if "S" in b else ("N" if "N" in b else None)
    if sn_a is None or sn_b is None:
        return 0
    return 2 if sn_a == sn_b else -1


def _compute_socionics_bonus(relationship: str) -> int:
    """2단계 — Socionics 관계 가중치."""
    mapping = {
        "dual": 4,
        "activation": 3,
        "mirror": 2,
        "identity": 1,
        "conflict": -4,
        "super_ego": -2,
        "neutral": 0,
    }
    return mapping.get(relationship, 0)


def _compute_keirsey_bonus(a: str, b: str) -> int:
    """3단계 — Keirsey NT-NF 결합 상보성 보너스 (보고서 §5.1 3단계).

    N 공유 + T/F 역전 + J/P 역전 → +1.
    """
    if "N" not in a or "N" not in b:
        return 0

    # T/F 역전
    tf_a = "T" if "T" in a else "F"
    tf_b = "T" if "T" in b else "F"
    if tf_a == tf_b:
        return 0

    # J/P 역전
    jp_a = "J" if a.endswith("J") else "P"
    jp_b = "J" if b.endswith("J") else "P"
    if jp_a == jp_b:
        return 0

    return 1


def compute_mbti_compat(a: str, b: str) -> MBTICompatResult:
    """MBTI 두 유형 → 호환 점수 1~9 (결정론 4단계).

    Args:
        a: 첫 MBTI 유형.
        b: 둘째 MBTI 유형.

    Returns:
        MBTICompatResult — 점수 + 관계명 + 가중치 분해 + 면책.

    Raises:
        ValueError: 잘못된 MBTI 유형 입력 시.

    설계 (보고서 §5.1):
        · 1단계 기본 5점 + S/N 동기화 (±2)
        · 2단계 Socionics 관계 (+4·+3·+2·+1·-2·-4)
        · 3단계 Keirsey NT-NF 보너스 (+1)
        · 4단계 정규화 [1, 9]
    """
    a_norm = _normalize(a)
    b_norm = _normalize(b)

    if a_norm not in _VALID_TYPES or b_norm not in _VALID_TYPES:
        raise ValueError(f"잘못된 MBTI 유형: a={a!r}, b={b!r}")

    relationship = classify_relationship(a_norm, b_norm)

    base = 5
    sn_bonus = _compute_sn_bonus(a_norm, b_norm)
    soc_bonus = _compute_socionics_bonus(relationship)
    keirsey_bonus = _compute_keirsey_bonus(a_norm, b_norm)

    raw = base + sn_bonus + soc_bonus + keirsey_bonus
    # 4단계: 정규화 [1, 9]
    score = max(1, min(9, raw))

    return MBTICompatResult(
        score=score,
        type_a=a_norm,
        type_b=b_norm,
        relationship_type=relationship,
        base=base,
        sn_bonus=sn_bonus,
        socionics_bonus=soc_bonus,
        keirsey_bonus=keirsey_bonus,
        disclaimers=list(DEFAULT_DISCLAIMERS),
    )


# ─────────────────────────── 256 매트릭스 사전 연산 (선택, O(1) 룩업) ───────────────────────────


def precompute_matrix() -> dict[tuple[str, str], int]:
    """16×16 = 256 매트릭스 사전 연산 (대칭 행렬).

    부팅 시 1회 호출 후 메모리 룩업으로 O(1) 조회 가능.
    """
    matrix: dict[tuple[str, str], int] = {}
    types = sorted(_VALID_TYPES)
    for a in types:
        for b in types:
            result = compute_mbti_compat(a, b)
            matrix[(a, b)] = result.score
    return matrix


__all__ = [
    "DEFAULT_DISCLAIMERS",
    "MBTICompatResult",
    "is_valid_mbti",
    "classify_relationship",
    "compute_mbti_compat",
    "precompute_matrix",
]
