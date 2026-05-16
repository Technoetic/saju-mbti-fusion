"""개명(改名) 트랙 — 보고서 §5-A 본문화.

개자(改字)와의 차이:
  · 개자(name_gaeja): 한글 발음 고정 + 한자만 swap (사회적 마찰 0)
  · 개명(name_gaemyeong): **한글 발음·한자 모두 새로** 짓기

알고리즘 (보고서 §5-A 5단계):
  1. 성씨 발음오행 기준 상생 흐름 한글 조합 1차 생성 (이름 2자)
  2. 각 한글 음절에 매핑되는 한자 후보 풀 매핑
  3. Hard filter: 불용한자 + 미수록 제외
  4. 81수리 4격 + 음양 조화 + 자원오행 매칭 검증
  5. 다차원 스코어링 → 상위 N개 큐레이션

운영표준:
  · 결정론 (재현성)
  · LLM 무관
  · 발음 풀이 매우 커서 조합 폭발 위험 → 발음오행 상생 필터로 1차 압축
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Any

from engine.divination.name_bulyong import is_bulyong
from engine.divination.name_strokes import kangxi_strokes, resource_ohaeng
from engine.divination.name_scoring import calc_four_gyeok
from engine.divination.name_eumyang import evaluate_eumyang, GRADE_BAD as EUMYANG_BAD
from engine.divination.name_baleum import (
    syllable_to_ohaeng,
    WOOD, FIRE, EARTH, METAL, WATER,
)


@dataclass(frozen=True)
class GaemyeongCandidate:
    """단일 개명 후보."""
    surname_hanja: str
    surname_korean: str
    given_korean: str          # 새 한글 이름
    given_hanja: str           # 새 한자
    full_hanja: str
    full_korean: str
    strokes: list[int]
    baleum_grade: str          # 발음오행 등급
    eumyang_grade: str
    ohaeng_match_count: int
    score: float


@dataclass(frozen=True)
class GaemyeongResult:
    surname_hanja: str
    surname_korean: str
    candidates: list[GaemyeongCandidate] = field(default_factory=list)
    total_combinations: int = 0
    filtered_count: int = 0


# ─────────────────────────── 발음 상생 흐름 ───────────────────────────

# 상생: 木→火→土→金→水→(木)
_SANGSAENG_NEXT: dict[str, str] = {
    WOOD: FIRE, FIRE: EARTH, EARTH: METAL, METAL: WATER, WATER: WOOD,
}


def _hangul_pool_by_ohaeng(
    candidate_pool: dict[str, list[str]],
) -> dict[str, list[str]]:
    """한글음→한자 dict을 오행→한글음 dict로 역인덱싱.

    예: {木: ['김', '강', '계', ...], 火: ['남', '도', '란', ...], ...}
    """
    out: dict[str, list[str]] = {WOOD: [], FIRE: [], EARTH: [], METAL: [], WATER: []}
    for syllable in candidate_pool:
        o = syllable_to_ohaeng(syllable)
        if o in out:
            out[o].append(syllable)
    return out


# ─────────────────────────── 단일 조합 평가 ───────────────────────────

def _score_combo(
    surname_strokes: list[int],
    surname_korean: str,
    given_korean: str,
    given_strokes: list[int],
    given_hanja_chars: list[str],
    target_ohaeng: str | None,
) -> tuple[bool, float, str, int]:
    """단일 한글+한자 조합 평가.

    Returns:
        (passes_hard, score, eumyang_grade, ohaeng_match_count)
    """
    # 4격
    four = calc_four_gyeok(surname_strokes, given_strokes)
    if not four.all_good:
        return (False, 0.0, "", 0)

    # 음양
    ey = evaluate_eumyang(surname_strokes + given_strokes)
    if ey.grade == EUMYANG_BAD:
        return (False, 0.0, ey.grade, 0)

    # 자원오행 매칭
    match_count = 0
    if target_ohaeng:
        for ch in given_hanja_chars:
            if resource_ohaeng(ch) == target_ohaeng:
                match_count += 1

    score = 0.5  # 4격 모두 GOOD
    if given_hanja_chars:
        score += 0.5 * (match_count / len(given_hanja_chars))

    return (True, score, ey.grade, match_count)


# ─────────────────────────── 통합 진입점 ───────────────────────────

def find_gaemyeong_candidates(
    *,
    surname_hanja: str,
    surname_korean: str,
    candidate_pool: dict[str, list[str]],
    target_ohaeng: str | None = None,
    given_length: int = 2,
    require_baleum_sangsaeng: bool = True,
    top_n: int = 10,
    max_combinations: int = 50000,
) -> GaemyeongResult:
    """개명 트랙 — 발음+한자 모두 새로 생성.

    Args:
        surname_hanja: 성씨 한자 (고정).
        surname_korean: 성씨 한글.
        candidate_pool: {한글음: [한자 후보]} 사전.
        target_ohaeng: 목표 자원오행 (선택).
        given_length: 이름 글자 수 (보통 2, 외자면 1).
        require_baleum_sangsaeng: True면 성→이름1→이름2 발음오행이
            상생 흐름인 한글 조합만 생성. False면 모든 조합.
        top_n: 반환 상위 N개.
        max_combinations: 조합 폭발 방지 상한.

    Returns:
        GaemyeongResult — 상위 N개 추천 (점수 내림차순).
    """
    surname_strokes_raw = kangxi_strokes(surname_hanja)
    if surname_strokes_raw is None:
        return GaemyeongResult(
            surname_hanja=surname_hanja, surname_korean=surname_korean,
        )
    surname_strokes = [surname_strokes_raw]

    # 성씨 발음오행
    surname_ohaeng = syllable_to_ohaeng(surname_korean)

    # 한글 음절 풀 — 오행별 인덱싱
    by_ohaeng = _hangul_pool_by_ohaeng(candidate_pool)

    # 1) 발음오행 상생 흐름 한글 조합 생성
    syllable_combos: list[tuple[str, ...]] = []
    if require_baleum_sangsaeng and surname_ohaeng:
        # 성씨 → 이름1 상생 → 이름2 상생
        next_o = _SANGSAENG_NEXT.get(surname_ohaeng)
        if next_o is None:
            return GaemyeongResult(
                surname_hanja=surname_hanja, surname_korean=surname_korean,
            )
        if given_length == 1:
            for s1 in by_ohaeng.get(next_o, []):
                syllable_combos.append((s1,))
        else:
            next2_o = _SANGSAENG_NEXT.get(next_o)
            if next2_o is None:
                return GaemyeongResult(
                    surname_hanja=surname_hanja, surname_korean=surname_korean,
                )
            for s1 in by_ohaeng.get(next_o, []):
                for s2 in by_ohaeng.get(next2_o, []):
                    syllable_combos.append((s1, s2))
    else:
        # 발음 필터 없이 모든 음절 조합 (조합 폭발 주의)
        all_syllables = list(candidate_pool.keys())
        if given_length == 1:
            syllable_combos = [(s,) for s in all_syllables]
        else:
            for s1 in all_syllables:
                for s2 in all_syllables:
                    syllable_combos.append((s1, s2))

    # 2) 각 한글 조합 + 한자 조합 평가
    all_candidates: list[GaemyeongCandidate] = []
    total = 0
    for syl_combo in syllable_combos:
        # 음절별 한자 후보
        per_syllable_pools = []
        skip = False
        for syl in syl_combo:
            raw = candidate_pool.get(syl, [])
            filtered = [h for h in raw if not is_bulyong(h) and kangxi_strokes(h) is not None]
            if not filtered:
                skip = True
                break
            per_syllable_pools.append(filtered)
        if skip:
            continue

        for hanja_combo in product(*per_syllable_pools):
            total += 1
            if total > max_combinations:
                break

            given_chars = list(hanja_combo)
            given_strokes = [kangxi_strokes(c) for c in given_chars]
            if any(s is None for s in given_strokes):
                continue
            given_strokes_int = [s for s in given_strokes if s is not None]

            given_korean = "".join(syl_combo)
            passes, score, ey_grade, match = _score_combo(
                surname_strokes, surname_korean, given_korean,
                given_strokes_int, given_chars, target_ohaeng,
            )
            if not passes:
                continue

            # 발음오행 등급은 항상 GOOD (상생 흐름 강제 시) 또는 분석
            baleum_grade = "good" if require_baleum_sangsaeng else ""

            all_candidates.append(GaemyeongCandidate(
                surname_hanja=surname_hanja,
                surname_korean=surname_korean,
                given_korean=given_korean,
                given_hanja="".join(given_chars),
                full_hanja=surname_hanja + "".join(given_chars),
                full_korean=surname_korean + given_korean,
                strokes=surname_strokes + given_strokes_int,
                baleum_grade=baleum_grade,
                eumyang_grade=ey_grade,
                ohaeng_match_count=match,
                score=round(score, 3),
            ))

        if total > max_combinations:
            break

    all_candidates.sort(key=lambda c: (c.score, c.ohaeng_match_count), reverse=True)
    top = all_candidates[:top_n]

    return GaemyeongResult(
        surname_hanja=surname_hanja,
        surname_korean=surname_korean,
        candidates=top,
        total_combinations=total,
        filtered_count=len(all_candidates),
    )


def result_to_dict(result: GaemyeongResult) -> dict[str, Any]:
    """JSON 직렬화."""
    def _c(c: GaemyeongCandidate) -> dict[str, Any]:
        return {
            "surname_hanja": c.surname_hanja,
            "surname_korean": c.surname_korean,
            "given_korean": c.given_korean,
            "given_hanja": c.given_hanja,
            "full_hanja": c.full_hanja,
            "full_korean": c.full_korean,
            "strokes": list(c.strokes),
            "baleum_grade": c.baleum_grade,
            "eumyang_grade": c.eumyang_grade,
            "ohaeng_match_count": c.ohaeng_match_count,
            "score": c.score,
        }
    return {
        "surname_hanja": result.surname_hanja,
        "surname_korean": result.surname_korean,
        "candidates": [_c(c) for c in result.candidates],
        "total_combinations": result.total_combinations,
        "filtered_count": result.filtered_count,
    }
