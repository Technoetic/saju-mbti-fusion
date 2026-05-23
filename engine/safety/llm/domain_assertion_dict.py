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


_DOMAIN_VOCAB = {
    "face": _COMMON_FATE_ASSERTIONS,
    "palm": _COMMON_FATE_ASSERTIONS + _PALM_FATE_ASSERTIONS,
    "name": _COMMON_FATE_ASSERTIONS + _NAME_FATE_ASSERTIONS,
    "dream": _COMMON_FATE_ASSERTIONS + _DREAM_FATE_ASSERTIONS,
    "hwapae": _COMMON_FATE_ASSERTIONS + _HWAPAE_FATE_ASSERTIONS,
}


@dataclass(frozen=True)
class FateAssertionResult:
    detected: bool
    matched_terms: list[str] = field(default_factory=list)
    domain: str | None = None


def _is_negated(text: str, term: str) -> bool:
    idx = text.find(term)
    if idx < 0:
        return False
    start = max(0, idx - 25)
    end = min(len(text), idx + len(term) + 25)
    window = text[start:end]
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
