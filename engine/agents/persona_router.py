"""B3 페르소나 분기기 — P1~P10 자동 분류.

문서 §6 10대 페르소나 분기 → 호출 이론 우선순위·UX 톤 결정.

10 페르소나:
  P1  임산부·예비 부모    (태몽·동물·과일·보석)
  P2  PTSD·악몽 환자      (반복 악몽·자살 사고)
  P3  자각몽 훈련자        (메타인지 훈련)
  P4  사주·운세 사용자     (오행·길흉)
  P5  Z세대·자기탐색       (짧은 일기·시각화)
  P6  학습자·창작자        (영감·기억 통합)
  P7  한방·건강 관심자     (체질·장부)
  P8  다문화·해외          (영문·이슬람)
  P9  어린이·청소년        (보호자 동반)
  P10 노년·돌봄           (사별·치매·약물)

결정론 점수화 + 사용자 프로필 가중치. LLM 호출 0회.
"""

from __future__ import annotations
from typing import Any
from dataclasses import dataclass


# ─────────────────────────── 페르소나 정의 ───────────────────────────
PERSONAS = {
    "P1": {"label": "임산부·예비 부모", "ux_tone": "따뜻·축복",
            "theory_boost": {"korean_folk_태몽": 2.0, "archetypes_self": 1.2}},
    "P2": {"label": "PTSD·악몽 환자", "ux_tone": "임상·간결",
            "theory_boost": {"clinical": 2.0, "irt": 2.5, "tst": 1.5}},
    "P3": {"label": "자각몽 훈련자", "ux_tone": "게이미피케이션",
            "theory_boost": {"lucid": 2.5, "myoe": 1.3}},
    "P4": {"label": "사주·운세 사용자", "ux_tone": "동양적 권위",
            "theory_boost": {"wuxing": 2.0, "iching": 2.0, "zhougong": 1.5, "korean_folk": 1.5}},
    "P5": {"label": "Z세대·자기탐색", "ux_tone": "짧고 모던",
            "theory_boost": {"hvdc": 1.5, "domhoff": 1.5, "archetypes": 1.3}},
    "P6": {"label": "학습자·창작자", "ux_tone": "노트앱·캘린더",
            "theory_boost": {"stickgold": 2.0, "domhoff": 1.5, "schredl_diary": 1.5}},
    "P7": {"label": "한방·건강 관심자", "ux_tone": "한의학",
            "theory_boost": {"eumsabalmong": 2.0, "donguibogam": 2.0, "wuxing": 1.5}},
    "P8": {"label": "다문화·해외", "ux_tone": "다국어·종교 중립",
            "theory_boost": {"ibn_sirin": 2.0, "artemidorus": 1.5}},
    "P9": {"label": "어린이·청소년", "ux_tone": "보호자 공동",
            "theory_boost": {"clinical_pediatric": 2.0, "tst": 1.3, "archetypes_child": 1.5}},
    "P10": {"label": "노년·돌봄", "ux_tone": "큰 글씨·음성",
             "theory_boost": {"cartwright_grief": 2.0, "korean_folk_사망": 1.5, "donguibogam": 1.5}},
}


