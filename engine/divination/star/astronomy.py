"""ADR-114 — Skyfield + JPL DE440s 천체역학 기반 점성술 결정론.

본 모듈은 ADR-068·106·107 정합 — 결정론 산출만, LLM 작문 분리.

영역:
  · 빅3 (Sun·Moon·Ascendant) 정밀 산출
  · 10 행성 황도대 좌표 (분초 단위)
  · 하우스 시스템 (Whole Sign·Equal 디폴트)
  · 행성 트랜짓 + 5 애스펙트 (Conjunction·Sextile·Square·Trine·Opposition)
  · 시너스트리 10×10 매트릭스 + 컴포짓 차트 중점

출처 (ADR-010 사실성 분리):
  · Skyfield (Brandon Rhodes 2020) — rhodesmill.org/skyfield/
  · NASA JPL DE440s ephemeris (2020) — ssd.jpl.nasa.gov/ftp/eph/
  · Stephen Arroyo (1975) ISBN 978-0916360016 — 오브 표준 + 컴포짓
  · Liz Greene (1976) ISBN 978-0877285-01-9 — element·modality 정합
  · Michael P. Munkasey (2006) — An Astrological House Formulary

원칙 (ADR-002·006·010·015 정합):
  · 단정 예언 차단 — "운명·결혼·이혼·파산" 단정 X
  · 다학파 병행 — Whole Sign 디폴트 + Equal 옵션
  · 결정론 — 동일 입력 (UTC + 위경도) → 동일 결과 (분초 단위)
  · UTC 변환 의무 (한국 KST UTC+9 + DST 1948-1988 zoneinfo 처리)

면책:
  · 의료·법률·금융 의사결정 단독 근거 X
  · 출생 시간 누락 시 Ascendant·House 산출 X (Sun만 fallback)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


# ─────────────────────────── 10 행성 + 황도대 메타 ───────────────────────────

PLANETS_10: tuple[str, ...] = (
    "sun", "moon", "mercury", "venus", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
)

# 황도대 12 별자리 (Aries 0° ~ Pisces 330°)
ZODIAC_LABELS_KO: tuple[str, ...] = (
    "양자리", "황소자리", "쌍둥이자리", "게자리",
    "사자자리", "처녀자리", "천칭자리", "전갈자리",
    "사수자리", "염소자리", "물병자리", "물고기자리",
)

ZODIAC_LABELS_EN: tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


def zodiac_from_longitude(ecliptic_lon_deg: float) -> tuple[int, float, str]:
    """황경 도수 → (별자리 인덱스 0~11, 별자리 내 도수 0~30, 한국어 라벨).

    Args:
        ecliptic_lon_deg: 황도 경도 (0~360, 춘분점 기준 양자리 0°)

    Returns:
        (sign_index, degree_in_sign, label_ko)

    Examples:
        >>> zodiac_from_longitude(15.5)
        (0, 15.5, '양자리')
        >>> zodiac_from_longitude(125.7)
        (4, 5.7, '사자자리')
        >>> zodiac_from_longitude(359.99)
        (11, 29.99, '물고기자리')
    """
    lon = float(ecliptic_lon_deg) % 360.0
    sign_idx = int(lon // 30) % 12
    degree_in = lon - sign_idx * 30
    return sign_idx, round(degree_in, 4), ZODIAC_LABELS_KO[sign_idx]


# ─────────────────────────── 결과 dataclass ───────────────────────────

@dataclass(frozen=True)
class PlanetPosition:
    """행성 황도대 위치 (결정론).

    Attributes:
        planet: 행성 키 (sun·moon·... pluto)
        ecliptic_longitude_deg: 황경 (0~360 분초 단위)
        sign_index: 별자리 인덱스 (0~11)
        sign_label_ko: 별자리 한국어 명
        degree_in_sign: 별자리 내 도수 (0~30)
        is_retrograde: 역행 여부 (Δλ < 0)
    """
    planet: str
    ecliptic_longitude_deg: float
    sign_index: int
    sign_label_ko: str
    degree_in_sign: float
    is_retrograde: bool


@dataclass(frozen=True)
class BigThreeReading:
    """빅3 (Sun·Moon·Ascendant) 결정론 결과.

    ★ 의도적 부재 필드 (ADR-006):
      - life_outcome, marriage_outcome — 운명·결혼 단정 X
    """
    sun: PlanetPosition
    moon: PlanetPosition | None         # 출생시간 부재 시 None
    ascendant_longitude_deg: float | None  # 출생시간·장소 부재 시 None
    ascendant_sign_label_ko: str | None
    target_utc_iso: str
    has_birth_time: bool
    disclaimer: str


# ─────────────────────────── 면책 ───────────────────────────

_DISCLAIMER = (
    "본 점성술 산출은 Skyfield + JPL DE440s 천체역학 기반 결정론 좌표로, "
    "운명·결혼·이혼·파산·건강 단정 X. 천체 위치는 우주의 기하학적 배치를 "
    "나타낼 뿐 인과적 동인이 아닙니다 (Liz Greene 1976·Stephen Arroyo 1975 정통). "
    "참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다."
)


# ─────────────────────────── Skyfield 로드 (lazy) ───────────────────────────

_EPHEMERIS_CACHE: dict = {}
_PLANET_BARYCENTER_MAP = {
    "sun": "sun",
    "moon": "moon",
    "mercury": "mercury barycenter",
    "venus": "venus barycenter",
    "mars": "mars barycenter",
    "jupiter": "jupiter barycenter",
    "saturn": "saturn barycenter",
    "uranus": "uranus barycenter",
    "neptune": "neptune barycenter",
    "pluto": "pluto barycenter",
}


def _load_ephemeris(bsp_path: str = "de440s.bsp"):
    """JPL DE440s ephemeris lazy 로드 (캐시)."""
    if "eph" not in _EPHEMERIS_CACHE:
        from skyfield.api import load  # type: ignore
        _EPHEMERIS_CACHE["eph"] = load(bsp_path)
        _EPHEMERIS_CACHE["ts"] = load.timescale()
    return _EPHEMERIS_CACHE["eph"], _EPHEMERIS_CACHE["ts"]


# ─────────────────────────── 행성 위치 결정론 산출 ───────────────────────────

def compute_planet_position(planet: str, dt_utc: datetime, bsp_path: str = "de440s.bsp") -> PlanetPosition | None:
    """행성 황도대 위치 결정론 산출.

    Args:
        planet: 행성 키 (PLANETS_10)
        dt_utc: 관측 시점 (UTC tzinfo 의무)
        bsp_path: DE440s 파일 경로

    Returns:
        PlanetPosition 또는 None (입력 부정합)

    Examples:
        >>> from datetime import datetime, timezone
        >>> dt = datetime(1879, 3, 14, 10, 30, tzinfo=timezone.utc)
        >>> r = compute_planet_position("sun", dt)
        >>> r.sign_label_ko
        '물고기자리'
    """
    if planet not in _PLANET_BARYCENTER_MAP:
        return None
    if dt_utc.tzinfo is None:
        return None

    eph, ts = _load_ephemeris(bsp_path)
    t = ts.utc(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute, dt_utc.second)
    earth = eph["earth"]
    target = eph[_PLANET_BARYCENTER_MAP[planet]]

    astrometric = earth.at(t).observe(target)
    apparent = astrometric.apparent()
    _, lon, _ = apparent.ecliptic_latlon(epoch="date")
    lon_deg = float(lon.degrees) % 360.0

    # 역행 판별 (1시간 후 황경 변화율)
    from datetime import timedelta
    dt_future = dt_utc + timedelta(hours=1)
    t_future = ts.utc(dt_future.year, dt_future.month, dt_future.day,
                       dt_future.hour, dt_future.minute, dt_future.second)
    apparent_future = earth.at(t_future).observe(target).apparent()
    _, lon_future, _ = apparent_future.ecliptic_latlon(epoch="date")
    lon_future_deg = float(lon_future.degrees) % 360.0

    # wrap-around 보정 (360° 경계 통과 시)
    delta = lon_future_deg - lon_deg
    if delta > 180:
        delta -= 360
    elif delta < -180:
        delta += 360
    is_retro = delta < 0 and planet != "moon"  # 달은 항상 순행

    sign_idx, deg_in, label_ko = zodiac_from_longitude(lon_deg)
    return PlanetPosition(
        planet=planet,
        ecliptic_longitude_deg=round(lon_deg, 4),
        sign_index=sign_idx,
        sign_label_ko=label_ko,
        degree_in_sign=deg_in,
        is_retrograde=is_retro,
    )


# ─────────────────────────── 상승점 (Ascendant) 산출 ───────────────────────────

def compute_ascendant(dt_utc: datetime, latitude_deg: float, longitude_deg: float,
                      bsp_path: str = "de440s.bsp") -> float | None:
    """상승점 (Ascendant) 황경 결정론 산출.

    공식 (Munkasey 2006 + Meeus):
        λ_Asc = arctan2(cos(LST), -sin(LST)*cos(ε) - tan(φ)*sin(ε))

    Args:
        dt_utc: 관측 시점 UTC (tzinfo 의무)
        latitude_deg: 위도 (-90 ~ 90, 양수=북반구)
        longitude_deg: 경도 (-180 ~ 180, 양수=동경)
        bsp_path: DE440s 경로

    Returns:
        상승점 황경 (0~360 도) 또는 None (위도 범위 외)

    참고:
        본 함수는 Whole Sign·Equal 디폴트와 호환. Placidus/Koch는 고위도
        붕괴 위험으로 별도 함수 필요. ADR-015 옵션 A 정신.
    """
    if dt_utc.tzinfo is None:
        return None
    if not (-90 <= latitude_deg <= 90):
        return None
    if not (-180 <= longitude_deg <= 180):
        return None

    import numpy as np  # type: ignore
    from skyfield.nutationlib import earth_tilt  # type: ignore

    _, ts = _load_ephemeris(bsp_path)
    t = ts.utc(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute, dt_utc.second)

    # earth_tilt returns tuple — 첫 요소가 mean obliquity (deg)
    tilt_result = earth_tilt(t)
    if isinstance(tilt_result, (tuple, list)):
        obliquity_deg = float(tilt_result[0])
    else:
        obliquity_deg = float(tilt_result)
    eps_rad = np.radians(obliquity_deg)

    # GMST (시간) → LST 변환
    gmst_hours = float(t.gast)
    lst_hours = (gmst_hours + longitude_deg / 15.0) % 24.0
    lst_rad = np.radians(lst_hours * 15.0)

    lat_rad = np.radians(latitude_deg)
    y = np.cos(lst_rad)
    x = -np.sin(lst_rad) * np.cos(eps_rad) - np.tan(lat_rad) * np.sin(eps_rad)
    asc_rad = np.arctan2(y, x)
    asc_deg = (np.degrees(asc_rad)) % 360.0
    return float(round(asc_deg, 4))


# ─────────────────────────── 빅3 통합 ───────────────────────────

def compute_big_three(dt_utc: datetime, latitude_deg: float | None = None,
                       longitude_deg: float | None = None,
                       bsp_path: str = "de440s.bsp") -> BigThreeReading | None:
    """빅3 (Sun·Moon·Ascendant) 결정론 통합.

    Args:
        dt_utc: 출생 시점 UTC (tzinfo 의무)
        latitude_deg: 출생지 위도 (옵션, None 시 Ascendant·Moon 미산출)
        longitude_deg: 출생지 경도 (옵션, None 시 Ascendant·Moon 미산출)
        bsp_path: DE440s 경로

    Returns:
        BigThreeReading 또는 None (입력 부정합)

    출생 시간·장소 미입력 시 fallback:
        - Sun만 산출 (날짜만 있어도 가능)
        - Moon은 None (12시간 6° 이동으로 부정확)
        - Ascendant는 None (위도·경도 의존)
    """
    if dt_utc.tzinfo is None:
        return None

    sun = compute_planet_position("sun", dt_utc, bsp_path)
    if sun is None:
        return None

    has_time = latitude_deg is not None and longitude_deg is not None

    moon = None
    asc_deg = None
    asc_label = None
    if has_time and latitude_deg is not None and longitude_deg is not None:
        moon = compute_planet_position("moon", dt_utc, bsp_path)
        asc_deg = compute_ascendant(dt_utc, float(latitude_deg), float(longitude_deg), bsp_path)
        if asc_deg is not None:
            _, _, asc_label = zodiac_from_longitude(asc_deg)

    return BigThreeReading(
        sun=sun,
        moon=moon,
        ascendant_longitude_deg=asc_deg,
        ascendant_sign_label_ko=asc_label,
        target_utc_iso=dt_utc.isoformat(),
        has_birth_time=has_time,
        disclaimer=_DISCLAIMER,
    )


# ─────────────────────────── 하우스 시스템 (Whole Sign·Equal) ───────────────────────────

def compute_houses_whole_sign(ascendant_deg: float) -> list[dict]:
    """Whole Sign 하우스 12 산출 (헬레니즘 정통, Robert Hand 부활).

    상승점이 위치한 별자리 전체 (0~30°)가 1하우스. 위도 무관 보편 적용.

    Args:
        ascendant_deg: 상승점 황경 (0~360)

    Returns:
        12 하우스 리스트 — 각 dict는 {house_number, sign_index, sign_label_ko, start_deg}

    Examples:
        >>> r = compute_houses_whole_sign(125.5)  # 사자자리 5.5°
        >>> r[0]['sign_label_ko']
        '사자자리'
        >>> r[0]['start_deg']
        120.0
    """
    asc_sign_idx = int(ascendant_deg // 30) % 12
    houses = []
    for h in range(12):
        sign_idx = (asc_sign_idx + h) % 12
        houses.append({
            "house_number": h + 1,
            "sign_index": sign_idx,
            "sign_label_ko": ZODIAC_LABELS_KO[sign_idx],
            "start_deg": float(sign_idx * 30),
        })
    return houses


def compute_houses_equal(ascendant_deg: float) -> list[dict]:
    """Equal House 12 산출 (Asc + 30N 공간 분할, 고위도 보편 적용).

    Args:
        ascendant_deg: 상승점 황경

    Returns:
        12 하우스 리스트 — 각 dict는 {house_number, start_deg, sign_index, sign_label_ko}
    """
    houses = []
    for h in range(12):
        start = (ascendant_deg + 30.0 * h) % 360.0
        sign_idx, _, label = zodiac_from_longitude(start)
        houses.append({
            "house_number": h + 1,
            "start_deg": round(start, 4),
            "sign_index": sign_idx,
            "sign_label_ko": label,
        })
    return houses


# ─────────────────────────── 행성 트랜짓 + 애스펙트 ───────────────────────────

# Stephen Arroyo 1975 + Liz Greene 1976 정통 오브 표준
_ASPECT_ANGLES: dict[str, float] = {
    "conjunction": 0.0,
    "sextile": 60.0,
    "square": 90.0,
    "trine": 120.0,
    "opposition": 180.0,
}

_ASPECT_ORB_DEFAULT: dict[str, float] = {
    "conjunction": 8.0,
    "sextile": 4.0,
    "square": 8.0,
    "trine": 8.0,
    "opposition": 8.0,
}

# 태양·달은 발현력 강해 오브 확장 (Arroyo·Greene 권고)
_ASPECT_ORB_LUMINARY_SUN = 10.0
_ASPECT_ORB_LUMINARY_MOON = 5.0


@dataclass(frozen=True)
class AspectResult:
    """행성 간 애스펙트 결정론 결과."""
    planet_a: str
    planet_b: str
    aspect_type: str
    angle_deg: float
    orb_used_deg: float
    actual_deviation_deg: float


def shortest_angular_distance(lon_a: float, lon_b: float) -> float:
    """원형 황도 상 최단 각도 거리 (0~180)."""
    delta = abs(lon_a - lon_b) % 360.0
    return min(delta, 360.0 - delta)


def detect_aspect(lon_a: float, lon_b: float,
                  planet_a: str = "", planet_b: str = "") -> AspectResult | None:
    """두 황경 → 5 애스펙트 중 일치 검출 (없으면 None).

    Arroyo·Greene 오브 표준 적용:
      - 주요 애스펙트: ±8° (Conjunction·Square·Trine·Opposition)
      - 보조 애스펙트: ±4° (Sextile)
      - 태양 포함 시: ±10°, 달 포함 시: ±5°

    Args:
        lon_a: 행성 A 황경
        lon_b: 행성 B 황경
        planet_a: 행성 A 키 (오브 확장 판정용)
        planet_b: 행성 B 키

    Returns:
        AspectResult 또는 None
    """
    dist = shortest_angular_distance(lon_a, lon_b)

    for aspect_type, target_angle in _ASPECT_ANGLES.items():
        orb = _ASPECT_ORB_DEFAULT[aspect_type]
        # 태양·달 발광체 오브 확장
        if "sun" in (planet_a, planet_b):
            orb = max(orb, _ASPECT_ORB_LUMINARY_SUN)
        if "moon" in (planet_a, planet_b):
            orb = max(orb, _ASPECT_ORB_LUMINARY_MOON)

        deviation = abs(dist - target_angle)
        # opposition은 180° 기준이라 원형 거리 측면에서 정확히 180까지만
        if deviation <= orb:
            return AspectResult(
                planet_a=planet_a,
                planet_b=planet_b,
                aspect_type=aspect_type,
                angle_deg=target_angle,
                orb_used_deg=orb,
                actual_deviation_deg=round(deviation, 4),
            )
    return None


# ─────────────────────────── 시너스트리 + 컴포짓 ───────────────────────────

def compute_synastry_matrix(natal_a: dict[str, float],
                             natal_b: dict[str, float]) -> list[AspectResult]:
    """시너스트리 10×10 애스펙트 매트릭스.

    Args:
        natal_a: 사용자 A의 행성 황경 dict ({"sun": 23.5, "moon": ..., ...})
        natal_b: 사용자 B의 행성 황경 dict

    Returns:
        검출된 AspectResult 리스트 (오브 내 일치만)
    """
    results = []
    for p_a, lon_a in natal_a.items():
        for p_b, lon_b in natal_b.items():
            r = detect_aspect(lon_a, lon_b, p_a, p_b)
            if r is not None:
                results.append(r)
    return results


def compute_composite_midpoint(lon_a: float, lon_b: float) -> float:
    """컴포짓 차트 중점 계산 (Stephen Arroyo 1975).

    180° 경계선 wrap-around 보정 (가장 가까운 내각 중점).

    Args:
        lon_a: 황경 A
        lon_b: 황경 B

    Returns:
        중점 황경 (0~360)

    Examples:
        >>> compute_composite_midpoint(10.0, 50.0)
        30.0
        >>> compute_composite_midpoint(350.0, 10.0)  # wrap-around 보정
        0.0
        >>> compute_composite_midpoint(170.0, 190.0)
        180.0
    """
    lon_a = lon_a % 360.0
    lon_b = lon_b % 360.0
    diff = abs(lon_a - lon_b)

    if diff > 180.0:
        # wrap-around 보정 — 내각 중점
        mid = ((lon_a + lon_b) / 2.0 + 180.0) % 360.0
    else:
        mid = (lon_a + lon_b) / 2.0
    return round(mid, 4)


__all__ = [
    "PLANETS_10", "ZODIAC_LABELS_KO", "ZODIAC_LABELS_EN",
    "zodiac_from_longitude",
    "PlanetPosition", "BigThreeReading",
    "compute_planet_position", "compute_ascendant", "compute_big_three",
    "compute_houses_whole_sign", "compute_houses_equal",
    "AspectResult", "shortest_angular_distance", "detect_aspect",
    "compute_synastry_matrix", "compute_composite_midpoint",
]
