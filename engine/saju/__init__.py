"""Saju subpackage — exposes the SajuCLI entry point.

구조 리팩터링 (2026-06-21): 일부 모듈을 책임별 하위 패키지로 그룹화하되,
기존 import 경로(engine.saju.<module>)를 sys.modules 별칭으로 100% 호환 유지.
"""

import sys as _sys
import importlib as _importlib

# 하위 패키지로 이동한 모듈 → 옛 경로 별칭 (engine.saju.<old> 호환)
_MOVED = {
    "alias": "engine.saju.hanja.alias",
    "balance_meter": "engine.saju.tengods.balance_meter",
    "calendar": "engine.saju.core.calendar",
    "compat": "engine.saju.gunghap.compat",
    "explain": "engine.saju.interpret.explain",
    "geo_lut": "engine.saju.core.geo_lut",
    "hanja_data": "engine.saju.hanja.hanja_data",
    "image_gen": "engine.saju.media.image_gen",
    "luck_cycle": "engine.saju.core.luck_cycle",
    "mbti_compat_v2": "engine.saju.gunghap.mbti_compat_v2",
    "mbti_functions": "engine.saju.gunghap.mbti_functions",
    "music_gen": "engine.saju.media.music_gen",
    "myeong": "engine.saju.interpret.myeong",
    "pillars": "engine.saju.core.pillars",
    "shensha": "engine.saju.sinsal.shensha",
    "ten_gods": "engine.saju.tengods.ten_gods",
    "twelve_sinsal": "engine.saju.sinsal.twelve_sinsal",
    "twelve_stages": "engine.saju.sinsal.twelve_stages",
    "wuxing": "engine.saju.core.wuxing",
}
for _old, _new in _MOVED.items():
    try:
        _mod = _importlib.import_module(_new)
        _sys.modules[f"{__name__}.{_old}"] = _mod
    except Exception:  # noqa: BLE001 — 선택적 의존(예: 미디어 라이브러리 부재) 허용
        pass

from .cli import SajuCLI

__all__ = ["SajuCLI"]
