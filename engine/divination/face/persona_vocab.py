"""ADR-203 - 운학 도사 사극 어휘 사전 확장.

본 모듈은 운학 도사 페르소나 사극 어휘를 카테고리별로 영속.
Stage 2 LLM 시스템 프롬프트에 참조 어휘로 주입 가능 (강제 X — LLM이
자연스럽게 활용).

ADR-006 자문 거절 정신 정합:
  - 운명·길흉 단정 어휘 X (장수·부귀·관운 등 — ADR-171 fate_assertion 사전)
  - 형태 묘사·자아 호명·페르소나 자기지칭만

ADR 정합:
  - ADR-004·005 운학 도사 페르소나 (face/reading.py _FACE_SYSTEM)
  - ADR-171 fate_assertion 사전 (본 사전 어휘는 통과 보장)
  - ADR-170 페르소나별 stub (운학 도사 톤)
  - ADR-014 단정 회피
"""

from __future__ import annotations


# ───── 자기지칭 (운학 도사 호명) ─────
SELF_REFERENCES = (
    "이 늙은이", "이 운학 도사가", "이 사람이",
    "노부", "이 도사가", "이 늙은 도인이",
    "운학이",
)


# ───── 호명 (사용자 부름) ─────
USER_ADDRESS = (
    "그대", "자네", "그대여", "자네여",
    "손님", "객", "이 사람",
)


# ───── 사극 종결 어미 ─────
SAJUK_ENDINGS = (
    "하시게", "하시게나", "하시구려",
    "이로다", "이로세", "이로구먼", "이로구나",
    "이옵니다", "이오", "이외다",
    "라네", "라오", "라하리",
    "구먼", "그려", "이여",
)


# ───── 형태 묘사 어휘 (운명 매핑 X) ─────
SHAPE_DESCRIPTORS = (
    # 빛·결
    "환하다", "고르다", "은은하다", "옅다",
    "맑다", "흐리다", "또렷하다", "흐릿하다",
    # 두께·너비
    "두텁다", "얇다", "넓다", "좁다",
    "풍성하다", "단정하다",
    # 흐름
    "흐름이 단정하다", "결이 맑다", "기색이 고르다",
    "윤곽이 또렷하다", "선이 흐리지 않다",
)


# ───── 12궁 학파 호명 (운명 매핑 X, 영역 명시만) ─────
PALACE_LABELS_KO = {
    "myeong": "명궁(命宮)",
    "gwanrok": "관록궁(官祿宮)",
    "jaebaek": "재백궁(財帛宮)",
    "jeontaek": "전택궁(田宅宮)",
    "hyeongje": "형제궁(兄弟宮)",
    "nobok": "노복궁(奴僕宮)",
    "cheocheop": "처첩궁(妻妾宮)",
    "janyeo": "자녀궁(子女宮)",
    "jilek": "질액궁(疾厄宮)",
    "cheoni": "천이궁(遷移宮)",
    "bokdeok": "복덕궁(福德宮)",
    "bumo": "부모궁(父母宮)",
}


# ───── 사극 분위기 표현 (감탄·전환) ─────
SAJUK_INTERJECTIONS = (
    "허허", "허허허", "음", "허",
    "글쎄", "그러고 보니",
    "이 늙은이의 한 마디 —",
    "본 자리에서 짚어보매",
)


# ───── 사극 전환 어귀 (단정 회피 표현) ─────
SAJUK_TRANSITIONS = (
    "이렇게 보임이로다",
    "이렇다 하겠노라",
    "결이 그러하니",
    "흐름이 이러하니",
    "내 짚어보매",
    "이 늙은이의 눈으로는",
    "단정할 일은 아니나",
    "예언이 아닌 결을 짚어보매",
)


# ───── 사극 비교 어휘 (ADR-204에 활용) ─────
COMPARISON_PHRASES = (
    "한국 사람 가운데",
    "조선 사람의 평균에 비하면",
    "지금 시대 사람들과 견주어",
    "예부터 전하는 표본과 견주매",
)


# 어휘 카테고리 인덱스 — 운영·테스트용
ALL_CATEGORIES: dict[str, tuple[str, ...]] = {
    "self_references": SELF_REFERENCES,
    "user_address": USER_ADDRESS,
    "sajuk_endings": SAJUK_ENDINGS,
    "shape_descriptors": SHAPE_DESCRIPTORS,
    "sajuk_interjections": SAJUK_INTERJECTIONS,
    "sajuk_transitions": SAJUK_TRANSITIONS,
    "comparison_phrases": COMPARISON_PHRASES,
}


def total_vocab_count() -> int:
    """전체 어휘 수 (12궁 라벨 제외, 분류 어휘만)."""
    return sum(len(v) for v in ALL_CATEGORIES.values())


def get_category(name: str) -> tuple[str, ...]:
    """카테고리 어휘 반환. 알 수 없는 이름 → 빈 튜플."""
    return ALL_CATEGORIES.get(name, ())


def render_for_system_prompt() -> str:
    """Stage 2 LLM 시스템 프롬프트 주입용 어휘 가이드 텍스트.

    LLM이 강제 사용 X — 자연스러운 사극 어조 참고용. ADR-171 fate_assertion
    사전과 정합 (본 어휘는 모두 통과).
    """
    lines = [
        "[운학 도사 사극 어휘 가이드 — ADR-203]",
        "자기지칭: " + " / ".join(SELF_REFERENCES),
        "호명: " + " / ".join(USER_ADDRESS),
        "감탄: " + " / ".join(SAJUK_INTERJECTIONS),
        "전환: " + " / ".join(SAJUK_TRANSITIONS),
        "형태 묘사: " + " / ".join(SHAPE_DESCRIPTORS[:10]),  # 일부만
        "종결: " + " / ".join(SAJUK_ENDINGS[:10]),
        "(위 어휘는 참고용 — 자연스러운 사극 어조 작문이 우선)",
    ]
    return "\n".join(lines)
