"""출력 토큰 가드 — 운영표준 §5.2.6 본문화.

LLM 응답이 다음 중 하나에 해당하는지 결정론 감지하고, llm_fallback_router의
폴백 트리거에 매핑한다:

  · TOO_SHORT       — 본문이 너무 짧음 (품질 부족, 페르소나 톤 못 채움)
  · TOO_LONG        — 토큰 한도 근접 (다음 호출 비용 폭발 우려)
  · TRUNCATED       — 미완 문장 끝 (할당 토큰 한도 초과)
  · LANGUAGE_DRIFT  — lang=ko인데 한글 비율이 낮음 (모델 혼동)
  · REPETITION      — 동일 문구 3회 이상 반복 (LLM degeneration)

본 모듈은 검증만 — 응답 변경 X. face_reading은 결과에 따라 폴백 트리거.

§5.2.6 임계:
  · MIN_CHARS = 80    (사극풍 인사 + 본문 최소)
  · MAX_CHARS = 3500  (token≈한자 1.5 → 약 2300 tokens)
  · TRUNCATED 표시: 마지막 문장이 종결 어미·구두점으로 끝나지 않음
  · KO_LANG_MIN = 0.6 (한글 비율 60% 미만이면 drift)
  · REPETITION_MIN = 3 (같은 8자 구절 3회 이상)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# §5.2.6 진단 코드
ISSUE_TOO_SHORT = "too_short"
ISSUE_TOO_LONG = "too_long"
ISSUE_TRUNCATED = "truncated"
ISSUE_LANGUAGE_DRIFT = "language_drift"
ISSUE_REPETITION = "repetition"
ISSUE_NONE = ""

# §5.2.6 임계
MIN_CHARS = 80
MAX_CHARS = 3500
KO_LANG_MIN = 0.6
REPETITION_PHRASE_LEN = 8
REPETITION_MIN = 3

# §5.2.6 종결 표지 — 사극풍 어미 + 일반 구두점
_TERMINAL_MARKERS = (
    "구먼.", "구먼!", "이로세.", "이로구나.", "하이.", "하시게.", "이로세!",
    "한다.", "다.", ".", "!", "?", "…",
    "なさい。", "ます。", "です。",  # ja
    "了。", "吧。", "呢。",         # zh
    "yours.", "yours!", "you.",     # en 영어 사극 종결 흉내 시
)

# 한글 음절 범위
_KO_SYLLABLE_RE = re.compile(r"[가-힣]")
# 공백·구두점 제외 글자 수 셈용
_NON_WS_RE = re.compile(r"\S")


@dataclass(frozen=True)
class TokenGuardResult:
    issues: list[str] = field(default_factory=list)
    char_count: int = 0
    ko_char_ratio: float = 0.0
    ends_with_terminal: bool = False
    top_repeated_phrase: str = ""
    repetition_count: int = 0

    @property
    def ok(self) -> bool:
        return not self.issues


# ─────────────────────────── 헬퍼 ───────────────────────────

def _ko_char_ratio(text: str) -> float:
    """한글 음절 / 전체 비공백 글자."""
    total = len(_NON_WS_RE.findall(text))
    if total == 0:
        return 0.0
    ko = len(_KO_SYLLABLE_RE.findall(text))
    return ko / total


def _ends_with_terminal(text: str) -> bool:
    s = (text or "").rstrip()
    if not s:
        return False
    return any(s.endswith(m) for m in _TERMINAL_MARKERS)


def _detect_repetition(text: str) -> tuple[str, int]:
    """가장 많이 반복된 길이 N 구절과 횟수. 한글 음절 기준 8글자 슬라이딩."""
    if not text or len(text) < REPETITION_PHRASE_LEN * REPETITION_MIN:
        return "", 0
    counts: dict[str, int] = {}
    n = len(text)
    for i in range(n - REPETITION_PHRASE_LEN + 1):
        phrase = text[i:i + REPETITION_PHRASE_LEN]
        # 공백·구두점만으로 이뤄진 구절은 제외
        if not _NON_WS_RE.search(phrase):
            continue
        counts[phrase] = counts.get(phrase, 0) + 1
    if not counts:
        return "", 0
    top = max(counts.items(), key=lambda kv: kv[1])
    return top[0], top[1]


# ─────────────────────────── 진단 ───────────────────────────

def evaluate_output(text: str | None, *, lang: str = "ko") -> TokenGuardResult:
    """§5.2.6 응답 토큰 가드 — 모든 위반 사항 수집.

    Args:
        text: LLM 본문 (legal_footer 등 첨부 전).
        lang: 'ko'면 한글 비율 검사 활성화.
    """
    if not text or not isinstance(text, str):
        return TokenGuardResult(issues=[ISSUE_TOO_SHORT])

    issues: list[str] = []
    n = len(text)
    if n < MIN_CHARS:
        issues.append(ISSUE_TOO_SHORT)
    if n > MAX_CHARS:
        issues.append(ISSUE_TOO_LONG)

    ends_terminal = _ends_with_terminal(text)
    if not ends_terminal and n >= MIN_CHARS:
        issues.append(ISSUE_TRUNCATED)

    ko_ratio = _ko_char_ratio(text)
    if lang == "ko" and ko_ratio < KO_LANG_MIN and n >= MIN_CHARS:
        issues.append(ISSUE_LANGUAGE_DRIFT)

    top_phrase, rep_count = _detect_repetition(text)
    if rep_count >= REPETITION_MIN:
        issues.append(ISSUE_REPETITION)

    return TokenGuardResult(
        issues=issues,
        char_count=n,
        ko_char_ratio=round(ko_ratio, 3),
        ends_with_terminal=ends_terminal,
        top_repeated_phrase=top_phrase,
        repetition_count=rep_count,
    )


def should_trigger_fallback(result: TokenGuardResult) -> bool:
    """폴백 시도가 필요한가 — 단순 빠른 게이트."""
    return bool(result.issues)


def to_fallback_trigger(result: TokenGuardResult) -> str:
    """llm_fallback_router.TRIGGER_* 호환 분류 매핑.

    most-severe 우선 — truncated > too_short > language_drift > repetition > too_long.
    issues 없으면 빈 문자열.
    """
    if not result.issues:
        return ""
    # 매핑 (llm_fallback_router의 TRIGGER 이름과 호환)
    if ISSUE_TRUNCATED in result.issues:
        return "token_limit"
    if ISSUE_TOO_SHORT in result.issues:
        return "empty_response"
    if ISSUE_LANGUAGE_DRIFT in result.issues:
        return "persona_failed"  # 결과적으로 페르소나 자체 평가도 실패할 가능성
    if ISSUE_REPETITION in result.issues:
        return "persona_failed"
    return "token_limit"  # too_long도 보수적으로 폴백
