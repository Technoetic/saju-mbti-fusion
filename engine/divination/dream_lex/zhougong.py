"""주공해몽(周公解夢) — 송·명대 통속 사전형 해몽 코퍼스.

천문·인사·동물·기물 표상을 1:1 길흉으로 매핑한 동아시아 공유 민속 사전.
한국·중국·일본·베트남에 영향. 한국 민속의 korean_folk와 부분 중복하나,
주공해몽은 더 광범위한 한자권 공통 표상을 다룬다.
"""

from __future__ import annotations
from typing import Any


ZHOUGONG_LABEL = (
    "주공해몽 — 송·명대 동아시아 표상 사전. 한자권 공유 길흉 1:1 매핑."
)


ZHOUGONG_CATEGORIES = {
    "천문": "해·달·별·구름·바람·비·뇌·무지개",
    "지리": "산·강·바다·들·도시·길·다리",
    "인물": "왕·관리·승려·도사·노인·아이·죽은이",
    "신체": "머리·얼굴·이·머리카락·손·발·내장",
    "동물": "용·호랑이·뱀·새·물고기·가축",
    "기물": "옷·관·신·칼·거울·문·집·돈·보석",
    "행위": "결혼·장례·잔치·전쟁·여행·노동",
    "신귀": "신·부처·귀신·조상·천사·악마",
}


