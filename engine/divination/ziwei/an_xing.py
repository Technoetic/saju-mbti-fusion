"""자미두수 안성법(安星法) — 결정론 명반 산출 순수 함수.

본 모듈은 ADR-010 정합 — 명반 배치를 결정론적으로 산출 (LLM 자체산출 금지).
입력: 음력 월/일 + 시지 인덱스 + 년간 인덱스 (lunar-python이 산출한 값).
출력: 명궁·신궁 위치, 오행국, 자미성 위치, 14주성 배치, 생년사화.

검증 (vault/references/ziwei-doushu-anseong.md, 1990-05-15 10시 남성):
  음력 4/21 사시(5) 경오(庚)년 → 명궁 자(0), 신궁 술(10),
  명궁 천간 무(戊), 화6국, [자미성 조견표는 딥리서치 확정 대기].

지지 인덱스: 자0 축1 인2 묘3 진4 사5 오6 미7 신8 유9 술10 해11.
"""

from __future__ import annotations

from dataclasses import dataclass

from engine.divination.ziwei.palace_data import (
    FOURTEEN_STARS,
    NAYIN_JU,
    SIHUA_DEFAULT,
    SIHUA_VARIANTS,
    SiHuaSet,
    TWELVE_PALACES,
    WUHUDUN_YIN_STEM,
    WUXING_JU,
    WuxingJu,
)

_YIN = 2  # 인궁 지지 인덱스 (안성 기점)


# ─────────────────────────── 명궁·신궁 정위 ───────────────────────────

def ming_palace(lunar_month: int, hour_branch: int) -> int:
    """명궁(命宮) 지지 인덱스.

    인궁 기점, 생월(음력) 순행 → 도달 위치에서 생시 역행.
    검증: 음력 4월 + 사시(5) → 자(0).

    Args:
        lunar_month: 음력 월 1~12 (윤달은 caller가 분월 규칙으로 정수 월 결정).
        hour_branch: 생시 지지 인덱스 0~11 (자시=0).
    """
    if not 1 <= lunar_month <= 12:
        raise ValueError(f"lunar_month must be 1..12, got {lunar_month}")
    if not 0 <= hour_branch <= 11:
        raise ValueError(f"hour_branch must be 0..11, got {hour_branch}")
    pos_month = (_YIN + (lunar_month - 1)) % 12   # 인 기점 월 순행
    return (pos_month - hour_branch) % 12          # 시 역행


def body_palace(lunar_month: int, hour_branch: int) -> int:
    """신궁(身宮) 지지 인덱스.

    인궁 기점, 생월 순행 → 다시 생시 순행.
    검증: 음력 4월 + 사시(5) → 술(10).
    """
    if not 1 <= lunar_month <= 12:
        raise ValueError(f"lunar_month must be 1..12, got {lunar_month}")
    if not 0 <= hour_branch <= 11:
        raise ValueError(f"hour_branch must be 0..11, got {hour_branch}")
    pos_month = (_YIN + (lunar_month - 1)) % 12
    return (pos_month + hour_branch) % 12


# ─────────────────────────── 오행국 (오호둔 → 납음) ───────────────────────────

def palace_stem(year_gan: int, branch: int) -> int:
    """오호둔법으로 특정 지지의 천간 인덱스.

    년간의 인월(寅) 천간을 기준으로 인궁부터 순행.
    검증: 경(6)년 자궁(0) → 무(4).
    """
    yin_stem = WUHUDUN_YIN_STEM[year_gan % 10]
    steps = (branch - _YIN) % 12   # 인 기점 몇 칸
    return (yin_stem + steps) % 10


def _ganzhi_index(gan: int, zhi: int) -> int:
    """천간·지지 인덱스 → 60갑자 인덱스 (갑자=0)."""
    for i in range(60):
        if i % 10 == gan and i % 12 == zhi:
            return i
    raise ValueError(f"invalid ganzhi combination gan={gan} zhi={zhi}")


def wuxing_ju(year_gan: int, ming_branch: int) -> WuxingJu:
    """오행국 — 명궁 천간·지지 납음오행으로 국수 결정.

    검증: 경(6)년 명궁 자(0) → 무자(戊子) → 납음 화6국.
    """
    stem = palace_stem(year_gan, ming_branch)
    gz = _ganzhi_index(stem, ming_branch)
    num = NAYIN_JU[gz]
    return WUXING_JU[num]


# ─────────────────────────── 자미성 안성 (표준 정국표 하드코딩) ───────────────────────────
# ★ 자미성 정국표(定局表) — 국수(2~6) × 생일(1~30) → 지지 인덱스.
#   표준 《자미두수전서》 逐日安紫微 정국표. 공식(나머지 보정)은 원전 서술이 모호해
#   오차가 실증되어 폐기하고, 다수 공개 출처가 일치하는 검증된 조견표를 하드코딩.
#   앵커 검증(전부 통과): 수2국1일=축, 목3국1일=진, 금4국1일=해, 토5국1일=오, 화6국1일=유.
#   검증 예시(화6국 21일)=인(寅2). ⚠️ Export.md는 '진(辰)'으로 오기 — 표준·다수출처 불일치로
#   표준값 채택 (Export.md는 개념 딥리서치라 검증예시 오류 확인).
#   각 리스트는 지지 인덱스 (자0 축1 ... 해11), 생일 1~30 순서.

