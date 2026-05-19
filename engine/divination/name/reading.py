"""성명학(姓名學) — 묵향 선생(墨香) 페르소나 이름 풀이 에이전트.

흐름:
  1. 입력: 한글 이름 + 한자 (선택) + 성별/생년월일 (선택)
  2. 묵향 선생 시스템 프롬프트로 풀이 생성 (text only — vision 불필요)
  3. 결과 캐시 (입력 조합 hash 24h)
"""

from __future__ import annotations

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


_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "step_archive" / "name_reading_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_TTL_SEC = 24 * 3600
_MAX_TOKENS = 3000


_NAME_SYSTEM = (
    '당신은 "묵향 선생(墨香)"입니다. 조선 사대부 가문 출신의 학자·선비로, '
    "과거에 급제하여 벼슬길에 올랐다가 한 사람의 이름이 가진 운명적 무게를 깨닫고 "
    "모든 관직을 내려놓고 평생을 작명(作名)과 성명학(姓名學)의 길을 걸어온 큰 어른입니다. "
    "월하몽 정자에서 만월 아씨와 자주 학문을 논하며, 옥선 할미와는 같은 어른 동료입니다.\n\n"
    "[페르소나 규칙 — 절대 준수]\n"
    "  • 점잖은 선비의 학자체. 어미: \"~외다\", \"~하오\", \"~이로다\", \"~함이라\".\n"
    "  • 호칭: 사용자를 \"그대\" 또는 \"손님\"이라 부른다.\n"
    "  • 본인을 '묵향' 또는 '이 사람'이라 칭함. AI/모델/시스템 같은 메타 언급 절대 금지.\n"
    "  • 단정적 예언 금지 — \"~될 것이로다\" 같은 단언 X. 대신 \"~한 결이 보이오\", "
    "\"~의 기운이 깃들었구려\" 같은 경향성 표현.\n"
    "  • 점쟁이 자극 어휘 금지 (대박/대운/금전수/재물수 같은 어휘 X).\n"
    "  • 이름의 결을 평가하되, 사람의 가치를 평가하지 말 것. "
    "안 좋은 결이 있어도 \"~허나 …\" 식으로 길을 함께 알려준다.\n"
    "  • 의료·법률·투자 자문 거절, '전문가에게 물어보시오'로 우회.\n\n"
    "[성명학 풀이의 결 — 네 기둥]\n"
    "이름은 네 가지 기둥으로 본다오 — "
    "① 자원오행(字源五行 · 한자의 부수·뜻으로 본 오행), "
    "② 음오행(音五行 · 한글 초성으로 본 오행), "
    "③ 수리오격(數理五格 · 원격·형격·이격·정격·총격의 81수 길흉), "
    "④ 자의(字義 · 글자 본래의 뜻과 어울림). "
    "여기에 사주 일간이 주어지면 '용신(用神)과의 조화'도 함께 살핀다오.\n\n"
    "[작성 형식]\n"
    "  • 첫 문장: \"이 사람이…\" 또는 \"그대의 이름은…\"으로 시작하는 학자의 도입.\n"
    "  • 본문: 다음 네 자리를 자연스러운 흐름으로 풀어낸다 (각 한 단락):\n"
    "    1) 자의(字義) — 글자의 뜻과 짝의 어울림\n"
    "    2) 음오행 — 한글 초성의 흐름과 입에 붙는 결\n"
    "    3) 자원오행 + 사주 보조(있으면) — 오행의 균형\n"
    "    4) 수리오격 — 81수 기준 길흉 (있으면 획수 합산 풀이)\n"
    "  • 마무리 한 줄: \"이 사람의 한 마디 — …\" 또는 \"이름이란 평생의 화두라, …\" 식의 "
    "묵향 선생다운 권유.\n"
    "  • 800~1300자, 마크다운 없이 자연 문장. 학자체 일관 유지.\n\n"
    "[안전·태도]\n"
    "  • 한자가 비어 있으면 한글 음오행만으로 짚어준다 (한자 강요 X).\n"
    "  • 미성년·아기 이름: 부드러운 격려와 자라남의 결 위주로.\n"
    "  • 어떤 경우에도 이름 점수·등급·평가를 매기지 말 것.\n"
    "  • 흉운으로 분류된 한자가 섞여도 단언 금지 — \"이 글자는 어두운 결을 띠나 …\" 식으로."
)


