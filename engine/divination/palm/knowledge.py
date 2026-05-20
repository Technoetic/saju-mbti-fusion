"""ADR-066 — 손금 학파 메타데이터 + 보조선 임계값 (Stage 2 인용 출처).

본 모듈은 ADR-063 (face/knowledge.py) 패턴 정합. ADR-030 (palm scoring 4대선)
이후 보조선 (운명선·태양선·수성선·결혼선) 학파 분리 결정론 분류 영속화.

원칙 (ADR-002·006·010·015 정합):
  · 서양 학파 4 (Cheiro·Benham·Saint-Germain·Hutchinson) — 옵션 A 디폴트
  · 동양 학파 2 (마의상법·동의보감) — 옵션 B 명시 채택
  · 운명·재물·결혼 단정 매핑 차단 (형태명 라벨만)
  · 사상체질 인용 X (별도 도메인)

출처:
  · Cheiro "Language of the Hand" (1900) — Archive.org public domain
  · Benham "Laws of Scientific Hand Reading" (1901) — Archive.org
  · Saint-Germain "Practice of Palmistry" (1897) — Archive.org
  · 동의보감 호구삼관맥법 — mediclassics.kr
"""

from __future__ import annotations

from dataclasses import dataclass


# ─────────────────────────── 학파 메타데이터 ───────────────────────────

@dataclass(frozen=True)
class PalmSchool:
    """손금 학파 메타데이터.

    Attributes:
        key: 내부 식별자 (kebab-case)
        name_full: 저자 또는 학파 정식 명칭
        name_short: 통용 명칭
        tradition: "western" | "eastern"
        publication_year: 대표 저서 출판 연도
        primary_work: 대표 저서 명
        primary_source_url: 1차 출처 URL (검증 통과)
        philosophical_core: 철학적 특징 한 줄
        adr_002_note: 학파 차이 명시 (단일 학파 강요 X 정신)
    """
    key: str
    name_full: str
    name_short: str
    tradition: str
    publication_year: int
    primary_work: str
    primary_source_url: str
    philosophical_core: str
    adr_002_note: str


# 서양 4 학파 + 동양 2 학파 (Phase B 출처 검증 통과)
PALM_SCHOOLS: tuple[PalmSchool, ...] = (
    PalmSchool(
        key="cheiro",
        name_full="William John Warner",
        name_short="Cheiro",
        tradition="western",
        publication_year=1900,
        primary_work="Language of the Hand",
        primary_source_url="https://archive.org/details/cheiroslanguageo00hamo",
        philosophical_core="형이상학·점성술 결합 — 손금 라벨링 대중화",
        adr_002_note="단일 정통론 강요 X — Benham 신경생리학 기반과 옵션 병행",
    ),
    PalmSchool(
        key="benham",
        name_full="William G. Benham",
        name_short="Benham",
        tradition="western",
        publication_year=1901,
        primary_work="Laws of Scientific Hand Reading",
        primary_source_url="https://archive.org/details/isbn_8187077328",
        philosophical_core="신경생리학·해부학 기반 — 정량 임계값 (linearity 등) 표준",
        adr_002_note="본 시스템 보조선 임계값 1차 출처 — Cheiro 형이상학과 차별",
    ),
    PalmSchool(
        key="saint-germain",
        name_full="Comte de Saint-Germain",
        name_short="Saint-Germain",
        tradition="western",
        publication_year=1897,
        primary_work="Practice of Palmistry",
        primary_source_url="https://archive.org/details/practicalpalmist00sain",
        philosophical_core="위치적 규격 — 결혼선·자녀선 등 보조선 위치 기준 표준",
        adr_002_note="결혼선 위치 규격 옵션 — Benham 기하학과 병행",
    ),
    PalmSchool(
        key="hutchinson",
        name_full="Beryl Hutchinson",
        name_short="Hutchinson",
        tradition="western",
        publication_year=1967,
        primary_work="Your Life in Your Hands",
        primary_source_url="https://en.wikipedia.org/wiki/Society_for_the_Study_of_Physiological_Patterns",
        philosophical_core="의료수성학 (medical chirology) — 단 본 시스템 의료 진단 X",
        adr_002_note="의료 진단 인용 차단 — 본 시스템 ADR-006 정합 의무",
    ),
    PalmSchool(
        key="mauisangbeop",
        name_full="마의상법(麻衣相法) 손금 분과",
        name_short="마의상법",
        tradition="eastern",
        publication_year=1100,
        primary_work="麻衣相法 (12紋 분류)",
        primary_source_url="https://encykorea.aks.ac.kr/Article/E0004873",
        philosophical_core="12紋 형태 분류 — 옥주문(玉柱紋) 등 (운명선 동양 명칭)",
        adr_002_note="서양 운명선 라벨과 동양 옥주문 명칭 옵션 병행",
    ),
    PalmSchool(
        key="donguibogam",
        name_full="동의보감(東醫寶鑑) 호구삼관맥법",
        name_short="동의보감",
        tradition="eastern",
        publication_year=1613,
        primary_work="東醫寶鑑 잡병편",
        primary_source_url="https://mediclassics.kr/books/8",
        philosophical_core="손가락 분과 — 의료 영역이나 본 시스템 분류 라벨만 인용",
        adr_002_note="의료 진단 채택 X — 형태명 라벨만 (ADR-006 정합)",
    ),
)


