"""사주 결과 → 결정론적 별칭 (MBTI 의 '전략가' 같은 한 줄 페르소나).

입력:
    day_master (한자 1글자, 10간)
    wuxing_dist (5오행 dict)
    pattern (격국 한국어 명칭, None 가능)

출력:
    {
        "headline": "강철 정원사",        # 짧은 페르소나 명
        "subtitle": "금속 사이의 등나무",  # 1줄 비유
        "summary": "...",                 # 2~3문장 설명
        "tags": ["lead", "balance"],      # 보조 라벨 (UI 색)
    }
"""

from __future__ import annotations

from typing import Any

# 10간 기본 페르소나 (일간 자체)
_DAY_MASTER_BASE = {
    "甲": {"name": "큰 나무", "trait": "곧고 우직한 성장형"},
    "乙": {"name": "넝쿨 화초", "trait": "유연하고 끈질긴 적응형"},
    "丙": {"name": "태양", "trait": "환하게 비추는 표현형"},
    "丁": {"name": "촛불", "trait": "집중력 깊은 섬세형"},
    "戊": {"name": "큰 산", "trait": "중심 잡는 신중형"},
    "己": {"name": "밭흙", "trait": "현실적이고 돌봄형"},
    "庚": {"name": "강철", "trait": "기준이 분명한 결단형"},
    "辛": {"name": "보석", "trait": "정교한 완성도 추구형"},
    "壬": {"name": "큰 강", "trait": "유연하고 지혜로운 흐름형"},
    "癸": {"name": "이슬과 비", "trait": "감각적이고 관찰력 깊은 형"},
}

# 가장 강한 오행 → 형용사
_DOMINANT_WX = {
    "목": "푸른 숲의",
    "화": "타오르는",
    "토": "단단한 대지의",
    "금": "강철의",
    "수": "깊은 물의",
}

# 가장 약한 오행 → 보완 키워드
_WEAKEST_WX = {
    "목": "성장과 인내",
    "화": "표현과 열정",
    "토": "안정과 신뢰",
    "금": "기준과 결단",
    "수": "지혜와 휴식",
}

# 격국 → 페르소나 후위
_PATTERN_SUFFIX = {
    "정관격": "원칙의 수호자",
    "편관격": "도전의 검객",
    "정재격": "현실의 경영자",
    "편재격": "기회의 사냥꾼",
    "정인격": "지식의 수도자",
    "편인격": "통찰의 탐험가",
    "식신격": "표현의 예술가",
    "상관격": "혁신의 발명가",
    "비견격": "독립의 개척자",
    "겁재격": "경쟁의 도전자",
    "건록격": "자립의 장인",
    "양인격": "강단의 행동가",
}


def compute_alias(saju: dict[str, Any]) -> dict[str, Any]:
    """사주 결과 dict → 별칭 + 짧은 설명."""
    dm_han = (saju.get("day_master") or "?").strip()
    base = _DAY_MASTER_BASE.get(dm_han, {"name": "고유한 존재", "trait": "독자적 흐름형"})

    wx = saju.get("wuxing_dist") or {}
    if wx:
        strongest = max(wx, key=lambda k: wx[k])
        weakest = min(wx, key=lambda k: wx[k])
    else:
        strongest = weakest = "?"

    pattern = (saju.get("pattern") or "").strip()
    suffix = _PATTERN_SUFFIX.get(pattern, "균형의 탐구자")

    dominant_adj = _DOMINANT_WX.get(strongest, "")
    weak_hint = _WEAKEST_WX.get(weakest, "")

    # 헤드라인: "{형용사} {일간 별칭} — {격국 페르소나}"
    headline = f"{dominant_adj} {base['name']}".strip()
    persona = f"{headline} · {suffix}"

    subtitle = f"일간 {dm_han}({base['trait']}) / 강한 기운: {strongest} / 보완: {weakest}"

    summary = (
        f"당신은 {base['trait']} 성향을 바탕으로 '{strongest}' 의 기운이 가장 두드러집니다. "
        f"{suffix}로서의 역할 의식이 강하며, "
        f"균형을 위해서는 '{weakest}' 의 결을 의식적으로 보강하는 것이 도움이 됩니다 "
        f"(키워드: {weak_hint})."
    )

    return {
        "persona": persona,
        "headline": headline,
        "suffix": suffix,
        "subtitle": subtitle,
        "summary": summary,
        "day_master_name": base["name"],
        "day_master_trait": base["trait"],
        "strongest": strongest,
        "weakest": weakest,
    }


