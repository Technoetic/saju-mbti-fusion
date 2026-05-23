"""ADR-163 회귀 — face/reading.py에서 run_safety_gates 자동 호출 + 폴백 검증.

ADR-161에서 인터페이스만 만들고 face/reading.py 본문 통합이 부재했던 한계를
ADR-163가 해소. 본 테스트는 다음을 검증:

  · palace_scores와 모순되는 LLM 단정 어휘 → deterministic stub 폴백
  · palace_scores 모순 없으면 원본 응답 유지
  · safety_gate_verdict / safety_gate_failures / safety_gate_fallback_used
    필드가 envelope에 노출 (트레이스 가능)
  · 안전망 자체 예외 → 회귀 보호 (원본 응답 유지)

본 테스트는 _call_stage2_persona를 monkeypatch로 가짜 단정 응답 주입.
실제 BizRouter 호출 X (오프라인 회귀).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# 1×1 투명 PNG (LLM 게이트는 통과, 결정론 로직만 검증)
_DUMMY_IMAGE_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7w"
    "AAAABJRU5ErkJggg=="
)


def _make_metrics_with_low_jaebaek():
    """jaebaek 점수가 낮게 나오게 하는 메트릭.

    scoring._score_jaebaek는 alar_ratio + nose 관련 지표를 사용.
    극단값으로 score < 0.30 유도.
    """
    return {
        "three_thirds": [0.30, 0.30, 0.40],
        "eye_distance_ratio": 1.0,
        "alar_ratio": 0.05,  # 극단적으로 작은 콧방울 → jaebaek 낮음
        "cheo_cheop_ratio": 0.3,
        "wajam_ratio": 0.5,
        "asymmetry": 0.01,
        "head_tilt_deg": 0.0,
        "mouth_corner_lift": 0.05,
        "face_shape": "oval",
        "blendshapes": {},
    }


# ─────────────────────────── 폴백 검증 ───────────────────────────

def test_adr163_palace_score_mismatch_triggers_fallback():
    """jaebaek 점수 낮은데 LLM이 '재물복이 풍성' 단정 → stub 폴백."""
    from engine.divination.face import reading as face_reading

    # Stage 1·2를 monkeypatch — Stage 2가 단정 환각 어휘 반환
    fake_anat = {
        "face_outline": {}, "forehead": {}, "eyebrow": {}, "eye": {},
        "nose": {}, "mouth": {}, "chin": {}, "cheek_zygomatic": {},
        "complexion": {}, "distinctive_feature": "",
        "photo_quality_note": "",
    }
    fake_persona = "허허, 그대 재물복이 풍성하니 곳간이 넉넉하리라. 청년의 결이 두텁고 환하니 좋은 자리로다."

    metrics = _make_metrics_with_low_jaebaek()
    with patch.object(face_reading, "_call_stage1_objective", return_value=fake_anat), \
         patch.object(face_reading, "_call_stage2_persona", return_value=fake_persona), \
         patch.object(face_reading, "_load_cache", return_value=None), \
         patch.object(face_reading, "_save_cache"):
        out = face_reading.generate_face_reading(
            image_b64=_DUMMY_IMAGE_B64,
            age=30,
            gender="male",
            question="재물운이 어떻소?",
            metrics=metrics,
        )

    assert out["safety_gate_fallback_used"] is True
    assert out["safety_gate_verdict"] in ("warn", "critical")
    assert "fact_mismatch" in out["safety_gate_failures"]
    # 폴백되었으니 원본 단정 어휘는 제거됨
    assert "재물복이 풍성" not in out["text"]


def test_adr163_clean_response_no_fallback():
    """결정론 점수와 일치하는 응답은 폴백 X."""
    from engine.divination.face import reading as face_reading

    fake_anat = {
        "face_outline": {}, "forehead": {}, "eyebrow": {}, "eye": {},
        "nose": {}, "mouth": {}, "chin": {}, "cheek_zygomatic": {},
        "complexion": {}, "distinctive_feature": "",
        "photo_quality_note": "",
    }
    # 단정 어휘 없는 안전한 응답 (페르소나 톤 + 화두 마커 포함)
    fake_persona = (
        "허허, 그대의 상을 살피니 재백궁의 결이 평이하고 코의 자리가 고른지라. "
        "재물의 흐름은 두드러지지도 옅지도 않으니, 차근차근 쌓아 가는 결이라 하겠네. "
        "이 늙은이 이만 자네의 상을 마치노라."
    )

    metrics = _make_metrics_with_low_jaebaek()
    with patch.object(face_reading, "_call_stage1_objective", return_value=fake_anat), \
         patch.object(face_reading, "_call_stage2_persona", return_value=fake_persona), \
         patch.object(face_reading, "_load_cache", return_value=None), \
         patch.object(face_reading, "_save_cache"):
        out = face_reading.generate_face_reading(
            image_b64=_DUMMY_IMAGE_B64,
            age=30,
            gender="male",
            question="재물운이 어떻소?",
            metrics=metrics,
        )

    # palace_score_mismatch는 없어야 함 — 단정 어휘 부재
    assert "fact_mismatch" not in out["safety_gate_failures"] or \
        "palace_score" not in " ".join(out["safety_gate_failures"])
    assert out["safety_gate_fallback_used"] is False
    # 원본 응답 유지
    assert "재백궁의 결이 평이하고" in out["text"]


# ─────────────────────────── 트레이스 노출 ───────────────────────────

def test_adr163_envelope_exposes_safety_gate_fields():
    """envelope에 safety_gate_verdict/failures/fallback_used 노출."""
    from engine.divination.face import reading as face_reading

    fake_anat = {
        "face_outline": {}, "forehead": {}, "eyebrow": {}, "eye": {},
        "nose": {}, "mouth": {}, "chin": {}, "cheek_zygomatic": {},
        "complexion": {}, "distinctive_feature": "",
        "photo_quality_note": "",
    }
    fake_persona = (
        "허허, 그대 코의 자리가 두드러져 보이는도다. 청년의 결이 환하니 좋은 결이로다. "
        "이 늙은이 이만 자네의 상을 마치노라."
    )
    metrics = _make_metrics_with_low_jaebaek()
    with patch.object(face_reading, "_call_stage1_objective", return_value=fake_anat), \
         patch.object(face_reading, "_call_stage2_persona", return_value=fake_persona), \
         patch.object(face_reading, "_load_cache", return_value=None), \
         patch.object(face_reading, "_save_cache"):
        out = face_reading.generate_face_reading(
            image_b64=_DUMMY_IMAGE_B64,
            age=30,
            gender="male",
            metrics=metrics,
        )

    assert "safety_gate_verdict" in out
    assert "safety_gate_failures" in out
    assert "safety_gate_fallback_used" in out
    assert isinstance(out["safety_gate_failures"], list)
    assert isinstance(out["safety_gate_fallback_used"], bool)


# ─────────────────────────── 안전망 자체 예외 회귀 보호 ───────────────────────────

def test_adr163_safety_gate_exception_preserves_original():
    """안전망이 예외 던져도 원본 응답 유지 (회귀 보호)."""
    from engine.divination.face import reading as face_reading

    fake_anat = {
        "face_outline": {}, "forehead": {}, "eyebrow": {}, "eye": {},
        "nose": {}, "mouth": {}, "chin": {}, "cheek_zygomatic": {},
        "complexion": {}, "distinctive_feature": "",
        "photo_quality_note": "",
    }
    fake_persona = "허허, 청년의 결이로다. 이 늙은이 이만 자네의 상을 마치노라."
    metrics = _make_metrics_with_low_jaebaek()

    # output_safety_gate를 예외 던지게 강제
    def _raise(*a, **kw):
        raise RuntimeError("forced gate failure")

    with patch.object(face_reading, "_call_stage1_objective", return_value=fake_anat), \
         patch.object(face_reading, "_call_stage2_persona", return_value=fake_persona), \
         patch.object(face_reading, "_load_cache", return_value=None), \
         patch.object(face_reading, "_save_cache"), \
         patch("engine.safety.llm.output_safety_gate.run_safety_gates", side_effect=_raise):
        out = face_reading.generate_face_reading(
            image_b64=_DUMMY_IMAGE_B64,
            age=30,
            metrics=metrics,
        )

    # 폴백 미발생, verdict는 None
    assert out["safety_gate_fallback_used"] is False
    assert out["safety_gate_verdict"] is None
    # 원본 응답 유지
    assert "청년의 결이로다" in out["text"]


# ─────────────────────────── metrics 부재 시 검증 면제 ───────────────────────────

def test_adr163_no_metrics_no_palace_score_check():
    """metrics 미주입 시 palace_scores=None → palace_score 검증 면제."""
    from engine.divination.face import reading as face_reading

    fake_anat = {
        "face_outline": {}, "forehead": {}, "eyebrow": {}, "eye": {},
        "nose": {}, "mouth": {}, "chin": {}, "cheek_zygomatic": {},
        "complexion": {}, "distinctive_feature": "",
        "photo_quality_note": "",
    }
    # 단정 어휘는 있으나 metrics 없으므로 점수 검증 X
    fake_persona = (
        "허허, 그대 재물복이 풍성하니 좋은 결이로다. 청년의 자리가 두텁구먼. "
        "이 늙은이 이만 자네의 상을 마치노라."
    )

    with patch.object(face_reading, "_call_stage1_objective", return_value=fake_anat), \
         patch.object(face_reading, "_call_stage2_persona", return_value=fake_persona), \
         patch.object(face_reading, "_load_cache", return_value=None), \
         patch.object(face_reading, "_save_cache"):
        out = face_reading.generate_face_reading(
            image_b64=_DUMMY_IMAGE_B64,
            age=30,
            gender="male",
            metrics=None,
        )

    # metrics 없으면 palace_scores도 None → palace_score 검증 면제
    # (다른 검증으로 인한 fallback은 가능하나 palace_score_mismatch 사유여서는 안 됨)
    palace_score_in_failures = any(
        "palace" in (f or "").lower() for f in out["safety_gate_failures"]
    )
    assert palace_score_in_failures is False
