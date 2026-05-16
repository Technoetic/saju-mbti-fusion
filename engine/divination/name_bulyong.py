"""성명학 불용한자(不用漢字) DB — 결정론 진단 엔진.

뜻이 좋아도 인명에 쓰면 흉화를 초래한다고 통설되는 한자 데이터.
프론트의 단순 Set(`불용한자`)를 백엔드 정식 모듈로 정리 + 흉화 사유 첨부.

⚠️ 본 모듈의 분류는 정통 성명학(마의상법·유장상법 등) 통설 기준의 참고용.
   학파별로 견해가 다를 수 있어 **절대적 금지가 아니라 진단·경고**용으로만 사용.

운영표준 정합:
  · LLM 없이 결정론 진단 (재현성)
  · 응답 envelope에 사유 노출 (검증성)
  · "흉상/흉명" 평가어를 사용자 응답에 단정적으로 쓰지 않음 (안전)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# 흉화 카테고리 — 유사 사유끼리 묶어 UI에서 그룹 표시 가능
CATEGORY_DEATH = "death"             # 죽음·소멸·끝
CATEGORY_ILLNESS = "illness"         # 병·고통·슬픔
CATEGORY_DISASTER = "disaster"       # 흉·재앙·악
CATEGORY_GLOOM = "gloom"             # 어두움·차가움·낡음
CATEGORY_BREAK = "break"             # 파괴·실패·결핍
CATEGORY_BASE = "base"               # 천한 직위·신체 일부
CATEGORY_BEAST = "beast"             # 동물·곤충(부정적 함의)
CATEGORY_WEAPON = "weapon"           # 흉기·갈등
CATEGORY_CELESTIAL = "celestial"     # 천기·자연 거대 형상 (감당 어려움)
CATEGORY_EXTREME = "extreme"         # 한계·극단
CATEGORY_NUMBER = "number"           # 숫자·순서 (서열 혼란)
CATEGORY_TEMPER = "temper"           # 성정 극단 (인간관계 불화)
CATEGORY_FORTUNE = "fortune"         # 역효과 (좋은 글자가 흉으로)


@dataclass(frozen=True)
class BulyongEntry:
    """단일 불용한자 정보.

    Attributes:
        char: 한자
        category: 흉화 카테고리 (CATEGORY_*)
        reason: 흉화 사유 (한글, 사용자 노출용)
        source: 분류 근거 (학파·문헌)
    """
    char: str
    category: str
    reason: str
    source: str = "통설"


# 핵심 불용한자 — 보고서 §1 + 프론트 기존 Set 통합
_BULYONG_ENTRIES: tuple[BulyongEntry, ...] = (
    # ── 보고서 §1 명시 12자 ──
    BulyongEntry("星", CATEGORY_CELESTIAL,
                 "단명(短命)하는 자가 많으며, 고독·부부운이 불길함.",
                 "마의상법·유장상법"),
    BulyongEntry("吉", CATEGORY_FORTUNE,
                 "뜻은 좋으나 부모덕 박하고 매사 지연.",
                 "역효과 통설"),
    BulyongEntry("極", CATEGORY_EXTREME,
                 "부모덕이 없고 가난·궁핍 초래. 운세 확장 차단.",
                 "한계 암시"),
    BulyongEntry("錦", CATEGORY_GLOOM,
                 "고생·고독 암시. 겉은 화려하나 속이 비어 있음.",
                 "화려함 이면의 쇠퇴"),
    BulyongEntry("敏", CATEGORY_TEMPER,
                 "성질이 날카로워 인간관계 불화 초래.",
                 "성정 극단"),
    BulyongEntry("二", CATEGORY_NUMBER,
                 "형제간 다툼 유발, 서열 혼란.",
                 "숫자·순서"),
    BulyongEntry("小", CATEGORY_NUMBER, "왜소·축소 의미로 운세 한정.", "한계 암시"),
    BulyongEntry("末", CATEGORY_DEATH, "끝·종말. 인생 후반 쇠퇴.", "종결 의미"),
    BulyongEntry("終", CATEGORY_DEATH, "끝·마침. 인생 후반 쇠퇴.", "종결 의미"),
    BulyongEntry("天", CATEGORY_CELESTIAL,
                 "감당하기 어려운 거대 형상. 운세 극단."),
    BulyongEntry("地", CATEGORY_CELESTIAL,
                 "감당하기 어려운 거대 형상. 기초 약화."),
    BulyongEntry("月", CATEGORY_CELESTIAL,
                 "감당하기 어려운 거대 형상. 부부운 박함."),

    # ── 죽음·소멸·끝 ──
    BulyongEntry("死", CATEGORY_DEATH, "죽음 — 인명 절대 금기."),
    BulyongEntry("亡", CATEGORY_DEATH, "잃음·죽음."),
    BulyongEntry("滅", CATEGORY_DEATH, "소멸·멸망."),
    BulyongEntry("喪", CATEGORY_DEATH, "잃음·죽음."),
    BulyongEntry("葬", CATEGORY_DEATH, "장사 지냄."),
    BulyongEntry("墳", CATEGORY_DEATH, "무덤."),
    BulyongEntry("墓", CATEGORY_DEATH, "무덤."),
    BulyongEntry("棺", CATEGORY_DEATH, "관."),
    BulyongEntry("屍", CATEGORY_DEATH, "주검."),
    BulyongEntry("弔", CATEGORY_DEATH, "조문."),
    BulyongEntry("哭", CATEGORY_DEATH, "울음 — 슬픈 정서."),
    BulyongEntry("涕", CATEGORY_DEATH, "눈물."),
    BulyongEntry("涙", CATEGORY_DEATH, "눈물."),

    # ── 병·고통·슬픔 ──
    BulyongEntry("病", CATEGORY_ILLNESS, "병."),
    BulyongEntry("疾", CATEGORY_ILLNESS, "병."),
    BulyongEntry("痛", CATEGORY_ILLNESS, "고통."),
    BulyongEntry("苦", CATEGORY_ILLNESS, "쓸 — 고통."),
    BulyongEntry("哀", CATEGORY_ILLNESS, "슬픔."),
    BulyongEntry("愁", CATEGORY_ILLNESS, "근심·슬픔."),
    BulyongEntry("悲", CATEGORY_ILLNESS, "슬픔."),
    BulyongEntry("恨", CATEGORY_ILLNESS, "한·원망."),
    BulyongEntry("怨", CATEGORY_ILLNESS, "원망."),
    BulyongEntry("痾", CATEGORY_ILLNESS, "오랜 병."),
    BulyongEntry("疫", CATEGORY_ILLNESS, "전염병."),
    BulyongEntry("癌", CATEGORY_ILLNESS, "암."),

    # ── 흉·재앙·악 ──
    BulyongEntry("凶", CATEGORY_DISASTER, "흉·악."),
    BulyongEntry("災", CATEGORY_DISASTER, "재앙."),
    BulyongEntry("禍", CATEGORY_DISASTER, "재앙·화."),
    BulyongEntry("害", CATEGORY_DISASTER, "해 끼침."),
    BulyongEntry("殺", CATEGORY_DISASTER, "죽임."),
    BulyongEntry("罪", CATEGORY_DISASTER, "죄."),
    BulyongEntry("罰", CATEGORY_DISASTER, "벌."),
    BulyongEntry("邪", CATEGORY_DISASTER, "사악함."),
    BulyongEntry("妖", CATEGORY_DISASTER, "요사함."),
    BulyongEntry("鬼", CATEGORY_DISASTER, "귀신."),
    BulyongEntry("怪", CATEGORY_DISASTER, "괴이함."),
    BulyongEntry("厄", CATEGORY_DISASTER, "재앙."),

    # ── 어두움·차가움·낡음 ──
    BulyongEntry("暗", CATEGORY_GLOOM, "어두움."),
    BulyongEntry("黑", CATEGORY_GLOOM, "검음·어두움."),
    BulyongEntry("陰", CATEGORY_GLOOM, "그늘·어두움."),
    BulyongEntry("寒", CATEGORY_GLOOM, "추움."),
    BulyongEntry("冷", CATEGORY_GLOOM, "차가움."),
    BulyongEntry("老", CATEGORY_GLOOM, "늙음 — 인명 부적합."),
    BulyongEntry("朽", CATEGORY_GLOOM, "썩음."),
    BulyongEntry("衰", CATEGORY_GLOOM, "쇠퇴."),
    BulyongEntry("枯", CATEGORY_GLOOM, "마름·시듦."),
    BulyongEntry("腐", CATEGORY_GLOOM, "썩음."),

    # ── 파괴·실패·결핍 ──
    BulyongEntry("破", CATEGORY_BREAK, "깨뜨림."),
    BulyongEntry("折", CATEGORY_BREAK, "꺾임·부러짐."),
    BulyongEntry("缺", CATEGORY_BREAK, "이지러짐·결핍."),
    BulyongEntry("失", CATEGORY_BREAK, "잃음."),
    BulyongEntry("散", CATEGORY_BREAK, "흩어짐."),
    BulyongEntry("離", CATEGORY_BREAK, "헤어짐·이별."),
    BulyongEntry("敗", CATEGORY_BREAK, "패배."),
    BulyongEntry("劣", CATEGORY_BREAK, "열등."),
    BulyongEntry("弱", CATEGORY_BREAK, "약함."),
    BulyongEntry("卑", CATEGORY_BREAK, "낮음·천함."),
    BulyongEntry("賤", CATEGORY_BREAK, "천함."),
    BulyongEntry("拙", CATEGORY_BREAK, "졸렬·서툼."),
    BulyongEntry("愚", CATEGORY_BREAK, "어리석음."),
    BulyongEntry("狂", CATEGORY_BREAK, "미침."),
    BulyongEntry("痴", CATEGORY_BREAK, "어리석음."),
    BulyongEntry("迷", CATEGORY_BREAK, "미혹·헤맴."),

    # ── 천한 직위·신체 일부 ──
    BulyongEntry("奴", CATEGORY_BASE, "노예."),
    BulyongEntry("婢", CATEGORY_BASE, "여자 종."),
    BulyongEntry("屎", CATEGORY_BASE, "똥."),
    BulyongEntry("尿", CATEGORY_BASE, "오줌."),
    BulyongEntry("血", CATEGORY_BASE, "피."),

    # ── 동물·곤충(부정적 함의) ──
    BulyongEntry("蛇", CATEGORY_BEAST, "뱀."),
    BulyongEntry("蟲", CATEGORY_BEAST, "벌레."),
    BulyongEntry("虫", CATEGORY_BEAST, "벌레."),
    BulyongEntry("鼠", CATEGORY_BEAST, "쥐."),
    BulyongEntry("豚", CATEGORY_BEAST, "돼지."),

    # ── 흉기·갈등 ──
    BulyongEntry("刀", CATEGORY_WEAPON, "칼."),
    BulyongEntry("劍", CATEGORY_WEAPON, "검."),
    BulyongEntry("槍", CATEGORY_WEAPON, "창."),
    BulyongEntry("矛", CATEGORY_WEAPON, "창."),
    BulyongEntry("戈", CATEGORY_WEAPON, "창."),
    BulyongEntry("戰", CATEGORY_WEAPON, "전쟁."),
    BulyongEntry("爭", CATEGORY_WEAPON, "다툼."),
    BulyongEntry("鬪", CATEGORY_WEAPON, "싸움."),
)


# 빠른 조회용 dict
_BY_CHAR: dict[str, BulyongEntry] = {e.char: e for e in _BULYONG_ENTRIES}


# ─────────────────────────── Public API ───────────────────────────

def is_bulyong(char: str) -> bool:
    """단일 한자가 불용한자인지."""
    return char in _BY_CHAR


def get_entry(char: str) -> BulyongEntry | None:
    """불용한자 항목 조회. 아니면 None."""
    return _BY_CHAR.get(char)


def all_entries() -> tuple[BulyongEntry, ...]:
    return _BULYONG_ENTRIES


def list_by_category(category: str) -> list[BulyongEntry]:
    return [e for e in _BULYONG_ENTRIES if e.category == category]


def scan_name(name_hanja: str) -> list[BulyongEntry]:
    """이름(한자 문자열)에서 불용한자 모두 추출.

    Args:
        name_hanja: 한자 문자열 (예: "李星敏"). 한글·공백·기타 문자는 무시.

    Returns:
        발견된 BulyongEntry 리스트 (중복 가능 — 같은 글자 두 번이면 두 항목).
    """
    if not isinstance(name_hanja, str):
        return []
    found = []
    for ch in name_hanja:
        e = _BY_CHAR.get(ch)
        if e is not None:
            found.append(e)
    return found


def diagnose_name(name_hanja: str) -> dict[str, Any]:
    """이름 진단 — 응답 envelope에 첨부할 dict.

    Returns:
        {
            "name": "李星敏",
            "has_bulyong": bool,
            "bulyong_count": int,
            "matched": [{char, category, reason, source}, ...],
            "severity": "none" | "minor" | "major" | "severe"
        }
    """
    matched = scan_name(name_hanja)
    n = len(matched)
    if n == 0:
        severity = "none"
    elif n == 1:
        severity = "minor"
    elif n == 2:
        severity = "major"
    else:
        severity = "severe"
    return {
        "name": name_hanja,
        "has_bulyong": n > 0,
        "bulyong_count": n,
        "matched": [
            {
                "char": e.char,
                "category": e.category,
                "reason": e.reason,
                "source": e.source,
            }
            for e in matched
        ],
        "severity": severity,
    }


def total_count() -> int:
    return len(_BULYONG_ENTRIES)