# MBTI 16유형 한국어 별칭 + 트레잇
_MBTI_PERSONA = {
    "INTJ": {"alias": "전략가", "trait": "장기 비전 + 체계적 실행"},
    "INTP": {"alias": "논리학자", "trait": "분석 + 호기심"},
    "ENTJ": {"alias": "통솔자", "trait": "결단 + 조직 운영"},
    "ENTP": {"alias": "변론가", "trait": "창의 + 토론"},
    "INFJ": {"alias": "옹호자", "trait": "통찰 + 이상주의"},
    "INFP": {"alias": "중재자", "trait": "가치 지향 + 공감"},
    "ENFJ": {"alias": "선도자", "trait": "카리스마 + 이타"},
    "ENFP": {"alias": "활동가", "trait": "열정 + 자발성"},
    "ISTJ": {"alias": "현실주의자", "trait": "책임감 + 전통"},
    "ISFJ": {"alias": "수호자", "trait": "헌신 + 세심"},
    "ESTJ": {"alias": "경영자", "trait": "실용 + 관리"},
    "ESFJ": {"alias": "집정관", "trait": "사교 + 협력"},
    "ISTP": {"alias": "장인", "trait": "실용 + 기술"},
    "ISFP": {"alias": "모험가", "trait": "감각 + 예술"},
    "ESTP": {"alias": "사업가", "trait": "행동 + 현실"},
    "ESFP": {"alias": "연예인", "trait": "활달 + 즐거움"},
}

# MBTI 4축 ↔ 사주 오행 친화 매핑
_MBTI_AXIS_ELEMENTS = {
    "T": "금/수", "F": "목/화",
    "E": "화/목", "I": "수/금",
    "N": "화/목", "S": "토/금",
    "J": "금/토", "P": "수/화",
}


def _resonance(mbti: str, strongest_wx: str) -> str:
    matches = [ch for ch in mbti if strongest_wx in _MBTI_AXIS_ELEMENTS.get(ch, "")]
    return "".join(matches) if matches else "—"


# 새 페르소나 합성: 사주 일간(자연물) + MBTI 4축(수식어 4종) → 단일 명사
# 각 축의 한 면을 수식어로 사용
_AXIS_PREFIX = {
    "I": "고요한", "E": "빛나는",
    "N": "꿈꾸는", "S": "단단한",
    "T": "예리한", "F": "다정한",
    "J": "정렬된", "P": "흐르는",
}

# 사주 일간(천간) → 핵심 명사 (자연물)
_DM_NOUN = {
    "甲": "거목", "乙": "넝쿨",
    "丙": "태양", "丁": "촛불",
    "戊": "산봉우리", "己": "옥토",
    "庚": "검(劍)", "辛": "보석",
    "壬": "바다", "癸": "이슬",
}

# 강한 오행 → 영역 명사 (장소/세계)
_WX_DOMAIN = {
    "목": "숲", "화": "노을",
    "토": "고원", "금": "철광",
    "수": "심해",
}

# 강한 오행 → 행위 동사형 (역할)
_WX_ROLE = {
    "목": "키우는", "화": "비추는",
    "토": "다지는", "금": "벼리는",
    "수": "헤아리는",
}


def _synthesize_persona_name(mbti: str, dm_han: str, strongest_wx: str) -> str:
    """결정론적 융합 페르소나명 — 단일 명사구로 합성.

    구조: {축1 수식어}{축2 수식어} {오행 도메인}을 {오행 역할} {일간 자연물}
    예) INTJ + 甲 + 목 → "고요한 꿈꾸는 숲을 키우는 거목"
        ENFP + 丙 + 화 → "빛나는 꿈꾸는 노을을 비추는 태양"
    """
    # MBTI 4글자 중 첫 2축(에너지·인식) 수식어 사용 → 두 단어로 압축
    chars = list(mbti)
    pref1 = _AXIS_PREFIX.get(chars[0], "")
    pref2 = _AXIS_PREFIX.get(chars[1], "")
    domain = _WX_DOMAIN.get(strongest_wx, "세계")
    role = _WX_ROLE.get(strongest_wx, "다루는")
    noun = _DM_NOUN.get(dm_han, "존재")
    # 두 수식어가 같은 경우 한 단어만 사용
    if pref1 == pref2:
        prefix = pref1
    else:
        prefix = f"{pref1} {pref2}"
    return f"{prefix} {domain}{_obj_particle(domain)} {role} {noun}"


def _obj_particle(word: str) -> str:
    """한국어 목적격 조사 — 마지막 음절 받침 유무 판정."""
    if not word:
        return "을"
    last = word[-1]
    code = ord(last)
    if 0xAC00 <= code <= 0xD7A3:
        jong = (code - 0xAC00) % 28
        return "을" if jong else "를"
    return "을"


