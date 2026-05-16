"""응답 표준화 어댑터 — 운영표준 §7.2.13 본문화.

face_reading의 응답 분기(정상 / 캐시 히트 / 위기 차단 / jailbreak 차단 /
ERR / WARN)가 모두 동일한 envelope 키 집합을 유지하는지 검증·정규화.

이 검증이 없으면 클라이언트가 "어떤 분기에는 a11y가 있고 어떤 분기에는 없다"
같은 분기별 차이를 겪고, 회귀 시 누락된 키를 발견하기 어렵다.

§7.2.13 필수 키:
  · text             — str (사용자 노출 본문)
  · cached           — bool
  · crisis_alert     — dict|None
  · legal_notice     — str|None
  · detected_language — str|None
  · language_advisory — str|None

§7.2.13 선택 키 (분기별):
  · a11y               — 정상/ERR/위기 (jailbreak는 선택)
  · emotion_disclosure — 정상 응답 (EU 메타)
  · error_code         — ERR/WARN/jailbreak
  · photo_guidance     — ERR/WARN
  · jailbreak_categories — jailbreak
  · persona_self_eval  — 정상 응답
"""

from __future__ import annotations

from typing import Any


# §7.2.13 envelope 분기 식별자
ENVELOPE_NORMAL = "normal"
ENVELOPE_CACHED = "cached"
ENVELOPE_CRISIS = "crisis"
ENVELOPE_JAILBREAK = "jailbreak"
ENVELOPE_ERROR = "error"
ENVELOPE_WARN = "warn"


# §7.2.13 — 모든 분기에 반드시 있어야 하는 키
REQUIRED_KEYS = (
    "text",
    "cached",
    "crisis_alert",
    "legal_notice",
    "detected_language",
    "language_advisory",
)


# §7.2.13 — 분기별 추가 필수 키
_BRANCH_REQUIRED = {
    ENVELOPE_NORMAL: ("a11y", "persona_self_eval"),
    ENVELOPE_CACHED: ("a11y",),
    ENVELOPE_CRISIS: ("a11y", "crisis_alert"),
    ENVELOPE_JAILBREAK: ("error_code", "jailbreak_categories", "a11y"),
    ENVELOPE_ERROR: ("error_code", "photo_guidance", "a11y"),
    ENVELOPE_WARN: ("error_code", "photo_guidance", "a11y"),
}


# ─────────────────────────── 분기 추정 ───────────────────────────

def detect_branch(envelope: dict[str, Any]) -> str:
    """응답 dict을 보고 어느 분기인지 추정. 우선순위: crisis > jailbreak > ERR > WARN > cached > normal."""
    if not isinstance(envelope, dict):
        return ""
    crisis = envelope.get("crisis_alert")
    if crisis:
        return ENVELOPE_CRISIS
    cats = envelope.get("jailbreak_categories")
    if cats:
        return ENVELOPE_JAILBREAK
    code = envelope.get("error_code")
    if code:
        if str(code).startswith("WARN_"):
            return ENVELOPE_WARN
        return ENVELOPE_ERROR
    if envelope.get("cached") is True:
        return ENVELOPE_CACHED
    return ENVELOPE_NORMAL


# ─────────────────────────── 검증 ───────────────────────────

def validate_envelope(envelope: dict[str, Any]) -> list[str]:
    """envelope 검증 — 위반 사항 리스트 (비어있으면 OK)."""
    violations: list[str] = []
    if not isinstance(envelope, dict):
        return ["not_a_dict"]
    # 1) REQUIRED_KEYS 모두 존재
    for k in REQUIRED_KEYS:
        if k not in envelope:
            violations.append(f"missing_required:{k}")
    # 2) text는 비어있지 않은 str
    text = envelope.get("text")
    if not isinstance(text, str) or not text:
        violations.append("text_invalid")
    # 3) cached는 bool
    if not isinstance(envelope.get("cached"), bool):
        violations.append("cached_not_bool")
    # 4) crisis_alert는 dict | None
    crisis = envelope.get("crisis_alert")
    if crisis is not None and not isinstance(crisis, dict):
        violations.append("crisis_alert_invalid")
    # 5) 분기별 추가 필수 키
    branch = detect_branch(envelope)
    if branch:
        for extra in _BRANCH_REQUIRED.get(branch, ()):
            if extra not in envelope:
                violations.append(f"missing_branch_key:{branch}:{extra}")
    return violations


def is_valid(envelope: dict[str, Any]) -> bool:
    return not validate_envelope(envelope)


# ─────────────────────────── 정규화 ───────────────────────────

def normalize_envelope(envelope: dict[str, Any]) -> dict[str, Any]:
    """REQUIRED_KEYS에 None 기본값을 채워 누락 차단. 원본 변경 없이 사본 반환.

    text는 비어있으면 빈 문자열로, cached는 None이면 False로 대체.
    a11y가 있으면 그대로, 없으면 분기에 따라 기본 빈 dict.
    """
    if not isinstance(envelope, dict):
        return {}
    out = dict(envelope)
    defaults: dict[str, Any] = {
        "text": "",
        "cached": False,
        "crisis_alert": None,
        "legal_notice": None,
        "detected_language": None,
        "language_advisory": None,
    }
    for k, v in defaults.items():
        if k not in out:
            out[k] = v
    if out.get("text") is None:
        out["text"] = ""
    if out.get("cached") is None:
        out["cached"] = False
    return out


# ─────────────────────────── 집계 ───────────────────────────

def audit_envelopes(envelopes: list[dict[str, Any]]) -> dict[str, Any]:
    """N건의 envelope를 일괄 감사. branch_distribution + violation_by_index."""
    distribution: dict[str, int] = {}
    violations_by_index: dict[int, list[str]] = {}
    for i, env in enumerate(envelopes):
        branch = detect_branch(env)
        distribution[branch] = distribution.get(branch, 0) + 1
        v = validate_envelope(env)
        if v:
            violations_by_index[i] = v
    valid_count = len(envelopes) - len(violations_by_index)
    return {
        "total": len(envelopes),
        "valid": valid_count,
        "invalid": len(violations_by_index),
        "branch_distribution": distribution,
        "violations_by_index": violations_by_index,
        "all_valid": not violations_by_index,
    }
