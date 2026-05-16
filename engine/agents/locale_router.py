"""B2 다국어 라우터 — 언어/문화에 따른 이론 가중치 조정.

문서 §11-E 다국어 우선순위:
  1. 한국어:  #1 #4 #12 #13 #14 #26 + 전체    [MVP]
  2. 영어:    #2 #5 #6 #7 #8 #9 #10 #11 #15 #22 [v2]
  3. 중국어:  #3 #12 #13 #14 + 전체              [v3]
  4. 일본어:  #16 #12 + 전체                     [v3]
  5. 아랍어:  #15 우선 #2                       [v4]
  6. 인니/말: #15 #12                           [v4]
  7. 스페인: #2 #5 #6 + 전체                    [v5]

결정론 — 언어 코드만으로 분기. LLM 호출 0회.
"""

from __future__ import annotations
from typing import Any
from dataclasses import dataclass


LOCALE_THEORY_WEIGHTS: dict[str, dict[str, float]] = {
    "ko": {
        "korean_folk": 2.0, "paja": 1.5, "zhougong": 1.3,
        "eumsabalmong": 1.3, "donguibogam": 1.3,
        "clinical_kr": 2.0,  # CES-D/BDI-K/STAI-K 한국판
        "iching": 1.3,
    },
    "en": {
        "artemidorus": 1.5, "freud": 1.3, "jung_archetypes": 1.3,
        "hobson": 1.3, "revonsuo_tst": 1.3, "domhoff": 1.3,
        "hallvandecastle": 1.3, "dreambank": 1.3, "ibn_sirin": 1.0,
        "schredl_diary": 1.3,
    },
    "zh": {
        "wuxing": 2.0, "iching": 2.0, "zhougong": 2.0,
        "eumsabalmong": 1.5, "donguibogam": 1.5,
    },
    "ja": {
        "myoe": 2.5, "zhougong": 1.5, "iching": 1.3, "wuxing": 1.3,
    },
    "ar": {
        "ibn_sirin": 3.0, "artemidorus": 1.5,
    },
    "id": {"ibn_sirin": 2.0, "zhougong": 1.3},
    "ms": {"ibn_sirin": 2.0, "zhougong": 1.3},
    "es": {"artemidorus": 1.5, "freud": 1.3, "jung_archetypes": 1.3},
}


LOCALE_LLM_DIRECTIVE = {
    "ko": "한국어로 답변하세요.",
    "en": "Answer in natural English.",
    "zh": "请用自然的中文回答。",
    "ja": "自然な日本語で回答してください。",
    "ar": "أجب باللغة العربية الفصحى.",
    "id": "Jawab dalam Bahasa Indonesia yang alami.",
    "ms": "Jawab dalam Bahasa Malaysia yang semula jadi.",
    "es": "Responde en español natural.",
}


# 종교 중립 가드 (#15 이븐 시린은 무슬림 사용자에게만 적극 활성)
RELIGIOUS_NEUTRAL_LOCALES = {"ko", "en", "ja", "zh", "es"}


@dataclass
class LocaleRouting:
    """다국어 라우팅 결과."""
    locale: str
    theory_weights: dict[str, float]
    llm_directive: str
    enable_ibn_sirin_active: bool  # 무슬림 시장에서만 적극 인용
    fallback_to_en: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "locale": self.locale,
            "theory_weights": self.theory_weights,
            "llm_directive": self.llm_directive,
            "enable_ibn_sirin_active": self.enable_ibn_sirin_active,
            "fallback_to_en": self.fallback_to_en,
        }


def route_locale(
    locale: str | None,
    religion: str | None = None,
) -> LocaleRouting:
    """언어 + 종교 → 이론 가중치·LLM 지시문 라우팅."""
    lc = (locale or "ko").split("-")[0].split("_")[0].lower()

    if lc not in LOCALE_THEORY_WEIGHTS:
        # fallback: en
        weights = LOCALE_THEORY_WEIGHTS["en"]
        directive = LOCALE_LLM_DIRECTIVE["en"]
        fallback = True
        lc = "en"
    else:
        weights = dict(LOCALE_THEORY_WEIGHTS[lc])
        directive = LOCALE_LLM_DIRECTIVE.get(lc, LOCALE_LLM_DIRECTIVE["en"])
        fallback = False

    # 무슬림 사용자라면 어느 언어든 ibn_sirin 적극 활성
    ibn_active = (lc in {"ar", "id", "ms"}) or (religion == "muslim")
    if ibn_active:
        weights["ibn_sirin"] = max(weights.get("ibn_sirin", 0.0), 2.0)

    return LocaleRouting(
        locale=lc,
        theory_weights=weights,
        llm_directive=directive,
        enable_ibn_sirin_active=ibn_active,
        fallback_to_en=fallback,
    )


__all__ = [
    "LOCALE_THEORY_WEIGHTS",
    "LOCALE_LLM_DIRECTIVE",
    "LocaleRouting",
    "route_locale",
]
