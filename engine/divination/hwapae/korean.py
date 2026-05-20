"""ADR-025 한국 화투 48매 결정론 점패 엔진.

보고서 §3-7 본문화:
  · 48패 카드 데이터 (광 20 / 열끗 10 / 띠 5 / 피 1)
  · 3장 스프레드 알고리즘 (과거-현재-미래)
  · 계절 순행/역행 + 카테고리 밀집도 연산
  · permitted/forbidden 키워드 물리 강제 (ADR-006/010 정합)
  · school_variants 메타 격리 (ADR-002 패턴)

설계 (CLAUDE.md §0 + ADR-021/023/024 패턴 정합):
  · 결정론 100% (LLM 호출 0)
  · 기존 hwapae.py (타로 변형) 유지 + 본 모듈 별개 시스템
  · DEFAULT_DISCLAIMERS 강제 (ADR-006/010)

학술 출처 (vault/references/korean-hwapae-traditional.md):
  · 한국민족문화대백과사전 (encykorea.aks.ac.kr)
  · 국립민속박물관 e-museum (유물 일본 568)
  · Wikipedia Korean Hanafuda
  · Fuda Wiki (Hwatu section)
  · 아패영유(雅牌靈遊) 국문필사본 (3회 추첨 + 합산 알고리즘)

본 모듈은 보고서 핵심 5패 + 알고리즘 본문화. 48패 전수 데이터는
data/hwapae_korean_48.json 별도 영속화 가능 (후속 보강).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


# ─────────────────────────── 카테고리 점수 (보고서 §3) ───────────────────────────


_CATEGORY_SCORES: dict[str, int] = {
    "광": 20,
    "열끗": 10,
    "띠": 5,
    "피": 1,
}


CategoryType = Literal["광", "열끗", "띠", "피"]


# ─────────────────────────── 카드 데이터 (보고서 §5 일부) ───────────────────────────


@dataclass(frozen=True)
class HwapaeCard:
    """단일 화패 카드 (보고서 §5 JSON 명세).

    Attributes:
        id: "01-01-gwang" 형식 (월-순서-카테고리).
        month: 1~12.
        card_index_in_month: 1~4 (월별 4매).
        name_ko: 한국어 명칭 (예: "송학 (광)").
        category: 광·열끗·띠·피.
        score: 20·10·5·1.
        symbol: 식물/동물/사물 기호.
        traditional_meaning: 전통 점패 상징 (객관 묘사).
        permitted_keywords: 페르소나 허용 키워드.
        forbidden_keywords: 페르소나 금지 키워드 (ADR-006 강제).
    """

    id: str
    month: int
    card_index_in_month: int
    name_ko: str
    category: str
    score: int
    symbol: str
    traditional_meaning: str
    permitted_keywords: tuple[str, ...]
    forbidden_keywords: tuple[str, ...]


# ADR-079: 표준 화투 48장 전수 본문화.
# 출처: 한국민족문화대백과사전·국립민속박물관 e-museum·Fuda Wiki·Wikipedia Hanafuda.
# 구조: 12月 × 4매. 광 5장(1·3·8·11·12月) + 열끗·띠·피 분포 (표준).
HWAPAE_CARDS: dict[str, HwapaeCard] = {
    # ── 1月 송학 (소나무·학) ──
    "01-01-gwang": HwapaeCard(
        id="01-01-gwang", month=1, card_index_in_month=1,
        name_ko="송학 (광)", category="광", score=20,
        symbol="소나무·학·일출",
        traditional_meaning="장수와 복록을 상징하며 새로운 흐름의 시작을 알리는 강한 양(陽)의 기운의 태동",
        permitted_keywords=("시작", "기반", "장수", "흔들리지 않음", "명료한 흐름"),
        forbidden_keywords=("대성공 확정", "무병장수", "로또 당첨", "운명적 결정"),
    ),
    "01-02-tti": HwapaeCard(
        id="01-02-tti", month=1, card_index_in_month=2,
        name_ko="송학 (홍단)", category="띠", score=5,
        symbol="소나무·붉은 띠",
        traditional_meaning="새해 첫 결의를 알리는 붉은 띠의 기운 (홍단 약 7끗)",
        permitted_keywords=("결의", "다짐", "선언", "공표"),
        forbidden_keywords=("승급 확정", "직위 획득"),
    ),
    "01-03-pi": HwapaeCard(
        id="01-03-pi", month=1, card_index_in_month=3,
        name_ko="송학 (피1)", category="피", score=1,
        symbol="소나무",
        traditional_meaning="새해 일상의 축적된 소소한 기운",
        permitted_keywords=("일상", "기본", "축적"),
        forbidden_keywords=("재물 확정", "성공 보장"),
    ),
    "01-04-pi": HwapaeCard(
        id="01-04-pi", month=1, card_index_in_month=4,
        name_ko="송학 (피2)", category="피", score=1,
        symbol="소나무",
        traditional_meaning="새해 일상 누적의 두 번째 기운",
        permitted_keywords=("일상 반복", "기반 축적"),
        forbidden_keywords=("운명 결정", "확정 사건"),
    ),

    # ── 2月 매조 (매화·휘파람새) ──
    "02-01-yeol": HwapaeCard(
        id="02-01-yeol", month=2, card_index_in_month=1,
        name_ko="매조 (열끗)", category="열끗", score=10,
        symbol="매화·휘파람새",
        traditional_meaning="이른 봄 얼어붙은 상황 속에서 가장 먼저 변화의 조짐을 알리며 날아드는 동적인 소식",
        permitted_keywords=("초기 소식", "동적인 조짐", "빠른 이동", "해빙기"),
        forbidden_keywords=("승진 통보", "소송 승리", "재물 획득"),
    ),
    "02-02-tti": HwapaeCard(
        id="02-02-tti", month=2, card_index_in_month=2,
        name_ko="매조 (홍단)", category="띠", score=5,
        symbol="매화·붉은 띠",
        traditional_meaning="초봄의 결심을 알리는 두 번째 홍단 (홍단 3매 조합 기능)",
        permitted_keywords=("초봄 다짐", "조심스러운 결단"),
        forbidden_keywords=("계약 체결 확정", "결혼 확정"),
    ),
    "02-03-pi": HwapaeCard(
        id="02-03-pi", month=2, card_index_in_month=3,
        name_ko="매조 (피1)", category="피", score=1,
        symbol="매화",
        traditional_meaning="초봄 일상의 잔잔한 흐름",
        permitted_keywords=("잔잔한 흐름", "준비"),
        forbidden_keywords=("재물 확정",),
    ),
    "02-04-pi": HwapaeCard(
        id="02-04-pi", month=2, card_index_in_month=4,
        name_ko="매조 (피2)", category="피", score=1,
        symbol="매화",
        traditional_meaning="초봄 일상 반복의 기운",
        permitted_keywords=("반복", "정착"),
        forbidden_keywords=("성공 보장",),
    ),

    # ── 3月 사쿠라 (벚꽃) ──
    "03-01-gwang": HwapaeCard(
        id="03-01-gwang", month=3, card_index_in_month=1,
        name_ko="사쿠라 (광)", category="광", score=20,
        symbol="벚꽃·만막",
        traditional_meaning="봄의 화려함이 절정에 달하여 사람과 시선이 운집하는 극도로 팽창된 에너지의 순간",
        permitted_keywords=("화려한 절정", "군중의 운집", "일시적 팽창", "시선 집중"),
        forbidden_keywords=("대성공", "유명인사 됨", "영원한 영광"),
    ),
    "03-02-tti": HwapaeCard(
        id="03-02-tti", month=3, card_index_in_month=2,
        name_ko="사쿠라 (홍단)", category="띠", score=5,
        symbol="벚꽃·붉은 띠",
        traditional_meaning="만개한 봄의 공식 선언 (홍단 3매 조합 완성)",
        permitted_keywords=("공식 선언", "축하", "절정의 다짐"),
        forbidden_keywords=("일생 영광", "최고 도달"),
    ),
    "03-03-pi": HwapaeCard(
        id="03-03-pi", month=3, card_index_in_month=3,
        name_ko="사쿠라 (피1)", category="피", score=1,
        symbol="벚꽃잎",
        traditional_meaning="봄꽃 흩날리는 일상의 흐름",
        permitted_keywords=("흩날림", "분산", "일상"),
        forbidden_keywords=("흩어짐 확정", "이별 확정"),
    ),
    "03-04-pi": HwapaeCard(
        id="03-04-pi", month=3, card_index_in_month=4,
        name_ko="사쿠라 (피2)", category="피", score=1,
        symbol="벚꽃잎",
        traditional_meaning="봄꽃 일상의 두 번째 흐름",
        permitted_keywords=("일상", "흐름"),
        forbidden_keywords=("결정적 사건",),
    ),

    # ── 4月 흑싸리 (등나무 또는 검은 띠) ──
    "04-01-yeol": HwapaeCard(
        id="04-01-yeol", month=4, card_index_in_month=1,
        name_ko="흑싸리 (열끗)", category="열끗", score=10,
        symbol="등나무·두견새",
        traditional_meaning="늦봄 부드러우나 끈질긴 흐름. 인내·은밀한 진전",
        permitted_keywords=("인내", "은밀한 진전", "끈질김"),
        forbidden_keywords=("끝까지 버팀 확정", "승리"),
    ),
    "04-02-tti": HwapaeCard(
        id="04-02-tti", month=4, card_index_in_month=2,
        name_ko="흑싸리 (초단)", category="띠", score=5,
        symbol="등나무·검은 띠",
        traditional_meaning="늦봄의 조심스러운 약속 (초단 3매 조합 기능)",
        permitted_keywords=("약속", "신중한 결심"),
        forbidden_keywords=("계약 확정", "맹세 영속"),
    ),
    "04-03-pi": HwapaeCard(
        id="04-03-pi", month=4, card_index_in_month=3,
        name_ko="흑싸리 (피1)", category="피", score=1,
        symbol="등나무 잎",
        traditional_meaning="늦봄 일상의 누적",
        permitted_keywords=("누적", "반복"),
        forbidden_keywords=("재물 확정",),
    ),
    "04-04-pi": HwapaeCard(
        id="04-04-pi", month=4, card_index_in_month=4,
        name_ko="흑싸리 (피2)", category="피", score=1,
        symbol="등나무 잎",
        traditional_meaning="늦봄 일상 두 번째 누적",
        permitted_keywords=("일상", "축적"),
        forbidden_keywords=("성공 보장",),
    ),

    # ── 5月 난초 (창포·붓꽃) ──
    "05-01-yeol": HwapaeCard(
        id="05-01-yeol", month=5, card_index_in_month=1,
        name_ko="난초 (열끗)", category="열끗", score=10,
        symbol="창포·다리 (花札 八橋)",
        traditional_meaning="초여름 다리를 건너는 흐름. 새 영역으로의 이행",
        permitted_keywords=("이행", "건너감", "새 영역"),
        forbidden_keywords=("승진 확정", "이주 성공"),
    ),
    "05-02-tti": HwapaeCard(
        id="05-02-tti", month=5, card_index_in_month=2,
        name_ko="난초 (초단)", category="띠", score=5,
        symbol="창포·검은 띠",
        traditional_meaning="초여름의 약속 (초단 3매 조합)",
        permitted_keywords=("초여름 다짐", "조용한 약속"),
        forbidden_keywords=("계약 확정",),
    ),
    "05-03-pi": HwapaeCard(
        id="05-03-pi", month=5, card_index_in_month=3,
        name_ko="난초 (피1)", category="피", score=1,
        symbol="창포 잎",
        traditional_meaning="초여름 일상",
        permitted_keywords=("일상", "흐름"),
        forbidden_keywords=("재물 확정",),
    ),
    "05-04-pi": HwapaeCard(
        id="05-04-pi", month=5, card_index_in_month=4,
        name_ko="난초 (피2)", category="피", score=1,
        symbol="창포 잎",
        traditional_meaning="초여름 일상 반복",
        permitted_keywords=("반복", "정착"),
        forbidden_keywords=("성공 보장",),
    ),

    # ── 6月 모란 (목단·나비) ──
    "06-01-yeol": HwapaeCard(
        id="06-01-yeol", month=6, card_index_in_month=1,
        name_ko="모란 (열끗)", category="열끗", score=10,
        symbol="목단·나비",
        traditional_meaning="여름 화려한 부귀의 짙은 기운. 풍요로움",
        permitted_keywords=("풍요", "성숙", "짙은 색감"),
        forbidden_keywords=("부귀 확정", "재물 획득"),
    ),
    "06-02-tti": HwapaeCard(
        id="06-02-tti", month=6, card_index_in_month=2,
        name_ko="모란 (청단)", category="띠", score=5,
        symbol="목단·푸른 띠",
        traditional_meaning="청단 3매 조합 기능 (학문·예술 결의)",
        permitted_keywords=("학예 다짐", "결의"),
        forbidden_keywords=("학위 획득", "예술적 성공 확정"),
    ),
    "06-03-pi": HwapaeCard(
        id="06-03-pi", month=6, card_index_in_month=3,
        name_ko="모란 (피1)", category="피", score=1,
        symbol="목단 잎",
        traditional_meaning="한여름 일상",
        permitted_keywords=("일상", "유지"),
        forbidden_keywords=("재물 확정",),
    ),
    "06-04-pi": HwapaeCard(
        id="06-04-pi", month=6, card_index_in_month=4,
        name_ko="모란 (피2)", category="피", score=1,
        symbol="목단 잎",
        traditional_meaning="한여름 일상 반복",
        permitted_keywords=("반복", "지속"),
        forbidden_keywords=("성공 보장",),
    ),

    # ── 7月 홍싸리 (싸리·멧돼지) ──
    "07-01-yeol": HwapaeCard(
        id="07-01-yeol", month=7, card_index_in_month=1,
        name_ko="홍싸리 (열끗)", category="열끗", score=10,
        symbol="싸리·멧돼지",
        traditional_meaning="여름 끝 무렵 돌진하는 야성의 동적 흐름",
        permitted_keywords=("돌진", "야성", "결단"),
        forbidden_keywords=("돌파 확정", "승부 승리"),
    ),
    "07-02-tti": HwapaeCard(
        id="07-02-tti", month=7, card_index_in_month=2,
        name_ko="홍싸리 (초단)", category="띠", score=5,
        symbol="싸리·검은 띠",
        traditional_meaning="여름 끝의 조용한 결심 (초단 3매 조합)",
        permitted_keywords=("결심", "다짐"),
        forbidden_keywords=("계약 확정",),
    ),
    "07-03-pi": HwapaeCard(
        id="07-03-pi", month=7, card_index_in_month=3,
        name_ko="홍싸리 (피1)", category="피", score=1,
        symbol="싸리 잎",
        traditional_meaning="여름 끝 일상",
        permitted_keywords=("일상", "정착"),
        forbidden_keywords=("재물 확정",),
    ),
    "07-04-pi": HwapaeCard(
        id="07-04-pi", month=7, card_index_in_month=4,
        name_ko="홍싸리 (피2)", category="피", score=1,
        symbol="싸리 잎",
        traditional_meaning="여름 끝 일상 반복",
        permitted_keywords=("반복",),
        forbidden_keywords=("성공 보장",),
    ),

    # ── 8月 공산 (텅 빈 산·달) ──
    "08-01-gwang": HwapaeCard(
        id="08-01-gwang", month=8, card_index_in_month=1,
        name_ko="공산 (광)", category="광", score=20,
        symbol="텅 빈 산·달·기러기",
        traditional_meaning="달과 기러기만 남은 적막한 산처럼 모든 외부 활동이 정지된 거시적 비움의 상태",
        permitted_keywords=("성찰", "비움", "정중동", "고요한 응시"),
        forbidden_keywords=("고립무원", "단절 확정", "외로움의 영속"),
    ),
    "08-02-yeol": HwapaeCard(
        id="08-02-yeol", month=8, card_index_in_month=2,
        name_ko="공산 (열끗·기러기)", category="열끗", score=10,
        symbol="기러기 세 마리·달",
        traditional_meaning="가을 기러기의 무리 이동. 집단적 흐름의 전환",
        permitted_keywords=("집단 이동", "전환", "이주"),
        forbidden_keywords=("이별 확정", "관계 단절 영속"),
    ),
    "08-03-pi": HwapaeCard(
        id="08-03-pi", month=8, card_index_in_month=3,
        name_ko="공산 (피1)", category="피", score=1,
        symbol="가을 풀",
        traditional_meaning="가을 일상",
        permitted_keywords=("일상", "잔잔함"),
        forbidden_keywords=("재물 확정",),
    ),
    "08-04-pi": HwapaeCard(
        id="08-04-pi", month=8, card_index_in_month=4,
        name_ko="공산 (피2)", category="피", score=1,
        symbol="가을 풀",
        traditional_meaning="가을 일상 반복",
        permitted_keywords=("반복", "축적"),
        forbidden_keywords=("성공 보장",),
    ),

    # ── 9月 국화 (국준·잔) ──
    "09-01-yeol": HwapaeCard(
        id="09-01-yeol", month=9, card_index_in_month=1,
        name_ko="국화 (열끗·국준)", category="열끗", score=10,
        symbol="국화·술잔",
        traditional_meaning="가을 깊은 음미의 짧은 기쁨 (국준 단독 5끗 기능)",
        permitted_keywords=("음미", "짧은 기쁨", "되돌아봄"),
        forbidden_keywords=("축하 확정", "기쁨 영속"),
    ),
    "09-02-tti": HwapaeCard(
        id="09-02-tti", month=9, card_index_in_month=2,
        name_ko="국화 (청단)", category="띠", score=5,
        symbol="국화·푸른 띠",
        traditional_meaning="청단 3매 조합 기능 (지조·절개)",
        permitted_keywords=("지조", "절개"),
        forbidden_keywords=("명예 확정",),
    ),
    "09-03-pi": HwapaeCard(
        id="09-03-pi", month=9, card_index_in_month=3,
        name_ko="국화 (피1)", category="피", score=1,
        symbol="국화 잎",
        traditional_meaning="가을 깊은 일상",
        permitted_keywords=("일상", "잔잔함"),
        forbidden_keywords=("재물 확정",),
    ),
    "09-04-pi": HwapaeCard(
        id="09-04-pi", month=9, card_index_in_month=4,
        name_ko="국화 (피2)", category="피", score=1,
        symbol="국화 잎",
        traditional_meaning="가을 깊은 일상 반복",
        permitted_keywords=("반복",),
        forbidden_keywords=("성공 보장",),
    ),

    # ── 10月 단풍 (사슴) ──
    "10-01-yeol": HwapaeCard(
        id="10-01-yeol", month=10, card_index_in_month=1,
        name_ko="단풍 (열끗·사슴)", category="열끗", score=10,
        symbol="단풍·사슴",
        traditional_meaning="늦가을 외로운 행로. 고독한 결단 (시카토 五光 변형)",
        permitted_keywords=("고독한 결단", "단독 행로"),
        forbidden_keywords=("고립 확정", "사회적 단절"),
    ),
    "10-02-tti": HwapaeCard(
        id="10-02-tti", month=10, card_index_in_month=2,
        name_ko="단풍 (청단)", category="띠", score=5,
        symbol="단풍·푸른 띠",
        traditional_meaning="청단 3매 조합 (사색·고독한 깊이)",
        permitted_keywords=("사색", "깊이"),
        forbidden_keywords=("학위 확정",),
    ),
    "10-03-pi": HwapaeCard(
        id="10-03-pi", month=10, card_index_in_month=3,
        name_ko="단풍 (피1)", category="피", score=1,
        symbol="단풍잎",
        traditional_meaning="늦가을 일상",
        permitted_keywords=("일상", "변화"),
        forbidden_keywords=("재물 확정",),
    ),
    "10-04-pi": HwapaeCard(
        id="10-04-pi", month=10, card_index_in_month=4,
        name_ko="단풍 (피2)", category="피", score=1,
        symbol="단풍잎",
        traditional_meaning="늦가을 일상 반복",
        permitted_keywords=("반복",),
        forbidden_keywords=("성공 보장",),
    ),

    # ── 11月 오동 (봉황) ──
    "11-01-gwang": HwapaeCard(
        id="11-01-gwang", month=11, card_index_in_month=1,
        name_ko="오동 (광)", category="광", score=20,
        symbol="오동나무·봉황",
        traditional_meaning="새로운 차원의 도약을 알리는 거시적 변혁의 시점 (한국 통설: 11월 오동)",
        permitted_keywords=("질적 변혁", "새 차원", "도약", "거시적 변화"),
        forbidden_keywords=("출세 확정", "권력 획득", "최상위 도달"),
    ),
    "11-02-pi-bonus": HwapaeCard(
        id="11-02-pi-bonus", month=11, card_index_in_month=2,
        name_ko="오동 (쌍피)", category="피", score=1,
        symbol="오동 잎 (쌍피)",
        traditional_meaning="오동 쌍피 — 피 2장 효과 (한국 화투 변형)",
        permitted_keywords=("이중 누적", "확장된 일상"),
        forbidden_keywords=("재물 두 배",),
    ),
    "11-03-pi": HwapaeCard(
        id="11-03-pi", month=11, card_index_in_month=3,
        name_ko="오동 (피1)", category="피", score=1,
        symbol="오동 잎",
        traditional_meaning="초겨울 일상",
        permitted_keywords=("일상", "조용함"),
        forbidden_keywords=("재물 확정",),
    ),
    "11-04-pi": HwapaeCard(
        id="11-04-pi", month=11, card_index_in_month=4,
        name_ko="오동 (피2)", category="피", score=1,
        symbol="오동 잎",
        traditional_meaning="초겨울 일상 반복",
        permitted_keywords=("반복",),
        forbidden_keywords=("성공 보장",),
    ),

    # ── 12月 비 (수양버들·우산) ──
    "12-01-gwang": HwapaeCard(
        id="12-01-gwang", month=12, card_index_in_month=1,
        name_ko="비 (광)", category="광", score=20,
        symbol="비·수양버들·우산",
        traditional_meaning="한 해의 종결과 정화를 알리는 거시적 비움 (한국 통설: 12월 비)",
        permitted_keywords=("정화", "종결", "비움", "다시 시작 준비"),
        forbidden_keywords=("재난 확정", "파산", "이별의 영속"),
    ),
    "12-02-yeol": HwapaeCard(
        id="12-02-yeol", month=12, card_index_in_month=2,
        name_ko="비 (열끗·제비)", category="열끗", score=10,
        symbol="제비·비",
        traditional_meaning="겨울비 속 제비의 소식. 예상치 못한 전갈",
        permitted_keywords=("예상치 못한 소식", "전갈"),
        forbidden_keywords=("재난 통보", "사고 발생"),
    ),
    "12-03-tti": HwapaeCard(
        id="12-03-tti", month=12, card_index_in_month=3,
        name_ko="비 (띠)", category="띠", score=5,
        symbol="비·우산·띠",
        traditional_meaning="해 저무는 결심. 마지막 다짐",
        permitted_keywords=("마무리 결단", "정리"),
        forbidden_keywords=("최종 결정 확정",),
    ),
    "12-04-pi-bonus": HwapaeCard(
        id="12-04-pi-bonus", month=12, card_index_in_month=4,
        name_ko="비 (쌍피)", category="피", score=1,
        symbol="비·우산 (쌍피)",
        traditional_meaning="비 쌍피 — 한 해 마무리 이중 누적",
        permitted_keywords=("정리 누적", "마무리 일상"),
        forbidden_keywords=("재물 두 배", "마지막 결산"),
    ),
}


# ─────────────────────────── ADR-006/010 면책 (보고서 §8) ───────────────────────────


DEFAULT_DISCLAIMERS: list[str] = [
    "본 화패점 결과는 한국 전통 민속 문화의 계절 기호학과 수학적 배열 확률에 기반한 에너지 경향성 묘사이며 결혼·연애·재물·수명 단정 예언이 아닙니다.",
    "한국민족문화대백과사전·국립민속박물관 출처 + 아패영유(雅牌靈遊) 전통 골패점 알고리즘 인용입니다.",
    "permitted_keywords 범위 내 묘사만 채택하며 forbidden_keywords (대성공 확정·운명적 결정·재난 확정 등) 단정 표현은 차단합니다.",
]


# 보고서 §8 forbidden 패턴 (출력 검증용)
FORBIDDEN_OUTPUT_PATTERNS: tuple[str, ...] = (
    "대성공 확정",
    "무병장수",
    "로또 당첨",
    "운명적 결정",
    "출세 확정",
    "권력 획득",
    "재난 확정",
    "파산",
    "이별의 영속",
    "100% 성공",
    "운명이 결정",
    "큰 돈을 벌게 됨",
)


# ─────────────────────────── 결과 dataclass ───────────────────────────


SpreadPositionType = Literal["과거", "현재", "미래"]


@dataclass(frozen=True)
class HwapaeSpreadResult:
    """3장 스프레드 결정론 분석 결과 (보고서 §4 + §6).

    Attributes:
        cards: 3장 (과거·현재·미래 순서).
        positions: 위치명 매핑.
        total_score: 3장 점수 합산.
        category_distribution: 광·열끗·띠·피 분포.
        is_sequential: 계절 순행 여부 (월 오름차순).
        is_reverse: 계절 역행 여부.
        category_dominance: 가장 많은 카테고리 (없으면 None).
        interpretation_facts: 알고리즘 객관 사실 (페르소나 입력용).
        disclaimers: ADR-006/010/014 면책 강제.
        school: 학파 명시.
    """

    cards: tuple[HwapaeCard, HwapaeCard, HwapaeCard]
    positions: tuple[str, str, str] = ("과거", "현재", "미래")
    total_score: int = 0
    category_distribution: dict[str, int] = field(default_factory=dict)
    is_sequential: bool = False
    is_reverse: bool = False
    category_dominance: str | None = None
    interpretation_facts: list[str] = field(default_factory=list)
    disclaimers: list[str] = field(default_factory=list)
    school: str = "한국 전통 화투 + 아패영유 골패점"

    def to_dict(self) -> dict:
        return {
            "school": self.school,
            "cards": [c.name_ko for c in self.cards],
            "positions": list(self.positions),
            "total_score": self.total_score,
            "category_distribution": self.category_distribution,
            "is_sequential": self.is_sequential,
            "is_reverse": self.is_reverse,
            "category_dominance": self.category_dominance,
            "interpretation_facts": self.interpretation_facts,
            "disclaimers": self.disclaimers,
        }


# ─────────────────────────── 알고리즘 (보고서 §4·§6) ───────────────────────────


def _is_sequential(months: tuple[int, int, int]) -> bool:
    """계절 순행 (월 오름차순, 단조 증가)."""
    return months[0] < months[1] < months[2]


def _is_reverse(months: tuple[int, int, int]) -> bool:
    """계절 역행 (월 내림차순)."""
    return months[0] > months[1] > months[2]


def _category_distribution(cards: tuple[HwapaeCard, ...]) -> dict[str, int]:
    """광·열끗·띠·피 분포 카운트."""
    dist: dict[str, int] = {"광": 0, "열끗": 0, "띠": 0, "피": 0}
    for c in cards:
        if c.category in dist:
            dist[c.category] += 1
    return dist


def _category_dominance(distribution: dict[str, int]) -> str | None:
    """가장 많은 카테고리 (2장 이상이면 dominant)."""
    if not distribution:
        return None
    max_cat = max(distribution.items(), key=lambda kv: kv[1])
    if max_cat[1] >= 2:
        return max_cat[0]
    return None


def three_card_spread(card_ids: tuple[str, str, str]) -> HwapaeSpreadResult:
    """3장 스프레드 결정론 분석 (보고서 §4).

    Args:
        card_ids: 카드 ID 3개 (과거·현재·미래 순서).

    Returns:
        HwapaeSpreadResult — 객관 사실 + 알고리즘 결과 + 면책.

    Raises:
        ValueError: 알 수 없는 카드 ID.

    설계 (CLAUDE.md §0 결정론 + LLM 분리):
        · 결정론 100% (LLM 호출 0)
        · permitted_keywords 범위만 페르소나에 전달 (forbidden 차단)
        · ADR-006/010 disclaimers 자동 포함
    """
    cards = []
    for cid in card_ids:
        if cid not in HWAPAE_CARDS:
            raise ValueError(f"알 수 없는 카드 ID: {cid!r}")
        cards.append(HWAPAE_CARDS[cid])

    cards_tuple = (cards[0], cards[1], cards[2])
    months = (cards[0].month, cards[1].month, cards[2].month)
    total = sum(c.score for c in cards)
    dist = _category_distribution(cards_tuple)
    seq = _is_sequential(months)
    rev = _is_reverse(months)
    dom = _category_dominance(dist)

    facts: list[str] = []

    # 카드 의미 (permitted_keywords 범위)
    for pos, card in zip(("과거", "현재", "미래"), cards):
        facts.append(f"{pos}: {card.name_ko} — {card.traditional_meaning}")

    # 계절 흐름
    if seq:
        facts.append("계절 순행 — 자연의 순리에 따르는 지연 없는 에너지 흐름")
    elif rev:
        facts.append("계절 역행 — 흐름의 역행, 내면적 성찰과 회고의 에너지")
    else:
        facts.append("계절 비선형 — 다층적 흐름, 단순 시간선 외 작용")

    # 카테고리 우세
    if dom:
        facts.append(f"{dom} 카테고리 우세 ({dist[dom]}장) — 해당 영역 에너지 집중")

    # 점수 (아패영유 3구간)
    if total >= 35:
        facts.append(f"총 점수 {total} — 상상 구간 (강한 양적 에너지 집중)")
    elif total >= 20:
        facts.append(f"총 점수 {total} — 상중 구간 (중간 균형 에너지)")
    else:
        facts.append(f"총 점수 {total} — 하하 구간 (미세 기반 에너지)")

    return HwapaeSpreadResult(
        cards=cards_tuple,
        positions=("과거", "현재", "미래"),
        total_score=total,
        category_distribution=dist,
        is_sequential=seq,
        is_reverse=rev,
        category_dominance=dom,
        interpretation_facts=facts,
        disclaimers=list(DEFAULT_DISCLAIMERS),
        school="한국 전통 화투 + 아패영유 골패점",
    )


# ─────────────────────────── 출력 검증 (보고서 §8) ───────────────────────────


def has_forbidden_output(text: str) -> bool:
    """페르소나 LLM 출력에 금지 패턴 포함 여부.

    True 반환 시 페르소나 응답 차단 + 안전 기본 응답 대체 의무.
    """
    if not text or not isinstance(text, str):
        return False
    for p in FORBIDDEN_OUTPUT_PATTERNS:
        if p in text:
            return True
    return False


def get_permitted_keywords(card_id: str) -> tuple[str, ...]:
    """단일 카드의 페르소나 허용 키워드 (LLM 시스템 프롬프트 주입용)."""
    card = HWAPAE_CARDS.get(card_id)
    if card is None:
        return ()
    return card.permitted_keywords


__all__ = [
    "DEFAULT_DISCLAIMERS",
    "FORBIDDEN_OUTPUT_PATTERNS",
    "HWAPAE_CARDS",
    "HwapaeCard",
    "HwapaeSpreadResult",
    "three_card_spread",
    "has_forbidden_output",
    "get_permitted_keywords",
]