def compute_fusion_alias(saju: dict[str, Any], mbti: str) -> dict[str, Any]:
    """사주 + MBTI 융합 별칭."""
    mbti = (mbti or "").upper().strip()
    persona = _MBTI_PERSONA.get(mbti)
    if not persona:
        raise ValueError(f"unknown MBTI: {mbti}")

    base_alias = compute_alias(saju)
    dm_han = saju.get("day_master", "?")
    strongest = base_alias["strongest"]
    weakest = base_alias["weakest"]
    resonance = _resonance(mbti, strongest)

    fusion_headline = _synthesize_persona_name(mbti, dm_han, strongest)
    legacy_pair = f"{persona['alias']} × {base_alias['headline']}"
    fusion_subtitle = (
        f"{mbti} {persona['alias']} + 일간 {dm_han} · 강한 기운 {strongest} "
        f"→ 친화축 {resonance}  (별칭쌍: {legacy_pair})"
    )

    if resonance == "—":
        synergy = (
            f"MBTI {mbti} 의 축 어디와도 사주 강기운 '{strongest}' 의 정합은 약합니다. "
            f"두 체계가 서로 다른 면을 비추므로, 자기이해의 폭이 더 넓게 확보됩니다."
        )
    else:
        synergy = (
            f"MBTI {mbti} 의 '{resonance}' 축이 사주 강기운 '{strongest}' 과 공명합니다. "
            f"{persona['alias']} 의 기질이 사주 '{base_alias['headline']}' 색채와 결합해 "
            f"행동 양식이 한 방향으로 정렬되기 쉽습니다."
        )
    summary = (
        f"{synergy} 약한 기운 '{weakest}' 은 {persona['alias']} 의 기본 스타일에서 자주 간과되니, "
        f"의식적으로 보완할수록 안정감이 커집니다."
    )

    return {
        "persona": fusion_headline,
        "headline": fusion_headline,
        "mbti": mbti,
        "mbti_alias": persona["alias"],
        "mbti_trait": persona["trait"],
        "saju_alias": base_alias["headline"],
        "saju_suffix": base_alias["suffix"],
        "resonance_axis": resonance,
        "subtitle": fusion_subtitle,
        "summary": summary,
        "strongest": strongest,
        "weakest": weakest,
    }


# 이름 음령오행 → 페르소나 수식어 (보완도가 + 일 때 어울리는 형용사)
_NAME_PREFIX_POS = {
    "목": "푸른 가지를 품은",
    "화": "불씨를 품은",
    "토": "두터운 흙을 딛고 선",
    "금": "벼린 날을 가진",
    "수": "맑은 물길을 두른",
}

# 이름이 사주 강한 기운을 또 강화하는 경우 (보완도 -)
_NAME_PREFIX_NEG = {
    "목": "지나치게 자란 가지의",
    "화": "더 타오르는 불꽃의",
    "토": "더 깊어진 흙의",
    "금": "더 날카로워진 칼의",
    "수": "더 깊어진 물결의",
}


def _name_modifier(name_wuxing_dist: dict[str, int], complement_grade: str) -> str:
    """이름 오행 + 보완도 → 페르소나 앞에 붙는 수식어."""
    if not name_wuxing_dist:
        return ""
    # 이름에서 가장 많은 오행
    dominant = max(
        name_wuxing_dist.items(), key=lambda kv: kv[1], default=("", 0)
    )[0]
    if not dominant or name_wuxing_dist[dominant] == 0:
        return ""
    if complement_grade == "흉":
        return _NAME_PREFIX_NEG.get(dominant, "")
    return _NAME_PREFIX_POS.get(dominant, "")


def compute_fusion_alias_v2(
    saju: dict[str, Any], mbti: str, myeong: dict[str, Any] | None
) -> dict[str, Any]:
    """사주 + MBTI + 이름 (선택) → 3중 융합 별칭.

    이름이 없으면 기존 compute_fusion_alias 결과 그대로.
    이름이 있으면 헤드라인 앞에 음령오행 + 보완도 기반 수식어 추가.
    """
    base = compute_fusion_alias(saju, mbti)
    if not myeong:
        return base

    name_wx = myeong.get("wuxing_dist", {})
    comp = myeong.get("complement", {}) or {}
    grade = comp.get("grade", "평")
    modifier = _name_modifier(name_wx, grade)
    name_ko = myeong.get("name_ko", "")

    if modifier:
        new_headline = f"{modifier} {base['headline']}"
        base["headline"] = new_headline
        base["persona"] = new_headline
        base["name_modifier"] = modifier

    # subtitle 에 이름 보완 정보 추가
    if comp.get("score") is not None:
        base["subtitle"] = (
            base.get("subtitle", "")
            + f"  ·  이름({name_ko}) 보완 {comp['score']:+d}/{grade}"
        )

    base["name_ko"] = name_ko
    base["name_wuxing"] = name_wx
    base["name_complement"] = comp
    return base


__all__ = [
    "compute_alias",
    "compute_fusion_alias",
    "compute_fusion_alias_v2",
]
