"""ADR-134 — 토정비결 시구 단정 어휘 차단 + 흐름 톤 치환.

학술 근거:
  - 보고서 「한국 토정비결 144괘 정통 시구 학술 출처」 §4·§6 본문 명시
  - assertion_words_to_block: 6 단정 어휘
  - recommended_flow_tone_substitutions: 10 치환 패턴

ADR 정합:
  - ADR-006 자문 거절 정신 핵심 — 토정비결 정통 시구 단정 어휘 차단
  - ADR-094·113·115·116·117 sanitize 4중 안전망 후속 6번째 확장
  - 정통 시구의 凶事·大凶·病死 단정 어휘는 원전 본질이나 SaaS 출력은 흐름 톤 의무
"""
from __future__ import annotations


# ADR-134 차단 + 치환 매핑 (보고서 §4·§6 본문 명시)
# 순서 중요: 긴 패턴 먼저 (예: "大凶" 먼저, 그 후 "凶")
_TOJEONG_FORBIDDEN_REPLACEMENTS: list[tuple[str, str]] = [
    # 차단 어휘 6건 (assertion_words_to_block)
    ("大凶", "매우 어려운 흐름의 결"),
    ("病死", "건강 유의가 필요한 흐름의 결"),
    ("凶事", "어려운 흐름의 결"),
    # 한글 단정 어휘
    ("이혼", "관계의 변화가 예상되는 흐름의 결"),
    ("사망", "주의와 대비가 필요한 흐름의 결"),
    ("재앙", "신중함이 요구되는 흐름의 결"),
    # 긍정 치환 (정통 시구 한자 → 흐름 톤)
    ("大吉", "큰 흐름의 결"),
    ("亨通", "형통한 흐름의 결"),
    ("通達", "순조롭게 뜻이 통하는 흐름의 결"),
    # 단독 "吉"은 마지막 — 앞의 "大吉"·"길한"과 충돌 회피
    ("吉운", "긍정적인 흐름의 결"),
]


def sanitize_tojeong_verse(text: str) -> str:
    """토정비결 시구 출력 텍스트 sanitize — ADR-134 단정 어휘 6중 안전망.

    학술 근거: 보고서 §4 + §6 본문 명시 10 치환 패턴.

    Args:
        text: LLM 작문 또는 정통 시구 인용 텍스트.

    Returns:
        단정 어휘가 흐름 톤으로 치환된 텍스트.

    Examples:
        >>> sanitize_tojeong_verse("凶事가 다가옵니다")
        '어려운 흐름의 결가 다가옵니다'
        >>> sanitize_tojeong_verse("大吉의 운수")
        '큰 흐름의 결의 운수'
    """
    if not text:
        return text
    for pattern, replacement in _TOJEONG_FORBIDDEN_REPLACEMENTS:
        text = text.replace(pattern, replacement)
    return text


# 차단 어휘 풀 (회귀 테스트용)
TOJEONG_FORBIDDEN_WORDS: tuple[str, ...] = (
    "凶事", "大凶", "病死", "이혼", "사망", "재앙",
)

# 치환 매핑 (회귀 + LLM 시스템 프롬프트 주입용)
TOJEONG_FLOW_TONE_SUBSTITUTIONS: dict[str, str] = {
    pattern: replacement
    for pattern, replacement in _TOJEONG_FORBIDDEN_REPLACEMENTS
}


__all__ = [
    "sanitize_tojeong_verse",
    "TOJEONG_FORBIDDEN_WORDS",
    "TOJEONG_FLOW_TONE_SUBSTITUTIONS",
]
