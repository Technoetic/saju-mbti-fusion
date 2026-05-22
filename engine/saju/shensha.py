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


# ADR-128 양인살(羊刃殺) 옵션 A — 양간 5종 (자평진전 정통 디폴트).
# 자평진전(沈孝瞻 1734) — 범진 직역본 ISBN 9791196084417 (박영창·김미석 옮김 2018),
# 이담북스 (2011, 김정혜·서소옥·안명순 역) 등 ISBN 다수 검증.
_YANGIN: Dict[str, str] = {
    "甲": "卯",
    "丙": "午",
    "戊": "午",
    "庚": "酉",
    "壬": "子",
}

# ADR-132 양인살 옵션 B — 삼명통회 음간 5종 확장 (학파 분기 명시 채택).
# 삼명통회(萬民英 1578) ISBN 9791139035261·9791137216822 — 음간 관대(冠帶)·묘고(墓庫)
# 진입 시 음인(陰刃) 작용 인정 (자평진전 격국론과 분기).
# 학파 출처: 보고서 「사주 신살 학파별 분류 표준 조사」 §2.4 + §6 라인 230~234.
_YANGIN_OPTION_B: Dict[str, str] = {
    "乙": "辰",
    "丁": "未",
    "己": "未",
    "辛": "戌",
    "癸": "丑",
}

# ADR-128 괴강살(魁罡殺) — 정통 4 일주 (자평진전·삼명통회 일치 표준).
_GOEGANG_PILLARS: frozenset = frozenset({"庚辰", "庚戌", "壬辰", "戊戌"})

# ADR-128 백호살(白虎殺) — 정통 7 일주 (자평진전·삼명통회 일치 표준).
_BAEKHO_PILLARS: frozenset = frozenset({"甲辰", "乙未", "丙戌", "丁丑", "戊辰", "壬戌", "癸丑"})


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