def _hash_payload(
    fullname_ko: str,
    fullname_han: str | None,
    gender: str | None,
    birth: str | None,
    saju_day_master: str | None,
) -> str:
    h = hashlib.sha256()
    h.update((fullname_ko or "").strip().encode("utf-8", errors="ignore"))
    h.update(b"|")
    h.update((fullname_han or "").strip().encode("utf-8", errors="ignore"))
    h.update(b"|")
    h.update((gender or "").encode())
    h.update(b"|")
    h.update((birth or "").encode())
    h.update(b"|")
    h.update((saju_day_master or "").encode())
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
    fullname_ko: str,
    fullname_han: str | None,
    gender: str | None,
    birth: str | None,
    saju_day_master: str | None,
    saju_summary: str | None,
) -> str:
    lines = ["[손님의 이름]"]
    lines.append(f"  • 한글: {fullname_ko}")
    if fullname_han:
        lines.append(f"  • 한자: {fullname_han}")
    if gender:
        lines.append(f"  • 성별: {gender}")
    if birth:
        lines.append(f"  • 생년월일: {birth}")
    if saju_day_master:
        lines.append(f"  • 사주 일간: {saju_day_master}")
    if saju_summary:
        lines.append(f"  • 사주 요약: {saju_summary[:300]}")
    lines.append("")
    lines.append(
        "위 이름을 묵향 선생의 어조로 성명학 풀이를 해주시오. "
        "자의 → 음오행 → 자원오행/사주 보조 → 수리오격 → 한 마디 권유 의 "
        "흐름으로 자연스럽게 풀어주시오."
    )
    return "\n".join(lines)


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


def _call_llm(
    system_prompt: str,
    user_text: str,
    usage_sink: list[Any] | None = None,
) -> str:
    """텍스트 전용 LLM 호출 — Bizrouter 우선, Anthropic fallback."""
    if _bizrouter_enabled():
        client = _bizrouter_client()
        model = (
            os.environ.get("BIZROUTER_MODEL")
            or "google/gemini-2.5-flash-lite"
        )
        resp = client.chat.completions.create(
            model=model,
            max_tokens=_MAX_TOKENS,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
        )
        if not resp.choices:
            raise ValueError("empty model response")
        content = resp.choices[0].message.content
        if not content:
            raise ValueError("empty model response")
        return content

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
        messages=[{"role": "user", "content": user_text}],
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


def generate_name_reading(
    fullname_ko: str,
    fullname_han: str | None = None,
    gender: str | None = None,
    birth: str | None = None,
    saju_day_master: str | None = None,
    saju_summary: str | None = None,
) -> dict[str, Any]:
    """묵향 선생 성명학 풀이.

    Returns:
        {
            "text": str,
            "cached": bool,
            "crisis_alert": dict | None,
            "legal_notice": str | None,
        }
    """
    if not (fullname_ko or "").strip():
        raise ValueError("fullname_ko is required")

    # 위기 신호는 이름 입력엔 거의 없겠지만 안전망
    full_text_for_crisis = " ".join(
        x for x in [fullname_ko, saju_summary] if x
    )
    crisis = detect_crisis(full_text_for_crisis)
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

    key = _hash_payload(fullname_ko, fullname_han, gender, birth, saju_day_master)
    cached = _load_cache(key)
    if cached is not None:
        cached.setdefault("crisis_alert", None)
        cached.setdefault("legal_notice", None)
        cached.setdefault("prompt_cache_usage", None)
        return cached

    user_text = _build_user_text(
        fullname_ko, fullname_han, gender, birth, saju_day_master, saju_summary
    )
    # ADR-013 prompt cache telemetry sink 동반
    usage_sink: list[Any] = []
    text = _call_llm(_NAME_SYSTEM, user_text, usage_sink=usage_sink)
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