_ZIWEI_TABLE: dict[int, tuple[int, ...]] = {
    2: (1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 0, 0, 1, 1, 2, 2, 3, 3, 4),
    3: (4, 1, 2, 5, 2, 3, 6, 3, 4, 7, 4, 5, 8, 5, 6, 9, 6, 7, 10, 7, 8, 11, 8, 9, 0, 9, 10, 1, 10, 11),
    4: (11, 4, 1, 2, 0, 5, 2, 3, 1, 6, 3, 4, 2, 7, 4, 5, 3, 8, 5, 6, 4, 9, 6, 7, 5, 10, 7, 8, 6, 11),
    5: (6, 11, 4, 1, 2, 7, 0, 5, 2, 3, 8, 1, 6, 3, 4, 9, 2, 7, 4, 5, 10, 3, 8, 5, 6, 11, 4, 9, 6, 7),
    6: (9, 6, 11, 4, 1, 2, 10, 7, 0, 5, 2, 3, 11, 8, 1, 6, 3, 4, 0, 9, 2, 7, 4, 5, 1, 10, 3, 8, 5, 6),
}


def ziwei_star(ju_num: int, lunar_day: int) -> int:
    """자미성 지지 인덱스 — 오행국 국수 + 음력 생일 (표준 정국표).

    Args:
        ju_num: 오행국 국수 2~6.
        lunar_day: 음력 생일 1~30.
    """
    if ju_num not in _ZIWEI_TABLE:
        raise ValueError(f"ju_num must be 2..6, got {ju_num}")
    if not 1 <= lunar_day <= 30:
        raise ValueError(f"lunar_day must be 1..30, got {lunar_day}")
    return _ZIWEI_TABLE[ju_num][lunar_day - 1]


# ─────────────────────────── 14주성 배치 ───────────────────────────

def tianfu_star(ziwei_branch: int) -> int:
    """천부성 위치 — 자미성과 인-신 축 대칭.

    검증: 자미 인(2)→천부 인(2, 동궁), 자미 진(4)→천부 자(0).
    """
    return (4 - ziwei_branch) % 12


def place_fourteen_stars(ziwei_branch: int) -> dict[str, int]:
    """14주성 → 지지 인덱스 배치.

    자미성계는 자미 위치 기준 오프셋, 천부성계는 천부 위치 기준 오프셋.
    """
    tf = tianfu_star(ziwei_branch)
    positions: dict[str, int] = {}
    for star in FOURTEEN_STARS:
        anchor = ziwei_branch if star.series == "ziwei" else tf
        positions[star.key] = (anchor + star.offset) % 12
    return positions


# ─────────────────────────── 12궁 배열 ───────────────────────────

def arrange_palaces(ming_branch: int) -> list[tuple[int, int]]:
    """12궁 배열 — 명궁 기점 역행.

    Returns:
        [(궁 seq, 지지 인덱스), ...] 명궁(seq 0)부터 부모궁(seq 11)까지.
        seq 진행 방향은 지지 역행(반시계).
    """
    result: list[tuple[int, int]] = []
    for meta in TWELVE_PALACES:
        branch = (ming_branch - meta.seq) % 12   # 역행
        result.append((meta.seq, branch))
    return result


# ─────────────────────────── 생년사화 ───────────────────────────

@dataclass(frozen=True)
class SiHuaResult:
    """생년사화 결과 (유파 태그 포함)."""
    school: str                # 채택 유파 ("중주파 표준" 등)
    lu_star_ko: str            # 화록 주성 (한국어)
    quan_star_ko: str
    ke_star_ko: str
    ji_star_ko: str
    has_variants: bool         # 유파 병기 대상 년간 여부


def _star_ko(key: str) -> str:
    """성요 key → 한국어 (주성 14 + 사화 보조성 4)."""
    from engine.divination.ziwei.palace_data import SIHUA_STAR_LABEL_KO
    return SIHUA_STAR_LABEL_KO.get(key, key)


def sihua(year_gan: int, school: str = "남파") -> SiHuaResult:
    """생년사화 — 년간별 화록·화권·화과·화기 배속.

    Args:
        year_gan: 년간 인덱스 0~9.
        school: 유파. 기본 "남파"(全書/全集/흠천 원전 배속). 병기 대상(戊·庚·壬)만
            "남파"|"민파"|"중주파"|"흠천사법"|"북파"|"전서계열" 로 분기.

    ADR-002·015: 원전(남파) 기본, 戊·庚·壬 유파 쟁점은 SIHUA_VARIANTS로 병기.
    원전 근거: 자미/자미두수 안성법 원전 검증.md (《자미두수전서》 卷二 축자).
    """
    gan = year_gan % 10
    variants = SIHUA_VARIANTS.get(gan)
    if variants and school in variants:
        s: SiHuaSet = variants[school]
        school_label = f"{school}"
    else:
        s = SIHUA_DEFAULT[gan]
        school_label = "남파(전서) 표준"
    return SiHuaResult(
        school=school_label,
        lu_star_ko=_star_ko(s.lu_star),
        quan_star_ko=_star_ko(s.quan_star),
        ke_star_ko=_star_ko(s.ke_star),
        ji_star_ko=_star_ko(s.ji_star),
        has_variants=variants is not None,
    )


__all__ = [
    "ming_palace", "body_palace",
    "palace_stem", "wuxing_ju",
    "ziwei_star", "tianfu_star", "place_fourteen_stars",
    "arrange_palaces",
    "SiHuaResult", "sihua",
]
