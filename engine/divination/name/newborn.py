"""ADR-138 — 신생아 작명 결정론 (newborn 카드).

본 모듈은 ADR-001·028·109·129·125·126·127 정합 통합:
  · 사주 부족 오행 산출 (engine.divination.name.saju_ohaeng)
  · 추천 자원오행 KCI 한자 풀 (unihan.py resource_ohaeng_kci)
  · 성씨 발음오행 흐름 + 음 조화 (baleum.py)
  · 4격 길흉 (strokes.py + scoring.py)

원칙 (ADR-002·006·010·015):
  · 본 모듈은 결정론 후보 풀만 산출 — LLM 작문이 최종 후보 선정
  · 사용자 (부모)의 바람 텍스트는 LLM에 전달 — 결정론 모듈 미수정
  · 학파 분기 명시 — 디폴트 자평진전 + 옵션 B 가능
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date as _date
from typing import List, Optional

from engine.divination.name.saju_ohaeng import compute_saju_ohaeng
from engine.divination.name.unihan import (
    _load_db,
    hangul_of,
    kangxi_strokes,
    kci_reason,
    kci_school_source,
)


@dataclass(frozen=True)
class NewbornNamingResult:
    """신생아 작명 결정론 산출 결과.

    Attributes:
        surname: 성 한자 또는 한글
        baby_birth_iso: 출생 (예정)일 ISO
        baby_hour: 출생 시각 (지지 한자) 또는 None
        baby_gender: 성별 ('M'·'F' 또는 None)
        saju_recommended_ohaeng: 사주 부족 오행 추천 풀
        saju_balance_score: 사주 균형 점수
        saju_summary: 사주 일주 + 일간 요약
        recommended_hanja: 추천 한자 풀 (사주 보강 오행 매칭)
        parent_wish: 부모 바람 텍스트 (LLM 전달)
        school_source: 학파 출처
        disclaimer: 면책
    """
    surname: str
    baby_birth_iso: str
    baby_hour: Optional[str]
    baby_gender: Optional[str]
    saju_recommended_ohaeng: List[str]
    saju_balance_score: float
    saju_summary: str
    recommended_hanja: List[dict]
    parent_wish: str
    school_source: str
    disclaimer: str


_HOUR_BRANCH_TO_HOUR: dict[str, int] = {
    "子": 0, "丑": 2, "寅": 4, "卯": 6, "辰": 8, "巳": 10,
    "午": 12, "未": 14, "申": 16, "酉": 18, "戌": 20, "亥": 22,
}


def _candidate_hanja_for_saju(
    target_ohaeng: List[str], limit: int = 30
) -> List[dict]:
    """사주 추천 오행 → KCI 자원오행 매핑 한자 풀."""
    db = _load_db()
    results = []
    for char, entry in db.items():
        ohaeng = entry.get("resource_ohaeng_kci")
        if ohaeng in target_ohaeng:
            results.append({
                "char": char,
                "hangul": hangul_of(char) or "",
                "ohaeng": ohaeng,
                "kangxi_strokes": kangxi_strokes(char) or 0,
                "kci_reason": kci_reason(char) or "",
                "school": kci_school_source(char) or "",
            })
        if len(results) >= limit:
            break
    return results


def compute_newborn_naming(
    surname: str,
    baby_birth_iso: str,
    baby_hour_branch: Optional[str] = None,
    baby_gender: Optional[str] = None,
    parent_wish: str = "",
) -> Optional[NewbornNamingResult]:
    """신생아 작명 결정론 후보 추천.

    Args:
        surname: 성 (한자 또는 한글).
        baby_birth_iso: 출생일 'YYYY-MM-DD'.
        baby_hour_branch: 출생 시각 지지 한자 (子~亥). None이면 정오 12시 폴백.
        baby_gender: 'M' · 'F' · None.
        parent_wish: 부모의 바람 텍스트 (LLM 전달용 — 결정론 미수정).

    Returns:
        NewbornNamingResult 또는 None (입력 파싱 실패 시).
    """
    try:
        d = _date.fromisoformat(baby_birth_iso)
    except (ValueError, TypeError):
        return None

    # 출생 시각 산출
    hour_int = 12  # 폴백
    if baby_hour_branch and baby_hour_branch in _HOUR_BRANCH_TO_HOUR:
        hour_int = _HOUR_BRANCH_TO_HOUR[baby_hour_branch]

    try:
        report = compute_saju_ohaeng(d.year, d.month, d.day, hour_int)
    except Exception:
        return None

    target_ohaeng: List[str] = []
    if report.recommended_target:
        target_ohaeng.append(report.recommended_target)
    for missing in report.missing:
        if missing not in target_ohaeng:
            target_ohaeng.append(missing)

    # 추천 풀 부재 시 폴백 — weakest 오행
    if not target_ohaeng and report.weakest:
        target_ohaeng = [report.weakest]

    hanja_pool = _candidate_hanja_for_saju(target_ohaeng, limit=30) if target_ohaeng else []

    # 사주 요약 텍스트
    day_pillar = report.pillars.get("day", "") if isinstance(report.pillars, dict) else ""
    saju_summary = (
        f"일주: {day_pillar} / 일간: {report.day_master} / "
        f"균형: {report.balance_score:.2f} / 부족 오행: {','.join(report.missing) or '(없음)'}"
    )

    return NewbornNamingResult(
        surname=surname,
        baby_birth_iso=baby_birth_iso,
        baby_hour=baby_hour_branch,
        baby_gender=baby_gender,
        saju_recommended_ohaeng=target_ohaeng,
        saju_balance_score=report.balance_score,
        saju_summary=saju_summary,
        recommended_hanja=hanja_pool,
        parent_wish=parent_wish,
        school_source=(
            "정통 사주명리 (자평진전·삼명통회) + KCI 자원오행 학파 "
            "(이재승·김만태 2018 DOI 10.33645/cnc.2018.06.40.3.339)"
        ),
        disclaimer=(
            "참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다. "
            "신생아 작명은 부모의 최종 결단이며, 본 추천은 학파 통설 후보 풀일 뿐."
        ),
    )


__all__ = ["NewbornNamingResult", "compute_newborn_naming"]
