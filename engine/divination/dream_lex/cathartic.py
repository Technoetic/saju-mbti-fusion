"""카타르시스 꿈 분류 — 감정 아크(emotional arc) 분석.

출처: 2025 LLM 연구 (DreamNet 계열) — 꿈의 감정 기승전결을 추적해
'카타르시스 꿈(cathartic dream)' 범주를 식별. 인간 평가자와 일치도 87~100%.

핵심 차이:
  - 기존 valence(정서가)는 평균값만 측정 — 아크를 잡지 못함
  - 카타르시스 꿈 = 초중반 부정 → 결말 긍정/해소 (능동적 정서 처리)
  - 악몽 = 부정 시작 → 부정 유지/폭력적 결말 (미해결)
  - 길몽 = 긍정 시작 → 긍정 유지

본 모듈은 결정론 분류 + (선택) LLM 보조.
임상 데이터: 카타르시스 꿈 빈도 ↑ ↔ 우울·불안 점수 ↓ (유의미).
"""

from __future__ import annotations
from typing import Any


CATHARTIC_LABEL = (
    "카타르시스 꿈 — 감정이 초중반 부정 → 결말 긍정 반전. "
    "능동적 정서 처리의 신호. 빈도 증가는 우울·불안 감소와 비례 (2025 연구)."
)


# 부정 정서 마커 (초중반·결말 모두 적용)
NEGATIVE_AFFECT = [
    "무서웠", "두려", "공포", "겁났", "떨었",
    "슬펐", "울었", "비통", "외로움",
    "화났", "분노", "짜증", "성났",
    "당황", "혼란", "당혹",
    "절망", "막막", "갇혔", "출구가 없",
    "쫓겼", "공격받", "위협",
]

# 긍정 정서·해소 마커 (결말 우선)
POSITIVE_AFFECT = [
    "기뻤", "행복", "즐거", "신나", "웃었",
    "안도", "편안", "평화", "고요", "안심",
    "도움 받았", "구조됐", "이겨냈", "벗어났",
    "안전한 곳", "보호받",
    "사랑", "포옹", "재회", "용서",
]

# 강한 해소·반전 마커 (카타르시스 핵심)
CATHARTIC_RESOLUTION = [
    "마침내", "결국", "끝내", "드디어",
    "갑자기 좋아짐", "갑자기 평화", "전환됐",
    "구원받", "해방", "풀려났",
]

# 폭력·미해결 결말 (악몽)
VIOLENT_ENDING = [
    "결국 죽었", "결국 잡혔", "결국 실패", "결국 무너",
    "다 끝났", "포기했", "어쩔 수 없",
    "피로 물든", "잔혹", "처참",
]


def _split_into_thirds(text: str) -> tuple[str, str, str]:
    """텍스트를 대략 3등분 (초/중/결말)."""
    if not text:
        return "", "", ""
    n = len(text)
    a = n // 3
    b = 2 * n // 3
    return text[:a], text[a:b], text[b:]


def _count_affect(segment: str, markers: list[str]) -> int:
    return sum(1 for m in markers if m in segment)


def classify_cathartic_arc(text: str) -> dict[str, Any]:
    """결정론적 감정 아크 분류."""
    t = text or ""
    if not t.strip():
        return {
            "arc_type": "unknown",
            "interpretive_note": "텍스트가 비어 있음.",
        }

    first, mid, last = _split_into_thirds(t)

    neg = (
        _count_affect(first, NEGATIVE_AFFECT),
        _count_affect(mid, NEGATIVE_AFFECT),
        _count_affect(last, NEGATIVE_AFFECT),
    )
    pos = (
        _count_affect(first, POSITIVE_AFFECT),
        _count_affect(mid, POSITIVE_AFFECT),
        _count_affect(last, POSITIVE_AFFECT),
    )
    resolution_in_last = _count_affect(last, CATHARTIC_RESOLUTION)
    violent_in_last = _count_affect(last, VIOLENT_ENDING)

    # 아크 분류 로직
    early_negative = neg[0] + neg[1] >= 2
    late_positive = pos[2] >= 1 or resolution_in_last >= 1
    late_violent = violent_in_last >= 1
    overall_positive = sum(pos) >= 2 and sum(neg) <= 1
    overall_negative = sum(neg) >= 3 and sum(pos) <= 1

    if early_negative and late_positive and not late_violent:
        arc = "cathartic"
        label = "카타르시스 꿈"
        clinical_note = (
            "초중반 부정 → 결말 긍정/해소 — 능동적 정서 처리의 핵심 신호. "
            "빈도 증가는 우울·불안 감소와 비례한다는 연구 결과 (2025)."
        )
    elif early_negative and late_violent:
        arc = "nightmare"
        label = "악몽"
        clinical_note = (
            "부정 시작 → 폭력적/미해결 결말. 주 1회+ × 6개월+ 지속 시 IRT(악몽 재각본) 권장."
        )
    elif early_negative and not late_positive and not late_violent:
        arc = "unresolved_anxiety"
        label = "미해결 불안"
        clinical_note = "부정 정서가 해소되지 못한 채 끝남. Cartwright 관점에선 정서 처리가 진행 중."
    elif overall_positive:
        arc = "positive"
        label = "긍정 꿈"
        clinical_note = "전반적으로 긍정 정서. 길몽 또는 SEEKING 회로 활성."
    elif overall_negative:
        arc = "negative"
        label = "전반 부정"
        clinical_note = "전반적으로 부정 정서가 짙음. 연속 발생 시 정서 점검 권장."
    else:
        arc = "neutral_or_mixed"
        label = "중립/혼합"
        clinical_note = "명확한 감정 아크 신호 없음."

    return {
        "arc_type": arc,
        "arc_label": label,
        "negative_by_third": neg,
        "positive_by_third": pos,
        "resolution_markers_in_last": resolution_in_last,
        "violent_markers_in_last": violent_in_last,
        "is_cathartic": arc == "cathartic",
        "clinical_note": clinical_note,
        "research_basis": (
            "2025 LLM 연구 (DreamNet 계열): 카타르시스 꿈 빈도 ↑ ↔ "
            "우울(CES-D)·불안(STAI) 점수 ↓ 유의미한 상관관계 입증."
        ),
    }


__all__ = [
    "CATHARTIC_LABEL",
    "NEGATIVE_AFFECT",
    "POSITIVE_AFFECT",
    "CATHARTIC_RESOLUTION",
    "VIOLENT_ENDING",
    "classify_cathartic_arc",
]
