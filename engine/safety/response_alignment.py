"""응답 정렬 검증 — 운영표준 §7.2.20 본문화.

LLM 응답이 입력 화두(question)에 실제로 답하는지 결정론 후처리 검증.
화두 주제가 응답에서 다뤄지지 않으면 misalignment → 폴백 트리거.

§7.2.20 검증 차원:
  · topic_overlap     — 화두 주제 키워드가 응답에 등장
  · question_acknowledged — 응답이 화두를 인지(언급)했는지
  · off_topic_drift   — 응답이 무관한 다른 주제로 흐른 정도

본 모듈은 보수적 — false positive 최소화. 화두가 짧거나 추상적이면
검증 면제(주제 미상).

§7.2.20 주제 사전 — 한국 관상학 주요 카테고리:
  · 결혼/배우자 — 처첩궁
  · 재물/사업 — 재백궁
  · 건강 — 질액궁
  · 직업/관운 — 관록궁
  · 자녀 — 자녀궁
  · 학업 — 상정
  · 부모/형제 — 부모궁·형제궁
"""

from __future__ import annotations

from dataclasses import dataclass, field


# §7.2.20 정렬 결과 코드
ALIGN_TOPIC_MISSING = "topic_missing"      # 화두 주제가 응답에 0건 등장
ALIGN_OFF_TOPIC = "off_topic"              # 무관한 주제가 응답을 지배
ALIGN_QUESTION_IGNORED = "question_ignored"  # 화두 키워드 자체 미언급


# §7.2.20 — 주제 클러스터. 각 카테고리는 화두 마커 + 응답 마커 한 쌍.
_TOPIC_CLUSTERS = {
    "marriage": {
        "question_markers": ("결혼", "배우자", "남편", "아내", "연애", "이성"),
        "response_markers": ("결혼", "배우자", "처첩궁", "남편", "아내",
                              "연애", "혼인", "어미", "눈꼬리"),
    },
    "wealth": {
        "question_markers": ("재물", "돈", "사업", "재산", "투자처"),
        "response_markers": ("재백궁", "재물", "코", "콧대", "콧방울",
                              "난대", "정위", "사업", "재산"),
    },
    "health": {
        "question_markers": ("건강", "병", "아픈", "수명", "장수"),
        "response_markers": ("질액궁", "산근", "건강", "수명", "기색",
                              "기운", "신(神)", "혈색"),
    },
    "career": {
        "question_markers": ("직업", "직장", "관운", "취업", "승진"),
        "response_markers": ("관록궁", "이마", "직업", "관운", "벼슬",
                              "사회", "자리"),
    },
    "children": {
        "question_markers": ("자녀", "아이", "임신", "출산"),
        "response_markers": ("자녀궁", "와잠", "눈 아래", "자녀", "아이",
                              "자손"),
    },
    "study": {
        "question_markers": ("학업", "공부", "시험", "진학"),
        "response_markers": ("상정", "이마", "학문", "지혜", "공부"),
    },
    "family": {
        "question_markers": ("부모", "형제", "자매", "가족"),
        "response_markers": ("부모궁", "형제궁", "일각", "월각",
                              "눈썹", "가족"),
    },
}


@dataclass(frozen=True)
class AlignmentResult:
    topic_detected: str = ""               # 감지된 화두 주제 (없으면 빈 문자열)
    response_has_topic: bool = True
    issues: list[str] = field(default_factory=list)
    question_markers_hit: list[str] = field(default_factory=list)
    response_markers_hit: list[str] = field(default_factory=list)

    @property
    def aligned(self) -> bool:
        return not self.issues


# ─────────────────────────── 헬퍼 ───────────────────────────

def detect_topic(question: str | None) -> tuple[str, list[str]]:
    """화두 본문에서 주제 추정. 반환: (topic_key, matched_markers).

    가장 많이 매칭되는 주제 우선. 매칭 0건이면 ("", []).
    """
    if not question or not isinstance(question, str):
        return "", []
    best_topic = ""
    best_hits: list[str] = []
    for topic, markers in _TOPIC_CLUSTERS.items():
        hits = [m for m in markers["question_markers"] if m in question]
        if len(hits) > len(best_hits):
            best_topic = topic
            best_hits = hits
    return best_topic, best_hits


def check_response_topic(text: str | None, topic: str) -> list[str]:
    """응답에서 해당 topic의 응답 마커가 등장하는지."""
    if not text or not topic:
        return []
    markers = _TOPIC_CLUSTERS.get(topic, {}).get("response_markers", ())
    return [m for m in markers if m in text]


# ─────────────────────────── 통합 진입점 ───────────────────────────

def evaluate_alignment(
    *,
    question: str | None,
    response_text: str | None,
) -> AlignmentResult:
    """§7.2.20 응답 정렬 평가.

    Returns:
        AlignmentResult — aligned (issues 비어있으면 True).
    """
    if not response_text or not isinstance(response_text, str):
        return AlignmentResult(issues=[ALIGN_QUESTION_IGNORED])

    topic, q_hits = detect_topic(question)

    # 화두에서 주제 미상 → 검증 면제 (false positive 회피)
    if not topic:
        return AlignmentResult(
            topic_detected="",
            response_has_topic=True,
            question_markers_hit=[],
        )

    r_hits = check_response_topic(response_text, topic)
    issues: list[str] = []
    if not r_hits:
        issues.append(ALIGN_TOPIC_MISSING)

    return AlignmentResult(
        topic_detected=topic,
        response_has_topic=bool(r_hits),
        issues=issues,
        question_markers_hit=q_hits,
        response_markers_hit=r_hits,
    )


def to_fallback_trigger(result: AlignmentResult) -> str:
    """llm_fallback_router 호환 — misalignment 시 persona_failed."""
    return "persona_failed" if result.issues else ""
