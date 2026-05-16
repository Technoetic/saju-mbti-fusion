"""24절기 기반 사주월(月) 결정 모듈.

사주 月柱는 양력 월이 아닌 절기 12개(節, jeolgi) 기준으로 끊는다.
각 절기는 태양 황경(ecliptic longitude)이 특정 각도에 도달하는 순간이다.

寅月 시작: 立春(입춘) 黄经 315° → month=1
卯月 시작: 驚蟄(경칩) 黄经 345° → month=2
...
丑月 시작: 小寒(소한) 黄经 285° → month=12

구현:
1. skyfield + DE440/DE421 ephemeris 로 태양 황경 정밀 계산
2. ephemeris 미가용 시 평균 절기일 표(fallback) 사용
3. 출생지 경도(longitude) → 진태양시(true solar time) 보정
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Optional

# ── 절기 12개: (한자, 黄经도, 寅月 기준 사주월 index) ──────────────
# month index: 1=寅, 2=卯, 3=辰, 4=巳, 5=午, 6=未, 7=申, 8=酉, 9=戌, 10=亥, 11=子, 12=丑
SOLAR_TERMS_MAJOR = [
    ("立春", 315, 1),  # 寅月 시작
    ("驚蟄", 345, 2),  # 卯月
    ("淸明", 15, 3),  # 辰月
    ("立夏", 45, 4),  # 巳月
    ("芒種", 75, 5),  # 午月
    ("小暑", 105, 6),  # 未月
    ("立秋", 135, 7),  # 申月
    ("白露", 165, 8),  # 酉月
    ("寒露", 195, 9),  # 戌月
    ("立冬", 225, 10),  # 亥月
    ("大雪", 255, 11),  # 子月
    ("小寒", 285, 12),  # 丑月
]

# ── Fallback: 평균 절기일 (월-일, KST 기준 근사) ──────────────────
# 절기는 매년 ±1일 변동. 정밀 계산 불가 시 평균값 사용.
_AVG_TERM_DATES = [
    (1, (2, 4)),  # 立春 → 2/4
    (2, (3, 6)),  # 驚蟄 → 3/6
    (3, (4, 5)),  # 淸明 → 4/5
    (4, (5, 6)),  # 立夏 → 5/6
    (5, (6, 6)),  # 芒種 → 6/6
    (6, (7, 7)),  # 小暑 → 7/7
    (7, (8, 8)),  # 立秋 → 8/8
    (8, (9, 8)),  # 白露 → 9/8
    (9, (10, 8)),  # 寒露 → 10/8
    (10, (11, 7)),  # 立冬 → 11/7
    (11, (12, 7)),  # 大雪 → 12/7
    (12, (1, 6)),  # 小寒 → 다음해 1/6 (丑月은 전년도 12월말~당년 1월)
]

# skyfield ephemeris 로드 (lazy)
_eph = None
_ts = None
_sun = None
_earth = None


def _load_ephemeris():
    """skyfield DE440 → DE421 fallback 로드. 실패 시 None 반환."""
    global _eph, _ts, _sun, _earth
    if _eph is not None:
        return True
    try:
        from skyfield.api import load

        _ts = load.timescale()
        for kernel in ("de440s.bsp", "de421.bsp"):
            try:
                _eph = load(kernel)
                _sun = _eph["sun"]
                _earth = _eph["earth"]
                return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def _sun_longitude(dt_utc: datetime) -> Optional[float]:
    """주어진 UTC 시각의 태양 시황경(apparent ecliptic longitude, 도)."""
    if not _load_ephemeris() or _ts is None or _earth is None or _sun is None:
        return None
    t = _ts.from_datetime(dt_utc.replace(tzinfo=timezone.utc))
    astrometric = _earth.at(t).observe(_sun).apparent()
    _lat, lon, _dist = astrometric.ecliptic_latlon("date")
    return lon.degrees % 360


def _apply_solar_time(dt_local: datetime, longitude: float) -> datetime:
    """경도 기반 진태양시 보정. KST(135°E) 기준 차이를 분 단위로 가감."""
    # 한국 표준시 = UTC+9 = 135°E. 실제 경도와 차이 4분/도.
    delta_minutes = (longitude - 135.0) * 4.0
    return dt_local + timedelta(minutes=delta_minutes)


def _term_datetime_fallback(year: int, term_idx: int) -> datetime:
    """평균 절기일 fallback. term_idx 1~12 (입춘=1)."""
    mm, dd = _AVG_TERM_DATES[term_idx - 1][1]
    y = year + 1 if term_idx == 12 and mm == 1 else year
    return datetime(y, mm, dd, 0, 0, 0)


def _term_datetime(year: int, term_idx: int) -> datetime:
    """절기 정확 시각(local naive). term_idx 1~12. skyfield 가능 시 정밀, 아니면 fallback."""
    if not _load_ephemeris() or year < 1900:
        return _term_datetime_fallback(year, term_idx)
    target_lon = SOLAR_TERMS_MAJOR[term_idx - 1][1]
    mm, dd = _AVG_TERM_DATES[term_idx - 1][1]
    y = year + 1 if term_idx == 12 and mm == 1 else year
    # 평균일 기준 ±3일 이분탐색
    lo = datetime(y, mm, dd) - timedelta(days=3)
    hi = lo + timedelta(days=6)
    for _ in range(40):
        mid = lo + (hi - lo) / 2
        lon = _sun_longitude(mid - timedelta(hours=9))  # KST→UTC
        if lon is None:
            return _term_datetime_fallback(year, term_idx)
        diff = (lon - target_lon + 540) % 360 - 180
        if diff < 0:
            lo = mid
        else:
            hi = mid
        if abs(diff) < 1e-4:
            break
    return lo + (hi - lo) / 2


@lru_cache(maxsize=1024)
def _solar_term_month_cached(
    year: int, month: int, day: int, hour: int, longitude_q: float
) -> int:
    """내부 캐시 함수. longitude 는 이미 0.001 단위 양자화된 값."""
    dt_local = datetime(year, month, day, hour)
    dt_solar = _apply_solar_time(dt_local, longitude_q)
    # 당해 12개 절기 시각 비교. dt_solar 이전 마지막 절기의 month index 반환.
    # 立春(term1) 이전이면 전년도 丑月(=12).
    current_month = 12
    for term_idx in range(1, 13):
        term_year = (
            year - 1
            if term_idx == 12
            and SOLAR_TERMS_MAJOR[11][1] == 285
            and dt_solar.month >= 2
            else year
        )
        # 단순화: 각 절기 시각 < dt_solar 이면 해당 month 적용
        t_dt = _term_datetime(year, term_idx)
        if dt_solar >= t_dt:
            current_month = SOLAR_TERMS_MAJOR[term_idx - 1][2]
    # 立春 이전 1~2월: 전년 丑月
    立春 = _term_datetime(year, 1)
    if dt_solar < 立春:
        return 12
    return current_month


def solar_term_month(
    year: int, month: int, day: int, hour: int, longitude: float = 126.978
) -> int:
    """절기 기반 사주월 반환 (1=寅月 ... 12=丑月).

    Parameters
    ----------
    year, month, day, hour : 양력 + KST 시각
    longitude : 출생지 경도(°, E+). 기본 서울 126.978.

    longitude 는 0.001 precision 으로 round 한 뒤 lru_cache 적중을 노린다.
    """
    longitude_q = round(float(longitude), 3)
    return _solar_term_month_cached(year, month, day, hour, longitude_q)


def is_before_term(dt_local: datetime, year: int) -> bool:
    """입춘 이전인지 판정 (년주가 전년도로 넘어가는지)."""
    立春 = _term_datetime(year, 1)
    return dt_local < 立春


__all__ = [
    "SOLAR_TERMS_MAJOR",
    "solar_term_month",
    "is_before_term",
]
