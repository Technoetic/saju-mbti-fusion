"""자미두수 결정론 명반 산출 진입점 + 프롬프트 포맷터.

본 모듈은 ADR-010 정합 — 결정론 명반을 산출(compute_ziwei_chart)하고,
LLM 시스템 프롬프트에 주입할 텍스트(format_ziwei_for_prompt)를 생성한다.
LLM은 이 배치를 받아 해석 작문만 하며, 명반을 자체 산출하지 않는다.

음력 변환·윤달·시지·년간은 lunar-python(1.4.4)에 위임한다.
안성 계산은 engine.divination.ziwei.an_xing 순수 함수를 사용한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from engine.divination.ziwei import an_xing
from engine.divination.ziwei.palace_data import (
    DISCLAIMER,
    TWELVE_PALACES,
    WuxingJu,
    gan_ko,
    zhi_hanja,
    zhi_ko,
)

# lunar-python 시지(時支) 한자 → 지지 인덱스 (자0 ... 해11)
_TIME_ZHI_TO_IDX: dict[str, int] = {
    "子": 0, "丑": 1, "寅": 2, "卯": 3, "辰": 4, "巳": 5,
    "午": 6, "未": 7, "申": 8, "酉": 9, "戌": 10, "亥": 11,
}

# lunar-python 년간(年干) 한자 → 천간 인덱스 (갑0 ... 계9)
_YEAR_GAN_TO_IDX: dict[str, int] = {
    "甲": 0, "乙": 1, "丙": 2, "丁": 3, "戊": 4,
    "己": 5, "庚": 6, "辛": 7, "壬": 8, "癸": 9,
}


# ─────────────────────────── 결과 dataclass ───────────────────────────

@dataclass(frozen=True)
class PalaceCell:
    """12궁 단일 궁 결과."""
    key: str            # 궁 키 (ming·cai_bo 등)
    label_ko: str       # "명궁" 등
    label_hanja: str    # "命宮" 등
    alias_ko: str       # 별칭 (노복=교우 등, 없으면 "")
    branch_ko: str      # 소재 지지 한국어
    branch_hanja: str   # 소재 지지 한자
    main_stars_ko: tuple[str, ...]  # 이 궁의 14주성 (없으면 빈 튜플 = 공궁)


@dataclass(frozen=True)
class ZiweiChart:
    """자미두수 결정론 명반 (핵심).

    ★ 의도적 부재 (ADR-006): 길흉 단정·묘왕리함 밝기·대한·유년·럭키 요소 없음.
    """
    # 입력 에코 (음력 변환 결과)
    lunar_month: int          # 안성에 쓴 음력 월 (윤달 분월 보정 후)
    lunar_day: int            # 음력 일
    is_leap_month: bool       # 윤달 여부
    hour_branch_ko: str       # 시지 한국어
    hour_branch_hanja: str    # 시지 한자
    year_gan_ko: str          # 년간 한국어
    # 안성 결과
    ming_branch_ko: str       # 명궁 지지
    body_branch_ko: str       # 신궁 지지
    ming_stem_ko: str         # 명궁 천간
    wuxing_ju_ko: str         # 오행국 "화육국" 등
    wuxing_ju_num: int        # 국수 2~6
    ziwei_branch_ko: str      # 자미성 소재 지지
    palaces: tuple[PalaceCell, ...]  # 12궁 (명궁 seq 0 → 부모 seq 11)
    # 생년사화
    sihua_school: str         # 채택 유파
    sihua_lu_ko: str          # 화록 주성
    sihua_quan_ko: str        # 화권
    sihua_ke_ko: str          # 화과
    sihua_ji_ko: str          # 화기
    sihua_has_variants: bool  # 유파 병기 대상 년간 여부
    # 면책
    disclaimer: str


# ─────────────────────────── 진입점 ───────────────────────────

def _leap_month_split(lunar_month: int, lunar_day: int) -> tuple[int, bool]:
    """윤달 분월법 (ADR-002 옵션): lunar-python은 윤달을 음수 월로 반환.

    본 시스템 기본 = split_half(15일 분월법) — ★ 원전 정통과 일치.
      윤달 15일 이전=전월(=|월|), 16일 이후=후월(=|월|+1).
    ★ 원전 확정 (자미/자미두수 안성법 원전 검증.md):
        · 《자미두수전서》 卷一 論閏月生人: "凡閏月生人，作兩月算，
          十五日以前作前月，十五日以後作後月" → 원전 자체가 15일 분월법.
        · 현대 iztro fixLeap 기본값도 동일 (15일 분기). 본 시스템 채택 = 원전+실무 주류 일치.
        · 재야 이설(전월 전체 편입 / 후월 전체 편입)은 원전 위배 — 미채택.
      자미두수는 절기 불용(不用節氣, 只依陰曆), 삭망월(음력월) 기준 — 절기월 아님(원전 확정).
    """
    is_leap = lunar_month < 0
    month = abs(lunar_month)
    if is_leap:
        if lunar_day >= 16:
            month = month + 1 if month < 12 else 1
    return month, is_leap


def compute_ziwei_chart(
    birth: date,
    birth_hour: int,
    gender: str,
) -> ZiweiChart:
    """자미두수 결정론 명반 산출.

    Args:
        birth: 양력 생년월일.
        birth_hour: 0~23 시각 (시지 산출용).
        gender: "M" | "F" (명반 배치는 성별 무관 — 표준 안명법. 에코용으로만 받음).

    Returns:
        ZiweiChart — 명궁·12궁·14주성·오행국·생년사화 결정론 배치.
    """
    if not 0 <= birth_hour <= 23:
        raise ValueError(f"birth_hour must be 0..23, got {birth_hour}")

    # 1) 음력 변환 (lunar-python 위임)
    from lunar_python import Solar
    solar = Solar.fromYmdHms(birth.year, birth.month, birth.day, birth_hour, 0, 0)
    lunar = solar.getLunar()

    raw_month = lunar.getMonth()        # 음수면 윤달
    lunar_day = lunar.getDay()
    time_zhi = lunar.getTimeZhi()       # 시지 한자
    year_gan_han = lunar.getYearGan()   # 년간 한자

    hour_branch = _TIME_ZHI_TO_IDX[time_zhi]
    year_gan = _YEAR_GAN_TO_IDX[year_gan_han]
    lunar_month, is_leap = _leap_month_split(raw_month, lunar_day)

    # 2) 안성 계산 (순수 함수)
    ming = an_xing.ming_palace(lunar_month, hour_branch)
    body = an_xing.body_palace(lunar_month, hour_branch)
    ming_stem = an_xing.palace_stem(year_gan, ming)
    ju: WuxingJu = an_xing.wuxing_ju(year_gan, ming)
    ziwei = an_xing.ziwei_star(ju.num, lunar_day)
    star_positions = an_xing.place_fourteen_stars(ziwei)
    palace_layout = an_xing.arrange_palaces(ming)
    sihua = an_xing.sihua(year_gan)

    # 3) 12궁 셀 조립 (지지 인덱스 → 주성 역인덱스)
    from engine.divination.ziwei.palace_data import STAR_LABEL_KO
    stars_by_branch: dict[int, list[str]] = {}
    for star_key, br in star_positions.items():
        stars_by_branch.setdefault(br, []).append(STAR_LABEL_KO[star_key])

    cells: list[PalaceCell] = []
    for seq, branch in palace_layout:
        meta = TWELVE_PALACES[seq]
        cells.append(PalaceCell(
            key=meta.key,
            label_ko=meta.label_ko,
            label_hanja=meta.label_hanja,
            alias_ko=meta.alias_ko,
            branch_ko=zhi_ko(branch),
            branch_hanja=zhi_hanja(branch),
            main_stars_ko=tuple(stars_by_branch.get(branch, ())),
        ))

    return ZiweiChart(
        lunar_month=lunar_month,
        lunar_day=lunar_day,
        is_leap_month=is_leap,
        hour_branch_ko=zhi_ko(hour_branch),
        hour_branch_hanja=zhi_hanja(hour_branch),
        year_gan_ko=gan_ko(year_gan),
        ming_branch_ko=zhi_ko(ming),
        body_branch_ko=zhi_ko(body),
        ming_stem_ko=gan_ko(ming_stem),
        wuxing_ju_ko=ju.label_ko,
        wuxing_ju_num=ju.num,
        ziwei_branch_ko=zhi_ko(ziwei),
        palaces=tuple(cells),
        sihua_school=sihua.school,
        sihua_lu_ko=sihua.lu_star_ko,
        sihua_quan_ko=sihua.quan_star_ko,
        sihua_ke_ko=sihua.ke_star_ko,
        sihua_ji_ko=sihua.ji_star_ko,
        sihua_has_variants=sihua.has_variants,
        disclaimer=DISCLAIMER,
    )


# ─────────────────────────── 프롬프트 포맷터 (ADR-010) ───────────────────────────

# 4대 핵심 궁 (프론트 요구 — 명궁·재백·관록·복덕)
_CORE_PALACE_KEYS = ("ming", "cai_bo", "guan_lu", "fu_de")


def format_ziwei_for_prompt(chart: ZiweiChart) -> str:
    """LLM 시스템 프롬프트에 주입할 명반 메타 텍스트 (ADR-010).

    결정론 배치만 전달. LLM은 이 배치의 해석을 작문하되 배치를 바꾸지 않는다.
    """
    lines: list[str] = []
    lines.append("[자미두수 결정론 명반 — 아래 배치는 확정값, 임의 변경 금지]")
    leap = " (윤달)" if chart.is_leap_month else ""
    lines.append(
        f"  · 음력 {chart.lunar_month}월{leap} {chart.lunar_day}일 "
        f"{chart.hour_branch_ko}시({chart.hour_branch_hanja}時), 년간 {chart.year_gan_ko}"
    )
    lines.append(
        f"  · 명궁(命宮): {chart.ming_branch_ko}궁 / 신궁(身宮): {chart.body_branch_ko}궁 "
        f"/ 오행국: {chart.wuxing_ju_ko} / 자미성(紫微星): {chart.ziwei_branch_ko}궁"
    )

    # 4대 핵심 궁 주성
    core_by_key = {c.key: c for c in chart.palaces}
    lines.append("  · 4대 핵심 궁 주성:")
    for key in _CORE_PALACE_KEYS:
        c = core_by_key.get(key)
        if not c:
            continue
        stars = ", ".join(c.main_stars_ko) if c.main_stars_ko else "공궁(空宮 — 주성 없음)"
        lines.append(f"      - {c.label_ko}({c.branch_ko}궁): {stars}")

    # 생년사화
    lines.append(
        f"  · 생년사화(生年四化, {chart.sihua_school}): "
        f"화록={chart.sihua_lu_ko} 화권={chart.sihua_quan_ko} "
        f"화과={chart.sihua_ke_ko} 화기={chart.sihua_ji_ko}"
    )
    if chart.sihua_has_variants:
        lines.append("      ※ 이 년간의 사화는 유파에 따라 배속이 다를 수 있음 (채택 유파 표기).")

    lines.append(
        "[안전 장치 — ADR-006] 위 배치의 결(흐름)만 부드럽게 풀이. "
        "운명·연애·재물·직업·수명 단정 금지. '반드시/확실히' 등 단정 어휘 금지."
    )
    return "\n".join(lines)


def full_palace_summary(chart: ZiweiChart) -> str:
    """12궁 전체 요약 (선택적 상세 표시용)."""
    parts: list[str] = []
    for c in chart.palaces:
        stars = "·".join(c.main_stars_ko) if c.main_stars_ko else "공궁"
        alias = f"({c.alias_ko})" if c.alias_ko else ""
        parts.append(f"{c.label_ko}{alias} {c.branch_ko}궁: {stars}")
    return " / ".join(parts)


__all__ = [
    "PalaceCell", "ZiweiChart",
    "compute_ziwei_chart",
    "format_ziwei_for_prompt", "full_palace_summary",
]