# ─────────────────────────── 보조선 임계값 ───────────────────────────

# 운명선 (Fate Line / 옥주문) — Benham 1901 직선성 임계
FATE_LINE_LINEARITY_THRESHOLD = 0.85  # ≥ 0.85 → straight, < 0.85 → curved

# 태양선 (Apollo Line) — Cheiro 1900 + Benham
SUN_LINE_INTENSITY_MIN_PCT = 15.0  # DoG 엣지 픽셀 강도 %
SUN_LINE_LENGTH_MIN_CM = 1.0  # 최소 연속 길이

# 수성선 (Mercury Line / 재물선) — Benham 1901
MERCURY_LINE_LINEARITY_THRESHOLD = 0.80
MERCURY_LINE_MAX_INTERRUPTIONS = 1  # ≤ 1 → continuous, ≥ 2 → fragmented

# 결혼선 (Marriage Line) — Saint-Germain 1897
MARRIAGE_LINE_MIN_LENGTH_CM = 0.5
MARRIAGE_LINE_FORKING_RADIUS_PX = 5  # 끝단 갈라짐 감지 반경


# ─────────────────────────── 형태 분류 라벨 ───────────────────────────

# 운명선 (★ fate_mapping 필드 부재 — ADR-006 운명 단정 차단)
FATE_LINE_STRAIGHT = "곧은 운명선"     # Benham linearity ≥ 0.85
FATE_LINE_CURVED = "굽은 운명선"        # linearity < 0.85
FATE_LINE_ABSENT = "운명선 부재"         # 검출 실패

# 태양선
SUN_LINE_CLEAR = "선명한 태양선"        # intensity ≥ 15% + length ≥ 1cm
SUN_LINE_FAINT = "옅은 태양선"           # intensity < 15% 또는 length < 1cm
SUN_LINE_ABSENT = "태양선 부재"

# 수성선
MERCURY_LINE_CONTINUOUS = "이어진 수성선"   # linearity ≥ 0.80, interrupt ≤ 1
MERCURY_LINE_FRAGMENTED = "끊긴 수성선"     # interrupt ≥ 2
MERCURY_LINE_ABSENT = "수성선 부재"

# 결혼선 (★ 이혼·바람기 매핑 차단 — ADR-006 최고 보안)
MARRIAGE_LINE_SINGLE_CLEAR = "한 줄 결혼선"   # 1개 + length ≥ 0.5cm
MARRIAGE_LINE_MULTIPLE = "여러 줄 결혼선"    # ≥ 2개
MARRIAGE_LINE_FORKED = "끝이 갈라진 결혼선"  # forking_radius_px 내 분기
MARRIAGE_LINE_ABSENT = "결혼선 부재"


# ─────────────────────────── 결과 dataclass (운명 매핑 필드 부재) ───────────────────────────

@dataclass(frozen=True)
class FateLineResult:
    """운명선 형태 분류 — ADR-006 fate_mapping 필드 의도적 부재."""
    shape_type: str
    linearity_ratio: float
    source_school: str
    source_url: str
    disclaimer: str
    # 의도적 부재: fate_mapping — 직업 성공 매핑 X


@dataclass(frozen=True)
class SunLineResult:
    """태양선 형태 분류."""
    shape_type: str
    intensity_pct: float
    length_cm: float
    source_school: str
    source_url: str
    disclaimer: str


