"""한국 민간 해몽 — 6대 카테고리 사전.

카테고리:
  - 태몽(胎夢): 잉태·자녀 예지
  - 재물몽: 횡재·손실
  - 합격몽: 시험·승진
  - 죽음몽(逆夢): 죽음 = 흔히 길몽 역해(逆解)
  - 가위눌림: 수면마비·심리 압박
  - 이별몽: 관계의 변화
"""

from __future__ import annotations
from typing import Any


KOREAN_FOLK_CATEGORIES = {
    "태몽": "임신·자녀 잉태의 예지몽. 동물·과일·자연물의 강렬한 인상이 특징.",
    "재물몽": "금전·재물의 득실에 관한 꿈. 특정 사물의 등장 형태가 길흉 결정.",
    "합격몽": "시험·승진·취업·합격에 관한 예지. 오르기·날기·문 통과가 핵심 모티프.",
    "죽음몽": "죽음·장례·관 — 한국 민간에선 새 시작의 역몽으로 길몽 분류.",
    "가위눌림": "수면마비. 영적 압박 또는 스트레스·수면자세 문제로 해석.",
    "이별몽": "관계의 정리·변화. 헤어짐·재회·실종 모티프.",
}


# ─────────────────────────── 태몽(胎夢) ───────────────────────────
TAEMONG: dict[str, dict[str, str]] = {
    "구렁이": {"meaning": "큰 인물의 자녀(아들) 잉태 — 권력·재물", "polarity": "길", "gender_hint": "남"},
    "뱀": {"meaning": "지혜로운 자녀 잉태 — 학자·문인", "polarity": "길", "gender_hint": "남"},
    "백사": {"meaning": "귀한 자녀 — 특별한 운명의 아이", "polarity": "길", "gender_hint": "남"},
    "용": {"meaning": "큰 인물(왕재) 잉태 — 최상의 태몽", "polarity": "길", "gender_hint": "남"},
    "이무기": {"meaning": "잠재력 큰 자녀 — 후일 대성", "polarity": "길", "gender_hint": "남"},
    "호랑이": {"meaning": "강한 기상의 자녀 — 무관·지도자", "polarity": "길", "gender_hint": "남"},
    "곰": {"meaning": "강건한 자녀 — 신체·근력 강함", "polarity": "길", "gender_hint": "남"},
    "잉어": {"meaning": "출세하는 자녀 — 입신양명", "polarity": "길", "gender_hint": "남"},
    "큰 물고기": {"meaning": "재능 있는 자녀 — 큰 성취", "polarity": "길", "gender_hint": "중립"},
    "복숭아": {"meaning": "딸 — 미모와 다정함", "polarity": "길", "gender_hint": "여"},
    "사과": {"meaning": "딸 — 단정하고 영민", "polarity": "길", "gender_hint": "여"},
    "감": {"meaning": "총명한 자녀 — 학문적 성취", "polarity": "길", "gender_hint": "중립"},
    "배": {"meaning": "딸 — 청순하고 부드러움", "polarity": "길", "gender_hint": "여"},
    "포도": {"meaning": "다산·다복 — 여러 자녀의 가능성", "polarity": "길", "gender_hint": "중립"},
    "밤": {"meaning": "딸 — 견고한 성품", "polarity": "길", "gender_hint": "여"},
    "꽃": {"meaning": "딸 — 아름다운 여아", "polarity": "길", "gender_hint": "여"},
    "장미": {"meaning": "딸 — 화려하고 정열적", "polarity": "길", "gender_hint": "여"},
    "백합": {"meaning": "딸 — 청초하고 고결", "polarity": "길", "gender_hint": "여"},
    "해": {"meaning": "왕재의 자녀 — 큰 권위", "polarity": "길", "gender_hint": "남"},
    "달": {"meaning": "딸 — 우아하고 지혜로움", "polarity": "길", "gender_hint": "여"},
    "별": {"meaning": "재능 있는 자녀 — 특별한 운명", "polarity": "길", "gender_hint": "중립"},
    "북두칠성": {"meaning": "비범한 자녀 — 큰 인물", "polarity": "길", "gender_hint": "중립"},
    "보석": {"meaning": "귀한 자녀 — 보배 같은 아이", "polarity": "길", "gender_hint": "중립"},
    "황금": {"meaning": "부귀의 자녀 — 재물 풍요", "polarity": "길", "gender_hint": "중립"},
    "금반지": {"meaning": "결혼·잉태의 길조", "polarity": "길", "gender_hint": "중립"},
    "은가락지": {"meaning": "딸 — 정숙한 여아", "polarity": "길", "gender_hint": "여"},
    "산삼": {"meaning": "비범한 자녀 — 귀인", "polarity": "길", "gender_hint": "남"},
    "거북이": {"meaning": "장수·복록의 자녀", "polarity": "길", "gender_hint": "중립"},
    "학": {"meaning": "고고한 자녀 — 학문·예술", "polarity": "길", "gender_hint": "중립"},
    "봉황": {"meaning": "최상의 태몽 — 왕비·왕족", "polarity": "길", "gender_hint": "여"},
    "공작": {"meaning": "미모의 딸 — 화려한 자녀", "polarity": "길", "gender_hint": "여"},
    "토끼": {"meaning": "총명한 딸", "polarity": "길", "gender_hint": "여"},
    "돼지": {"meaning": "재물복 자녀 — 부유하게 자람", "polarity": "길", "gender_hint": "중립"},
    "황소": {"meaning": "강건한 자녀 — 우직·근면", "polarity": "길", "gender_hint": "남"},
    "검은 황소": {"meaning": "권력의 자녀", "polarity": "길", "gender_hint": "남"},
}

