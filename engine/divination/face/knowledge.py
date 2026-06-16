"""ADR-063 — 관상학 통설 지식 DB (Stage 2 인용 출처).

본 모듈은 ADR-005 Stage 2 (Gemini 자연어 풀이)의 학파 통설 인용 출처를
본 시스템 코드 내 영속화. Gemini 사전학습 운명 매핑 사용 차단 + 본 시스템
검증 출처에서만 학파 명칭·영역 정의 인용 가능.

원칙 (ADR-002·006·010 정합):
  · 학파 차이 명시 (마의상법·유장상법·달마상법·신상전편 + 한국 통설 병행)
  · 운명·관운·재물복 단정 차단 (영역명·형태 정의만)
  · 모든 항목 출처 URL + 라이브 검증 가능 메타데이터
  · 한국 고유 통설은 옵션 B 명시 채택 패턴 (ADR-015)

출처:
  · 보고서 "한국 전통 관상학 통설 지식 DB" (2026-05-20)
  · 한국민족문화대백과 (encykorea.aks.ac.kr) 200 OK 검증
  · DBpia 마의상법 번역 논문 (NODE11235666)
  · Aladin 마의상법 (ISBN 9788970300412)
  · Kyobobook 유장상법 (ISBN S000001863597)
"""

from __future__ import annotations

from dataclasses import dataclass


# ─────────────────────────── 학파 메타데이터 ───────────────────────────

@dataclass(frozen=True)
class PhysiognomySchool:
    """관상학 학파 메타데이터.

    Attributes:
        key: 내부 식별자 (kebab-case)
        name_ko: 한국어 명칭
        name_hanja: 한자 명칭
        author: 저자/편자 (한국어)
        compilation_era: 편찬 시대
        philosophical_core: 철학적 특징 한 줄
        primary_source_url: 1차 출처 URL (검증 통과)
        adr_002_note: 학파 차이 명시 (단일 학파 강요 X 정신)
    """
    key: str
    name_ko: str
    name_hanja: str
    author: str
    compilation_era: str
    philosophical_core: str
    primary_source_url: str
    adr_002_note: str


# 4 학파 메타데이터 (보고서 §5.12-5.15, Phase B 출처 검증 통과)
PHYSIOGNOMY_SCHOOLS: tuple[PhysiognomySchool, ...] = (
    PhysiognomySchool(
        key="maui",
        name_ko="마의상법",
        name_hanja="麻衣相法",
        author="마의도자(麻衣道者) — 송대 추정",
        compilation_era="송대 (10~13세기)",
        philosophical_core="물상론 — 동물 비유 중심 (호상·용상·구상 등)",
        primary_source_url="https://www.aladin.co.kr/shop/wproduct.aspx?ItemId=7253384",
        adr_002_note="한국 통설(하정 우위·눈 5할)과 차이 있음 — 옵션 병행 의무",
    ),
    PhysiognomySchool(
        key="yujang",
        name_ko="유장상법",
        name_hanja="柳莊相法",
        author="원충철(元忠徹) — 명대",
        compilation_era="명대 (14~17세기)",
        philosophical_core="유년운기도 — 음양오행+경락+12궁 정밀 시계열",
        primary_source_url="https://product.kyobobook.co.kr/detail/S000001863597",
        adr_002_note="유년운기 시간 매핑은 본 시스템 ADR-006 위반 — 명칭만 인용",
    ),
    PhysiognomySchool(
        key="dalma",
        name_ko="달마상법",
        name_hanja="達磨相法",
        author="달마(達磨) — 양대 인도 승려",
        compilation_era="6세기",
        philosophical_core="심상(心相) 철학 — 외형보다 내면 중시",
        primary_source_url="https://encykorea.aks.ac.kr/Article/E0004873",
        adr_002_note="물질 형태만으로 판단 불가 명시 — ADR-006 정신 정합 학파",
    ),
    PhysiognomySchool(
        key="sinsang",
        name_ko="신상전편",
        name_hanja="神相全編",
        author="원공(袁珙) 편 — 명대",
        compilation_era="명대 (14~17세기)",
        philosophical_core="도해 집대성 — 관상 그림 표본 정리",
        primary_source_url="https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE11235666",
        adr_002_note="도해는 시각 참고만, 운명 매핑 X",
    ),
)


# ─────────────────────────── 삼정 체계 (ADR-015 옵션 병행) ───────────────────────────

@dataclass(frozen=True)
class SamjeongRegion:
    """삼정 영역 — 학파 옵션 병행 (한국 vs 중국)."""
    key: str
    label_ko: str
    label_hanja: str
    anatomical_region: str
    chinese_school_emphasis: str  # 중국 학파 (옵션 A)
    korean_school_emphasis: str   # 한국 통설 (옵션 B)


