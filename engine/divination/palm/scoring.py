"""손금 4대 선 + 보조선 결정론 점수 엔진 (ADR-030).

보고서 "손금 4대 선 및 보조선 결정론 점수 엔진 구축 명세서" (2026-05-17, 652줄)
§2~§7 기반. face_scoring.py (ADR-004) 패턴 차용.

목적: MediaPipe Hand 21 키포인트 → 4대 선(생명·두뇌·감정·운명) + 금성대
결정론 점수 [0.0, 1.0] + 학파 명시 라벨링 + ADR-010 면책 자동 포함.

데이터 출처:
  · Size Korea 7/8차 인체측정 (KCI)
  · KCI NODE00559265: 한국인 손금 형태 조사
  · PubMed PMC7195958: Dermatoglyphics
  · PubMed PMC9256497: Palmar crease asymmetry
  · MediaPipe Hand Landmarker 공식 (ai.google.dev)

호환성:
  · palm_reading.py (LLM Vision) — 본 모듈은 독립 결정론 엔진
  · face_scoring.py (ADR-004) — 동일 패턴 (PalaceScore → LineScore)

면책 (ADR-010 의무):
  · 본 점수는 손바닥 주름의 형태적 비율 정량 분석
  · 운명·수명·재물 인과 X (forbidden_interpretation 자동 차단)
  · 사용자 출력 시 disclaimer 자동 포함
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Literal


# 데이터 경로
_RULES_PATH = Path(__file__).parent.parent.parent / "data" / "palm_scoring_rules.json"

LineKey = Literal["lifeline", "headline", "heartline", "fateline", "girdle_of_venus"]
ScoreLabel = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class LineScore:
    """단일 손금 선 점수 (불변).

    score: 정규화 점수 [0.0, 1.0]
    label: "low" / "medium" / "high"
    label_ko: 한국어 형태 기술 (인과 표현 0)
    evidence: 결정론 산출 근거 (raw metric value)
    """
    key: str
    name: str
    score: float
    label: str
    label_ko: str
    evidence: float
    academic_source: str


@dataclass(frozen=True)
class PalmScoringReport:
    """손금 결정론 점수 종합 보고."""
    hand_side: str  # "left" | "right" | "unknown"
    lines: dict[str, LineScore]
    disclaimer_ko: str
    rationale: str
    metadata: dict = field(default_factory=dict)


# ───────────────────── 데이터 로드 ─────────────────────


@lru_cache(maxsize=1)
def _load_rules() -> dict:
    """data/palm_scoring_rules.json 로드."""
    if not _RULES_PATH.exists():
        return {}
    return json.loads(_RULES_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _line_config_by_key() -> dict[str, dict]:
    """{'lifeline': {metric, thresholds, ...}, ...}"""
    rules = _load_rules()
    return {l["key"]: l for l in rules.get("lines", [])}


@lru_cache(maxsize=1)
def _forbidden_tokens_pattern() -> re.Pattern:
    """ADR-010 차단 토큰 regex (사용자 출력 자동 검증)."""
    rules = _load_rules()
    tokens = rules.get("forbidden_tokens_regex", [])
    if not tokens:
        return re.compile(r"(?!.*)")  # 무매치
    escaped = [re.escape(t) for t in tokens]
    return re.compile("|".join(escaped))


# ───────────────────── 기하 헬퍼 ─────────────────────


def _distance(p1: list[float], p2: list[float]) -> float:
    """2D 거리 (z 좌표 무시)."""
    if not p1 or not p2 or len(p1) < 2 or len(p2) < 2:
        return 0.0
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def _score_from_value(value: float, mean: float, std: float, low: float, high: float) -> tuple[float, str]:
    """raw metric → 정규화 점수 [0,1] + 라벨.

    값이 (mean - 3*std, mean + 3*std) 범위 내라 가정.
    label: < low → "low" / [low, high] → "medium" / > high → "high"
    score: low/high 기준 3분위 → [0, 0.3) / [0.3, 0.6] / (0.6, 1.0]
    """
    if value < low:
        # low: [0, 0.3)
        # value 0 → 0.0, value=low → 0.3
        if low <= 0:
            score = 0.15
        else:
            score = max(0.0, min(0.3, 0.3 * value / low))
        return (round(score, 3), "low")
    if value > high:
        # high: (0.6, 1.0]
        # value=high → 0.6, value=1.0+ → 1.0
        cap = max(high * 1.5, 1.0)
        score = 0.6 + 0.4 * min(1.0, (value - high) / max(0.001, cap - high))
        return (round(score, 3), "high")
    # medium: [0.3, 0.6]
    span = max(0.001, high - low)
    score = 0.3 + 0.3 * (value - low) / span
    return (round(score, 3), "medium")


# ───────────────────── 4대 선 메트릭 산출 ─────────────────────


def _compute_lifeline_metric(keypoints: dict) -> float:
    """생명선 arc_length_normalized = lifeline_arc / distance(kp5, kp0).

    keypoints에 arc_length_normalized가 명시되면 그것을 사용 (회귀 데이터).
    """
    if "lifeline_arc" in keypoints:
        return float(keypoints["lifeline_arc"])
    kp5 = keypoints.get("kp5")
    kp0 = keypoints.get("kp0")
    if kp5 and kp0:
        # 단순 근사: 엄지·검지 공간 → 손목 거리 (정규화 분모만 계산 가능)
        # 실제 호 길이는 LLM Vision 또는 U-Net 마스크 필요 → 부분 추정
        return _distance(kp5, kp0)
    return 0.0


def _compute_headline_metric(keypoints: dict) -> float:
    """두뇌선 horizontal_extent."""
    if "headline_horizontal" in keypoints:
        return float(keypoints["headline_horizontal"])
    kp5 = keypoints.get("kp5")
    kp17 = keypoints.get("kp17")
    if kp5 and kp17:
        return _distance(kp5, kp17)
    return 0.0


def _compute_heartline_metric(keypoints: dict) -> float:
    """감정선 curvature_prominence."""
    if "heartline_curve" in keypoints:
        return float(keypoints["heartline_curve"])
    return 0.0


def _compute_fateline_metric(keypoints: dict) -> float:
    """운명선 vertical_linearity."""
    if "fateline_vertical" in keypoints:
        return float(keypoints["fateline_vertical"])
    return 0.0


def _compute_girdle_metric(keypoints: dict) -> float:
    """금성대 arc_prominence."""
    if "girdle_arc" in keypoints:
        return float(keypoints["girdle_arc"])
    return 0.0


_METRIC_FUNCS = {
    "lifeline": _compute_lifeline_metric,
    "headline": _compute_headline_metric,
    "heartline": _compute_heartline_metric,
    "fateline": _compute_fateline_metric,
    "girdle_of_venus": _compute_girdle_metric,
}


# ───────────────────── ADR-010 차단 ─────────────────────


def filter_forbidden_tokens(text: str) -> tuple[bool, list[str]]:
    """사용자 출력 텍스트에서 ADR-010 차단 토큰 검출.

    Returns:
        (안전 여부, 검출된 차단 토큰 리스트)
        - 안전: True (차단 토큰 0건) / False (1건 이상)
    """
    pattern = _forbidden_tokens_pattern()
    matches = pattern.findall(text)
    return (len(matches) == 0, matches)


def disclaimer_palm_ko() -> str:
    """ADR-030 손금 전용 면책 문구."""
    rules = _load_rules()
    return rules.get(
        "disclaimer_palm_ko",
        "본 손금 분석은 객관 데이터 기반이며 운명·길흉 인과관계 X.",
    )


# ───────────────────── Public API ─────────────────────


def score_palm(
    keypoints: dict,
    hand_side: str = "unknown",
) -> PalmScoringReport:
    """손금 4대 선 + 금성대 결정론 점수.

    Args:
        keypoints: MediaPipe Hand 21 키포인트 또는 보고서 §7 스타일 raw scores.
          - 예시 1 (raw): {"kp0": [x,y,z], "kp5": [...], ...}
          - 예시 2 (precomputed): {"lifeline_arc": 0.85, "headline_horizontal": 0.65, ...}
        hand_side: "left" | "right" | "unknown"

    Returns:
        PalmScoringReport (lines dict + disclaimer + rationale)
    """
    config = _line_config_by_key()
    lines: dict[str, LineScore] = {}

    for line_key, line_cfg in config.items():
        metric_func = _METRIC_FUNCS.get(line_key)
        if metric_func is None:
            continue
        raw_value = metric_func(keypoints)
        mean = line_cfg.get("korean_baseline_mean", 0.5)
        std = line_cfg.get("korean_baseline_std", 0.15)
        thr = line_cfg.get("thresholds", {})
        low = thr.get("low", mean - std)
        high = thr.get("high", mean + std)
        score, label = _score_from_value(raw_value, mean, std, low, high)
        labels = line_cfg.get("labels", {})
        lines[line_key] = LineScore(
            key=line_key,
            name=line_cfg.get("name", line_key),
            score=score,
            label=label,
            label_ko=labels.get(label, ""),
            evidence=round(raw_value, 4),
            academic_source=line_cfg.get("academic_source", ""),
        )

    rationale = _build_rationale(lines, hand_side)
    return PalmScoringReport(
        hand_side=hand_side,
        lines=lines,
        disclaimer_ko=disclaimer_palm_ko(),
        rationale=rationale,
        metadata={
            "adr": "ADR-030",
            "school_source": "MediaPipe Hand + Size Korea + KCI",
        },
    )


def _build_rationale(lines: dict[str, LineScore], hand_side: str) -> str:
    """학파 명시 + ADR-010 면책 포함 사용자 출력 (보고서 §5.2 패턴)."""
    if not lines:
        return f"손금 분석 데이터 부족. ※ {disclaimer_palm_ko()}"
    parts = []
    for key, ls in lines.items():
        parts.append(f"{ls.name}: {ls.label_ko} (점수 {ls.score:.2f})")
    side_str = {"left": "왼손", "right": "오른손", "unknown": "분석 대상 손"}.get(hand_side, "손")
    return (
        f"{side_str}의 형태적 분석 결과: " + " | ".join(parts) + ". "
        f"※ 본 지표는 한국 전통 손금 및 인도 Samudrika Shastra 학설을 "
        f"참조한 객관적 형태 분류이며, 운명·수명·재물과 인과관계는 없습니다. "
        f"{disclaimer_palm_ko()}"
    )


def asymmetry_index(left_report: PalmScoringReport, right_report: PalmScoringReport) -> dict:
    """좌우 손 비대칭성 지수 (보고서 §5.1).

    AI = Σ(Δ_i × W_i), W_i는 모든 선 동일 (W_i=0.25, equal weighting).
    학파 이견 영역으로 ADR-029 정신 (DEFER 대신 객관 라벨만).

    Returns:
        {asymmetry_index: float, line_deltas: dict, rationale: str}
    """
    deltas = {}
    for key in left_report.lines:
        if key not in right_report.lines:
            continue
        ls_l = left_report.lines[key]
        ls_r = right_report.lines[key]
        deltas[key] = abs(ls_l.score - ls_r.score)
    # 4대 선 equal weighting (W_i = 0.25 × 4 = 1.0)
    main_keys = ["lifeline", "headline", "heartline", "fateline"]
    main_deltas = [deltas.get(k, 0.0) for k in main_keys]
    ai = sum(main_deltas) / max(1, len([d for d in main_deltas if d > 0])) if any(main_deltas) else 0.0
    ai = round(ai, 3)
    return {
        "asymmetry_index": ai,
        "line_deltas": deltas,
        "rationale": (
            f"양손 주름 형태적 비대칭 지수 산출 결과 {ai}. "
            f"인도 Samudrika Shastra 학설 및 한국 전통 손금 관습에서는 "
            f"비우세수를 선천적 성향, 우세수를 후천적 변화 지표로 분석합니다. "
            f"본 지표는 양손 근육 사용량 및 환경 부하에 따른 형태적 차이 정량화입니다. "
            f"※ {disclaimer_palm_ko()}"
        ),
    }


def total_lines() -> int:
    """본문화된 손금 선 수 (5)."""
    return len(_line_config_by_key())


def is_loaded() -> bool:
    return bool(_load_rules())
