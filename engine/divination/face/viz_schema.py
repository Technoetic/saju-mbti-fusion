"""ADR-208 - 시각화 인포그래픽 데이터 schema.

face/reading.py 결과를 front 시각화 라이브러리(D3·Chart.js·SVG)에 직접
전달 가능한 표준 schema 변환. ADR-006 위반 어휘 차단 + 출처 명시 강제.

ADR 정합:
  - ADR-006 (운명 단정 어휘 X — 형태·점수만 노출)
  - ADR-010 (출처 명시 강제 — schema에 source_url 필드 필수)
  - ADR-171 (fate_assertion 통과 라벨만)
  - ADR-159 (face MediaPipe Phase 1.5)
"""

from __future__ import annotations

from typing import Any


def to_radar_chart_data(palace_scores: dict[str, Any]) -> dict[str, Any]:
    """12궁 점수 → 레이더 차트 schema.

    Args:
        palace_scores: scoring.report_to_dict() 출력 palaces dict.

    Returns:
        {
            "type": "radar",
            "labels": [한국어 라벨 리스트],
            "values": [0~1 점수 리스트],
            "max": 1.0,
            "min": 0.0,
            "disclaimer": "...",
        }
    """
    if not isinstance(palace_scores, dict):
        return {"type": "radar", "labels": [], "values": [], "max": 1.0, "min": 0.0,
                "disclaimer": ""}

    palaces = palace_scores.get("palaces", {}) if "palaces" in palace_scores else palace_scores
    labels: list[str] = []
    values: list[float] = []
    for k, v in palaces.items():
        if not isinstance(v, dict):
            continue
        label_ko = v.get("label_ko", k)
        score = v.get("score")
        if isinstance(score, (int, float)):
            labels.append(label_ko)
            values.append(round(float(score), 3))

    return {
        "type": "radar",
        "labels": labels,
        "values": values,
        "max": 1.0,
        "min": 0.0,
        "disclaimer": "12궁 형태 점수 — 운명 단정 아님 (ADR-006)",
        "source_url": "https://pubmed.ncbi.nlm.nih.gov/15262719/",
    }


def to_complexion_heatmap(complexion: dict[str, Any]) -> dict[str, Any]:
    """8 ROI L* 점수 → 히트맵 schema."""
    if not isinstance(complexion, dict):
        return {"type": "heatmap", "rois": {}, "disclaimer": ""}

    rois_in = complexion.get("rois", {})
    rois_out: dict[str, dict[str, Any]] = {}
    roi_ko = {
        "forehead": "이마", "nose_tip": "코끝", "nose_bridge": "콧대",
        "chin": "턱", "cheekbone": "광대", "cheek": "뺨",
        "jaw": "턱선", "neck": "목",
    }
    for k, v in rois_in.items():
        if not isinstance(v, dict):
            continue
        rois_out[k] = {
            "label_ko": roi_ko.get(k, k),
            "L": v.get("L", 0),
            "a": v.get("a", 0),
            "b": v.get("b", 0),
            "L_zscore": v.get("L_zscore", 0),
            "label_short": v.get("label_short", ""),
        }
    return {
        "type": "heatmap",
        "rois": rois_out,
        "overall_L_mean": complexion.get("overall_L_mean"),
        "overall_tone": complexion.get("overall_tone", ""),
        "disclaimer": "면색 형태 측정 — 의료 진단·체질 분류 아님 (ADR-006)",
        "source_url": "https://link.springer.com/article/10.1186/s41702-017-0002-7",
    }


def to_samjeong_bar(palace_scores: dict[str, Any]) -> dict[str, Any]:
    """삼정(상정·중정·하정) 점수 → 가로 막대 schema."""
    if not isinstance(palace_scores, dict):
        return {"type": "bar", "labels": [], "values": [], "disclaimer": ""}
    sam = palace_scores.get("samjeong", {})
    labels: list[str] = []
    values: list[float] = []
    for k, v in sam.items():
        if not isinstance(v, dict):
            continue
        labels.append(v.get("label_ko", k))
        score = v.get("score")
        if isinstance(score, (int, float)):
            values.append(round(float(score), 3))
    return {
        "type": "bar",
        "labels": labels,
        "values": values,
        "max": 1.0,
        "disclaimer": "삼정 비율 형태 점수 — 운명 단정 아님 (ADR-006)",
    }


def build_full_viz_schema(face_reading_result: dict[str, Any]) -> dict[str, Any]:
    """face_reading 응답 envelope → 시각화 schema 묶음.

    Args:
        face_reading_result: face.reading.generate_face_reading() 응답.

    Returns:
        {
            "radar_12_palaces": {...},
            "heatmap_complexion": {...},
            "bar_samjeong": {...},
            "metadata": {...},
        }
    """
    palace_scores = face_reading_result.get("palace_scores") or {}
    complexion = face_reading_result.get("complexion") or {}

    return {
        "radar_12_palaces": to_radar_chart_data(palace_scores),
        "heatmap_complexion": to_complexion_heatmap(complexion),
        "bar_samjeong": to_samjeong_bar(palace_scores),
        "metadata": {
            "persona": "운학 도사",
            "system_id": "saju-mbti-fusion",
            "domain": "face",
            "disclaimer_global": (
                "본 시각화는 형태·통계 분석이며 운명·길흉 단정이 아닙니다. "
                "참고용으로만 활용해 주십시오."
            ),
        },
    }
