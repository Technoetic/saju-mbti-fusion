"""묘에 쇼닌『몽기(夢記)』 — 일본 화엄·진언종 자기관찰 일기 전통.

출처: 明恵『夢記』, 久保田 淳·山口 明穂 校註本 (1981)

핵심:
  - 일본 가마쿠라 시대 화엄·진언종 묘에 쇼닌(1173~1232)이 약 40년간
    자신의 꿈을 도해·서술 기록 — 깨달음 자료
  - 단순 해몽이 아니라 장기 자기관찰의 수행 도구
  - 종교적 수행 동기 + 도해(visual diary) 전통

본 모듈의 역할:
  - 장기 누적 일기에서 반복 모티프·자기 변화 곡선 추출
  - "도해"의 현대화 — 텍스트 기반 핵심 이미지 태깅
  - Schredl Diary(#22)의 역사적 UX 모티브 — 일본 시장 친화
"""

from __future__ import annotations
from typing import Any
from collections import Counter


MYOE_LABEL = (
    "묘에 쇼닌『몽기』 — 40년 자기관찰 일기 전통. 꿈을 깨달음의 자료로 삼는 수행. "
    "Schredl Diary 표준의 역사적 모티브."
)


# 묘에가 즐겨 기록한 도해 모티프 (현대 자기관찰 적용)
TRADITIONAL_MOTIFS = {
    "佛像 (불상)": ["부처", "관음", "보살", "여래", "불상"],
    "蓮花 (연꽃)": ["연꽃", "연잎", "수련"],
    "山 (산)": ["산", "봉우리", "정상", "능선"],
    "水 (물)": ["바다", "강", "호수", "샘", "물"],
    "雲 (구름)": ["구름", "안개", "노을"],
    "鳥 (새)": ["새", "학", "봉황", "독수리"],
    "光 (빛)": ["빛", "광채", "후광", "광명"],
    "境 (경계)": ["문", "다리", "터널", "경계", "임계"],
    "塔 (탑)": ["탑", "사찰", "절", "신전"],
    "鏡 (거울)": ["거울", "반사", "물에 비친"],
}


# 묘에 스타일 자기관찰 일지 추천 항목
MYOE_DIARY_FIELDS_KO = [
    {
        "key": "core_image",
        "name": "핵심 도해 (1개)",
        "instruction": "꿈에서 가장 인상 깊었던 단일 이미지를 한 단어로. 묘에처럼 그릴 수 있다면 더 좋음.",
    },
    {
        "key": "felt_meaning",
        "name": "느낌의 의미",
        "instruction": "해석이 아닌 '느낀 의미'를 한 줄로. 정답을 찾지 말고 첫 인상을 적으세요.",
    },
    {
        "key": "spiritual_resonance",
        "name": "수행적 울림",
        "instruction": "오늘의 마음 공부·삶의 화두와 어떻게 연결되는지. 종교 무관 — 자기 성찰 차원.",
    },
    {
        "key": "recurring_motif_check",
        "name": "반복 모티프 확인",
        "instruction": "과거 일기에서 같은 모티프가 등장한 적이 있는가? 있다면 며칠 전·어떤 맥락이었나.",
    },
    {
        "key": "next_intention",
        "name": "다음 의도",
        "instruction": "이 꿈이 일러주는 듯한 다음 작은 행동 한 가지를 정하세요. 강제하지 말고 자연스럽게.",
    },
]


def extract_traditional_motifs(text: str) -> dict[str, Any]:
    """한 꿈 텍스트에서 묘에 전통 도해 모티프 추출."""
    t = text or ""
    found: dict[str, list[str]] = {}
    for motif, kws in TRADITIONAL_MOTIFS.items():
        hits = [k for k in kws if k in t]
        if hits:
            found[motif] = hits

    return {
        "motifs_found": found,
        "motif_count": len(found),
        "interpretive_note": (
            f"묘에 전통 모티프 {len(found)}개 등장: {', '.join(found.keys())}."
            if found
            else "묘에 전통 도해 모티프 미감지 — 일상적·세속적 꿈에 가까움."
        ),
    }


def analyze_long_term_diary(
    entries: list[dict[str, Any]],
    min_entries: int = 14,
) -> dict[str, Any]:
    """장기 일기(2주+)에서 반복 모티프·자기 변화 추출.

    Args:
        entries: 일기 항목 리스트 (각 {date_iso, narrative_text, core_image?, valence?})
        min_entries: 분석 최소 항목 수

    Returns:
        반복 모티프·곡선·묘에 통찰 노트
    """
    n = len(entries)
    if n < min_entries:
        return {
            "entries_observed": n,
            "min_required": min_entries,
            "analysis_available": False,
            "note": f"묘에식 장기 관찰은 최소 {min_entries}일 누적 후 분석합니다 (현재 {n}일).",
        }

    # 모티프 카운트 (전통 + 자유 core_image)
    motif_counter: Counter[str] = Counter()
    for e in entries:
        text = e.get("narrative_text") or ""
        for motif, kws in TRADITIONAL_MOTIFS.items():
            if any(k in text for k in kws):
                motif_counter[motif] += 1
        ci = e.get("core_image")
        if ci:
            motif_counter[f"core: {ci}"] += 1

    most_common = motif_counter.most_common(5)
    repeating = [m for m, c in most_common if c >= 3]

    # 정서 곡선
    valences = [int(e.get("valence", 0)) for e in entries if e.get("valence") is not None]
    if valences:
        mean = round(sum(valences) / len(valences), 2)
        half = len(valences) // 2
        delta = (
            round(sum(valences[half:]) / (len(valences) - half) - sum(valences[:half]) / half, 2)
            if half > 0 else 0.0
        )
    else:
        mean, delta = 0.0, 0.0

    return {
        "entries_observed": n,
        "analysis_available": True,
        "top_5_motifs": most_common,
        "repeating_motifs": repeating,
        "valence_mean": mean,
        "valence_trend_delta": delta,
        "myoe_insight": _build_insight(repeating, mean, delta, n),
    }


def _build_insight(
    repeating: list[str], mean: float, delta: float, n: int
) -> str:
    parts = [f"{n}일 누적 관찰:"]
    if repeating:
        parts.append(f"반복 모티프 {len(repeating)}개 — {', '.join(repeating[:3])}.")
        parts.append("묘에 관점에서 이는 현재 마음 공부의 화두입니다.")
    else:
        parts.append("강한 반복 모티프 없음 — 마음이 여러 화두를 펼쳐 보이는 시기.")
    if delta > 0.5:
        parts.append("정서 곡선은 회복 추세.")
    elif delta < -0.5:
        parts.append("정서 곡선은 침체 추세 — 무리하지 마세요.")
    return " ".join(parts)


__all__ = [
    "MYOE_LABEL",
    "TRADITIONAL_MOTIFS",
    "MYOE_DIARY_FIELDS_KO",
    "extract_traditional_motifs",
    "analyze_long_term_diary",
]
