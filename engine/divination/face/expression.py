"""ADR-275 — MediaPipe Face Blendshapes 52종 → 표정 요약.

클라이언트(MediaPipe Face Landmarker) outputFaceBlendshapes=true에서 산출되는
52종 표정 강도 (categoryName: score 0..1)를 의미 그룹별로 집계하여
Stage 2 사극 어조 풀이에 "표정 메타" 한 단락 주입.

원칙 (ADR-006/010 정합):
- 감정 단정 X — "행복/슬픔/분노" 같은 라벨링 회피
- 시각 관찰 어휘만 — "입꼬리 강도", "미간 긴장도"
- DeepFace 같은 별도 감정 분류기 미사용 (비용·윤리 리스크)
"""
from __future__ import annotations

from typing import Any


# MediaPipe 52 blendshape categoryName 그룹 매핑
# 참조: https://developers.google.com/mediapipe/solutions/vision/face_landmarker
_SMILE_KEYS = ("mouthSmileLeft", "mouthSmileRight")
_FROWN_KEYS = ("mouthFrownLeft", "mouthFrownRight")
_MOUTH_OPEN_KEYS = ("jawOpen", "mouthOpen")  # mouthOpen은 일부 모델 only
_BROW_UP_KEYS = ("browInnerUp", "browOuterUpLeft", "browOuterUpRight")
_BROW_DOWN_KEYS = ("browDownLeft", "browDownRight")
_EYE_BLINK_KEYS = ("eyeBlinkLeft", "eyeBlinkRight")
_EYE_WIDE_KEYS = ("eyeWideLeft", "eyeWideRight")
_EYE_SQUINT_KEYS = ("eyeSquintLeft", "eyeSquintRight")
_CHEEK_RAISE_KEYS = ("cheekSquintLeft", "cheekSquintRight")
_NOSE_SNEER_KEYS = ("noseSneerLeft", "noseSneerRight")
_LIP_PRESS_KEYS = ("mouthPressLeft", "mouthPressRight", "mouthPucker")


def _avg(d: dict[str, float], keys: tuple[str, ...]) -> float:
    vals = [float(d.get(k, 0.0) or 0.0) for k in keys]
    return sum(vals) / len(vals) if vals else 0.0


def _max(d: dict[str, float], keys: tuple[str, ...]) -> float:
    vals = [float(d.get(k, 0.0) or 0.0) for k in keys]
    return max(vals) if vals else 0.0


def _asym(d: dict[str, float], left_key: str, right_key: str) -> float:
    """좌우 비대칭 절대값 (0..1)."""
    return abs(float(d.get(left_key, 0.0) or 0.0) - float(d.get(right_key, 0.0) or 0.0))


def _label(v: float) -> str:
    """0..1 강도 → 시각 관찰 어휘 (감정 단정 X)."""
    if v >= 0.6:
        return "뚜렷함"
    if v >= 0.35:
        return "보통"
    if v >= 0.15:
        return "옅음"
    return "거의 없음"


def summarize_expression(raw_blendshapes: dict[str, Any] | None) -> dict[str, Any] | None:
    """52종 raw blendshape → 의미 그룹 요약.

    Args:
        raw_blendshapes: {"mouthSmileLeft": 0.83, "browInnerUp": 0.42, ...}

    Returns:
        {
          "groups": {"smile": {"score": 0.78, "label": "뚜렷함"}, ...},
          "asymmetry": {"smile": 0.12, "brow_down": 0.04},
          "notes": ["입꼬리 뚜렷함", "미간 옅음"],
          "출처": "MediaPipe Face Blendshapes v2 52종 (시각 표정 강도, 감정 단정 X)",
        }
        raw 미주입/빈 dict면 None.
    """
    if not raw_blendshapes or not isinstance(raw_blendshapes, dict):
        return None
    # 모든 키 string 변환 + float coercion
    d: dict[str, float] = {}
    for k, v in raw_blendshapes.items():
        try:
            d[str(k)] = float(v)
        except (TypeError, ValueError):
            continue
    if not d:
        return None

    groups = {
        "smile": _avg(d, _SMILE_KEYS),
        "frown": _avg(d, _FROWN_KEYS),
        "mouth_open": _max(d, _MOUTH_OPEN_KEYS),
        "brow_up": _max(d, _BROW_UP_KEYS),
        "brow_down": _avg(d, _BROW_DOWN_KEYS),
        "eye_blink": _avg(d, _EYE_BLINK_KEYS),
        "eye_wide": _avg(d, _EYE_WIDE_KEYS),
        "eye_squint": _avg(d, _EYE_SQUINT_KEYS),
        "cheek_raise": _avg(d, _CHEEK_RAISE_KEYS),
        "nose_sneer": _avg(d, _NOSE_SNEER_KEYS),
        "lip_press": _max(d, _LIP_PRESS_KEYS),
    }

    asymmetry = {
        "smile": _asym(d, "mouthSmileLeft", "mouthSmileRight"),
        "brow_down": _asym(d, "browDownLeft", "browDownRight"),
        "eye_blink": _asym(d, "eyeBlinkLeft", "eyeBlinkRight"),
    }

    # Stage 2가 짧게 인용할 수 있는 한국어 노트 (감정 단정 X)
    labels = {
        "smile": "입꼬리",
        "frown": "입꼬리 처짐",
        "mouth_open": "입 벌림",
        "brow_up": "눈썹 올라감",
        "brow_down": "미간 조임",
        "eye_blink": "눈 감김",
        "eye_wide": "눈 크게 뜸",
        "eye_squint": "눈 가늘게 뜸",
        "cheek_raise": "광대 올라감",
        "nose_sneer": "코 찡그림",
        "lip_press": "입술 다묾",
    }
    notes: list[str] = []
    # 강도 상위 3개만 노트화 (저강도는 무시 — 0.15 미만)
    sorted_groups = sorted(groups.items(), key=lambda kv: kv[1], reverse=True)
    for name, score in sorted_groups[:3]:
        if score < 0.15:
            break
        notes.append(f"{labels.get(name, name)} {_label(score)}")

    # 비대칭 0.2 이상이면 노트 추가 (시각 사실)
    for name, val in asymmetry.items():
        if val >= 0.2:
            notes.append(f"{labels.get(name, name)} 좌우 차이 있음")

    return {
        "groups": {
            k: {"score": round(v, 3), "label": _label(v)}
            for k, v in groups.items()
        },
        "asymmetry": {k: round(v, 3) for k, v in asymmetry.items()},
        "notes": notes,
        "출처": "MediaPipe Face Blendshapes v2 52종 (시각 표정 강도, 감정 단정 X)",
    }
