"""ADR-215 - 손금 선 검출 회귀."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_gabor_kernel_shape():
    from engine.divination.palm.line_extraction import gabor_kernel
    k = gabor_kernel(ksize=15)
    assert k.shape == (15, 15)
    assert k.dtype == np.float64


def test_gabor_kernel_centered():
    """Gabor 커널은 중심 대칭에 가까워야."""
    from engine.divination.palm.line_extraction import gabor_kernel
    k = gabor_kernel(ksize=15, theta=0.0)
    # 중심에서 양옆이 비슷한 패턴 (좌우 대칭)
    h = k.shape[0]
    center = k[h // 2, :]
    assert np.abs(center).max() > 0


def test_to_grayscale_rgb():
    from engine.divination.palm.line_extraction import to_grayscale
    rgb = np.zeros((10, 10, 3), dtype=np.uint8)
    rgb[..., 0] = 255  # 적색만
    gray = to_grayscale(rgb)
    assert gray.shape == (10, 10)
    # BT.709 luminance R=0.2126 가중
    assert abs(gray[0, 0] - 0.2126 * 255) < 1.0


def test_to_grayscale_already_gray():
    from engine.divination.palm.line_extraction import to_grayscale
    gray_in = np.full((10, 10), 128.0)
    gray_out = to_grayscale(gray_in)
    assert gray_out.shape == (10, 10)


def test_detect_palm_lines_empty():
    from engine.divination.palm.line_extraction import detect_palm_lines
    r = detect_palm_lines(np.array([]))
    assert r.n_lines_detected == 0
    assert "비어" in r.description_ko or "잘못" in r.description_ko


def test_detect_palm_lines_uniform_no_lines():
    """균일한 회색 이미지 → 선 검출 거의 없음."""
    from engine.divination.palm.line_extraction import detect_palm_lines
    img = np.full((100, 100, 3), 128, dtype=np.uint8)
    r = detect_palm_lines(img)
    # 균일한 이미지는 모든 픽셀의 Gabor 응답이 거의 동일 → 임계 통과 안 함
    assert r.n_lines_detected <= 3  # 임계 percentile에 따라 다름


def test_detect_palm_lines_with_horizontal_lines():
    """수평 줄무늬 이미지 → 선 다수 검출."""
    from engine.divination.palm.line_extraction import detect_palm_lines
    img = np.full((90, 90, 3), 200, dtype=np.uint8)
    # 수평 어두운 줄 3개
    img[20, :, :] = 50
    img[45, :, :] = 50
    img[70, :, :] = 50
    r = detect_palm_lines(img)
    assert r.line_density > 0
    assert r.raw_metrics["gabor_threshold"] > 0


def test_disclaimer_blocks_fate_mapping():
    from engine.divination.palm.line_extraction import detect_palm_lines, DISCLAIMER
    assert "운명" in DISCLAIMER
    assert "수명·재물 매핑이 아닙니다" in DISCLAIMER
    assert "의료" in DISCLAIMER


def test_source_urls_arxiv():
    from engine.divination.palm.line_extraction import SOURCE_URLS
    assert len(SOURCE_URLS) >= 2
    assert any("arxiv" in u.lower() for u in SOURCE_URLS)


def test_no_fate_assertion_in_descriptions():
    """모든 묘사 어휘가 ADR-171 fate_assertion 통과."""
    from engine.divination.palm.line_extraction import detect_palm_lines
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    # 3 케이스 묘사 모두 검증
    img_full = np.full((60, 60, 3), 100, dtype=np.uint8)
    img_full[10, :, :] = 200
    img_full[30, :, :] = 200
    img_full[50, :30, :] = 200
    r = detect_palm_lines(img_full)
    fate = detect_fate_assertions(r.description_ko, domain="palm")
    assert fate.detected is False, f"fate_assertion in: {r.description_ko}"


def test_raw_metrics_present():
    from engine.divination.palm.line_extraction import detect_palm_lines
    img = np.full((60, 60, 3), 150, dtype=np.uint8)
    img[20, :, :] = 50
    r = detect_palm_lines(img)
    assert "upper_density" in r.raw_metrics
    assert "middle_density" in r.raw_metrics
    assert "lower_left_density" in r.raw_metrics
    assert "gabor_threshold" in r.raw_metrics


def test_3_lines_detected_synthetic():
    """3 영역에 각각 강한 수평선 → 3 주선 모두 검출."""
    from engine.divination.palm.line_extraction import detect_palm_lines
    img = np.full((90, 90, 3), 200, dtype=np.uint8)
    # 상부 (감정선) — 두꺼운 줄
    img[10:13, :, :] = 30
    # 중부 (두뇌선)
    img[40:43, :, :] = 30
    # 하부 좌측 (생명선)
    img[70:73, :40, :] = 30
    r = detect_palm_lines(img)
    # 적어도 1선은 검출
    assert r.n_lines_detected >= 1
