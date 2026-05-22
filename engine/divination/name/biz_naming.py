"""ADR-136 — 상호 작명 결정론 (biz 카드).

본 모듈은 정통 작명학 학파 정합 — 업종 → 오행 매핑 + 상호 한자 풀 산출.

학파 출처:
  · 김기승 (2022) 『자원오행 성명학 제5판』 ISBN 9791160782363 — 다산글방
    - 업종별 오행 매핑 표 (제3장 직업·상호)
  · 이재승 (2025) 『명리·용신 성명학 원론』 ISBN 9791173182693 — 한국학술정보
  · 보고서 「작명학 한자 자원오행 매핑 학술 출처 조사」 §2.3·§4.1
    (정통 자원오행 학파 — ISBN 출판 서적 기반 실용 매핑)

원칙 (ADR-002·006·010):
  · 단일 학파 강요 X — 본 매핑은 정통 작명학 (김기승·이재승) 통설
  · 업종은 사용자가 자유 텍스트 입력 — 본 모듈은 키워드 매칭 결정론
  · 결과는 추천 한자 풀만 — 단정 X (LLM 작문이 페르소나 톤 적용)
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


# 업종 키워드 → 추천 오행 매핑 (정통 작명학 학파)
# 출처: 김기승 (2022) 자원오행 성명학 + 이재승 (2025) 명리·용신 성명학 원론
# 학파 통설 — 단일 학파 강요 X (사용자 사주 보강 우선)
_BIZ_TYPE_OHAENG: dict[tuple[str, ...], list[str]] = {
    # 木 — 성장·교육·출판·종이·의류·식물
    ("교육", "학원", "출판", "서점", "도서", "문구", "종이", "의류", "패션",
     "옷", "원예", "꽃집", "조경", "농산물"):
        ["목"],
    # 火 — 조명·예술·요리·미용·전기·IT(에너지)·연예
    ("요리", "음식", "식당", "카페", "베이커리", "디저트", "미용", "헤어",
     "조명", "전기", "예술", "갤러리", "공연", "연예", "방송"):
        ["화"],
    # 土 — 부동산·건설·중개·창고·농지·도자기
    ("부동산", "건설", "공사", "중개", "창고", "물류", "도자기", "토목",
     "건축", "리모델링", "인테리어"):
        ["토"],
    # 金 — 금속·기계·금융·법무·자동차·보석·IT(하드웨어)
    ("금속", "기계", "공구", "자동차", "정비", "보석", "주얼리", "금융",
     "은행", "증권", "투자", "법무", "회계", "IT", "소프트웨어", "하드웨어"):
        ["금"],
    # 水 — 유통·물·음료·여행·해운·약국·병원·운송
    ("유통", "무역", "운송", "택배", "해운", "음료", "주류", "약국",
     "약품", "병원", "의료", "헬스케어", "여행", "관광"):
        ["수"],
}

# 컨셉 키워드 → 보조 오행 (사용자 선호 톤 반영)
_CONCEPT_OHAENG: dict[tuple[str, ...], str] = {
    ("따뜻한", "친근한", "포근한", "온화한"): "화",
    ("전통적인", "고전적인", "정통의", "고풍의"): "토",
    ("세련된", "모던한", "스마트한", "정밀한"): "금",
    ("자연의", "친환경", "초록의", "성장의"): "목",
    ("유연한", "맑은", "흐름의", "투명한"): "수",
}


@dataclass(frozen=True)
class BizNamingResult:
    """상호 작명 결정론 산출 결과.

    Attributes:
        biz_type: 업종 (사용자 입력)
        concept: 컨셉 (사용자 입력, 옵션)
        target_ohaeng_primary: 1차 추천 오행 (업종 매칭)
        target_ohaeng_secondary: 2차 추천 오행 (컨셉 매칭, None 가능)
        recommended_hanja: 추천 한자 풀 (target_ohaeng 자원오행 매칭, 최대 20자)
        school_source: 학파 출처 명시
        disclaimer: 면책
    """
    biz_type: str
    concept: str
    target_ohaeng_primary: List[str]
    target_ohaeng_secondary: Optional[str]
    recommended_hanja: List[dict]
    school_source: str
    disclaimer: str
    notes: str = ""


def _match_biz_ohaeng(biz_type: str) -> List[str]:
    """업종 텍스트 → 1차 추천 오행 리스트 (키워드 매칭)."""
    bt_lower = biz_type.lower().strip()
    matched = []
    for keywords, ohaengs in _BIZ_TYPE_OHAENG.items():
        for kw in keywords:
            if kw in biz_type or kw.lower() in bt_lower:
                for o in ohaengs:
                    if o not in matched:
                        matched.append(o)
                break
    return matched


def _match_concept_ohaeng(concept: str) -> Optional[str]:
    """컨셉 텍스트 → 2차 보조 오행 (키워드 매칭)."""
    if not concept:
        return None
    for keywords, ohaeng in _CONCEPT_OHAENG.items():
        for kw in keywords:
            if kw in concept:
                return ohaeng
    return None


def _candidate_hanja_for_ohaeng(
    target_ohaeng: List[str], limit: int = 20
) -> List[dict]:
    """추천 오행에 해당하는 한자 풀 — KCI 학파 출처 명시 우선.

    Returns:
        [{"char": "鐵", "hangul": "철", "ohaeng": "금", "school": "...", ...}, ...]
    """
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


def compute_biz_naming(
    biz_type: str,
    concept: str = "",
    owner_saju_weak_ohaeng: Optional[List[str]] = None,
) -> BizNamingResult:
    """상호 작명 결정론 산출.

    Args:
        biz_type: 업종 (예: '카페·IT 스타트업·의류 브랜드').
        concept: 사용자 추구 컨셉 (예: '따뜻한·전통적인'). 옵션.
        owner_saju_weak_ohaeng: 사업자 사주 부족 오행 (saju_ohaeng.py 산출).
                                있으면 1차 추천에 합산.

    Returns:
        BizNamingResult — 추천 오행 + 한자 풀.
    """
    primary = _match_biz_ohaeng(biz_type)
    secondary = _match_concept_ohaeng(concept)

    # 사주 부족 오행 합산 (옵션)
    if owner_saju_weak_ohaeng:
        for o in owner_saju_weak_ohaeng:
            if o and o not in primary:
                primary.append(o)

    # 1차 매칭 없으면 폴백 — 모든 오행 (NoneType 매칭)
    if not primary:
        primary = ["목", "화", "토", "금", "수"]
        notes = "업종 키워드 미매칭 — 전체 오행 폴백"
    else:
        notes = ""

    # 추천 한자 풀
    target_ohaengs = list(primary)
    if secondary and secondary not in target_ohaengs:
        target_ohaengs.append(secondary)
    hanja_pool = _candidate_hanja_for_ohaeng(target_ohaengs, limit=20)

    return BizNamingResult(
        biz_type=biz_type,
        concept=concept,
        target_ohaeng_primary=primary,
        target_ohaeng_secondary=secondary,
        recommended_hanja=hanja_pool,
        school_source=(
            "김기승 (2022) 자원오행 성명학 제5판 ISBN 9791160782363 + "
            "이재승 (2025) 명리·용신 성명학 원론 ISBN 9791173182693"
        ),
        disclaimer=(
            "참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다. "
            "상호는 사업의 한 요소이며 사업 성공의 단독 근거 X."
        ),
        notes=notes,
    )


__all__ = ["BizNamingResult", "compute_biz_naming"]
