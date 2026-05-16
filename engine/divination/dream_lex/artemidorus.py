"""아르테미도로스 『꿈의 해석(Oneirocritica)』 — 1차 분류 + 핵심 요소 사전.

3분류:
  - enhypnion: 비의미적 (생리·일상 잔재)
  - theorematic: 정리적 (문자적 미래 표상)
  - allegorical: 우의적 (상징·장기·해독)
"""

from __future__ import annotations
from typing import Any


ARTEMIDORUS_CLASSES = {
    "enhypnion": "비의미적 — 일상의 잔재·생리적 반응. 진단적 가치는 있으나 미래 예지 없음.",
    "theorematic": "정리적 — 가까운 미래의 사건이 문자 그대로 표상됨.",
    "allegorical": "우의적 — 장기적 미래를 상징과 비유로 보여줌. 해독이 필요.",
}

# 분류 1차 마커 — 결정론 1차 분류
_ENHYPNION_MARKERS = [
    "배고픔", "갈증", "추웠", "더웠", "화장실", "구토", "오줌", "방귀",
    "어제 만난", "어제 본", "회사에서", "방금 전", "어제", "그제",
    "지난주", "최근", "요즘", "오늘", "낮에 본",
]
_THEOREMATIC_MARKERS = [
    "정확히", "그대로", "내일", "다음 주", "예정된", "예약된",
    "약속한", "다가오는", "곧",
]
_ALLEGORICAL_MARKERS = [
    "이상한", "기괴한", "낯선", "신비로운", "변신", "날아",
    "초현실", "환상", "꿈속의 꿈", "용", "신", "천사", "악마",
    "마법", "주문", "예언", "오래된",
]


def classify_dream(text: str) -> dict[str, Any]:
    """결정론적 1차 분류 — 키워드 카운트 기반."""
    t = text or ""
    scores = {
        "enhypnion": sum(1 for k in _ENHYPNION_MARKERS if k in t),
        "theorematic": sum(1 for k in _THEOREMATIC_MARKERS if k in t),
        "allegorical": sum(1 for k in _ALLEGORICAL_MARKERS if k in t),
    }
    if max(scores.values()) == 0:
        cls = "allegorical"  # 기본 우의적
    else:
        cls = max(scores, key=lambda k: scores[k])
    return {
        "class": cls,
        "label": ARTEMIDORUS_CLASSES[cls],
        "scores": scores,
    }


