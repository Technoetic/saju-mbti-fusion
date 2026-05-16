"""A13 소셜 무의식 리포트 에이전트 (v3) — Lawrence 소셜 드리밍 매트릭스.

문서: 전체 사용자 꿈 코퍼스(집계) → 주간 사회 무의식 클러스터.

활성 조건: DB에 최소 30명 × 최근 7일 일기 합 100건+ 누적 후.
미충족 시 기본 안내.

구현:
  - 결정론 토픽 클러스터링 (감금/추락/쫓김/이별 등 보편 모티프 카운트)
  - 익명 통계만 (개별 사용자 ID·텍스트 노출 X)
"""

from __future__ import annotations
from typing import Any
from collections import Counter
from datetime import datetime, timezone, timedelta

from engine.storage.db import get_connection


SOCIAL_UNCONSCIOUS_LABEL = (
    "A13 소셜 무의식 — 전체 사용자 일기 코퍼스의 주간 토픽 클러스터. "
    "Lawrence 소셜 드리밍 매트릭스 디지털 구현. 익명 집계."
)


# 보편 사회 무의식 모티프 (위협·관계·존재)
SOCIAL_MOTIFS = {
    "감금": ["갇혔", "감금", "갇혀", "닫힌 공간", "탈출 불가"],
    "추락": ["떨어졌", "추락", "낙하", "절벽", "바닥으로"],
    "쫓김": ["쫓겼", "쫓아왔", "추적", "도망", "추적자"],
    "이별": ["이별", "헤어진", "버려졌", "떠난", "잃었"],
    "재난": ["지진", "홍수", "쓰나미", "화재", "전쟁"],
    "질식": ["숨막힘", "질식", "숨이 안", "공기 부족"],
    "벌거벗음": ["벌거벗", "옷이 없", "수치"],
    "시험": ["시험", "면접", "발표", "심사"],
    "사망": ["죽었", "장례", "시신", "관 속"],
    "병원": ["병원", "수술", "의사", "환자"],
    "재회": ["재회", "다시 만났", "돌아왔"],
    "비행": ["날기", "비행", "하늘로", "공중 부양"],
}


def aggregate_social_unconscious(
    *,
    days: int = 7,
    min_users: int = 30,
    min_entries: int = 100,
) -> dict[str, Any]:
    """최근 N일치 전체 사용자 일기 → 토픽 클러스터.

    Returns:
        {
            'ready': bool,
            'period_days': N,
            'unique_users': int,
            'total_entries': int,
            'motif_clusters': [{motif, count, percent}],
            'dominant_themes': [...],
            'comparison_to_previous_week': {...},
        }
    """
    from engine.storage import init_db
    init_db()

    kst = timezone(timedelta(hours=9))
    cutoff = (datetime.now(kst) - timedelta(days=days)).isoformat()
    prev_start = (datetime.now(kst) - timedelta(days=days * 2)).isoformat()

    with get_connection() as conn:
        # 최근 N일 일기
        rows = conn.execute(
            """SELECT user_id, narrative_text, valence FROM dream_diary
               WHERE created_at_iso >= ?""",
            (cutoff,),
        ).fetchall()
        # 이전 N일 (비교용)
        prev_rows = conn.execute(
            """SELECT narrative_text FROM dream_diary
               WHERE created_at_iso >= ? AND created_at_iso < ?""",
            (prev_start, cutoff),
        ).fetchall()

    unique_users = len({r["user_id"] for r in rows})
    total_entries = len(rows)

    if unique_users < min_users or total_entries < min_entries:
        return {
            "agent": "A13",
            "ready": False,
            "period_days": days,
            "unique_users": unique_users,
            "total_entries": total_entries,
            "threshold": {"min_users": min_users, "min_entries": min_entries},
            "note": (
                f"활성화 미충족 — 최근 {days}일 {unique_users}명/{total_entries}건. "
                f"({min_users}명/{min_entries}건+ 필요)"
            ),
        }

    # 모티프 카운트
    current_counter: Counter[str] = Counter()
    prev_counter: Counter[str] = Counter()
    for r in rows:
        text = r["narrative_text"] or ""
        for motif, kws in SOCIAL_MOTIFS.items():
            if any(k in text for k in kws):
                current_counter[motif] += 1
    for r in prev_rows:
        text = r["narrative_text"] or ""
        for motif, kws in SOCIAL_MOTIFS.items():
            if any(k in text for k in kws):
                prev_counter[motif] += 1

    # 비율 + 변화율
    clusters: list[dict[str, Any]] = []
    for motif, count in current_counter.most_common():
        pct = round(count / total_entries * 100, 1)
        prev_count = prev_counter.get(motif, 0)
        prev_pct = round(prev_count / max(1, len(prev_rows)) * 100, 1) if prev_rows else 0.0
        delta_pct = round(pct - prev_pct, 1)
        clusters.append({
            "motif": motif,
            "count": count,
            "percent": pct,
            "previous_percent": prev_pct,
            "delta_pct": delta_pct,
            "trending": "↑" if delta_pct > 2 else ("↓" if delta_pct < -2 else "→"),
        })

    dominant = [c["motif"] for c in clusters[:3]]

    # 평균 정서
    valences = [r["valence"] for r in rows if r["valence"] is not None]
    avg_valence = round(sum(valences) / len(valences), 2) if valences else 0.0

    return {
        "agent": "A13",
        "ready": True,
        "period_days": days,
        "unique_users": unique_users,
        "total_entries": total_entries,
        "motif_clusters": clusters,
        "dominant_themes": dominant,
        "avg_valence": avg_valence,
        "interpretive_note": (
            f"지난 {days}일 사용자 {unique_users}명의 일기 {total_entries}건에서 "
            f"가장 두드러진 사회 무의식 모티프는 '{dominant[0] if dominant else '없음'}'입니다."
        ),
        "principle": (
            "Lawrence 소셜 드리밍 매트릭스 디지털 구현 — 개인 익명 집계로 "
            "사회 전체 무의식의 주간 동향 추출. 개인 ID·텍스트 노출 X."
        ),
    }


__all__ = [
    "SOCIAL_UNCONSCIOUS_LABEL",
    "SOCIAL_MOTIFS",
    "aggregate_social_unconscious",
]
