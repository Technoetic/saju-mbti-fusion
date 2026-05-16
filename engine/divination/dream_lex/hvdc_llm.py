"""LLM 자동 HVdC 코딩 — Bertolini 2024 한국어 적용.

출처:
  - Bertolini et al. (2024) "Automatic Scoring of Dream Reports' Emotional
    Content with LLMs", arXiv:2402.14223
  - Fox et al. (2013) — 인간 코더 κ 합의 베이스라인

핵심:
  - LLM이 HVdC 10 카테고리 + 5 정서를 자동 분류
  - 영문 표본에서 인간 코더와 κ 0.6~0.8 달성
  - 본 모듈은 Bizrouter(Gemini)로 한국어 자동 코딩

결정론 코더(hallvandecastle.py)는 키워드 매칭 위주 → recall 한계.
LLM 코더는 의미 기반 → 결정론 코더로 잡지 못한 사례 보완.
"""

from __future__ import annotations
from typing import Any
import json


HVDC_LLM_LABEL = (
    "LLM 자동 HVdC 코딩 — Bertolini 2024 영문 κ 0.6~0.8을 한국어 Gemini로 재현. "
    "결정론 코더의 보완 — 의미 기반 추출."
)


HVDC_LLM_SYSTEM = (
    "당신은 Hall-Van de Castle 꿈 코딩 시스템의 자동 코더입니다.\n\n"
    "입력으로 한국어 꿈 보고서가 주어지면, 다음 10 카테고리로 분류해 "
    "JSON으로만 출력하십시오. 설명·머리말·꼬리말 일절 금지.\n\n"
    "[10 카테고리 + enum]\n"
    "  1. characters: 등장인물 리스트 (각 {role, gender, familiarity})\n"
    "     role enum: SELF / FAMILIAR / UNFAMILIAR / FAMOUS / IMAGINARY / ANIMAL\n"
    "     gender enum: m / f / na\n"
    "     familiarity: 0.0~1.0\n"
    "  2. social_interactions: {friendly: [str], aggressive: [str], sexual: [str]}\n"
    "  3. activities: {physical: [str], movement: [str], cognitive: [str]}\n"
    "  4. success_failure: {success: [str], failure: [str]}\n"
    "  5. fortune_misfortune: {fortune: [str], misfortune: [str]}\n"
    "  6. emotions: {anger: int, apprehension: int, happiness: int, sadness: int, confusion: int}\n"
    "     (각 정서가 등장한 횟수 카운트)\n"
    "  7. settings: {home: [], work: [], school: [], outdoor: [], public: [], other: []}\n"
    "  8. objects: [str]\n"
    "  9. descriptive: {color: [str], size: [str]}\n"
    "  10. food_eating: [str]\n\n"
    "[엄격 규칙]\n"
    "  • 본문에 명시되지 않은 항목은 빈 리스트/0\n"
    "  • 추측·확장 금지 — 본문에 실제로 등장한 단어/사건만\n"
    "  • 출력은 반드시 valid JSON 1개\n"
    "  • 마크다운 코드 블록 사용 금지 (```json 금지)"
)


def code_dream_with_llm(text: str) -> dict[str, Any]:
    """LLM으로 한국어 꿈을 HVdC 자동 코딩.

    Returns:
        {
            "coding": dict (10 카테고리),
            "method": "llm" | "fallback",
            "raw_response": str,
            "parse_success": bool,
        }
    """
    from engine.llm_sync import call_llm_sync

    if not text or not text.strip():
        return {
            "coding": _empty_coding(),
            "method": "fallback",
            "raw_response": "",
            "parse_success": False,
        }

    try:
        raw = call_llm_sync(
            user_text=f"[꿈 보고서]\n{text.strip()[:2400]}\n\n위 보고서를 HVdC JSON으로 코딩.",
            system_prompt=HVDC_LLM_SYSTEM,
        )
    except Exception as e:
        return {
            "coding": _empty_coding(),
            "method": "fallback",
            "raw_response": f"(LLM 호출 실패: {e})",
            "parse_success": False,
        }

    # JSON 파싱 — 코드블록·전후 잡음 제거
    cleaned = (raw or "").strip()
    # ```json ... ``` 제거
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # 첫 줄·마지막 줄 제거
        cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned

    # 첫 { 부터 마지막 } 까지 추출
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace >= 0 and last_brace > first_brace:
        cleaned = cleaned[first_brace : last_brace + 1]

    try:
        coding = json.loads(cleaned)
        return {
            "coding": coding,
            "method": "llm",
            "raw_response": raw[:500] if raw else "",
            "parse_success": True,
        }
    except json.JSONDecodeError as e:
        return {
            "coding": _empty_coding(),
            "method": "fallback",
            "raw_response": f"(파싱 실패: {e}; 원문: {raw[:200]})",
            "parse_success": False,
        }


