"""ADR-216 - U-Net 손금 선 검출 인터페이스 회귀."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_check_availability_no_pytorch_or_no_weights(tmp_path, monkeypatch):
    """PyTorch 부재 또는 가중치 부재 → fallback_reason 명시.

    ADR-223 이후 기본 경로(data/palm/unet_weights.pt)에 가중치 존재 가능 —
    본 테스트는 임시 cwd로 격리해 가중치 부재 환경 강제.
    """
    from engine.divination.palm.unet_line_extractor import check_unet_availability
    monkeypatch.chdir(tmp_path)  # 가중치 기본 경로 부재 환경
    monkeypatch.delenv("PALM_UNET_MODEL_PATH", raising=False)
    r = check_unet_availability()
    assert r.model_loadable is False
    assert r.fallback_reason in ("no_pytorch", "no_weights")


def test_check_availability_nonexistent_weights_path(monkeypatch):
    """존재하지 않는 가중치 경로 → no_weights (PyTorch 분기).

    ADR-253 이후 check_unet_availability 는 ONNX(_HAS_ORT)를 우선 점검하므로,
    PyTorch 가중치 분기를 검증하려면 ONNX 경로를 비활성화해야 한다.
    (onnxruntime 설치 환경에서 _HAS_ORT=True 면 환경변수 무관하게 'ready' 반환)
    """
    from engine.divination.palm import unet_line_extractor as ule

    # ONNX 우선 경로 비활성화 → PyTorch 가중치 분기 강제
    monkeypatch.setattr(ule, "_HAS_ORT", False, raising=False)
    monkeypatch.setenv("PALM_UNET_MODEL_PATH", "/nonexistent/path/model.pt")

    r = ule.check_unet_availability()
    if r.pytorch_available:  # PyTorch 미설치 환경은 no_pytorch 로 조기 반환
        assert r.fallback_reason == "no_weights"
        assert r.model_loadable is False


def test_extract_palm_lines_falls_back_to_gabor(tmp_path, monkeypatch):
    """가중치 부재 시 Gabor fallback 작동.

    ADR-223 이후 기본 경로에 가중치 존재 가능 — 임시 cwd로 격리.
    """
    from engine.divination.palm.unet_line_extractor import (
        extract_palm_lines_best_available,
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PALM_UNET_MODEL_PATH", raising=False)
    img = np.full((90, 90, 3), 200, dtype=np.uint8)
    img[20, :, :] = 50
    r = extract_palm_lines_best_available(img)
    # 가중치 격리 환경 → Gabor fallback
    assert r.used_unet is False
    assert "upper_density" in r.raw_metrics
    assert r.fallback_reason in ("no_pytorch", "no_weights")


def test_extract_palm_lines_with_gabor_raw_metrics():
    """Gabor fallback도 raw_metrics 5 영역 모두 노출."""
    from engine.divination.palm.unet_line_extractor import (
        extract_palm_lines_best_available,
    )
    img = np.full((60, 60, 3), 150, dtype=np.uint8)
    img[20, :, :] = 50
    r = extract_palm_lines_best_available(img)
    assert "upper_density" in r.raw_metrics
    assert "middle_density" in r.raw_metrics
    assert "lower_density" in r.raw_metrics
    assert "lower_left_density" in r.raw_metrics
    assert "lower_right_density" in r.raw_metrics


def test_disclaimer_blocks_fate_mapping():
    from engine.divination.palm.unet_line_extractor import DISCLAIMER
    assert "운명" in DISCLAIMER
    assert "학파 명칭" in DISCLAIMER


def test_source_url_arxiv():
    from engine.divination.palm.unet_line_extractor import (
        SOURCE_URL_PAPER, SOURCE_URL_PYTORCH_UNET,
    )
    assert "arxiv" in SOURCE_URL_PAPER.lower()
    assert "2102.12127" in SOURCE_URL_PAPER
    assert "github" in SOURCE_URL_PYTORCH_UNET.lower()


def test_unet_placeholder_returns_none():
    """_run_unet_inference은 placeholder — None 반환 (사용자 결단 전)."""
    from engine.divination.palm.unet_line_extractor import _run_unet_inference
    result = _run_unet_inference(np.zeros((10, 10, 3)), "/some/path.pt")
    assert result is None


def test_fallback_disclaimer_passes_fate_assertion():
    """DISCLAIMER 어휘가 ADR-171 fate_assertion 통과."""
    from engine.divination.palm.unet_line_extractor import DISCLAIMER
    from engine.safety.llm.domain_assertion_dict import detect_fate_assertions
    r = detect_fate_assertions(DISCLAIMER, domain="palm")
    assert r.detected is False
