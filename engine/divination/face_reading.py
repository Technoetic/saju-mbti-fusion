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
    "구름과 학을 벗삼아 산중에서 수십 년간 사람의 얼굴 형상을 살펴온 노도사입니다.\n\n"
    "[근본 원칙 — ADR-010 사실성 분리 절대 준수]\n"
    "당신의 역할은 사진에서 보이는 **객관적 시각 형태만 묘사**하는 것입니다. "
    "운명·성격·길흉·미래를 해석하지 않습니다. 보이는 그대로의 형태·색상·균형·강도만 "
    "사극풍 어조로 풀어 전합니다. 학파 통설의 운명 매핑(예: '이마가 넓으니 학문복', "
    "'콧방울 두툼하니 재물복')은 절대 사용 금지 — 이것이 본 시스템의 사실성 원칙입니다.\n\n"
    "[페르소나 어조]\n"
    "  • 친근한 어른의 반말체와 존중체의 중간 톤. 어미: \"~시게\", \"~하시게나\", \"~인고\", "
    "\"~이로구먼\", \"~이로세\". 사용자를 \"그대\" 또는 \"자네\"라 부른다.\n"
    "  • 습관어: \"허허\", \"이 늙은이가\", \"자, 보시게\".\n"
    "  • 본인을 '운학 도사' 또는 '이 늙은이'라 칭함. AI/모델/시스템 메타 언급 절대 금지.\n\n"
    "[허용 — 시각 객관 묘사만]\n"
    "사진에서 직접 보이는 형태·색상·비율·균형만 묘사:\n"
    "  • 얼굴 윤곽: 둥근·각진·긴·짧은·균형 잡힌 등\n"
    "  • 이마: 넓은·좁은·둥근·평평한·솟은 등\n"
    "  • 눈썹: 짙은·옅은·긴·짧은·곧은·휜 등\n"
    "  • 눈: 큰·작은·또렷한·차분한·맑은 (눈빛 강도)\n"
    "  • 코: 곧은·휜·콧대 높은·콧방울 두툼한 등 (형태만)\n"
    "  • 입: 두툼한·얇은·입꼬리 올라간/내려간 등\n"
    "  • 턱: 각진·둥근·뾰족한·살 있는 등\n"
    "  • 기색: 맑은·붉은·창백한·노란기 도는 (색상만)\n"
    "  • 좌우 대칭·전체 균형\n"
    "결정론 점수가 제공되면 묘사의 정량 근거로 인용: \"비율 0.81로 넓고 평평한 결\".\n\n"
    "[엄격 금지 — 운명·해석 매핑]\n"
    "다음 표현 절대 사용 금지:\n"
    "  • 시간 차원 해석: \"초년/중년/말년 복록·운\", \"학문복\", \"재물복\", \"인덕\"\n"
    "  • 12궁 운명 매핑: \"관록궁이 또렷하니 직장운\", \"재백궁이 좋으니 재물\"\n"
    "  • 5형 운명 매핑: \"토형이라 신용이 두텁다\", \"화형이라 성격 급하다\"\n"
    "  • 점쟁이 어휘: 대박·대운·금전수·재물수·길흉화복·운명\n"
    "  • 단정 예언: \"~될 것이로세\", \"~의 운이 있다\"\n"
    "  • 학파 직접 인용: \"마의상법에 이르길\", \"신상전편에 따르면\"\n"
    "  • 외모 평가·미추 비교, 인종·민족 일반화\n"
    "  • 의료·법률·투자 자문 — '의원·전문가에게 물으시게'로 우회\n\n"
    "[명칭 사용 — 영역명만, 운명 매핑 X]\n"
    "  • 삼정(상정·중정·하정) 명칭: 얼굴 영역 명칭으로만 사용 가능. "
    "단 \"상정 = 이마 영역의 형태\" 객관 묘사에 한정. \"상정이 초년운\" 같은 매핑 X.\n"
    "  • 12궁 명칭(명궁·관록궁·재백궁 등): 영역 명칭으로만 사용 가능. "
    "\"명궁이 또렷하다\" (영역 묘사) ✓ / \"명궁이 또렷하니 평생운 밝다\" (운명 매핑) ✗\n"
    "  • 5형 명칭(목·화·토·금·수): face_shape 결정론 결과 인용 가능. "
    "\"토형의 결로구먼 — 가로세로 비율이 균형 잡힌 모양\" (형태 묘사) ✓ / "
    "\"토형이라 신용 두텁다\" (성격 매핑) ✗\n\n"
    "[결정론 점수 활용 — ADR-004·022 정합]\n"
    "유저 메시지에 [얼굴 구조 분류] / [십이궁·삼정·오관 결정론 점수] 가 포함되면:\n"
    "  • 비율·대칭·구조의 정량 측정 결과로 묘사의 근거로 인용\n"
    "  • 점수 높음 = 표준 비율에 부합, 점수 낮음 = 표준에서 벗어남 — 결코 부정 표현 X, "
    "그대만의 개성·결로 묘사 (운명 해석은 여전히 금지)\n"
    "  • 결정론 점수와 시각 인상이 충돌하면 둘 다 명시: "
    "\"비율은 0.7로 측정되되, 기색은 맑은 결이로다\"\n\n"
    "[작성 형식]\n"
    "  • 첫 문장: \"허허\"로 시작하는 인사 한 마디.\n"
    "  • 본문: 다음 다섯 자리를 자연스러운 흐름으로 풀어낸다 (각 한 단락, 시각 묘사만):\n"
    "    1) 전체 인상 — 얼굴 형태·균형·기색의 첫인상 (운명 X)\n"
    "    2) 이마(상정 영역) — 형태·넓이·평평함·주름의 결 (시간 운 X)\n"
    "    3) 눈썹·눈·코(중정 영역) — 형태·색상·눈빛 강도 (성격 X)\n"
    "    4) 입·턱(하정 영역) — 형태·두께·각도 (복록 X)\n"
    "    5) 그대만의 한 가지 — 가장 또렷한 시각 특징 하나 (운명 X)\n"
    "  • 마무리 한 줄: \"이 늙은이의 한 마디 — …\" 형식으로 사진 촬영 환경·면책 안내. "
    "운명 권유 X.\n"
    "  • 800~1300자, 마크다운 없이 자연 문장. 사극풍 어조 일관 유지.\n\n"
    "[안전·태도]\n"
    "  • 사진이 너무 흐리거나, 얼굴이 보이지 않거나, 사람의 얼굴이 아닌 경우: "
    "\"허허, 이 늙은이의 눈에는 그대의 상이 잘 잡히지 않는구먼. 빛 좋은 곳에서 "
    "정면으로 한 번 더 담아 보시게나.\" 라고 한 줄로 답하고 끝낸다. 억지로 묘사하지 말 것.\n"
    "  • 미성년으로 보이는 경우: 어른스러운 격려와 객관 묘사만, 짧게.\n"
    "  • 어떤 경우에도 외모 점수·등급·평가를 매기지 말 것.\n"
    "  • 사용자가 \"제 운은요?\"·\"미래는?\"·\"길흉 알려주세요\" 같이 운명 해석을 요청해도: "
    "\"허허, 이 늙은이는 그대의 얼굴 형상을 비추어 드릴 뿐, 운명의 길흉은 헤아리지 않는다네\" "
    "한 줄로 답하고 객관 묘사로 돌아간다."
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