SAMJEONG_REGIONS: tuple[SamjeongRegion, ...] = (
    SamjeongRegion(
        key="sangjeong",
        label_ko="상정",
        label_hanja="上停",
        anatomical_region="이마 ~ 눈썹 위",
        chinese_school_emphasis="이마 우위 — 학문·관운 중시 (마의상법 등)",
        korean_school_emphasis="이마 보조 — 하정 우위 통설로 상대 비중 낮음",
    ),
    SamjeongRegion(
        key="jungjeong",
        label_ko="중정",
        label_hanja="中停",
        anatomical_region="눈썹 ~ 코끝",
        chinese_school_emphasis="중년기 활동 표지",
        korean_school_emphasis="중년기 표지 — 학파 간 큰 차이 없음",
    ),
    SamjeongRegion(
        key="hajeong",
        label_ko="하정",
        label_hanja="下停",
        anatomical_region="코끝 ~ 턱",
        chinese_school_emphasis="중국 학파에서 보조 영역",
        korean_school_emphasis="한국 통설 최우위 — '턱이 좋은 것을 최고로 침' (대지 중심 가치관)",
    ),
)


# ─────────────────────────── 12궁 명칭·영역 (운명 매핑 X, 명칭만) ───────────────────────────

@dataclass(frozen=True)
class TwelvePalace:
    """12궁 영역 — 명칭·해부학 영역 정의만. 운명 매핑 차단 (ADR-006)."""
    key: str
    label_ko: str
    label_hanja: str
    anatomical_region: str
    # 의도적으로 fate_mapping 필드 부재 — ADR-006 운명 단정 차단


TWELVE_PALACES: tuple[TwelvePalace, ...] = (
    TwelvePalace("myeong", "명궁", "命宮", "미간 (양 눈썹 사이)"),
    TwelvePalace("gwanrok", "관록궁", "官祿宮", "이마 중앙"),
    TwelvePalace("jaebaek", "재백궁", "財帛宮", "코 전체"),
    TwelvePalace("jeontaek", "전택궁", "田宅宮", "눈 · 윗눈꺼풀"),
    TwelvePalace("hyeongje", "형제궁", "兄弟宮", "눈썹"),
    TwelvePalace("nobok", "노복궁", "奴僕宮", "턱 양옆"),
    TwelvePalace("cheocheop", "처첩궁", "妻妾宮", "눈꼬리 (어미)"),
    TwelvePalace("janyeo", "자녀궁", "子女宮", "와잠 (아래 눈꺼풀 아래)"),
    TwelvePalace("jilek", "질액궁", "疾厄宮", "산근 (콧대 시작)"),
    TwelvePalace("cheoni", "천이궁", "遷移宮", "이마 양옆"),
    TwelvePalace("bokdeok", "복덕궁", "福德宮", "이마 양옆 위쪽"),
    TwelvePalace("bumo", "부모궁", "父母宮", "일각·월각 (이마 좌우 모서리)"),
)


# ─────────────────────────── 한국 고유 통설 (ADR-015 옵션 B) ───────────────────────────

@dataclass(frozen=True)
class KoreanFolkSchool:
    """한국 민간 통설 — 중국 학파와 차이 명시 (옵션 B 채택 패턴)."""
    key: str
    title_ko: str
    chinese_baseline: str
    korean_variant: str
    source_url: str
    adr_006_safety_note: str  # 운명 단정 차단 안전 장치


KOREAN_FOLK_SCHOOLS: tuple[KoreanFolkSchool, ...] = (
    KoreanFolkSchool(
        key="hajeong-superiority",
        title_ko="하정 우위론",
        chinese_baseline="중국 학파: 상정 우위 (이마 중시)",
        korean_variant="한국 통설: 하정 우위 ('턱이 좋은 것을 최고로 침')",
        source_url="https://encykorea.aks.ac.kr/Article/E0004873",
        adr_006_safety_note="영역 비중 차이만 인용. 운명 단정 X",
    ),
    KoreanFolkSchool(
        key="eye-five-tenths",
        title_ko="눈 5할론",
        chinese_baseline="중국: 눈 3할 (전체 관상에서 비중)",
        korean_variant="한국: 눈 5할 — 인상 핵심으로 눈 강조",
        source_url="https://encykorea.aks.ac.kr/Article/E0004873",
        adr_006_safety_note="비중 차이만 인용. '눈빛이 흉하다' 등 단정 X",
    ),
    KoreanFolkSchool(
        key="biboksun-form",
        title_ko="비복순(鼻覆脣) 형태",
        chinese_baseline="중국: 비복순 일반론",
        korean_variant="한국: 코끝이 입술을 덮는 형태로 통용",
        source_url="https://encykorea.aks.ac.kr/Article/E0004873",
        # ★ ADR-006 핵심: "패가망신" 운명 단정은 본 시스템 채택 X
        adr_006_safety_note=(
            "보고서 §5.11에 '패가망신' 운명 단정이 있으나 ADR-006 위반으로 "
            "본 시스템에서는 채택 X. 형태 명칭만 인용. 운명 매핑 절대 금지. "
            "사용자 출력 시 '코끝이 입술을 덮는 형태' 객관 묘사만 허용."
        ),
    ),
)


