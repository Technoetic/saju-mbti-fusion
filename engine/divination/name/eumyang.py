"""음양(陰陽) 조화 — 보고서 §3 본문화.

획수의 홀짝으로 음양 구분:
  · 홀수 획 = 양(陽)
  · 짝수 획 = 음(陰)

성+이름 세 글자의 음양 배열이 '음-음-음' 또는 '양-양-양'으로 극단 편중되지
않고, '음-양-양' / '양-음-양' / '음-음-양' 등 조화롭게 배열되도록 검증.

본 모듈은 결정론 필터.
"""

from __future__ import annotations

from dataclasses import dataclass


YANG = "양"   # 陽 — 홀수 획
EUM = "음"    # 陰 — 짝수 획

# 음양 등급
GRADE_GOOD = "good"       # 조화 (혼합)
GRADE_NEUTRAL = "neutral" # 약간 편중
GRADE_BAD = "bad"         # 극단 편중 (전부 동일)


@dataclass(frozen=True)
class EumYangReport:
    """음양 배열 평가."""
    pattern: str               # "양-음-양" 같은 사람 읽기 가능 라벨
    sequence: list[str]        # [YANG, EUM, YANG] 같은 원시 시퀀스
    yang_count: int
    eum_count: int
    grade: str                 # good/neutral/bad
    reason: str = ""           # 평가 사유


def stroke_to_eumyang(strokes: int) -> str:
    """단일 획수 → 음/양."""
    return YANG if strokes % 2 == 1 else EUM


def evaluate_eumyang(strokes: list[int]) -> EumYangReport:
    """획수 시퀀스의 음양 조화 평가.

    Args:
        strokes: 성+이름 글자별 원획수 리스트 (보통 3개, 외자/복성은 가변).

    Returns:
        EumYangReport — 패턴 + 등급(good/neutral/bad).

    평가 기준:
      · 3자 기준
        - 양-양-양 또는 음-음-음 → BAD (극단 편중)
        - 그 외 모든 혼합 → GOOD
      · 2자/4자도 동일 규칙 적용
    """
    if not strokes:
        return EumYangReport(
            pattern="(빈 시퀀스)",
            sequence=[], yang_count=0, eum_count=0,
            grade=GRADE_NEUTRAL,
            reason="획수 정보 없음",
        )

    sequence = [stroke_to_eumyang(s) for s in strokes]
    yang_count = sequence.count(YANG)
    eum_count = sequence.count(EUM)
    total = len(sequence)
    pattern = "-".join(sequence)

    # 극단 편중 (전부 동일)
    if yang_count == total:
        grade = GRADE_BAD
        reason = f"양(陽)으로만 편중 — 음양 조화 결여 (모두 홀수 획)"
    elif eum_count == total:
        grade = GRADE_BAD
        reason = f"음(陰)으로만 편중 — 음양 조화 결여 (모두 짝수 획)"
    else:
        # 1자만 다른 경우 (예: 양-양-음, 음-양-양) — 약한 조화로 NEUTRAL
        # 단, 3자에서 1:2 또는 2:1은 일반적으로 양호함 → GOOD으로 처리
        diff = abs(yang_count - eum_count)
        if total <= 2 or diff <= total // 2 + 1:
            grade = GRADE_GOOD
            reason = "음양 조화 양호"
        else:
            grade = GRADE_NEUTRAL
            reason = "음양이 한쪽으로 약간 기울어짐"

    return EumYangReport(
        pattern=pattern,
        sequence=sequence,
        yang_count=yang_count,
        eum_count=eum_count,
        grade=grade,
        reason=reason,
    )


def is_balanced(strokes: list[int]) -> bool:
    """음양 조화 양호 여부 (BAD가 아니면 True)."""
    return evaluate_eumyang(strokes).grade != GRADE_BAD


def report_to_dict(report: EumYangReport) -> dict:
    return {
        "pattern": report.pattern,
        "sequence": list(report.sequence),
        "yang_count": report.yang_count,
        "eum_count": report.eum_count,
        "grade": report.grade,
        "reason": report.reason,
    }
