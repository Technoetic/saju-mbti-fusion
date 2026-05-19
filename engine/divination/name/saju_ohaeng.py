"""사주 기반 작명 추천 오행 — 보고서 §3 옵션 A 본문화.

생년월일시 → 사주 8글자 → 5오행 분포(가중치 합) → **결핍 오행 추천**.

옵션 A 선택 이유:
  · 학파 무관, 객관적 데이터
  · "당신의 사주에 火 4점, 水 0점 — 작명 시 水 자원오행 추천"
  · 용신 도출 알고리즘(격국·조후·통관·억부) **회피** — 학파 분쟁 없음

⚠️ 본 모듈은 명리학적 "용신 판정"이 아닌 **단순 오행 분포 통계**.
   진정한 용신은 학파별 차이 있음. 사용자에게 "참고용·균형 보강 지표"로 명시.

운영표준:
  · 결정론 (재현성)
  · LLM 무관
  · engine/saju/ 기존 엔진 재사용
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.saju.pillars import compute_pillars
from engine.saju.wuxing import wuxing_dist


# 오행 한글 라벨
OHAENG_LABELS = ("목", "화", "토", "금", "수")


@dataclass(frozen=True)
class SajuOhaengReport:
    """사주 기반 오행 분포 리포트.

    Attributes:
        pillars: 4기둥 한자 (예: {"year": "甲子", ...})
        day_master: 일간 (예: "정")
        distribution: 오행 분포 (합 ≈ 8.0)
        weakest: 가장 부족한 오행 (작명 우선 추천)
        strongest: 가장 강한 오행
        missing: 0점 오행 리스트 (절대 결핍)
        recommended_target: 작명용 추천 자원오행 (= weakest 또는 missing[0])
        balance_score: 균형 점수 (0~1, 1.0=완전 균형)
    """
    pillars: dict[str, str]
    day_master: str
    distribution: dict[str, float]
    weakest: str
    strongest: str
    missing: list[str] = field(default_factory=list)
    recommended_target: str = ""
    balance_score: float = 0.0


# ─────────────────────────── 사주 → 오행 분포 ───────────────────────────

def compute_saju_ohaeng(
    year: int,
    month: int,
    day: int,
    hour: int,
) -> SajuOhaengReport:
    """생년월일시 → 사주 + 오행 분포 + 추천 자원오행.

    Args:
        year, month, day: 절기 보정된 양력 (caller가 calendar.py로 전처리 권장).
            본 wrapper는 단순 입력만 받음. 절기 기준 월이 필요한 경우 caller 책임.
        hour: 0~23

    Returns:
        SajuOhaengReport
    """
    pillar_dict = compute_pillars(year, month, day, hour)

    # wuxing_dist용 포맷 변환: {"year": "甲子", ...}
    pillars_for_wuxing = {
        "year": pillar_dict["year_pillar"]["gan_han"] + pillar_dict["year_pillar"]["ji_han"],
        "month": pillar_dict["month_pillar"]["gan_han"] + pillar_dict["month_pillar"]["ji_han"],
        "day": pillar_dict["day_pillar"]["gan_han"] + pillar_dict["day_pillar"]["ji_han"],
        "hour": pillar_dict["hour_pillar"]["gan_han"] + pillar_dict["hour_pillar"]["ji_han"],
    }

    dist = wuxing_dist(pillars_for_wuxing)

    # weakest / strongest
    sorted_by_value = sorted(dist.items(), key=lambda kv: kv[1])
    weakest = sorted_by_value[0][0]
    strongest = sorted_by_value[-1][0]

    # 0점 (절대 결핍) 오행
    missing = [k for k, v in dist.items() if v == 0.0]

    # 추천 자원오행 — 0점이 있으면 그것 우선, 아니면 weakest
    recommended = missing[0] if missing else weakest

    # 균형 점수 — 분포 표준편차 기반 (낮을수록 균형)
    avg = sum(dist.values()) / 5.0
    variance = sum((v - avg) ** 2 for v in dist.values()) / 5.0
    std = variance ** 0.5
    # 최대 std(8점이 한 오행에 몰림) ≈ 3.2 → 균형 점수 0
    balance = max(0.0, 1.0 - std / 3.2)

    return SajuOhaengReport(
        pillars=pillars_for_wuxing,
        day_master=pillar_dict["day_master"],
        distribution=dist,
        weakest=weakest,
        strongest=strongest,
        missing=missing,
        recommended_target=recommended,
        balance_score=round(balance, 3),
    )


# ─────────────────────────── 직렬화 ───────────────────────────

def report_to_dict(report: SajuOhaengReport) -> dict[str, Any]:
    """JSON 직렬화."""
    return {
        "pillars": dict(report.pillars),
        "day_master": report.day_master,
        "distribution": dict(report.distribution),
        "weakest": report.weakest,
        "strongest": report.strongest,
        "missing": list(report.missing),
        "recommended_target": report.recommended_target,
        "balance_score": report.balance_score,
        # 작명 모듈 호환 — target_ohaeng 그대로 사용 가능
        "advisory": _build_advisory(report),
    }


def _build_advisory(report: SajuOhaengReport) -> str:
    """사용자 노출용 한 줄 설명. 단정·예언 회피, 균형 지표로만 표현."""
    parts = []
    if report.missing:
        parts.append(f"사주에서 {', '.join(report.missing)} 오행이 비어 있어,")
    else:
        parts.append(f"사주에서 {report.weakest} 오행이 가장 적어,")
    parts.append(f"작명 시 자원오행이 '{report.recommended_target}'인 한자를 우선 고려하면 균형 보강에 도움이 됩니다.")
    parts.append("(참고용 — 정통 용신 판정은 학파별 차이 있음)")
    return " ".join(parts)


# ─────────────────────────── 작명 모듈 호환 ───────────────────────────

def get_target_ohaeng(
    year: int, month: int, day: int, hour: int,
) -> str:
    """작명 모듈(name_gaeja / name_gaemyeong)이 받는 target_ohaeng 직접 반환.

    예:
        from engine.divination.name.gaemyeong import find_gaemyeong_candidates
        from engine.divination.name.saju_ohaeng import get_target_ohaeng

        target = get_target_ohaeng(1990, 5, 15, 14)  # → "수"
        r = find_gaemyeong_candidates(..., target_ohaeng=target)
    """
    return compute_saju_ohaeng(year, month, day, hour).recommended_target
