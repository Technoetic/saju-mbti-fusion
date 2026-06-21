"""십신(十神) 계산.

日干(일간) 기준 다른 천간/지지의 오행·음양 관계를 10신으로 매핑.

10신:
  비견, 겁재, 식신, 상관, 편재, 정재, 편관, 정관, 편인, 정인
"""

# 천간 → 오행
_STEM_WUXING = {
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

# 천간 음양 (양=True, 음=False)
_STEM_YANG = {
    "甲": True,
    "丙": True,
    "戊": True,
    "庚": True,
    "壬": True,
    "乙": False,
    "丁": False,
    "己": False,
    "辛": False,
    "癸": False,
}

# 지지 → 본기 천간
_BRANCH_MAIN_STEM = {
    "寅": "甲",
    "卯": "乙",
    "辰": "戊",
    "巳": "丙",
    "午": "丁",
    "未": "己",
    "申": "庚",
    "酉": "辛",
    "戌": "戊",
    "亥": "壬",
    "子": "癸",
    "丑": "己",
}

# 오행 상생: A → B (A가 B를 생함)
_GENERATES = {"목": "화", "화": "토", "토": "금", "금": "수", "수": "목"}
# 오행 상극: A → B (A가 B를 극함)
_OVERCOMES = {"목": "토", "토": "수", "수": "화", "화": "금", "금": "목"}


def ten_god(day_master_han: str, other_gan_han: str) -> str:
    """일간 기준 다른 천간의 10신을 반환."""
    if day_master_han not in _STEM_WUXING or other_gan_han not in _STEM_WUXING:
        return ""

    dm_wx = _STEM_WUXING[day_master_han]
    o_wx = _STEM_WUXING[other_gan_han]
    same_yy = _STEM_YANG[day_master_han] == _STEM_YANG[other_gan_han]

    if o_wx == dm_wx:
        return "비견" if same_yy else "겁재"
    if _GENERATES[dm_wx] == o_wx:  # 일간이 생하는 오행
        return "식신" if same_yy else "상관"
    if _OVERCOMES[dm_wx] == o_wx:  # 일간이 극하는 오행
        return "편재" if same_yy else "정재"
    if _OVERCOMES[o_wx] == dm_wx:  # 일간을 극하는 오행
        return "편관" if same_yy else "정관"
    if _GENERATES[o_wx] == dm_wx:  # 일간을 생하는 오행
        return "편인" if same_yy else "정인"
    return ""


def compute_ten_gods(pillars: dict) -> dict:
    """4기둥의 천간/지지 각각에 대해 10신을 계산.

    Args:
        pillars: {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"}
                 day 의 천간이 일간(day_master).

    Returns:
        {"year_gan": "...", "year_ji": "...", "month_gan": "...", ...,
         "hour_gan": "...", "hour_ji": "..."}
        (단, day_gan 은 자기 자신 = 비견 으로 표기하되 호출자 판단)
    """
    day_gz = pillars.get("day", "")
    if len(day_gz) < 2:
        return {}
    day_master = day_gz[0]

    result = {}
    for key in ("year", "month", "day", "hour"):
        gz = pillars.get(key, "")
        if len(gz) < 2:
            continue
        stem, branch = gz[0], gz[1]
        result[f"{key}_gan"] = ten_god(day_master, stem)
        main_stem = _BRANCH_MAIN_STEM.get(branch, "")
        result[f"{key}_ji"] = ten_god(day_master, main_stem) if main_stem else ""

    return result


# 4 세력 (성·재·관·식) — 설계도 §2.3 매핑
_CLUSTER_OF = {
    "비견": "비겁", "겁재": "비겁",
    "식신": "식상", "상관": "식상",
    "편재": "재성", "정재": "재성",
    "편관": "관살", "정관": "관살",
    "편인": "인성", "정인": "인성",
}

# 4세력 → MBTI 인지 기능 (설계도 §3.2)
_CLUSTER_TO_MBTI = {
    "인성": "N (직관 — Ni·Ne, 통찰·잠재력)",
    "재성": "S (감각 — Si·Se, 현실·구체)",
    "관살": "T (사고 — Te·Ti, 원칙·논리)",
    "식상": "F+N (감정·직관 — Fe·Ne, 표현·창의)",
    "비겁": "E/I 자아축 (자기주장·경쟁)",
}


# ─────────────────────────── ADR-086: 십성 메타 분류 ───────────────────────────
# 출처: 다시배우는 사주명리 — 사길신(四吉神)·사흉신(四兇神) 표준 분류
# 본 메타는 **구조 라벨**일 뿐 **길흉 단정 X** (ADR-006·010·014 정합).
# 결정론 출력은 페르소나에게 "이러한 구조 명칭이 존재함"만 전달.

# 사길신(四吉神) — 명리학 통설 분류 (단일 학파 강요 X, 옵션 메타)
SAGILSHIN = ("식신", "정재", "정관", "정인")
# 사흉신(四兇神) — 동일 출처. 명칭일 뿐 단정 X.
SAHYUNGSHIN = ("상관", "겁재", "편관", "편인")


def classify_gilhyung(ten_god_name: str) -> str | None:
    """십성 길흉신 분류 라벨 반환.

    Returns:
        "사길신" | "사흉신" | None
    ADR-006: 길흉 단정 X. 본 함수는 **명리학 표준 분류 라벨**만 회신.
    """
    if ten_god_name in SAGILSHIN:
        return "사길신"
    if ten_god_name in SAHYUNGSHIN:
        return "사흉신"
    return None


# ─────────────────────────── 특수 조합 플래그 ───────────────────────────
# 다음 조합은 사주 명리학에서 빈번히 언급되는 구조 패턴.
# 결과는 **구조 명칭**일 뿐 **운명·길흉 인과 X** (ADR-006·010·014).


def has_siksinjesal(ten_gods_result: dict) -> bool:
    """식신제살(食神制殺) — 식신이 편관을 극하는 구조.

    Returns:
        True if 식신 + 편관 동시 존재. 구조 명칭일 뿐 길흉 단정 X.
    """
    vals = list(ten_gods_result.values())
    return "식신" in vals and "편관" in vals


def has_jaegukin(ten_gods_result: dict) -> bool:
    """재극인(財剋印) — 재성이 인성을 극하는 구조."""
    vals = list(ten_gods_result.values())
    has_jae = "편재" in vals or "정재" in vals
    has_in = "편인" in vals or "정인" in vals
    return has_jae and has_in


def has_dosik(ten_gods_result: dict) -> bool:
    """도식(倒食) — 편인이 식신을 극하는 구조."""
    vals = list(ten_gods_result.values())
    return "편인" in vals and "식신" in vals


def detect_special_combinations(ten_gods_result: dict) -> list[str]:
    """4주 십성 결과에서 특수 구조 조합 명칭 목록 반환.

    Returns:
        ["식신제살", "재극인", "도식"] 중 해당 구조 명칭 (구조만, 길흉 X).
    """
    flags = []
    if has_siksinjesal(ten_gods_result):
        flags.append("식신제살")
    if has_jaegukin(ten_gods_result):
        flags.append("재극인")
    if has_dosik(ten_gods_result):
        flags.append("도식")
    return flags


# ADR-086 면책: 본 메타는 명리학 표준 분류 라벨일 뿐 운명·길흉 단정 X.
# 사용자 출력 시 build_legal_footer + ADR-006 약화 표현 의무.
_META_DISCLAIMER = (
    "본 십성 메타(사길신·사흉신·식신제살·재극인·도식)는 명리학 통설의 "
    "구조 분류 라벨이며 운명·길흉 단정 X. 결정론 라벨만 인용 가능."
)

# 10 십성 개별 → MBTI 인지 기능 정밀 매핑 (설계도 §3.2 표)
_TENGOD_TO_MBTI_FN = {
    "정인": "Ni (내향 직관 — 깊은 수용·이상)",
    "편인": "Ne (외향 직관 — 비주류 통찰·탐험)",
    "정재": "Si (내향 감각 — 꼼꼼·과거 기록·계산)",
    "편재": "Se (외향 감각 — 개방·즉시 반응·기회)",
    "정관": "Te (외향 사고 — 체계·시스템 순응)",
    "편관": "Ti (내향 사고 — 독립·강박적 원칙)",
    "식신": "Fe (외향 감정 — 조화·완만 표현)",
    "상관": "Ne+Fe (창의 표현·거침없는 발산)",
    "비견": "I 자아 (독립·동지)",
    "겁재": "E 자아 (경쟁·강한 자기주장)",
}


def tengod_function_hints(ten_gods_map: dict) -> list[dict]:
    """8개 십성 슬롯별 MBTI 인지 기능 정밀 매핑."""
    out = []
    for slot, tengod in ten_gods_map.items():
        if tengod:
            out.append({
                "slot": slot,
                "tengod": tengod,
                "function": _TENGOD_TO_MBTI_FN.get(tengod, ""),
            })
    return out


# 오행 → E/I 매핑 (설계도 §3.1)
# 목·화 우세 → E (외향, 발산), 금·수 우세 → I (내향, 수렴)
def wuxing_ei_signal(wuxing_dist: dict) -> dict:
    """사주 오행 분포 → E/I 신호 추정.

    Returns:
        {"signal": "E"|"I"|"BALANCED", "score": float (-1=I, +1=E),
         "fire_wood": float, "metal_water": float}
    """
    fire_wood = float(wuxing_dist.get("목", 0)) + float(wuxing_dist.get("화", 0))
    metal_water = float(wuxing_dist.get("금", 0)) + float(wuxing_dist.get("수", 0))
    total = fire_wood + metal_water
    if total == 0:
        return {"signal": "BALANCED", "score": 0.0, "fire_wood": 0.0, "metal_water": 0.0}
    score = (fire_wood - metal_water) / total
    if score > 0.2:
        signal = "E"
    elif score < -0.2:
        signal = "I"
    else:
        signal = "BALANCED"
    return {
        "signal": signal,
        "score": round(score, 2),
        "fire_wood": round(fire_wood, 1),
        "metal_water": round(metal_water, 1),
    }


def sipsung_clusters(ten_gods_map: dict) -> dict:
    """8개 십성 슬롯 → 5 세력 카운트.

    Args:
        ten_gods_map: compute_ten_gods 반환 dict (year_gan, year_ji, ...)

    Returns:
        {"인성": int, "재성": int, "관살": int, "식상": int, "비겁": int}
    """
    counts = {"인성": 0, "재성": 0, "관살": 0, "식상": 0, "비겁": 0}
    for v in ten_gods_map.values():
        cluster = _CLUSTER_OF.get(v)
        if cluster:
            counts[cluster] += 1
    return counts


def cluster_mbti_hints(clusters: dict) -> list[dict]:
    """4세력 → MBTI 친화 힌트 (강한 순)."""
    sorted_pairs = sorted(clusters.items(), key=lambda x: -x[1])
    hints = []
    for cluster, n in sorted_pairs:
        if n > 0:
            hints.append({
                "cluster": cluster,
                "count": n,
                "mbti_axis": _CLUSTER_TO_MBTI.get(cluster, ""),
            })
    return hints


# ─────────────────────────── ADR-157 — 십성·격국 KCI 학술 인용 ───────────────────────────

# /squeeze-report 월하몽_도메인지식_URL_검증목록.md 차분.
# 본 모듈 십성 매핑의 추가 학술 출처 영속.

from dataclasses import dataclass as _dataclass


@_dataclass(frozen=True)
class SipsungKciCitation:
    """ADR-157 — 십성·격국 KCI 학술 인용."""
    author_ko: str
    title_ko: str
    journal: str
    publication_year: int
    kci_indexed: bool
    identifier: str
    topic_focus: str


SIPSUNG_KCI_CITATIONS: tuple[SipsungKciCitation, ...] = (
    SipsungKciCitation(
        author_ko="십성 계량화 연구",
        title_ko="사주 십성(十星)의 계량화(計量化)와 활용에 대한 고찰",
        journal="KCI 등재 학술",
        publication_year=0,
        kci_indexed=True,
        identifier="ART002438633",
        topic_focus=(
            "십성 (비견·겁재·식신·상관 등 10종) 계량화 방법론 학술 분석. "
            "본 시스템 ten_gods.py 십성 매핑 + 강도 활용의 학술 출처."
        ),
    ),
    SipsungKciCitation(
        author_ko="명리학 적성론 연구",
        title_ko="명리학의 적성론 — 왕(旺)한 십성과 격국 비교 연구",
        journal="KCI 등재 학술",
        publication_year=0,
        kci_indexed=True,
        identifier="ART002596247",
        topic_focus=(
            "왕한 십성 (해당 일주에서 강한 십성)과 격국 (월령·전체 분포 기반) "
            "비교 학술 분석. 본 시스템 sipsung_clusters + 격국 추론 학술 출처."
        ),
    ),
)


def get_sipsung_kci_citations() -> tuple[SipsungKciCitation, ...]:
    """ADR-157 — 십성·격국 KCI 학술 인용 풀 조회."""
    return SIPSUNG_KCI_CITATIONS


__all__ = [
    "ten_god",
    "compute_ten_gods",
    "sipsung_clusters",
    "cluster_mbti_hints",
    "tengod_function_hints",
    "wuxing_ei_signal",
    # ADR-157 십성·격국 KCI 학술 인용
    "SipsungKciCitation", "SIPSUNG_KCI_CITATIONS", "get_sipsung_kci_citations",
]
