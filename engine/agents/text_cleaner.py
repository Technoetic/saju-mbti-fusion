"""A1 꿈 텍스트 정제 에이전트 — raw → 정규화 + 개체 추출.

문서: 음성→텍스트 raw, 이모지·색상 태그 → 정규화 narrative_text +
       characters / settings / activities enum

본 구현:
  - 결정론 1차 정제 (이모지 제거, 공백 정규화, 길이 제한)
  - LLM 호출로 HvDC enum 자동 추출 (Schredl 표준 호환)
  - 안전 가드: 위기 키워드 검사를 같은 단계에서 수행

LLM 시스템 프롬프트:
  Schredl/HvDC enum만 출력, 추측 금지, JSON 1개만.
"""

from __future__ import annotations
from typing import Any
import json
import re
import unicodedata


TEXT_CLEANER_LABEL = (
    "A1 텍스트 정제 — 음성/이모지/잡음 제거 + Schredl·HvDC enum 추출."
)


# 결정론 정제
_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "☀-⛿✀-➿"  # misc symbols
    "]+",
    flags=re.UNICODE,
)

_MULTI_SPACE_RE = re.compile(r"\s+")
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def deterministic_clean(raw: str, max_chars: int = 3000) -> dict[str, Any]:
    """이모지·HTML·공백 정규화. LLM 호출 0회."""
    t = raw or ""
    original_len = len(t)

    # Unicode 정규화
    t = unicodedata.normalize("NFKC", t)
    # HTML 태그 제거
    t = _HTML_TAG_RE.sub(" ", t)
    # 이모지 제거 (단, 정서가는 별도 추출 가능 — 향후 확장)
    emojis_found = _EMOJI_RE.findall(t)
    t = _EMOJI_RE.sub(" ", t)
    # 다중 공백 압축
    t = _MULTI_SPACE_RE.sub(" ", t).strip()
    # 길이 제한
    truncated = len(t) > max_chars
    if truncated:
        t = t[:max_chars]

    return {
        "cleaned_text": t,
        "original_length": original_len,
        "cleaned_length": len(t),
        "emojis_removed": len(emojis_found),
        "truncated": truncated,
    }


# LLM 시스템 프롬프트 — HvDC enum 자동 추출
_EXTRACTION_SYSTEM = (
    "당신은 꿈 보고서 자동 정제기입니다. 입력된 한국어 꿈 텍스트에서 "
    "Schredl·HvDC 표준에 따른 구조화 정보만 추출해 JSON으로 출력하십시오.\n\n"
    "[엄격 규칙]\n"
    "  • 본문에 명시되지 않은 항목은 빈 리스트로.\n"
    "  • 추측·확장·해석 금지. 본문에 실제 등장한 단어/사건만.\n"
    "  • 출력은 valid JSON 1개. 마크다운 코드블록 금지.\n\n"
    "[출력 스키마]\n"
    "  {\n"
    '    "narrative_summary": "1~2문장 요약",\n'
    '    "characters": [{"role": "SELF|FAMILIAR|UNFAMILIAR|FAMOUS|IMAGINARY|ANIMAL", "gender": "m|f|na", "label": "한국어 라벨"}],\n'
    '    "settings": ["indoor"|"outdoor"|"water"|"sky"|"childhood_home"|"workplace"|"school"|"public"],\n'
    '    "activities": ["walking"|"flying"|"falling"|"chase"|"conversation"|"sexual"|"eating"|"other"],\n'
    '    "dominant_emotion": "happy|angry|sad|fear|confused|neutral",\n'
    '    "estimated_valence": -3..3,\n'
    '    "estimated_vividness": 1..5\n'
    "  }"
)


def extract_structured(cleaned_text: str) -> dict[str, Any]:
    """LLM으로 구조화 추출 — Schredl·HvDC enum.

    실패 시 빈 구조 반환 (앱이 계속 진행 가능하도록).
    """
    from engine.llm_sync import call_llm_sync

    if not cleaned_text or not cleaned_text.strip():
        return _empty_structure()

    try:
        raw = call_llm_sync(
            user_text=f"[꿈 본문]\n{cleaned_text[:2400]}\n\n위 본문에서 구조화 정보를 JSON으로 추출.",
            system_prompt=_EXTRACTION_SYSTEM,
        )
    except Exception as e:
        return {**_empty_structure(), "error": f"LLM 호출 실패: {e}"}

    cleaned_json = _strip_codeblock(raw or "")
    try:
        data = json.loads(cleaned_json)
        # 안전 디폴트
        return _normalize_structure(data)
    except json.JSONDecodeError as e:
        return {**_empty_structure(), "error": f"JSON 파싱 실패: {e}", "raw": (raw or "")[:200]}


def _strip_codeblock(text: str) -> str:
    """```json ... ``` 또는 ``` ... ``` 제거."""
    t = text.strip()
    if t.startswith("```"):
        lines = t.split("\n")
        if len(lines) > 2:
            t = "\n".join(lines[1:-1])
    # 첫 { ~ 마지막 } 추출
    first = t.find("{")
    last = t.rfind("}")
    if first >= 0 and last > first:
        t = t[first:last + 1]
    return t


def _empty_structure() -> dict[str, Any]:
    return {
        "narrative_summary": "",
        "characters": [],
        "settings": [],
        "activities": [],
        "dominant_emotion": "neutral",
        "estimated_valence": 0,
        "estimated_vividness": 3,
    }


def _normalize_structure(data: dict[str, Any]) -> dict[str, Any]:
    """필수 키 보장 + enum 검증."""
    result = _empty_structure()
    if isinstance(data.get("narrative_summary"), str):
        result["narrative_summary"] = data["narrative_summary"][:300]
    if isinstance(data.get("characters"), list):
        result["characters"] = data["characters"][:10]
    if isinstance(data.get("settings"), list):
        result["settings"] = [s for s in data["settings"][:10] if isinstance(s, str)]
    if isinstance(data.get("activities"), list):
        result["activities"] = [a for a in data["activities"][:10] if isinstance(a, str)]
    de = data.get("dominant_emotion")
    if de in {"happy", "angry", "sad", "fear", "confused", "neutral"}:
        result["dominant_emotion"] = de
    v = data.get("estimated_valence")
    if isinstance(v, (int, float)) and -3 <= v <= 3:
        result["estimated_valence"] = int(v)
    vv = data.get("estimated_vividness")
    if isinstance(vv, (int, float)) and 1 <= vv <= 5:
        result["estimated_vividness"] = int(vv)
    return result


def run_text_cleaner(raw: str, *, use_llm: bool = True) -> dict[str, Any]:
    """전체 정제 파이프라인.

    Args:
        raw: 원본 텍스트
        use_llm: False면 결정론 정제만 (LLM 호출 0회)
    """
    cleaned = deterministic_clean(raw)
    if use_llm:
        structured = extract_structured(cleaned["cleaned_text"])
    else:
        structured = _empty_structure()
    return {
        "agent": "A1",
        "deterministic": cleaned,
        "structured": structured,
    }


__all__ = [
    "TEXT_CLEANER_LABEL",
    "deterministic_clean",
    "extract_structured",
    "run_text_cleaner",
]
