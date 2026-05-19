"""개자(改字) 트랙 — 보고서 §5-B 본문화.

핵심 차별화 기능: 한글 발음은 유지하고 한자만 성명학적으로 더 좋은 글자로
교체. 사회적 마찰비용 0.

알고리즘:
  1. 타겟 발음 고정 (사용자 입력 한글 그대로)
  2. 각 음절별 대법원 인명용 한자 후보 스캔
  3. Hard filter:
     - 불용한자 제외
     - 미수록(원획수 없음) 제외
  4. 조합 평가:
     - 81수리 4격 모두 길수
     - 음양 조화 (BAD 제외)
     - 자원오행 목표(용신)와 일치하는지 점수
  5. 상위 N개 추천

본 모듈은 한자 후보 dict을 **외부 주입**받는 구조. 프론트의 한글음_한자
사전이나 별도 DB를 호출자가 전달.

운영표준:
  · 결정론 (재현성)
  · LLM 무관
  · 발음 고정 → 사회적 마찰 0 (보고서 §5-B 블루오션)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Any

from engine.divination.name.bulyong import is_bulyong
from engine.divination.name.strokes import kangxi_strokes, resource_ohaeng
from engine.divination.name.scoring import calc_four_gyeok
from engine.divination.name.eumyang import evaluate_eumyang, GRADE_BAD


@dataclass(frozen=True)
class GaejaCandidate:
    """단일 개자 후보."""
    surname_hanja: str            # 성씨 한자 (고정)
    given_hanja: str              # 새 이름 한자 (제안)
    full_hanja: str               # 성+이름 합본
    strokes: list[int]            # 글자별 원획수
    four_gyeok_summary: str       # good/neutral/bad
    all_gyeok_good: bool          # 4격 모두 길수
    eumyang_grade: str            # 음양 조화
    ohaeng_match_count: int       # 목표 자원오행 매칭 글자 수
    score: float                  # 종합 점수 (0~1)


@dataclass(frozen=True)
class GaejaResult:
    """개자 트랙 결과."""
    surname_hanja: str
    surname_korean: str
    given_korean: str             # 한글 이름 (고정)
    candidates: list[GaejaCandidate] = field(default_factory=list)
    total_combinations: int = 0   # 평가 시도한 조합 총수
    filtered_count: int = 0       # 통과한 후보 수


# ─────────────────────────── 후보 풀 정제 ───────────────────────────

def filter_hanja_pool(
    syllable_pool: list[str],
) -> list[str]:
    """단일 음절의 한자 후보 풀에서 부적격 제거.

    제거 기준:
      · 불용한자
      · 원획수 미수록 (name_strokes에 없음)
    """
    out = []
    for h in syllable_pool:
        if is_bulyong(h):
            continue
        if kangxi_strokes(h) is None:
            continue
        out.append(h)
    return out


# ─────────────────────────── 단일 조합 평가 ───────────────────────────

def _score_combo(
    surname_strokes: list[int],
    given_strokes: list[int],
    given_hanja_chars: list[str],
    target_ohaeng: str | None,
) -> tuple[bool, float, str, str, int]:
    """단일 한자 조합 평가.

    Returns:
        (passes_hard, score, four_gyeok_summary, eumyang_grade, ohaeng_match_count)
        passes_hard=True여야 후보로 인정.

    Hard 제약:
      · 4격에 흉수 0 (all_good=True)
      · 음양이 극단 BAD가 아님
    Soft 점수:
      · 모든 4격이 GOOD이면 +0.5
      · 자원오행 매칭 글자 수 / 이름 글자 수 × 0.5
    """
    # 4격
    four = calc_four_gyeok(surname_strokes, given_strokes)
    if not four.all_good:
        return (False, 0.0, four.summary_grade, "", 0)

    # 음양
    all_strokes = surname_strokes + given_strokes
    ey = evaluate_eumyang(all_strokes)
    if ey.grade == GRADE_BAD:
        return (False, 0.0, four.summary_grade, ey.grade, 0)

    # 자원오행 매칭
    match_count = 0
    if target_ohaeng:
        for ch in given_hanja_chars:
            if resource_ohaeng(ch) == target_ohaeng:
                match_count += 1

    # 스코어
    score = 0.5  # 4격 모두 GOOD
    if given_hanja_chars:
        score += 0.5 * (match_count / len(given_hanja_chars))

    return (True, score, four.summary_grade, ey.grade, match_count)


# ─────────────────────────── 통합 진입점 ───────────────────────────

def find_gaeja_candidates(
    *,
    surname_hanja: str,
    surname_korean: str,
    given_korean: str,
    candidate_pool: dict[str, list[str]],
    target_ohaeng: str | None = None,
    top_n: int = 10,
) -> GaejaResult:
    """개자 트랙 알고리즘 — 발음 고정, 한자만 swap.

    Args:
        surname_hanja: 성씨 한자 (고정, 보통 1자)
        surname_korean: 성씨 한글 (예: "이")
        given_korean: 이름 한글 (예: "성민")
        candidate_pool: {한글음: [한자 후보 리스트]} dict.
            프론트 한글음_한자 사전 같은 외부 데이터.
        target_ohaeng: 목표 자원오행 (사주 용신, 선택).
            "木"/"火"/"土"/"金"/"水" 중 하나, None이면 자원오행 점수 0.
        top_n: 반환할 최상위 후보 수.

    Returns:
        GaejaResult — 통과한 후보 리스트 (점수 내림차순).
    """
    surname_strokes_raw = kangxi_strokes(surname_hanja)
    if surname_strokes_raw is None:
        return GaejaResult(
            surname_hanja=surname_hanja,
            surname_korean=surname_korean,
            given_korean=given_korean,
            candidates=[],
        )
    surname_strokes = [surname_strokes_raw]

    # 각 음절별 후보 풀 정제
    given_syllables = [s for s in (given_korean or "") if s.strip()]
    per_syllable_pools: list[list[str]] = []
    for syl in given_syllables:
        raw_pool = candidate_pool.get(syl, [])
        filtered = filter_hanja_pool(raw_pool)
        if not filtered:
            # 어느 음절이라도 후보가 없으면 빈 결과
            return GaejaResult(
                surname_hanja=surname_hanja,
                surname_korean=surname_korean,
                given_korean=given_korean,
                candidates=[],
                total_combinations=0,
                filtered_count=0,
            )
        per_syllable_pools.append(filtered)

    # Cross product — 모든 조합 평가
    all_candidates: list[GaejaCandidate] = []
    total = 0
    for combo in product(*per_syllable_pools):
        total += 1
        given_chars = list(combo)
        given_strokes = [kangxi_strokes(ch) for ch in given_chars]
        # 미수록 방어
        if any(s is None for s in given_strokes):
            continue
        given_strokes_int = [s for s in given_strokes if s is not None]

        passes, score, four_summary, ey_grade, match = _score_combo(
            surname_strokes, given_strokes_int, given_chars, target_ohaeng,
        )
        if not passes:
            continue

        all_candidates.append(GaejaCandidate(
            surname_hanja=surname_hanja,
            given_hanja="".join(given_chars),
            full_hanja=surname_hanja + "".join(given_chars),
            strokes=surname_strokes + given_strokes_int,
            four_gyeok_summary=four_summary,
            all_gyeok_good=True,
            eumyang_grade=ey_grade,
            ohaeng_match_count=match,
            score=round(score, 3),
        ))

    # 점수 내림차순 → top_n
    all_candidates.sort(key=lambda c: (c.score, c.ohaeng_match_count), reverse=True)
    top = all_candidates[:top_n]

    return GaejaResult(
        surname_hanja=surname_hanja,
        surname_korean=surname_korean,
        given_korean=given_korean,
        candidates=top,
        total_combinations=total,
        filtered_count=len(all_candidates),
    )


def result_to_dict(result: GaejaResult) -> dict[str, Any]:
    """JSON 직렬화."""
    def _c(c: GaejaCandidate) -> dict[str, Any]:
        return {
            "surname_hanja": c.surname_hanja,
            "given_hanja": c.given_hanja,
            "full_hanja": c.full_hanja,
            "strokes": list(c.strokes),
            "four_gyeok_summary": c.four_gyeok_summary,
            "all_gyeok_good": c.all_gyeok_good,
            "eumyang_grade": c.eumyang_grade,
            "ohaeng_match_count": c.ohaeng_match_count,
            "score": c.score,
        }
    return {
        "surname_hanja": result.surname_hanja,
        "surname_korean": result.surname_korean,
        "given_korean": result.given_korean,
        "candidates": [_c(c) for c in result.candidates],
        "total_combinations": result.total_combinations,
        "filtered_count": result.filtered_count,
    }