# ─────────────────────────── 재물몽 ───────────────────────────
JAEMUL: dict[str, dict[str, str]] = {
    "돼지": {"meaning": "재물 — 큰 횡재 가능성", "polarity": "길"},
    "황금돼지": {"meaning": "복권 당첨급 횡재", "polarity": "길"},
    "똥": {"meaning": "재물 — 똥은 황금의 역상", "polarity": "길"},
    "똥 밟음": {"meaning": "예상치 못한 돈", "polarity": "길"},
    "오물 묻음": {"meaning": "재물 — 더러울수록 큰돈", "polarity": "길"},
    "돈": {"meaning": "다툼·손실 — 직접적 돈 꿈은 역몽 경향", "polarity": "흉"},
    "지갑 잃음": {"meaning": "오히려 새 기회 — 손실의 역상", "polarity": "길"},
    "지갑 주움": {"meaning": "작은 횡재", "polarity": "길"},
    "보물 발견": {"meaning": "노력의 결실", "polarity": "길"},
    "금괴": {"meaning": "큰 재물 도래", "polarity": "길"},
    "은화": {"meaning": "작은 재물", "polarity": "길"},
    "수표": {"meaning": "지연된 보상", "polarity": "중립"},
    "복권": {"meaning": "기회의 상징 — 다만 직접 꿈은 회피", "polarity": "중립"},
    "강도": {"meaning": "재물 손실 두려움 — 실제 손실 아님", "polarity": "중립"},
    "도둑": {"meaning": "예기치 못한 소득 — 역해", "polarity": "길"},
    "불": {"meaning": "재물 — 활활 타오를수록 길몽", "polarity": "길"},
    "큰 불": {"meaning": "큰 재물 — 불 클수록 좋음", "polarity": "길"},
    "홍수": {"meaning": "재물 — 큰돈 유입", "polarity": "길"},
    "맑은 물": {"meaning": "재물·기쁨", "polarity": "길"},
    "흙탕물": {"meaning": "금전 시비·손실", "polarity": "흉"},
    "물 마심": {"meaning": "재물 흡수", "polarity": "길"},
    "황금색 잉어": {"meaning": "출세·재물", "polarity": "길"},
    "큰 물고기 잡음": {"meaning": "큰 재물 획득", "polarity": "길"},
    "은행": {"meaning": "재정 문제 — 신중", "polarity": "중립"},
    "도둑맞음": {"meaning": "역몽 — 오히려 득", "polarity": "길"},
    "구덩이에 빠짐": {"meaning": "금전 곤란 가능", "polarity": "흉"},
    "쓰레기": {"meaning": "재물 — 더러움 = 돈", "polarity": "길"},
    "오줌 줄기": {"meaning": "재물의 흐름", "polarity": "길"},
    "황금 알": {"meaning": "잠재된 큰 보상", "polarity": "길"},
}

