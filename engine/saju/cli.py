"""SajuCLI — 결정론적 사주 평가 클래스 진입점.

BaseCLI 상속. assess() 가 dt_local 문자열을 받아
4기둥/오행/10신/대운/신살을 한 번에 계산해 dict 반환.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from functools import lru_cache
from typing import Any

from engine.cli_base import BaseCLI

from .alias import compute_alias
from .calendar import solar_term_month
from .luck_cycle import compute_luck_cycle
from .pillars import compute_pillars
from .shensha import compute_shensha, SHENSHA_MEANINGS
from .ten_gods import compute_ten_gods
from .wuxing import wuxing_dist


def _pillar_label(p: dict) -> str:
    """{gan, ji, gan_han, ji_han} → '갑자(甲子)' 한글(한자) 표기."""
    return f"{p['gan']}{p['ji']}({p['gan_han']}{p['ji_han']})"


def _pillar_str(p: dict) -> str:
    """{gan_han, ji_han} → '甲子' 한자 2글자."""
    return f"{p['gan_han']}{p['ji_han']}"


@lru_cache(maxsize=512)
def _compute_saju_cached(
    dt_local: str,
    tz: str,
    longitude: float,
    latitude: float,
    is_lunar: bool,
    is_leap_month: bool,
    time_unknown: bool,
    gender: str | None,
) -> str:
    """모듈 레벨 사주 결정론적 계산 캐시. JSON str 을 반환 (dict 은 unhashable 회피).

    longitude/latitude 는 호출 측에서 round(x, 3) 양자화한 값을 받는다.
    """
    # 1. dt_local 파싱
    try:
        dt = datetime.fromisoformat(dt_local)
    except (ValueError, TypeError) as e:
        raise ValueError(f"dt_local parse failed: {dt_local!r} ({e})") from e

    # 2. 음력 → 양력 변환
    lunar_meta = None
    if is_lunar:
        lunar_year, lunar_month, lunar_day = dt.year, dt.month, dt.day
        try:
            from lunar_python import Lunar  # type: ignore

            leap = 1 if is_leap_month else 0
            lunar = Lunar.fromYmdHms(
                dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second,
            )
            solar = lunar.getSolar()
            dt = datetime(
                solar.getYear(), solar.getMonth(), solar.getDay(),
                dt.hour, dt.minute, dt.second,
            )
            lunar_meta = {
                "lunar_ymd": f"{lunar_year:04d}-{lunar_month:02d}-{lunar_day:02d}",
                "solar_ymd": f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}",
                "is_leap_month": bool(leap),
            }
        except ImportError:
            pass

    # 3. 절기 기반 사주월
    saju_month = solar_term_month(
        dt.year, dt.month, dt.day, dt.hour, longitude=longitude,
    )

    # 4. 4기둥
    hour_for_pillar = 12 if time_unknown else dt.hour
    pillars_raw = compute_pillars(dt.year, saju_month, dt.day, hour_for_pillar)

    pillars_str = {
        "year": _pillar_str(pillars_raw["year_pillar"]),
        "month": _pillar_str(pillars_raw["month_pillar"]),
        "day": _pillar_str(pillars_raw["day_pillar"]),
        "hour": _pillar_str(pillars_raw["hour_pillar"]),
    }

    # 5. 오행
    wuxing = wuxing_dist(pillars_str)

    # 6. 10신
    ten_gods = compute_ten_gods(pillars_str)

    # 7. 대운
    try:
        luck_cycle = compute_luck_cycle(
            year_gan_han=pillars_raw["year_pillar"]["gan_han"],
            gender=gender or "M",
            month_gan_han=pillars_raw["month_pillar"]["gan_han"],
            month_ji_han=pillars_raw["month_pillar"]["ji_han"],
            count=8,
        )
    except ValueError:
        luck_cycle = []

    # 8. 신살
    shensha = compute_shensha(pillars_raw)

    result = {
        "year": _pillar_label(pillars_raw["year_pillar"]),
        "month": _pillar_label(pillars_raw["month_pillar"]),
        "day": _pillar_label(pillars_raw["day_pillar"]),
        "hour": (
            None if time_unknown else _pillar_label(pillars_raw["hour_pillar"])
        ),
        "day_master": pillars_raw["day_master_han"],
        "wuxing_dist": wuxing,
        "ten_gods": ten_gods,
        "luck_cycle": [
            {"start_age": c["start_age"], "ganzhi": c["ganzhi"]} for c in luck_cycle
        ],
        "shensha": shensha,
        "shensha_meanings": {
            k: SHENSHA_MEANINGS[k] for k in shensha if shensha[k] and k in SHENSHA_MEANINGS
        },
        "pattern": None,
        "pattern_full": None,
        "yongshin": [],
        "alias": None,  # 아래에서 채움
        "meta": {
            "dt_local": dt_local,
            "tz": tz,
            "longitude": longitude,
            "latitude": latitude,
            "is_lunar": is_lunar,
            "is_leap_month": is_leap_month,
            "time_unknown": time_unknown,
            "gender": gender,
            "saju_month": saju_month,
            "lunar_solar_conversion": lunar_meta,
        },
    }
    result["alias"] = compute_alias(result)
    return json.dumps(result, ensure_ascii=False, sort_keys=True)


class SajuCLI(BaseCLI):
    """결정론적 사주 평가 CLI / 라이브러리 클래스."""

    prog_name = "saju-engine"

    # === 라이브러리 메서드 ===

    def assess(
        self,
        dt_local: str,
        tz: str = "Asia/Seoul",
        longitude: float = 126.978,
        latitude: float = 37.5665,
        is_lunar: bool = False,
        is_leap_month: bool = False,
        time_unknown: bool = False,
        gender: str | None = None,
    ) -> dict[str, Any]:
        """사주 평가 단일 진입점.

        결정론적 계산은 모듈 레벨 `_compute_saju_cached` 에 위임 (lru_cache).
        longitude/latitude 는 round(_, 3) 양자화 → 동일 출생지 ±100m 캐시 히트.
        """
        longitude_q = round(float(longitude), 3)
        latitude_q = round(float(latitude), 3)
        cached_json = _compute_saju_cached(
            dt_local,
            tz,
            longitude_q,
            latitude_q,
            is_lunar,
            is_leap_month,
            time_unknown,
            gender,
        )
        return json.loads(cached_json)

    # === BaseCLI 구현 ===

    def build_parser(self) -> argparse.ArgumentParser:
        p = argparse.ArgumentParser(prog=self.prog_name)
        p.add_argument(
            "--dt", required=True, help="ISO datetime (예: 1990-05-15T08:30:00)"
        )
        p.add_argument("--tz", default="Asia/Seoul")
        p.add_argument("--lon", type=float, default=126.978)
        p.add_argument("--lat", type=float, default=37.5665)
        p.add_argument("--lunar", action="store_true")
        p.add_argument("--leap-month", action="store_true")
        p.add_argument("--time-unknown", action="store_true")
        p.add_argument("--gender", default=None)
        p.add_argument("--interpret", action="store_true", help="LLM 해석 추가")
        return p

    async def run_async(self, args: argparse.Namespace) -> dict[str, Any]:
        payload = await asyncio.to_thread(
            self.assess,
            dt_local=args.dt,
            tz=args.tz,
            longitude=args.lon,
            latitude=args.lat,
            is_lunar=args.lunar,
            is_leap_month=args.leap_month,
            time_unknown=args.time_unknown,
            gender=args.gender,
        )
        if args.interpret:
            from .explain import explain_saju

            try:
                payload["interpretation"] = await asyncio.to_thread(
                    explain_saju,
                    payload,
                )
            except Exception as e:
                payload["interpretation_error"] = str(e)
        return payload


def class_main(argv=None):
    return SajuCLI().run(argv)


if __name__ == "__main__":
    sys.exit(class_main())


__all__ = ["SajuCLI", "class_main"]