# ─────────────────────────── 인용 헬퍼 (Stage 2 시스템 프롬프트 주입용) ───────────────────────────

def get_school_by_key(key: str) -> PhysiognomySchool | None:
    """학파 메타 조회."""
    for s in PHYSIOGNOMY_SCHOOLS:
        if s.key == key:
            return s
    return None


def get_palace_by_key(key: str) -> TwelvePalace | None:
    """12궁 명칭·영역 조회."""
    for p in TWELVE_PALACES:
        if p.key == key:
            return p
    return None


def format_schools_metadata_for_prompt() -> str:
    """Stage 2 시스템 프롬프트에 주입할 학파 메타 텍스트.

    운명 단정 차단을 위해 학파 차이를 객관 사실로만 인용.
    """
    lines = ["[관상학 학파 메타 — 본 시스템 영속 출처에서만 인용 가능]"]
    for s in PHYSIOGNOMY_SCHOOLS:
        lines.append(f"  · {s.name_ko}({s.name_hanja}): {s.philosophical_core}")
    lines.append(
        "[필수 안전 장치 — ADR-006] 학파 명칭·영역명만 사용. "
        "유년운기·운명 매핑·관운·재물복 단정 절대 금지."
    )
    return "\n".join(lines)


def format_korean_folk_for_prompt() -> str:
    """한국 고유 통설 — 옵션 B 명시 채택 (ADR-015)."""
    lines = ["[한국 민간 통설 — 옵션 B (학파 차이 명시 의무)]"]
    for k in KOREAN_FOLK_SCHOOLS:
        lines.append(f"  · {k.title_ko}: {k.korean_variant} (cf. {k.chinese_baseline})")
    lines.append(
        "[★ 비복순 운명 단정 차단] '패가망신' 등 운명 단정 절대 금지. "
        "형태 명칭만 객관 묘사."
    )
    return "\n".join(lines)


__all__ = [
    "PhysiognomySchool",
    "PHYSIOGNOMY_SCHOOLS",
    "SamjeongRegion",
    "SAMJEONG_REGIONS",
    "TwelvePalace",
    "TWELVE_PALACES",
    "KoreanFolkSchool",
    "KOREAN_FOLK_SCHOOLS",
    "get_school_by_key",
    "get_palace_by_key",
    "format_schools_metadata_for_prompt",
    "format_korean_folk_for_prompt",
    # ADR-103 — 육경형 + 다학파 해석 메타
    "SixMeridianType",
    "SIX_MERIDIAN_TYPES",
    "FaceSchoolInterpretation",
    "FACE_SCHOOL_INTERPRETATIONS",
    "get_six_meridian_by_key",
    "get_school_interpretation_by_feature",
    "format_school_interpretations_for_prompt",
]


# ═════════════════════════════════════════════════════════════════════════════
# ADR-103 — 형상의학 육경형(六經形) + 다학파 해석 컨텍스트
#
# ★ ADR-102 경계 명확화: 학파 라벨은 본 메타 풀에만 격리.
#    classify_* 함수 출력은 절대 학파 라벨 노출 X (인체계측 용어만).
#
# 출처 (Phase 1 라이브 검증):
#   - PMC10568153 "East Asian Medical Knowledge & Donguibogam Currents" ✅
#   - hyungsang.or.kr 형상의학회 공식 (박인규 지산) ✅
#   - mediclassics.kr 한국의학고전DB (상한론·동의보감) ⚠ LOW (PDF 바이너리)
# ═════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class SixMeridianType:
    """형상의학 육경형(六經形) 벡터 메타데이터 (ADR-103).

    분류 함수 반환 X — 본 메타는 Stage 2 자연어 풀이 컨텍스트로만 사용.
    feature_classifier.py classify_* 함수는 ADR-102 정신 유지
    (인체계측 용어 anthropometric_label만 반환).

    Attributes:
        key: 내부 식별자 (taeyang·taeeum·soyang·soeum)
        name_ko: 한국어 학파 명칭 ("태양형" 등) — Stage 2 자연어 풀이용
        name_hanja: 한자 명칭 ("太陽形" 등)
        eye_vector_description: 외안각 벡터 형태 설명
        nose_vector_description: 코 승강 벡터 형태 설명
        anthropometric_label: ★ 분류 함수 매핑용 인체계측 라벨
            (예: "upturned_eye_upturned_nose") — ADR-102 정신
        primary_source_url: 1차 출처 (hyungsang.or.kr 또는 PMC live)
        secondary_source_url: 2차 출처 (mediclassics LOW) — fallback만
        adr_006_safety_note: 의료·운명 단정 차단 명시
    """
    key: str
    name_ko: str
    name_hanja: str
    eye_vector_description: str
    nose_vector_description: str
    anthropometric_label: str
    primary_source_url: str
    secondary_source_url: str
    adr_006_safety_note: str


