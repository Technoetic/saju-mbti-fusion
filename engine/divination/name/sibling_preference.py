"""가족 서열별 한자 선호 모듈 — 결정론 진단 (ADR-010).

본 모듈은 한국 정통 작명 관습에서 **형제 호칭 위계(백중숙계)**와 직접 연관된
한자가 사용자 가족 서열과 부적합한 경우 참고용 표시를 반환한다.

⚠️ 본 모듈의 분류는 전통 관습 참고용이며, 다음을 **하지 않는다**:
  · 인과적 흉화 예언 (단명·관재·신체 훼손 등)
  · 의료·법률 자문 (ADR-006 준수)
  · "절대적 흉" 단정

사용자 출력에는 항상 다음 표현을 사용한다:
  · "○○ 서열에 더 자주 사용되는 글자입니다."
  · "○○ 서열에서는 사용 빈도가 낮은 글자입니다."
  · "참고용이며 의료·법률 자문이 아닙니다."

데이터 출처: data/name_sibling_preference.json (ADR-010 사실성 분리 적용)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


# ─────────────────────────── 상수 ───────────────────────────

# 카테고리
CATEGORY_FIRSTBORN = "firstborn_only"
CATEGORY_LASTBORN = "lastborn_only"
CATEGORY_MIDDLEBORN = "middleborn_only"
CATEGORY_ONLY_CHILD = "only_child_only"

# 부적합도 (보고서의 흉화 강도 → 호칭 직접성으로 재정의)
SEVERITY_STRONG = "STRONG"           # 호칭 의미 직접 (예: 伯=맏, 季=막내)
SEVERITY_WEAK = "WEAK"               # 호칭 함의 (예: 大=큼, 小=작음)
SEVERITY_CONDITIONAL = "CONDITIONAL" # 사주·조건부 적용

# 외동 정책 (1-D 카테고리에만 존재)
POLICY_HARD_BLOCK_ALWAYS = "hard_block_always"     # 형제 유무 무관 표시
POLICY_ONLY_CHILD_PASS = "only_child_pass"          # 외동에 적합 (길자 전환)
POLICY_ONLY_CHILD_WARNING = "only_child_warning"    # 외동도 주의

# 사용자 서열 (입력 enum)
SIBLING_FIRSTBORN = "firstborn"
SIBLING_MIDDLEBORN = "middleborn"
SIBLING_LASTBORN = "lastborn"
SIBLING_ONLY_CHILD = "only_child"


# ─────────────────────────── 데이터 모델 ───────────────────────────


@dataclass(frozen=True)
class SiblingEntry:
    """단일 한자의 서열 선호 정보."""
    char: str
    reading: str
    meaning: str
    category: str
    gender: str           # male / female / neutral
    severity: str         # STRONG / WEAK / CONDITIONAL
    reason: str           # 객관 묘사 (인과 주장 없음)
    sources: tuple[str, ...]
    policy: str | None = None   # only_child_only 카테고리에만 존재


@dataclass(frozen=True)
class SiblingDiagnosis:
    """진단 결과 — 사용자 노출 + 시스템 내부 처리 분리."""
    char: str
    is_match: bool                # 서열과 호칭이 일치 (또는 부적합 아님)
    severity: str | None          # 부적합 시 강도, 적합 시 None
    user_message: str             # 사용자 노출 문구 (객관 묘사)
    internal_reason: str          # 시스템 로그용 사유
    entry: SiblingEntry | None    # 매칭된 DB 엔트리, 없으면 None
    applied_exceptions: tuple[str, ...] = ()  # 적용된 현대 가정 예외 명


# ─────────────────────────── 데이터 로더 ───────────────────────────


_DATA_PATH = Path(__file__).parent.parent.parent.parent / "data" / "name/sibling_preference.json"


@lru_cache(maxsize=1)
def _load_entries() -> dict[str, SiblingEntry]:
    """JSON 데이터 → {char: SiblingEntry} 인덱스. 1회 로드."""
    raw = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    out: dict[str, SiblingEntry] = {}
    for e in raw["entries"]:
        out[e["char"]] = SiblingEntry(
            char=e["char"],
            reading=e["reading"],
            meaning=e["meaning"],
            category=e["category"],
            gender=e["gender"],
            severity=e["severity"],
            reason=e["reason"],
            sources=tuple(e.get("sources", ("전통 관습",))),
            policy=e.get("policy"),
        )
    return out


def lookup(char: str) -> SiblingEntry | None:
    """단일 한자의 서열 엔트리 조회. 없으면 None."""
    return _load_entries().get(char)


def total_entries() -> int:
    """라이브 점검용."""
    return len(_load_entries())


# ─────────────────────────── 현대 가정 예외 처리 ───────────────────────────


def _apply_modern_exceptions(
    sibling_order: str,
    *,
    is_twin: bool = False,
    is_blended_cohabiting: bool = False,
    has_older_brother_as_female: bool = False,
    is_adopted: bool = False,
    gender: str = "neutral",
) -> tuple[str, tuple[str, ...]]:
    """현대 가정 형태에 따라 sibling_order를 변환.

    Returns:
        (effective_sibling_order, applied_exceptions)
    """
    applied: list[str] = []
    effective = sibling_order

    # 큰누나 (여성 + 위에 오빠 1명 이상) → middleborn으로 downcast
    if (
        gender == "female"
        and sibling_order == SIBLING_FIRSTBORN
        and has_older_brother_as_female
    ):
        effective = SIBLING_MIDDLEBORN
        applied.append("eldest_sister_with_older_brother")

    # 입양아: 호적 100% 우선 — 입력값(sibling_order)을 그대로 신뢰.
    # 이 함수에서는 별도 변환 없음. 호출부에서 호적 서열을 sibling_order로 전달.
    if is_adopted:
        applied.append("adopted_uses_legal_order")

    # 재혼·이복 거주: 입력 서열 유지 + 플래그만 표시 (호출부에서 추가 권고 가능)
    if is_blended_cohabiting:
        applied.append("blended_cohabiting")

    # 쌍둥이: 출산 순서 유지, 단 severity 1단계 완화는 별도 함수에서 처리
    if is_twin:
        applied.append("twin_severity_softened")

    return effective, tuple(applied)


def _soften_severity_for_twin(severity: str) -> str:
    """쌍둥이의 경우 STRONG → WEAK로 1단계 하향."""
    if severity == SEVERITY_STRONG:
        return SEVERITY_WEAK
    return severity


# ─────────────────────────── 메시지 빌더 (객관 묘사) ───────────────────────────


def _build_user_message(
    entry: SiblingEntry,
    is_match: bool,
    severity: str | None,
) -> str:
    """사용자 노출 문구 생성 — 인과 주장 절대 금지."""
    if is_match:
        # 외동 적합 길자 케이스
        if entry.category == CATEGORY_ONLY_CHILD and entry.policy == POLICY_ONLY_CHILD_PASS:
            return f"'{entry.char}'({entry.reading})은(는) 외동에 자주 사용되는 글자입니다. 참고용입니다."
        return f"'{entry.char}'({entry.reading})은(는) 해당 서열에 부적합 표시가 없습니다."

    # 부적합 케이스
    cat_label = {
        CATEGORY_FIRSTBORN: "첫째(장자)",
        CATEGORY_LASTBORN: "막내",
        CATEGORY_MIDDLEBORN: "둘째 이하 중간 서열",
        CATEGORY_ONLY_CHILD: "외동",
    }.get(entry.category, entry.category)

    intensity = {
        SEVERITY_STRONG: "전통 관념상 ",
        SEVERITY_WEAK: "전통 관념상 다소 ",
        SEVERITY_CONDITIONAL: "사주에 따라 ",
    }.get(severity or "", "")

    return (
        f"'{entry.char}'({entry.reading}, {entry.meaning})은(는) "
        f"{intensity}{cat_label} 호칭에서 유래한 글자입니다. "
        "참고용이며 의료·법률 자문이 아닙니다."
    )


# ─────────────────────────── 진단 메인 ───────────────────────────


def diagnose_char(
    char: str,
    sibling_order: str,
    *,
    gender: str = "neutral",
    is_twin: bool = False,
    is_blended_cohabiting: bool = False,
    has_older_brother_as_female: bool = False,
    is_adopted: bool = False,
) -> SiblingDiagnosis:
    """한 글자에 대한 서열 부적합 진단.

    Args:
        char: 한자 1자
        sibling_order: 'firstborn' | 'middleborn' | 'lastborn' | 'only_child'
        gender: 'male' | 'female' | 'neutral' (사용자 성별)
        is_twin: 쌍둥이 여부 — severity 1단계 완화
        is_blended_cohabiting: 재혼+이복 동거 여부 — 권고 플래그
        has_older_brother_as_female: 여성+위 오빠 있음 → middleborn downcast
        is_adopted: 입양 여부 — 호적 서열 사용 표시
    """
    entry = lookup(char)
    if entry is None:
        # DB 미등록 한자 — 부적합 아님
        return SiblingDiagnosis(
            char=char,
            is_match=True,
            severity=None,
            user_message=f"'{char}'은(는) 서열 호칭 DB에 등록되지 않은 글자입니다.",
            internal_reason="not_in_db",
            entry=None,
        )

    effective_order, applied = _apply_modern_exceptions(
        sibling_order,
        is_twin=is_twin,
        is_blended_cohabiting=is_blended_cohabiting,
        has_older_brother_as_female=has_older_brother_as_female,
        is_adopted=is_adopted,
        gender=gender,
    )

    # ─── 외동 전용 처리 (1-D 카테고리) ───
    if entry.category == CATEGORY_ONLY_CHILD:
        if entry.policy == POLICY_HARD_BLOCK_ALWAYS:
            # 형제 유무 무관 — 항상 부적합
            return SiblingDiagnosis(
                char=char,
                is_match=False,
                severity=entry.severity,
                user_message=_build_user_message(entry, False, entry.severity),
                internal_reason=f"hard_block_always:{entry.reason}",
                entry=entry,
                applied_exceptions=applied,
            )
        if entry.policy == POLICY_ONLY_CHILD_PASS:
            # 외동만 적합, 다자녀는 부적합
            if effective_order == SIBLING_ONLY_CHILD:
                return SiblingDiagnosis(
                    char=char,
                    is_match=True,
                    severity=None,
                    user_message=_build_user_message(entry, True, None),
                    internal_reason="only_child_pass:matched",
                    entry=entry,
                    applied_exceptions=applied,
                )
            return SiblingDiagnosis(
                char=char,
                is_match=False,
                severity=entry.severity,
                user_message=_build_user_message(entry, False, entry.severity),
                internal_reason="only_child_pass:not_only_child",
                entry=entry,
                applied_exceptions=applied,
            )
        if entry.policy == POLICY_ONLY_CHILD_WARNING:
            # 외동도 약한 부적합
            return SiblingDiagnosis(
                char=char,
                is_match=False,
                severity=SEVERITY_WEAK,
                user_message=_build_user_message(entry, False, SEVERITY_WEAK),
                internal_reason="only_child_warning",
                entry=entry,
                applied_exceptions=applied,
            )

    # ─── 일반 카테고리 (firstborn/middleborn/lastborn) ───
    category_to_order = {
        CATEGORY_FIRSTBORN: SIBLING_FIRSTBORN,
        CATEGORY_LASTBORN: SIBLING_LASTBORN,
        CATEGORY_MIDDLEBORN: SIBLING_MIDDLEBORN,
    }
    expected_order = category_to_order.get(entry.category)

    # 카테고리와 사용자 서열이 일치 → 적합
    if expected_order == effective_order:
        return SiblingDiagnosis(
            char=char,
            is_match=True,
            severity=None,
            user_message=_build_user_message(entry, True, None),
            internal_reason="match",
            entry=entry,
            applied_exceptions=applied,
        )

    # 외동은 형제 호칭 자체가 비적용 → 통과
    if effective_order == SIBLING_ONLY_CHILD:
        return SiblingDiagnosis(
            char=char,
            is_match=True,
            severity=None,
            user_message=f"'{char}'({entry.reading})은(는) 형제 호칭 한자이나, 외동에게는 적용되지 않습니다.",
            internal_reason="only_child_skips_sibling_categories",
            entry=entry,
            applied_exceptions=applied,
        )

    # 성별 추가 검증: gender가 명시되어 있고 사용자 성별과 불일치
    gender_mismatch = entry.gender in ("male", "female") and entry.gender != gender

    # severity 결정 (쌍둥이 완화 적용)
    severity = entry.severity
    if is_twin:
        severity = _soften_severity_for_twin(severity)

    internal = f"category_mismatch:{entry.category}_vs_{effective_order}"
    if gender_mismatch:
        internal += f";gender_mismatch:{entry.gender}_vs_{gender}"

    return SiblingDiagnosis(
        char=char,
        is_match=False,
        severity=severity,
        user_message=_build_user_message(entry, False, severity),
        internal_reason=internal,
        entry=entry,
        applied_exceptions=applied,
    )


def diagnose_name(
    name_hanja: str,
    sibling_order: str,
    *,
    gender: str = "neutral",
    is_twin: bool = False,
    is_blended_cohabiting: bool = False,
    has_older_brother_as_female: bool = False,
    is_adopted: bool = False,
) -> dict[str, Any]:
    """이름 전체 한자에 대한 서열 진단.

    Returns:
        {
          "name_hanja": str,
          "sibling_order": str,
          "results": [SiblingDiagnosis, ...],
          "any_strong_mismatch": bool,
          "summary": str  # 사용자 노출 요약
        }
    """
    results = [
        diagnose_char(
            ch,
            sibling_order,
            gender=gender,
            is_twin=is_twin,
            is_blended_cohabiting=is_blended_cohabiting,
            has_older_brother_as_female=has_older_brother_as_female,
            is_adopted=is_adopted,
        )
        for ch in name_hanja
    ]
    any_strong = any(
        not r.is_match and r.severity == SEVERITY_STRONG for r in results
    )
    any_mismatch = any(not r.is_match for r in results)

    if any_strong:
        summary = "이름에 서열 호칭과 불일치 표시가 있는 글자가 있습니다. 참고용이며 의료·법률 자문이 아닙니다."
    elif any_mismatch:
        summary = "이름에 서열 관습상 약한 부적합 표시가 있습니다. 참고용입니다."
    else:
        summary = "이름에 서열 호칭 부적합 표시가 없습니다."

    return {
        "name_hanja": name_hanja,
        "sibling_order": sibling_order,
        "results": results,
        "any_strong_mismatch": any_strong,
        "any_mismatch": any_mismatch,
        "summary": summary,
    }
