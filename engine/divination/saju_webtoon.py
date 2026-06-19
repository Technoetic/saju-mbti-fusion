"""정통 사주 풀이 결과를 웹툰 5장(p6~p10.jpg)에 글자가 그려진 이미지로 변환.

bizrouter API의 Nano Banana Pro(google/gemini-3-pro-image)를 5장 병렬 호출.
풀이 텍스트를 단락 단위로 분할 → 각 페이지의 말풍선/박스에 들어갈 만한 문장을
프롬프트에 넣어 모델이 직접 글자를 이미지에 그리도록 한다.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_BIZROUTER_BASE = os.environ.get("BIZROUTER_BASE_URL", "https://api.bizrouter.ai/v1")
_MODEL = os.environ.get("BIZROUTER_WEBTOON_MODEL", "google/gemini-3-pro-image")

_WEBTOON_DIR = Path(__file__).resolve().parent.parent.parent / "front" / "media" / "saju_webtoon"
_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "step_archive" / "saju_webtoon_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_TTL_SEC = 7 * 24 * 3600  # 7일

# 페이지별 슬롯 메타 — 어떤 종류·몇 개 말풍선이 있는지를 모델에게 알려주는 힌트.
PAGES = [
    {"src": "p6.jpg", "slots": [
        {"kind": "갈색 박스(나레이션)", "pos": "정자 풍경 컷 끝 가운데"},
        {"kind": "흰 타원(만월 아씨 대사)", "pos": "만월 아씨와 수정구 컷 끝 가운데"},
        {"kind": "갈색 박스(나레이션)", "pos": "책상 컷 끝 가운데"},
    ]},
    {"src": "p7.jpg", "slots": [
        {"kind": "흰 타원(만월 아씨 대사)", "pos": "책상 컷 끝 왼쪽"},
        {"kind": "큰 흰 타원(만월 아씨 대사)", "pos": "가운데 종이 컷 끝 가운데"},
        {"kind": "흰 타원(만월 아씨 대사)", "pos": "글 쓰는 컷 끝 좌측 작은 꼬리"},
    ]},
    {"src": "p8.jpg", "slots": [
        {"kind": "흰 타원(만월 아씨 대사)", "pos": "바둑돌 컷 끝 우측"},
        {"kind": "흰 타원(만월 아씨 대사)", "pos": "보름달 컷 끝 가운데"},
        {"kind": "흰 타원(만월 아씨 대사)", "pos": "등불 컷 끝 가운데"},
    ]},
    {"src": "p9.jpg", "slots": [
        {"kind": "흰 타원(만월 아씨 대사)", "pos": "종이 든 컷 끝 우상단"},
        {"kind": "큰 흰 타원(만월 아씨 대사)", "pos": "정자 가리키는 컷 끝 가운데"},
        {"kind": "흰 타원(만월 아씨 대사)", "pos": "글 쓰는 컷 끝 좌측 꼬리"},
    ]},
    {"src": "p10.jpg", "slots": [
        {"kind": "큰 흰 타원(만월 아씨 대사)", "pos": "꽃·만월 컷 끝 가운데"},
        {"kind": "흰 타원(만월 아씨 대사)", "pos": "보름달 컷 끝 가운데"},
    ]},
]


def _strip_markdown(md: str) -> str:
    if not md:
        return ""
    s = re.sub(r"^#{1,6}\s+", "", md, flags=re.M)
    s = re.sub(r"```[\s\S]*?```", "", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"\*([^*]+)\*", r"\1", s)
    s = re.sub(r"^\s*[-*+]\s+", "", s, flags=re.M)
    return s.strip()


def _split_sentences(text: str) -> list[str]:
    text = _strip_markdown(text)
    parts = re.split(r"(?<=[.!?。…])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip() and len(p.strip()) >= 6]


def _distribute_to_slots(text: str, total_slots: int) -> list[str]:
    """풀이를 14개 슬롯에 균등 분배 + 한 슬롯당 30~60자."""
    sentences = _split_sentences(text)
    if not sentences:
        return [""] * total_slots
    # 인접 병합으로 슬롯 수 맞춤
    units = sentences[:]
    while len(units) > total_slots:
        # 가장 짧은 인접 두 단락 병합
        min_idx, min_sum = 0, 10**9
        for i in range(len(units) - 1):
            s = len(units[i]) + len(units[i+1])
            if s < min_sum:
                min_sum, min_idx = s, i
        units[min_idx] = units[min_idx] + " " + units[min_idx+1]
        del units[min_idx+1]
    # 슬롯이 더 많으면 빈 채움
    while len(units) < total_slots:
        units.append("")
    # 각 슬롯 길이 제한 (말풍선 안에 들어갈 만큼)
    return [u[:80] for u in units]


def _build_prompt(page_idx: int, page_meta: dict, slot_texts: list[str]) -> str:
    slot_desc = []
    for i, (slot, text) in enumerate(zip(page_meta["slots"], slot_texts), 1):
        if text:
            slot_desc.append(f"{i}. {slot['pos']}의 {slot['kind']} → \"{text}\"")
        else:
            slot_desc.append(f"{i}. {slot['pos']}의 {slot['kind']} → (빈칸 유지)")
    return (
        "이 웹툰 페이지의 빈 말풍선과 나레이션 박스에 한국어 글자를 깔끔하게 그려 넣어주세요.\n\n"
        "## 규칙\n"
        "- 그림(만월 아씨 캐릭터·배경·말풍선 모양)은 절대 바꾸지 마세요.\n"
        "- 빈 흰 타원과 갈색 박스 안에만 글자를 그리세요.\n"
        "- 글자는 한국어 손글씨 스타일, 또렷한 검은색(흰 타원) 또는 따뜻한 크림색(갈색 박스).\n"
        "- 글자는 말풍선 가운데에 자연스럽게 정렬, 줄바꿈은 적절히.\n"
        "- 한 글자도 빠뜨리지 말고 정확하게 그려주세요.\n\n"
        f"## 이 페이지의 말풍선 → 들어갈 글자\n" + "\n".join(slot_desc)
    )


def _cache_key(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]


def _load_cache(text: str) -> list[str] | None:
    key = _cache_key(text)
    cf = _CACHE_DIR / f"{key}.json"
    if not cf.exists():
        return None
    try:
        data = json.loads(cf.read_text(encoding="utf-8"))
        if time.time() - data.get("_saved_at", 0) > _TTL_SEC:
            return None
        return data.get("images")
    except Exception:
        return None


def _save_cache(text: str, images_b64: list[str]) -> None:
    key = _cache_key(text)
    cf = _CACHE_DIR / f"{key}.json"
    try:
        cf.write_text(json.dumps({
            "images": images_b64,
            "_saved_at": time.time(),
        }), encoding="utf-8")
    except Exception:
        pass


def _call_nano_banana(page_idx: int, page_meta: dict, slot_texts: list[str]) -> str:
    """단일 페이지 호출 → base64 PNG 반환."""
    from openai import OpenAI

    api_key = os.environ.get("BIZROUTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("BIZROUTER_API_KEY not set")

    src_path = _WEBTOON_DIR / page_meta["src"]
    if not src_path.exists():
        raise FileNotFoundError(f"webtoon page not found: {src_path}")
    raw = src_path.read_bytes()
    img_b64 = base64.b64encode(raw).decode("ascii")
    data_url = f"data:image/jpeg;base64,{img_b64}"

    prompt = _build_prompt(page_idx, page_meta, slot_texts)
    client = OpenAI(api_key=api_key, base_url=_BIZROUTER_BASE)
    resp = client.chat.completions.create(
        model=_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }],
        max_tokens=16384,
    )
    if not resp.choices:
        raise ValueError(f"page {page_idx}: empty choices")
    content = resp.choices[0].message.content
    if not isinstance(content, list):
        raise ValueError(f"page {page_idx}: content not list (got {type(content).__name__})")
    for item in content:
        if isinstance(item, dict) and item.get("type") == "image_url":
            url = item.get("image_url", {}).get("url", "")
            if url.startswith("data:") and "," in url:
                _, b64part = url.split(",", 1)
                return b64part
    raise ValueError(f"page {page_idx}: no image in response")


def generate_webtoon_images(reading_text: str) -> list[str]:
    """5장을 병렬 호출하여 base64 PNG 리스트 반환.

    - 같은 입력은 7일 캐시.
    - 한 장이라도 실패하면 RuntimeError. 호출자는 fallback으로 기존 CSS 오버레이.
    """
    cached = _load_cache(reading_text)
    if cached and len(cached) == len(PAGES):
        return cached

    total_slots = sum(len(p["slots"]) for p in PAGES)
    all_texts = _distribute_to_slots(reading_text, total_slots)

    cursor = 0
    page_inputs = []
    for p in PAGES:
        n = len(p["slots"])
        page_inputs.append((p, all_texts[cursor:cursor+n]))
        cursor += n

    results: list[str | None] = [None] * len(PAGES)
    errors: list[str] = []

    def worker(i: int, page_meta: dict, slot_texts: list[str]) -> None:
        try:
            results[i] = _call_nano_banana(i, page_meta, slot_texts)
        except Exception as e:
            errors.append(f"page {i}: {e}")

    with ThreadPoolExecutor(max_workers=5) as pool:
        futs = [pool.submit(worker, i, pm, st) for i, (pm, st) in enumerate(page_inputs)]
        for f in as_completed(futs):
            f.result()

    if errors or any(r is None for r in results):
        raise RuntimeError(f"webtoon generation failed: {errors}")

    _save_cache(reading_text, results)  # type: ignore[arg-type]
    return results  # type: ignore[return-value]