# 4 육경형 메타 (보고서 §3.2, Phase 1 라이브 검증)
_HYUNGSANG_PRIMARY = "https://hyungsang.or.kr/a-introduce"
_MEDICLASSICS_SECONDARY = "https://mediclassics.kr/"  # LOW 검증 (PDF 바이너리)
_SHANGHAN_ADR_006_NOTE = (
    "본 형태 벡터는 형상의학 학파 분류이며, 방광염·만성위염·불임·당뇨 등 "
    "질환 단정 인용 X (보고서 §7.2 영구 차단 리스트 준수). "
    "운명·관운·성격 단정 X (ADR-006)."
)

SIX_MERIDIAN_TYPES: tuple[SixMeridianType, ...] = (
    SixMeridianType(
        key="taeyang",
        name_ko="태양형",
        name_hanja="太陽形",
        eye_vector_description="외안각 상행 (수평축 대비 위로 올라감)",
        nose_vector_description="코끝 상승 벡터 (상방향으로 들림)",
        anthropometric_label="upturned_eye_upturned_nose",
        primary_source_url=_HYUNGSANG_PRIMARY,
        secondary_source_url=_MEDICLASSICS_SECONDARY,
        adr_006_safety_note=_SHANGHAN_ADR_006_NOTE,
    ),
    SixMeridianType(
        key="taeeum",
        name_ko="태음형",
        name_hanja="太陰形",
        eye_vector_description="외안각 하행 (수평축 대비 아래로 처짐)",
        nose_vector_description="코끝 하강 벡터 (하방향)",
        anthropometric_label="downturned_eye_downturned_nose",
        primary_source_url=_HYUNGSANG_PRIMARY,
        secondary_source_url=_MEDICLASSICS_SECONDARY,
        adr_006_safety_note=_SHANGHAN_ADR_006_NOTE,
    ),
    SixMeridianType(
        key="soyang",
        name_ko="소양형",
        name_hanja="少陽形",
        eye_vector_description="외안각 상행 + 코는 보통",
        nose_vector_description="코 수평 (벡터 0)",
        anthropometric_label="upturned_eye_neutral_nose",
        primary_source_url=_HYUNGSANG_PRIMARY,
        secondary_source_url=_MEDICLASSICS_SECONDARY,
        adr_006_safety_note=_SHANGHAN_ADR_006_NOTE,
    ),
    SixMeridianType(
        key="soeum",
        name_ko="소음형",
        name_hanja="少陰形",
        eye_vector_description="외안각 보통 + 코끝 하강",
        nose_vector_description="코끝 하강 (수평축 아래)",
        anthropometric_label="neutral_eye_downturned_nose",
        primary_source_url=_HYUNGSANG_PRIMARY,
        secondary_source_url=_MEDICLASSICS_SECONDARY,
        adr_006_safety_note=_SHANGHAN_ADR_006_NOTE,
    ),
)


def get_six_meridian_by_key(key: str) -> SixMeridianType | None:
    """육경형 key로 메타 조회 (ADR-103)."""
    for t in SIX_MERIDIAN_TYPES:
        if t.key == key:
            return t
    return None


@dataclass(frozen=True)
class FaceSchoolInterpretation:
    """동일 형태에 대한 학파별 해석 메타 (ADR-103, ADR-002 강화).

    Stage 2 자연어 풀이 프롬프트 주입용. UI 직접 출력 X.
    classify_* 함수는 본 메타와 무관 — ADR-102 정신 유지.

    Attributes:
        feature_key: 인체계측 형태 식별자 ("upturned_eye"·"square_jaw" 등)
        anthropometric_name: 인체계측 라벨 ("외안각 상행형" 등)
        school_interpretations: 학파별 해석 풀
            {school_key: {label, interpretation, source_url, adr_006_warning}}
    """
    feature_key: str
    anthropometric_name: str
    school_interpretations: dict[str, dict[str, str]]


_MAUI_SOURCE = "https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE11235666"
_PMC_DONGUIBOGAM = "https://pmc.ncbi.nlm.nih.gov/articles/PMC10568153/"

FACE_SCHOOL_INTERPRETATIONS: tuple[FaceSchoolInterpretation, ...] = (
    FaceSchoolInterpretation(
        feature_key="upturned_eye",
        anthropometric_name="외안각 상행형",
        school_interpretations={
            "maui": {
                "label": "봉안(鳳眼)",
                "interpretation": "봉황의 눈에 비유한 형태 — 동물 비유 학파 해석",
                "source_url": _MAUI_SOURCE,
                "adr_006_warning": "운명·관운·재물 단정 X — 형태 비유만 인용",
            },
            "hyungsang": {
                "label": "태양형(太陽形)",
                "interpretation": "외안각 + 코끝 상행 벡터 — 형상의학 육경형",
                "source_url": _HYUNGSANG_PRIMARY,
                "adr_006_warning": "방광염·교감신경 항진 등 의료 단정 X (보고서 §7.2)",
            },
        },
    ),
    FaceSchoolInterpretation(
        feature_key="square_jaw",
        anthropometric_name="사각형 턱",
        school_interpretations={
            "maui": {
                "label": "지각방원(地閣方圓)",
                "interpretation": "대지의 풍요로움에 비유한 형태",
                "source_url": _MAUI_SOURCE,
                "adr_006_warning": "말년 재물복·고독 단정 X — 형태 비유만",
            },
            "hyungsang": {
                "label": "기과(氣科)",
                "interpretation": "기혈 순환 강도 지표 — 정기신혈과 분류",
                "source_url": _PMC_DONGUIBOGAM,
                "adr_006_warning": "기병·만성질환 단정 X (보고서 §7.2)",
            },
        },
    ),
    FaceSchoolInterpretation(
        feature_key="prominent_nose",
        anthropometric_name="현저한 코",
        school_interpretations={
            "maui": {
                "label": "현담비(懸膽鼻)",
                "interpretation": "쓸개를 매단 듯한 형태 — 중악(中嶽) 지표",
                "source_url": _MAUI_SOURCE,
                "adr_006_warning": "재물 축적·관운 단정 X — 형태 비유만",
            },
            "hyungsang": {
                "label": "육경형 y축 벡터",
                "interpretation": "얼굴 전체 승강 벡터 결정 인자",
                "source_url": _HYUNGSANG_PRIMARY,
                "adr_006_warning": "성격·질환 단정 X (ADR-006)",
            },
        },
    ),
)


