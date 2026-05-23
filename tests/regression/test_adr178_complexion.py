"""ADR-178 - 한국인 얼굴 L*a*b* 화장품 베이스라인 결정론 회귀."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_rgb_to_lab_white():
    """순백 RGB(255,255,255) → L≈100, a≈0, b≈0."""
    from engine.divination.face.complexion import rgb_to_lab
    L, a, b = rgb_to_lab(255, 255, 255)
    assert L > 99.0
    assert abs(a) < 1.0
    assert abs(b) < 1.0


def test_rgb_to_lab_black():
    """순흑 RGB(0,0,0) → L=0."""
    from engine.divination.face.complexion import rgb_to_lab
    L, a, b = rgb_to_lab(0, 0, 0)
    assert L < 1.0


def test_rgb_to_lab_red_positive_a():
    """순적색 RGB(255,0,0) → a > 0 (적-녹 축 양수)."""
    from engine.divination.face.complexion import rgb_to_lab
    L, a, b = rgb_to_lab(255, 0, 0)
    assert a > 50.0


def test_compute_facial_color_basic():
    """기본 8 ROI 평균 RGB → ComplexionReport 산출."""
    from engine.divination.face.complexion import compute_facial_color
    roi_rgb = {
        "forehead": (180, 150, 130),
        "nose_tip": (190, 155, 135),
        "chin": (175, 145, 125),
        "cheekbone": (185, 150, 130),
        "cheek": (180, 148, 128),
        "jaw": (175, 142, 122),
        "neck": (180, 148, 128),
        "nose_bridge": (180, 150, 130),
    }
    report = compute_facial_color(roi_rgb)
    assert len(report.rois) == 8
    assert report.overall_L_mean > 0
    assert report.overall_uniformity >= 0


def test_unknown_roi_skipped():
    from engine.divination.face.complexion import compute_facial_color
    roi_rgb = {
        "forehead": (180, 150, 130),
        "unknown_zone": (100, 100, 100),
    }
    report = compute_facial_color(roi_rgb)
    assert "forehead" in report.rois
    assert "unknown_zone" not in report.rois


def test_lightness_label_bright():
    from engine.divination.face.complexion import compute_facial_color
    roi_rgb = {"forehead": (240, 230, 220)}
    report = compute_facial_color(roi_rgb)
    assert report.rois["forehead"].label_short == "환하다"


def test_lightness_label_dim():
    from engine.divination.face.complexion import compute_facial_color
    roi_rgb = {"forehead": (100, 80, 70)}
    report = compute_facial_color(roi_rgb)
    assert report.rois["forehead"].label_short == "옅다"


def test_disclaimer_in_report():
    from engine.divination.face.complexion import compute_facial_color, DISCLAIMER
    report = compute_facial_color({"forehead": (180, 150, 130)})
    assert report.disclaimer == DISCLAIMER
    assert "화장품 베이스라인" in DISCLAIMER
    assert "의료 진단" in DISCLAIMER


def test_sanitize_blocks_medical_terms():
    from engine.divination.face.complexion import sanitize_complexion_text
    safe, matched = sanitize_complexion_text("이 사람은 심장이 약합니다.")
    assert safe is False
    assert "심장" in matched


def test_sanitize_blocks_sasang_terms():
    from engine.divination.face.complexion import sanitize_complexion_text
    safe, matched = sanitize_complexion_text("이 사람은 태음인입니다.")
    assert safe is False
    assert "태음인" in matched


def test_sanitize_allows_safe_text():
    from engine.divination.face.complexion import sanitize_complexion_text
    safe, matched = sanitize_complexion_text(
        "그대의 이마가 환하고 광대가 고르니 결이 단정하다."
    )
    assert safe is True
    assert matched == []


def test_report_to_dict_serialization():
    from engine.divination.face.complexion import (
        compute_facial_color, report_to_dict, SOURCE_URL,
    )
    report = compute_facial_color({"forehead": (180, 150, 130)})
    d = report_to_dict(report)
    assert "rois" in d
    assert "forehead" in d["rois"]
    assert d["rois"]["forehead"]["L"] > 0
    assert d["source_url"] == SOURCE_URL


def test_source_url_is_springer():
    from engine.divination.face.complexion import SOURCE_URL
    assert "springer" in SOURCE_URL.lower()
    assert "10.1186/s41702-017-0002-7" in SOURCE_URL


def test_uniformity_zero_for_single_roi():
    from engine.divination.face.complexion import compute_facial_color
    report = compute_facial_color({"forehead": (180, 150, 130)})
    assert report.overall_uniformity == 0.0


def test_uniformity_increases_with_variation():
    from engine.divination.face.complexion import compute_facial_color
    uniform = {
        "forehead": (180, 150, 130),
        "cheek": (180, 150, 130),
    }
    varied = {
        "forehead": (240, 230, 220),
        "cheek": (100, 80, 70),
    }
    r1 = compute_facial_color(uniform)
    r2 = compute_facial_color(varied)
    assert r2.overall_uniformity > r1.overall_uniformity


# ───── ADR-201 gender 분기 베이스라인 회귀 ─────

def test_adr201_male_baseline_darker_than_female():
    """남성 베이스라인 L*은 여성보다 낮음 (피부 더 어두움)."""
    from engine.divination.face.complexion import _select_baseline
    male_baseline = _select_baseline("male")
    female_baseline = _select_baseline("female")
    for roi in male_baseline:
        assert male_baseline[roi]["L"] < female_baseline[roi]["L"]


def test_adr201_male_z_score_differs():
    """동일 RGB라도 gender 분기 시 z-score 다름."""
    from engine.divination.face.complexion import compute_facial_color
    rgb_input = {"forehead": (180, 150, 130)}
    r_male = compute_facial_color(rgb_input, gender="male")
    r_female = compute_facial_color(rgb_input, gender="female")
    assert r_male.rois["forehead"].L_zscore != r_female.rois["forehead"].L_zscore


def test_adr201_korean_gender_terms_accepted():
    """한국어 gender 어휘 '남'/'여' 인식."""
    from engine.divination.face.complexion import _select_baseline
    m1 = _select_baseline("M")
    m2 = _select_baseline("남")
    assert m1 == m2


def test_adr201_none_gender_falls_back_to_female():
    """gender=None 이면 여성 베이스라인 (역호환)."""
    from engine.divination.face.complexion import (
        _select_baseline, _KOREAN_FACIAL_LAB_BASELINE_FEMALE,
    )
    assert _select_baseline(None) is _KOREAN_FACIAL_LAB_BASELINE_FEMALE


def test_adr201_unknown_gender_safe_fallback():
    """알 수 없는 gender → 여성 (안전 우선)."""
    from engine.divination.face.complexion import (
        _select_baseline, _KOREAN_FACIAL_LAB_BASELINE_FEMALE,
    )
    assert _select_baseline("other") is _KOREAN_FACIAL_LAB_BASELINE_FEMALE
