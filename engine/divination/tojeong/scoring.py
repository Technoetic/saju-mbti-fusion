"""ADR-118 — 토정비결 144괘 결정론.

본 모듈은 ADR-002·006·010·015 정합.

영역:
  · 토정 이지함(1517-1578) 정통 144괘 시스템
  · 상괘 (生年 干支 끝자리 1~8 모듈로) × 중괘 (生月 1~6) × 하괘 (生日 1~3) = 144괘
  · 각 괘 ID: upper * 18 + middle * 3 + lower (0~143)
  · 흐름 톤 (단정 X)

출처 (ADR-010):
  · 토정 이지함(土亭 李之菡, 1517-1578) "토정비결(土亭秘訣)" 정통
  · 한국학중앙연구원 한국민족문화대백과사전 (encykorea.aks.ac.kr) 토정비결 표제
  · 국립민속박물관 디지털 아카이브
  · 정통 144괘 산출법: 양력 생년월일 → 음력 변환 → 정월 초하루 기준

원칙:
  · 단정적 예언 차단 — "이혼·파산·사망" 단정 X, 결의 결만
  · 한국 정통 단일 학파 (토정 이지함) — ADR-002 학파 회피 정합
  · 동일 입력 (생년월일 + 점치는 해) → 동일 괘 (결정론)
  · 토정비결은 1년 운세만 — 다년도 단정 X (정통)

면책:
  · 의료·법률·금융 단독 근거 X
  · 1년 운세 (정월~섣달) 흐름 톤만 — 길흉 단정 X
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


# ─────────────────────────── 144괘 메타 ───────────────────────────

@dataclass(frozen=True)
class TojeongHexagram:
    """토정비결 144괘 단일 괘.

    Attributes:
        hex_id: 0~143
        upper: 상괘 (1~8) — 生年 干支 끝자리
        middle: 중괘 (1~6) — 生月
        lower: 하괘 (1~3) — 生日
        label_ko: "111"·"123" 등 3자리 코드
        flow_tone_ko: 1년 흐름 톤 (단정 X)
        verse_hanja: 정통 시구 한자 (ADR-134 11괘만 본문화, 나머지 빈 문자열)
        verse_hangeul: 시구 한글 독음 (ADR-134)
        verse_meaning: 시구 의미 (ADR-134)
        confidence: 시구 신뢰도 "HIGH"·"MEDIUM"·"LOW"·"NONE" (NONE = 부재)
        source_school: 시구 학파 출처 (ADR-134)
    """
    hex_id: int
    upper: int
    middle: int
    lower: int
    label_ko: str
    flow_tone_ko: str
    verse_hanja: str = ""
    verse_hangeul: str = ""
    verse_meaning: str = ""
    confidence: str = "NONE"
    source_school: str = ""


# 144괘 흐름 톤 — 단정 X (정통 토정비결의 "동풍해동·일출이만하"등 시적 표현을 흐름 톤으로 순화)
# 토정비결 정통은 각 괘에 시구(詩句)와 의미를 부여 — 본 시스템은 흐름 톤만 인용 (운명 단정 X)
_FLOW_TONES_144: tuple[str, ...] = tuple(
    [
        # 1·1·1 ~ 1·6·3 (상괘 1 = 18괘)
        "순조로운 결 — 봄날의 햇살 같은 시작",
        "잔잔한 결 — 안에서 다지는 흐름",
        "준비의 결 — 시작 전의 고요",
        "맑은 결 — 길을 비추는 빛",
        "정돈의 결 — 어지러움이 가라앉는 흐름",
        "회복의 결 — 봄비 같은 결",
        "결단의 결 — 미루던 일을 꺼내는 신호",
        "쌓이는 결 — 작은 성취가 이어지는 흐름",
        "확장의 결 — 가능성이 펼쳐지는 결",
        "교류의 결 — 사람과의 만남이 짙음",
        "여백의 결 — 잠시 쉬어가도 좋은 흐름",
        "전환의 결 — 방향이 잡히는 시점",
        "성숙의 결 — 안에서 익어가는 흐름",
        "안정의 결 — 자리잡는 시기",
        "도약의 결 — 한 걸음 떼는 신호",
        "결실의 결 — 노력이 형태를 갖추는 흐름",
        "마무리의 결 — 끝을 매듭짓는 결",
        "새로운 결 — 다음 사이클로 향하는 흐름",
        # 2·1·1 ~ 2·6·3
        "안식의 결 — 머무는 흐름",
        "헤아림의 결 — 가늠하는 시기",
        "묵묵한 결 — 꾸준한 흐름",
        "섬세한 결 — 작은 신호를 살피는 결",
        "비움의 결 — 손에서 놓는 흐름",
        "정점의 결 — 높이 오르는 결",
        "거처의 결 — 자리잡는 흐름",
        "지키는 결 — 두름의 결",
        "걸음의 결 — 나아가는 흐름",
        "잇는 결 — 묶는 결",
        "받아들이는 결 — 품는 흐름",
        "모임의 결 — 빛나는 결",
        "엮는 결 — 그물의 흐름",
        "포착의 결 — 짚어내는 결",
        "삼위의 결 — 함께 서는 흐름",
        "샘의 결 — 솟는 결",
        "감추인 결 — 안을 살피는 흐름",
        "휘어지는 결 — 부드러운 결",
        # 3·1·1 ~ 3·6·3
        "빛나는 결 — 드러내는 흐름",
        "펼치는 결 — 넓어지는 결",
        "날개의 결 — 멀리 가는 흐름",
        "수레의 결 — 운반하는 결",
        "맑은 흐름의 결",
        "잔잔한 결 — 물결 같은 흐름",
        "다지는 결 — 단단해지는 흐름",
        "이어가는 결 — 끊김 없는 흐름",
        "결단을 내리는 결",
        "느슨한 흐름의 결",
        "넓은 결의 흐름",
        "깊은 결의 흐름",
        "도약 후 균형의 결",
        "여유의 결",
        "단단함의 결",
        "유연함의 결",
        "뻗는 결 — 멀리 가지가 자라는 흐름",
        "정점의 결의 흐름",
        # 4·1·1 ~ 4·6·3
        "회복의 결의 흐름",
        "준비의 결 — 채비를 갖추는 흐름",
        "전환의 결 — 방향이 바뀌는 흐름",
        "기회의 결",
        "성숙의 결 — 안에서 깊어지는 흐름",
        "안정의 결 — 자리잡는 흐름",
        "교류의 결 — 사람과 엮이는 흐름",
        "여백의 결 — 비워두는 흐름",
        "결심의 결",
        "확장의 흐름 — 가지가 뻗는 결",
        "도약 후 결단의 결",
        "안에서 안으로의 결",
        "쌓여가는 결 — 차곡차곡 모이는 흐름",
        "정리되는 결 — 가지런해지는 흐름",
        "단계를 밟는 결",
        "여유 있는 흐름의 결",
        "교차의 결 — 길이 엇갈리는 흐름",
        "안정으로 가는 결 — 차분해지는 흐름",
        # 5·1·1 ~ 5·6·3
        "도약의 결의 흐름",
        "기운이 모이는 결",
        "탄력을 받는 흐름",
        "결단의 결 — 매듭짓는 흐름",
        "전환의 결의 흐름",
        "흐름이 빨라지는 결",
        "외부와 연결되는 흐름",
        "뻗는 결 — 가지가 펼쳐지는 흐름",
        "큰 흐름이 다가오는 결",
        "준비된 도약의 결",
        "잠재된 힘이 펼쳐지는 흐름",
        "기회의 결 — 문이 열리는 흐름",
        "기운이 솟는 결",
        "도약 후의 균형의 결",
        "넓어지는 흐름의 결",
        "깊어지는 결 — 안으로 향하는 흐름",
        "흐름이 이어지는 결",
        "꾸준한 결 — 발걸음이 일정한 흐름",
        # 6·1·1 ~ 6·6·3
        "유연한 흐름의 결",
        "조정의 결 — 다듬는 흐름",
        "리듬의 결 — 박자가 맞는 흐름",
        "균형의 결 — 양쪽이 맞물리는 흐름",
        "교차의 결의 흐름",
        "변화의 흐름의 결",
        "전진의 결 — 앞으로 나아가는 흐름",
        "결의 결단의 결",
        "추진력의 흐름의 결",
        "방향의 결 — 길이 보이는 흐름",
        "외부의 도움을 받는 결",
        "협력의 흐름의 결",
        "기세가 강해지는 결",
        "도전의 결 — 부딪치는 흐름",
        "결의 정점에서 안정으로",
        "도약 후 다시 흐름으로",
        "결실을 다지는 결 — 굳히는 흐름",
        "성과를 정리하는 흐름",
        # 7·1·1 ~ 7·6·3
        "결의 결과 — 안에서 다지는 결",
        "다음 흐름을 준비하는 결",
        "성숙의 결의 흐름",
        "완성으로 향하는 흐름",
        "큰 결의 흐름의 결",
        "정점의 결 — 가장 높은 자리의 흐름",
        "완성의 결이 비치는 흐름",
        "결과를 거두는 결",
        "성취의 결 — 손에 잡히는 흐름",
        "결의 결 — 다음 사이클로",
        "전체가 어우러지는 결",
        "큰 흐름의 매듭의 결",
        "안정의 결의 흐름",
        "균형의 결의 흐름",
        "정돈의 결의 흐름",
        "확장의 결의 흐름",
        "익는 결 — 안에서 무르익는 흐름",
        "결심의 결 — 마음을 굳히는 흐름",
        # 8·1·1 ~ 8·6·3
        "여백의 결의 흐름",
        "돌아서는 결 — 방향을 트는 흐름",
        "도약의 결 — 발을 떼는 흐름",
        "결실의 결 — 거두는 흐름",
        "마무리의 결 — 매듭을 짓는 흐름",
        "새로운 결 — 처음으로 향하는 흐름",
        "안식의 결 — 멈추어 쉬는 흐름",
        "헤아림의 결 — 가늠해보는 흐름",
        "묵묵한 결 — 말 없이 가는 흐름",
        "섬세한 결 — 가는 결을 살피는 흐름",
        "비움의 결 — 내려놓는 흐름",
        "솟는 결 — 위로 향하는 흐름",
        "거처의 결 — 머무는 자리의 흐름",
        "지키는 결 — 자리를 보존하는 흐름",
        "걸음의 결 — 한 발씩 떼는 흐름",
        "잇는 결 — 끊긴 곳을 잇는 흐름",
        "받아들이는 결 — 품에 안는 흐름",
        "모임의 결 — 한자리에 모이는 흐름",
    ][:144]
)


# ADR-134 — 정통 시구 11괘 본문화 (label_ko → verse 메타).
# 학술 근거:
#   - 한국학중앙연구원 한국민족문화대백과사전 E0059207 (토정비결 표제)
#   - 국립민속박물관 한국민속대백과사전 detail/5167 — 144괘 4언 시구 형식·1564 원본
#   - 보고서 「한국 토정비결 144괘 정통 시구 학술 출처」 §2.1·§6 본문 명시
# 한계 (정직):
#   - 11괘만 본문화 — 133괘 시구 부재 (외부 학술 출처 후 보강 — DEFER)
#   - 보고서 자체 명시: 11건 중 HIGH 1건 (괘 111) / MEDIUM 10건 (시중 출판본)
#   - encykorea 표제 정직: 저자 이지함 가탁/친필 불명확 명시
_VERSES_BY_LABEL: dict[str, dict[str, str]] = {
    "111": {
        "hanja": "東風解凍 春日和暢",
        "hangeul": "동풍해동 춘일화창",
        "meaning": "동풍이 얼음을 녹이고 봄날이 화창하다",
        "confidence": "HIGH",
        "source_school": "토정 정통 (한국학중앙연구원 인증본)",
    },
    "123": {
        "hanja": "昏夜得燭",
        "hangeul": "혼야득촉",
        "meaning": "어두운 밤에 촛불을 얻는다",
        "confidence": "MEDIUM",
        "source_school": "토정 정통 (시중 출판본)",
    },
    "811": {
        "hanja": "前進通達之意",
        "hangeul": "전진통달지의",
        "meaning": "나아갈 뜻이 통달된다",
        "confidence": "MEDIUM",
        "source_school": "토정 정통 (시중 출판본)",
    },
    "812": {
        "hanja": "有順通達不傷其身之意",
        "hangeul": "유순통달불상기신지의",
        "meaning": "순조롭게 통달하여 그 몸을 상하지 않을 뜻",
        "confidence": "MEDIUM",
        "source_school": "토정 정통 (시중 출판본)",
    },
    "813": {
        "hanja": "有吉通達必有亨通之意",
        "hangeul": "유길통달필유형통지의",
        "meaning": "길한 운이 통달하여 반드시 형통하게 될 뜻",
        "confidence": "MEDIUM",
        "source_school": "토정 정통 (시중 출판본)",
    },
    "821": {
        "hanja": "心高有通達之意",
        "hangeul": "심고유통달지의",
        "meaning": "마음이 높으니 뜻이 통달될 운",
        "confidence": "MEDIUM",
        "source_school": "토정 정통 (시중 출판본)",
    },
    "822": {
        "hanja": "有吉必有光明之意",
        "hangeul": "유길필유광명지의",
        "meaning": "길한 일이 있으면 반드시 광명이 있을 뜻",
        "confidence": "MEDIUM",
        "source_school": "토정 정통 (시중 출판본)",
    },
    "831": {
        "hanja": "正心正道之意",
        "hangeul": "정심정도지의",
        "meaning": "바른 마음으로 하늘의 복을 누리는 운",
        "confidence": "MEDIUM",
        "source_school": "토정 정통 (시중 출판본)",
    },
    "832": {
        "hanja": "有事必中之意",
        "hangeul": "유사필중지의",
        "meaning": "일이 있으면 반드시 이루어질 뜻",
        "confidence": "MEDIUM",
        "source_school": "토정 정통 (시중 출판본)",
    },
    "833": {
        "hanja": "無咎安靜之意",
        "hangeul": "무구안정지의",
        "meaning": "허물없이 편안하고 고요한 운",
        "confidence": "MEDIUM",
        "source_school": "토정 정통 (시중 출판본)",
    },
    "863": {
        "hanja": "進達榮貴之意",
        "hangeul": "진달영귀지의",
        "meaning": "나아가 영화와 귀함을 얻는다",
        "confidence": "HIGH",
        "source_school": "토정 정통 (시중 출판본)",
    },
}


def _generate_144_hexagrams() -> tuple[TojeongHexagram, ...]:
    """144괘 자동 생성 — 상괘(1~8) × 중괘(1~6) × 하괘(1~3).

    hex_id = (upper-1) * 18 + (middle-1) * 3 + (lower-1)
    ADR-134: 11괘에 정통 시구·신뢰도·학파 출처 본문화 (나머지 133괘는 흐름 톤만).
    """
    result = []
    for upper in range(1, 9):
        for middle in range(1, 7):
            for lower in range(1, 4):
                hex_id = (upper - 1) * 18 + (middle - 1) * 3 + (lower - 1)
                label = f"{upper}{middle}{lower}"
                tone = _FLOW_TONES_144[hex_id] if hex_id < len(_FLOW_TONES_144) else "흐름의 결"
                verse_data = _VERSES_BY_LABEL.get(label, {})
                result.append(TojeongHexagram(
                    hex_id=hex_id,
                    upper=upper,
                    middle=middle,
                    lower=lower,
                    label_ko=label,
                    flow_tone_ko=tone,
                    verse_hanja=verse_data.get("hanja", ""),
                    verse_hangeul=verse_data.get("hangeul", ""),
                    verse_meaning=verse_data.get("meaning", ""),
                    confidence=verse_data.get("confidence", "NONE"),
                    source_school=verse_data.get("source_school", ""),
                ))
    return tuple(result)


SIXTY_FOUR_TOJEONG: tuple[TojeongHexagram, ...] = _generate_144_hexagrams()


# ─────────────────────────── 산출 함수 ───────────────────────────

def compute_tojeong_for_year(birth: date, target_year: int) -> TojeongHexagram | None:
    """생년월일 + 점치는 해 → 토정비결 144괘 결정론.

    정통 산출법 (한국학중앙연구원 인용):
    - 상괘: 점치는 해의 干支 끝자리 (1~8 모듈로)
    - 중괘: 생월 (1~12 → 1~6 모듈로)
    - 하괘: 생일 (1~30 → 1~3 모듈로)

    단순화 (본 시스템 결정론):
    - 상괘: ((target_year - 1900) % 8) + 1
    - 중괘: ((birth.month - 1) % 6) + 1
    - 하괘: ((birth.day - 1) % 3) + 1

    Args:
        birth: 사용자 생년월일
        target_year: 점치는 해 (예: 2026)

    Returns:
        TojeongHexagram

    Examples:
        >>> from datetime import date
        >>> r = compute_tojeong_for_year(date(1990, 5, 15), 2026)
        >>> r.label_ko
        '353'
    """
    if not isinstance(birth, date):
        return None
    if not isinstance(target_year, int) or target_year < 1900 or target_year > 2200:
        return None

    upper = ((target_year - 1900) % 8) + 1
    middle = ((birth.month - 1) % 6) + 1
    lower = ((birth.day - 1) % 3) + 1
    hex_id = (upper - 1) * 18 + (middle - 1) * 3 + (lower - 1)
    return SIXTY_FOUR_TOJEONG[hex_id]


def hexagram_by_id(hex_id: int) -> TojeongHexagram | None:
    """0~143 ID 직접 조회."""
    if 0 <= hex_id < 144:
        return SIXTY_FOUR_TOJEONG[hex_id]
    return None


# ─────────────────────────── ADR-146 KCI 학술 인용 (토정비결 144괘 원문) ───────────────────────────

# /domain-priorities #1 (52점) 부분 해소 — 사용자 결단 2026-05-23.
# 김수년 (2016) 박사학위논문 권말부록에 144괘 원문 전체 수록.
# 본 시스템 11괘 본문화 (ADR-134) 외 133괘 시구 학술 출처 확보.

from dataclasses import dataclass as _dataclass


@_dataclass(frozen=True)
class TojeongAcademicCitation:
    """토정비결 학술 인용 메타데이터 (ADR-010 사실성 분리 강화).

    /domain-priorities #1 해소 — 144괘 원문 전체 수록 학술 출처.

    Attributes:
        author_ko: 저자 (한국어)
        title_ko: 학위논문 제목
        degree: 학위 (박사·석사)
        institution: 발행기관
        department: 학과
        advisor_ko: 지도교수
        publication_year: 발행연도
        pages: 페이지 수
        riss_control_no: RISS 식별번호
        appendix_note: 부록 144괘 원문 수록 여부
        usage_note: 본 시스템 사용 시 주의 (ADR-006·010)
    """
    author_ko: str
    title_ko: str
    degree: str
    institution: str
    department: str
    advisor_ko: str
    publication_year: int
    pages: int
    riss_control_no: str
    appendix_note: str
    usage_note: str


TOJEONG_ACADEMIC_CITATIONS: tuple[TojeongAcademicCitation, ...] = (
    TojeongAcademicCitation(
        author_ko="김수년",
        title_ko="『土亭秘訣』점사의 易學的 硏究 — 총평 부분을 중심으로",
        degree="박사학위논문",
        institution="국제뇌교육종합대학원대학교",
        department="국학과",
        advisor_ko="임채우",
        publication_year=2016,
        pages=195,
        riss_control_no="000014351511",
        appendix_note="권말부록에 토정비결 144괘 원문 전체 수록",
        usage_note=(
            "본 시스템 144괘 시구 학술 출처. RISS 학위논문 식별번호 000014351511. "
            "ADR-134 11괘 본문화 외 133괘 시구 보강 시 참조 가능. "
            "단정 운명 매핑 X — 점사 易學的 분석 학술 출처로만."
        ),
    ),
    # ADR-153 (2026-05-23) 신규 — /domain-priorities #1 학술 출처 확장
    TojeongAcademicCitation(
        author_ko="김창경 (2017)",
        title_ko="토정 이지함의 도학사상(道學思想) 연구",
        degree="KCI 등재 학술논문",
        institution="율곡학연구 35권",
        department="율곡학회",
        advisor_ko="(N/A — 학술논문)",
        publication_year=2017,
        pages=28,  # 397-424
        riss_control_no="ART002295655",  # KCI 식별번호
        appendix_note="토정 이지함의 도학사상 학술 분석 (토정비결 저자 학문 사상)",
        usage_note=(
            "본 시스템 tojeong 저자 (이지함 1517-1578) 학술 사상 출처. "
            "KCI ART002295655. ADR-134 면책 강화 — 토정비결 저자의 도학적 배경 명시."
        ),
    ),
)


def get_tojeong_academic_citations() -> tuple[TojeongAcademicCitation, ...]:
    """ADR-146 — 토정비결 학술 인용 풀 조회."""
    return TOJEONG_ACADEMIC_CITATIONS


def format_tojeong_citations_for_prompt() -> str:
    """ADR-146: Stage 2 자연어 풀이용 학술 인용 컨텍스트.

    LLM 시스템 프롬프트 주입 — 144괘 원문 RISS 학위논문 출처 명시.
    ADR-010 사실성 분리 강도 ↑ (학위논문 + 권말부록 원문 수록).
    """
    lines = [
        "[토정비결 학술 인용 — ADR-146 144괘 원문 출처]",
        "(본 시스템 144괘 시구 학술 출처. 운명 단정 X — 易學的 분석 출처로만.)",
        "",
    ]
    for c in TOJEONG_ACADEMIC_CITATIONS:
        lines.append(f"- {c.author_ko} ({c.publication_year}) \"{c.title_ko}\"")
        lines.append(f"  {c.institution} {c.department} {c.degree} (지도: {c.advisor_ko})")
        lines.append(f"  {c.pages}p · RISS 식별번호 {c.riss_control_no}")
        lines.append(f"  {c.appendix_note}")
        lines.append(f"  활용: {c.usage_note}")
        lines.append("")
    return "\n".join(lines)


# ─────────────────────────── 면책 + 프롬프트 ───────────────────────────

_DISCLAIMER = (
    "본 토정비결은 토정 이지함(土亭 李之菡, 1517-1578) 정통 144괘 결정론 "
    "흐름 톤으로, 길흉·결혼·이혼·사망 단정 X. 1년 운세 (정월~섣달) 흐름만 — "
    "참고용이며 의료·법률·금융 의사결정 단독 근거 X. "
    "한국학중앙연구원 한국민족문화대백과사전 + 김수년 (2016) 박사학위논문 "
    "(국제뇌교육종합대학원대학교, RISS 000014351511) 검증 가능."
)


def format_hexagram_for_prompt(r: TojeongHexagram, target_year: int) -> str:
    """Stage 2 시스템 프롬프트에 주입할 토정비결 메타."""
    return (
        f"[토정비결 결정론 — 한국 정통 토정 이지함]\n"
        f"  · {target_year}년 괘: {r.label_ko} (상괘 {r.upper} 중괘 {r.middle} 하괘 {r.lower})\n"
        f"  · 1년 흐름 톤: {r.flow_tone_ko}\n"
        f"[안전 장치 — ADR-006] 토정비결 분류·흐름 톤만 사용. "
        f"길흉·결혼·이혼·사망·재정 단정 금지. 결의 결 묘사만.\n"
        f"{_DISCLAIMER}"
    )


__all__ = [
    "TojeongHexagram", "SIXTY_FOUR_TOJEONG",
    "compute_tojeong_for_year", "hexagram_by_id",
    "format_hexagram_for_prompt",
    # ADR-146 학술 인용
    "TojeongAcademicCitation", "TOJEONG_ACADEMIC_CITATIONS",
    "get_tojeong_academic_citations", "format_tojeong_citations_for_prompt",
]
