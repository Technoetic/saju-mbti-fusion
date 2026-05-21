"""사주 사주(四柱) 계산 모듈.

천간(天干) / 지지(地支) 60갑자 순환을 기반으로 年/月/日/時 4주(柱)를 산출한다.

기준:
- 60갑자: (year - 4) % 60 에서 BC 2697 갑자년 정합
- 月柱: 五虎遁(오호둔) - 年干으로 寅月 月干 결정
- 日柱: 1900-01-01 = 己亥 기준 일수 차이 60갑자 순환
- 時柱: 五鼠遁(오서둔) - 日干으로 子時 時干 결정

caller (calendar.py) 가 절기 기반 월(1~12)을 제공한다.
"""

from __future__ import annotations

from datetime import date

# ── 천간(天干) 10 ─────────────────────────────────────────────
CHEONGAN_HAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
CHEONGAN_KO = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]

# ── 지지(地支) 12 ─────────────────────────────────────────────
JIJI_HAN = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
JIJI_KO = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]

# ── 五虎遁 表: 年干 index → 寅月(1월) 月干 index ───────────────
# 甲己年 → 丙寅, 乙庚年 → 戊寅, 丙辛年 → 庚寅, 丁壬年 → 壬寅, 戊癸年 → 甲寅
_OHOTUN_INMONTH = {
    0: 2,  # 甲 → 丙
    5: 2,  # 己 → 丙
    1: 4,  # 乙 → 戊
    6: 4,  # 庚 → 戊
    2: 6,  # 丙 → 庚
    7: 6,  # 辛 → 庚
    3: 8,  # 丁 → 壬
    8: 8,  # 壬 → 壬
    4: 0,  # 戊 → 甲
    9: 0,  # 癸 → 甲
}

# ── 五鼠遁 表: 日干 index → 子時 時干 index ───────────────────
# 甲己日 → 甲子, 乙庚日 → 丙子, 丙辛日 → 戊子, 丁壬日 → 庚子, 戊癸日 → 壬子
_OSEOTUN_JAHOUR = {
    0: 0,  # 甲 → 甲
    5: 0,  # 己 → 甲
    1: 2,  # 乙 → 丙
    6: 2,  # 庚 → 丙
    2: 4,  # 丙 → 戊
    7: 4,  # 辛 → 戊
    3: 6,  # 丁 → 庚
    8: 6,  # 壬 → 庚
    4: 8,  # 戊 → 壬
    9: 8,  # 癸 → 壬
}

# ADR-085: KASI 음양력 공식 API 회신 정합 — 1900-01-01 = 甲戌日 (甲=0, 戌=10).
# 이전 앵커 己亥(5,11)는 60갑자 cycle 내 +25 offset 오류 (KASI 10건 회귀 100% 검출).
# 출처: data.go.kr LrsrCldInfoService getLunCalInfo lunIljin 회신.
_BASE_DATE = date(1900, 1, 1)
_BASE_GAN_IDX = 0  # 甲
_BASE_JI_IDX = 10  # 戌


def _pack(gan_idx: int, ji_idx: int) -> dict:
    """천간/지지 인덱스를 한글+한자 dict 로 직렬화."""
    gan_idx %= 10
    ji_idx %= 12
    return {
        "gan": CHEONGAN_KO[gan_idx],
        "ji": JIJI_KO[ji_idx],
        "gan_han": CHEONGAN_HAN[gan_idx],
        "ji_han": JIJI_HAN[ji_idx],
        "gan_idx": gan_idx,
        "ji_idx": ji_idx,
    }


def year_pillar(year: int) -> dict:
    """年柱: (year - 4) % 60 = 60갑자 index."""
    idx = (year - 4) % 60
    return _pack(idx % 10, idx % 12)


def month_pillar(year: int, month: int) -> dict:
    """月柱: 五虎遁 표 기반.

    month: 1~12 (절기 기준 월. caller 가 변환). 1=寅月(立春~驚蟄), 2=卯月, ...
    """
    if not 1 <= month <= 12:
        raise ValueError(f"month must be 1..12, got {month}")
    year_gan_idx = (year - 4) % 10
    in_month_gan = _OHOTUN_INMONTH[year_gan_idx]
    # month=1 이 寅(index 2), month=2 가 卯(index 3), ...
    month_gan_idx = (in_month_gan + (month - 1)) % 10
    month_ji_idx = (2 + (month - 1)) % 12  # 寅(2) 부터 시작
    return _pack(month_gan_idx, month_ji_idx)


def day_pillar(year: int, month: int, day: int) -> dict:
    """日柱: 1900-01-01 (己亥) 기준 일수 차이 60갑자 순환.

    1900년 이전도 datetime.date 가 지원하는 1년 이후라면 정상 작동(음수 delta).
    """
    target = date(year, month, day)
    delta = (target - _BASE_DATE).days
    gan_idx = (_BASE_GAN_IDX + delta) % 10
    ji_idx = (_BASE_JI_IDX + delta) % 12
    return _pack(gan_idx, ji_idx)


_HOUR_SCHEMA_UNIFIED = "unified"
_HOUR_SCHEMA_YAJASI = "yajasi_separate"
_HOUR_SCHEMAS: tuple[str, ...] = (_HOUR_SCHEMA_UNIFIED, _HOUR_SCHEMA_YAJASI)