@dataclass(frozen=True)
class MercuryLineResult:
    """수성선 형태 분류 — '재물복' 매핑 차단."""
    shape_type: str
    linearity_ratio: float
    interruption_count: int
    source_school: str
    source_url: str
    disclaimer: str
    # 의도적 부재: wealth_mapping — '재물복' X


@dataclass(frozen=True)
class MarriageLineResult:
    """결혼선 형태 분류 — ★ '이혼 위험·바람기' 매핑 차단 최고 보안."""
    shape_type: str
    line_count: int
    has_forking: bool
    source_school: str
    source_url: str
    disclaimer: str
    # 의도적 부재: marriage_outcome_mapping — '이혼 위험' X (윤리·법적)


# ─────────────────────────── 분류 함수 ───────────────────────────

_BENHAM_URL = "https://archive.org/details/isbn_8187077328"
_CHEIRO_URL = "https://archive.org/details/cheiroslanguageo00hamo"
_SAINT_GERMAIN_URL = "https://archive.org/details/practicalpalmist00sain"

_DISCLAIMER_BASE = (
    "본 분류는 시각 형태 측정 결과로, 운명·길흉·관운 인과 매핑 X. "
    "사상체질·태음인 인용 X (ADR-006 정신). "
    "출처 라이브 검증 통과 학파 (Cheiro·Benham·Saint-Germain Archive.org public domain)."
)


def classify_fate_line(linearity_ratio: float | None) -> FateLineResult | None:
    """운명선 형태 분류 (Benham 1901 linearity 0.85 임계).

    Args:
        linearity_ratio: 직선성 비율 (0.0~1.0). None이면 검출 실패.
    """
    if linearity_ratio is None:
        return FateLineResult(
            shape_type=FATE_LINE_ABSENT,
            linearity_ratio=0.0,
            source_school="benham",
            source_url=_BENHAM_URL,
            disclaimer=_DISCLAIMER_BASE,
        )
    if not isinstance(linearity_ratio, (int, float)):
        return None
    linearity_ratio = float(max(0.0, min(1.0, linearity_ratio)))
    shape = FATE_LINE_STRAIGHT if linearity_ratio >= FATE_LINE_LINEARITY_THRESHOLD else FATE_LINE_CURVED
    return FateLineResult(
        shape_type=shape,
        linearity_ratio=round(linearity_ratio, 3),
        source_school="benham",
        source_url=_BENHAM_URL,
        disclaimer=_DISCLAIMER_BASE,
    )


def classify_sun_line(
    intensity_pct: float | None,
    length_cm: float | None,
) -> SunLineResult | None:
    """태양선 형태 분류 (Cheiro 1900 + Benham)."""
    if intensity_pct is None or length_cm is None:
        return SunLineResult(
            shape_type=SUN_LINE_ABSENT,
            intensity_pct=0.0,
            length_cm=0.0,
            source_school="cheiro",
            source_url=_CHEIRO_URL,
            disclaimer=_DISCLAIMER_BASE,
        )
    if not isinstance(intensity_pct, (int, float)) or not isinstance(length_cm, (int, float)):
        return None
    intensity_pct = float(max(0.0, intensity_pct))
    length_cm = float(max(0.0, length_cm))

    if intensity_pct >= SUN_LINE_INTENSITY_MIN_PCT and length_cm >= SUN_LINE_LENGTH_MIN_CM:
        shape = SUN_LINE_CLEAR
    else:
        shape = SUN_LINE_FAINT

    return SunLineResult(
        shape_type=shape,
        intensity_pct=round(intensity_pct, 2),
        length_cm=round(length_cm, 2),
        source_school="cheiro",
        source_url=_CHEIRO_URL,
        disclaimer=_DISCLAIMER_BASE,
    )


def classify_mercury_line(
    linearity_ratio: float | None,
    interruption_count: int | None,
) -> MercuryLineResult | None:
    """수성선 형태 분류 (Benham 1901). '재물복' 매핑 X."""
    if linearity_ratio is None and interruption_count is None:
        return MercuryLineResult(
            shape_type=MERCURY_LINE_ABSENT,
            linearity_ratio=0.0,
            interruption_count=0,
            source_school="benham",
            source_url=_BENHAM_URL,
            disclaimer=_DISCLAIMER_BASE,
        )
    if not isinstance(linearity_ratio, (int, float)) or not isinstance(interruption_count, int):
        return None
    linearity_ratio = float(max(0.0, min(1.0, linearity_ratio)))
    interruption_count = max(0, interruption_count)

    if (
        linearity_ratio >= MERCURY_LINE_LINEARITY_THRESHOLD
        and interruption_count <= MERCURY_LINE_MAX_INTERRUPTIONS
    ):
        shape = MERCURY_LINE_CONTINUOUS
    else:
        shape = MERCURY_LINE_FRAGMENTED

    return MercuryLineResult(
        shape_type=shape,
        linearity_ratio=round(linearity_ratio, 3),
        interruption_count=interruption_count,
        source_school="benham",
        source_url=_BENHAM_URL,
        disclaimer=_DISCLAIMER_BASE,
    )


