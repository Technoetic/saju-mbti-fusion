"""B1 환각 억제 RAG 게이트 — 모든 LLM 출력 전 사실 검증.

문서: 모든 해석 출력 전 심리학 코퍼스 사실 검증, 환각률 ≤3%.

전략:
  - LLM이 합성한 본문에서 도메인 이름·키워드를 추출
  - 사실 블록(facts)에 등장한 키워드와 매칭률 계산
  - 매칭률이 임계 미만이면 환각 의심 → 재시도 권고 플래그

본 게이트는 결정론적 검증만 수행 (LLM 호출 0회). dream.py의 critic 루프와 협력.
"""

from __future__ import annotations
from typing import Any
import re


RAG_GATE_LABEL = (
    "B1 환각 억제 RAG 게이트 — 본문 vs 사실 블록 매칭률로 환각 의심 탐지."
)


# 모든 도메인 라벨 (LLM이 인용해야 할 정규 표현들)
DOMAIN_LABELS = [
    "아르테미도로스", "오행", "사주", "한국 민간", "민속",
    "융", "원형", "그림자", "아니마", "아니무스", "자기", "페르소나",
    "프로이트", "꿈-작업", "응축", "전치",
    "홉슨", "활성-합성", "기괴성",
    "TST", "위협 시뮬레이션", "레본수오",
    "돔호프", "연속성", "DMN",
    "HvDC", "Hall-Van de Castle", "DreamBank",
    "파자", "주공해몽", "이븐 시린", "Ruyā", "Hulm",
    "황제내경", "동의보감", "음사발몽", "혼백",
    "Solms", "SEEKING", "Cartwright", "정서 조절",
    "Stickgold", "기억 통합", "자각몽", "lucid",
    "SST", "사회 시뮬레이션",
    "Hoel", "과적합", "Friston", "예측", "자유에너지",
    "Lakoff", "은유", "Griffin", "EFT",
    "Zhang", "자기조직화", "카타르시스",
    "주역", "괘", "팔괘",
    "Schredl", "묘에", "Dormio", "Ullman", "Hill",
]

# 환각 의심 패턴 (LLM이 흔히 만드는 가짜 인용)
HALLUCINATION_PATTERNS = [
    r"논문에 따르면",
    r"\d+%의 확률로",
    r"\d+%의 가능성으로",
    r"의학적으로 입증",
    r"과학적으로 증명",
    r"진단 결과",
    r"\d{4}년 .* 연구에서",  # 가짜 연도+연구
]

# 단정 표현 (가드)
ASSERTION_PATTERNS = [
    r"~될 것입니다",
    r"~할 것이다",
    r"분명히 ",
    r"확실히 ",
    r"틀림없이 ",
    r"~병이 있",
    r"~증상입니다",
]


def evaluate_rag_compliance(
    generated_text: str,
    facts_block: str,
    *,
    min_domain_citations: int = 3,
    max_hallucination_hits: int = 0,
) -> dict[str, Any]:
    """LLM 본문이 사실 블록에 기반했는지 결정론 검증.

    Returns:
        {
            'pass': bool,
            'domain_citations': int,
            'hallucination_hits': list[str],
            'assertion_hits': list[str],
            'fact_overlap_ratio': float,
            'recommendation': str
        }
    """
    text = generated_text or ""
    facts = facts_block or ""

    # 1. 도메인 라벨 인용 카운트
    cited = [label for label in DOMAIN_LABELS if label in text]

    # 2. 환각 패턴 검출
    hallucinations = []
    for pat in HALLUCINATION_PATTERNS:
        matches = re.findall(pat, text)
        hallucinations.extend(matches)

    # 3. 단정 표현 검출
    assertions = []
    for pat in ASSERTION_PATTERNS:
        matches = re.findall(pat, text)
        assertions.extend(matches)

    # 4. 사실 블록 키워드 매칭률
    # 사실 블록에서 한글 2자 이상 어절 추출
    fact_tokens = set(w for w in re.findall(r"[가-힣]{2,}", facts))
    text_tokens = set(w for w in re.findall(r"[가-힣]{2,}", text))
    if len(fact_tokens) >= 5:
        overlap = len(fact_tokens & text_tokens) / len(fact_tokens)
    else:
        # 사실 블록이 너무 짧으면 overlap 검증 생략 (citation 만으로 판정)
        overlap = 1.0

    # 5. 종합 판정
    issues: list[str] = []
    if len(cited) < min_domain_citations:
        issues.append(f"도메인 인용 부족 ({len(cited)}/{min_domain_citations})")
    if len(hallucinations) > max_hallucination_hits:
        issues.append(f"환각 패턴 감지 ({len(hallucinations)}건)")
    if len(assertions) > 0:
        issues.append(f"단정 표현 감지 ({len(assertions)}건)")
    if overlap < 0.1 and len(fact_tokens) >= 5:
        issues.append(f"사실 블록 매칭률 낮음 ({overlap:.0%})")

    passed = len(issues) == 0
    recommendation = (
        "재시도 권고 — critic 루프 재실행."
        if not passed
        else "통과 — 사용자에게 안전하게 전달 가능."
    )

    return {
        "agent": "B1",
        "pass": passed,
        "domain_citations": len(cited),
        "cited_labels": cited[:10],
        "hallucination_hits": list(set(hallucinations))[:5],
        "assertion_hits": list(set(assertions))[:5],
        "fact_overlap_ratio": round(overlap, 3),
        "issues": issues,
        "recommendation": recommendation,
        "principle": (
            "환각 억제 — LLM 본문이 (1) 도메인 라벨을 충분히 인용, "
            "(2) 환각 패턴 없음, (3) 단정 표현 없음, (4) 사실 블록과 매칭률이 일정 수준 이상."
        ),
    }


__all__ = [
    "RAG_GATE_LABEL",
    "DOMAIN_LABELS",
    "evaluate_rag_compliance",
]
