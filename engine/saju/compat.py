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


# ADR-130 지지 삼합(三合) 4국 — 자평진전·삼명통회 정통 표준 일치
# 화국: 申子辰 → 水局 (수국)
# 금국: 巳酉丑 → 金局 (금국)
# 화국: 寅午戌 → 火局 (화국)
# 목국: 亥卯未 → 木局 (목국)
_BRANCH_SAMHAP = {
    frozenset({"申", "子", "辰"}): {"label": "申子辰", "guk": "水局", "ohaeng": "수"},
    frozenset({"巳", "酉", "丑"}): {"label": "巳酉丑", "guk": "金局", "ohaeng": "금"},
    frozenset({"寅", "午", "戌"}): {"label": "寅午戌", "guk": "火局", "ohaeng": "화"},
    frozenset({"亥", "卯", "未"}): {"label": "亥卯未", "guk": "木局", "ohaeng": "목"},
}

# ADR-130 지지 방합(方合) 4국 — 자평진전·삼명통회 정통 표준 일치
# 춘목국: 寅卯辰 → 春木 (봄·동방·木)
# 하화국: 巳午未 → 夏火 (여름·남방·火)
# 추금국: 申酉戌 → 秋金 (가을·서방·金)
# 동수국: 亥子丑 → 冬水 (겨울·북방·水)
_BRANCH_BANGHAP = {
    frozenset({"寅", "卯", "辰"}): {"label": "寅卯辰", "guk": "春木", "ohaeng": "목", "direction": "동방"},
    frozenset({"巳", "午", "未"}): {"label": "巳午未", "guk": "夏火", "ohaeng": "화", "direction": "남방"},
    frozenset({"申", "酉", "戌"}): {"label": "申酉戌", "guk": "秋金", "ohaeng": "금", "direction": "서방"},
    frozenset({"亥", "子", "丑"}): {"label": "亥子丑", "guk": "冬水", "ohaeng": "수", "direction": "북방"},
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

    # MBTI 호환 (ADR-090: 점수 제거 → 학파 라벨만)
    # Socionics + Type Dynamics 학파 분류 — 단일 학파 단정 X (ADR-002)
    mbti_label = None
    if mbti_a and mbti_b:
        mbti_label = _mbti_socionics_label(mbti_a, mbti_b)

    # 음령오행 결합 (이름)
    name_flow = None
    if myeong_a and myeong_b:
        wxa = myeong_a.get("combined_wuxing_dist") or myeong_a.get("wuxing_dist") or {}
        wxb = myeong_b.get("combined_wuxing_dist") or myeong_b.get("wuxing_dist") or {}
        name_flow = _wuxing_compat(wxa, wxb)

    # ADR-090: 0~100점 score + 최상/상/중/하/최하 grade 단정 제거.
    # 사주 단독에서는 "좋은/안 좋은 사주" 단정 차단하면서 궁합에서만 점수 단정은
    # ADR 일관성 결손. 본 버전은 명리학 통설 결정론 라벨만 회신.
    # 사용자 출력: 합/충/형/파/해 명칭 + 상생/상극 흐름 + 양면 해석 (LLM 책임).

    return {
        # ADR-090: score·grade 키 의도적 부재 — 단정 차단
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
            "socionics_label": mbti_label,  # ADR-090: 점수 → 학파 라벨
        } if mbti_a and mbti_b else None,
        "name_flow": name_flow,
        "disclaimer": (
            "본 궁합 분석은 명리학 통설 (합·충·형·파·해) + Socionics MBTI 분류 결정론 라벨이며 "
            "관계 성공·실패·이별·결혼 단정 X. 사용자 인생 결정의 단독 근거 X (ADR-006·010·014)."
        ),
    }


# ADR-090: MBTI 16x16 Socionics 학파 라벨 (점수 X)
_MBTI_SOCIONICS_RELATIONS = {
    # Duality (보완)
    "INTJ-ENFP": "Duality (보완)", "INTP-ENTJ": "Duality (보완)",
    "ENTJ-INFP": "Duality (보완)", "ENTP-INFJ": "Duality (보완)",
    "INFJ-ENTP": "Duality (보완)", "INFP-ENTJ": "Duality (보완)",
    "ENFJ-INTP": "Duality (보완)", "ENFP-INTJ": "Duality (보완)",
    "ISTJ-ESFP": "Duality (보완)", "ISFJ-ESTP": "Duality (보완)",
    "ESTJ-ISFP": "Duality (보완)", "ESFJ-ISTP": "Duality (보완)",
    "ISTP-ESFJ": "Duality (보완)", "ISFP-ESTJ": "Duality (보완)",
    "ESTP-ISFJ": "Duality (보완)", "ESFP-ISTJ": "Duality (보완)",
    # Identity (동일)
    "INTJ-INTJ": "Identity (동일)", "INTP-INTP": "Identity (동일)",
    "ENTJ-ENTJ": "Identity (동일)", "ENTP-ENTP": "Identity (동일)",
    "INFJ-INFJ": "Identity (동일)", "INFP-INFP": "Identity (동일)",
    "ENFJ-ENFJ": "Identity (동일)", "ENFP-ENFP": "Identity (동일)",
    "ISTJ-ISTJ": "Identity (동일)", "ISFJ-ISFJ": "Identity (동일)",
    "ESTJ-ESTJ": "Identity (동일)", "ESFJ-ESFJ": "Identity (동일)",
    "ISTP-ISTP": "Identity (동일)", "ISFP-ISFP": "Identity (동일)",
    "ESTP-ESTP": "Identity (동일)", "ESFP-ESFP": "Identity (동일)",
}


