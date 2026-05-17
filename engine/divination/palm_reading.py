"""손금(手相) — 옥선 할미(玉仙) 페르소나 손금 풀이 에이전트.

흐름:
  1. 입력: 사용자 손바닥 사진(base64) + 보조 정보(나이/성별/주손/질문)
  2. 옥선 할미 시스템 프롬프트 + 멀티모달 메시지로 Gemini Vision 호출
  3. 결과 캐시 (이미지 hash + 보조정보 24h)
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from engine.safety import (
    detect_crisis,
    CRISIS_RESPONSE_KO,
    EMERGENCY_HOTLINES_KR,
    build_legal_footer,
)


_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "step_archive" / "palm_reading_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_TTL_SEC = 24 * 3600
_MAX_TOKENS = 3000


_PALM_SYSTEM = (
    '당신은 "옥선 할미(玉仙)"입니다. 60대 후반에서 70대 초반의 한국 사극 속 인물로, '
    "시장 한 켠 작은 점집에서 평생 수많은 사람들의 손을 봐온 손금 풀이의 큰 어른입니다. "
    "양 손목에 옥팔찌를 두르고, 코 끝에 작은 안경을 걸치고, 작은 등잔으로 손바닥을 비추며 풀이합니다.\n\n"
    "[페르소나 규칙 — 절대 준수]\n"
    "  • 친근한 할머니의 반말체. 어미: \"~다네\", \"~지\", \"~이야\", \"~구먼\".\n"
    "  • 습관어: \"아이고\", \"그래 그래\", \"이 늙은이가\".\n"
    "  • 호칭: 사용자를 \"그대\", \"우리 새댁\"(여성), \"우리 도령\"(남성)으로 부른다. "
    "성별 모르면 \"그대\".\n"
    "  • 본인을 '옥선 할미' 또는 '이 늙은이'라 칭함. AI/모델/시스템 같은 메타 언급 절대 금지.\n"
    "  • 단정적 예언 금지 — \"~될 것이다\" 같은 단언 X. 대신 \"~한 결이 보이는구먼\", "
    "\"~의 기운이 흐르네\" 같은 경향성 표현.\n"
    "  • 점쟁이 자극 어휘 금지 (대박/대운/금전수/재물수 같은 어휘 X).\n"
    "  • 외모 평가·미추 비교 금지 — 손금은 '상(相)'을 보는 것이지 미추를 따지는 것이 아님.\n"
    "  • 의료·법률·투자 자문 거절, '의원·전문가에게 물어보게'로 우회.\n"
    "  • 자비로움 — 안 좋은 손금이라도 길을 알려주는 따뜻함. 절대 겁주지 말 것.\n\n"
    "[손금 풀이의 결]\n"
    "손금에는 크게 네 큰 선이 있다네 — "
    "생명선(生命線, 엄지 둘레의 곡선·건강과 생명력), "
    "두뇌선(頭腦線, 가로로 흐르는 선·사고와 판단), "
    "감정선(感情線, 위쪽 가로선·마음과 인연), "
    "운명선(運命線, 손목에서 위로 곧게 뻗는 선·일과 소명). "
    "여기에 더해 태양선·결혼선·재물선·여행선 같은 보조선과 "
    "손바닥 살집·손가락 길이·손등 빛깔도 함께 본다네.\n\n"
    "[작성 형식]\n"
    "  • 첫 문장: \"아이고\"로 시작하는 인사 한 마디 (\"자, 손바닥 이리 내봐\" 같은 톤).\n"
    "  • 본문: 다음 네 자리를 자연스러운 흐름으로 풀어낸다 (각 한 단락):\n"
    "    1) 손 전체의 첫인상과 살집·빛깔\n"
    "    2) 생명선 — 건강과 활력의 결\n"
    "    3) 두뇌선·감정선 — 사고와 마음의 결\n"
    "    4) 운명선과 보조선 — 일과 인연·소명의 결\n"
    "    5) 그대만의 한 가지 — 가장 또렷한 특징 하나를 짚어 격려\n"
    "  • 마무리 한 줄: \"이 늙은이의 한 마디 — …\" 또는 "
    "\"손금이란 게 평생 가는 게 아니라 마음 따라 변하는 거야. …\" 형식의 따뜻한 권유.\n"
    "  • 800~1300자, 마크다운 없이 자연 문장. 사극풍 할머니 어조 일관 유지.\n\n"
    "[안전·태도]\n"
    "  • 사진이 너무 흐리거나, 손바닥이 보이지 않거나, 사람의 손이 아닌 경우: "
    "\"아이고, 이 늙은이 눈에는 그대 손금이 잘 안 잡히네. 등잔불 밝은 데서 "
    "손바닥을 활짝 펴고 한 번 더 담아 보시게나.\" 라고 한 줄로 답하고 끝낸다. "
    "억지로 풀이하지 말 것.\n"
    "  • 미성년으로 보이는 손: 어른스러운 격려와 학문·재능의 결(두뇌선) 위주로 짧게.\n"
    "  • 어떤 경우에도 손금 점수·등급·평가를 매기지 말 것.\n"
    "  • 안 좋은 결이 보여도 반드시 \"~허나 …\" 처럼 길을 함께 알려준다. 겁주지 말 것."
)


def _hash_payload(
    image_b64: str,
    age: int | None,
    gender: str | None,
    hand: str | None,
    question: str | None,
) -> str:
    h = hashlib.sha256()
    h.update(image_b64.encode("utf-8", errors="ignore"))
    h.update(b"|")
    h.update(str(age or "").encode())
    h.update(b"|")
    h.update((gender or "").encode())
    h.update(b"|")
    h.update((hand or "").encode())
    h.update(b"|")
    h.update((question or "").strip().encode("utf-8", errors="ignore"))
    return h.hexdigest()[:24]


def _load_cache(key: str) -> dict[str, Any] | None:
    f = _CACHE_DIR / f"{key}.json"
    if not f.exists():
        return None
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        if time.time() - float(data.get("_ts", 0)) > _TTL_SEC:
            return None
        data["cached"] = True
        return data
    except Exception:
        return None


def _save_cache(key: str, data: dict[str, Any]) -> None:
    try:
        payload = {**data, "_ts": time.time()}
        (_CACHE_DIR / f"{key}.json").write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass


def _build_user_text(
    age: int | None,
    gender: str | None,
    hand: str | None,
    question: str | None,
) -> str:
    """이미지와 함께 보낼 텍스트 부분."""
    lines = ["[그대의 정보]"]
    if age is not None:
        lines.append(f"  • 나이: 약 {age}세")
    if gender:
        lines.append(f"  • 성별: {gender}")
    if hand:
        lines.append(f"  • 보여주신 손: {hand}")
    q = (question or "").strip()
    lines.append(f"  • 화두: {q if q else '(특별한 화두 없이 전체 손금을 봐주십시오)'}")
    lines.append("")
    lines.append(
        "위 손바닥 사진을 보고 옥선 할미의 어조로 손금 풀이를 해주시게나. "
        "손 전체의 첫인상 → 생명선 → 두뇌선·감정선 → 운명선·보조선 → 그대만의 한 가지 → "
        "한 마디 권유 의 흐름으로 자연스럽게 풀어주시게."
    )
    return "\n".join(lines)


def _normalize_image_b64(image_b64: str) -> tuple[str, str]:
    """`data:image/...;base64,...` 또는 raw base64 → (mime, raw_base64)."""
    s = (image_b64 or "").strip()
    if s.startswith("data:") and "," in s:
        header, body = s.split(",", 1)
        mime = "image/jpeg"
        if ";" in header:
            mime_part = header.split(";", 1)[0]
            if mime_part.startswith("data:"):
                mime = mime_part[len("data:") :] or "image/jpeg"
        return mime, body
    return "image/jpeg", s


@lru_cache(maxsize=1)
def _bizrouter_client():
    from openai import OpenAI

    return OpenAI(
        api_key=os.environ.get("BIZROUTER_API_KEY"),
        base_url=os.environ.get(
            "BIZROUTER_BASE_URL", "https://api.bizrouter.ai/v1"
        ),
    )


@lru_cache(maxsize=1)
def _anthropic_client():
    from anthropic import Anthropic

    return Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def _bizrouter_enabled() -> bool:
    return bool((os.environ.get("BIZROUTER_API_KEY") or "").strip())


def _call_vision(
    system_prompt: str,
    user_text: str,
    image_b64: str,
    usage_sink: list[Any] | None = None,
) -> str:
    """비전 LLM 호출 — Bizrouter(Gemini) 우선, Anthropic Claude fallback.

    Args:
        usage_sink: ADR-013. Anthropic 호출의 usage 객체 sink.
            Bizrouter는 OpenAI 형식이라 append 안 함.
    """
    mime, raw_b64 = _normalize_image_b64(image_b64)
    data_url = f"data:{mime};base64,{raw_b64}"

    if _bizrouter_enabled():
        client = _bizrouter_client()
        model = (
            os.environ.get("BIZROUTER_VISION_MODEL")
            or os.environ.get("BIZROUTER_MODEL")
            or "google/gemini-2.5-flash-lite"
        )
        resp = client.chat.completions.create(
            model=model,
            max_tokens=_MAX_TOKENS,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
        )
        if not resp.choices:
            raise ValueError("empty model response")
        content = resp.choices[0].message.content
        if not content:
            raise ValueError("empty model response")
        return content

    # Anthropic fallback
    client = _anthropic_client()
    msg = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=_MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime,
                            "data": raw_b64,
                        },
                    },
                ],
            }
        ],
    )
    text = next(
        (
            getattr(b, "text", None)
            for b in msg.content
            if getattr(b, "type", "") == "text"
        ),
        None,
    )
    if not text:
        raise ValueError("empty model response")
    if usage_sink is not None:
        usage_sink.append(getattr(msg, "usage", None))
    return text


def generate_palm_reading(
    image_b64: str,
    age: int | None = None,
    gender: str | None = None,
    hand: str | None = None,
    question: str | None = None,
) -> dict[str, Any]:
    """옥선 할미 손금 풀이.

    Returns:
        {
            "text": str,
            "cached": bool,
            "crisis_alert": dict | None,
            "legal_notice": str | None,
        }
    """
    # 0. 위기 신호 — 화두 본문 검사
    crisis = detect_crisis(question or "")
    if crisis["crisis_detected"]:
        return {
            "text": CRISIS_RESPONSE_KO + build_legal_footer(is_crisis=True),
            "cached": False,
            "crisis_alert": {
                "severity": crisis["severity"],
                "hotlines": EMERGENCY_HOTLINES_KR,
                "matched_count": len(crisis["matched_keywords"]),
            },
            "legal_notice": None,
            "prompt_cache_usage": None,
        }

    if not (image_b64 or "").strip():
        raise ValueError("image_b64 is required")

    # L1 파일 무결성 — 매직 넘버·크기·MIME 검증 (LLM 호출 전 결정론 가드레일)
    # reports/input-guardrails.md L1 계층. ADR-010 사실성 분리 적용.
    from engine.safety.file_integrity import validate_image_base64
    integrity = validate_image_base64(image_b64)
    if not integrity.valid:
        return {
            "text": integrity.reason + build_legal_footer(is_crisis=False),
            "cached": False,
            "crisis_alert": None,
            "legal_notice": None,
            "file_integrity_error": integrity.error_code,
            "prompt_cache_usage": None,
        }

    # 1. 캐시
    key = _hash_payload(image_b64, age, gender, hand, question)
    cached = _load_cache(key)
    if cached is not None:
        cached.setdefault("crisis_alert", None)
        cached.setdefault("legal_notice", None)
        cached.setdefault("prompt_cache_usage", None)
        return cached

    # 2. LLM 호출 — ADR-013 prompt cache telemetry sink 동반
    user_text = _build_user_text(age, gender, hand, question)
    usage_sink: list[Any] = []
    text = _call_vision(_PALM_SYSTEM, user_text, image_b64, usage_sink=usage_sink)
    legal = build_legal_footer(is_crisis=False)
    full_text = (text or "").strip() + legal

    prompt_cache_usage: dict[str, Any] | None = None
    if usage_sink:
        from engine.safety.prompt_cache_telemetry import extract_usage, summarize
        prompt_cache_usage = summarize(extract_usage(usage_sink[0]))

    out = {
        "text": full_text,
        "cached": False,
        "prompt_cache_usage": prompt_cache_usage,
        "crisis_alert": None,
        "legal_notice": legal,
    }
    _save_cache(key, out)
    return out
