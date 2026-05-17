"""facial_feature_classifier 회귀 — ADR-034 Phase 1 (앙월구·복주구·일자구).

검증:
- 임계값 정확성 (±2도 마진)
- ADR-022 5형 분류와 직교 (충돌 없음)
- ADR-010 면책 메시지 자동 부착
- ADR-006 사상체질·운명 매핑 어휘 부재
- 세 가지 입력 경로 (landmarks dict / 키포인트 직접 / 사전계산 각도)
- 비정상 입력 None 반환
"""

from __future__ import annotations

import pytest

from engine.divination.facial_feature_classifier import (
    KP_MOUTH_CORNER_LEFT,
    KP_MOUTH_CORNER_RIGHT,
    SHAPE_ANGSWOLGU,
    SHAPE_BOKJUGU,
    SHAPE_ILJAGU,
    classify_from_metrics,
    classify_mouth_corner,
)


# ─────────────────────────────────────────────────────────────────────────────
# 기본 분류 — 세 가지 형상 검출
# ─────────────────────────────────────────────────────────────────────────────


def test_angswolgu_detected_when_corners_lifted():
    """입꼬리가 입술 중앙선보다 위 → 앙월구 (이미지 좌표 y는 아래로 향함).

    입술 중앙선 = KP_13 윗입술 중앙 (y=0.5) + KP_14 아랫입술 중앙 (y=0.55)
                  → baseline_y = 0.525
    좌측 입꼬리 (0.3, 0.45) → baseline y=0.525보다 위 → 양수 각도
    """
    result = classify_mouth_corner({
        KP_MOUTH_CORNER_LEFT: (0.3, 0.45),
        KP_MOUTH_CORNER_RIGHT: (0.7, 0.45),
        13: (0.5, 0.5),   # 윗입술 중앙
        14: (0.5, 0.55),  # 아랫입술 중앙
    })
    assert result is not None
    assert result.shape_type == SHAPE_ANGSWOLGU
    assert result.angle_deg > 2.0


def test_bokjugu_detected_when_corners_dropped():
    """입꼬리가 입술 중앙선보다 아래 → 복주구."""
    result = classify_mouth_corner({
        KP_MOUTH_CORNER_LEFT: (0.3, 0.6),
        KP_MOUTH_CORNER_RIGHT: (0.7, 0.6),
        13: (0.5, 0.5),
        14: (0.5, 0.55),
    })
    assert result is not None
    assert result.shape_type == SHAPE_BOKJUGU
    assert result.angle_deg < -2.0


def test_iljagu_detected_when_corners_near_baseline():
    """입꼬리가 입술 중앙선과 거의 같은 y → 일자구."""
    # baseline_y = (0.5 + 0.55) / 2 = 0.525, 입꼬리도 0.525 → 거의 0도
    result = classify_mouth_corner({
        KP_MOUTH_CORNER_LEFT: (0.3, 0.525),
        KP_MOUTH_CORNER_RIGHT: (0.7, 0.525),
        13: (0.5, 0.5),
        14: (0.5, 0.55),
    })
    assert result is not None
    assert result.shape_type == SHAPE_ILJAGU
    assert abs(result.angle_deg) < 2.0


def test_iljagu_within_noise_margin():
    """잡음 마진 내 미세 기울기는 일자구."""
    # baseline_y = 0.525, 입꼬리 0.524 → 거의 수평
    result = classify_mouth_corner({
        KP_MOUTH_CORNER_LEFT: (0.3, 0.524),
        KP_MOUTH_CORNER_RIGHT: (0.7, 0.524),
        13: (0.5, 0.5),
        14: (0.5, 0.55),
    })
    assert result is not None
    assert result.shape_type == SHAPE_ILJAGU


# ─────────────────────────────────────────────────────────────────────────────
# 입력 경로 3종
# ─────────────────────────────────────────────────────────────────────────────


def test_classify_from_metrics_landmarks_dict():
    """metrics.landmarks dict 경로 (입술 중앙 KP 포함)."""
    result = classify_from_metrics({
        "landmarks": {
            61: [0.3, 0.45],
            291: [0.7, 0.45],
            13: [0.5, 0.5],
            14: [0.5, 0.55],
            33: [0.2, 0.4],  # 다른 키포인트 무관
        }
    })
    assert result is not None
    assert result.shape_type == SHAPE_ANGSWOLGU


def test_classify_from_metrics_direct_corners_falls_back_to_iljagu():
    """metrics.mouth_corner_left/right 직접 좌표 — 입술 중앙 KP 없으니
    baseline 미정 → 일자구 폴백 (의도된 동작, 사전 계산 각도 경로 권장)."""
    result = classify_from_metrics({
        "mouth_corner_left": [0.3, 0.55],
        "mouth_corner_right": [0.7, 0.55],
    })
    assert result is not None
    assert result.shape_type == SHAPE_ILJAGU  # baseline 없음 → 0도 폴백