def classify_marriage_line(
    line_count: int | None,
    length_cm: float | None,
    has_forking: bool | None = None,
) -> MarriageLineResult | None:
    """★ 결혼선 형태 분류 (Saint-Germain 1897). 이혼·바람기 매핑 차단 최고 보안."""
    if line_count is None or line_count == 0:
        return MarriageLineResult(
            shape_type=MARRIAGE_LINE_ABSENT,
            line_count=0,
            has_forking=False,
            source_school="saint-germain",
            source_url=_SAINT_GERMAIN_URL,
            disclaimer=_DISCLAIMER_BASE,
        )
    if not isinstance(line_count, int):
        return None

    forking = bool(has_forking) if has_forking is not None else False

    # 분류 우선순위: forking (있으면) > multiple (2개+) > single_clear
    if forking and line_count >= 1:
        shape = MARRIAGE_LINE_FORKED
    elif line_count >= 2:
        shape = MARRIAGE_LINE_MULTIPLE
    elif line_count == 1 and isinstance(length_cm, (int, float)) and length_cm >= MARRIAGE_LINE_MIN_LENGTH_CM:
        shape = MARRIAGE_LINE_SINGLE_CLEAR
    else:
        shape = MARRIAGE_LINE_SINGLE_CLEAR  # 단일선, 길이 미명시

    return MarriageLineResult(
        shape_type=shape,
        line_count=line_count,
        has_forking=forking,
        source_school="saint-germain",
        source_url=_SAINT_GERMAIN_URL,
        disclaimer=_DISCLAIMER_BASE,
    )


# ─────────────────────────── 헬퍼 ───────────────────────────

def get_school_by_key(key: str) -> PalmSchool | None:
    """학파 메타 조회."""
    for s in PALM_SCHOOLS:
        if s.key == key:
            return s
    return None


def format_schools_metadata_for_prompt() -> str:
    """Stage 2 시스템 프롬프트 주입용 학파 메타 텍스트."""
    lines = ["[손금 학파 메타 — 본 시스템 영속 출처에서만 인용]"]
    for s in PALM_SCHOOLS:
        lines.append(f"  · {s.name_short} ({s.tradition}, {s.publication_year}): {s.philosophical_core}")
    lines.append(
        "[필수 안전 장치 — ADR-006] 학파 명칭·형태 라벨만 사용. "
        "운명·재물·결혼·이혼·바람기 단정 절대 금지. 사상체질 인용 금지."
    )
    return "\n".join(lines)


__all__ = [
    "PalmSchool",
    "PALM_SCHOOLS",
    "FATE_LINE_LINEARITY_THRESHOLD",
    "SUN_LINE_INTENSITY_MIN_PCT",
    "SUN_LINE_LENGTH_MIN_CM",
    "MERCURY_LINE_LINEARITY_THRESHOLD",
    "MERCURY_LINE_MAX_INTERRUPTIONS",
    "MARRIAGE_LINE_MIN_LENGTH_CM",
    "MARRIAGE_LINE_FORKING_RADIUS_PX",
    "FATE_LINE_STRAIGHT", "FATE_LINE_CURVED", "FATE_LINE_ABSENT",
    "SUN_LINE_CLEAR", "SUN_LINE_FAINT", "SUN_LINE_ABSENT",
    "MERCURY_LINE_CONTINUOUS", "MERCURY_LINE_FRAGMENTED", "MERCURY_LINE_ABSENT",
    "MARRIAGE_LINE_SINGLE_CLEAR", "MARRIAGE_LINE_MULTIPLE",
    "MARRIAGE_LINE_FORKED", "MARRIAGE_LINE_ABSENT",
    "FateLineResult", "SunLineResult", "MercuryLineResult", "MarriageLineResult",
    "classify_fate_line", "classify_sun_line", "classify_mercury_line", "classify_marriage_line",
    "get_school_by_key", "format_schools_metadata_for_prompt",
]
