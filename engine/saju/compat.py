"""두 사람 사주 + MBTI + 이름 → 궁합 결정론 분석.

핵심 축:
  1. 일간 천간 합/충
  2. 일지 지지 합/충/형/파/해
  3. 오행 전체 분포 상생/상극
  4. MBTI 16×16 호환 매트릭스
  5. 음령오행 결합 (이름)
"""

from __future__ import annotations

from typing import Any

# 천간 5합 (음양 결합)
_STEM_HE = {
    frozenset({"甲", "己"}): "甲己合土",
    frozenset({"乙", "庚"}): "乙庚合金",
    frozenset({"丙", "辛"}): "丙辛合水",
    frozenset({"丁", "壬"}): "丁壬合木",
    frozenset({"戊", "癸"}): "戊癸合火",
}

# 천간 4충
_STEM_CHONG = {
    frozenset({"甲", "庚"}): "甲庚沖",
    frozenset({"乙", "辛"}): "乙辛沖",
    frozenset({"丙", "壬"}): "丙壬沖",
    frozenset({"丁", "癸"}): "丁癸沖",
}

# 지지 6합
_BRANCH_HE = {
    frozenset({"子", "丑"}): "子丑合土",
    frozenset({"寅", "亥"}): "寅亥合木",
    frozenset({"卯", "戌"}): "卯戌合火",
    frozenset({"辰", "酉"}): "辰酉合金",
    frozenset({"巳", "申"}): "巳申合水",
    frozenset({"午", "未"}): "午未合(火土)",
}

# 지지 6충
_BRANCH_CHONG = {
    frozenset({"子", "午"}): "子午沖",
    frozenset({"丑", "未"}): "丑未沖",
    frozenset({"寅", "申"}): "寅申沖",
    frozenset({"卯", "酉"}): "卯酉沖",
    frozenset({"辰", "戌"}): "辰戌沖",
    frozenset({"巳", "亥"}): "巳亥沖",
}

# 지지 형 (대표)
_BRANCH_HYUNG = {
    frozenset({"寅", "巳"}): "寅巳刑",
    frozenset({"巳", "申"}): "巳申刑",  # 합이자 형
    frozenset({"丑", "戌"}): "丑戌刑",
    frozenset({"戌", "未"}): "戌未刑",
    frozenset({"子", "卯"}): "子卯刑",
}

# 지지 파
_BRANCH_PA = {
    frozenset({"子", "酉"}): "子酉破",
    frozenset({"丑", "辰"}): "丑辰破",
    frozenset({"寅", "亥"}): "寅亥破",
    frozenset({"卯", "午"}): "卯午破",
    frozenset({"巳", "申"}): "巳申破",
    frozenset({"未", "戌"}): "未戌破",
}

# 지지 해 (원진)
_BRANCH_HAE = {
    frozenset({"子", "未"}): "子未害",
    frozenset({"丑", "午"}): "丑午害",
    frozenset({"寅", "巳"}): "寅巳害",
    frozenset({"卯", "辰"}): "卯辰害",
    frozenset({"申", "亥"}): "申亥害",
    frozenset({"酉", "戌"}): "酉戌害",
}

# 오행 상생 (생하는 관계)
_WX_GENERATE = {"목": "화", "화": "토", "토": "금", "금": "수", "수": "목"}
# 오행 상극 (극하는 관계)
_WX_CONTROL = {"목": "토", "토": "수", "수": "화", "화": "금", "금": "목"}


# MBTI 16×16 호환 매트릭스 (간이 — 인지 기능 거울/짝 기준)
# Socionics + Type Dynamics 결합한 한국 대중 매핑
_MBTI_PAIR_SCORE = {
    # 듀얼 (Best) — 8쌍
    "INTJ-ENFP": 9, "INTP-ENTJ": 9, "ENTJ-INFP": 9, "ENTP-INFJ": 9,
    "INFJ-ENTP": 9, "INFP-ENTJ": 9, "ENFJ-INTP": 9, "ENFP-INTJ": 9,
    "ISTJ-ESFP": 9, "ISFJ-ESTP": 9, "ESTJ-ISFP": 9, "ESFJ-ISTP": 9,
    "ISTP-ESFJ": 9, "ISFP-ESTJ": 9, "ESTP-ISFJ": 9, "ESFP-ISTJ": 9,
    # 자가 (Identity) — 같은 유형
    "INTJ-INTJ": 7, "INTP-INTP": 7, "ENTJ-ENTJ": 7, "ENTP-ENTP": 7,
    "INFJ-INFJ": 7, "INFP-INFP": 7, "ENFJ-ENFJ": 7, "ENFP-ENFP": 7,
    "ISTJ-ISTJ": 7, "ISFJ-ISFJ": 7, "ESTJ-ESTJ": 7, "ESFJ-ESFJ": 7,
    "ISTP-ISTP": 7, "ISFP-ISFP": 7, "ESTP-ESTP": 7, "ESFP-ESFP": 7,
}


def _mbti_score(a: str, b: str) -> int:
    """MBTI 두 유형 호환 점수 (1~9). 매트릭스에 없으면 6 (보통)."""
    a, b = a.upper().strip(), b.upper().strip()
    key1 = f"{a}-{b}"
    key2 = f"{b}-{a}"
    return _MBTI_PAIR_SCORE.get(key1) or _MBTI_PAIR_SCORE.get(key2) or 6