# 페르소나 결정 신호 (사용자 프로필 + 입력 텍스트 기반)
_SIGNAL_MAP: dict[str, dict[str, Any]] = {
    "P1": {
        "profile_predicates": [
            lambda p: p.get("is_pregnant") is True,
            lambda p: "임신" in (p.get("current_concerns") or []),
            lambda p: "출산" in (p.get("current_concerns") or []),
        ],
        "text_markers": ["태몽", "임신", "잉태", "아기", "출산", "구렁이를 잡", "복숭아를 따"],
    },
    "P2": {
        "profile_predicates": [
            lambda p: "PTSD" in (p.get("current_concerns") or []),
            lambda p: "악몽" in (p.get("current_concerns") or []),
        ],
        "text_markers": ["반복되는 악몽", "매일 악몽", "트라우마", "외상", "수면 마비",
                         "자살 사고", "공황", "쫓김 반복"],
    },
    "P3": {
        "profile_predicates": [
            lambda p: "자각몽" in (p.get("current_concerns") or []),
            lambda p: "lucid" in str(p.get("current_concerns") or []).lower(),
        ],
        "text_markers": ["자각몽", "lucid", "꿈인 줄 알았", "꿈에서 통제",
                         "MILD", "WBTB", "reality check"],
    },
    "P4": {
        "profile_predicates": [
            lambda p: bool(p.get("day_master")),
            lambda p: bool(p.get("yongsin")),
            lambda p: p.get("occupation") in ("점술가", "역술인"),
        ],
        "text_markers": ["사주", "용신", "운세", "팔자", "오행", "길흉", "점몽"],
    },
    "P5": {
        "profile_predicates": [
            lambda p: (p.get("age") or 99) <= 27,
        ],
        "text_markers": ["짧게", "간단히", "이모지", "공유"],
    },
    "P6": {
        "profile_predicates": [
            lambda p: p.get("occupation") in ("학생", "수험생", "디자이너", "작가", "개발자", "연구자"),
            lambda p: "시험" in (p.get("current_concerns") or []),
            lambda p: "공부" in (p.get("current_concerns") or []),
        ],
        "text_markers": ["시험", "공부", "코드", "디자인", "아이디어", "영감", "작품"],
    },
    "P7": {
        "profile_predicates": [
            lambda p: "건강" in (p.get("current_concerns") or []),
            lambda p: "한방" in (p.get("current_concerns") or []),
        ],
        "text_markers": ["몸이 안 좋", "허리", "심장", "체질", "기혈", "한의원",
                         "장부", "기허", "신허", "간기"],
    },
    "P8": {
        "profile_predicates": [
            lambda p: p.get("locale") and p["locale"] not in ("ko", "ko_KR"),
            lambda p: p.get("religion") == "muslim",
        ],
        "text_markers": ["Ruyā", "Hulm", "Allah", "Islam", "mosque", "Quran"],
    },
    "P9": {
        "profile_predicates": [
            lambda p: (p.get("age") or 99) < 18,
            lambda p: p.get("guardian_account") is True,
        ],
        "text_markers": ["엄마가 함께", "보호자", "학교", "선생님", "방학"],
    },
    "P10": {
        "profile_predicates": [
            lambda p: (p.get("age") or 0) >= 65,
        ],
        "text_markers": ["사별", "돌아가신", "고인", "장례", "약물", "치매",
                         "노년", "은퇴"],
    },
}


@dataclass
class PersonaClassification:
    """페르소나 분류 결과."""
    primary: str | None
    secondary: str | None
    scores: dict[str, float]
    theory_boost: dict[str, float]
    ux_tone: str | None
    confidence: float
    rationale: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary": self.primary,
            "primary_label": (PERSONAS.get(self.primary) or {}).get("label") if self.primary else None,
            "secondary": self.secondary,
            "secondary_label": (PERSONAS.get(self.secondary) or {}).get("label") if self.secondary else None,
            "scores": self.scores,
            "theory_boost": self.theory_boost,
            "ux_tone": self.ux_tone,
            "confidence": round(self.confidence, 2),
            "rationale": self.rationale,
        }


def classify_persona(
    profile: dict[str, Any] | None,
    dream_text: str = "",
) -> PersonaClassification:
    """프로필 + 꿈 텍스트 기반 페르소나 점수화."""
    p = profile or {}
    t = dream_text or ""
    scores: dict[str, float] = {k: 0.0 for k in PERSONAS}
    rationale: list[str] = []

    for persona_key, signals in _SIGNAL_MAP.items():
        # 프로필 술어
        for pred in signals["profile_predicates"]:
            try:
                if pred(p):
                    scores[persona_key] += 3.0
                    rationale.append(f"{persona_key}: 프로필 매칭")
            except Exception:
                pass
        # 텍스트 마커
        for m in signals["text_markers"]:
            if m in t:
                scores[persona_key] += 1.0
                rationale.append(f"{persona_key}: '{m}' 등장")

    # 정렬
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top = sorted_scores[0]
    second = sorted_scores[1] if len(sorted_scores) > 1 else (None, 0.0)

    primary = top[0] if top[1] > 0 else None
    secondary = second[0] if second[1] > 0 and second[0] != primary else None
    total_signal = sum(scores.values())
    confidence = min(1.0, top[1] / 6.0) if top[1] > 0 else 0.0

    theory_boost: dict[str, float] = {}
    if primary:
        theory_boost.update(PERSONAS[primary]["theory_boost"])
    if secondary:
        for k, v in PERSONAS[secondary]["theory_boost"].items():
            # 부 페르소나는 50% 반영
            theory_boost[k] = max(theory_boost.get(k, 0.0), v * 0.5)

    ux_tone = (PERSONAS.get(primary) or {}).get("ux_tone") if primary else "기본"

    return PersonaClassification(
        primary=primary,
        secondary=secondary,
        scores=scores,
        theory_boost=theory_boost,
        ux_tone=ux_tone,
        confidence=confidence,
        rationale=rationale[:6],
    )


__all__ = [
    "PERSONAS",
    "PersonaClassification",
    "classify_persona",
]
