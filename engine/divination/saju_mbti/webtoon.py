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
_RECOMPOSE_MODEL = os.environ.get("BIZROUTER_RECOMPOSE_MODEL", "anthropic/claude-sonnet-4.6")

_RECOMPOSE_SYSTEM = (
    "당신은 한국 사극 만담 구성가입니다. 사주 풀이 본문을 받아서 만월 아씨(달빛 아래 사주를 짚어드리는 정자의 아씨)의 "
    "웹툰 5장(14컷) 대사로 자연스럽게 다듬어 주세요.\n\n"
    "## 컷 배치\n"
    "1장(3컷): 나레이션·인사 → 만월 대사·운명 운\n"
    "2장(3컷): 성격·기질 본격 풀이\n"
    "3장(3컷): 재물·일·직업\n"
    "4장(3컷): 인연·인간관계·연애\n"
    "5장(2컷): 마무리 조언·한 마디\n\n"
    "## 규칙\n"
    "- 한 컷 = 한 마디. 30~70자, 자연스러운 종결.\n"
    "- 사극 존댓말 (\"~하시지요\", \"~의 결로 흐를 듯하옵니다\" 등). 만월 아씨가 손님에게 차분히 이야기하는 톤.\n"
    "- AI/모델 메타 언급 금지. 단정적 예언 금지(\"~의 흐름이 보입니다\" 같은 경향성).\n"
    "- 14컷 흐름이 한 편의 만담이 되도록. 끊김·중복 없이.\n"
    "- JSON 외 다른 텍스트는 출력하지 마라."
)

# saju_mbti/ 하위로 이동해 깊이 +1 (구조 리팩터링 2026-06-21)
_WEBTOON_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "front" / "media" / "saju_webtoon"
)
_CACHE_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "step_archive"
    / "saju_webtoon_cache"
)
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


def _recompose_to_14_cuts(reading_text: str) -> list[str]:
    """풀이 본문을 14컷 사극 만담 대사로 다듬는다. 실패 시 단순 분배 폴백."""
    api_key = os.environ.get("BIZROUTER_API_KEY", "").strip()
    if not api_key:
        return _distribute_to_slots(reading_text, 14)

    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=_BIZROUTER_BASE)
    user_msg = (
        f"[풀이 본문]\n{reading_text}\n\n"
        "위 풀이를 14컷 만담으로 다듬어 다음 JSON으로만 반환:\n"
        '{"cuts": ["...", "...", ...] }\n'
        "cuts 배열 길이는 정확히 14."
    )
    try:
        resp = client.chat.completions.create(
            model=_RECOMPOSE_MODEL,
            messages=[
                {"role": "system", "content": _RECOMPOSE_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=4096,
        )
        content = (resp.choices[0].message.content or "").strip()
        m = re.search(r"\{[\s\S]*\}", content)
        if not m:
            raise ValueError("no JSON in recompose response")
        data = json.loads(m.group(0))
        cuts = data.get("cuts", [])
        if not isinstance(cuts, list) or len(cuts) != 14:
            raise ValueError(f"cuts length != 14 (got {len(cuts)})")
        return [str(c).strip()[:120] for c in cuts]
    except Exception as e:
        logger.warning("recompose failed, fallback to simple distribution: %s", e)
        return _distribute_to_slots(reading_text, 14)


def _build_prompt(page_idx: int, page_meta: dict, slot_texts: list[str]) -> str:
    slot_desc = []
    for i, (slot, text) in enumerate(zip(page_meta["slots"], slot_texts), 1):
        clean = (text or "").strip()
        if clean:
            slot_desc.append(f"{i}번 슬롯 — {slot['pos']}의 {slot['kind']}:\n   \"{clean}\"")
        else:
            slot_desc.append(f"{i}번 슬롯 — {slot['pos']}의 {slot['kind']}: (빈칸 유지)")
    return (
        "## 이미지 편집 작업: 빈 말풍선·박스에 한국어 글자 그리기\n\n"
        "이 만월 아씨 웹툰 페이지 이미지에 한국어 글자를 그려 넣어주세요.\n\n"
        "## 절대 규칙\n"
        "1. 원본 그림(만월 아씨 캐릭터, 배경, 말풍선과 박스의 모양·테두리·색)은 **절대** 바꾸지 마세요.\n"
        "2. 흰 타원과 갈색 박스 안에만 글자를 그립니다.\n"
        "3. **글자는 한 글자도 빠뜨리거나 잘못 쓰지 말고 정확히** 받아쓰세요. 받침·자모 모두 정확.\n"
        "4. 글자 스타일: 한국어 손글씨, 또렷한 가독성. 흰 타원 안엔 진한 갈색(#2a1f1c), 갈색 박스 안엔 따뜻한 크림색(#f5ead2).\n"
        "5. 글자는 말풍선/박스의 가운데에 자연스럽게 배치. 줄바꿈은 가독성 좋게.\n"
        "6. 글자 크기는 말풍선 안에 가득 들어차되 가장자리 여백 5%.\n\n"
        "## 이 페이지의 글자 배치\n" + "\n".join(slot_desc) + "\n\n"
        "위 글자들을 정확하게 그려 넣어 완성된 이미지를 반환해주세요."
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
    # Stage A: 14컷 재구성 (Sonnet 4.6)
    all_texts = _recompose_to_14_cuts(reading_text)
    if len(all_texts) != total_slots:
        # 길이 안 맞으면 안전 폴백
        all_texts = _distribute_to_slots(reading_text, total_slots)

    cursor = 0
    page_inputs = []
    for pm in PAGES:
        n = len(pm["slots"])
        page_inputs.append((pm, all_texts[cursor:cursor+n]))
        cursor += n

    # Stage B: 5장 병렬 호출 (Nano Banana Pro)
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