# ─────────────────────────── 합격몽 ───────────────────────────
HAPGYEOK: dict[str, dict[str, str]] = {
    "오르기": {"meaning": "지위 상승 — 시험 합격·승진", "polarity": "길"},
    "산 정상": {"meaning": "목표 달성 — 합격 강조", "polarity": "길"},
    "계단 오름": {"meaning": "단계적 성취", "polarity": "길"},
    "건물 옥상": {"meaning": "정점 도달", "polarity": "길"},
    "사다리 오름": {"meaning": "기회의 통로 — 승진", "polarity": "길"},
    "날기": {"meaning": "자유로운 성취 — 합격·해방", "polarity": "길"},
    "하늘로 올라감": {"meaning": "큰 성취 — 명예 획득", "polarity": "길"},
    "용이 됨": {"meaning": "입신양명 — 최고 합격몽", "polarity": "길"},
    "잉어가 용 됨": {"meaning": "어변성룡 — 등용문 통과", "polarity": "길"},
    "큰 문 통과": {"meaning": "관문 통과 — 합격", "polarity": "길"},
    "성문 들어감": {"meaning": "공직·진입 성공", "polarity": "길"},
    "관문 통과": {"meaning": "시험 합격", "polarity": "길"},
    "왕 만남": {"meaning": "권위자의 인정", "polarity": "길"},
    "임금 알현": {"meaning": "큰 인물의 후원", "polarity": "길"},
    "관복 입음": {"meaning": "공직 진출", "polarity": "길"},
    "도장 받음": {"meaning": "공식 인정·승진", "polarity": "길"},
    "벼슬": {"meaning": "관직 진출", "polarity": "길"},
    "임명장": {"meaning": "공식 합격 통보", "polarity": "길"},
    "트로피": {"meaning": "성취의 가시화", "polarity": "길"},
    "메달": {"meaning": "공로 인정", "polarity": "길"},
    "왕관 씀": {"meaning": "최고의 영광", "polarity": "길"},
    "박수 받음": {"meaning": "공적 인정", "polarity": "길"},
    "수석": {"meaning": "최우수 성취", "polarity": "길"},
    "글을 잘 씀": {"meaning": "지적 성취", "polarity": "길"},
    "책을 받음": {"meaning": "학문적 진보", "polarity": "길"},
    "스승 만남": {"meaning": "지도·가르침의 운", "polarity": "길"},
    "시험 잘 봄": {"meaning": "정몽 — 좋은 결과", "polarity": "길"},
    "시험 망침": {"meaning": "역몽 — 실제로는 합격", "polarity": "길"},
    "지각하지 않음": {"meaning": "기회 잡음", "polarity": "길"},
    "넓은 길": {"meaning": "전도양양", "polarity": "길"},
}

# ─────────────────────────── 죽음몽(逆夢) ───────────────────────────
DEATH_DREAM: dict[str, dict[str, str]] = {
    "자기 죽음": {"meaning": "역몽 — 새로운 시작·재생", "polarity": "길"},
    "장례식": {"meaning": "옛 자아 정리 — 변화의 길조", "polarity": "길"},
    "내 장례": {"meaning": "재탄생 — 운명 전환", "polarity": "길"},
    "관": {"meaning": "옛 시기의 마감 — 새 출발", "polarity": "길"},
    "시신": {"meaning": "과거의 정리", "polarity": "중립"},
    "내 시신": {"meaning": "변신·재생의 길몽", "polarity": "길"},
    "묘": {"meaning": "조상의 음덕·뿌리 인식", "polarity": "중립"},
    "묘지 방문": {"meaning": "조상 발복 — 길조", "polarity": "길"},
    "조상 만남": {"meaning": "음덕·계시", "polarity": "길"},
    "죽은 부모": {"meaning": "조상의 보호", "polarity": "길"},
    "죽은 친지": {"meaning": "가족의 정리", "polarity": "중립"},
    "검은 옷": {"meaning": "엄숙한 변화", "polarity": "중립"},
    "상복": {"meaning": "정리·전환", "polarity": "중립"},
    "곡소리": {"meaning": "감정의 정리", "polarity": "중립"},
    "영구차": {"meaning": "이행의 시간", "polarity": "중립"},
    "병원에서 죽음": {"meaning": "병의 해소·치유", "polarity": "길"},
    "익사": {"meaning": "감정의 정화 — 역몽 경향", "polarity": "중립"},
    "추락사": {"meaning": "옛 지위 정리 — 새 자리", "polarity": "중립"},
    "사고사": {"meaning": "급격한 변화 — 적응 필요", "polarity": "중립"},
    "타살": {"meaning": "외부 변화의 압박", "polarity": "흉"},
    "내가 누구를 죽임": {"meaning": "내 안의 무언가 정리", "polarity": "중립"},
    "유언": {"meaning": "전달의 의지·정리", "polarity": "중립"},
    "부활": {"meaning": "재생·재기", "polarity": "길"},
    "환생": {"meaning": "운명의 전환", "polarity": "길"},
}

