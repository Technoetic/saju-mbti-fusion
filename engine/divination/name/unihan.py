"""Unihan 기반 한자 자동 매핑 — ADR-026 9,932자 풀 + ADR-027 KCI 옵션 C.

data/korean_hanja_unihan.json에서 9,932자 (대법원 9,389자 + 변형자) 로드:
  · char: 한자
  · hangul: 한국어 음 (대표 1자)
  · kangxi_strokes: 강희자전 원획수 (또는 총획수)
  · radical: 부수 번호 (1~214, 신규 1,407자는 빈 문자열)
  · resource_ohaeng: 자원오행 (부수 자동 매핑 옵션 A, 35.5%)
  · resource_ohaeng_kci: KCI 학설 매핑 (옵션 C, ADR-027 94자)
  · kci_reason: 옵션 C 매핑 근거 (자원·본의 형태론)
  · kci_school_source: KCI 학설 출처 (김기승·이재승·김만태)
  · source: 'scourt_2024' (신규 추가분만)
  · is_scourt_approved: True (신규 추가분만)

데이터 출처:
  · 기존 8,525자: Unihan 자동 매핑 (한국어 음 보유 한자)
  · 신규 1,407자: 법원 전자가족관계등록시스템 API
    (efamily.scourt.go.kr/webhanja/whjsearch, mode=listUnicodeByTotstroke, 2026-05-17 fetch)
  · 대법원규칙 제3151호 (2024-06-11 시행) 인명용 한자 9,389자
  · 저작권법 제7조 (국가 법령 저작권 배제)

지연 로딩 — 처음 호출 시에만 JSON 파싱. 메모리 ~6MB.

호환성:
  · name_strokes (수동 250자) — 우선순위
  · name_unihan (자동 9932자, 대법원 9389자 + 변형자 보존) — fallback

운영표준:
  · 결정론 (재현성)
  · LLM 무관
  · JSON 손실·미수록 시 None 반환 (예외 X)
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


# 데이터 경로 — engine/ 기준 부모 디렉토리의 data/
_DATA_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "korean_hanja_unihan.json"
)


@lru_cache(maxsize=1)
def _load_db() -> dict[str, dict[str, Any]]:
    """JSON 로드. 파일 없으면 빈 dict.

    Returns:
        {"星": {"hangul": "성", "kangxi_strokes": 9, "radical": 72,
                 "resource_ohaeng": "화"}, ...}
    """
    if not _DATA_PATH.exists():
        return {}
    try:
        raw = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return {}
        return {entry["char"]: entry for entry in raw if "char" in entry}
    except Exception:
        return {}


@lru_cache(maxsize=1)
def _build_hangul_index() -> dict[str, list[str]]:
    """{"성": ["星","城","誠",...], ...} 역인덱스. 한 번만 계산."""
    db = _load_db()
    out: dict[str, list[str]] = {}
    for char, entry in db.items():
        hangul = entry.get("hangul", "")
        if not hangul:
            continue
        out.setdefault(hangul, []).append(char)
    return out


# ─────────────────────────── Public API ───────────────────────────

def kangxi_strokes(char: str) -> int | None:
    """단일 한자의 강희자전 원획수. 미수록 시 None."""
    if not isinstance(char, str) or not char:
        return None
    entry = _load_db().get(char)
    if entry is None:
        return None
    val = entry.get("kangxi_strokes")
    return int(val) if isinstance(val, (int, float)) else None


def hangul_of(char: str) -> str | None:
    """단일 한자의 한국어 음 (대표 1자). 미수록 시 None."""
    if not isinstance(char, str) or not char:
        return None
    entry = _load_db().get(char)
    return entry.get("hangul") if entry else None


def radical_of(char: str) -> int | None:
    """단일 한자의 부수 번호 (1~214). 미수록 시 None."""
    if not isinstance(char, str) or not char:
        return None
    entry = _load_db().get(char)
    val = entry.get("radical") if entry else None
    return int(val) if isinstance(val, (int, float)) and val > 0 else None


def resource_ohaeng(char: str) -> str | None:
    """단일 한자의 자원오행. 미수록·미정 시 None.

    부수 기반 자동 매핑(옵션 A). 학설 충돌 시 ``resource_ohaeng_kci`` 우선.
    """
    if not isinstance(char, str) or not char:
        return None
    entry = _load_db().get(char)
    if entry is None:
        return None
    val = entry.get("resource_ohaeng", "")
    return val if val else None


def resource_ohaeng_kci(char: str) -> str | None:
    """단일 한자의 KCI 학설 기반 자원오행 (옵션 C). 미수록 시 None.

    ADR-027 기반. 옵션 C는 자원·본의 직접 매핑. 부수 자동 매핑(옵션 A)과
    충돌 가능. 학설 출처는 ``kci_school_source()`` 조회.

    학파 출처:
      · 김기승 (2024): 『자원오행 성명학』 (다산글방, ISBN 9788932901138)
      · 이재승 (2025): 『명리·용신 성명학 원론』 (ISBN 9791173182693)
      · 김만태 (2018): KCI 「한국 성씨한자(姓氏漢字)의 자원오행에 대한 고찰」
        (문화와융합 40권 3호, DOI 10.33645/cnc.2018.06.40.3.339)
    """
    if not isinstance(char, str) or not char:
        return None
    entry = _load_db().get(char)
    if entry is None:
        return None
    val = entry.get("resource_ohaeng_kci", "")
    return val if val else None


def kci_reason(char: str) -> str | None:
    """KCI 자원오행 배속 이유 (자원·본의 형태론 추적). 미수록 시 None."""
    if not isinstance(char, str) or not char:
        return None
    entry = _load_db().get(char)
    if entry is None:
        return None
    val = entry.get("kci_reason", "")
    return val if val else None


def kci_school_source(char: str) -> str | None:
    """KCI 매핑 학파 출처 (예: '김기승(2024), 이재승(2025)'). 미수록 시 None."""
    if not isinstance(char, str) or not char:
        return None
    entry = _load_db().get(char)
    if entry is None:
        return None
    val = entry.get("kci_school_source", "")
    return val if val else None


def preferred_ohaeng(char: str) -> str | None:
    """학설 우선 자원오행 — KCI 매핑이 있으면 그것, 없으면 부수 자동 매핑.

    학설 충돌 시 옵션 C(자원·본의 KCI 학설) 우선. 사용자 출력에서는
    ``kci_reason()`` 동반 노출 권장 (ADR-010 사실성 분리).
    """
    return resource_ohaeng_kci(char) or resource_ohaeng(char)


def get_candidates_by_hangul(syllable: str) -> list[str]:
    """단일 한글 음 → 해당 음을 가진 한자 후보 리스트.

    Unihan에서 추출된 모든 한자 — 대법원 인명용 풀 자체는 별도 검증 필요.
    """
    if not syllable:
        return []
    return list(_build_hangul_index().get(syllable, []))


def total_chars() -> int:
    return len(_load_db())


def total_with_ohaeng() -> int:
    """자원오행이 매핑된 한자 수 (부수 기반 옵션 A)."""
    return sum(1 for e in _load_db().values() if e.get("resource_ohaeng"))


def total_with_kci() -> int:
    """KCI 학설 매핑된 한자 수 (옵션 C). ADR-027 본문화 기준 94자."""
    return sum(1 for e in _load_db().values() if e.get("resource_ohaeng_kci"))


def is_loaded() -> bool:
    return bool(_load_db())
