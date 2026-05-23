"""ADR-228 - Gemini 2.5 Flash Image 손금 사진 자동 생성 파이프라인.

학술 근거:
  - Canny2Palm (arXiv 2505.04922, 2025) — 합성 손금 학습 시 실 데이터
    7.2% 초과 정확도, 10% 실 데이터로 100% 동등 효과 입증
  - RPG-Palm (arXiv 2307.14016) — pseudo-data pretrain → real fine-tune
    성능 향상 패턴

본 모듈은 **사진 촬영 결단까지 본 AI 단독 해결**:
  - BizRouter 경유 Gemini 2.5 Flash Image API 호출
  - 다양한 손금 패턴 자동 생성 (생명선·두뇌선·감정선·운명선 강조)
  - 이미지 → 학습 데이터셋 자동 저장

비용:
  - $0.039/이미지 (BizRouter 가격 동일 추정)
  - 무료 500장/일 한도 (Gemini Direct API)

ADR 정합:
  - ADR-225 데이터셋 파이프라인 (4번째 갈래 추가)
  - ADR-226 self-training (생성 사진 → pseudo-label)
  - ADR-006 자문 거절 (생성된 사진에 운명 매핑 X — 형태 학습만)
  - ADR-010 사실성 분리 (생성 사진 명시 영속)
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass


GEMINI_IMAGE_MODEL = "google/gemini-2.5-flash-image"
SOURCE_URL = "https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash-image"


# Canny2Palm 학술 근거 — 다양한 손금 패턴 프롬프트 다양성
_PROMPT_TEMPLATES = [
    "A clear close-up photograph of an open human palm showing visible palm lines "
    "(life line, head line, heart line) in natural lighting. Photorealistic, "
    "neutral background, no jewelry, no text.",

    "Detailed high-resolution photograph of a human palm with prominent simian "
    "crease (single transverse line). Photorealistic, natural skin tone, "
    "centered composition.",

    "Photo of an aged human palm showing deep wrinkles and clear palm lines, "
    "well-defined heart line and head line. Soft lighting, photorealistic.",

    "Young adult human palm photograph with three clear principal lines and "
    "fine secondary creases visible. Natural daylight, neutral background.",

    "Human palm with curved life line, straight head line, and wavy heart line. "
    "Bright lighting, photorealistic close-up.",

    "Female human palm with delicate lines including girdle of Venus. "
    "Photorealistic, soft natural light, no nail polish.",

    "Male human palm with strong fate line and clear principal creases. "
    "Photorealistic, neutral palette, close-up framing.",

    "Human palm with short life line and long head line. "
    "Photorealistic close-up, even lighting.",
]


@dataclass(frozen=True)
class GeminiImageGenResult:
    """Gemini 이미지 생성 결과."""
    n_generated: int
    output_dir: str
    failed_attempts: int
    cost_estimate_usd: float       # 0.039 × n_generated
    source_url: str = SOURCE_URL


def _bizrouter_client():
    """BizRouter OpenAI 호환 클라이언트."""
    from openai import OpenAI
    return OpenAI(
        api_key=os.environ.get("BIZROUTER_API_KEY"),
        base_url=os.environ.get(
            "BIZROUTER_BASE_URL", "https://api.bizrouter.ai/v1"
        ),
    )


def _gemini_direct_client():
    """Gemini Direct API 폴백 (옵션)."""
    try:
        from google import genai  # type: ignore[import-not-found]
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return None
        return genai.Client(api_key=api_key)
    except ImportError:
        return None


def generate_palm_image_bizrouter(
    prompt: str,
    timeout: int = 60,
) -> bytes | None:
    """BizRouter 경유 Gemini 이미지 생성.

    Args:
        prompt: 생성 프롬프트.
        timeout: 타임아웃 (초).

    Returns:
        PNG bytes 또는 None (실패 시).
    """
    api_key = os.environ.get("BIZROUTER_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        client = _bizrouter_client()
        # BizRouter는 OpenAI 호환 → Gemini image generation API 형식
        # (BizRouter가 Gemini image를 라우팅하는 경우)
        resp = client.images.generate(
            model=GEMINI_IMAGE_MODEL,
            prompt=prompt,
            n=1,
            size="1024x1024",
        )
        if not resp.data:
            return None
        # base64 응답 디코드
        b64_data = getattr(resp.data[0], "b64_json", None)
        if b64_data:
            return base64.b64decode(b64_data)
        # URL 응답 폴백
        img_url = getattr(resp.data[0], "url", None)
        if img_url:
            import urllib.request
            with urllib.request.urlopen(img_url, timeout=timeout) as r:
                return r.read()
        return None
    except Exception:
        return None


def generate_palm_image_gemini_direct(prompt: str) -> bytes | None:
    """Gemini Direct API 경유 이미지 생성 (폴백)."""
    client = _gemini_direct_client()
    if client is None:
        return None
    try:
        resp = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt,
        )
        # 응답에서 이미지 데이터 추출
        for part in resp.candidates[0].content.parts:  # type: ignore[union-attr,index]
            if hasattr(part, "inline_data") and part.inline_data:
                data = getattr(part.inline_data, "data", None)
                if data:
                    if isinstance(data, str):
                        return base64.b64decode(data)
                    if isinstance(data, bytes):
                        return data
        return None
    except Exception:
        return None


def generate_synthetic_palm_dataset(
    output_dir: str = "data/palm/training/",
    n_images: int = 20,
    prompts: list[str] | None = None,
    seed: int = 42,
) -> GeminiImageGenResult:
    """Gemini 이미지 생성으로 손금 학습 데이터셋 자동 구축.

    Args:
        output_dir: 저장 디렉토리.
        n_images: 생성 이미지 수.
        prompts: 커스텀 프롬프트 (None이면 기본 다양 프롬프트 순환).
        seed: 프롬프트 선택 시드.

    Returns:
        GeminiImageGenResult.
    """
    import random

    if prompts is None:
        prompts = list(_PROMPT_TEMPLATES)

    os.makedirs(output_dir, exist_ok=True)
    rng = random.Random(seed)
    success = 0
    failed = 0

    for i in range(n_images):
        prompt = rng.choice(prompts)
        # 1. BizRouter 시도
        img_bytes = generate_palm_image_bizrouter(prompt)
        # 2. Gemini Direct 폴백
        if img_bytes is None:
            img_bytes = generate_palm_image_gemini_direct(prompt)
        if img_bytes is None:
            failed += 1
            continue
        out_path = os.path.join(output_dir, f"gemini_{i:03d}.png")
        try:
            with open(out_path, "wb") as f:
                f.write(img_bytes)
            success += 1
        except Exception:
            failed += 1

    cost = round(success * 0.039, 4)
    return GeminiImageGenResult(
        n_generated=success,
        output_dir=output_dir,
        failed_attempts=failed,
        cost_estimate_usd=cost,
    )


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Gemini 손금 이미지 생성 (ADR-228)")
    parser.add_argument("--output-dir", default="data/palm/training/")
    parser.add_argument("--n-images", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    result = generate_synthetic_palm_dataset(
        output_dir=args.output_dir,
        n_images=args.n_images,
        seed=args.seed,
    )
    print(f"n_generated: {result.n_generated}")
    print(f"failed_attempts: {result.failed_attempts}")
    print(f"cost_estimate_usd: ${result.cost_estimate_usd}")
    print(f"output_dir: {result.output_dir}")


if __name__ == "__main__":
    main()
