"""한국 성씨·인명 빈도 결정론 분석 (ADR-029).

보고서 "작명 SaaS 백엔드 결손 영역 보강을 위한 한국 성씨·인명 빈도 통계의
결정론적 분석 및 시스템 통합 보고서" (2026-05-17, 642줄) §5 함수 명세 기반.

목적: 동명이인 회피용 객관 통계 라벨 제공 (very_common·common·uncommon·rare).
인과적 길흉화복 해석 절대 금지 (ADR-010 사실성 분리).

데이터 출처:
  · 통계청 2015년 인구주택총조사 성씨·본관 편 (공공누리 제1유형)
    https://kosis.kr (상업 사용 + 출처표시 필수)
  · 대법원 전자가족관계등록시스템 efamily.scourt.go.kr (ADR-026 영속화)
  · 본 시스템 ADR-016 name_aesthetic_syllable_freq.json (음절 빈도)

라이선스 컴플라이언스:
  · 공공누리 제1유형: 영리 SaaS 사용 허가, 출처표시 의무
  · 텍스트 데이터 (집계 통계): 저작권법 비보호 (사실의 전달)
  · 개인정보 보호: 비식별 집계 데이터만 사용

면책 (ADR-010 의무):
  · 본 점수는 통계청·대법원 공공 통계 기반 객관 빈도 라벨
  · 운명·길흉·사주와 인과관계 X
  · 사용자 출력 시 면책 자동 포함
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

from engine.divination.name_aesthetic import (
    _get_freq_dict,
    _get_positional_freq,
)


# 데이터 경로
_SURNAME_PATH = Path(__file__).parent.parent.parent / "data" / "korean_surname_frequency.json"

# 빈도 임계값 (보고서 §5.3)
THRESHOLD_VERY_COMMON = 300  # 동명이인 추정 ≥ 300 → very_common
THRESHOLD_COMMON = 50         # ≥ 50 → common
THRESHOLD_UNCOMMON = 10       # ≥ 10 → uncommon
# < 10 → rare

# 복성 (보고서 §5.2)
KOREAN_COMPOUND_SURNAMES = frozenset([
    "남궁", "황보", "제갈", "사공", "선우", "독고",
    "동방", "서문", "어금", "장곡", "남궐", "제오",
])

FrequencyLabel = Literal["very_common", "common", "uncommon", "rare"]


@dataclass(frozen=True)
class UniquenessResult:
    """인명 빈도 분석 결과 (불변)."""
    name: str
    gender: str
    surname: str
    given_name: str
    surname_rank: int | None  # 없으면 None (300위 외)
    surname_pct: float | None
    first_syllable_rank: int | None
    last_syllable_rank: int | None
    combined_frequency: FrequencyLabel
    estimated_count: int  # 동명이인 추정 수
    rationale: str  # 면책 자동 포함


# ─────────────────────── 데이터 로드 ───────────────────────


@lru_cache(maxsize=1)
def _load_surname_db() -> dict[str, dict]:
    """data/korean_surname_frequency.json 로드.

    동음이의 성씨(예: 方·龐 둘 다 한글 '방') → 최상위(낮은 rank) 우선.
    """
    if not _SURNAME_PATH.exists():
        return {}
    raw = json.loads(_SURNAME_PATH.read_text(encoding="utf-8"))
    surnames = raw.get("surnames", [])
    out: dict[str, dict] = {}
    for s in surnames:
        key = s["surname"]
        existing = out.get(key)
        # rank 낮은 (상위) 우선
        if existing is None or s.get("rank", 999) < existing.get("rank", 999):
            out[key] = s
    return out


def _surname_info(surname: str) -> dict | None:
    """단일 성씨의 본문 명시 데이터 (없으면 None)."""
    return _load_surname_db().get(surname)


# ─────────────────────── 성씨·이름 분리 ───────────────────────


def split_korean_name(name: str) -> tuple[str, str] | None:
    """한국어 성명 → (성, 이름). 복성 우선 매칭.

    Examples:
        split_korean_name("김민준") == ("김", "민준")
        split_korean_name("남궁민") == ("남궁", "민")
        split_korean_name("이서연") == ("이", "서연")
    """
    if not name or len(name) < 2:
        return None
    # 복성 우선 (2글자 surname)
    if len(name) >= 3:
        prefix2 = name[:2]
        if prefix2 in KOREAN_COMPOUND_SURNAMES:
            return (prefix2, name[2:])
    # 단성 (1글자)
    return (name[0], name[1:])


# ─────────────────────── 빈도 라벨링 ───────────────────────


def _surname_rank_or_none(surname: str) -> tuple[int | None, float | None]:
    """성씨 → (rank, pct) 또는 (None, None) — DB 미수록."""
    info = _surname_info(surname)
    if info is None:
        return (None, None)
    return (info.get("rank"), info.get("pct"))


def _syllable_rank(syllable: str, gender: str, position: str) -> int | None:
    """음절의 위치별 순위 (1위가 최빈) 또는 None — 데이터 없음."""
    if not syllable or gender not in ("male", "female", "neutral"):
        return None
    if position == "first":
        freq = _get_positional_freq(gender, "first")
    elif position == "last":
        freq = _get_positional_freq(gender, "last")
    else:
        freq = _get_freq_dict(gender)
    if syllable not in freq:
        return None
    # 순위 = 자기보다 빈도 높은 음절 수 + 1
    self_count = freq[syllable]
    return sum(1 for c in freq.values() if c > self_count) + 1


def _estimate_homonym_count(
    surname_pct: float | None,
    first_rank: int | None,
    last_rank: int | None,
    total_pop: int = 49_705_663,
) -> int:
    """동명이인 추정 수 (보고서 §5.1 결합 확률).

    P(name) ≈ P(surname) × P(syllable_position) × γ (쏠림 보정)

    매우 보수적 추정 — 실제 측정 X. 임계값 라벨링 용도.
    음절 데이터 미수록 시 보수적 평균 추정 (uncommon 영역).
    """
    if surname_pct is None:
        # 성씨 미수록 → 매우 희소 (보고서 §3 150위권 0.001%)
        surname_pct = 0.001

    # 음절 순위 → 확률 추정 (1위 ≈ 5%, 10위 ≈ 1%, 50위 ≈ 0.1%)
    def rank_to_pct(r: int | None) -> float:
        if r is None:
            return 0.001  # 데이터 미수록 보수적 평균 (uncommon 추정)
        if r > 500:
            return 0.0001
        if r == 1:
            return 0.05
        if r <= 5:
            return 0.03
        if r <= 10:
            return 0.01
        if r <= 50:
            return 0.005
        if r <= 100:
            return 0.001
        return 0.0001

    fs_pct = rank_to_pct(first_rank)
    ls_pct = rank_to_pct(last_rank)
    # 둘 다 None이면 데이터 보수적 (uncommon 추정)
    if first_rank is None and last_rank is None:
        joint_pct = 0.001
    else:
        # 한쪽만 있으면 그 값 사용 (보고서 §6 freq_004 패턴: last만)
        joint_pct = max(fs_pct, ls_pct)

    estimated = int(total_pop * (surname_pct / 100) * joint_pct)
    return max(estimated, 0)


def _classify_frequency(estimated_count: int) -> FrequencyLabel:
    """동명이인 수 → 빈도 라벨 (보고서 §5.3 임계값)."""
    if estimated_count >= THRESHOLD_VERY_COMMON:
        return "very_common"
    if estimated_count >= THRESHOLD_COMMON:
        return "common"
    if estimated_count >= THRESHOLD_UNCOMMON:
        return "uncommon"
    return "rare"


def _build_rationale(
    name: str,
    surname: str,
    rank: int | None,
    label: FrequencyLabel,
    estimated_count: int,
) -> str:
    """ADR-010 면책 자동 포함 사용자 출력."""
    label_korean = {
        "very_common": "매우 흔한",
        "common": "흔한",
        "uncommon": "다소 희소한",
        "rare": "희귀한",
    }[label]
    if rank is not None:
        rank_phrase = f"성씨 빈도 {rank}위"
    else:
        rank_phrase = "성씨 빈도 통계 미수록 (희귀 성씨)"
    return (
        f"'{name}'은 통계청 2015년 인구주택총조사 기준 {rank_phrase}, "
        f"추정 동명이인 약 {estimated_count}명으로 '{label_korean}' 이름으로 분류됩니다. "
        f"※ 본 분류는 공공 통계 기반 객관 빈도 라벨이며, "
        f"이름의 운명·길흉·사주와 어떠한 인과관계도 없습니다. "
        f"동명이인 회피를 위한 참고 지표로만 활용하시기 바랍니다."
    )


# ─────────────────────── Public API ───────────────────────


def name_uniqueness_score(
    name: str,
    gender: Literal["male", "female", "neutral"] = "neutral",
    year: int | None = None,
) -> UniquenessResult | None:
    """한국어 성명의 빈도 결정론 분석.

    Args:
        name: 성명 (성+이름).
        gender: 음절 빈도 조회용 ('male'·'female'·'neutral').
        year: 출생 연도 — 현재 미사용 (시계열 데이터 없음). 향후 ADR.

    Returns:
        UniquenessResult 또는 None (분리 실패).

    Examples:
        name_uniqueness_score("김민준", gender="male")
            → UniquenessResult(combined_frequency='very_common', ...)
        name_uniqueness_score("옹지원", gender="female")
            → UniquenessResult(combined_frequency='rare', ...)
    """
    split = split_korean_name(name)
    if split is None:
        return None
    surname, given_name = split
    if not given_name:
        return None

    surname_rank, surname_pct = _surname_rank_or_none(surname)

    # 첫 음절·끝 음절 순위
    first_syl = given_name[0] if given_name else ""
    last_syl = given_name[-1] if given_name else ""
    fs_rank = _syllable_rank(first_syl, gender, "first") if first_syl else None
    ls_rank = _syllable_rank(last_syl, gender, "last") if last_syl else None

    estimated = _estimate_homonym_count(surname_pct, fs_rank, ls_rank)
    label = _classify_frequency(estimated)
    rationale = _build_rationale(name, surname, surname_rank, label, estimated)

    return UniquenessResult(
        name=name,
        gender=gender,
        surname=surname,
        given_name=given_name,
        surname_rank=surname_rank,
        surname_pct=surname_pct,
        first_syllable_rank=fs_rank,
        last_syllable_rank=ls_rank,
        combined_frequency=label,
        estimated_count=estimated,
        rationale=rationale,
    )


def total_surnames() -> int:
    """본문화된 성씨 수 (보고서 §3 명시 15건)."""
    return len(_load_surname_db())


def surname_rank(surname: str) -> int | None:
    """성씨 순위 (미수록 시 None)."""
    info = _surname_info(surname)
    return info.get("rank") if info else None


def is_compound_surname(surname: str) -> bool:
    """복성 여부 (보고서 §5.2 12종)."""
    return surname in KOREAN_COMPOUND_SURNAMES


def is_loaded() -> bool:
    return bool(_load_surname_db())
