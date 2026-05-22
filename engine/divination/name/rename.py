"""ADR-139 — 개명 추천 결정론 (rename 카드).

본 모듈은 현 이름과 사주의 충(沖) 진단 + 사주 보강 한자 후보 풀 산출.

학파 출처:
  · 자평진전·삼명통회 — 천간/지지 합·충·형·파·해 (engine/saju/compat.py)
  · 김기승 (2022) 자원오행 성명학 — 이름-사주 정합 학파
  · 이재승 (2025) 명리·용신 성명학 원론 — 용신 보강 학파

원칙 (ADR-002·006·010·015):
  · 현 이름 발음오행 vs 사주 일간 오행 충돌 진단
  · 충돌이 있을 때만 개명 후보 추천 — 단정 X
  · LLM 작문이 페르소나 톤 적용 — 결정론 모듈은 후보만
  · 부정적 진단 어휘 차단 (ADR-006) — "운이 안 좋다"는 사용자 입력만 인용
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date as _date
from typing import List, Optional

from engine.divination.name.baleum import evaluate_baleum
from engine.divination.name.newborn import _candidate_hanja_for_saju
from engine.divination.name.saju_ohaeng import compute_saju_ohaeng


_HOUR_BRANCH_TO_HOUR: dict[str, int] = {
    "子": 0, "丑": 2, "寅": 4, "卯": 6, "辰": 8, "巳": 10,
    "午": 12, "未": 14, "申": 16, "酉": 18, "戌": 20, "亥": 22,
}

# 오행 상극 (충돌) 매핑
_WX_CONTROL: dict[str, str] = {
    "목": "토", "토": "수", "수": "화", "화": "금", "금": "목",
}

# 천간 → 오행
_STEM_WUXING: dict[str, str] = {
    "甲": "목", "乙": "목", "丙": "화", "丁": "화", "戊": "토",
    "己": "토", "庚": "금", "辛": "금", "壬": "수", "癸": "수",
}


@dataclass(frozen=True)
class RenameDiagnosis:
    """개명 진단 결정론 산출.

    Attributes:
        current_name: 현재 이름
        birth_iso: 생년월일 ISO
        ohaeng_conflict: 발음오행과 사주 일간 충돌 여부
        conflict_detail: 충돌 상세 (한 줄)
        baleum_grade: 발음오행 등급
        baleum_reason: 발음오행 평가 사유
        saju_recommended_ohaeng: 사주 보강 추천 오행
        recommended_hanja: 개명 후보 한자 풀
        user_reason: 사용자 입력 개명 이유 (LLM 전달용)
        school_source: 학파 출처
        disclaimer: 면책
    """
    current_name: str
    birth_iso: str
    ohaeng_conflict: bool
    conflict_detail: str
    baleum_grade: str
    baleum_reason: str
    saju_recommended_ohaeng: List[str]
    recommended_hanja: List[dict]
    user_reason: str
    school_source: str
    disclaimer: str


def _diagnose_ohaeng_conflict(
    name_baleum_seq: List[str], day_master_ohaeng: str
) -> tuple[bool, str]:
    """이름 발음오행 흐름 vs 일간 오행 충돌 진단.

    Returns:
        (충돌 여부, 상세 한 줄)
    """
    if not name_baleum_seq or not day_master_ohaeng:
        return False, "발음오행 또는 일간 오행 부재 — 진단 미수행"

    # 일간을 극하는 오행 (상극) 발생 여부
    controller = None
    for o, target in _WX_CONTROL.items():
        if target == day_master_ohaeng:
            controller = o
            break

    if controller and controller in name_baleum_seq:
        return True, (
            f"이름 발음오행에 '{controller}'(이/가) 포함 — 일간 '{day_master_ohaeng}' "
            f"오행을 극(剋)하는 흐름 존재"
        )
    return False, "이름 발음오행과 일간 오행이 상극 관계 미발견"


def compute_rename(
    current_name: str,
    birth_iso: str,
    hour_branch: Optional[str] = None,
    gender: Optional[str] = None,
    user_reason: str = "",
) -> Optional[RenameDiagnosis]:
    """개명 진단 + 후보 산출 결정론.

    Args:
        current_name: 현재 이름 (한글).
        birth_iso: 생년월일 'YYYY-MM-DD'.
        hour_branch: 태어난 시각 지지 한자 (옵션). None이면 정오 12시 폴백.
        gender: 'M' · 'F' · None.
        user_reason: 사용자 개명 이유 텍스트 (LLM 전달용).

    Returns:
        RenameDiagnosis 또는 None (파싱 실패).
    """
    try:
        d = _date.fromisoformat(birth_iso)
    except (ValueError, TypeError):
        return None

    hour_int = 12
    if hour_branch and hour_branch in _HOUR_BRANCH_TO_HOUR:
        hour_int = _HOUR_BRANCH_TO_HOUR[hour_branch]

    try:
        report = compute_saju_ohaeng(d.year, d.month, d.day, hour_int)
    except Exception:
        return None

    # 일간 오행 (한글)
    day_pillar = report.pillars.get("day", "") if isinstance(report.pillars, dict) else ""
    day_gan_han = day_pillar[0] if day_pillar else ""
    day_master_ohaeng = _STEM_WUXING.get(day_gan_han, "")

    # 발음오행 평가
    name_baleum_seq: List[str] = []
    baleum_grade = ""
    baleum_reason = ""
    try:
        baleum_report = evaluate_baleum(current_name, include_jongsung=False)
        name_baleum_seq = list(getattr(baleum_report, "ohaeng_sequence", []) or [])
        baleum_grade = getattr(baleum_report, "grade", "") or ""
        baleum_reason = getattr(baleum_report, "reason", "") or ""
    except Exception:
        pass

    conflict, detail = _diagnose_ohaeng_conflict(name_baleum_seq, day_master_ohaeng)

    # 추천 오행 — 사주 보강 우선
    target_ohaeng: List[str] = []
    if report.recommended_target:
        target_ohaeng.append(report.recommended_target)
    for missing in report.missing:
        if missing not in target_ohaeng:
            target_ohaeng.append(missing)

    if not target_ohaeng and report.weakest:
        target_ohaeng = [report.weakest]

    hanja_pool = _candidate_hanja_for_saju(target_ohaeng, limit=30) if target_ohaeng else []

    return RenameDiagnosis(
        current_name=current_name,
        birth_iso=birth_iso,
        ohaeng_conflict=conflict,
        conflict_detail=detail,
        baleum_grade=baleum_grade,
        baleum_reason=baleum_reason,
        saju_recommended_ohaeng=target_ohaeng,
        recommended_hanja=hanja_pool,
        user_reason=user_reason,
        school_source=(
            "정통 사주명리 (자평진전·삼명통회) + KCI 자원오행 학파 "
            "(이재승 2024 KCI DSpace 2187321) + 발음오행 (조현아 2014 DBpia T13373928)"
        ),
        disclaimer=(
            "참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다. "
            "개명은 본인의 최종 결단이며, 본 진단은 학파 통설 분석일 뿐."
        ),
    )


__all__ = ["RenameDiagnosis", "compute_rename"]
