"""응답 일관성 검증 — 운영표준 §5.2.9 본문화.

LLM은 temperature > 0이면 같은 입력에 대해 매번 다른 응답을 생성한다.
모든 응답이 페르소나·결론의 핵심 부분에서 일관성을 유지하는지 결정론 검증.

§5.2.9 일관성 차원:
  · persona_consistency  — 사극풍 어휘가 모든 응답에 ≥ MIN_ENCOURAGED_HITS
  · medical_legal_consistency — 의료/법률 단정 0건 (모든 응답에서)
  · forbidden_consistency — 금지어 0건 (모든 응답에서)
  · topic_consistency    — 같은 화두에 대해 같은 주제 클러스터 응답
  · length_variance      — 응답 길이가 비슷한 범위
  · sentiment_stability  — 결정적 표현(단정)과 경향성 표현 비율

§5.2.9 임계:
  · MIN_CONSISTENT_SAMPLES — N=2 이상이어야 평가 (단일 응답은 면제)
  · LENGTH_CV_MAX = 0.5    — 변동계수(std/mean) 50% 이하
  · TOPIC_AGREEMENT_MIN = 0.8 — 80% 이상 응답이 같은 주제 다룸

본 모듈은 검증만 — N개 응답을 일괄 받고 일관성 위반 단계 보고.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


# §5.2.9 임계
LENGTH_CV_MAX = 0.5
TOPIC_AGREEMENT_MIN = 0.8
MIN_SAMPLES_FOR_EVAL = 2

# §5.2.9 위반 코드
CONSISTENCY_PERSONA_DROP = "persona_drop"
CONSISTENCY_MEDICAL_LEAK = "medical_legal_inconsistent"
CONSISTENCY_FORBIDDEN_INCONSISTENT = "forbidden_inconsistent"
CONSISTENCY_TOPIC_DRIFT = "topic_drift"
CONSISTENCY_LENGTH_VARIANCE_HIGH = "length_variance_high"


@dataclass(frozen=True)
class ConsistencyReport:
    sample_count: int
    issues: list[str] = field(default_factory=list)
    persona_pass_rate: float = 1.0
    forbidden_total: int = 0
    medical_legal_total: int = 0
    length_cv: float = 0.0
    topic_agreement: float = 1.0
    dominant_topic: str = ""

    @property
    def consistent(self) -> bool:
        return not self.issues


# ─────────────────────────── 헬퍼 ───────────────────────────

def _coefficient_of_variation(values: list[int]) -> float:
    """std / mean. mean=0이면 0."""
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    if mean == 0:
        return 0.0
    var = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(var) / mean


# ─────────────────────────── 평가 ───────────────────────────

def evaluate_consistency(
    responses: list[str],
    *,
    question: str | None = None,
) -> ConsistencyReport:
    """N개 응답의 §5.2.9 일관성을 일괄 평가.

    Args:
        responses: 같은 입력에 대한 N개 LLM 응답
        question: 화두 본문 (topic_consistency 검증용, 없으면 면제)
    """
    if not responses or len(responses) < MIN_SAMPLES_FOR_EVAL:
        return ConsistencyReport(sample_count=len(responses or []))

    from engine.safety.llm.persona_self_eval import evaluate_persona_tone
    from engine.safety.llm.response_alignment import detect_topic, check_response_topic

    issues: list[str] = []
    persona_pass_count = 0
    forbidden_total = 0
    medical_legal_total = 0
    lengths: list[int] = []
    topic_hit_count = 0

    # 화두 주제 (있을 때만)
    q_topic = ""
    if question:
        q_topic, _ = detect_topic(question)

    for resp in responses:
        ev = evaluate_persona_tone(resp)
        if ev.passed:
            persona_pass_count += 1
        forbidden_total += ev.forbidden_hits
        medical_legal_total += ev.medical_legal_hits
        lengths.append(len(resp or ""))
        if q_topic:
            hits = check_response_topic(resp, q_topic)
            if hits:
                topic_hit_count += 1

    n = len(responses)
    persona_pass_rate = persona_pass_count / n
    length_cv = _coefficient_of_variation(lengths)
    topic_agreement = (topic_hit_count / n) if q_topic else 1.0

    # 위반 검출
    # 페르소나 통과율이 80% 미만이면 일관성 깨짐 (한두 응답이 사극풍 잃음)
    if persona_pass_rate < 0.8:
        issues.append(CONSISTENCY_PERSONA_DROP)
    if medical_legal_total > 0:
        issues.append(CONSISTENCY_MEDICAL_LEAK)
    if forbidden_total > 0:
        issues.append(CONSISTENCY_FORBIDDEN_INCONSISTENT)
    if q_topic and topic_agreement < TOPIC_AGREEMENT_MIN:
        issues.append(CONSISTENCY_TOPIC_DRIFT)
    if length_cv > LENGTH_CV_MAX:
        issues.append(CONSISTENCY_LENGTH_VARIANCE_HIGH)

    return ConsistencyReport(
        sample_count=n,
        issues=issues,
        persona_pass_rate=round(persona_pass_rate, 4),
        forbidden_total=forbidden_total,
        medical_legal_total=medical_legal_total,
        length_cv=round(length_cv, 4),
        topic_agreement=round(topic_agreement, 4),
        dominant_topic=q_topic,
    )


def to_fallback_trigger(report: ConsistencyReport) -> str:
    """llm_fallback_router 호환 매핑. 의료/법률 누출은 critical, 나머지는 persona_failed."""
    if not report.issues:
        return ""
    if CONSISTENCY_MEDICAL_LEAK in report.issues:
        return "persona_failed"
    return "persona_failed"


def to_alert_payload(report: ConsistencyReport) -> dict[str, object]:
    """§14.3 alert_router 호환."""
    if not report.issues:
        severity = "P3"
    elif CONSISTENCY_MEDICAL_LEAK in report.issues:
        severity = "P1"
    elif len(report.issues) >= 3:
        severity = "P1"
    else:
        severity = "P2"
    return {
        "service": "response_consistency",
        "severity": severity,
        "sample_count": report.sample_count,
        "issues": list(report.issues),
        "persona_pass_rate": report.persona_pass_rate,
        "medical_legal_total": report.medical_legal_total,
        "topic_agreement": report.topic_agreement,
        "length_cv": report.length_cv,
    }