def _build_user_text(
    age: int | None,
    gender: str | None,
    question: str | None,
    palace_scores: dict[str, Any] | None = None,
    face_shape: dict[str, Any] | None = None,
) -> str:
    """이미지와 함께 보낼 텍스트 부분 — 사진 + 결정론 점수 4중 신호 통합.

    Args:
        palace_scores: face_scoring report_to_dict() — 12궁·삼정·오관 결정론 점수
        face_shape: face_shape FaceShapeResult asdict — 오행 5형 분류
    """
    lines = ["[그대의 정보]"]
    if age is not None:
        lines.append(f"  • 나이: 약 {age}세")
    if gender:
        lines.append(f"  • 성별: {gender}")
    q = (question or "").strip()
    lines.append(f"  • 화두: {q if q else '(특별한 화두 없이 전체 상을 봐주십시오)'}")

    # 결정론 점수 — 5형 (얼굴 구조 본바탕, ADR-022)
    if face_shape and face_shape.get("shape_type"):
        lines.append("")
        lines.append("[얼굴 구조 분류 — MediaPipe 키포인트 기반 결정론, ADR-022]")
        lines.append(f"  • 오행 5형: {face_shape['shape_type']} ({face_shape.get('morphological_name', '')})")
        criteria = face_shape.get("matched_criteria") or []
        if criteria:
            lines.append(f"  • 통과 임계값: {', '.join(str(c) for c in criteria[:3])}")

    # 결정론 점수 — 12궁·삼정·오관 (ADR-004)
    if palace_scores:
        lines.append("")
        lines.append("[십이궁·삼정·오관 결정론 점수 — MediaPipe 478 키포인트 비율·대칭, ADR-004]")
        samjeong = palace_scores.get("samjeong") or {}
        if samjeong:
            sj_line = ", ".join(
                f"{v.get('label_ko', k)} {v.get('score', 0):.2f}"
                for k, v in list(samjeong.items())[:3]
            )
            lines.append(f"  • 삼정: {sj_line}")
        ogwan = palace_scores.get("ogwan") or {}
        if ogwan:
            og_line = ", ".join(
                f"{v.get('label_ko', k)} {v.get('score', 0):.2f}"
                for k, v in list(ogwan.items())[:5]
            )
            lines.append(f"  • 오관: {og_line}")
        top = palace_scores.get("top_palace")
        weak = palace_scores.get("weakest_palace")
        if top:
            lines.append(f"  • 가장 또렷한 자리: {top}")
        if weak:
            lines.append(f"  • 가장 옅은 자리: {weak} (※ 부정 표현 X, 개성으로 해석)")
        shen = palace_scores.get("shen_score")
        qi = palace_scores.get("qi_score")
        if shen is not None or qi is not None:
            lines.append(f"  • 신(神)·기(氣) 정량: 신 {shen or 0:.2f}, 기 {qi or 0:.2f}")

    lines.append("")
    lines.append(
        "위 사진과 결정론 점수를 함께 참조하여 운학 도사의 어조로 **시각 객관 묘사**를 해주시게. "
        "운명·길흉·시간 흐름 해석은 절대 금지 — 보이는 형태·색상·균형만 사극풍 어조로 풀어 전한다. "
        "결정론 점수는 비율·대칭·구조의 측정 근거로 인용. "
        "전체 인상 → 이마(상정 영역) 형태 → 눈썹·눈·코(중정 영역) 형태 → 입·턱(하정 영역) 형태 → "
        "그대만의 또렷한 시각 특징 한 가지 → 마무리 한 마디(촬영 환경·면책 안내) "
        "흐름으로 객관 묘사하시게."
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
    """비전 LLM 호출 — Bizrouter(claude-opus-4.7) 우선, Anthropic SDK 자동 fallback.

    BIZROUTER_VISION_MODEL이 timeout·5xx·권한 부재 등으로 실패하면 즉시
    Anthropic SDK 직접 호출(claude-opus-4-7)로 fallback. 사용자 의도와
    실제 가용성 사이의 갭을 코드 수준에서 회복.

    Args:
        usage_sink: 옵션. 빈 리스트 전달 시 Anthropic SDK 호출의 usage
            객체를 append. Bizrouter 경로는 OpenAI 형식이라 append 안 함.
            ADR-013 prompt cache telemetry 통합.
    """
    mime, raw_b64 = _normalize_image_b64(image_b64)
    data_url = f"data:{mime};base64,{raw_b64}"

    if _bizrouter_enabled():
        model = (
            os.environ.get("BIZROUTER_VISION_MODEL")
            or os.environ.get("BIZROUTER_MODEL")
            or "anthropic/claude-opus-4.7"
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
    if usage_sink is not None:
        usage_sink.append(getattr(msg, "usage", None))
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
            "palace_scores": None,
            "file_integrity_error": integrity.error_code,
            "prompt_cache_usage": None,
        }

    # 키포인트 → 12궁·5형 결정론 점수 (LLM 호출 전, 캐시와 무관하게 항상 산출)
    # ADR-004 (face_scoring) + ADR-022 (face_shape) 정합. 4중 신호 통합 풀이.
    from engine.divination.face_scoring import score_face, report_to_dict
    score_report = score_face(metrics)
    palace_scores = report_to_dict(score_report)

    face_shape_dict: dict[str, Any] | None = None
    if metrics:
        try:
            from dataclasses import asdict
            from engine.divination.face_shape import classify_face_shape
            shape_result = classify_face_shape(metrics)
            face_shape_dict = asdict(shape_result)
        except Exception:
            face_shape_dict = None

    # 1. 캐시 — 같은 이미지+보조정보 24h 재사용 (메트릭은 캐시 키에 미포함, 결정론은 항상 재산출)
    key = _hash_payload(image_b64, age, gender, question)
    cached = _load_cache(key)
    if cached is not None:
        cached.setdefault("crisis_alert", None)
        cached.setdefault("legal_notice", None)
        cached.setdefault("prompt_cache_usage", None)
        cached["text"] = cached.get("text", "") + ""
        # palace_scores·face_shape는 결정론이므로 항상 최신 재산출 (캐시 본문 그대로 + 점수만 갱신)
        cached["palace_scores"] = palace_scores
        cached["face_shape"] = face_shape_dict
        return cached

    # 2. LLM 호출 — ADR-013 prompt cache telemetry sink 동반
    # 4중 신호: 사진 + age/gender/question + palace_scores + face_shape
    user_text = _build_user_text(
        age, gender, question,
        palace_scores=palace_scores,
        face_shape=face_shape_dict,
    )
    usage_sink: list[Any] = []
    text = _call_vision(_FACE_SYSTEM, user_text, image_b64, usage_sink=usage_sink)
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
        "palace_scores": palace_scores,
        "face_shape": face_shape_dict,
    }
    _save_cache(key, out)
    return out
