"""주역(I-Ching) 64괘 물상(物象) 매핑 — 동양 결정론적 꿈 해석.

핵심:
  - 팔괘(八卦): 건(乾)·태(兌)·이(離)·진(震)·손(巽)·감(坎)·간(艮)·곤(坤)
  - 각 괘 = 자연 요소·동물·인간관계 상징
  - 두 괘 조합 = 64괘(상괘·하괘) → 서사 구조
  - 상생상극(오행)으로 길흉 계산

본 모듈:
  - 꿈 텍스트 → 등장 사물 → 팔괘 매핑
  - 상괘·하괘 결정 → 64괘 도출 → 길흉 + 미래 지향 해석
"""

from __future__ import annotations
from typing import Any


ICHING_LABEL = (
    "주역 64괘 — 팔괘 물상 조합으로 길흉·미래 흐름 계산. "
    "동양 결정론적 해석의 정수."
)


# 팔괘 정의 — 자연/동물/관계/오행
TRIGRAMS: dict[str, dict[str, Any]] = {
    "건": {
        "symbol": "☰", "korean": "건(乾)", "nature": "하늘", "wuxing": "金",
        "animals": ["용", "말"], "family": "아버지", "attribute": "강건",
        "keywords": ["하늘", "용", "말", "아버지", "왕", "권위", "강함", "리더", "양"],
    },
    "태": {
        "symbol": "☱", "korean": "태(兌)", "nature": "연못", "wuxing": "金",
        "animals": ["양"], "family": "막내딸", "attribute": "기쁨",
        "keywords": ["연못", "호수", "양", "막내딸", "기쁨", "입", "노래", "잔치"],
    },
    "이": {
        "symbol": "☲", "korean": "이(離)", "nature": "불", "wuxing": "火",
        "animals": ["꿩", "거북"], "family": "둘째딸", "attribute": "밝음",
        "keywords": ["불", "태양", "빛", "꿩", "거북", "둘째딸", "밝음", "지혜", "눈"],
    },
    "진": {
        "symbol": "☳", "korean": "진(震)", "nature": "번개", "wuxing": "木",
        "animals": ["용"], "family": "장남", "attribute": "움직임",
        "keywords": ["번개", "천둥", "장남", "움직임", "충격", "발", "성장"],
    },
    "손": {
        "symbol": "☴", "korean": "손(巽)", "nature": "바람", "wuxing": "木",
        "animals": ["닭"], "family": "장녀", "attribute": "들어감",
        "keywords": ["바람", "닭", "장녀", "유연", "스며듦", "나무", "들어감"],
    },
    "감": {
        "symbol": "☵", "korean": "감(坎)", "nature": "물", "wuxing": "水",
        "animals": ["돼지"], "family": "둘째아들", "attribute": "험함",
        "keywords": ["물", "비", "돼지", "둘째아들", "구덩이", "위험", "귀", "험난"],
    },
    "간": {
        "symbol": "☶", "korean": "간(艮)", "nature": "산", "wuxing": "土",
        "animals": ["개"], "family": "막내아들", "attribute": "멈춤",
        "keywords": ["산", "개", "막내아들", "멈춤", "고요", "손", "정지"],
    },
    "곤": {
        "symbol": "☷", "korean": "곤(坤)", "nature": "땅", "wuxing": "土",
        "animals": ["소"], "family": "어머니", "attribute": "수용",
        "keywords": ["땅", "흙", "소", "어머니", "수용", "포용", "음", "복종"],
    },
}