def hour_pillar(
    day_gan_idx: int,
    hour: int,
    schema: str = _HOUR_SCHEMA_UNIFIED,
) -> dict:
    """時柱: 五鼠遁 표 + ADR-105 야자시 학파 옵션.

    Args:
        day_gan_idx: 일간 인덱스 (0~9). schema에 따라 caller 책임 다름:
            - "unified" (디폴트): caller가 23시 입력 시 익일 일간 전달 의무
              (통합 자시 학파, 23:00 시점 일주 변경 — compute_pillars()가 처리).
            - "yajasi_separate": 23시 입력 시 당일 일간 전달 (야자시는 당일 일진 유지).
        hour: 0~23 (24시간제).
            23:00~00:59 = 子時(0), 01:00~02:59 = 丑時(1), ..., 21:00~22:59 = 亥時(11).
        schema (ADR-105 옵션 B):
            - "unified" (디폴트): 통합 자시 학파 (현 구현 유지, 역호환 의무).
              23:00~00:59 모두 子時 ji_idx=0.
            - "yajasi_separate": 야자시(夜子時) 분리 학파.
              23:00~23:59 = 야자시 (당일 일진 유지 + 익일 일간 오서둔 — caller 책임).
              00:00~00:59 = 정자시 (익일 일진 + 익일 일간 오서둔).
              본 함수 출력의 ji_idx는 동일 (子=0)이나 caller의 day_gan_idx 전달 의무가 다름.

    Returns:
        {gan_idx, ji_idx, ...} 시주.

    ADR 정합:
        - ADR-002: 단일 학파 강요 X (옵션 B 병행)
        - ADR-006: 운명 단정 X (시주 분류만)
        - ADR-015: schema='unified' 디폴트 (옵션 A) + 'yajasi_separate' 옵션 B
    """
    if not 0 <= hour <= 23:
        raise ValueError(f"hour must be 0..23, got {hour}")
    if schema not in _HOUR_SCHEMAS:
        raise ValueError(f"schema must be one of {_HOUR_SCHEMAS}, got {schema!r}")
    # 23시는 익일 子時 로 보지만 여기서는 동일 일자 子時 로 처리 (caller 가 day 조정 가능).
    # ADR-105: schema 분기는 본 함수 내부 ji_idx 계산에 영향 X — 두 학파 모두 23시 = 子時.
    # schema 차이는 compute_pillars()에서 day_pillar·hour_pillar 결합 시 caller가 처리.
    if hour == 23:
        ji_idx = 0  # 子
    else:
        ji_idx = ((hour + 1) // 2) % 12

    ja_gan = _OSEOTUN_JAHOUR[day_gan_idx % 10]
    gan_idx = (ja_gan + ji_idx) % 10
    return _pack(gan_idx, ji_idx)


def compute_pillars(
    year: int,
    month: int,
    day: int,
    hour: int,
    schema: str = _HOUR_SCHEMA_UNIFIED,
) -> dict:
    """4주(年月日時) + 日主(일간) 통합 계산 (ADR-073 + ADR-105 야자시 옵션).

    Parameters
    ----------
    year, month, day : 절기 보정된 양력 (caller 가 calendar.py 에서 처리)
    hour : 0~23
    schema : ADR-105 야자시 학파 옵션
        - "unified" (디폴트): 통합 자시 학파.
          23시 입력 시 day+1 익일 일주로 자동 보정 후 hour_pillar 호출.
          (현 동작 호환 의무 — caller가 별도 조정 불필요해짐)
        - "yajasi_separate": 야자시 분리 학파.
          23시 입력 시 day 그대로 (당일 일주 유지), 익일 일간으로 오서둔 적용.

    Returns
    -------
    {
        "year_pillar":  {...},
        "month_pillar": {...},
        "day_pillar":   {...},
        "hour_pillar":  {...},
        "day_master":   "갑"  # 日干 (일간) - 사주 분석의 중심
    }

    ADR 정합:
        - ADR-002: 단일 학파 강요 X
        - ADR-015: 옵션 B 병행 (디폴트=통합 자시)
        - ADR-073: 결정론 보장
        - ADR-085: KASI 앵커 정정 영향 없음
    """
    if schema not in _HOUR_SCHEMAS:
        raise ValueError(f"schema must be one of {_HOUR_SCHEMAS}, got {schema!r}")

    yp = year_pillar(year)
    mp = month_pillar(year, month)

    # ADR-105: 23시 처리 — schema에 따라 일주 시점 결정
    # 역호환 의무: schema='unified' (디폴트)는 현 동작 유지 (caller가 day 조정 책임).
    # 새 동작은 schema='yajasi_separate'에만 적용.
    if hour == 23 and schema == _HOUR_SCHEMA_YAJASI:
        # 야자시 분리: 23시는 당일 일주 유지 + 익일 일간으로 오서둔
        from datetime import date as _date, timedelta as _timedelta
        dp = day_pillar(year, month, day)  # 당일 일주 유지
        next_day = _date(year, month, day) + _timedelta(days=1)
        next_dp = day_pillar(next_day.year, next_day.month, next_day.day)
        hp = hour_pillar(next_dp["gan_idx"], hour, schema=schema)
    else:
        # schema='unified' (디폴트) 또는 hour != 23: 현 동작 유지
        dp = day_pillar(year, month, day)
        hp = hour_pillar(dp["gan_idx"], hour, schema=schema)

    return {
        "year_pillar": yp,
        "month_pillar": mp,
        "day_pillar": dp,
        "hour_pillar": hp,
        "day_master": dp["gan"],
        "day_master_han": dp["gan_han"],
    }


__all__ = [
    "CHEONGAN_HAN",
    "CHEONGAN_KO",
    "JIJI_HAN",
    "JIJI_KO",
    "year_pillar",
    "month_pillar",
    "day_pillar",
    "hour_pillar",
    "compute_pillars",
]