# 주공해몽 표상 사전 (한자권 공통)
ZHOUGONG_LEXICON: dict[str, dict[str, str]] = {
    # ─── 천문 ───
    "해가 떠오름": {"category": "천문", "polarity": "길", "meaning": "큰 영예·승진"},
    "해가 짐": {"category": "천문", "polarity": "흉", "meaning": "지위 하락·노쇠"},
    "두 개의 해": {"category": "천문", "polarity": "흉", "meaning": "다툼·분쟁"},
    "달이 밝음": {"category": "천문", "polarity": "길", "meaning": "여성에게 길조·잉태"},
    "달이 가려짐": {"category": "천문", "polarity": "흉", "meaning": "여성·어머니 흉사"},
    "별이 떨어짐": {"category": "천문", "polarity": "흉", "meaning": "윗사람의 변고"},
    "별이 빛남": {"category": "천문", "polarity": "길", "meaning": "운명의 길조"},
    "오색 구름": {"category": "천문", "polarity": "길", "meaning": "큰 경사·귀인 도래"},
    "검은 구름": {"category": "천문", "polarity": "흉", "meaning": "근심·재앙의 조짐"},
    "비가 옴": {"category": "천문", "polarity": "길", "meaning": "재물·은혜"},
    "큰 비": {"category": "천문", "polarity": "길", "meaning": "큰 재물 유입"},
    "벼락": {"category": "천문", "polarity": "양가", "meaning": "권력자의 노여움 또는 갑작스러운 영예"},
    "무지개": {"category": "천문", "polarity": "길", "meaning": "약속 성취·경사"},
    "큰 바람": {"category": "천문", "polarity": "양가", "meaning": "변화·이동 — 좋고 나쁨 동시"},

    # ─── 지리 ───
    "높은 산": {"category": "지리", "polarity": "길", "meaning": "지위 상승·후원자"},
    "산이 무너짐": {"category": "지리", "polarity": "흉", "meaning": "큰 변동·기반 흔들림"},
    "맑은 강": {"category": "지리", "polarity": "길", "meaning": "재물·인연의 흐름"},
    "강을 건넘": {"category": "지리", "polarity": "길", "meaning": "큰 일을 성취·전환 성공"},
    "다리를 건넘": {"category": "지리", "polarity": "길", "meaning": "전환·관문 통과"},
    "다리가 끊김": {"category": "지리", "polarity": "흉", "meaning": "단절·관계 끊김"},
    "큰 바다": {"category": "지리", "polarity": "길", "meaning": "포부의 크기·기회"},
    "바다에 빠짐": {"category": "지리", "polarity": "흉", "meaning": "감당 못할 일에 휘말림"},
    "길을 잃음": {"category": "지리", "polarity": "흉", "meaning": "방향 상실·결단 필요"},
    "새 길을 발견": {"category": "지리", "polarity": "길", "meaning": "새 기회·진로"},

    # ─── 인물 ───
    "왕을 만남": {"category": "인물", "polarity": "길", "meaning": "큰 인물의 도움·승진"},
    "관리를 만남": {"category": "인물", "polarity": "길", "meaning": "공직·문서 처리에 길조"},
    "승려와 대화": {"category": "인물", "polarity": "길", "meaning": "정신적 가르침·내면 정화"},
    "도사를 만남": {"category": "인물", "polarity": "길", "meaning": "내면 인도자·계시"},
    "노인의 가르침": {"category": "인물", "polarity": "길", "meaning": "조상·지혜의 음덕"},
    "아이를 안음": {"category": "인물", "polarity": "길", "meaning": "새 시작·잉태 가능성"},
    "죽은 사람과 대화": {"category": "인물", "polarity": "양가", "meaning": "조상의 메시지 또는 사별 처리"},
    "죽은 조상": {"category": "인물", "polarity": "길", "meaning": "조상의 음덕 — 도움 도래"},
    "낯선 사람과 동행": {"category": "인물", "polarity": "양가", "meaning": "새 인연 또는 미지의 자기"},

    # ─── 신체 ───
    "머리가 잘림": {"category": "신체", "polarity": "양가", "meaning": "큰 변동 — 길몽으로도 자주 해석"},
    "이가 빠짐": {"category": "신체", "polarity": "양가", "meaning": "친족 변고 또는 재물·신분 변동"},
    "이가 새로 남": {"category": "신체", "polarity": "길", "meaning": "재생·새 출발"},
    "머리카락 빠짐": {"category": "신체", "polarity": "흉", "meaning": "손재·근심"},
    "머리카락이 길어짐": {"category": "신체", "polarity": "길", "meaning": "생명력·재물 증가"},
    "손이 잘림": {"category": "신체", "polarity": "흉", "meaning": "친족·재산 손실"},
    "발이 부러짐": {"category": "신체", "polarity": "흉", "meaning": "이동·계획 좌절"},
    "눈이 멈": {"category": "신체", "polarity": "흉", "meaning": "통찰력 상실·근심"},
    "눈이 밝아짐": {"category": "신체", "polarity": "길", "meaning": "통찰·진실 발견"},
    "내장이 보임": {"category": "신체", "polarity": "양가", "meaning": "본질 노출 — 진실 또는 취약"},

    # ─── 동물 ───
    "용을 봄": {"category": "동물", "polarity": "길", "meaning": "최고의 길조·큰 인물 됨"},
    "용을 탐": {"category": "동물", "polarity": "길", "meaning": "출세·등용"},
    "호랑이를 봄": {"category": "동물", "polarity": "양가", "meaning": "강한 권력자 — 도움 또는 위협"},
    "호랑이를 잡음": {"category": "동물", "polarity": "길", "meaning": "큰 적을 제압·승진"},
    "뱀이 몸을 감": {"category": "동물", "polarity": "길", "meaning": "잉태·재물의 기운"},
    "뱀에 물림": {"category": "동물", "polarity": "양가", "meaning": "큰 시련 또는 큰 행운의 전조"},
    "흰 뱀": {"category": "동물", "polarity": "길", "meaning": "귀한 손님·재물"},
    "검은 뱀": {"category": "동물", "polarity": "흉", "meaning": "은밀한 적·근심"},
    "새가 날아옴": {"category": "동물", "polarity": "길", "meaning": "소식·기쁜 일"},
    "물고기를 잡음": {"category": "동물", "polarity": "길", "meaning": "재물·잉태"},
    "물고기가 죽음": {"category": "동물", "polarity": "흉", "meaning": "기회 상실"},
    "말을 탐": {"category": "동물", "polarity": "길", "meaning": "출세·여행·승진"},
    "소를 봄": {"category": "동물", "polarity": "길", "meaning": "근면·재물"},
    "돼지를 봄": {"category": "동물", "polarity": "길", "meaning": "재물·풍요"},

    # ─── 기물 ───
    "새 옷": {"category": "기물", "polarity": "길", "meaning": "새 역할·승진"},
    "흰 옷": {"category": "기물", "polarity": "양가", "meaning": "장례·정화 — 맥락에 따라"},
    "관복": {"category": "기물", "polarity": "길", "meaning": "공직 진출·승진"},
    "왕관": {"category": "기물", "polarity": "길", "meaning": "최고의 영광"},
    "신발을 잃음": {"category": "기물", "polarity": "흉", "meaning": "지위·기반 상실"},
    "새 신발": {"category": "기물", "polarity": "길", "meaning": "새 출발·여행"},
    "거울을 봄": {"category": "기물", "polarity": "양가", "meaning": "자기 인식 — 진실 또는 충격"},
    "거울이 깨짐": {"category": "기물", "polarity": "흉", "meaning": "관계의 깨짐"},
    "문이 열림": {"category": "기물", "polarity": "길", "meaning": "기회·전환의 도래"},
    "문이 닫힘": {"category": "기물", "polarity": "흉", "meaning": "기회 차단"},
    "큰 집": {"category": "기물", "polarity": "길", "meaning": "재물·가문의 번창"},
    "집이 무너짐": {"category": "기물", "polarity": "흉", "meaning": "기반 흔들림"},
    "황금": {"category": "기물", "polarity": "길", "meaning": "큰 재물"},
    "은": {"category": "기물", "polarity": "길", "meaning": "재물·청정한 가치"},

    # ─── 행위 ───
    "결혼식": {"category": "행위", "polarity": "양가", "meaning": "새 결합 또는 큰 변동"},
    "장례식": {"category": "행위", "polarity": "양가", "meaning": "옛 자아 정리·재생의 전조"},
    "잔치": {"category": "행위", "polarity": "길", "meaning": "기쁨·축하"},
    "전쟁": {"category": "행위", "polarity": "흉", "meaning": "큰 갈등·시련"},
    "여행": {"category": "행위", "polarity": "양가", "meaning": "변화·새 기회 또는 분주함"},
    "공부": {"category": "행위", "polarity": "길", "meaning": "지적 성취·합격"},

    # ─── 신귀 ───
    "신을 만남": {"category": "신귀", "polarity": "길", "meaning": "큰 도움·계시"},
    "부처를 봄": {"category": "신귀", "polarity": "길", "meaning": "정신적 평화·깨달음"},
    "조상이 나타남": {"category": "신귀", "polarity": "길", "meaning": "음덕·보호"},
    "귀신이 따라옴": {"category": "신귀", "polarity": "흉", "meaning": "근심·미해결 감정"},
    "악마를 봄": {"category": "신귀", "polarity": "흉", "meaning": "내면의 어두운 충동"},
    "천사가 내려옴": {"category": "신귀", "polarity": "길", "meaning": "큰 보호·구원"},
}


