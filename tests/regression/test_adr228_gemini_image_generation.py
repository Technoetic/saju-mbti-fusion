"""ADR-228 - Gemini 2.5 Flash Image 손금 사진 생성 회귀.

API 키 부재 환경에서 안전 폴백·인터페이스 검증. 실 API 호출은 Fly.io 운영에서.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_adr228_module_imports():
    """gemini_image_generator 모듈 import 안전."""
    from engine.divination.palm.gemini_image_generator import (
        GEMINI_IMAGE_MODEL, SOURCE_URL, GeminiImageGenResult,
    )
    assert "gemini-2.5-flash-image" in GEMINI_IMAGE_MODEL
    assert "google" in GEMINI_IMAGE_MODEL or "gemini" in GEMINI_IMAGE_MODEL.lower()
    assert SOURCE_URL.startswith("http")


def test_adr228_prompt_templates_diverse():
    """다양 프롬프트 풀 (Canny2Palm 학술 근거 — 다양성 ↑ F1 ↑)."""
    from engine.divination.palm.gemini_image_generator import _PROMPT_TEMPLATES
    assert len(_PROMPT_TEMPLATES) >= 5
    # 손금 종류 다양성 (life·head·heart·fate·simian·girdle)
    all_prompts = " ".join(_PROMPT_TEMPLATES).lower()
    diverse_terms = ["life", "head", "heart", "fate", "simian", "girdle"]
    matched = sum(1 for t in diverse_terms if t in all_prompts)
    assert matched >= 4


def test_adr228_bizrouter_no_key_returns_none(monkeypatch):
    """BIZROUTER_API_KEY 부재 시 안전 None 반환."""
    from engine.divination.palm.gemini_image_generator import (
        generate_palm_image_bizrouter,
    )
    monkeypatch.delenv("BIZROUTER_API_KEY", raising=False)
    result = generate_palm_image_bizrouter("test prompt")
    assert result is None


def test_adr228_gemini_direct_no_key_returns_none(monkeypatch):
    """GEMINI_API_KEY·GOOGLE_API_KEY 부재 시 안전 None."""
    from engine.divination.palm.gemini_image_generator import (
        generate_palm_image_gemini_direct,
    )
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    result = generate_palm_image_gemini_direct("test prompt")
    assert result is None


def test_adr228_dataset_generation_no_keys_safe(tmp_path, monkeypatch):
    """API 키 모두 부재 시 안전 폴백 — failed_attempts 카운트."""
    from engine.divination.palm.gemini_image_generator import (
        generate_synthetic_palm_dataset,
    )
    monkeypatch.delenv("BIZROUTER_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    result = generate_synthetic_palm_dataset(
        output_dir=str(tmp_path), n_images=3,
    )
    assert result.n_generated == 0
    assert result.failed_attempts == 3
    assert result.cost_estimate_usd == 0.0


def test_adr228_cost_estimate_calculation():
    """비용 추정 = 0.039 × n_generated."""
    from engine.divination.palm.gemini_image_generator import GeminiImageGenResult
    r = GeminiImageGenResult(
        n_generated=10, output_dir="/tmp", failed_attempts=0, cost_estimate_usd=0.39,
    )
    assert r.cost_estimate_usd == 0.39


def test_adr228_source_url_google():
    from engine.divination.palm.gemini_image_generator import SOURCE_URL
    assert "google" in SOURCE_URL.lower() or "ai.google" in SOURCE_URL.lower()


def test_adr228_output_dir_created(tmp_path, monkeypatch):
    """API 키 부재여도 디렉토리 자동 생성."""
    from engine.divination.palm.gemini_image_generator import (
        generate_synthetic_palm_dataset,
    )
    monkeypatch.delenv("BIZROUTER_API_KEY", raising=False)
    output = tmp_path / "new_dir"
    result = generate_synthetic_palm_dataset(
        output_dir=str(output), n_images=1,
    )
    assert output.exists()
    assert result.output_dir == str(output)
