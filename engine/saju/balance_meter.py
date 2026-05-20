"""ADR-093 — 궁합 LLM 응답 양면 해석 균형도 객관 측정 모듈.

긍정 어휘 카운트 + 부정 균형 어휘 카운트 → 균형도 % 산출.
ADR-092 (긍정·부정 1:1 지시) 라이브 효과 객관 측정.

원칙 (ADR-002·006·010 정합):
  · 긍정/부정 어휘 풀은 명리학 통설 + 일반 한국어
  · 단일 학파 단정 X — 어휘 풀은 메타 분류 (강점/약점/조화/갈등)
  · 본 측정은 LLM 응답 품질 메트릭 — 사용자 운명 단정 X
"""

from __future__ import annotations

from dataclasses import dataclass

# 긍정 표현 풀 (강점·조화·보완·활력)
_POSITIVE_VOCAB: tuple[str, ...] = (
    "수 있",        # 가능성 조건절
    "조화",
    "보완",
    "강점",
    "긍정",
    "활력",
    "성장",
    "기회",
    "발전",
    "안정",
    "신뢰",
    "지지",
    "긍정적",
    "도움",
    "원활",
)

# 부정 균형 표현 풀 (갈등·약점·주의·신중)
_NEGATIVE_VOCAB: tuple[str, ...] = (
    "갈등",
    "약점",
    "어려움",
    "주의",
    "신중",
    "마찰",
    "충돌",
    "과제",
    "긴장",
    "부담",
    "압박",
    "조심",
    "오해",
    "장애",
    "단점",
)


@dataclass(frozen=True)
class BalanceResult:
    """균형도 측정 결과.

    Attributes:
        positive_count: 긍정 어휘 출현 횟수
        negative_count: 부정 균형 어휘 출현 횟수
        balance_pct: min(pos,neg) / max(pos,neg) * 100 — 0% (극단) ~ 100% (완전 균형)
        total_signal: pos + neg
        verdict: 본 시스템 ADR-092 권장 임계값
    """
    positive_count: int
    negative_count: int
    balance_pct: float
    total_signal: int
    verdict: str


# ADR-093 임계값 — 단일 호출 기준
_MIN_BALANCE_PCT_PASS = 40.0   # 40% 미만 → 암묵적 단정 위험
_MIN_BALANCE_PCT_GOOD = 60.0   # 60% 이상 → ADR-092 양호


def measure_balance(text: str) -> BalanceResult:
    """LLM 응답 텍스트의 양면 해석 균형도 측정.

    Args:
        text: LLM 응답 본문 (한국어)

    Returns:
        BalanceResult — 긍정/부정 카운트 + 균형도 + verdict.
    """
    pos = sum(text.count(w) for w in _POSITIVE_VOCAB)
    neg = sum(text.count(w) for w in _NEGATIVE_VOCAB)
    total = pos + neg
    balance = min(pos, neg) / max(pos, neg, 1) * 100 if total > 0 else 0.0

    if balance >= _MIN_BALANCE_PCT_GOOD:
        verdict = "GOOD"
    elif balance >= _MIN_BALANCE_PCT_PASS:
        verdict = "PASS"
    elif total == 0:
        verdict = "EMPTY"
    else:
        verdict = "WARN_IMPLICIT_BIAS"

    return BalanceResult(
        positive_count=pos,
        negative_count=neg,
        balance_pct=round(balance, 1),
        total_signal=total,
        verdict=verdict,
    )


def measure_batch(texts: list[str]) -> dict:
    """다회 응답 평균 균형도.

    Args:
        texts: 라이브 응답 본문 리스트 (N회 호출)

    Returns:
        {
            "count": N,
            "avg_balance_pct": float,
            "min_balance_pct": float,
            "max_balance_pct": float,
            "samples": list[BalanceResult],
            "verdict": "GOOD" | "PASS" | "WARN_IMPLICIT_BIAS" | "EMPTY"
        }
    """
    if not texts:
        return {
            "count": 0,
            "avg_balance_pct": 0.0,
            "min_balance_pct": 0.0,
            "max_balance_pct": 0.0,
            "samples": [],
            "verdict": "EMPTY",
        }

    samples = [measure_balance(t) for t in texts]
    balances = [s.balance_pct for s in samples]
    avg = sum(balances) / len(balances)

    if avg >= _MIN_BALANCE_PCT_GOOD:
        verdict = "GOOD"
    elif avg >= _MIN_BALANCE_PCT_PASS:
        verdict = "PASS"
    else:
        verdict = "WARN_IMPLICIT_BIAS"

    return {
        "count": len(texts),
        "avg_balance_pct": round(avg, 1),
        "min_balance_pct": round(min(balances), 1),
        "max_balance_pct": round(max(balances), 1),
        "samples": samples,
        "verdict": verdict,
    }


__all__ = [
    "BalanceResult",
    "measure_balance",
    "measure_batch",
]
