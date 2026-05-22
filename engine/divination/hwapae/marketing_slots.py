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


# ─────────────────────────── ADR-155 — A/B 테스트 측정 인프라 ───────────────────────────

# /domain-priorities 잔여 #3 추가 부분 해소 — 사용자 사업 결단 (어느 메시지 채택)을
# 데이터 기반으로 가능하게 하는 측정 인프라. 본 AI 단독 코드 영속.

import hashlib


@dataclass
class ABTestExposure:
    """단일 노출 이벤트 (사용자 anon_id × variant_key × timestamp)."""
    anon_id: str           # localStorage 익명 ID
    variant_key: str       # 'academic_kci' 등
    timestamp_ms: int      # UTC ms
    converted: bool = False  # 전환 여부 (구매·CTA 클릭)


# 인메모리 누적 (운영 시 SQLite·Redis 영속 별건).
_AB_EXPOSURES: list[ABTestExposure] = []


def assign_variant(anon_id: str, candidate_keys: tuple[str, ...] | None = None) -> str:
    """ADR-155 — 결정론 변형 할당 (anon_id 해시 → variant).

    동일 사용자는 항상 동일 variant 노출 (UX 일관성).

    Args:
        anon_id: localStorage 익명 ID
        candidate_keys: 후보 키 풀 (None = MARKETING_CANDIDATES 전체)

    Returns:
        할당된 variant_key
    """
    keys = candidate_keys or tuple(m.key for m in MARKETING_CANDIDATES)
    if not keys:
        return ACTIVE_MARKETING_KEY
    digest = hashlib.sha256(anon_id.encode("utf-8")).digest()
    idx = int.from_bytes(digest[:4], "big") % len(keys)
    return keys[idx]


def record_exposure(anon_id: str, variant_key: str, timestamp_ms: int) -> None:
    """노출 이벤트 기록 (인메모리). 운영 시 영속 DB로 별건."""
    _AB_EXPOSURES.append(ABTestExposure(
        anon_id=anon_id, variant_key=variant_key, timestamp_ms=timestamp_ms,
    ))


def record_conversion(anon_id: str, variant_key: str) -> bool:
    """전환 이벤트 (구매·CTA 클릭). 가장 최근 노출에 converted=True."""
    for exposure in reversed(_AB_EXPOSURES):
        if exposure.anon_id == anon_id and exposure.variant_key == variant_key and not exposure.converted:
            exposure.converted = True
            return True
    return False


def compute_ab_test_stats() -> dict[str, dict[str, float]]:
    """ADR-155 — variant별 노출·전환·전환율 집계.

    Returns:
        {variant_key: {"exposures": N, "conversions": N, "conversion_rate": 0.0~1.0}}
    """
    stats: dict[str, dict[str, float]] = {}
    for e in _AB_EXPOSURES:
        s = stats.setdefault(e.variant_key, {"exposures": 0.0, "conversions": 0.0, "conversion_rate": 0.0})
        s["exposures"] += 1
        if e.converted:
            s["conversions"] += 1
    for s in stats.values():
        s["conversion_rate"] = round(s["conversions"] / s["exposures"], 4) if s["exposures"] else 0.0
    return stats


def reset_ab_test_state() -> None:
    """회귀·테스트용 — 인메모리 상태 초기화."""
    _AB_EXPOSURES.clear()


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
    # ADR-155 A/B 테스트 측정 인프라
    "ABTestExposure", "assign_variant", "record_exposure", "record_conversion",
    "compute_ab_test_stats", "reset_ab_test_state",
]
