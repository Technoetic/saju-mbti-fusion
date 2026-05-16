# -*- coding: utf-8 -*-
"""신살(神煞) 계산 모듈.

주요 신살 5종:
  - 천을귀인(天乙貴人)
  - 문창귀인(文昌貴人)
  - 역마(驛馬)
  - 도화(桃花)
  - 공망(空亡)
"""
from __future__ import annotations

from typing import Dict, List

# 천간/지지 한자 시퀀스
_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
_JI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 일간 -> 천을귀인 지지 목록
_CHEONEUL: Dict[str, List[str]] = {
    "甲": ["丑", "未"],
    "戊": ["丑", "未"],
    "庚": ["丑", "未"],
    "乙": ["子", "申"],
    "己": ["子", "申"],
    "丙": ["亥", "酉"],
    "丁": ["亥", "酉"],
    "壬": ["卯", "巳"],
    "癸": ["卯", "巳"],
    "辛": ["寅", "午"],
}

# 일간 -> 문창귀인 지지
_MUNCHANG: Dict[str, str] = {
    "甲": "巳",
    "乙": "午",
    "丙": "申",
    "戊": "申",
    "丁": "酉",
    "己": "酉",
    "庚": "亥",
    "辛": "子",
    "壬": "寅",
    "癸": "卯",
}

# 삼합 기준 역마/도화 (年支·日支 기준 트리거 지지군)
_TRIPLES = {
    ("申", "子", "辰"): {"yeokma": "寅", "dohwa": "酉"},
    ("巳", "酉", "丑"): {"yeokma": "亥", "dohwa": "午"},
    ("寅", "午", "戌"): {"yeokma": "申", "dohwa": "卯"},
    ("亥", "卯", "未"): {"yeokma": "巳", "dohwa": "子"},
}

# 旬 -> 공망 지지 2개 (인덱스 // 10)
_KONGMANG_BY_SUN: List[List[str]] = [
    ["戌", "亥"],  # 甲子旬 (0~9)
    ["申", "酉"],  # 甲戌旬 (10~19)
    ["午", "未"],  # 甲申旬 (20~29)
    ["辰", "巳"],  # 甲午旬 (30~39)
    ["寅", "卯"],  # 甲辰旬 (40~49)
    ["子", "丑"],  # 甲寅旬 (50~59)
]


# 60갑자 인덱스 사전 빌드 (모듈 로드 시 1회). O(1) 룩업.
# (gan_han, ji_han) -> 60갑자 인덱스 (0~59)
_GAPJA_INDEX: Dict[tuple, int] = {}
for _i in range(60):
    _GAPJA_INDEX[(_GAN[_i % 10], _JI[_i % 12])] = _i
del _i


def _ganzhi_index(gan_han: str, ji_han: str) -> int:
    """천간·지지 한자 -> 60갑자 인덱스 (0~59). O(1) dict 룩업."""
    return _GAPJA_INDEX.get((gan_han, ji_han), -1)


def _ji_list(pillars: Dict) -> List[str]:
    """4주 지지 한자 리스트."""
    return [
        pillars["year_pillar"]["ji_han"],
        pillars["month_pillar"]["ji_han"],
        pillars["day_pillar"]["ji_han"],
        pillars["hour_pillar"]["ji_han"],
    ]


def compute_shensha(pillars: Dict) -> Dict[str, List[str]]:
    """4주(年月日時)에서 주요 신살 5종을 계산.

    Args:
        pillars: {year_pillar, month_pillar, day_pillar, hour_pillar} —
                 각 항목은 {gan_han, ji_han, gan, ji}.

    Returns:
        {cheoneul, munchang, yeokma, dohwa, kongmang}: 각 키 값은
        해당 신살에 해당하는 지지(한자) 리스트, 없으면 빈 리스트.
    """
    day_gan = pillars["day_pillar"]["gan_han"]
    day_ji = pillars["day_pillar"]["ji_han"]
    year_ji = pillars["year_pillar"]["ji_han"]
    all_ji = _ji_list(pillars)

    # 1. 천을귀인
    cheoneul_targets = set(_CHEONEUL.get(day_gan, []))
    cheoneul = [j for j in all_ji if j in cheoneul_targets]

    # 2. 문창귀인
    munchang_target = _MUNCHANG.get(day_gan)
    munchang = [j for j in all_ji if munchang_target and j == munchang_target]

    # 3·4. 역마/도화 (年支·日支 모두 트리거로 사용)
    yeokma_targets: set = set()
    dohwa_targets: set = set()
    for base_ji in (year_ji, day_ji):
        for triple, mapping in _TRIPLES.items():
            if base_ji in triple:
                yeokma_targets.add(mapping["yeokma"])
                dohwa_targets.add(mapping["dohwa"])
    yeokma = [j for j in all_ji if j in yeokma_targets]
    dohwa = [j for j in all_ji if j in dohwa_targets]

    # 5. 공망 (일주 60갑자 -> 旬 -> 공망 2지지)
    idx = _ganzhi_index(day_gan, day_ji)
    if idx >= 0:
        sun_idx = idx // 10
        kongmang_targets = set(_KONGMANG_BY_SUN[sun_idx])
        kongmang = [j for j in all_ji if j in kongmang_targets]
    else:
        kongmang = []

    return {
        "cheoneul": cheoneul,
        "munchang": munchang,
        "yeokma": yeokma,
        "dohwa": dohwa,
        "kongmang": kongmang,
    }


# 신살 한 줄 의미 — 프론트가 태그 옆에 표시할 용도
SHENSHA_MEANINGS: Dict[str, Dict[str, str]] = {
    "cheoneul": {
        "label": "천을귀인",
        "summary": "어려울 때 도와주는 귀인이 있는 길성. 위기에서 인복으로 활로가 열림.",
    },
    "munchang": {
        "label": "문창귀인",
        "summary": "학문·창작·시험에 강한 별. 두뇌 회전이 빠르고 글·말 재능이 있음.",
    },
    "yeokma": {
        "label": "역마살",
        "summary": "이동·변화·여행이 잦은 별. 한 곳에 머물지 않고 활동 반경이 넓음.",
    },
    "dohwa": {
        "label": "도화살",
        "summary": "매력·예술성·인기. 이성에게 끌리고 끌어당기는 힘이 강함.",
    },
    "kongmang": {
        "label": "공망",
        "summary": "비어있는 자리. 해당 영역(재물·자식·관운 등)에서 헛수고와 허무함을 자주 만남.",
    },
}
