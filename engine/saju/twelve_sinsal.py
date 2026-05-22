# -*- coding: utf-8 -*-
"""십이신살(十二神煞) 결정론 매핑 모듈 — ADR-131.

자평진전(沈孝瞻 1734) + 삼명통회(萬民英 1578) 일치 표준 (학파 분기 없음).

12 신살 (출생 연도 지지 또는 일주 지지 → 삼합 기준):
  겁살(劫殺)·재살(災殺)·천살(天殺)·지살(地殺)·년살(年殺)·월살(月殺)
  ·망신살(亡身殺)·장성살(將星殺)·반안살(攀鞍殺)·역마살(驛馬殺)
  ·육해살(六害殺)·화개살(華蓋殺)

매핑 원칙 (4 삼합 → 12 지지 순서):
  - 申子辰 (수국): 巳·午·未·申·酉·戌·亥·子·丑·寅·卯·辰
  - 巳酉丑 (금국): 寅·卯·辰·巳·午·未·申·酉·戌·亥·子·丑
  - 寅午戌 (화국): 亥·子·丑·寅·卯·辰·巳·午·未·申·酉·戌
  - 亥卯未 (목국): 申·酉·戌·亥·子·丑·寅·卯·辰·巳·午·未

본 시스템 정합 검증:
  - 천살(天殺)은 engine/divination/ancestor/cheonsal.py와 동일 매핑 (ADR-122)
  - 역마살(驛馬殺)은 engine/saju/shensha.py _TRIPLES 동일 매핑

학술 출처:
  - 자평진전 한국 번역본 (이담북스 2011·푸른길 2023·문원북 2020 등 ISBN 다수)
  - 삼명통회 한국 번역본 (문원북 2017-2019·부크크 2023 등 ISBN 다수)
  - KCI 직접 인용 부재 (ADR-128 정합 — 정직 명시)

ADR 정합:
  - ADR-002: 학파 분기 없는 표준 — 자평진전·삼명통회 일치
  - ADR-006: 결정론 매칭만 — 단정 어휘 X (흐름 톤 동반 의무)
  - ADR-010: 정통 사주명리 원전 ISBN 학파만
  - ADR-122 천살 + ADR-128 추가 신살 정합
"""
from __future__ import annotations

from typing import Dict, List


# 12 신살 순서 (삼합 4 시작 지지 → 12 지지 순환)
_SINSAL_ORDER = (
    "겁살", "재살", "천살", "지살", "년살", "월살",
    "망신살", "장성살", "반안살", "역마살", "육해살", "화개살",
)

_SINSAL_HAN: Dict[str, str] = {
    "겁살": "劫殺",
    "재살": "災殺",
    "천살": "天殺",
    "지살": "地殺",
    "년살": "年殺",
    "월살": "月殺",
    "망신살": "亡身殺",
    "장성살": "將星殺",
    "반안살": "攀鞍殺",
    "역마살": "驛馬殺",
    "육해살": "六害殺",
    "화개살": "華蓋殺",
}

# 4 삼합 기준 시작 지지 (겁살 위치) → 12 지지 순환
# 자평진전 정통 표준 매핑
_SAMHAP_START_JI: Dict[frozenset, str] = {
    frozenset({"申", "子", "辰"}): "巳",   # 수국 — 겁살 巳에서 시작
    frozenset({"巳", "酉", "丑"}): "寅",   # 금국 — 겁살 寅
    frozenset({"寅", "午", "戌"}): "亥",   # 화국 — 겁살 亥
    frozenset({"亥", "卯", "未"}): "申",   # 목국 — 겁살 申
}

# 12 지지 순서 (子부터 시작, 시계 방향)
_JI_ORDER = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def _find_samhap(year_ji: str) -> frozenset:
    """출생 연도 지지가 속한 삼합 frozenset 반환."""
    for samhap in _SAMHAP_START_JI.keys():
        if year_ji in samhap:
            return samhap
    return frozenset()


def _build_sinsal_mapping(year_ji: str) -> Dict[str, str]:
    """출생 연도 지지 → 12 신살 → 지지 한자 매핑.

    Args:
        year_ji: 출생 연도 지지 한자 (子~亥 중 1).

    Returns:
        {"겁살": "巳", "재살": "午", ..., "화개살": "辰"} 12 신살 매핑.
        잘못된 입력 시 빈 dict.
    """
    samhap = _find_samhap(year_ji)
    if not samhap:
        return {}
    start_ji = _SAMHAP_START_JI[samhap]
    start_idx = _JI_ORDER.index(start_ji)
    mapping = {}
    for offset, sinsal_name in enumerate(_SINSAL_ORDER):
        ji_idx = (start_idx + offset) % 12
        mapping[sinsal_name] = _JI_ORDER[ji_idx]
    return mapping


def get_sinsal_for_year(year_ji: str) -> Dict[str, Dict[str, str]]:
    """출생 연도 지지 → 12 신살 풀 결정론 매핑 (자평진전 정통 — 연주 기준).

    Args:
        year_ji: 출생 연도 지지 한자.

    Returns:
        {신살명: {ji: 지지 한자, han: 신살 한자}} 12건.
        잘못된 입력 시 빈 dict.

    Examples:
        >>> result = get_sinsal_for_year("子")  # 申子辰 수국
        >>> result["천살"]["ji"]
        '未'
        >>> result["겁살"]["ji"]
        '巳'
    """
    mapping = _build_sinsal_mapping(year_ji)
    if not mapping:
        return {}
    return {
        name: {"ji": ji, "han": _SINSAL_HAN[name]}
        for name, ji in mapping.items()
    }


