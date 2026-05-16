"""입력 정제기 — 운영표준 §7.2.15 본문화.

사용자 화두 본문을 LLM에 전달하기 전에:
  1) 제어 문자(NULL/CR/LF 폭주) 제거
  2) prompt injection 마커 제거 ("\\n\\nSystem:", "```", "<|im_end|>" 등)
  3) 길이 상한 적용 (기본 800자) — 초과분은 잘라내고 표시
  4) 인코딩 정규화 (NFC) — zero-width 문자 제거
  5) 공백 정규화 (연속 공백·개행 압축)

§5.2.4 jailbreak_defense가 의미·의도 차단이라면, 본 모듈은 형식·구조 정제다.
LLM 호출 전 항상 적용.

본 모듈은 결정론·idempotent — 같은 입력은 같은 정제 결과.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


# §7.2.15 기본 상한
MAX_QUESTION_CHARS = 800
MAX_NAME_CHARS = 100  # 사용자 이름·식별값용

# §7.2.15 — prompt injection 마커. 본문에 포함되면 제거 또는 거부.
# 보수적 — 흔히 사용되는 시스템 프롬프트 경계 표지만 제거.
_INJECTION_MARKERS = [
    "\n\nsystem:",
    "\n\nassistant:",
    "\n\nhuman:",
    "<|im_start|>",
    "<|im_end|>",
    "<|endoftext|>",
    "<|system|>",
    "<|user|>",
    "<|assistant|>",
    "[INST]",
    "[/INST]",
    "<<SYS>>",
    "<</SYS>>",
]

# §7.2.15 zero-width 및 보이지 않는 문자 — 제거
_ZERO_WIDTH_CHARS = [
    "​",  # zero-width space
    "‌",  # zero-width non-joiner
    "‍",  # zero-width joiner
    "﻿",  # zero-width no-break space (BOM)
    "⁠",  # word joiner
    "­",  # soft hyphen
]

# 제어 문자 (0x00-0x1F, 0x7F-0x9F) 단 \t \n 제외
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]")

# 3+ 연속 개행 압축 + 5+ 연속 공백 압축
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
_MULTI_SPACE_RE = re.compile(r" {5,}")


@dataclass(frozen=True)
class SanitizeResult:
    text: str
    original_length: int
    final_length: int
    truncated: bool = False
    injection_markers_removed: list[str] = field(default_factory=list)
    zero_width_removed: int = 0
    control_chars_removed: int = 0


# ─────────────────────────── 정제 ───────────────────────────

def sanitize_question(
    text: str | None,
    *,
    max_chars: int = MAX_QUESTION_CHARS,
) -> SanitizeResult:
    """화두 본문 정제. None이면 빈 결과.

    Args:
        text: 사용자 화두
        max_chars: 길이 상한 (default 800)
    """
    if not text or not isinstance(text, str):
        return SanitizeResult(text="", original_length=0, final_length=0)

    original_length = len(text)
    out = text

    # 1) NFC 정규화 (조합 자모 → 음절)
    out = unicodedata.normalize("NFC", out)

    # 2) zero-width 제거
    zw_removed = 0
    for ch in _ZERO_WIDTH_CHARS:
        n_before = out.count(ch)
        if n_before:
            out = out.replace(ch, "")
            zw_removed += n_before

    # 3) 제어 문자 제거
    cc_before = len(out)
    out = _CONTROL_CHAR_RE.sub("", out)
    control_removed = cc_before - len(out)

    # 4) prompt injection 마커 제거
    lower = out.lower()
    markers_hit: list[str] = []
    for marker in _INJECTION_MARKERS:
        ml = marker.lower()
        if ml in lower:
            markers_hit.append(marker)
            # 대소문자 무관 제거 — 정규식
            out = re.sub(re.escape(marker), "", out, flags=re.IGNORECASE)
            lower = out.lower()

    # 5) 공백 정규화 — 3+ 개행 → 2개, 5+ 공백 → 1개
    out = _MULTI_NEWLINE_RE.sub("\n\n", out)
    out = _MULTI_SPACE_RE.sub(" ", out)

    # 6) 양끝 trim
    out = out.strip()

    # 7) 길이 상한
    truncated = False
    if len(out) > max_chars:
        out = out[:max_chars]
        truncated = True

    return SanitizeResult(
        text=out,
        original_length=original_length,
        final_length=len(out),
        truncated=truncated,
        injection_markers_removed=markers_hit,
        zero_width_removed=zw_removed,
        control_chars_removed=control_removed,
    )


def sanitize_name(
    text: str | None,
    *,
    max_chars: int = MAX_NAME_CHARS,
) -> str:
    """사용자 이름·식별값 — 화두보다 더 엄격. 개행 0개, 특수문자 제한."""
    if not text or not isinstance(text, str):
        return ""
    # NFC 정규화
    out = unicodedata.normalize("NFC", text)
    # 모든 제어 문자 + 개행 제거 (이름은 단일 라인)
    out = re.sub(r"[\x00-\x1f\x7f-\x9f\n\r\t]", "", out)
    # zero-width 제거
    for ch in _ZERO_WIDTH_CHARS:
        out = out.replace(ch, "")
    # 공백 정규화
    out = re.sub(r"\s+", " ", out).strip()
    # 길이 상한
    if len(out) > max_chars:
        out = out[:max_chars]
    return out


def has_injection_attempt(text: str | None) -> bool:
    """빠른 게이트 — injection 마커 1개라도 있으면 True. 정제 없이 판정만."""
    if not text or not isinstance(text, str):
        return False
    lower = text.lower()
    return any(m.lower() in lower for m in _INJECTION_MARKERS)


def to_trace_event(result: SanitizeResult) -> dict[str, object]:
    """§7.3.4 tracing extra 호환 페이로드."""
    return {
        "sanitize_original_length": result.original_length,
        "sanitize_final_length": result.final_length,
        "sanitize_truncated": result.truncated,
        "sanitize_injection_count": len(result.injection_markers_removed),
        "sanitize_zero_width_removed": result.zero_width_removed,
        "sanitize_control_chars_removed": result.control_chars_removed,
    }
