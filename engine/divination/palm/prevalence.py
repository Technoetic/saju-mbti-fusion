"""ADR-192 - 한국인 손금 형태 prevalence 통계 본문화.

학술 출처(KoreaMed Synapse, Anatomy & Cell Biology 2010·2022):
  - 한국인 normal 3선 손금: 84.4%
  - Simian crease (단일 통합 횡선): 11.2%
  - Suwon crease (수원 패턴): 0.5%
  - Sydney crease: 1.92% (Ethiopian 표본, 한국 별도 데이터 부재)
  - 기타 변종: 잔여

본 모듈은 사용자 손금 형태 분류 결과에 한국인 prevalence 비교 정보를
첨부 — "당신의 손금은 한국 성인의 약 11%에서 나타나는 simian 패턴" 같은
통계 베이스라인 묘사 가능.

ADR 정합:
  - ADR-010 사실성 분리: KoreaMed Synapse 검증 출처
  - ADR-006 자문 거절: 운명·길흉 매핑 X. 통계 분포만.
  - ADR-030 손금 결정론: 본 모듈은 score_palm과 독립
  - ADR-171 운명 단정 사전: 본 모듈도 sanitize 통과 필요
"""

from __future__ import annotations

from dataclasses import dataclass


# 한국 성인 손금 형태 prevalence (KoreaMed Synapse 출처)
# https://synapse.koreamed.org/articles/1071604
# https://synapse.koreamed.org/articles/1516078767
KOREAN_PALM_CREASE_PREVALENCE: dict[str, float] = {
    "normal": 0.844,    # 3선 (생명선·두뇌선·감정선) 정상 패턴
    "simian": 0.112,    # 단일 통합 횡선 (Simian/단지) — 한국 11.2%
    "suwon": 0.005,     # Suwon crease (수원 패턴, 한국 명명)
    "other": 0.039,     # 기타 변종 (Sydney 등)
}


SOURCE_URLS = (
    "https://synapse.koreamed.org/articles/1071604",      # 2010 N=3,216
    "https://synapse.koreamed.org/articles/1516078767",   # 2022 prevalence
)


CREASE_DESCRIPTIONS_KO: dict[str, str] = {
    "normal": "3선 형태 — 생명선·두뇌선·감정선이 각각 또렷이 구분되는 손금. 한국 성인 약 84%에서 나타나는 가장 일반적 형태",
    "simian": "단지(單指) 형태 — 두뇌선과 감정선이 하나로 통합되어 손바닥을 가로지르는 손금. 한국 성인 약 11%에서 나타나는 변종 형태",
    "suwon": "수원(水原) 형태 — 두 주선이 만나면서 보조선이 동반되는 손금. 한국 성인 약 0.5%에서 나타나는 희소 변종 형태",
    "other": "기타 변종 — Sydney crease 등 잔여 형태. 한국 성인 약 4%",
}


_DISCLAIMER = (
    "본 prevalence 통계는 한국인 표본(N=3,216 등) 학술 자료 기반 형태 분포이며, "
    "운명·길흉 매핑이 아닙니다. 손금 형태는 dermatoglyphic 변종이며 의료 "
    "진단·인격 평가 도구가 아닙니다."
)


@dataclass(frozen=True)
class PalmCreasePrevalenceResult:
    """손금 형태 prevalence 비교 결과."""
    crease_type: str            # 'normal'·'simian'·'suwon'·'other'
    prevalence_pct: float       # 0.0~1.0
    description_ko: str
    rank: str                   # 'most_common'·'variant'·'rare'·'unknown'
    source_urls: tuple[str, ...]
    disclaimer: str


def get_prevalence(crease_type: str) -> PalmCreasePrevalenceResult:
    """손금 형태 → prevalence 비교 결과.

    Args:
        crease_type: 'normal'|'simian'|'suwon'|'other' (소문자).
            알 수 없는 값은 'other' 폴백.

    Returns:
        PalmCreasePrevalenceResult (disclaimer 포함).
    """
    ct = (crease_type or "").lower().strip()
    if ct not in KOREAN_PALM_CREASE_PREVALENCE:
        ct = "other"
    pct = KOREAN_PALM_CREASE_PREVALENCE[ct]
    desc = CREASE_DESCRIPTIONS_KO.get(ct, "")

    if pct >= 0.50:
        rank = "most_common"
    elif pct >= 0.05:
        rank = "variant"
    elif pct >= 0.005:
        rank = "rare"
    else:
        rank = "unknown"

    return PalmCreasePrevalenceResult(
        crease_type=ct,
        prevalence_pct=round(pct, 4),
        description_ko=desc,
        rank=rank,
        source_urls=SOURCE_URLS,
        disclaimer=_DISCLAIMER,
    )


def all_prevalences() -> dict[str, PalmCreasePrevalenceResult]:
    """4 형태 전부의 prevalence 결과 dict."""
    return {ct: get_prevalence(ct) for ct in KOREAN_PALM_CREASE_PREVALENCE}