def test_classify_from_metrics_precomputed_angle():
    """metrics.mouth_corner_lift_angle 사전 계산 경로."""
    # 클라이언트가 이미 계산한 각도 직접 제공
    result = classify_from_metrics({"mouth_corner_lift_angle": 8.5})
    assert result is not None
    assert result.shape_type == SHAPE_ANGSWOLGU
    assert result.angle_deg == 8.5


def test_classify_from_metrics_precomputed_negative_angle():
    """음수 사전 계산 각도 → 복주구."""
    result = classify_from_metrics({"mouth_corner_lift_angle": -5.0})
    assert result is not None
    assert result.shape_type == SHAPE_BOKJUGU


# ─────────────────────────────────────────────────────────────────────────────
# 비정상 입력 — None 반환
# ─────────────────────────────────────────────────────────────────────────────


def test_returns_none_when_metrics_none():
    assert classify_from_metrics(None) is None


def test_returns_none_when_metrics_empty():
    assert classify_from_metrics({}) is None


def test_returns_none_when_landmarks_missing_required_keys():
    """필수 키 61·291 부재 시 None."""
    result = classify_mouth_corner({33: (0.5, 0.5)})  # 다른 KP만
    assert result is None


def test_returns_none_when_landmarks_only_one_corner():
    """입꼬리 한 쪽만 있을 때 None."""
    result = classify_mouth_corner({KP_MOUTH_CORNER_LEFT: (0.3, 0.45)})
    assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# ADR 정합 — 면책·출처·운명 매핑 부재 자동 검증
# ─────────────────────────────────────────────────────────────────────────────


def test_disclaimer_explains_no_fate_mapping():
    """ADR-006/010 — 면책에 운명 매핑 부재 명시."""
    result = classify_from_metrics({"mouth_corner_lift_angle": 5.0})
    assert result is not None
    assert "운명" in result.disclaimer
    assert "관운" in result.disclaimer or "길흉" in result.disclaimer
    assert "매핑이 아닙" in result.disclaimer or "측정 결과" in result.disclaimer


def test_source_url_is_koreascience_paper():
    """ADR-010 — 출처가 KoreaScience JAKO 학술 URL."""
    result = classify_from_metrics({"mouth_corner_lift_angle": 0.0})
    assert result is not None
    assert "koreascience.kr" in result.source_url
    assert "JAKO200810103458095" in result.source_url


def test_no_saaschecheijl_dogma_in_module():
    """ADR-006 — 모듈 본문에 사상체질·태음인·소양인 어휘 부재."""
    import engine.divination.facial_feature_classifier as mod
    import inspect
    src = inspect.getsource(mod)
    for forbidden in ["태음인", "소양인", "태양인", "소음인", "사상체질"]:
        # 면책 + 주석에서 "의도적 미본문화" 명시 검증
        if forbidden in src:
            # 사용처가 "본문화 X" 또는 "ADR-006" 절 인용 부분이어야 함
            idx = src.index(forbidden)
            ctx = src[max(0, idx - 80):idx + 80]
            assert "본문화 X" in ctx or "ADR-006" in ctx or "의도적" in ctx, (
                f"사상체질 어휘가 면책 절 외부에서 사용: {ctx!r}"
            )


def test_classification_orthogonal_to_face_shape():
    """ADR-022 — 5형 얼굴 윤곽 분류와 별개 (충돌 없음).

    face_shape.classify_face_shape는 face_width_height_ratio 등 윤곽 메트릭만
    사용. 본 모듈은 입꼬리 키포인트만 사용. 두 모듈 동시 사용 가능.
    """
    # 본 모듈이 face_shape 의존성 0건
    import inspect
    import engine.divination.facial_feature_classifier as mod
    src = inspect.getsource(mod)
    assert "face_shape" not in src.split("ADR")[0]  # import 영역에 face_shape 의존성 없음
    # ADR 정합 문서화는 OK


def test_result_has_left_and_right_angles():
    """좌우 입꼬리 각도 개별 노출 — 비대칭 분석 가능."""
    result = classify_from_metrics({"mouth_corner_lift_angle": 5.0})
    assert result is not None
    assert hasattr(result, "left_angle_deg")
    assert hasattr(result, "right_angle_deg")
    assert hasattr(result, "confidence")
    assert result.confidence == "HIGH"


def test_kp_indices_match_official_mediapipe_doc():
    """MediaPipe 공식 face_landmarker 입꼬리 인덱스 정합 (61, 291)."""
    assert KP_MOUTH_CORNER_LEFT == 61
    assert KP_MOUTH_CORNER_RIGHT == 291
