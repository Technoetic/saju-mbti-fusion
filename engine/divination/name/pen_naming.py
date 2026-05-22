"""ADR-137 — 예명 작명 결정론 (pen 카드).

본 모듈은 정통 작명학 학파 정합 — 활동 분야 → 예명(아호·필명) 한자 풀 산출.

학파 출처:
  · 김기승 (2022) 자원오행 성명학 ISBN 9791160782363
  · 이재승 (2025) 명리·용신 성명학 원론 ISBN 9791173182693
  · 한국 정통 호(號) 작법 — 학파 통설:
    - 자호(自號): 본인의 자질·지향을 담음
    - 아호(雅號): 학예·문필 분야의 정신적 결을 담음
    - 필명(筆名): 청각·시각적 인상을 강조

원칙 (ADR-002·006·010):
  · 활동 분야별 오행 추천은 학파 통설만 인용 (단일 학파 강요 X)
  · 본인의 사주 부족 오행과 합산 가능 (옵션)
  · LLM 작문 시 페르소나 톤 적용 — 본 모듈은 한자 풀만 결정론 산출
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from engine.divination.name.unihan import (
    _load_db,
    hangul_of,
    kci_reason,
    kci_school_source,
)


# 활동 분야 → 추천 오행 매핑 (정통 작명학 학파)
# 분야 코드는 front/js/data/contents.js pen 카드 옵션과 정합
_FIELD_OHAENG: dict[str, dict] = {
    "writer": {
        "label_ko": "작가·시인",
        "ohaeng": ["목", "수"],  # 木 = 종이·문자·창작 / 水 = 흐름·감성
        "rationale": (
            "작가·시인은 종이(木)와 흐름(水)의 결합 — "
            "정신적 성장의 木 + 감성·서정의 水를 우선 추천."
        ),
    },
    "youtube": {
        "label_ko": "유튜브·크리에이터",
        "ohaeng": ["화", "금"],  # 火 = 방송·발신 / 金 = 정밀·편집
        "rationale": (
            "유튜브·크리에이터는 발신·방송(火)과 정밀 편집(金)의 결합 — "
            "에너지의 火 + 명확한 메시지의 金을 우선 추천."
        ),
    },
    "music": {
        "label_ko": "음악·DJ",
        "ohaeng": ["화", "수"],  # 火 = 발산 / 水 = 청각·흐름
        "rationale": (
            "음악·DJ는 발산(火)과 흐름(水)의 결합 — "
            "리듬의 火 + 청각·서정의 水를 우선 추천."
        ),
    },
    "visual": {
        "label_ko": "그림·디자인",
        "ohaeng": ["목", "화"],  # 木 = 성장·창작 / 火 = 발색·표현
        "rationale": (
            "그림·디자인은 창작(木)과 발색(火)의 결합 — "
            "성장의 木 + 색·표현의 火를 우선 추천."
        ),
    },
    "actor": {
        "label_ko": "배우·연기",
        "ohaeng": ["화", "토"],  # 火 = 표현·발산 / 土 = 중심·신뢰
        "rationale": (
            "배우·연기는 표현(火)과 중심(土)의 결합 — "
            "발산의 火 + 깊이의 土를 우선 추천."
        ),
    },
    "other": {
        "label_ko": "기타",
        "ohaeng": ["목", "화", "토", "금", "수"],  # 전체
        "rationale": "활동 분야가 미지정 — 5 오행 폴백 풀.",
    },
}


@dataclass(frozen=True)
class PenNamingResult:
    """예명 작명 결정론 산출 결과.

    Attributes:
        field_code: 활동 분야 코드 (writer·youtube·music·visual·actor·other)
        field_label_ko: 분야 한국어 라벨
        target_ohaeng: 추천 오행 풀
        rationale: 학파 근거 설명
        recommended_hanja: 추천 한자 풀 (최대 20자)
        school_source: 학파 출처
        disclaimer: 면책
    """
    field_code: str
    field_label_ko: str
    target_ohaeng: List[str]
    rationale: str
    recommended_hanja: List[dict]
    school_source: str
    disclaimer: str


def _candidate_hanja_for_pen(
    target_ohaeng: List[str], limit: int = 20
) -> List[dict]:
    """추천 오행에 해당하는 KCI 학파 출처 명시 한자 풀."""
    db = _load_db()
    results = []
    seen_chars: set = set()
    for char, entry in db.items():
        if char in seen_chars:
            continue
        ohaeng = entry.get("resource_ohaeng_kci")
        if ohaeng in target_ohaeng:
            results.append({
                "char": char,
                "hangul": hangul_of(char) or "",
                "ohaeng": ohaeng,
                "kci_reason": kci_reason(char) or "",
                "school": kci_school_source(char) or "",
            })
            seen_chars.add(char)
        if len(results) >= limit:
            break
    return results


def compute_pen_naming(
    field_code: str,
    real_saju_weak_ohaeng: Optional[List[str]] = None,
) -> PenNamingResult:
    """예명 작명 결정론 산출.

    Args:
        field_code: 활동 분야 코드 (writer·youtube·music·visual·actor·other).
                    front/js/data/contents.js pen 카드 옵션과 정합.
        real_saju_weak_ohaeng: 본인 사주 부족 오행 (saju_ohaeng.py 산출).
                               있으면 추천 오행에 합산.

    Returns:
        PenNamingResult — 추천 오행 + 한자 풀 + 학파 근거.
    """
    field_data = _FIELD_OHAENG.get(field_code) or _FIELD_OHAENG["other"]
    target = list(field_data["ohaeng"])

    # 사주 부족 오행 합산 (옵션)
    if real_saju_weak_ohaeng:
        for o in real_saju_weak_ohaeng:
            if o and o not in target:
                target.append(o)

    hanja_pool = _candidate_hanja_for_pen(target, limit=20)

    return PenNamingResult(
        field_code=field_code,
        field_label_ko=field_data["label_ko"],
        target_ohaeng=target,
        rationale=field_data["rationale"],
        recommended_hanja=hanja_pool,
        school_source=(
            "김기승 (2022) 자원오행 성명학 제5판 ISBN 9791160782363 + "
            "이재승 (2025) 명리·용신 성명학 원론 ISBN 9791173182693"
        ),
        disclaimer=(
            "참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다. "
            "예명은 활동의 한 요소이며 활동 성공의 단독 근거 X."
        ),
    )


__all__ = ["PenNamingResult", "compute_pen_naming"]