def lookup_zhougong(text: str, limit: int = 12) -> dict[str, Any]:
    """주공해몽 사전 매칭."""
    t = text or ""
    matches: list[dict[str, Any]] = []
    by_category: dict[str, list[dict[str, Any]]] = {}
    polarity_counts = {"길": 0, "흉": 0, "양가": 0}

    for kw, data in ZHOUGONG_LEXICON.items():
        if kw in t:
            entry = {"keyword": kw, **data}
            matches.append(entry)
            by_category.setdefault(data["category"], []).append(entry)
            polarity_counts[data["polarity"]] += 1
            if len(matches) >= limit:
                break

    dominant_polarity = max(polarity_counts, key=lambda k: polarity_counts[k]) if any(polarity_counts.values()) else None

    return {
        "matches": matches,
        "by_category": by_category,
        "polarity_counts": polarity_counts,
        "dominant_polarity": dominant_polarity,
        "interpretive_note": (
            f"주공해몽 우세 길흉: {dominant_polarity} ({polarity_counts[dominant_polarity]}건). "
            "양가 해석은 맥락(임신·구직·시험·상중)에 따라 분기됩니다."
            if dominant_polarity
            else "주공해몽 표상 매칭 없음."
        ),
    }


__all__ = [
    "ZHOUGONG_LABEL",
    "ZHOUGONG_CATEGORIES",
    "ZHOUGONG_LEXICON",
    "lookup_zhougong",
]