def _wuxing_compat(a: dict, b: dict) -> dict:
    """두 사람 오행 분포 → 상생/상극 흐름."""
    pos, neg = [], []
    for k, v in a.items():
        if v == 0:
            continue
        gen_target = _WX_GENERATE.get(k)
        ctrl_target = _WX_CONTROL.get(k)
        if gen_target and b.get(gen_target, 0) > 0:
            pos.append(f"A의 {k} → B의 {gen_target} 生 (상생)")
        if ctrl_target and b.get(ctrl_target, 0) > 0:
            neg.append(f"A의 {k} → B의 {ctrl_target} 剋 (상극)")
    return {"positive": pos[:5], "negative": neg[:5]}


def _branch_relations(b1: str, b2: str) -> list[str]:
    """두 지지 간 관계 (합/충/형/파/해 검사)."""
    pair = frozenset({b1, b2})
    out = []
    if b1 == b2:
        return ["같은 지지 (자형 가능)"]
    for table, label in [
        (_BRANCH_HE, "合"),
        (_BRANCH_CHONG, "沖"),
        (_BRANCH_HYUNG, "刑"),
        (_BRANCH_PA, "破"),
        (_BRANCH_HAE, "害"),
    ]:
        if pair in table:
            out.append(table[pair])
    return out


def _extract_day_pillar(saju: dict) -> tuple[str, str]:
    """SajuCLI assess 결과 → 일주 (천간, 지지) 한자."""
    day_label = saju.get("day", "")  # 형식 "을해(乙亥)" 또는 "乙亥"
    han_chars = [c for c in day_label if "一" <= c <= "鿿"]
    if len(han_chars) >= 2:
        return han_chars[0], han_chars[1]
    return saju.get("day_master", "?"), "?"


def analyze_compat(
    saju_a: dict[str, Any],
    saju_b: dict[str, Any],
    mbti_a: str | None = None,
    mbti_b: str | None = None,
    myeong_a: dict[str, Any] | None = None,
    myeong_b: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """두 사람 결정론 궁합 분석."""
    # 일주 (천간, 지지) 추출
    stem_a, branch_a = _extract_day_pillar(saju_a)
    stem_b, branch_b = _extract_day_pillar(saju_b)

    # 천간 합/충
    stem_pair = frozenset({stem_a, stem_b})
    stem_he = _STEM_HE.get(stem_pair)
    stem_chong = _STEM_CHONG.get(stem_pair)
    stem_relations = []
    if stem_he:
        stem_relations.append({"type": "合", "label": stem_he})
    if stem_chong:
        stem_relations.append({"type": "沖", "label": stem_chong})
    if stem_a == stem_b:
        stem_relations.append({"type": "同", "label": f"{stem_a}{stem_b} 동일 일간"})

    # 지지 합/충/형/파/해
    branch_relations = _branch_relations(branch_a, branch_b)

    # 오행 흐름
    wx_a = saju_a.get("wuxing_dist", {})
    wx_b = saju_b.get("wuxing_dist", {})
    wx_flow = _wuxing_compat(wx_a, wx_b)

    # MBTI 호환
    mbti_score = None
    if mbti_a and mbti_b:
        mbti_score = _mbti_score(mbti_a, mbti_b)

    # 음령오행 결합 (이름)
    name_flow = None
    if myeong_a and myeong_b:
        wxa = myeong_a.get("combined_wuxing_dist") or myeong_a.get("wuxing_dist") or {}
        wxb = myeong_b.get("combined_wuxing_dist") or myeong_b.get("wuxing_dist") or {}
        name_flow = _wuxing_compat(wxa, wxb)

    # 점수 산정 (0~100)
    score = 50  # 기준
    if stem_he:
        score += 10
    if stem_chong:
        score -= 10
    for rel in branch_relations:
        if "合" in rel:
            score += 8
        elif "沖" in rel:
            score -= 8
        elif "刑" in rel:
            score -= 5
        elif "破" in rel:
            score -= 4
        elif "害" in rel:
            score -= 3
    score += min(15, len(wx_flow["positive"]) * 3)
    score -= min(15, len(wx_flow["negative"]) * 3)
    if mbti_score is not None:
        score += (mbti_score - 6) * 3  # 9점 → +9, 6점 → 0
    if name_flow:
        score += min(8, len(name_flow["positive"]) * 2)
        score -= min(8, len(name_flow["negative"]) * 2)
    score = max(0, min(100, score))

    if score >= 75:
        grade = "최상"
    elif score >= 60:
        grade = "상"
    elif score >= 45:
        grade = "중"
    elif score >= 30:
        grade = "하"
    else:
        grade = "최하"

    return {
        "score": score,
        "grade": grade,
        "stem": {
            "a": stem_a,
            "b": stem_b,
            "relations": stem_relations,
        },
        "branch": {
            "a": branch_a,
            "b": branch_b,
            "relations": branch_relations,
        },
        "wuxing_flow": wx_flow,
        "mbti": {
            "a": mbti_a,
            "b": mbti_b,
            "score": mbti_score,
        } if mbti_a and mbti_b else None,
        "name_flow": name_flow,
    }


__all__ = ["analyze_compat"]
