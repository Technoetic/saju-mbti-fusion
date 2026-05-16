"""임상 위험도 통합 라우터 — 모든 척도 결과를 종합해 의뢰 결정.

규칙 (문서 §7 임상 위기 분기):
  - CES-D ≥ 16점 (노인 21점) 또는
  - BDI-K ≥ 14점 또는 BDI 항목 9 ≥ 1점 (자살 사고) 또는
  - STAI 상태 ≥ 52점 또는
  - PSQI > 5점 동반 + 우울 임계 초과 또는
  - 악몽 주 1회+ × 6개월+ (만성 PTSD 의심)

위 중 하나라도 트리거되면 → 모든 해석 중단 + 1393/1577-0199 안내.
"""

from __future__ import annotations
from typing import Any


def assess_clinical_risk(
    *,
    ces_d_result: dict[str, Any] | None = None,
    bdi_k_result: dict[str, Any] | None = None,
    stai_k_result: dict[str, Any] | None = None,
    psqi_result: dict[str, Any] | None = None,
    isi_result: dict[str, Any] | None = None,
    chronic_nightmare_weeks: int | None = None,
    nightmare_freq_per_week: int | None = None,
) -> dict[str, Any]:
    """모든 임상 척도 결과를 종합해 위험 등급 산출.

    Returns:
        {
            "risk_level": "정상" | "주의" | "고위험" | "임상 위기",
            "triggers": list[str],
            "referral_required": bool,
            "interpretive_note": str,
            "scales_summary": dict,
        }
    """
    triggers: list[str] = []
    summary: dict[str, Any] = {}

    if ces_d_result and ces_d_result.get("exceeded_cutoff"):
        triggers.append(f"CES-D {ces_d_result['total_score']}점 ≥ {ces_d_result['cutoff']} (우울 의심)")
        summary["ces_d"] = ces_d_result["severity"]
    if bdi_k_result:
        if bdi_k_result.get("suicide_alert"):
            triggers.append(f"BDI 자살 사고 항목 {bdi_k_result['suicide_item_score']}점 — 임상 위기")
        if bdi_k_result.get("exceeded_cutoff"):
            triggers.append(f"BDI-K {bdi_k_result['total_score']}점 ≥ 14 (우울 의심)")
        summary["bdi_k"] = bdi_k_result["severity"]
    if stai_k_result and stai_k_result.get("exceeded_cutoff"):
        triggers.append(f"STAI 상태 {stai_k_result['total_score']}점 ≥ 52 (고불안)")
        summary["stai_k_state"] = stai_k_result["severity"]
    if psqi_result and psqi_result.get("exceeded_cutoff"):
        triggers.append(f"PSQI {psqi_result['total_score']}점 > 5 (수면 질 저하)")
        summary["psqi"] = psqi_result["severity"]
    if isi_result and isi_result["total_score"] >= 15:
        triggers.append(f"ISI {isi_result['total_score']}점 ≥ 15 (임상적 불면)")
        summary["isi"] = isi_result["severity"]

    # 만성 악몽 (AASM 2018 cutoff: 주 1회+ × 6개월+)
    if (
        chronic_nightmare_weeks is not None
        and nightmare_freq_per_week is not None
        and chronic_nightmare_weeks >= 26
        and nightmare_freq_per_week >= 1
    ):
        triggers.append(
            f"만성 악몽: 주 {nightmare_freq_per_week}회 × {chronic_nightmare_weeks}주 (PTSD 의심)"
        )
        summary["chronic_nightmare"] = "만성"

    # 위험 등급 — BDI 자살 사고 트리거가 있으면 무조건 임상 위기
    suicide_trigger = bdi_k_result and bdi_k_result.get("suicide_alert")
    if suicide_trigger:
        level = "임상 위기"
    elif len(triggers) >= 2:
        level = "고위험"
    elif len(triggers) == 1:
        level = "주의"
    else:
        level = "정상"

    return {
        "risk_level": level,
        "triggers": triggers,
        "referral_required": level in ("고위험", "임상 위기"),
        "suicide_concern": bool(suicide_trigger),
        "scales_summary": summary,
        "interpretive_note": _build_note(level, triggers),
        "hotlines": (
            ["자살예방상담 1393 (24시간)", "정신건강위기상담 1577-0199 (24시간)"]
            if level == "임상 위기"
            else ["보건복지콜센터 129 (평일 09-18시)", "필요 시 1393 (24시간)"]
            if level in ("고위험", "주의")
            else []
        ),
    }


def _build_note(level: str, triggers: list[str]) -> str:
    if level == "임상 위기":
        return (
            "임상 위기 신호가 탐지되었습니다. 본 자가검사는 진단이 아니며 참고용이지만, "
            "자살예방상담전화 1393(24시간 무료) 또는 정신건강의학과를 즉시 연결해 주십시오."
        )
    if level == "고위험":
        return (
            f"다중 임계 초과({len(triggers)}건). 자가 모니터링만으로 충분하지 않을 수 있으니 "
            "정신건강의학과 또는 가정의학과 전문의 상담을 권합니다."
        )
    if level == "주의":
        return "일부 임계 초과. 증상이 2주 이상 지속되면 전문가 상담을 권합니다."
    return "임상 의뢰 임계치 미만. 자가보고는 그날의 컨디션에 영향 받으니 추세로 보세요."


__all__ = ["assess_clinical_risk"]
