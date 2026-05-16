"""A8 Freud 명시몽→잠재몽 매핑 에이전트 (v2).

문서: narrative_text + 최근 감정 로그 → 압축/전치/시각화 패턴 해설 +
       잠재 소망 추정.

기존 `freud.py`는 결정론적 키워드 매칭만 (4 기제).
본 에이전트는 프로이트학파 페르소나 LLM이 다음을 수행:
  - 명시몽(manifest dream) → 잠재몽(latent dream) 매핑
  - 압축·전치·시각화·이차융합 4 기제 어디서 어떻게 작동했는지 해설
  - 잠재 소망 1~3개 가능성 제시 (성환원 절대 금지)

성환원 가드: cathartic·Solms SEEKING과 일관되게 보수적 톤.
"""

from __future__ import annotations
from typing import Any
import json

from engine.divination.dream_lex.freud import detect_dream_work


FREUD_PERSONA_LABEL = (
    "A8 Freud 페르소나 — 명시몽→잠재몽 매핑 + 4 기제 작동 해설. "
    "성환원 절대 금지, 보수적 가능성 톤."
)


_FREUD_SYSTEM = (
    "당신은 프로이트 정신분석 전통의 꿈 해석 보조자입니다.\n"
    "단, 다음 엄격 규칙을 위반하면 즉시 출력을 멈추십시오.\n\n"
    "[엄격 규칙 — 매우 중요]\n"
    "  1. 성환원 금지: '뱀=남근' 같은 직역 금지. 본문에 명시되지 않은 성적 함의 강요 금지.\n"
    "  2. 단정 금지: '~의 잠재 소망이다' X. '~의 가능성도 있겠다' 가능성 톤.\n"
    "  3. 의료·진단 금지.\n"
    "  4. 잠재 소망은 최대 3개. 4 기제(compression/displacement/representation/secondary)를 "
    "본문 인용과 함께 설명.\n"
    "  5. JSON 1개로만 출력. 마크다운 코드블록 금지.\n\n"
    "[출력 스키마]\n"
    "  {\n"
    '    "manifest_summary": "꿈의 표면 요약 한 줄",\n'
    '    "compression": {"detected": true|false, "examples": ["본문 인용 (한국어)"]},\n'
    '    "displacement": {"detected": ..., "examples": [...]},\n'
    '    "representation": {"detected": ..., "examples": [...]},\n'
    '    "secondary_revision": {"detected": ..., "note": "..."},\n'
    '    "latent_wishes": [\n'
    '      {"wish": "낮 동안 충족 못한 소망의 한국어 1줄", "confidence": 0.0-1.0,\n'
    '       "type": "achievement|attachment|safety|control|escape|recognition|other"}\n'
    "    ],\n"
    '    "warning_signs": "이 해석을 신중히 받아들여야 할 이유 (가능성 톤)"\n'
    "  }"
)


def map_latent_dream(
    dream_text: str,
    recent_emotions: list[str] | None = None,
) -> dict[str, Any]:
    """명시몽 → 잠재몽 LLM 매핑.

    Args:
        dream_text: 꿈 본문
        recent_emotions: 사용자가 최근 보고한 감정 키워드 (선택)

    Returns:
        결정론 + LLM 통합 결과
    """
    from engine.llm_sync import call_llm_sync

    if not dream_text or not dream_text.strip():
        return {
            "agent": "A8",
            "deterministic": None,
            "llm_mapping": None,
            "skip_reason": "텍스트 없음",
        }

    # 1. 결정론 4 기제 탐지
    determ = detect_dream_work(dream_text)

    # 2. LLM 매핑
    emotions_block = (
        f"\n[사용자 최근 감정 로그]\n  · {', '.join(recent_emotions[:8])}"
        if recent_emotions else ""
    )
    user_msg = (
        f"[꿈 본문]\n{dream_text[:2000]}\n\n"
        f"[결정론 1차 탐지 결과]\n"
        f"  · 감지된 기제: {', '.join(determ.get('mechanisms_used') or ['없음'])}\n"
        f"{emotions_block}\n\n"
        f"위 본문을 프로이트 전통으로 분석해 JSON으로 출력. 성환원 절대 금지."
    )

    try:
        raw = call_llm_sync(user_text=user_msg, system_prompt=_FREUD_SYSTEM)
    except Exception as e:
        return {
            "agent": "A8",
            "deterministic": determ,
            "llm_mapping": None,
            "error": f"LLM 호출 실패: {e}",
        }

    cleaned = _strip_codeblock(raw or "")
    try:
        data = json.loads(cleaned)
        mapping = _normalize(data)
    except json.JSONDecodeError as e:
        mapping = None

    return {
        "agent": "A8",
        "deterministic": determ,
        "llm_mapping": mapping,
        "raw_response": (raw or "")[:300] if not mapping else None,
        "principle": (
            "프로이트의 압축·전치·시각화·이차융합 4 기제는 결정론 탐지가 1차. "
            "LLM은 그 위에 본문 인용과 잠재 소망 가능성을 보수적으로 제시 — "
            "성환원·단정 절대 금지."
        ),
    }


def _strip_codeblock(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        lines = t.split("\n")
        if len(lines) > 2:
            t = "\n".join(lines[1:-1])
    first = t.find("{")
    last = t.rfind("}")
    if first >= 0 and last > first:
        t = t[first:last + 1]
    return t


def _normalize(data: dict[str, Any]) -> dict[str, Any]:
    """LLM 응답 정규화 + 안전 디폴트."""
    out: dict[str, Any] = {
        "manifest_summary": "",
        "compression": {"detected": False, "examples": []},
        "displacement": {"detected": False, "examples": []},
        "representation": {"detected": False, "examples": []},
        "secondary_revision": {"detected": False, "note": ""},
        "latent_wishes": [],
        "warning_signs": "",
    }
    if isinstance(data.get("manifest_summary"), str):
        out["manifest_summary"] = data["manifest_summary"][:300]

    for key in ("compression", "displacement", "representation"):
        v = data.get(key) or {}
        if isinstance(v, dict):
            out[key] = {
                "detected": bool(v.get("detected")),
                "examples": [
                    str(e)[:200] for e in (v.get("examples") or [])[:5]
                    if isinstance(e, str)
                ],
            }

    sr = data.get("secondary_revision") or {}
    if isinstance(sr, dict):
        out["secondary_revision"] = {
            "detected": bool(sr.get("detected")),
            "note": str(sr.get("note", ""))[:300],
        }

    wishes = data.get("latent_wishes") or []
    if isinstance(wishes, list):
        valid_types = {"achievement", "attachment", "safety", "control", "escape", "recognition", "other"}
        out["latent_wishes"] = [
            {
                "wish": str(w.get("wish", ""))[:200],
                "confidence": min(1.0, max(0.0, float(w.get("confidence", 0.5)))),
                "type": w.get("type") if w.get("type") in valid_types else "other",
            }
            for w in wishes[:3]
            if isinstance(w, dict)
        ]

    if isinstance(data.get("warning_signs"), str):
        out["warning_signs"] = data["warning_signs"][:300]

    return out


__all__ = [
    "FREUD_PERSONA_LABEL",
    "map_latent_dream",
]