# ─────────────────────────── 가위눌림 ───────────────────────────
GAWI: dict[str, dict[str, str]] = {
    "가위눌림": {"meaning": "수면마비 — 스트레스·자세 점검", "polarity": "중립"},
    "몸이 안 움직임": {"meaning": "REM 마비 — 신체 휴식 부족", "polarity": "중립"},
    "소리 안 나옴": {"meaning": "수면마비 동반 증상", "polarity": "중립"},
    "검은 그림자": {"meaning": "가위눌림 시 흔한 환시", "polarity": "흉"},
    "검은 형체": {"meaning": "수면마비 환각 — 영적 의미 아님", "polarity": "중립"},
    "가슴 눌림": {"meaning": "기도·횡격막 압박감", "polarity": "중립"},
    "숨막힘": {"meaning": "수면 무호흡 가능 — 건강 점검", "polarity": "흉"},
    "귀신 봄": {"meaning": "REM 환각 — 심리적 압박 신호", "polarity": "중립"},
    "원귀": {"meaning": "내면의 미해결 감정", "polarity": "중립"},
    "처녀귀신": {"meaning": "표현 못한 감정의 투사", "polarity": "중립"},
    "총각귀신": {"meaning": "성취 못한 욕망의 투사", "polarity": "중립"},
    "이상한 그림자": {"meaning": "수면환각 — 무해", "polarity": "중립"},
}

# ─────────────────────────── 이별몽 ───────────────────────────
IBYEOL: dict[str, dict[str, str]] = {
    "이별": {"meaning": "관계의 변화 — 새 단계로 이행", "polarity": "중립"},
    "헤어짐": {"meaning": "정리 필요 — 또는 더 깊은 결합", "polarity": "중립"},
    "버려짐": {"meaning": "버려질까 하는 두려움의 투사", "polarity": "흉"},
    "전 연인": {"meaning": "미해결 감정 — 현 관계 점검", "polarity": "중립"},
    "옛사랑 만남": {"meaning": "과거 정리·재평가", "polarity": "중립"},
    "재회": {"meaning": "끊긴 인연의 복원 — 길조", "polarity": "길"},
    "결혼": {"meaning": "결합·전환 — 길몽", "polarity": "길"},
    "이혼": {"meaning": "관계의 재정의 — 흔히 역몽", "polarity": "중립"},
    "외도": {"meaning": "관계의 불안 — 솔직한 대화 필요", "polarity": "흉"},
    "배신": {"meaning": "신뢰의 점검", "polarity": "흉"},
    "실종": {"meaning": "관계의 거리감", "polarity": "흉"},
    "찾아 헤맴": {"meaning": "관계의 갈망", "polarity": "흉"},
    "추적": {"meaning": "회피하는 감정", "polarity": "흉"},
    "쫓김": {"meaning": "마주하지 않은 갈등", "polarity": "흉"},
    "친구와 다툼": {"meaning": "관계 조정 시기", "polarity": "중립"},
    "친구의 결혼식": {"meaning": "내 변화의 자극", "polarity": "중립"},
    "낯선 이성": {"meaning": "내면의 그림자·이상형 투사", "polarity": "중립"},
}


_CATEGORY_DICTS = {
    "태몽": TAEMONG,
    "재물몽": JAEMUL,
    "합격몽": HAPGYEOK,
    "죽음몽": DEATH_DREAM,
    "가위눌림": GAWI,
    "이별몽": IBYEOL,
}


def lookup_folk(text: str, limit: int = 15) -> dict[str, Any]:
    """6대 카테고리 사전 매칭·집계."""
    t = text or ""
    matches_by_category: dict[str, list[dict[str, str]]] = {k: [] for k in _CATEGORY_DICTS}
    flat_matches: list[dict[str, str]] = []

    for category, dictionary in _CATEGORY_DICTS.items():
        for kw, data in dictionary.items():
            if kw in t:
                entry = {"keyword": kw, "category": category, **data}
                matches_by_category[category].append(entry)
                flat_matches.append(entry)
                if len(flat_matches) >= limit:
                    break
        if len(flat_matches) >= limit:
            break

    category_counts = {k: len(v) for k, v in matches_by_category.items()}
    dominant_category = max(category_counts, key=lambda k: category_counts[k]) if any(category_counts.values()) else None

    return {
        "matches": flat_matches,
        "by_category": matches_by_category,
        "category_counts": category_counts,
        "dominant_category": dominant_category,
        "dominant_label": KOREAN_FOLK_CATEGORIES.get(dominant_category) if dominant_category else None,
    }


__all__ = [
    "KOREAN_FOLK_CATEGORIES",
    "TAEMONG", "JAEMUL", "HAPGYEOK", "DEATH_DREAM", "GAWI", "IBYEOL",
    "lookup_folk",
]