def get_school_interpretation_by_feature(feature_key: str) -> FaceSchoolInterpretation | None:
    """feature_key로 학파 해석 메타 조회 (ADR-103)."""
    for interp in FACE_SCHOOL_INTERPRETATIONS:
        if interp.feature_key == feature_key:
            return interp
    return None


# ─────────────────────────── ADR-144 KCI 학술 인용 (눈·턱 전문) ───────────────────────────

# /domain-priorities #6 (face KCI 학술 자료) 해소 — 사용자 결단 2026-05-22.
# Archives of Design Research = KCI 등재 + SCOPUS 동시 등재 (한국디자인학회 1978).
# 본 시스템 face/reading.py Stage 2 자연어 풀이에서 학파 인용 시 사용.

@dataclass(frozen=True)
class KciCitation:
    """KCI 등재 학술 논문 메타데이터 (ADR-010 사실성 분리 강화).

    Attributes:
        key: 내부 식별자
        authors_ko: 저자 (한국어, 발표년도)
        title_ko: 논문 제목 (한국어 원문)
        journal: 학술지 (KCI 등재명)
        volume_issue: 권·호 (예: "12권 1호")
        pages: 페이지 범위
        publication_year: 발행 연도
        kci_indexed: KCI 등재 여부 (True 보장)
        scopus_indexed: SCOPUS 등재 여부
        publisher_url: 학회/학술지 공식 URL
        dbpia_url: DBpia 검증 가능 URL
        topic_focus: 본 시스템 활용 영역 (예: "눈", "턱", "MBTI 매핑")
        usage_note: 본 시스템 사용 시 주의사항 (ADR-006·010 정합)
    """
    key: str
    authors_ko: str
    title_ko: str
    journal: str
    volume_issue: str
    pages: str
    publication_year: int
    kci_indexed: bool
    scopus_indexed: bool
    publisher_url: str
    dbpia_url: str
    topic_focus: str
    usage_note: str


FACE_KCI_CITATIONS: tuple[KciCitation, ...] = (
    KciCitation(
        key="oh_1999_eye",
        authors_ko="오근재 (1999)",
        title_ko="영상기호로서의 눈(眼)의 표정에 관한 연구: 관상학적 담론에 근거한 얼굴형과 구조를 중심으로",
        journal="Archives of Design Research (디자인학연구)",
        volume_issue="12권 1호 (Issue 28)",
        pages="121-130",
        publication_year=1999,
        kci_indexed=True,
        scopus_indexed=True,
        publisher_url="https://design-science.or.kr/",
        dbpia_url="https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE00892585",
        topic_focus="눈(眼) 관상학적 표정 분류 — 얼굴형·구조 의존성",
        usage_note=(
            "본 시스템 face/reading.py 눈 영역 자연어 풀이에 학파 인용 가능. "
            "단정 운명 매핑 X — 시각 기호 분류만. ADR-006·116 sanitize 동반 의무."
        ),
    ),
    KciCitation(
        key="kang_2008_mbti_face",
        authors_ko="강선희·김효동·이경원 (2008)",
        title_ko="동양 관상학을 적용한 성격별 얼굴 설계 시스템에 관한 연구",
        journal="Archives of Design Research (디자인학연구)",
        volume_issue="21권 4호",
        pages="해당 권 본문",
        publication_year=2008,
        kci_indexed=True,
        scopus_indexed=True,
        publisher_url="https://design-science.or.kr/",
        dbpia_url="https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE01057824",
        topic_focus=(
            "얼굴 6대 부위 (얼굴형·눈·코·입·이마·눈썹) × 29 하위 분류 × "
            "MBTI 39 성격 매핑 — 한국형 변환 시스템 FACE"
        ),
        usage_note=(
            "본 시스템 face/knowledge.py 12궁 + 삼정 보강 인용. "
            "MBTI 단정 매핑은 ADR-014 회피 — 본 인용은 부위 분류 체계만 활용. "
            "성격 → 운명 변환 X — 형태 분류 학술 출처로만."
        ),
    ),
)


