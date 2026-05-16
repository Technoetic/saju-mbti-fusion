"""황제내경 음사발몽(淫邪發夢) — 邪氣 침입 장부별 꿈 매핑.

출처: 『黃帝內經·靈樞』「淫邪發夢」 / 『素問』「方盛衰論」

원전 매핑 (간략):
  - 肝氣盛 → 怒夢 (분노·다툼)
  - 心氣盛 → 笑·驚·恐 (웃음·놀람·공포)
  - 脾氣盛 → 歌樂·身重 (노래·몸 무거움)
  - 肺氣盛 → 哭泣·飛揚 (울음·날아오름)
  - 腎氣盛 → 腰脊兩解 (허리 분리감)
"""

from __future__ import annotations
from typing import Any


EUMSA_LABEL = (
    "황제내경 음사발몽 — 邪氣가 침입한 장부에 따라 꿈 내용이 결정된다 "
    "(예: 肝氣盛 → 怒夢). 한방 진단의 보조 신호."
)


# 오장(五臟) → 오행 매핑
ORGAN_TO_WUXING = {
    "肝": "木",  # 간
    "心": "火",  # 심
    "脾": "土",  # 비
    "肺": "金",  # 폐
    "腎": "水",  # 신
}


# 꿈 키워드 → 장부 매핑 (음사발몽 + 임상 확장)
EUMSA_ORGAN_DREAMS: dict[str, dict[str, Any]] = {
    # ─── 肝(간) — 木·怒夢 ───
    "분노": {"organ": "肝", "wuxing": "木", "pattern": "肝氣盛 — 怒夢", "note": "간기 항진"},
    "화남": {"organ": "肝", "wuxing": "木", "pattern": "肝氣盛 — 怒夢", "note": "간기 항진"},
    "다툼": {"organ": "肝", "wuxing": "木", "pattern": "肝氣盛 — 怒夢", "note": "간기 항진"},
    "싸움": {"organ": "肝", "wuxing": "木", "pattern": "肝氣盛 — 怒夢", "note": "간기 항진"},
    "격노": {"organ": "肝", "wuxing": "木", "pattern": "肝氣盛 — 怒夢", "note": "간기 항진"},
    "성냄": {"organ": "肝", "wuxing": "木", "pattern": "肝氣盛 — 怒夢", "note": "간기 항진"},
    "푸른 풀": {"organ": "肝", "wuxing": "木", "pattern": "肝氣象", "note": "간기 발현"},
    "큰 나무": {"organ": "肝", "wuxing": "木", "pattern": "肝氣象", "note": "간기 발현"},
    "숲": {"organ": "肝", "wuxing": "木", "pattern": "肝氣象", "note": "간기 발현"},
    "눈 충혈": {"organ": "肝", "wuxing": "木", "pattern": "肝開竅於目", "note": "간경의 상부 표현"},

    # ─── 心(심) — 火·驚·恐·笑 ───
    "웃음": {"organ": "心", "wuxing": "火", "pattern": "心氣盛 — 笑夢", "note": "심기 항진"},
    "박장대소": {"organ": "心", "wuxing": "火", "pattern": "心氣盛 — 笑夢", "note": "심기 항진"},
    "놀람": {"organ": "心", "wuxing": "火", "pattern": "心氣盛 — 驚夢", "note": "심기 동요"},
    "충격": {"organ": "心", "wuxing": "火", "pattern": "心氣盛 — 驚夢", "note": "심기 동요"},
    "공포": {"organ": "心", "wuxing": "火", "pattern": "心氣盛 — 恐夢", "note": "심·신 양허"},
    "두려움": {"organ": "心", "wuxing": "火", "pattern": "心氣盛 — 恐夢", "note": "심·신 양허"},
    "불": {"organ": "心", "wuxing": "火", "pattern": "心氣象", "note": "심·화 발현"},
    "큰 불": {"organ": "心", "wuxing": "火", "pattern": "心火亢盛", "note": "심화 항성"},
    "화염": {"organcg": "心", "organ": "心", "wuxing": "火", "pattern": "心火亢盛", "note": "심화 항성"},
    "심장 두근": {"organ": "心", "wuxing": "火", "pattern": "心悸", "note": "심기허"},
    "가슴 답답": {"organ": "心", "wuxing": "火", "pattern": "心氣鬱", "note": "심기 울결"},

    # ─── 脾(비) — 土·歌樂 ───
    "노래": {"organ": "脾", "wuxing": "土", "pattern": "脾氣盛 — 歌樂夢", "note": "비기 발현"},
    "음악": {"organ": "脾", "wuxing": "土", "pattern": "脾氣盛 — 歌樂夢", "note": "비기 발현"},
    "춤": {"organ": "脾", "wuxing": "土", "pattern": "脾氣盛 — 歌樂夢", "note": "비기 발현"},
    "잔치": {"organ": "脾", "wuxing": "土", "pattern": "脾氣盛 — 歌樂夢", "note": "비기 발현"},
    "몸이 무거움": {"organ": "脾", "wuxing": "土", "pattern": "脾虛 — 身重夢", "note": "비기허"},
    "몸을 못 움직임": {"organ": "脾", "wuxing": "土", "pattern": "脾虛 — 身重夢", "note": "비기허"},
    "음식": {"organ": "脾", "wuxing": "土", "pattern": "脾胃象", "note": "비위 신호"},
    "밥": {"organ": "脾", "wuxing": "土", "pattern": "脾胃象", "note": "비위 신호"},
    "황색 흙": {"organ": "脾", "wuxing": "土", "pattern": "脾氣象", "note": "비기 발현"},
    "구토": {"organ": "脾", "wuxing": "土", "pattern": "脾胃不和", "note": "비위 부조화"},

    # ─── 肺(폐) — 金·哭泣·飛揚 ───
    "울음": {"organ": "肺", "wuxing": "金", "pattern": "肺氣盛 — 哭泣夢", "note": "폐기 동요"},
    "비통": {"organ": "肺", "wuxing": "金", "pattern": "肺氣盛 — 哭泣夢", "note": "폐기 동요"},
    "흐느낌": {"organ": "肺", "wuxing": "金", "pattern": "肺氣盛 — 哭泣夢", "note": "폐기 동요"},
    "날기": {"organ": "肺", "wuxing": "金", "pattern": "肺氣盛 — 飛揚夢", "note": "폐기 발산"},
    "공중 부양": {"organ": "肺", "wuxing": "金", "pattern": "肺氣盛 — 飛揚夢", "note": "폐기 발산"},
    "하늘로 올라감": {"organ": "肺", "wuxing": "金", "pattern": "肺氣盛 — 飛揚夢", "note": "폐기 발산"},
    "기침": {"organ": "肺", "wuxing": "金", "pattern": "肺氣不利", "note": "폐기 불리"},
    "숨막힘": {"organ": "肺", "wuxing": "金", "pattern": "肺氣鬱", "note": "폐기 울체"},
    "흰 옷": {"organ": "肺", "wuxing": "金", "pattern": "肺氣象", "note": "폐기 표현"},
    "흰 새": {"organ": "肺", "wuxing": "金", "pattern": "肺氣象", "note": "폐기 표현"},

    # ─── 腎(신) — 水·恐·腰脊 ───
    "허리 분리": {"organ": "腎", "wuxing": "水", "pattern": "腎氣盛 — 腰脊兩解夢", "note": "신기 동요"},
    "허리 끊김": {"organ": "腎", "wuxing": "水", "pattern": "腎氣盛 — 腰脊兩解夢", "note": "신기 동요"},
    "허리 아픔": {"organ": "腎", "wuxing": "水", "pattern": "腎氣虛", "note": "신허"},
    "물에 빠짐": {"organ": "腎", "wuxing": "水", "pattern": "腎氣象", "note": "신기 발현"},
    "깊은 물": {"organ": "腎", "wuxing": "水", "pattern": "腎氣象", "note": "신기 발현"},
    "검은 옷": {"organ": "腎", "wuxing": "水", "pattern": "腎氣象", "note": "신기 표현"},
    "검은 짐승": {"organ": "腎", "wuxing": "水", "pattern": "腎氣象", "note": "신기 표현"},
    "오줌": {"organ": "腎", "wuxing": "水", "pattern": "腎主水液", "note": "신·방광 신호"},
    "방광": {"organ": "腎", "wuxing": "水", "pattern": "腎主水液", "note": "신·방광 신호"},
    "추위": {"organ": "腎", "wuxing": "水", "pattern": "腎陽虛", "note": "신양허"},
    "다리 시림": {"organ": "腎", "wuxing": "水", "pattern": "腎陽虛", "note": "신양허"},
    "이빨 빠짐": {"organ": "腎", "wuxing": "水", "pattern": "腎主骨·齒爲骨之餘", "note": "신기 쇠약"},
}