def compute_shensha(pillars: Dict, *, yangin_school: str = "jappyeong") -> Dict[str, List[str]]:
    """4주(年月日時)에서 주요 신살 8종을 계산.

    학파:
      - 천을귀인·문창귀인·역마·도화·공망: 본 시스템 기존 5종 (전통)
      - 양인·괴강·백호: ADR-128 신규 (자평진전·삼명통회 정통)
      - 양인 옵션 B (삼명통회 음간 확장): ADR-132 추가

    Args:
        pillars: {year_pillar, month_pillar, day_pillar, hour_pillar} —
                 각 항목은 {gan_han, ji_han, gan, ji}.
        yangin_school: 양인살 학파 옵션 (ADR-132) —
            - 'jappyeong' (디폴트): 자평진전 옵션 A 양간 5종
            - 'samyeong': 삼명통회 옵션 B 음간 5종 추가 확장

    Returns:
        {cheoneul, munchang, yeokma, dohwa, kongmang, yangin, goegang, baekho}.
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

    # 6. ADR-128 양인살 (양간 디폴트) + ADR-132 음간 옵션 B 확장
    yangin_target = _YANGIN.get(day_gan)
    yangin = [j for j in all_ji if yangin_target and j == yangin_target]
    if yangin_school == "samyeong":
        yangin_target_b = _YANGIN_OPTION_B.get(day_gan)
        if yangin_target_b:
            yangin.extend([j for j in all_ji if j == yangin_target_b])

    # 7·8. ADR-128 괴강·백호 (일주 매칭 — 매칭 시 일주 한자 반환)
    day_pillar_han = day_gan + day_ji
    goegang = [day_pillar_han] if day_pillar_han in _GOEGANG_PILLARS else []
    baekho = [day_pillar_han] if day_pillar_han in _BAEKHO_PILLARS else []

    return {
        "cheoneul": cheoneul,
        "munchang": munchang,
        "yeokma": yeokma,
        "dohwa": dohwa,
        "kongmang": kongmang,
        "yangin": yangin,
        "goegang": goegang,
        "baekho": baekho,
    }


# ─────────────────────────── ADR-128 단독 API ───────────────────────────


def is_yangin(day_gan_han: str, ji_han: str, *, school: str = "jappyeong") -> bool:
    """일간·지지 한자 → 양인살 여부.

    Args:
        day_gan_han: 일간 한자 (甲~癸).
        ji_han: 지지 한자 (子~亥).
        school: 학파 옵션 (ADR-132) —
            - 'jappyeong' (옵션 A 디폴트): 자평진전 정통 양간 5종
            - 'samyeong' (옵션 B): 삼명통회 음간 5종 추가 (10간 확장)

    학파 출처:
        - 자평진전 ISBN 9791196084417 (범진 직역, 박영창·김미석 2018)
        - 삼명통회 ISBN 9791139035261·9791137216822 (음인 학파)
    """
    target = _YANGIN.get(day_gan_han)
    if target is not None and ji_han == target:
        return True
    if school == "samyeong":
        target_b = _YANGIN_OPTION_B.get(day_gan_han)
        if target_b is not None and ji_han == target_b:
            return True
    return False


def is_goegang(day_pillar_han: str) -> bool:
    """일주 한자 (예: '庚辰') → 괴강살 여부.

    학파: 자평진전·삼명통회 일치 표준 4 일주 (庚辰·庚戌·壬辰·戊戌).
    """
    return day_pillar_han in _GOEGANG_PILLARS


def is_baekho(day_pillar_han: str) -> bool:
    """일주 한자 (예: '甲辰') → 백호살 여부.

    학파: 자평진전·삼명통회 일치 표준 7 일주
    (甲辰·乙未·丙戌·丁丑·戊辰·壬戌·癸丑).
    """
    return day_pillar_han in _BAEKHO_PILLARS


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
    # ADR-128 신규 3종 — 흐름 톤 (단정 어휘 차단·ADR-006 정합)
    "yangin": {
        "label": "양인살",
        "summary": "일간의 강한 기운이 극단으로 치우치는 결. 결단력·강한 의지의 흐름.",
    },
    "goegang": {
        "label": "괴강살",
        "summary": "4 특수 일주(庚辰·庚戌·壬辰·戊戌)의 극단 기운. 리더십·강한 기운의 흐름.",
    },
    "baekho": {
        "label": "백호살",
        "summary": "7 특수 일주(甲辰·乙未·丙戌·丁丑·戊辰·壬戌·癸丑)의 활동 기운. 외향·활동성의 흐름.",
    },
}


# ─────────────────────────── ADR-133 신살 강도 가중치 + 톤 분기 ───────────────────────────


# ADR-133 양인+괴강+백호 강도 신살 중첩 가중치 (보고서 §6.3 라인 159~169 명시).
# 본 매핑은 학파 출처 부재 — 보고서 자체 시스템 설계 명제 (수학적 결정론).
_INTENSE_SINSAL_KEYS: tuple = ("yangin", "goegang", "baekho")


# ADR-153 (2026-05-23) 신살 시너지 학파별 가중치 분기 — /domain-priorities #11 해소
# 표준 학파 (보고서 §6.3 — ADR-133 디폴트): 0.0/1.0/1.5/2.0
# 보수적 학파 (강도 약화 변형): 0.0/0.8/1.4/1.8
# 강조적 학파 (강도 강화 변형): 0.0/1.2/1.8/2.5
_SYNERGY_WEIGHT_SCHOOLS: Dict[str, tuple] = {
    "standard": (0.0, 1.0, 1.5, 2.0),     # ADR-133 디폴트 (보고서 §6.3)
    "conservative": (0.0, 0.8, 1.4, 1.8), # 보수적 학파 — 신살 영향 약화
    "emphatic": (0.0, 1.2, 1.8, 2.5),     # 강조적 학파 — 신살 영향 강화
}


def compute_sinsal_synergy_weight(
    shensha_result: Dict[str, List[str]],
    school: str = "standard",
) -> Dict[str, object]:
    """양인·괴강·백호 중첩 가중치 산출 — ADR-133 + ADR-153 학파 분기.

    보고서 「사주 신살 학파별 분류 표준 조사」 §6.3 디폴트 (standard):
      - 0개 (해당 없음): 0.0
      - 1개 (단일 발현): 1.0 — 성격적 억양 톤
      - 2개 (중첩): 1.5 — 직업적 특성 톤
      - 3개 (양인+괴강+백호 동시): 2.0 — 메인 동력 톤

    ADR-153 학파 옵션:
      - school="standard" (디폴트): ADR-133 정통 (0.0/1.0/1.5/2.0)
      - school="conservative": 보수 학파 (0.0/0.8/1.4/1.8) — 신살 영향 약화
      - school="emphatic": 강조 학파 (0.0/1.2/1.8/2.5) — 신살 영향 강화

    Args:
        shensha_result: compute_shensha() 반환 dict.
        school: 학파 옵션 (디폴트 "standard" — 무회귀 보장).

    Returns:
        {
          "active_count": int (0~3),
          "active_sinsals": list[str],
          "weight": float,
          "tone_branch": str ("none"·"single_personality"·"dual_professional"·"triple_main_engine"),
          "school": str (적용 학파 명시),
        }
        잘못된 school → standard 디폴트 fallback (안전).
    """
    active: List[str] = []
    for key in _INTENSE_SINSAL_KEYS:
        if shensha_result.get(key):
            active.append(key)

    count = len(active)
    # ADR-153 학파 가중치 분기 (디폴트 standard로 fallback)
    weights = _SYNERGY_WEIGHT_SCHOOLS.get(school, _SYNERGY_WEIGHT_SCHOOLS["standard"])
    applied_school = school if school in _SYNERGY_WEIGHT_SCHOOLS else "standard"

    if count == 0:
        weight = weights[0]
        tone = "none"
    elif count == 1:
        weight = weights[1]
        tone = "single_personality"
    elif count == 2:
        weight = weights[2]
        tone = "dual_professional"
    else:  # 3
        weight = weights[3]
        tone = "triple_main_engine"

    return {
        "active_count": count,
        "active_sinsals": active,
        "weight": weight,
        "tone_branch": tone,
        "school": applied_school,
    }


# ADR-133 톤 분기 가이드 텍스트 (LLM 시스템 프롬프트 주입용)
SYNERGY_TONE_GUIDE: Dict[str, str] = {
    "none": "",
    "single_personality": (
        "본 사주에 양인·괴강·백호 중 1개 신살 발현 — 성격적 억양으로 자연스럽게 묘사. "
        "(예: 추진력이 돋보이는 성향)"
    ),
    "dual_professional": (
        "본 사주에 양인·괴강·백호 중 2개 중첩 — 뚜렷하고 강렬한 직업적·기질적 특성으로 묘사. "
        "(예: 불굴의 에너지로 위기를 기회로 뒤집는 위기관리 능력)"
    ),
    "triple_main_engine": (
        "본 사주에 양인·괴강·백호 3개 동시 중첩 — 인생 전반의 메인 동력(Main Engine)으로 작용. "
        "권력형 전문직·사업가·독립적 리더 포지션 적합. 강력한 카리스마와 추진력의 결."
    ),
}


def render_synergy_tone_guide(shensha_result: Dict[str, List[str]]) -> str:
    """LLM 시스템 프롬프트 주입용 신살 중첩 톤 가이드 텍스트 생성.

    Args:
        shensha_result: compute_shensha() 반환 dict.

    Returns:
        톤 가이드 텍스트. 신살 중첩 없으면 빈 문자열.
    """
    synergy = compute_sinsal_synergy_weight(shensha_result)
    tone_branch = str(synergy["tone_branch"])
    return SYNERGY_TONE_GUIDE.get(tone_branch, "")


# ─────────────────────────── ADR-140 지지 반합(半合) 약합 매칭 ───────────────────────────

# 반합 8쌍 (자평진전·삼명통회 일치 표준 — 학파 분쟁 없음).
# 삼합 4국 중 왕지(子午卯酉) 1지지 + 생지(寅申巳亥) 또는 묘지(辰戌丑未) 1지지 매칭.
# ADR-130 detect_samhap()(완전 3지지 매칭)와 의도적 분리 — 半合은 약합(strength=0.5).
# frozenset 패턴 — 지지 순서 무관.
_BANHAP_PAIRS: Dict[frozenset, Dict[str, object]] = {
    # 火 局 (삼합 寅午戌)
    frozenset(("寅", "午")): {"label": "寅午", "ohaeng": "화", "guk_full": "寅午戌"},
    frozenset(("午", "戌")): {"label": "午戌", "ohaeng": "화", "guk_full": "寅午戌"},
    # 木 局 (삼합 亥卯未)
    frozenset(("亥", "卯")): {"label": "亥卯", "ohaeng": "목", "guk_full": "亥卯未"},
    frozenset(("卯", "未")): {"label": "卯未", "ohaeng": "목", "guk_full": "亥卯未"},
    # 水 局 (삼합 申子辰)
    frozenset(("申", "子")): {"label": "申子", "ohaeng": "수", "guk_full": "申子辰"},
    frozenset(("子", "辰")): {"label": "子辰", "ohaeng": "수", "guk_full": "申子辰"},
    # 金 局 (삼합 巳酉丑)
    frozenset(("巳", "酉")): {"label": "巳酉", "ohaeng": "금", "guk_full": "巳酉丑"},
    frozenset(("酉", "丑")): {"label": "酉丑", "ohaeng": "금", "guk_full": "巳酉丑"},
}

# 半合 약합 강도 (자평진전 정통 — 완전 삼합 1.0 대비 0.5).
_BANHAP_STRENGTH: float = 0.5


def detect_banhap(branches: List[str]) -> List[Dict[str, object]]:
    """4주 지지에서 반합(半合) 8쌍 매칭 — ADR-140.

    반합은 삼합 3지지 중 왕지(子午卯酉) 포함 2지지만 일치 시 성립하는 약합(strength=0.5).
    완전 삼합(strength=1.0)은 ADR-130 detect_samhap() 별도 API 사용.

    학파 출처 (자평진전·삼명통회 일치 표준 — 학파 분쟁 없음):
      - 자평진전 ISBN 9791196084417 (범진 직역, 박영창·김미석 2018)
      - 삼명통회 ISBN 9791139035261·9791137216822
      - 외부 보고서: 「월하몽 도메인 지식 보강 가이드 v7」 §1.2 라인 49~61

    Args:
        branches: 4주 지지 한자 리스트 (예: ["子", "寅", "午", "戌"]).

    Returns:
        매칭된 반합 목록 (순서 무관, 중복 허용):
        [{"label": str, "ohaeng": str, "guk_full": str, "strength": float, "pair": list[str]}]

    Example:
        >>> detect_banhap(["寅", "午", "卯", "丑"])
        [{"label": "寅午", "ohaeng": "화", "guk_full": "寅午戌", "strength": 0.5, "pair": ["寅", "午"]}]
    """
    branch_set = set(branches)
    results: List[Dict[str, object]] = []
    for pair_set, info in _BANHAP_PAIRS.items():
        if pair_set.issubset(branch_set):
            results.append(
                {
                    "label": info["label"],
                    "ohaeng": info["ohaeng"],
                    "guk_full": info["guk_full"],
                    "strength": _BANHAP_STRENGTH,
                    "pair": list(pair_set),
                }
            )
    return results


def is_banhap_pair(ji1: str, ji2: str) -> bool:
    """두 지지 한자가 반합(半合) 쌍 여부 — ADR-140.

    Args:
        ji1, ji2: 지지 한자 (子~亥).

    Returns:
        반합 8쌍 중 1쌍이면 True.
    """
    return frozenset((ji1, ji2)) in _BANHAP_PAIRS