# 아르테미도로스 핵심 요소 사전 (Oneirocritica 5권 중 자주 출현하는 100항목)
# 형식: 키워드 -> {meaning: 상징, polarity: 길/흉/중립}
ARTEMIDORUS_LEXICON: dict[str, dict[str, str]] = {
    # 동물
    "뱀": {"meaning": "치유와 변환, 적과 위험의 양가성", "polarity": "중립"},
    "용": {"meaning": "권위와 큰 흐름, 비범한 인물의 등장", "polarity": "길"},
    "호랑이": {"meaning": "강한 권력자·아버지·시험관", "polarity": "중립"},
    "사자": {"meaning": "왕권·지배·강한 동맹자", "polarity": "길"},
    "물고기": {"meaning": "재물·소식·잉태의 가능성", "polarity": "길"},
    "새": {"meaning": "소식·여행·자유로운 의지", "polarity": "중립"},
    "독수리": {"meaning": "권위 있는 후원자·승진", "polarity": "길"},
    "까마귀": {"meaning": "어두운 소식·경고", "polarity": "흉"},
    "개": {"meaning": "충실한 친구·하인·보호자", "polarity": "길"},
    "고양이": {"meaning": "은밀한 적·여성적 비밀", "polarity": "중립"},
    "쥐": {"meaning": "사소한 손실·은밀한 불안", "polarity": "흉"},
    "벌": {"meaning": "근면·작은 보상", "polarity": "길"},
    "거미": {"meaning": "음모·복잡한 관계의 그물", "polarity": "흉"},
    # 자연
    "해": {"meaning": "권력자·아버지·명료한 진리", "polarity": "길"},
    "달": {"meaning": "어머니·여성성·주기적 변화", "polarity": "중립"},
    "별": {"meaning": "운명·먼 희망", "polarity": "길"},
    "바다": {"meaning": "큰 무의식·기회와 위험", "polarity": "중립"},
    "강": {"meaning": "흐름·이행·삶의 경계", "polarity": "중립"},
    "비": {"meaning": "정화·은혜·재물", "polarity": "길"},
    "눈": {"meaning": "정지·결백·차가운 진실", "polarity": "중립"},
    "구름": {"meaning": "불확실·임시적 가림", "polarity": "중립"},
    "번개": {"meaning": "갑작스러운 진실·충격", "polarity": "중립"},
    "산": {"meaning": "오르는 시험·권위", "polarity": "중립"},
    "불": {"meaning": "정열·정화·파괴 양가", "polarity": "중립"},
    # 신체
    "이빨 빠짐": {"meaning": "가족의 변동·체력 점검", "polarity": "흉"},
    "머리카락": {"meaning": "생명력·재산의 유무", "polarity": "중립"},
    "피": {"meaning": "혈육·생명력의 누출", "polarity": "흉"},
    "벗은 몸": {"meaning": "맥락 의존 — 가난한 자엔 자유, 부유한 자엔 망신", "polarity": "중립"},
    "발": {"meaning": "이동·삶의 방향", "polarity": "중립"},
    "손": {"meaning": "행동·도움·약속", "polarity": "중립"},
    "심장": {"meaning": "본질·생명의 중심", "polarity": "중립"},
    # 행위
    "달리기": {"meaning": "급한 일·추진", "polarity": "중립"},
    "떨어짐": {"meaning": "지위·통제력의 상실 두려움", "polarity": "흉"},
    "오르기": {"meaning": "지위·이상의 추구", "polarity": "길"},
    "날기": {"meaning": "자유·초월·야망", "polarity": "길"},
    "수영": {"meaning": "감정의 흐름을 다스림", "polarity": "중립"},
    "싸움": {"meaning": "내적 갈등·결단의 시간", "polarity": "중립"},
    "결혼": {"meaning": "결합·새 시작·변화", "polarity": "중립"},
    "장례": {"meaning": "옛 자아의 정리·재생의 전조", "polarity": "중립"},
    "출산": {"meaning": "새 시작·창조", "polarity": "길"},
    "추격": {"meaning": "회피하는 두려움", "polarity": "흉"},
    "도둑": {"meaning": "예기치 못한 손실의 두려움", "polarity": "흉"},
    # 사물
    "거울": {"meaning": "자기 인식·진실의 반영", "polarity": "중립"},
    "칼": {"meaning": "결단·갈등·분리", "polarity": "중립"},
    "문": {"meaning": "전환·기회·선택", "polarity": "중립"},
    "다리": {"meaning": "두 영역의 연결", "polarity": "길"},
    "계단": {"meaning": "단계적 진보", "polarity": "길"},
    "열쇠": {"meaning": "비밀의 해독·기회 획득", "polarity": "길"},
    "황금": {"meaning": "본질적 가치·자아의 중심", "polarity": "길"},
    "은": {"meaning": "정제된 가치·달의 기운", "polarity": "길"},
    "보석": {"meaning": "고귀한 본질의 발견", "polarity": "길"},
    "관": {"meaning": "한 시기의 마감", "polarity": "중립"},
    "책": {"meaning": "지식·전생의 기억", "polarity": "길"},
    "편지": {"meaning": "기다리던 소식", "polarity": "중립"},
    "거울 깨짐": {"meaning": "자기 인식의 균열", "polarity": "흉"},
    # 장소
    "집": {"meaning": "자아·내면의 거주", "polarity": "중립"},
    "학교": {"meaning": "배움·시험·과거 정리", "polarity": "중립"},
    "병원": {"meaning": "치유의 필요·신체 점검", "polarity": "중립"},
    "법원": {"meaning": "판단의 자리·도덕적 시험", "polarity": "중립"},
    "감옥": {"meaning": "스스로 만든 속박", "polarity": "흉"},
    "신전": {"meaning": "정화·기도의 자리", "polarity": "길"},
    "시장": {"meaning": "관계와 거래의 장", "polarity": "중립"},
    "묘지": {"meaning": "조상·뿌리·과거 정리", "polarity": "중립"},
    # 색
    "흰색": {"meaning": "정결·시작", "polarity": "길"},
    "검은색": {"meaning": "무의식·끝", "polarity": "중립"},
    "붉은색": {"meaning": "정열·경고", "polarity": "중립"},
    "푸른색": {"meaning": "고요·신뢰", "polarity": "길"},
    "노란색": {"meaning": "지혜·황금의 가치", "polarity": "길"},
    # 인물
    "왕": {"meaning": "권위·아버지·체계", "polarity": "중립"},
    "여왕": {"meaning": "어머니·내면의 권위", "polarity": "중립"},
    "노인": {"meaning": "지혜·과거의 음성", "polarity": "길"},
    "아이": {"meaning": "새 시작·순수한 마음", "polarity": "길"},
    "낯선이": {"meaning": "자아의 무의식 측면", "polarity": "중립"},
    "친구": {"meaning": "지지·일상의 거울", "polarity": "길"},
    "적": {"meaning": "내면의 그림자", "polarity": "흉"},
    "거지": {"meaning": "결핍의 두려움", "polarity": "흉"},
    "도사": {"meaning": "내적 인도자", "polarity": "길"},
    "스님": {"meaning": "정화·수행의 부름", "polarity": "길"},
    # 변화
    "변신": {"meaning": "정체성의 전환", "polarity": "중립"},
    "사라짐": {"meaning": "통제 밖의 변화", "polarity": "중립"},
    "잃어버림": {"meaning": "가치의 점검", "polarity": "흉"},
    "찾음": {"meaning": "잃었던 자기 회복", "polarity": "길"},
    "재회": {"meaning": "오래된 관계의 회복", "polarity": "길"},
    "이별": {"meaning": "관계의 정리·새 자리", "polarity": "중립"},
    # 환경
    "어둠": {"meaning": "무의식·미지", "polarity": "중립"},
    "빛": {"meaning": "통찰·진리의 발현", "polarity": "길"},
    "안개": {"meaning": "혼란·전환기", "polarity": "중립"},
    "지진": {"meaning": "근본의 흔들림·변혁", "polarity": "흉"},
    "홍수": {"meaning": "감정의 압도", "polarity": "흉"},
    "태풍": {"meaning": "큰 변화의 도래", "polarity": "흉"},
    "무지개": {"meaning": "약속·희망", "polarity": "길"},
}


def lookup_artemidorus(text: str, limit: int = 8) -> list[dict[str, str]]:
    """꿈 텍스트에서 아르테미도로스 사전 키워드를 매칭."""
    if not text:
        return []
    found: list[dict[str, str]] = []
    for kw, data in ARTEMIDORUS_LEXICON.items():
        if kw in text:
            found.append({"keyword": kw, **data})
        if len(found) >= limit:
            break
    return found


__all__ = [
    "ARTEMIDORUS_CLASSES",
    "ARTEMIDORUS_LEXICON",
    "classify_dream",
    "lookup_artemidorus",
]
