"""오행(五行) 분포 계산.

天干 1점 + 地支 지장간 가중치 합산. 4기둥 = 8.0점.
"""

STEM_WUXING = {
    "甲": "목",
    "乙": "목",
    "丙": "화",
    "丁": "화",
    "戊": "토",
    "己": "토",
    "庚": "금",
    "辛": "금",
    "壬": "수",
    "癸": "수",
}

BRANCH_HIDDEN = {
    "寅": [("甲", 0.6), ("丙", 0.2), ("戊", 0.2)],
    "卯": [("乙", 1.0)],
    "辰": [("戊", 0.5), ("乙", 0.3), ("癸", 0.2)],
    "巳": [("丙", 0.6), ("戊", 0.2), ("庚", 0.2)],
    "午": [("丁", 0.7), ("己", 0.3)],
    "未": [("己", 0.5), ("丁", 0.3), ("乙", 0.2)],
    "申": [("庚", 0.6), ("壬", 0.2), ("戊", 0.2)],
    "酉": [("辛", 1.0)],
    "戌": [("戊", 0.5), ("辛", 0.3), ("丁", 0.2)],
    "亥": [("壬", 0.7), ("甲", 0.3)],
    "子": [("癸", 1.0)],
    "丑": [("己", 0.5), ("癸", 0.3), ("辛", 0.2)],
}


def wuxing_dist(pillars: dict) -> dict:
    """4기둥(年月日時)에서 오행 분포 계산.

    Args:
        pillars: {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"}

    Returns:
        {"목": x, "화": y, "토": z, "금": w, "수": v} (합 ≈ 8.0)
    """
    dist = {"목": 0.0, "화": 0.0, "토": 0.0, "금": 0.0, "수": 0.0}

    for key in ("year", "month", "day", "hour"):
        gz = pillars.get(key, "")
        if len(gz) < 2:
            continue
        stem, branch = gz[0], gz[1]

        if stem in STEM_WUXING:
            dist[STEM_WUXING[stem]] += 1.0

        for hidden_stem, weight in BRANCH_HIDDEN.get(branch, []):
            if hidden_stem in STEM_WUXING:
                dist[STEM_WUXING[hidden_stem]] += weight

    return {k: round(v, 1) for k, v in dist.items()}
