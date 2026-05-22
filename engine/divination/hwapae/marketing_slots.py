"""ADR-154 — hwapae 마케팅 메시지 채택 슬롯.

/domain-priorities 잔여 #3 부분 해소 — 사용자 사업 결단 (어느 메시지 채택 +
가격·결제 정책) 영역의 본 AI 단독 가능 코드 영속.

본 모듈은 ADR-150 결단 지원 자료의 5 메시지 + 본 AI 추가 변형을 코드 슬롯으로
정합. 사용자 결단 시 `ACTIVE_MARKETING_KEY`만 변경하면 UI에 즉시 반영.

원칙 (ADR-006·002 정합):
  · 단정 어휘 0건 (반드시·확실히·100%·절대 회피)
  · 일제강점기 영향에서 독립한 한국 정통 화투 강조 (학파 단정 X)
  · 사주·운명 단정 X — 점복 보조 도구로만 (참고용)
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketingMessage:
    """단일 마케팅 메시지 후보."""
    key: str           # 'ko_independence' 등
    headline: str      # 1줄 헤드라인 (~40자)
    body: str          # 본문 (~120자)
    tone: str          # 'ko_pride' | 'academic' | 'tradition' | 'casual' | 'modern'
    target_demo: str   # '20대' | '30대' | '40대+' | '전 연령'
    adr_compliant: bool = True


# ─────────────────────────── 5 채택 후보 (사용자 결단 영역) ───────────────────────────

MARKETING_CANDIDATES: tuple[MarketingMessage, ...] = (
    MarketingMessage(
        key="ko_independence",
        headline="일본 화투 아닌 한국 정통 화투의 결",
        body=(
            "권현주 박사 (2017 KCI 등재) 학술 인용 기반. 일제강점기 영향 이전의 "
            "한국 정통 48패 흐름 톤만 풀이 — 점복 보조 도구로 참고용."
        ),
        tone="ko_pride",
        target_demo="30대+",
    ),
    MarketingMessage(
        key="academic_kci",
        headline="KCI 학술 인용 5건의 결정론 풀이",
        body=(
            "권현주 (2013·2017), 서강대 (2022) 등 KCI 등재 학술 출처 기반. "
            "단정·예언 X — 결정론 카드 분류 + 흐름 톤만."
        ),
        tone="academic",
        target_demo="40대+",
    ),
    MarketingMessage(
        key="tradition_warm",
        headline="할머니의 화투, 학술 정합 풀이로",
        body=(
            "어릴 적 명절 화투의 결을 학술 정합 결정론으로 — 1·2월 솔·매조부터 "
            "11·12월 오동·비까지 12 월별 결 풀이."
        ),
        tone="tradition",
        target_demo="40대+",
    ),
    MarketingMessage(
        key="casual_fun",
        headline="48패 뽑고 오늘의 결 보기",
        body=(
            "한 장 뽑아 오늘의 흐름 톤만 — 운명 단정 X, 가벼운 결의 결만. "
            "참고용 (의료·법률·금융 결단 단독 근거 X)."
        ),
        tone="casual",
        target_demo="20대",
    ),
    MarketingMessage(
        key="modern_minimal",
        headline="화투 × AI, 결정론 + 흐름 톤",
        body=(
            "결정론 48패 분류 → AI 자연어 풀이. 단정 어휘 차단 + 면책 자동 "
            "(ADR-006 정합). 참고용 — 의료·법률·금융 결단 단독 근거 X."
        ),
        tone="modern",
        target_demo="20대",
    ),
)


# ─────────────────────────── 활성 메시지 (사용자 결단 후 변경) ───────────────────────────

# 디폴트는 ADR-006·010 정합 강도가 가장 높은 'academic_kci'.
# 사용자 사업 결단 (어느 톤이 전환율 높을지 A/B 테스트) 후 변경 가능.
ACTIVE_MARKETING_KEY: str = "academic_kci"


def get_active_marketing_message() -> MarketingMessage:
    """ADR-154 — UI 마운트 시 호출. 사용자 결단 시 ACTIVE_MARKETING_KEY 변경."""
    for m in MARKETING_CANDIDATES:
        if m.key == ACTIVE_MARKETING_KEY:
            return m
    return MARKETING_CANDIDATES[0]


def list_marketing_candidates() -> tuple[MarketingMessage, ...]:
    """A/B 테스트용 — 5 후보 풀 조회."""
    return MARKETING_CANDIDATES


def validate_adr_006_compliance(msg: MarketingMessage) -> tuple[bool, list[str]]:
    """ADR-006 단정 어휘 차단 검증 — 사용자 신규 메시지 추가 시 호출.

    Returns:
        (정합 여부, 위반 어휘 목록)
    """
    forbidden = ["반드시", "확실히", "100%", "절대", "분명히", "당연히"]
    text = msg.headline + " " + msg.body
    violations = [w for w in forbidden if w in text]
    return (len(violations) == 0, violations)


__all__ = [
    "MarketingMessage", "MARKETING_CANDIDATES", "ACTIVE_MARKETING_KEY",
    "get_active_marketing_message", "list_marketing_candidates",
    "validate_adr_006_compliance",
]
