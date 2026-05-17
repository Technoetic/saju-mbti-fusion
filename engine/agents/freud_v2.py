"""ADR-023 A8 Freud v2 — 고전 정신분석 4기제 결정론 매핑 + 보편 상징.

보고서 §4 + §5 본문화:
  · 응축(Verdichtung) · 전치(Verschiebung) · 상징화(Symbolisierung) · 이차 가공(sekundäre Bearbeitung)
  · 6 보편 상징 (집·부모·왕족·물·여행·의복 벗기) + 한국어 표준판 ISBN
  · DEFAULT_DISCLAIMERS 강제 (ADR-006/010/014 정합)

설계 (CLAUDE.md §0 + ADR-021 B6 패턴 정합):
  · 결정론 4기제 검출 + 보편 상징 매핑 (LLM 호출 0)
  · v1 freud_persona.py와 별개 모듈 — v1은 LLM 페르소나, v2는 결정론 엔진
  · ADR-006 성환원 절대 금지 + ADR-010 학파 명시 의무

학술 근거 (한국어 표준판 KCI 등재 출판사):
  · 열린책들 『꿈의 해석』 (김인순 역) ISBN 9788932920528
  · 열린책들 『정신분석 강의』 (임홍빈 역) ISBN 9788932920498
  · 서울대학교출판부 『꿈의 해석』 (조대경 역) ISBN 9788952116291

ADR-021 B6 DreamNet v4 본문화 직후 본 ADR-023 = ADR-017 절차 4차 본문화.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ─────────────────────────── 4기제 결정론 검출 규칙 (보고서 §4 YAML) ───────────────────────────


@dataclass(frozen=True)
class MechanismRule:
    """단일 꿈 작업 기제 (Dream-Work) 검출 규칙.

    Attributes:
        mechanism: 기제명 (응축·전치·상징화·이차가공).
        latin: 영문 원어.
        detection_keywords: 한국어 텍스트 패턴 (substring 매칭).
        description: 객관 형태 설명 (학파 도그마 회피).
        freud_source: Freud 원전 인용 (한국어 표준판 ISBN).
    """

    mechanism: str
    latin: str
    detection_keywords: tuple[str, ...]
    description: str
    freud_source: str


# 보고서 §4 라인 78-145 YAML 본문화
DREAM_WORK_RULES: tuple[MechanismRule, ...] = (
    MechanismRule(
        mechanism="응축",
        latin="Verdichtung (Condensation)",
        detection_keywords=(
            "같은데 다른",
            "여러 명이 하나로",
            "혼합",
            "동시에 여러",
            "한 사람이지만",
            "얼굴은 X인데",
        ),
        description="여러 인물·시공간·상징이 한 장면 또는 한 인물로 결합되어 압축된 표상.",
        freud_source="열린책들 『꿈의 해석』 §6장 A절 (ISBN 9788932920528)",
    ),
    MechanismRule(
        mechanism="전치",
        latin="Verschiebung (Displacement)",
        detection_keywords=(
            "사소한 것에",
            "이상하게 신경 쓰여",
            "별것 아닌데",
            "왜 그런지",
            "초점이",
            "엉뚱한",
        ),
        description="중요한 잠재 의미가 사소한 외현 표상으로 옮겨지는 강조의 전치.",
        freud_source="열린책들 『꿈의 해석』 §6장 B절 (ISBN 9788932920528)",
    ),
    MechanismRule(
        mechanism="상징화",
        latin="Symbolisierung (Symbolization)",
        detection_keywords=(
            "집",
            "부모",
            "왕",
            "물",
            "여행",
            "의복",
            "벌거벗",
            "기차",
            "바다",
        ),
        description="추상 관념이 구체 이미지로 변환되어 표상되는 과정.",
        freud_source="열린책들 『정신분석 강의』 10강 (ISBN 9788932920498)",
    ),
    MechanismRule(
        mechanism="이차가공",
        latin="sekundäre Bearbeitung (Secondary Revision)",
        detection_keywords=(
            "이상하지만 말이 되는",
            "줄거리가 있는",
            "마치 영화처럼",
            "전체가 연결",
            "이야기로",
        ),
        description="혼란한 꿈 재료가 자아의 검열로 일관된 서사 형태로 재구성되는 과정.",
        freud_source="열린책들 『꿈의 해석』 §6장 I절 (ISBN 9788932920528)",
    ),
)


# ─────────────────────────── 보편 상징 매핑 (보고서 §5 라인 153-161) ───────────────────────────


@dataclass(frozen=True)
class UniversalSymbol:
    """Freud 보편 상징 결정론 매핑.

    Attributes:
        symbol: 외현 상징 한국어.
        latin: 영문 원어.
        latent_meaning: 잠재 의미 (다중 해석 가능).
        korean_source: 한국어 표준판 출처.
        isbn: 한국 ISBN.
        output_format: 사용자 출력 시 가능성 다중 제시 포맷 (ADR-006 준수).
    """

    symbol: str
    latin: str
    latent_meaning: str
    korean_source: str
    isbn: str
    output_format: str


UNIVERSAL_SYMBOLS: dict[str, UniversalSymbol] = {
    "집": UniversalSymbol(
        symbol="집",
        latin="House",
        latent_meaning="인간의 신체 전체, 내면의 자아",
        korean_source="열린책들 『정신분석 강의』 10강, p.217 (임홍빈 역)",
        isbn="9788932920498",
        output_format="집은 종종 자신만의 내면 공간이나 고유한 자아, 혹은 신체의 확장된 은유로 해석될 수 있습니다.",
    ),
    "부모": UniversalSymbol(
        symbol="부모",
        latin="Parents",
        latent_meaning="초자아(Superego), 내면화된 도덕률, 권위자",
        korean_source="열린책들 『꿈의 해석』 전집 4 개정판 (김인순 역)",
        isbn="9788932920528",
        output_format="꿈속의 부모님은 실제 부모님을 의미하기보다, 현실 사회의 권위·규칙·내면화된 양심(초자아)을 상징할 가능성이 높습니다.",
    ),
    "왕족": UniversalSymbol(
        symbol="왕족",
        latin="Royalty/President",
        latent_meaning="실제 부모에 대한 유아기적 거대 표상",
        korean_source="서울대학교출판부 『꿈의 해석』 (조대경 역)",
        isbn="9788952116291",
        output_format="왕·여왕·대통령 등 권위적 인물은 어린 시절 부모님이 자신에게 차지했던 절대적 영향력을 상징적으로 보여주는 것일 수 있습니다.",
    ),
    "물": UniversalSymbol(
        symbol="물",
        latin="Water",
        latent_meaning="출생·생명의 기원·자궁·무의식의 심연",
        korean_source="열린책들 『정신분석 강의』 10강 (임홍빈 역)",
        isbn="9788932920498",
        output_format="물에 빠지거나 물을 마주하는 이미지는 근원적인 편안함(혹은 불안감), 새로운 시작(출생), 억압된 감정의 방출 등 다양한 해석이 가능합니다.",
    ),
    "여행": UniversalSymbol(
        symbol="여행",
        latin="Journey/Travel",
        latent_meaning="죽음의 은유 또는 중대한 삶의 단계적 전환",
        korean_source="열린책들 『꿈의 해석』 전집 4 개정판 (김인순 역)",
        isbn="9788932920528",
        output_format="긴 여행을 떠나거나 기차를 타는 행위는 무의식적으로 삶의 중요한 전환기를 맞이했거나, 과거의 한 시절과의 이별을 상징하는 경우가 많습니다.",
    ),
    "벌거벗음": UniversalSymbol(
        symbol="벌거벗음",
        latin="Undressing",
        latent_meaning="노출에 대한 두려움, 억압된 유아기적 자유 욕동",
        korean_source="서울대학교출판부 『꿈의 해석』 (조대경 역)",
        isbn="9788952116291",
        output_format="벌거벗고 있어 수치심을 느끼는 것은 사회적 체면 뒤에 숨겨진 진솔한 모습을 드러내는 것에 대한 두려움이거나, 사회적 규범에서 벗어나고픈 내면의 갈등일 수 있습니다.",
    ),
}


# ─────────────────────────── ADR-006/010/014 면책 (보고서 §7) ───────────────────────────

# Blacklist (절대 금지) — 보고서 §7 라인 170-181
FORBIDDEN_OUTPUT_PATTERNS: tuple[str, ...] = (
    "당신은 [질병명]입니다",
    "확실히 [예언]",
    "반드시 일어납니다",
    "운명입니다",
    "지팡이는 남근",
    "긴 물체는 남근",
    "동굴은 자궁",
    "구멍은 자궁",
)

# DEFAULT_DISCLAIMERS (ADR-021 B6 패턴 정합)
DEFAULT_DISCLAIMERS: list[str] = [
    "본 결과는 Freud 정신분석 학파의 학설이며 임상 진단·미래 예언이 아닙니다.",
    "꿈 작업 기제(응축·전치·상징화·이차 가공)는 가능성 다중 해석으로 제시됩니다.",
    "다른 학파(Jung 분석심리학·Hobson 활성화종합·Solms SEEKING)는 다르게 해석할 수 있습니다.",
]


# ─────────────────────────── 결과 dataclass ───────────────────────────


@dataclass(frozen=True)
class FreudV2Result:
    """A8 Freud v2 결정론 분석 결과 (ADR-023).

    Attributes:
        detected_mechanisms: 검출된 꿈 작업 기제 목록.
        matched_symbols: 검출된 보편 상징 목록.
        disclaimers: ADR-006/010/014 강제 면책 (3건).
        school: 명시 학파명 ("Freud 정신분석").
        agent: 에이전트 ID.
    """

    detected_mechanisms: list[dict[str, str]] = field(default_factory=list)
    matched_symbols: list[dict[str, str]] = field(default_factory=list)
    disclaimers: list[str] = field(default_factory=list)
    school: str = "Freud 정신분석"
    agent: str = "A8_v2"

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "school": self.school,
            "detected_mechanisms": self.detected_mechanisms,
            "matched_symbols": self.matched_symbols,
            "disclaimers": self.disclaimers,
        }


# ─────────────────────────── 핵심 함수 ───────────────────────────


def detect_freud_mechanisms(dream_text: str) -> list[dict[str, str]]:
    """꿈 텍스트 → 검출된 4기제 목록 (결정론).

    각 MechanismRule의 detection_keywords substring 매칭. 학파 도그마 표현
    절대 미사용 — 객관 형태 라벨만 반환.
    """
    if not dream_text or not isinstance(dream_text, str):
        return []

    detected: list[dict[str, str]] = []
    for rule in DREAM_WORK_RULES:
        for kw in rule.detection_keywords:
            if kw in dream_text:
                detected.append({
                    "mechanism": rule.mechanism,
                    "latin": rule.latin,
                    "matched_keyword": kw,
                    "description": rule.description,
                    "freud_source": rule.freud_source,
                })
                break  # 같은 기제는 1회만
    return detected


def detect_universal_symbols(dream_text: str) -> list[dict[str, str]]:
    """꿈 텍스트 → 검출된 보편 상징 목록 (결정론).

    UNIVERSAL_SYMBOLS substring 매칭. 가능성 다중 제시 포맷 반환
    (ADR-006 준수).
    """
    if not dream_text or not isinstance(dream_text, str):
        return []

    detected: list[dict[str, str]] = []
    for key, sym in UNIVERSAL_SYMBOLS.items():
        # symbol 자체 또는 latin 영문 포함 시 (한국어 텍스트 기준)
        if key in dream_text or sym.symbol in dream_text:
            detected.append({
                "symbol": sym.symbol,
                "latin": sym.latin,
                "latent_meaning": sym.latent_meaning,
                "korean_source": sym.korean_source,
                "isbn": sym.isbn,
                "output_format": sym.output_format,
            })
    return detected


def analyze_freud_v2(dream_text: str) -> FreudV2Result:
    """A8 Freud v2 결정론 분석 (보고서 §4 + §5 통합).

    Args:
        dream_text: 꿈 보고 한국어 텍스트.

    Returns:
        FreudV2Result — 4기제 검출 + 보편 상징 + DEFAULT_DISCLAIMERS.

    설계 (ADR-006/010/014 정합):
        · LLM 호출 0 (결정론)
        · disclaimers 자동 포함 (학파 명시 + 의료 단정 금지 + 다중 해석)
        · 성환원 절대 금지 (FORBIDDEN_OUTPUT_PATTERNS 회피)
    """
    mechanisms = detect_freud_mechanisms(dream_text)
    symbols = detect_universal_symbols(dream_text)

    return FreudV2Result(
        detected_mechanisms=mechanisms,
        matched_symbols=symbols,
        disclaimers=list(DEFAULT_DISCLAIMERS),
        school="Freud 정신분석",
        agent="A8_v2",
    )


def has_forbidden_output(text: str) -> bool:
    """사용자 출력 텍스트에 금지 패턴 포함 여부 (output filter).

    LLM 페르소나(freud_persona.py)가 생성한 텍스트를 사후 검증할 때 사용.
    True 반환 시 safety override (안전 기본 응답으로 대체) 의무.
    """
    if not text or not isinstance(text, str):
        return False

    for pattern in FORBIDDEN_OUTPUT_PATTERNS:
        if pattern in text:
            return True
    return False


__all__ = [
    "DREAM_WORK_RULES",
    "UNIVERSAL_SYMBOLS",
    "DEFAULT_DISCLAIMERS",
    "FORBIDDEN_OUTPUT_PATTERNS",
    "MechanismRule",
    "UniversalSymbol",
    "FreudV2Result",
    "detect_freud_mechanisms",
    "detect_universal_symbols",
    "analyze_freud_v2",
    "has_forbidden_output",
]
