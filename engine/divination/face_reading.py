"""관상(觀相) — 운학 도사 페르소나 얼굴 풀이 에이전트.

흐름:
  1. 입력: 사용자 얼굴 사진(base64) + 보조 정보(나이/성별/질문)
  2. 운학 도사 시스템 프롬프트 + 멀티모달 메시지로 Gemini Vision 호출
  3. 결과 캐시 (이미지 hash + 보조정보 24h)

비전 입력은 OpenAI 호환 messages 의 content 배열을 사용한다.
Bizrouter(Gemini) 가 우선이며, 키 없으면 Anthropic Claude fallback.
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


_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "step_archive" / "face_reading_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_TTL_SEC = 24 * 3600
_MAX_TOKENS = 3000


_FACE_SYSTEM = (
    '당신은 "운학 도사(雲鶴道士)"입니다. 60대 후반에서 70대 초반의 한국 사극 속 인물로, '
    "구름과 학을 벗삼아 산중에서 수십 년간 관상학(觀相學)을 닦아온 노도사입니다.\n\n"
    "[페르소나 규칙 — 절대 준수]\n"
    "  • 친근한 어른의 반말체와 존중체의 중간 톤. 어미: \"~시게\", \"~하시게나\", \"~인고\", "
    "\"~이로구먼\", \"~이로세\". 사용자를 \"그대\" 또는 \"자네\"라 부른다.\n"
    "  • 습관어: \"허허\", \"이 늙은이가\", \"자, 보시게\".\n"
    "  • 본인을 '운학 도사' 또는 '이 늙은이'라 칭함. AI/모델/시스템 같은 메타 언급 절대 금지.\n"
    "  • 단정적 예언 금지 — \"~될 것이로세\" 같은 단언 X. 대신 \"~한 결이 보이는구먼\", "
    "\"~의 기운이 흐르는 듯하이\" 같은 경향성 표현.\n"
    "  • 점쟁이 자극 어휘 금지 (대박/대운/금전수/재물수 같은 어휘 X).\n"
    "  • 외모 평가·미추 비교 금지 — 관상은 '상(相)'을 보는 것이지 미추를 따지는 것이 아님.\n"
    "  • 의료·법률·투자 자문 거절, '의원·전문가에게 물으시게'로 우회.\n"
    "  • 인종·민족 특질 일반화 금지. 그대 한 사람의 상에만 집중.\n\n"
    "[관상 풀이의 결]\n"
    "관상은 얼굴을 셋으로 나누어 본다네 — 상정(上停 · 이마, 초년·지혜), "
    "중정(中停 · 눈썹부터 코끝, 중년·기개), 하정(下停 · 인중부터 턱, 말년·복록). "
    "또한 오관(五官 · 눈썹·눈·귀·코·입)과 십이궁(十二宮)을 살피지. "
    "기색(氣色)과 신(神 · 눈빛) 도 빼놓을 수 없네.\n\n"
    "[작성 형식]\n"
    "  • 첫 문장: \"허허\"로 시작하는 인사 한 마디.\n"
    "  • 본문: 다음 다섯 자리를 자연스러운 흐름으로 풀어낸다 (각 한 단락):\n"
    "    1) 전체 인상과 기색 — 첫눈에 보이는 상의 결\n"
    "    2) 상정(이마) — 초년의 지혜와 학문의 자리\n"
    "    3) 중정(눈썹·눈·코) — 중년의 기개와 의지\n"
    "    4) 하정(입·턱) — 말년의 복록과 인덕\n"
    "    5) 그대만의 한 가지 — 가장 또렷한 특징 하나를 짚어 격려\n"
    "  • 마무리 한 줄: \"이 늙은이의 한 마디 — …\" 형식으로 그대에게 권하는 한 걸음.\n"
    "  • 800~1300자, 마크다운 없이 자연 문장. 사극풍 어조 일관 유지.\n\n"
    "[안전·태도]\n"
    "  • 사진이 너무 흐리거나, 얼굴이 보이지 않거나, 사람의 얼굴이 아닌 경우: "
    "\"허허, 이 늙은이의 눈에는 그대의 상이 잘 잡히지 않는구먼. 빛 좋은 곳에서 "
    "정면으로 한 번 더 담아 보시게나.\" 라고 한 줄로 답하고 끝낸다. 억지로 풀이하지 말 것.\n"
    "  • 미성년으로 보이는 경우: 어른스러운 격려와 학문의 자리(상정) 위주로 짧게.\n"
    "  • 어떤 경우에도 외모 점수·등급·평가를 매기지 말 것."
)


def _hash_payload(image_b64: str, age: int | None, gender: str | None, question: str | None) -> str:
    """캐시 키 — 이미지 본문 + 보조 정보."""
    h = hashlib.sha256()
    h.update(image_b64.encode("utf-8", errors="ignore"))
    h.update(b"|")
    h.update(str(age or "").encode())
    h.update(b"|")
    h.update((gender or "").encode())
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


def _build_user_text(age: int | None, gender: str | None, question: str | None) -> str:
    """이미지와 함께 보낼 텍스트 부분."""
    lines = ["[그대의 정보]"]
    if age is not None:
        lines.append(f"  • 나이: 약 {age}세")
    if gender:
        lines.append(f"  • 성별: {gender}")
    q = (question or "").strip()
    lines.append(f"  • 화두: {q if q else '(특별한 화두 없이 전체 상을 봐주십시오)'}")
    lines.append("")
    lines.append(
        "위 사진을 보고 운학 도사의 어조로 관상 풀이를 해주시게나. "
        "전체 인상 → 상정(이마) → 중정(눈·코) → 하정(입·턱) → 그대만의 한 가지 → 한 마디 권유 의 "
        "흐름으로 자연스럽게 풀어주시게."
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


def _call_vision(system_prompt: str, user_text: str, image_b64: str) -> str:
    """비전 LLM 호출 — Bizrouter(claude-opus-4.7) 우선, Anthropic SDK 자동 fallback.

    BIZROUTER_VISION_MODEL이 timeout·5xx·권한 부재 등으로 실패하면 즉시
    Anthropic SDK 직접 호출(claude-opus-4-7)로 fallback. 사용자 의도와
    실제 가용성 사이의 갭을 코드 수준에서 회복.
    """
    mime, raw_b64 = _normalize_image_b64(image_b64)
    data_url = f"data:{mime};base64,{raw_b64}"

    if _bizrouter_enabled():
        model = (
            os.environ.get("BIZROUTER_VISION_MODEL")
            or os.environ.get("BIZROUTER_MODEL")
            or "google/gemini-2.5-flash-lite"
        )
        try:
            client = _bizrouter_client()
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
        except Exception:
            # Bizrouter 실패 → Anthropic SDK 직접 fallback (claude-opus-4-7)
            pass

    # Anthropic SDK 직접 호출
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
    return text


def generate_face_reading(
    image_b64: str,
    age: int | None = None,
    gender: str | None = None,
    question: str | None = None,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """운학 도사 관상 풀이.

    Args:
        image_b64: 사용자 얼굴 사진 (data URL 또는 raw base64).
        age, gender, question: 보조 정보.
        metrics: 클라이언트(MediaPipe Face Landmarker)에서 산출한 정량 메트릭.
            face_scoring으로 12궁 정량 점수 산출에 사용.

    Returns:
        {
            "text": str,
            "cached": bool,
            "crisis_alert": dict | None,
            "legal_notice": str | None,
            "palace_scores": dict | None,  # 키포인트 기반 결정론 12궁 점수
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
            "palace_scores": None,
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
            "palace_scores": None,
            "file_integrity_error": integrity.error_code,
        }

    # 키포인트 → 12궁 결정론 점수 (LLM 호출 전, 캐시와 무관하게 항상 산출)
    from engine.divination.face_scoring import score_face, report_to_dict
    score_report = score_face(metrics)
    palace_scores = report_to_dict(score_report)

    # 1. 캐시 — 같은 이미지+보조정보 24h 재사용 (메트릭은 캐시 키에 미포함, palace_scores만 재산출)
    key = _hash_payload(image_b64, age, gender, question)
    cached = _load_cache(key)
    if cached is not None:
        cached.setdefault("crisis_alert", None)
        cached.setdefault("legal_notice", None)
        cached["text"] = cached.get("text", "") + ""
        # palace_scores는 결정론이므로 항상 최신 재산출 (캐시 본문 그대로 + 점수만 갱신)
        cached["palace_scores"] = palace_scores
        return cached

    # 2. LLM 호출
    user_text = _build_user_text(age, gender, question)
    text = _call_vision(_FACE_SYSTEM, user_text, image_b64)
    legal = build_legal_footer(is_crisis=False)
    full_text = (text or "").strip() + legal

    out = {
        "text": full_text,
        "cached": False,
        "crisis_alert": None,
        "legal_notice": legal,
        "palace_scores": palace_scores,
    }
    _save_cache(key, out)
    return out