def get_kci_citation_by_key(key: str) -> KciCitation | None:
    """KCI 인용 키로 조회 — Stage 2 프롬프트 빌드 시 참조."""
    for c in FACE_KCI_CITATIONS:
        if c.key == key:
            return c
    return None


def format_kci_citations_for_prompt() -> str:
    """ADR-144: Stage 2 자연어 풀이 시 KCI 학술 인용 컨텍스트 빌드.

    LLM 시스템 프롬프트에 주입 — 본 시스템 출처가 KCI 등재 학술지임을 명시.
    ADR-010 사실성 분리 강도 ↑ (KCI 등재 + SCOPUS 인덱싱).
    """
    lines = [
        "[KCI 등재 학술 인용 — ADR-144 face 학술 출처 강화]",
        "(본 시스템 face 영역 풀이의 학술 인용 출처. 운명 단정 X — 분류 체계만.)",
        "",
    ]
    for c in FACE_KCI_CITATIONS:
        lines.append(f"- {c.authors_ko} \"{c.title_ko}\"")
        lines.append(f"  {c.journal} {c.volume_issue}, {c.pages}")
        kci_tag = "KCI 등재" + (" + SCOPUS" if c.scopus_indexed else "")
        lines.append(f"  {kci_tag} · {c.dbpia_url}")
        lines.append(f"  활용: {c.topic_focus}")
        lines.append(f"  주의: {c.usage_note}")
        lines.append("")
    return "\n".join(lines)


def format_school_interpretations_for_prompt(feature_key: str) -> str | None:
    """Stage 2 자연어 풀이용 학파 해석 텍스트 빌드 (ADR-103).

    LLM 시스템 프롬프트에 직접 주입. UI 출력 X.
    학파 라벨 노출은 본 함수 호출 결과에만 한정 (ADR-102 정신 유지 —
    classify_* 함수는 인체계측 용어만 반환).

    Returns:
        프롬프트 텍스트 또는 None (feature_key 미존재 시).
    """
    interp = get_school_interpretation_by_feature(feature_key)
    if interp is None:
        return None
    lines = [
        f"[학파별 해석 컨텍스트 — {interp.anthropometric_name}]",
        f"(다학파 병행 — ADR-002 정합. 운명·질환 단정 X — ADR-006)",
        "",
    ]
    for school_key, s in interp.school_interpretations.items():
        lines.append(f"- {s['label']} ({school_key}): {s['interpretation']}")
        lines.append(f"  출처: {s['source_url']}")
        lines.append(f"  안전 가드: {s['adr_006_warning']}")
    return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════════
# ADR-277 — 오행 5형(五形) 전통 기질 매핑 (관상 캐릭터 풀이)
#
# 배경: "정통 관상"이 형태 묘사·인상 형용사에 그쳐 "당신은 어떤 본바탕인가"라는
#   관상의 핵심 결론이 빠진다는 사용자 지적. 5형 분류(shape.py)는 결정론으로
#   산출되나 그 형이 뜻하는 전통 기질이 LLM에 주입되지 않았다.
#
# 해결: 오행 철학의 표준 오상(五常) 대응 — 목=仁·화=禮·토=信·금=義·수=智 —
#   을 관상 5형에 연결한 전통 해석을 데이터화. 사주(saju_mbti) 도메인이 4축
#   경향성을 내는 것과 동일 패턴.
#
# ★ ADR-010/006 정합: "당신은 ~한 사람이다"(단정·예언) X.
#   "전통 관상에서 ~형은 ~한 기질로 봅니다"(출처 명시 경향)만 허용.
#   tendency 문구는 모두 "~한 경향으로 봅니다 / ~로 풀이합니다" 형식.
#
# 출처:
#   - 오행-오상 대응: 동중서 春秋繁露, 황제내경(공유 철학 지식)
#   - 관상 5형 분류: 麻衣相法·신상전편(神相全編) 오형론, 송우철(2017) DBpia
# ═════════════════════════════════════════════════════════════════════════════

_FIVE_SHAPE_SOURCE_OHAENG = "동중서 春秋繁露 五行對應 + 황제내경 (오행-오상 공유 지식)"
_FIVE_SHAPE_SOURCE_FACE = "https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE11235666"  # 송우철(2017) 오형 분류


@dataclass(frozen=True)
class FiveShapeTrait:
    """오행 5형의 전통 기질 매핑 (ADR-277).

    Attributes:
        shape_type: 한글 오행명 (목형·화형·토형·금형·수형)
        ohaeng: 오행 (木火土金水)
        ohsang: 대응 오상 (仁禮信義智)
        keyword: 핵심 기질 키워드 (1~2어)
        tendency: 전통 해석상 경향 (단정 X — "~로 봅니다" 형식)
        strength: 강점 결 (관상 전통 통설)
        caution: 균형을 위한 주의 결 (양면 제시, ADR-094)
    """

    shape_type: str
    ohaeng: str
    ohsang: str
    keyword: str
    tendency: str
    strength: str
    caution: str