def _mbti_socionics_label(a: str, b: str) -> str:
    """ADR-090: MBTI 두 유형 → Socionics 학파 분류 라벨.

    Returns:
        "Duality (보완)" | "Identity (동일)" | "Standard (표준)"
    Notes:
        Socionics 학파 단일 채택. ADR-002 정합 — 명시적 학파 라벨로 단정 차단.
        호환 "점수" 회신 X. 분류 명칭만 회신.
    """
    a, b = a.upper().strip(), b.upper().strip()
    key1 = f"{a}-{b}"
    key2 = f"{b}-{a}"
    label = _MBTI_SOCIONICS_RELATIONS.get(key1) or _MBTI_SOCIONICS_RELATIONS.get(key2)
    return label or "Standard (표준)"


# ─────────────────────────── ADR-130 삼합·방합 API ───────────────────────────


def detect_samhap(branches: list[str]) -> list[dict]:
    """4주 지지 한자 리스트 → 삼합(三合) 완전 4국 매칭 결과.

    학파: 자평진전·삼명통회 정통 표준 일치.
    학술 출처: 본 시스템 shensha.py _TRIPLES 동일 매핑 검증.

    Args:
        branches: 4주 지지 한자 리스트 (例: ["子", "卯", "申", "辰"]).

    Returns:
        매칭된 삼합 국 정보 리스트. 4 지지 모두 한 국에 포함되어야 매칭.
        부분 매칭(반합·2지지만 일치)은 X.
        [{"label": "申子辰", "guk": "水局", "ohaeng": "수"}, ...]
    """
    if not branches:
        return []
    branch_set = set(branches)
    out = []
    for samhap_set, info in _BRANCH_SAMHAP.items():
        if samhap_set.issubset(branch_set):
            out.append(dict(info))
    return out


def detect_banghap(branches: list[str]) -> list[dict]:
    """4주 지지 한자 리스트 → 방합(方合) 완전 4국 매칭 결과.

    학파: 자평진전·삼명통회 정통 표준 일치.

    Args:
        branches: 4주 지지 한자 리스트.

    Returns:
        매칭된 방합 국 정보 리스트.
        [{"label": "寅卯辰", "guk": "春木", "ohaeng": "목", "direction": "동방"}, ...]
    """
    if not branches:
        return []
    branch_set = set(branches)
    out = []
    for banghap_set, info in _BRANCH_BANGHAP.items():
        if banghap_set.issubset(branch_set):
            out.append(dict(info))
    return out


def detect_compat_relations(branches: list[str]) -> dict:
    """4주 지지 합국·합충 일괄 매칭 (삼합·방합·6합·6충 통합).

    Returns:
        {
          "samhap": [...],        # 삼합 매칭 4국
          "banghap": [...],       # 방합 매칭 4국
          "yukhap_pairs": [...],  # 6합 쌍 라벨
          "yukchong_pairs": [...],# 6충 쌍 라벨
        }
    """
    samhap = detect_samhap(branches)
    banghap = detect_banghap(branches)

    # 6합·6충 쌍 점검
    yukhap_pairs = []
    yukchong_pairs = []
    n = len(branches)
    for i in range(n):
        for j in range(i + 1, n):
            pair = frozenset({branches[i], branches[j]})
            if pair in _BRANCH_HE:
                yukhap_pairs.append(_BRANCH_HE[pair])
            if pair in _BRANCH_CHONG:
                yukchong_pairs.append(_BRANCH_CHONG[pair])

    return {
        "samhap": samhap,
        "banghap": banghap,
        "yukhap_pairs": yukhap_pairs,
        "yukchong_pairs": yukchong_pairs,
    }


__all__ = ["analyze_compat", "detect_samhap", "detect_banghap", "detect_compat_relations"]