def map_dream_to_organ(text: str, limit: int = 8) -> dict[str, Any]:
    """꿈 텍스트에서 장부 신호 추출."""
    t = text or ""
    matched: list[dict[str, Any]] = []
    organ_counts: dict[str, int] = {"肝": 0, "心": 0, "脾": 0, "肺": 0, "腎": 0}

    for kw, data in EUMSA_ORGAN_DREAMS.items():
        if kw in t:
            matched.append({"keyword": kw, **{k: v for k, v in data.items() if k != "organcg"}})
            organ = data["organ"]
            if organ in organ_counts:
                organ_counts[organ] += 1
            if len(matched) >= limit:
                break

    dominant = max(organ_counts, key=lambda k: organ_counts[k]) if any(organ_counts.values()) else None

    return {
        "matched": matched,
        "organ_counts": organ_counts,
        "dominant_organ": dominant,
        "dominant_wuxing": ORGAN_TO_WUXING.get(dominant) if dominant else None,
        "interpretive_note": (
            f"꿈 신호가 '{dominant}'({ORGAN_TO_WUXING.get(dominant)})의 동요를 가리킵니다. "
            "한방 진단의 보조 신호이며, 신체 증상이 동반된다면 한의원 상담을 권합니다."
            if dominant
            else "음사발몽 신호 매칭 없음."
        ),
    }


__all__ = [
    "EUMSA_LABEL",
    "ORGAN_TO_WUXING",
    "EUMSA_ORGAN_DREAMS",
    "map_dream_to_organ",
]
