"""천살(天殺) 방위 결정론 산출.

학술 근거 (ADR-122):
  - 메트로신문 김상회 칼럼 (2021-12-12) — 제사 통하는 방향
    https://api.emetro.co.kr/article/20211212500014
  - 한국 사주명리 십이신살 정통 풀
  - 출생 연도 지지 삼합 → 천살 방위 매핑

매핑 규칙 (4 삼합 → 천살 지지):
  - 申子辰 (수국)       → 未 (남남서)
  - 巳酉丑 (금국)       → 辰 (동남동)
  - 寅午戌 (화국)       → 丑 (북북동)
  - 亥卯未 (목국)       → 戌 (서북서)

본 함수는 사용자 출생 연도 地支 한자를 입력받아 천살 방위(지지 + 도)를 반환.
조상 묘 방위·제사 헌작 방위 안내용 결정론 산출만 제공.
"""
from __future__ import annotations

from typing import Dict, Tuple


# 4 삼합 → 천살 지지 매핑 (정통 사주명리 십이신살)
_SAMHAP_TO_CHEONSAL: Dict[Tuple[str, str, str], str] = {
    ("申", "子", "辰"): "未",
    ("巳", "酉", "丑"): "辰",
    ("寅", "午", "戌"): "丑",
    ("亥", "卯", "未"): "戌",
}

# 지지 한자 → 방위 한글 + 도(0~359, 정북=0, 시계방향)
_JI_TO_DIRECTION: Dict[str, Tuple[str, int]] = {
    "子": ("정북", 0),
    "丑": ("북북동", 30),
    "寅": ("동북동", 60),
    "卯": ("정동", 90),
    "辰": ("동남동", 120),
    "巳": ("남남동", 150),
    "午": ("정남", 180),
    "未": ("남남서", 210),
    "申": ("서남서", 240),
    "酉": ("정서", 270),
    "戌": ("서북서", 300),
    "亥": ("북북서", 330),
}

# 출생 연도 지지 한자 → 천살 결과 (사전 빌드, O(1) 룩업)
CHEONSAL_DIRECTIONS_BY_YEAR_JI: Dict[str, Dict[str, object]] = {}
for samhap, cheonsal_ji in _SAMHAP_TO_CHEONSAL.items():
    direction_ko, degree = _JI_TO_DIRECTION[cheonsal_ji]
    for year_ji in samhap:
        CHEONSAL_DIRECTIONS_BY_YEAR_JI[year_ji] = {
            "cheonsal_ji": cheonsal_ji,
            "direction_ko": direction_ko,
            "direction_degree": degree,
            "samhap": "".join(samhap),
        }


def get_cheonsal_direction(year_ji_han: str) -> Dict[str, object]:
    """출생 연도 지지 한자 → 천살 방위 결정론 산출.

    Args:
        year_ji_han: 출생 연도 지지 한자 (子·丑·寅·卯·辰·巳·午·未·申·酉·戌·亥)

    Returns:
        dict: {
            "cheonsal_ji": 천살 지지 한자,
            "direction_ko": 방위 한글 (정북·북북동 등 12 방위),
            "direction_degree": 방위 도 (0~330, 30 간격),
            "samhap": 삼합 한자 (예: "申子辰"),
            "school": "정통 사주명리 십이신살",
            "disclaimer": "참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다.",
        }

    Raises:
        ValueError: year_ji_han이 12 지지 한자가 아닐 때.
    """
    if year_ji_han not in CHEONSAL_DIRECTIONS_BY_YEAR_JI:
        raise ValueError(
            f"year_ji_han '{year_ji_han}'은 12 지지 한자가 아닙니다 "
            f"(子丑寅卯辰巳午未申酉戌亥 중 1)."
        )
    result = dict(CHEONSAL_DIRECTIONS_BY_YEAR_JI[year_ji_han])
    result["school"] = "정통 사주명리 십이신살"
    result["disclaimer"] = (
        "참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다."
    )
    return result
