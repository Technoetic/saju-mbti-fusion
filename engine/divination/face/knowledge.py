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
]