# 64괘 일부 핵심 — 상괘+하괘 키 → 괘이름/길흉/메시지
# (전체 64괘 표는 매우 방대 — MVP는 자주 등장하는 24괘 + 양극단 우선)
HEXAGRAMS: dict[tuple[str, str], dict[str, Any]] = {
    ("건", "건"): {"no": 1, "name": "重天乾 (중천건)", "polarity": "대길",
                    "message": "강건한 양의 극치. 큰 결단·창조의 시기. 단 너무 강하면 꺾일 수 있음."},
    ("곤", "곤"): {"no": 2, "name": "重地坤 (중지곤)", "polarity": "길",
                    "message": "수용·포용의 큰 덕. 따르고 받아들이는 자세가 길조."},
    ("감", "진"): {"no": 3, "name": "水雷屯 (수뢰둔)", "polarity": "흉",
                    "message": "시작의 어려움. 막혔으나 인내하면 풀림."},
    ("간", "감"): {"no": 4, "name": "山水蒙 (산수몽)", "polarity": "중립",
                    "message": "어림·미숙. 배움이 필요한 시기."},
    ("감", "건"): {"no": 5, "name": "水天需 (수천수)", "polarity": "중립",
                    "message": "기다림. 때를 기다리면 성취."},
    ("건", "감"): {"no": 6, "name": "天水訟 (천수송)", "polarity": "흉",
                    "message": "다툼·소송. 갈등을 피하고 중재가 길."},
    ("곤", "감"): {"no": 7, "name": "地水師 (지수사)", "polarity": "양가",
                    "message": "군대·조직. 통솔력·결단으로 성취 가능."},
    ("감", "곤"): {"no": 8, "name": "水地比 (수지비)", "polarity": "길",
                    "message": "친밀·결합. 같은 뜻을 가진 이와의 결속."},
    ("손", "건"): {"no": 9, "name": "風天小畜 (풍천소축)", "polarity": "중립",
                    "message": "작은 축적. 큰 일 전 작은 정비."},
    ("건", "태"): {"no": 10, "name": "天澤履 (천택리)", "polarity": "중립",
                    "message": "조심스러운 발걸음. 호랑이 꼬리를 밟는 듯한 시기."},
    ("곤", "건"): {"no": 11, "name": "地天泰 (지천태)", "polarity": "대길",
                    "message": "음양 조화의 절정. 모든 일이 순조롭게 통함."},
    ("건", "곤"): {"no": 12, "name": "天地否 (천지비)", "polarity": "흉",
                    "message": "막힘·단절. 음양이 어긋난 시기. 인내·은인자중."},
    ("이", "건"): {"no": 13, "name": "天火同人 (천화동인)", "polarity": "길",
                    "message": "동지·연대. 사람들과의 협력으로 큰 일 성취."},
    ("건", "이"): {"no": 14, "name": "火天大有 (화천대유)", "polarity": "대길",
                    "message": "큰 소유·풍요. 다만 겸손해야 유지됨."},
    ("간", "곤"): {"no": 15, "name": "地山謙 (지산겸)", "polarity": "길",
                    "message": "겸손. 낮춤이 곧 높임이 됨."},
    ("진", "곤"): {"no": 16, "name": "雷地豫 (뇌지예)", "polarity": "길",
                    "message": "기쁨·예비. 미리 준비된 즐거움."},
    ("태", "진"): {"no": 17, "name": "澤雷隨 (택뢰수)", "polarity": "길",
                    "message": "따름. 자연의 흐름에 순응하면 길."},
    ("간", "손"): {"no": 18, "name": "山風蠱 (산풍고)", "polarity": "흉",
                    "message": "부패·정비 필요. 묵은 일을 바로잡을 때."},
    ("곤", "태"): {"no": 19, "name": "地澤臨 (지택임)", "polarity": "길",
                    "message": "다가옴·임함. 큰 일이 가까워짐."},
    ("손", "곤"): {"no": 20, "name": "風地觀 (풍지관)", "polarity": "중립",
                    "message": "관찰·성찰. 행동 전 깊은 관조."},
    ("이", "진"): {"no": 21, "name": "火雷噬嗑 (화뢰서합)", "polarity": "양가",
                    "message": "씹어 부숨. 단호한 결단·법적 정리."},
    ("간", "이"): {"no": 22, "name": "山火賁 (산화비)", "polarity": "중립",
                    "message": "꾸밈·문화. 본질에 형식을 더함."},
    ("간", "곤"): {"no": 23, "name": "山地剝 (산지박)", "polarity": "흉",
                    "message": "벗겨짐·박탈. 큰 쇠퇴 — 보존이 우선."},
    ("곤", "진"): {"no": 24, "name": "地雷復 (지뢰복)", "polarity": "길",
                    "message": "회복·돌아옴. 음 속에서 양이 다시 자람."},
    # ── 양극단 보강 ──
    ("이", "감"): {"no": 63, "name": "水火旣濟 (수화기제)", "polarity": "대길",
                    "message": "이미 건넘. 목표 달성·완성. 단 방심 금물."},
    ("감", "이"): {"no": 64, "name": "火水未濟 (화수미제)", "polarity": "양가",
                    "message": "아직 건너지 못함. 끝과 시작의 경계 — 인내 필요."},
}


