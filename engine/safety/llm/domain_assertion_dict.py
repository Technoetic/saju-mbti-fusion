"""ADR-171 - domain fate-assertion dictionary."""

from __future__ import annotations

from dataclasses import dataclass, field


FATE_ASSERTION = "fate_assertion_detected"


_NEGATION_MARKERS = (
    "아니라", "아니로", "아닌", "않으", "처럼 보이지", "같지 않",
    "단정할 수 없", "단언할 수 없", "예언이 아니",
)


_COMMON_FATE_ASSERTIONS = (
    "장수의 결", "장수하리", "오래 사실 것", "단명할 결", "단명하리",
    "큰 부를 이루", "거부가 되리", "큰 재물을 얻으리", "재물이 쏟아지",
    "관운이 트일 것이라", "벼슬길이 열리리", "출세하리라",
    "혼인이 이루어지리", "배필을 만나리", "자손이 번창하리",
    "병이 낫으리", "건강이 회복되리",
    "재앙이 닥치리", "큰 화가 있을 것",
    # ADR-188 보수적 확장 — 명백 위반 패턴만
    "반드시 부자가", "틀림없이 성공",
    "운명이 정해진", "피할 수 없는 운명",
    "이번 생은 다 ",
)


_PALM_FATE_ASSERTIONS = (
    "긴 생명선이라 장수", "짧은 생명선이라 단명",
    "감정선이 깊으니 사랑이",
    "운명선이 또렷하니 출세",
    "지능선이 길어 재능이",
)


_NAME_FATE_ASSERTIONS = (
    "이 이름은 부귀의 결", "이 이름이 큰 재물을",
    "이 이름은 단명의 결", "이 이름이 화를 부르",
    "이 이름은 관운의 결",
)


_DREAM_FATE_ASSERTIONS = (
    "이 꿈은 길몽이라 큰 재물이",
    "이 꿈은 흉몽이라 화가",
    "이 꿈을 꾸면 임신",
    "이 꿈을 꾸면 죽",
)


_HWAPAE_FATE_ASSERTIONS = (
    "이 화패는 큰 재물의 결",
    "이 화패는 흉운의",
    "이 화패가 혼인을 이루",
)


# ADR-175 — saju 사주 도메인 단정 어휘
# saju는 결정론 위주이나 saju_mbti·desire_saju·jeongin_saju 등 일부 LLM
# 호출 경로 보조. 학파 단정·시기 단정·결혼 시기 등 ADR-002·006 위반.
_SAJU_FATE_ASSERTIONS = (
    "이 사주는 대운이",  # "대운이 들어오리"·"대운이 트일 것" 등
    "이 사주는 큰 부를",
    "이 사주는 단명",
    "이 사주는 이혼",
    "이 사주가 출세",
    "올해 결혼할 사주",
    "내년에 자녀를 얻을 사주",
)


_DOMAIN_VOCAB = {
    "face": _COMMON_FATE_ASSERTIONS,
    "palm": _COMMON_FATE_ASSERTIONS + _PALM_FATE_ASSERTIONS,
    "name": _COMMON_FATE_ASSERTIONS + _NAME_FATE_ASSERTIONS,
    "dream": _COMMON_FATE_ASSERTIONS + _DREAM_FATE_ASSERTIONS,
    "hwapae": _COMMON_FATE_ASSERTIONS + _HWAPAE_FATE_ASSERTIONS,
    "saju": _COMMON_FATE_ASSERTIONS + _SAJU_FATE_ASSERTIONS,
}


@dataclass(frozen=True)
class FateAssertionResult:
    detected: bool
    matched_terms: list[str] = field(default_factory=list)
    domain: str | None = None


_SENTENCE_BOUNDARIES = (".", "!", "?", "\n", "。", "!", "?")


def _sentence_window(text: str, idx: int, term_len: int) -> str:
    """ADR-187 — 부정 컨텍스트 윈도우를 문장 경계까지 확장.

    이전: ±25자 고정 → 긴 문장에서 부정 마커 누락.
    이제: 좌측은 직전 문장 종결 부호까지, 우측은 다음 문장 종결 부호까지.
    문장 경계 미발견 시 ±60자로 폴백 (긴 문장 안전 마진).
    """
    # 좌측 — 직전 문장 종결 부호 위치
    start = idx
    while start > 0 and text[start - 1] not in _SENTENCE_BOUNDARIES:
        start -= 1
        if idx - start > 60:  # 안전 마진
            break
    # 우측 — 다음 문장 종결 부호 위치 (term_len 만큼 건너뛴 후)
    end = idx + term_len
    while end < len(text) and text[end] not in _SENTENCE_BOUNDARIES:
        end += 1
        if end - (idx + term_len) > 60:
            break
    return text[start:end]


def _is_negated(text: str, term: str) -> bool:
    """ADR-187 — 문장 경계 기반 부정 컨텍스트 검출."""
    idx = text.find(term)
    if idx < 0:
        return False
    window = _sentence_window(text, idx, len(term))
    return any(neg in window for neg in _NEGATION_MARKERS)


def detect_fate_assertions(
    text: str | None,
    domain: str | None = None,
) -> FateAssertionResult:
    """Detect fate-assertion vocabulary in text.

    Args:
        text: LLM response body.
        domain: 'face' | 'palm' | 'name' | 'dream' | 'hwapae' | None.
            None means use common assertions only.

    Returns:
        FateAssertionResult — detected=True if any fate-assertion term
        appears without negation marker in surrounding window.
    """
    if not text:
        return FateAssertionResult(detected=False, domain=domain)
    vocab = _DOMAIN_VOCAB.get(domain or "", _COMMON_FATE_ASSERTIONS)
    matched: list[str] = []
    for term in vocab:
        if term in text and not _is_negated(text, term):
            matched.append(term)
    return FateAssertionResult(
        detected=bool(matched),
        matched_terms=matched,
        domain=domain,
    )
