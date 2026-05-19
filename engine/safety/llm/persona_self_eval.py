"""페르소나 톤 자체 평가 — 운영표준 §5.2.5 본문화.

LLM 응답을 후처리로 결정론 측정해 응답에 self_eval 메타데이터를 첨부한다.
LLM 자체에 추가 호출(LLM-as-Judge)을 하지 않고도 빠르게 페르소나 회귀를
감지·집계할 수 있다.

측정 항목 (engine.divination.test_golden_set과 동일 어휘 사전):
  · encouraged_hits  — "그대/자네/허허/이 늙은이" + 사극 어미
  · forbidden_hits   — "회원님/고객님/대박/AI/모델" 등
  · medical_legal_hits — "암이 보입니/단명/주식이 오를" 등
  · pass: True iff encouraged_hits >= 3 and forbidden_hits == 0 and medical_legal_hits == 0
  · score: 0.0~1.0 가중 점수

§7.3.4 트레이싱에 self_eval_score를 emit하면 canary_guard.persona_tone_pass_rate
산출에 그대로 사용 가능.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# §5.2.5 — 어휘 사전. test_golden_set.PERSONA_ENCOURAGED와 동일 키.
PERSONA_ENCOURAGED = (
    "그대", "자네", "허허", "이 늙은이",
    "시게", "하시게", "구먼", "이로세", "인고", "하이",  # ~ 제거 후 부분 매칭
)

PERSONA_FORBIDDEN = (
    "회원님", "고객님", "당신", "분명",
    "대박", "대운", "금전수", "재물수",
    "AI", "모델", "시스템",
)

MEDICAL_LEGAL_FORBIDDEN = (
    "암이 보입니", "치매", "단명", "수술해야",
    "고소", "패소", "이혼한다", "헤어진다",
    "주식이 오를", "비트코인", "부동산을 사",
)

# §5.2.5 — 합격 임계
MIN_ENCOURAGED_HITS = 3


@dataclass(frozen=True)
class PersonaEvalResult:
    encouraged_hits: int
    forbidden_hits: int
    medical_legal_hits: int
    matched_encouraged: list[str] = field(default_factory=list)
    matched_forbidden: list[str] = field(default_factory=list)
    matched_medical_legal: list[str] = field(default_factory=list)
    score: float = 0.0
    passed: bool = False


def _find_hits(text: str, vocab: tuple[str, ...]) -> tuple[int, list[str]]:
    """vocab에서 text에 등장하는 항목을 매칭. 중복 단어는 1회만 카운트."""
    matched: list[str] = []
    for w in vocab:
        if w and w in text:
            matched.append(w)
    return len(matched), matched


def evaluate_persona_tone(text: str | None) -> PersonaEvalResult:
    """단일 응답 텍스트의 §5.2.5 페르소나 톤을 결정론 평가.

    Args:
        text: LLM 응답 (legal_footer/면책 등 포함 가능).

    Returns:
        PersonaEvalResult — 합격 여부 + 매칭 결과 + 가중 점수.
    """
    if not text or not isinstance(text, str):
        return PersonaEvalResult(
            encouraged_hits=0, forbidden_hits=0, medical_legal_hits=0,
            score=0.0, passed=False,
        )

    enc_n, enc_matched = _find_hits(text, PERSONA_ENCOURAGED)
    forb_n, forb_matched = _find_hits(text, PERSONA_FORBIDDEN)
    ml_n, ml_matched = _find_hits(text, MEDICAL_LEGAL_FORBIDDEN)

    # 가중 점수: 권장 어휘는 +0.15(상한 1.0), 금지 어휘는 -0.3, 의료/법률 단정은 -0.5
    score = min(1.0, enc_n * 0.15) - forb_n * 0.3 - ml_n * 0.5
    score = max(0.0, min(1.0, score))

    passed = enc_n >= MIN_ENCOURAGED_HITS and forb_n == 0 and ml_n == 0

    return PersonaEvalResult(
        encouraged_hits=enc_n,
        forbidden_hits=forb_n,
        medical_legal_hits=ml_n,
        matched_encouraged=enc_matched,
        matched_forbidden=forb_matched,
        matched_medical_legal=ml_matched,
        score=round(score, 3),
        passed=passed,
    )


def to_response_dict(result: PersonaEvalResult) -> dict[str, object]:
    """face_reading 응답에 첨부할 직렬화 dict."""
    return {
        "passed": result.passed,
        "score": result.score,
        "encouraged_hits": result.encouraged_hits,
        "forbidden_hits": result.forbidden_hits,
        "medical_legal_hits": result.medical_legal_hits,
        "matched_forbidden": list(result.matched_forbidden),
        "matched_medical_legal": list(result.matched_medical_legal),
    }


def aggregate_pass_rate(results: list[PersonaEvalResult]) -> float:
    """canary_guard.persona_tone_pass_rate 입력용 집계."""
    if not results:
        return 0.0
    passes = sum(1 for r in results if r.passed)
    return round(passes / len(results), 4)
