"""ADR-200 - 다중 사진 자동 선택.

여러 사진(blendshapes 포함 metrics 리스트) 중 표정 잡음이 가장 적은 사진
자동 선택. ADR-184 expression_noise 점수 + 추가 휴리스틱.

활용:
  - 사용자가 3~5장 연속 촬영 시 최선 선택
  - 단일 사진 강제 X — 명시 인터페이스
  - face/reading.py 본문 통합은 별도 ADR (호출자 책임)

선택 점수 = expression_noise.max_intensity (낮을수록 좋음)
  + head_tilt 절대값 정규화 (낮을수록 좋음)
  + asymmetry (낮을수록 좋음)

ADR 정합:
  - ADR-184 expression_noise (1차 신호)
  - ADR-159 face MediaPipe Phase 1.5 (metrics dict 형식)
  - ADR-010 사실성 분리 (휴리스틱 가중치 명시)
"""

from __future__ import annotations

from dataclasses import dataclass


# 점수 가중치 (낮을수록 좋은 사진)
_W_EXPRESSION = 1.0       # 표정 잡음 max intensity
_W_HEAD_TILT = 0.5        # head_tilt 절대값 (정규화: deg / 30)
_W_ASYMMETRY = 0.5        # asymmetry (이미 0~0.05 범위)


@dataclass(frozen=True)
class PhotoSelectionResult:
    """다중 사진 선택 결과."""
    selected_index: int           # 선택된 사진 index (0-based)
    selected_score: float          # 잡음 점수 (낮을수록 좋음)
    all_scores: list[float]        # 전체 사진 점수
    n_photos: int
    reason: str                    # 선택 사유 (한국어)


def _photo_noise_score(metrics: dict) -> float:
    """단일 사진 metrics → 잡음 점수 (낮을수록 좋은 사진)."""
    if not isinstance(metrics, dict):
        return float("inf")

    # 표정 잡음 (ADR-184 expression_noise.detect 결과 또는 blendshapes 직접)
    expr_score = 0.0
    bs = metrics.get("blendshapes")
    if isinstance(bs, dict):
        try:
            from engine.safety.photo.expression_noise import detect_expression_noise
            r = detect_expression_noise(bs)
            expr_score = r.max_intensity
        except Exception:
            expr_score = 0.0

    # head_tilt 정규화 (절대값 / 30 deg)
    tilt = metrics.get("head_tilt_deg", 0)
    if isinstance(tilt, (int, float)):
        tilt_score = min(abs(float(tilt)) / 30.0, 1.0)
    else:
        tilt_score = 0.0

    # asymmetry (이미 0~0.05 범위 → 0~1 정규화)
    asym = metrics.get("asymmetry", 0)
    if isinstance(asym, (int, float)):
        asym_score = min(float(asym) / 0.05, 1.0)
    else:
        asym_score = 0.0

    return (_W_EXPRESSION * expr_score +
            _W_HEAD_TILT * tilt_score +
            _W_ASYMMETRY * asym_score)


def select_best_photo(
    metrics_list: list[dict | None],
) -> PhotoSelectionResult:
    """여러 사진 metrics → 가장 잡음 적은 사진 선택.

    Args:
        metrics_list: face_metrics.computeMetrics() 결과 리스트.
            None entry는 제외 가치(점수 inf).

    Returns:
        PhotoSelectionResult — selected_index + 점수 분포.
        빈 리스트면 selected_index=-1.
    """
    if not metrics_list:
        return PhotoSelectionResult(
            selected_index=-1, selected_score=float("inf"),
            all_scores=[], n_photos=0,
            reason="사진이 제공되지 않았습니다.",
        )

    scores = [_photo_noise_score(m) if isinstance(m, dict) else float("inf")
              for m in metrics_list]
    best_idx = min(range(len(scores)), key=lambda i: scores[i])
    best_score = scores[best_idx]

    if best_score == float("inf"):
        return PhotoSelectionResult(
            selected_index=-1, selected_score=best_score,
            all_scores=scores, n_photos=len(metrics_list),
            reason="유효한 사진이 없습니다.",
        )

    n = len(metrics_list)
    if n == 1:
        reason = "단일 사진이라 자동 선택 없이 사용합니다."
    elif best_score < 0.1:
        reason = f"{n}장 중 {best_idx + 1}번째 사진이 가장 잡음이 적습니다."
    elif best_score < 0.3:
        reason = f"{n}장 중 {best_idx + 1}번째 사진을 선택했으나 약간의 표정·기울기가 있습니다."
    else:
        reason = f"{n}장 모두 잡음이 큽니다. 무표정 정면 사진으로 다시 촬영을 권장합니다."

    return PhotoSelectionResult(
        selected_index=best_idx,
        selected_score=round(best_score, 4),
        all_scores=[round(s, 4) if s != float("inf") else -1.0 for s in scores],
        n_photos=n,
        reason=reason,
    )