FIVE_SHAPE_TRAITS: tuple[FiveShapeTrait, ...] = (
    FiveShapeTrait(
        shape_type="목형",
        ohaeng="木",
        ohsang="仁",
        keyword="인자함·성장",
        tendency="곧게 위로 뻗는 나무의 결처럼, 전통 관상에서 목형은 어질고 곧으며 꾸준히 자라나는 기질로 풀이합니다",
        strength="인정이 두텁고 곧으며, 멀리 보고 꾸준히 나아가는 결",
        caution="때로 고집이 강해질 수 있으니 유연함을 곁들이면 더 좋은 결",
    ),
    FiveShapeTrait(
        shape_type="화형",
        ohaeng="火",
        ohsang="禮",
        keyword="정열·예의",
        tendency="위로 타오르는 불의 결처럼, 전통 관상에서 화형은 밝고 정열적이며 예를 아는 기질로 풀이합니다",
        strength="활기차고 표현이 밝으며, 사람을 끌어모으는 따뜻한 결",
        caution="기운이 급히 솟구칠 수 있으니 차분함을 더하면 더 좋은 결",
    ),
    FiveShapeTrait(
        shape_type="토형",
        ohaeng="土",
        ohsang="信",
        keyword="포용·신의",
        tendency="만물을 품는 흙의 결처럼, 전통 관상에서 토형은 듬직하고 믿음직하며 너그러운 기질로 풀이합니다",
        strength="포용력이 넓고 신의가 두터우며, 주변을 안정시키는 묵직한 결",
        caution="변화에 더딜 수 있으니 새로움을 받아들이면 더 좋은 결",
    ),
    FiveShapeTrait(
        shape_type="금형",
        ohaeng="金",
        ohsang="義",
        keyword="결단·의리",
        tendency="날카롭게 다듬어진 쇠의 결처럼, 전통 관상에서 금형은 단호하고 의리 있으며 맺고 끊음이 분명한 기질로 풀이합니다",
        strength="결단력이 뚜렷하고 원칙이 분명하며, 의리를 지키는 곧은 결",
        caution="때로 냉정해 보일 수 있으니 너그러움을 곁들이면 더 좋은 결",
    ),
    FiveShapeTrait(
        shape_type="수형",
        ohaeng="水",
        ohsang="智",
        keyword="지혜·유연",
        tendency="굽이쳐 흐르는 물의 결처럼, 전통 관상에서 수형은 슬기롭고 유연하며 두루 어울리는 기질로 풀이합니다",
        strength="총명하고 적응이 빠르며, 상황을 부드럽게 풀어가는 슬기로운 결",
        caution="마음이 자주 흔들릴 수 있으니 중심을 다잡으면 더 좋은 결",
    ),
    FiveShapeTrait(
        shape_type="복합형",
        ohaeng="土(中)",
        ohsang="中庸",
        keyword="균형·중용",
        tendency="어느 한쪽으로 치우치지 않은 결로, 전통 관상에서 복합형은 오행의 기운을 고루 갖춘 균형의 기질로 풀이합니다",
        strength="치우침 없이 두루 어울리며, 상황에 맞춰 여러 면모를 발휘하는 균형 잡힌 결",
        caution="뚜렷한 색이 옅을 수 있으니 자기만의 결을 또렷이 세우면 더 좋은 결",
    ),
)

_FIVE_SHAPE_BY_TYPE = {t.shape_type: t for t in FIVE_SHAPE_TRAITS}


def get_five_shape_trait(shape_type: str) -> FiveShapeTrait | None:
    """한글 오행명(목형·화형·토형·금형·수형) → 기질 매핑. 복합형·미상은 None."""
    return _FIVE_SHAPE_BY_TYPE.get(shape_type)


def format_five_shape_trait_for_prompt(shape_type: str) -> str | None:
    """5형 기질을 Stage 2 프롬프트 주입용 텍스트로. 복합형 등은 None.

    캐릭터 결론 단락의 재료. 단정 금지(ADR-006) — 모두 "~로 봅니다" 경향 어조.
    """
    t = get_five_shape_trait(shape_type)
    if t is None:
        return None
    return (
        f"[오행 5형 기질 — {t.shape_type}({t.ohaeng}·오상 {t.ohsang}), ADR-277]\n"
        f"  • 핵심 결: {t.keyword}\n"
        f"  • 전통 해석: {t.tendency}\n"
        f"  • 강점 결: {t.strength}\n"
        f"  • 주의 결(균형): {t.caution}\n"
        f"  • 출처: {_FIVE_SHAPE_SOURCE_OHAENG} / 5형 분류 {_FIVE_SHAPE_SOURCE_FACE}\n"
        f"  ※ 캐릭터 결론 단락에 활용. '~한 사람이다·~할 것이다' 단정 X, "
        f"'전통 관상에서 ~형은 ~한 결로 봅니다' 경향 어조만 (ADR-006·094)."
    )