def merge_deterministic_and_llm(
    deterministic_coding: dict[str, Any],
    llm_coding: dict[str, Any],
) -> dict[str, Any]:
    """결정론 코더 + LLM 코더 결과 병합 — recall 향상.

    원칙: union (둘 중 하나라도 잡으면 포함). 중복 제거.
    """
    merged: dict[str, Any] = {}

    # 리스트형 필드
    for key in ["characters", "objects", "food_eating"]:
        det_list = deterministic_coding.get(key) or []
        llm_list = llm_coding.get(key) or []
        if isinstance(det_list, list) and isinstance(llm_list, list):
            # characters는 dict 리스트라 단순 union 어려움 → 키워드 기준
            if key == "characters":
                # dict가 아니면 str 처리
                merged_items = []
                seen = set()
                for item in det_list + llm_list:
                    k = item if isinstance(item, str) else json.dumps(item, ensure_ascii=False, sort_keys=True)
                    if k not in seen:
                        seen.add(k)
                        merged_items.append(item)
                merged[key] = merged_items
            else:
                merged[key] = list(dict.fromkeys(det_list + llm_list))
        else:
            merged[key] = det_list or llm_list

    # 중첩 dict 필드 (각 하위 키도 union)
    for key in ["social_interactions", "activities", "success_failure",
                "fortune_misfortune", "settings", "descriptive"]:
        det_dict = deterministic_coding.get(key) or {}
        llm_dict = llm_coding.get(key) or {}
        merged_sub = {}
        all_subkeys = set(det_dict.keys()) | set(llm_dict.keys())
        for sk in all_subkeys:
            d = det_dict.get(sk) or []
            l = llm_dict.get(sk) or []
            if isinstance(d, list) and isinstance(l, list):
                merged_sub[sk] = list(dict.fromkeys(d + l))
            else:
                merged_sub[sk] = d or l
        merged[key] = merged_sub

    # emotions — int sum (LLM이 잡은 카운트 + 결정론 카운트)
    det_em = deterministic_coding.get("emotions") or {}
    llm_em = llm_coding.get("emotions") or {}
    merged_em = {}
    for k in ["anger", "apprehension", "happiness", "sadness", "confusion"]:
        d = det_em.get(k)
        l = llm_em.get(k)
        # 결정론은 list, LLM은 int → 길이로 환산
        d_n = len(d) if isinstance(d, list) else (d or 0)
        l_n = l if isinstance(l, int) else (len(l) if isinstance(l, list) else 0)
        merged_em[k] = d_n + l_n
    merged["emotions"] = merged_em

    return merged


def _empty_coding() -> dict[str, Any]:
    return {
        "characters": [],
        "social_interactions": {"friendly": [], "aggressive": [], "sexual": []},
        "activities": {"physical": [], "movement": [], "cognitive": []},
        "success_failure": {"success": [], "failure": []},
        "fortune_misfortune": {"fortune": [], "misfortune": []},
        "emotions": {"anger": 0, "apprehension": 0, "happiness": 0, "sadness": 0, "confusion": 0},
        "settings": {"home": [], "work": [], "school": [], "outdoor": [], "public": [], "other": []},
        "objects": [],
        "descriptive": {"color": [], "size": []},
        "food_eating": [],
    }


__all__ = [
    "HVDC_LLM_LABEL",
    "HVDC_LLM_SYSTEM",
    "code_dream_with_llm",
    "merge_deterministic_and_llm",
]
