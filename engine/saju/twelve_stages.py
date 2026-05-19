# -*- coding: utf-8 -*-
"""십이운성(十二運星) 결정론 매핑 모듈 (ADR-031).

자평진전(子平眞詮) 학파 표준 — 양순음역 + 화토동궁 원칙.

12단계 (生老病死 비유):
  태(胎)·양(養)·장생(長生)·목욕(沐浴)·관대(冠帶)·건록(建祿)
  ·제왕(帝旺)·쇠(衰)·병(病)·사(死)·묘(墓)·절(絶)

매핑 원칙:
  · 양간(甲丙戊庚壬): 시계 방향 순행
  · 음간(乙丁己辛癸): 반시계 방향 역행
  · 화토동궁: 戊=丙 궤적, 己=丁 궤적

학술 출처 (KCI 라이브 검증 통과):
  · 최산태·김만태 (2021) 영산대 동양문화연구 — NODE10738496 (화토동궁)
  · 김계성 (2016) 단국대 동양학 제65호 — NODE08998998 (양순음역)

ADR 정합:
  · ADR-002 (학파 회피): 자평진전 단일 학파 명시 → ADR-015 옵션 B 패턴 예외
  · ADR-010 (사실성 분리): 12단계는 객관 라벨, 운명 단정 X
  · ADR-015 (옵션 B 병행): 자평진전 명시 채택, 옵션 A(단순 오행) 디폴트 병행
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

# 데이터 경로
_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "saju/twelve_stages_mapping.json"

# 천간/지지 한자 시퀀스
_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
_JI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 12단계 (한자 + 한글)
STAGES = ("장생", "목욕", "관대", "건록", "제왕", "쇠", "병", "사", "묘", "절", "태", "양")

Stage = Literal["장생", "목욕", "관대", "건록", "제왕", "쇠", "병", "사", "묘", "절", "태", "양"]


@dataclass(frozen=True)
class TwelveStageResult:
    """십이운성 매핑 결과 (불변).

    day_stem: 일간 (10천간 중 1)
    branch: 지지 (12지지 중 1)
    stage: 12단계 라벨
    school: "자평진전 (양순음역 + 화토동궁)"
    rationale: 사용자 출력 (학파 명시 + ADR-010 면책)
    """
    day_stem: str
    branch: str
    stage: str
    school: str
    rationale: str


# ───────────────────── 데이터 로드 ─────────────────────


@lru_cache(maxsize=1)
def _load_mapping() -> dict:
    """data/twelve_stages_mapping.json 로드."""
    if not _DATA_PATH.exists():
        return {}
    return json.loads(_DATA_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _table() -> dict[str, dict[str, str]]:
    """{day_stem: {branch: stage}}"""
    data = _load_mapping()
    return data.get("twelve_stages_table", {})


# ───────────────────── 핵심 매핑 함수 ─────────────────────


def get_twelve_stage(day_stem: str, branch: str) -> str | None:
    """일간 + 지지 → 십이운성 라벨.

    Args:
        day_stem: 일간 한자 (예: '甲'·'乙')
        branch: 지지 한자 (예: '子'·'亥')

    Returns:
        12단계 한글 라벨 또는 None (잘못된 입력).

    Examples:
        get_twelve_stage('甲', '亥') == '장생'
        get_twelve_stage('壬', '子') == '제왕'
        get_twelve_stage('癸', '辰') == '양'
    """
    if not day_stem or not branch:
        return None
    tbl = _table().get(day_stem)
    if tbl is None:
        return None
    return tbl.get(branch)


def evaluate_four_pillars_stages(
    day_stem: str,
    year_branch: str,
    month_branch: str,
    day_branch: str,
    hour_branch: str,
) -> dict[str, str | None]:
    """4주(년·월·일·시) 십이운성 종합 평가.

    Returns:
        {year_stage, month_stage, day_stage, hour_stage} dict
        각 값은 12단계 한글 또는 None.
    """
    return {
        "year_stage": get_twelve_stage(day_stem, year_branch),
        "month_stage": get_twelve_stage(day_stem, month_branch),
        "day_stage": get_twelve_stage(day_stem, day_branch),
        "hour_stage": get_twelve_stage(day_stem, hour_branch),
    }


def get_twelve_stage_with_rationale(day_stem: str, branch: str) -> TwelveStageResult | None:
    """학파 명시 + ADR-010 면책 자동 포함 매핑.

    Returns:
        TwelveStageResult 또는 None.
    """
    stage = get_twelve_stage(day_stem, branch)
    if stage is None:
        return None
    return TwelveStageResult(
        day_stem=day_stem,
        branch=branch,
        stage=stage,
        school="자평진전 (양순음역 + 화토동궁)",
        rationale=_build_rationale(day_stem, branch, stage),
    )


def _build_rationale(day_stem: str, branch: str, stage: str) -> str:
    """ADR-010 면책 자동 포함 사용자 출력."""
    return (
        f"일간 '{day_stem}'이 지지 '{branch}'을 만났을 때, "
        f"자평진전 학파 기준 십이운성 단계는 '{stage}'으로 분류됩니다. "
        f"※ 본 결과는 자평진전 단일 학파(양순음역 + 화토동궁)의 객관적 매핑이며, "
        f"개인의 운명·수명·길흉화복과 인과관계는 없습니다. "
        f"타 학파(동생동사·수토동궁 등) 이견이 존재합니다. "
        f"사(死)·묘(墓) 단계는 실제 죽음이 아닌 기운의 추상적 상태를 의미합니다."
    )


# ───────────────────── 메타 ─────────────────────


def total_mappings() -> int:
    """본문화된 매핑 수 (10 × 12 = 120)."""
    return sum(len(v) for v in _table().values())


def total_stems() -> int:
    """본문화된 천간 수 (10)."""
    return len(_table())


def is_valid_stem(stem: str) -> bool:
    return stem in _GAN


def is_valid_branch(branch: str) -> bool:
    return branch in _JI


def is_loaded() -> bool:
    return bool(_table())


def list_stages() -> tuple[str, ...]:
    """12단계 순서대로."""
    return STAGES


def kci_sources() -> dict[str, str]:
    """학술 출처 (사용자 출력 시 노출 가능)."""
    data = _load_mapping()
    return data.get("kci_sources", {})