def _detect_trigrams(text: str) -> dict[str, int]:
    """꿈 텍스트에서 팔괘 키워드 등장 카운트."""
    t = text or ""
    counts: dict[str, int] = {}
    for key, tri in TRIGRAMS.items():
        n = sum(1 for kw in tri["keywords"] if kw in t)
        if n > 0:
            counts[key] = n
    return counts


def _pick_top_two(counts: dict[str, int]) -> tuple[str | None, str | None]:
    """등장 빈도 상위 2개 팔괘 선택."""
    if not counts:
        return None, None
    sorted_tri = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_tri) == 1:
        return sorted_tri[0][0], sorted_tri[0][0]  # 같은 괘 중첩
    return sorted_tri[0][0], sorted_tri[1][0]


# 오행 상생·상극
_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_OVERCOMES = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def _wuxing_relation(upper_wx: str, lower_wx: str) -> str:
    """두 오행의 관계 — 상생/상극/동일/중립."""
    if upper_wx == lower_wx:
        return "동기 (같은 오행)"
    if _GENERATES.get(upper_wx) == lower_wx:
        return f"상생 ({upper_wx}이 {lower_wx} 생함)"
    if _GENERATES.get(lower_wx) == upper_wx:
        return f"상생 ({lower_wx}이 {upper_wx} 생함)"
    if _OVERCOMES.get(upper_wx) == lower_wx:
        return f"상극 ({upper_wx}이 {lower_wx} 극함)"
    if _OVERCOMES.get(lower_wx) == upper_wx:
        return f"상극 ({lower_wx}이 {upper_wx} 극함)"
    return "중립"


def divine_hexagram(text: str) -> dict[str, Any]:
    """꿈 텍스트에서 64괘 도출 + 길흉 + 메시지."""
    t = text or ""
    counts = _detect_trigrams(t)

    if not counts:
        return {
            "trigrams_detected": {},
            "hexagram": None,
            "interpretive_note": "팔괘 키워드 매칭 없음 — 주역 분석 적용 불가.",
        }

    upper_key, lower_key = _pick_top_two(counts)
    if upper_key is None or lower_key is None:
        return {
            "trigrams_detected": counts,
            "hexagram": None,
            "interpretive_note": "팔괘 신호 부족.",
        }

    upper = TRIGRAMS[upper_key]
    lower = TRIGRAMS[lower_key]
    wx_relation = _wuxing_relation(upper["wuxing"], lower["wuxing"])

    hex_data = HEXAGRAMS.get((upper_key, lower_key))
    if hex_data:
        hex_info = {
            "number": hex_data["no"],
            "name": hex_data["name"],
            "polarity": hex_data["polarity"],
            "message": hex_data["message"],
            "in_lexicon": True,
        }
    else:
        # 64괘 사전에 없는 조합 — 팔괘 속성만 조합 해석
        hex_info = {
            "number": None,
            "name": f"{upper['korean']}({upper['symbol']})·{lower['korean']}({lower['symbol']})",
            "polarity": "중립",
            "message": (
                f"상괘 {upper['attribute']}({upper['nature']})과 "
                f"하괘 {lower['attribute']}({lower['nature']})의 조합. "
                f"{wx_relation} 관계로 흐름이 결정됨."
            ),
            "in_lexicon": False,
        }

    return {
        "trigrams_detected": counts,
        "upper_trigram": {
            "key": upper_key,
            "korean": upper["korean"],
            "symbol": upper["symbol"],
            "nature": upper["nature"],
            "wuxing": upper["wuxing"],
        },
        "lower_trigram": {
            "key": lower_key,
            "korean": lower["korean"],
            "symbol": lower["symbol"],
            "nature": lower["nature"],
            "wuxing": lower["wuxing"],
        },
        "wuxing_relation": wx_relation,
        "hexagram": hex_info,
        "interpretive_note": (
            f"주역 {hex_info['name']} — {hex_info['polarity']}. {hex_info['message']}"
        ),
    }


__all__ = [
    "ICHING_LABEL",
    "TRIGRAMS",
    "HEXAGRAMS",
    "divine_hexagram",
]