# ═════════════════════════════════════════════════════════════════════════════
# ADR-278 — 삼정(三停) 시기론 + 성격·인생 흐름 풀이
#
# 배경: "성격·인생 풀이를 하라"는 사용자 명시 요구. 기존 ADR-006은 성격·운명
#   단정을 막았으나, 사용자가 관상의 본령(성격·인생 흐름 해석)을 요구.
#   → 단정·예언은 여전히 금지하되, "전통 관상에서 ~한 시기·기질로 보는 경향"
#   어조의 성격·인생 흐름 풀이를 허용 (ADR-014 saju_mbti 경향성 예외와 동일 논리).
#
# 삼정 시기론: 전통 관상의 표준 — 얼굴을 상·중·하 삼등분하여 인생 시기에 대응.
#   상정(이마) = 초년運 (초년~30대 초반의 흐름·복록의 결)
#   중정(눈썹~코) = 중년運 (30~50대의 활동·실행의 결)
#   하정(입~턱) = 말년運 (50대 이후의 안정·수확의 결)
#
# ★ ADR-006/010/094 정합: "초년에 ~할 것이다"(예언) X.
#   "전통 관상에서 상정이 발달하면 초년의 결이 밝다고 봅니다"(경향) O.
#   각 정의 점수가 높으면 "그 시기의 결이 도드라진다", 낮으면 "차분히 다진다"
#   양면 어조. 시간 축은 '경향'으로만, 단정·구체 사건 예언 금지.
#
# 출처: 麻衣相法·神相全編 삼정론 (전통 관상 공유 지식), 송우철(2017) DBpia
# ═════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class SamjeongPeriod:
    """삼정 시기론 — 정(停)별 인생 시기 대응 (ADR-278).

    Attributes:
        region: 삼정 영역 (상정·중정·하정)
        period: 대응 인생 시기
        high_tendency: 점수 높을 때 경향 (단정 X — "~한 결로 봅니다")
        low_tendency: 점수 낮을 때 경향 (균형 어조)
    """

    region: str
    period: str
    high_tendency: str
    low_tendency: str


SAMJEONG_PERIODS: dict[str, SamjeongPeriod] = {
    "상정": SamjeongPeriod(
        region="상정",
        period="초년運 (초년~30대 초반)",
        high_tendency="이마(상정)가 도드라지니, 전통 관상에서 초년의 기운과 배움·복록의 결이 밝다고 보는 경향이 있습니다",
        low_tendency="이마(상정)가 차분하니, 초년은 서두르기보다 천천히 기틀을 다지는 결로 봅니다",
    ),
    "중정": SamjeongPeriod(
        region="중정",
        period="중년運 (30~50대)",
        high_tendency="눈썹~코(중정)의 기운이 강하니, 전통 관상에서 중년의 활동력·실행과 자기 확립의 결이 도드라진다고 보는 경향이 있습니다",
        low_tendency="중정이 차분하니, 중년은 무리하기보다 내실을 다지는 결로 봅니다",
    ),
    "하정": SamjeongPeriod(
        region="하정",
        period="말년運 (50대 이후)",
        high_tendency="입~턱(하정)이 도드라지니, 전통 관상에서 말년의 안정·수확과 사람을 품는 결이 두텁다고 보는 경향이 있습니다",
        low_tendency="하정이 차분하니, 말년의 결은 욕심을 덜고 마음을 다스리면 더 안정되는 것으로 봅니다",
    ),
}


def format_samjeong_periods_for_prompt(samjeong_scores: dict[str, float]) -> str | None:
    """삼정 점수 dict({상정:0.21, 중정:1.0, 하정:0.0}) → 인생 흐름 프롬프트.

    인생(시기) 풀이 단락 재료. 단정·예언 금지(ADR-006) — '~로 보는 경향' 어조.
    """
    if not samjeong_scores:
        return None
    lines = ["[삼정 시기론 — 인생 흐름 경향, ADR-278]"]
    for region in ("상정", "중정", "하정"):
        score = samjeong_scores.get(region)
        if score is None:
            continue
        p = SAMJEONG_PERIODS.get(region)
        if p is None:
            continue
        t = p.high_tendency if score >= 0.5 else p.low_tendency
        lines.append(f"  • {p.region}({p.period}) 점수 {score:.2f} → {t}")
    if len(lines) == 1:
        return None
    lines.append(
        "  ※ 인생 흐름 단락에 활용. '초년에 ~할 것이다·~운이 온다' 단정·예언 X, "
        "'전통 관상에서 ~시기의 결을 ~로 보는 경향이 있습니다' 어조만 (ADR-006·094)."
    )
    return "\n".join(lines)


__all__ += [
    "FiveShapeTrait",
    "FIVE_SHAPE_TRAITS",
    "get_five_shape_trait",
    "format_five_shape_trait_for_prompt",
    "SamjeongPeriod",
    "SAMJEONG_PERIODS",
    "format_samjeong_periods_for_prompt",
]