def get_sinsal_for_day(day_ji: str) -> Dict[str, Dict[str, str]]:
    """일주 지지 → 12 신살 풀 결정론 매핑 (명리정종 학파 — 일주 기준).

    ADR-141 supplement: ADR-131 한계 절 line 105 "일주 지지 기준 분기는
    학파 분기 영역 (DEFER)" 해소. 본 함수는 명리정종(命理正宗) 학파에서
    채택하는 일주(日柱) 지지 기준 12 신살 산출.

    매핑 룰은 자평진전(연주 기준)과 동일 — 삼합 기준 12 지지 순환.
    차이는 기준 지지만 (연 → 일).

    Args:
        day_ji: 일주 지지 한자 (子~亥).

    Returns:
        {신살명: {ji: 지지 한자, han: 신살 한자}} 12건.

    Examples:
        >>> # 일주 지지 子 → 申子辰 수국 → 겁살 巳
        >>> result = get_sinsal_for_day("子")
        >>> result["겁살"]["ji"]
        '巳'
    """
    return get_sinsal_for_year(day_ji)


def get_sinsal_by_basis(
    branch_ji: str,
    basis: str = "year",
) -> Dict[str, Dict[str, str]]:
    """기준 학파별 12 신살 매핑 — 통합 API.

    Args:
        branch_ji: 기준 지지 한자 (연주 또는 일주).
        basis: 학파 기준.
            - "year" (디폴트): 자평진전 정통 — 연주 지지 기준
            - "day": 명리정종 학파 — 일주 지지 기준

    Returns:
        {신살명: {ji: 지지 한자, han: 신살 한자}} 12건.
        잘못된 basis 또는 입력 시 빈 dict.
    """
    if basis not in ("year", "day"):
        return {}
    return get_sinsal_for_year(branch_ji)


def detect_sinsal_in_pillars(
    year_ji: str,
    pillar_ji_list: List[str],
    basis: str = "year",
) -> Dict[str, List[str]]:
    """4주 지지에 출현한 12 신살 매칭.

    Args:
        year_ji: 기준 지지 한자 (basis="year" 시 연주, basis="day" 시 일주).
        pillar_ji_list: 4주 지지 한자 리스트 (예: 4주 모두 또는 일부).
        basis: 학파 기준.
            - "year" (디폴트): 자평진전 정통 — 연주 기준
            - "day": 명리정종 학파 — 일주 기준
            매핑 룰은 동일 — 의미 라벨만 다름 (caller 결단).

    Returns:
        {신살명: [매칭된 지지 한자 리스트]} 12건.
        매칭 없으면 빈 리스트. 잘못된 basis 시 빈 dict 12건.

    Examples:
        >>> # 申子辰 수국 + 4주에 子·亥·辰·未 있는 사주
        >>> result = detect_sinsal_in_pillars("子", ["子", "亥", "辰", "未"])
        >>> result["장성살"]  # 자子 = 장성
        ['子']
        >>> result["천살"]  # 未未 = 천살
        ['未']
    """
    if basis not in ("year", "day"):
        return {name: [] for name in _SINSAL_ORDER}
    base_mapping = _build_sinsal_mapping(year_ji)
    if not base_mapping:
        return {name: [] for name in _SINSAL_ORDER}
    out: Dict[str, List[str]] = {}
    for sinsal_name, target_ji in base_mapping.items():
        out[sinsal_name] = [ji for ji in pillar_ji_list if ji == target_ji]
    return out


# 흐름 톤 (ADR-006 단정 어휘 차단 정합)
SINSAL_FLOW_TONE: Dict[str, Dict[str, str]] = {
    "겁살": {"label": "겁살", "summary": "외부 자극·변화의 결. 의도하지 않은 상황 변화."},
    "재살": {"label": "재살", "summary": "급변·격동의 결. 강한 변동 흐름."},
    "천살": {"label": "천살", "summary": "하늘의 결. 인력으로 통제하기 어려운 흐름."},
    "지살": {"label": "지살", "summary": "이동·환경 변화의 결. 새로운 자리로의 이동."},
    "년살": {"label": "년살", "summary": "도화의 결 (별칭 도화살). 매력·인기 흐름."},
    "월살": {"label": "월살", "summary": "정체·답답함의 결. 흐름의 잠시 멈춤."},
    "망신살": {"label": "망신살", "summary": "자기 노출의 결. 숨겨진 일이 드러나는 흐름."},
    "장성살": {"label": "장성살", "summary": "리더십·통솔의 결. 중심 자리의 흐름."},
    "반안살": {"label": "반안살", "summary": "안정·여유의 결. 평온한 자리의 흐름."},
    "역마살": {"label": "역마살", "summary": "이동·여행의 결. 활동 반경이 넓은 흐름."},
    "육해살": {"label": "육해살", "summary": "방해·지연의 결. 흐름이 더디게 풀리는 자리."},
    "화개살": {"label": "화개살", "summary": "예술·종교·학문의 결. 정신적 깊이의 흐름."},
}


__all__ = [
    "get_sinsal_for_year",
    "detect_sinsal_in_pillars",
    "SINSAL_FLOW_TONE",
]
