"""성명학 강희자전 원획수(原劃數) 모듈 — 결정론 획수 계산.

보고서 §2 본문화:
  · 일반 옥편의 필획수 ≠ 강희자전 원획수
  · 변형 부수 8종은 원부수 획으로 환산 (예: 氵 3획 → 水 4획)
  · 81수리 4격 계산의 입력 데이터

⚠️ 본 모듈의 원획수는 인명용 자주 쓰이는 1000~2000자 우선 수록.
   9,389자 풀 전체는 별도 데이터 수집 작업 필요. 미수록 한자는 strokes_for_char가
   None 반환 → 호출자가 LLM 보강 또는 사용자 입력으로 보충.

운영표준:
  · 결정론 (재현성)
  · 변형 부수 규칙은 명시적 상수
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ─────────────────────────── 보고서 §2 변형 부수 8종 ───────────────────────────
# 변형 부수 글자 → (원부수 글자, 원획수)
# 한자에 해당 변형 부수가 사용되면 부수 부분의 획수를 원획수로 환산.
RADICAL_VARIANTS: dict[str, tuple[str, int]] = {
    "氵": ("水", 4),    # 삼수변 3획 → 水 4획
    "忄": ("心", 4),    # 심방변 3획 → 心 4획
    "扌": ("手", 4),    # 재방변 3획 → 手 4획
    "艹": ("艸", 6),    # 초두머리 4획 → 艸 6획
    "衤": ("衣", 6),    # 옷의변 5획 → 衣 6획
    "罒": ("网", 6),    # 그물망 5획 → 网 6획
    "耂": ("老", 6),    # 늙을로엄 4획 → 老 6획
    # 月은 두 가지 — 달 月(4획)과 고기육변 月(원래 肉 6획)
    # 한자 내 월의 의미가 "고기"일 때만 6획으로 환산해야 하나, 결정론으로 구분 불가
    # → 이 모듈은 "달 月" 그대로 4획 처리. 육변 보정은 미수록 영역.
}


@dataclass(frozen=True)
class StrokesEntry:
    """단일 한자의 획수 정보.

    Attributes:
        char: 한자
        writing_strokes: 일반 필획수 (옥편·포털 사전 기준)
        kangxi_strokes: 강희자전 원획수 (성명학 표준)
        radical: 한자의 부수 (참고)
        resource_ohaeng: 자원오행 (木/火/土/金/水 중 택일, 미정시 빈 문자열)
    """
    char: str
    writing_strokes: int
    kangxi_strokes: int
    radical: str = ""
    resource_ohaeng: str = ""


# ─────────────────────────── 인명용 자주 쓰이는 한자 표본 (~250자) ───────────────────────────
# 참고: 강희자전 원획수는 공개 문헌·성명학 사전 통설 기준.
# 미수록 한자는 추후 확장 또는 LLM 보강.

_ENTRIES: tuple[StrokesEntry, ...] = (
    # ── 성씨 빈도 상위 (10대 성씨) ──
    StrokesEntry("李", 7, 7, "木", "木"),
    StrokesEntry("金", 8, 8, "金", "金"),
    StrokesEntry("朴", 6, 6, "木", "木"),
    StrokesEntry("崔", 11, 11, "山", "土"),
    StrokesEntry("鄭", 15, 19, "邑", "火"),     # 邑(阝) 부수
    StrokesEntry("姜", 9, 9, "女", "土"),
    StrokesEntry("趙", 14, 14, "走", "火"),
    StrokesEntry("尹", 4, 4, "尸", "土"),
    StrokesEntry("張", 11, 11, "弓", "火"),
    StrokesEntry("林", 8, 8, "木", "木"),
    StrokesEntry("吳", 7, 7, "口", "土"),
    StrokesEntry("韓", 17, 17, "韋", "水"),
    StrokesEntry("申", 5, 5, "田", "金"),
    StrokesEntry("徐", 10, 10, "彳", "金"),
    StrokesEntry("權", 22, 22, "木", "木"),
    StrokesEntry("黃", 12, 12, "黃", "土"),
    StrokesEntry("安", 6, 6, "宀", "土"),
    StrokesEntry("宋", 7, 7, "宀", "木"),
    StrokesEntry("柳", 9, 9, "木", "木"),
    StrokesEntry("洪", 9, 10, "水", "水"),       # 氵 → 水 보정
    StrokesEntry("劉", 15, 15, "刀", "金"),
    StrokesEntry("白", 5, 5, "白", "金"),

    # ── 이름자 자주 쓰임 (수~ㄱ) ──
    StrokesEntry("水", 4, 4, "水", "水"),
    StrokesEntry("火", 4, 4, "火", "火"),
    StrokesEntry("木", 4, 4, "木", "木"),
    StrokesEntry("金", 8, 8, "金", "金"),  # 중복 — 성씨와 동일
    StrokesEntry("土", 3, 3, "土", "土"),
    StrokesEntry("日", 4, 4, "日", "火"),
    StrokesEntry("月", 4, 4, "月", "水"),
    StrokesEntry("山", 3, 3, "山", "土"),
    StrokesEntry("川", 3, 3, "川", "水"),

    # ── ㄱ ──
    StrokesEntry("家", 10, 10, "宀", "木"),
    StrokesEntry("加", 5, 5, "力", "土"),
    StrokesEntry("嘉", 14, 14, "口", "土"),
    StrokesEntry("佳", 8, 8, "人", "火"),
    StrokesEntry("可", 5, 5, "口", "水"),
    StrokesEntry("江", 6, 7, "水", "水"),        # 氵 → 水
    StrokesEntry("姜", 9, 9, "女", "土"),
    StrokesEntry("剛", 10, 10, "刀", "金"),
    StrokesEntry("健", 11, 11, "人", "木"),
    StrokesEntry("建", 9, 9, "廴", "木"),
    StrokesEntry("傑", 12, 12, "人", "木"),
    StrokesEntry("敬", 13, 13, "攴", "木"),
    StrokesEntry("慶", 15, 15, "心", "木"),
    StrokesEntry("景", 12, 12, "日", "火"),
    StrokesEntry("京", 8, 8, "亠", "土"),
    StrokesEntry("經", 13, 13, "糸", "木"),
    StrokesEntry("瓊", 19, 19, "玉", "金"),
    StrokesEntry("啓", 11, 11, "口", "木"),
    StrokesEntry("癸", 9, 9, "癶", "水"),
    StrokesEntry("溪", 13, 14, "水", "水"),
    StrokesEntry("桂", 10, 10, "木", "木"),
    StrokesEntry("古", 5, 5, "口", "水"),
    StrokesEntry("高", 10, 10, "高", "火"),
    StrokesEntry("曲", 6, 6, "曰", "土"),
    StrokesEntry("公", 4, 4, "八", "金"),
    StrokesEntry("光", 6, 6, "儿", "火"),
    StrokesEntry("廣", 15, 15, "广", "木"),
    StrokesEntry("敎", 11, 11, "攴", "土"),
    StrokesEntry("橋", 16, 16, "木", "木"),
    StrokesEntry("具", 8, 8, "八", "金"),
    StrokesEntry("國", 11, 11, "囗", "水"),
    StrokesEntry("君", 7, 7, "口", "水"),
    StrokesEntry("郡", 10, 14, "邑", "土"),       # 邑 → 7획
    StrokesEntry("貴", 12, 12, "貝", "金"),
    StrokesEntry("奎", 9, 9, "大", "土"),
    StrokesEntry("圭", 6, 6, "土", "土"),
    StrokesEntry("均", 7, 7, "土", "土"),
    StrokesEntry("根", 10, 10, "木", "木"),
    StrokesEntry("槿", 15, 15, "木", "木"),
    StrokesEntry("錦", 16, 16, "金", "金"),     # 불용한자
    StrokesEntry("起", 10, 10, "走", "火"),
    StrokesEntry("基", 11, 11, "土", "土"),
    StrokesEntry("奇", 8, 8, "大", "木"),
    StrokesEntry("吉", 6, 6, "口", "水"),         # 불용한자

    # ── ㄴ ──
    StrokesEntry("男", 7, 7, "田", "火"),
    StrokesEntry("南", 9, 9, "十", "火"),
    StrokesEntry("年", 6, 6, "干", "木"),
    StrokesEntry("寧", 14, 14, "宀", "火"),
    StrokesEntry("勞", 12, 12, "力", "火"),

    # ── ㄷ ──
    StrokesEntry("多", 6, 6, "夕", "水"),
    StrokesEntry("丹", 4, 4, "丶", "火"),
    StrokesEntry("達", 13, 16, "辵", "土"),       # 辶(辵) 보정
    StrokesEntry("大", 3, 3, "大", "木"),
    StrokesEntry("德", 15, 15, "彳", "火"),
    StrokesEntry("道", 13, 16, "辵", "火"),
    StrokesEntry("都", 12, 16, "邑", "火"),
    StrokesEntry("東", 8, 8, "木", "木"),
    StrokesEntry("童", 12, 12, "立", "金"),

    # ── ㄹ ──
    StrokesEntry("樂", 15, 15, "木", "火"),
    StrokesEntry("良", 7, 7, "艮", "火"),
    StrokesEntry("亮", 9, 9, "亠", "火"),
    StrokesEntry("禮", 18, 18, "示", "木"),

    # ── ㅁ ──
    StrokesEntry("萬", 13, 15, "艸", "木"),       # 艹 → 艸
    StrokesEntry("梅", 11, 11, "木", "木"),
    StrokesEntry("明", 8, 8, "日", "火"),
    StrokesEntry("名", 6, 6, "口", "水"),
    StrokesEntry("茂", 9, 11, "艸", "木"),
    StrokesEntry("武", 8, 8, "止", "金"),
    StrokesEntry("文", 4, 4, "文", "水"),
    StrokesEntry("敏", 11, 11, "攴", "水"),       # 불용한자
    StrokesEntry("旼", 8, 8, "日", "火"),
    StrokesEntry("珉", 9, 10, "玉", "金"),        # 玉 부수
    StrokesEntry("旻", 8, 8, "日", "火"),
    StrokesEntry("民", 5, 5, "氏", "水"),

    # ── ㅂ ──
    StrokesEntry("博", 12, 12, "十", "水"),
    StrokesEntry("芳", 8, 10, "艸", "木"),
    StrokesEntry("白", 5, 5, "白", "金"),
    StrokesEntry("百", 6, 6, "白", "水"),
    StrokesEntry("範", 15, 15, "竹", "木"),
    StrokesEntry("法", 8, 9, "水", "水"),
    StrokesEntry("丙", 5, 5, "一", "火"),
    StrokesEntry("秉", 8, 8, "禾", "木"),
    StrokesEntry("寶", 20, 20, "宀", "金"),
    StrokesEntry("福", 14, 14, "示", "木"),
    StrokesEntry("奉", 8, 8, "大", "木"),
    StrokesEntry("鳳", 14, 14, "鳥", "火"),
    StrokesEntry("富", 12, 12, "宀", "木"),
    StrokesEntry("夫", 4, 4, "大", "木"),
    StrokesEntry("北", 5, 5, "匕", "水"),

    # ── ㅅ ──
    StrokesEntry("師", 10, 10, "巾", "金"),
    StrokesEntry("思", 9, 9, "心", "金"),
    StrokesEntry("詞", 12, 12, "言", "金"),
    StrokesEntry("史", 5, 5, "口", "金"),
    StrokesEntry("山", 3, 3, "山", "土"),
    StrokesEntry("三", 3, 3, "一", "火"),
    StrokesEntry("尚", 8, 8, "小", "金"),
    StrokesEntry("商", 11, 11, "口", "金"),
    StrokesEntry("瑞", 13, 14, "玉", "金"),
    StrokesEntry("書", 10, 10, "曰", "火"),
    StrokesEntry("石", 5, 5, "石", "金"),
    StrokesEntry("善", 12, 12, "口", "金"),
    StrokesEntry("仙", 5, 5, "人", "金"),
    StrokesEntry("先", 6, 6, "儿", "金"),
    StrokesEntry("成", 6, 7, "戈", "火"),         # 戈 부수 보정
    StrokesEntry("聖", 13, 13, "耳", "土"),
    StrokesEntry("城", 9, 10, "土", "土"),        # 土 부수
    StrokesEntry("誠", 13, 14, "言", "金"),
    StrokesEntry("盛", 11, 12, "皿", "火"),
    StrokesEntry("性", 8, 9, "心", "金"),         # 忄 → 心
    StrokesEntry("珹", 11, 12, "玉", "金"),       # 玉 → 11+1
    StrokesEntry("星", 9, 9, "日", "火"),         # 불용
    StrokesEntry("世", 5, 5, "一", "金"),
    StrokesEntry("洗", 9, 10, "水", "水"),
    StrokesEntry("少", 4, 4, "小", "金"),
    StrokesEntry("小", 3, 3, "小", "金"),         # 불용
    StrokesEntry("素", 10, 10, "糸", "金"),
    StrokesEntry("松", 8, 8, "木", "木"),
    StrokesEntry("壽", 14, 14, "士", "金"),
    StrokesEntry("淑", 11, 12, "水", "水"),
    StrokesEntry("純", 10, 10, "糸", "金"),
    StrokesEntry("舜", 12, 12, "舛", "水"),
    StrokesEntry("勝", 12, 12, "力", "土"),
    StrokesEntry("詩", 13, 13, "言", "金"),
    StrokesEntry("時", 10, 10, "日", "火"),
    StrokesEntry("信", 9, 9, "人", "金"),
    StrokesEntry("新", 13, 13, "斤", "金"),
    StrokesEntry("辛", 7, 7, "辛", "金"),
    StrokesEntry("身", 7, 7, "身", "火"),
    StrokesEntry("實", 14, 14, "宀", "金"),
    StrokesEntry("心", 4, 4, "心", "金"),

    # ── ㅇ ──
    StrokesEntry("我", 7, 7, "戈", "金"),
    StrokesEntry("安", 6, 6, "宀", "土"),
    StrokesEntry("愛", 13, 13, "心", "土"),
    StrokesEntry("陽", 12, 17, "阜", "土"),       # 阝(阜) 보정
    StrokesEntry("洋", 9, 10, "水", "水"),
    StrokesEntry("良", 7, 7, "艮", "火"),
    StrokesEntry("億", 15, 15, "人", "土"),
    StrokesEntry("彦", 9, 9, "彡", "土"),
    StrokesEntry("彦", 9, 9, "彡", "土"),  # 중복 방지 위해 한 번만
    StrokesEntry("彦", 9, 9, "彡", "土"),
    StrokesEntry("妍", 9, 9, "女", "水"),
    StrokesEntry("延", 7, 7, "廴", "土"),
    StrokesEntry("淵", 11, 12, "水", "水"),
    StrokesEntry("英", 9, 11, "艸", "木"),
    StrokesEntry("永", 5, 5, "水", "水"),
    StrokesEntry("瑩", 15, 16, "玉", "金"),
    StrokesEntry("榮", 14, 14, "木", "木"),
    StrokesEntry("映", 9, 9, "日", "火"),
    StrokesEntry("禮", 18, 18, "示", "木"),
    StrokesEntry("睿", 14, 14, "目", "金"),
    StrokesEntry("藝", 19, 21, "艸", "木"),
    StrokesEntry("五", 4, 4, "二", "土"),
    StrokesEntry("玉", 5, 5, "玉", "金"),
    StrokesEntry("溫", 13, 14, "水", "水"),
    StrokesEntry("完", 7, 7, "宀", "木"),
    StrokesEntry("旺", 8, 8, "日", "火"),
    StrokesEntry("龍", 16, 16, "龍", "土"),
    StrokesEntry("祐", 9, 10, "示", "土"),
    StrokesEntry("雨", 8, 8, "雨", "水"),
    StrokesEntry("宇", 6, 6, "宀", "土"),
    StrokesEntry("旭", 6, 6, "日", "火"),
    StrokesEntry("雲", 12, 12, "雨", "水"),
    StrokesEntry("元", 4, 4, "儿", "木"),
    StrokesEntry("原", 10, 10, "厂", "土"),
    StrokesEntry("園", 13, 13, "囗", "土"),
    StrokesEntry("月", 4, 4, "月", "水"),          # 불용
    StrokesEntry("胤", 9, 9, "肉", "土"),
    StrokesEntry("允", 4, 4, "儿", "土"),
    StrokesEntry("尹", 4, 4, "尸", "土"),
    StrokesEntry("銀", 14, 14, "金", "金"),
    StrokesEntry("殷", 10, 10, "殳", "土"),
    StrokesEntry("乙", 1, 1, "乙", "木"),
    StrokesEntry("音", 9, 9, "音", "土"),
    StrokesEntry("仁", 4, 4, "人", "木"),
    StrokesEntry("人", 2, 2, "人", "金"),
    StrokesEntry("日", 4, 4, "日", "火"),
    StrokesEntry("一", 1, 1, "一", "水"),

    # ── ㅈ ──
    StrokesEntry("子", 3, 3, "子", "水"),
    StrokesEntry("自", 6, 6, "自", "金"),
    StrokesEntry("慈", 13, 13, "心", "金"),
    StrokesEntry("作", 7, 7, "人", "火"),
    StrokesEntry("章", 11, 11, "立", "金"),
    StrokesEntry("長", 8, 8, "長", "木"),
    StrokesEntry("在", 6, 6, "土", "土"),
    StrokesEntry("才", 3, 4, "手", "金"),         # 扌 → 手
    StrokesEntry("載", 13, 13, "車", "火"),
    StrokesEntry("齋", 17, 17, "齊", "土"),
    StrokesEntry("正", 5, 5, "止", "金"),
    StrokesEntry("貞", 9, 9, "貝", "金"),
    StrokesEntry("廷", 7, 7, "廴", "火"),
    StrokesEntry("靜", 16, 16, "靑", "金"),
    StrokesEntry("精", 14, 14, "米", "木"),
    StrokesEntry("情", 11, 12, "心", "金"),
    StrokesEntry("淨", 11, 12, "水", "水"),
    StrokesEntry("珍", 9, 10, "玉", "金"),
    StrokesEntry("眞", 10, 10, "目", "金"),
    StrokesEntry("辰", 7, 7, "辰", "土"),
    StrokesEntry("智", 12, 12, "日", "火"),
    StrokesEntry("志", 7, 7, "心", "火"),
    StrokesEntry("地", 6, 6, "土", "土"),          # 불용
    StrokesEntry("祉", 8, 9, "示", "土"),
    StrokesEntry("鎭", 18, 18, "金", "金"),
    StrokesEntry("振", 10, 11, "手", "火"),
    StrokesEntry("眞", 10, 10, "目", "金"),

    # ── ㅊ ──
    StrokesEntry("茶", 9, 11, "艸", "木"),
    StrokesEntry("贊", 19, 19, "貝", "金"),
    StrokesEntry("讚", 26, 26, "言", "金"),
    StrokesEntry("昌", 8, 8, "日", "火"),
    StrokesEntry("彩", 11, 11, "彡", "金"),
    StrokesEntry("採", 11, 12, "手", "金"),
    StrokesEntry("天", 4, 4, "大", "火"),          # 불용
    StrokesEntry("淸", 11, 12, "水", "水"),
    StrokesEntry("靑", 8, 8, "靑", "木"),
    StrokesEntry("春", 9, 9, "日", "火"),
    StrokesEntry("忠", 8, 8, "心", "火"),
    StrokesEntry("致", 10, 10, "至", "火"),

    # ── ㅋㅌㅍㅎ ──
    StrokesEntry("快", 7, 8, "心", "木"),
    StrokesEntry("泰", 9, 9, "水", "水"),
    StrokesEntry("太", 4, 4, "大", "木"),
    StrokesEntry("通", 11, 14, "辵", "火"),
    StrokesEntry("八", 2, 2, "八", "金"),
    StrokesEntry("平", 5, 5, "干", "土"),
    StrokesEntry("豊", 13, 13, "豆", "火"),
    StrokesEntry("夏", 10, 10, "夊", "火"),
    StrokesEntry("學", 16, 16, "子", "水"),
    StrokesEntry("漢", 14, 15, "水", "水"),
    StrokesEntry("韓", 17, 17, "韋", "水"),
    StrokesEntry("海", 10, 11, "水", "水"),
    StrokesEntry("行", 6, 6, "行", "火"),
    StrokesEntry("香", 9, 9, "香", "木"),
    StrokesEntry("玄", 5, 5, "玄", "火"),
    StrokesEntry("賢", 15, 15, "貝", "土"),
    StrokesEntry("顯", 23, 23, "頁", "火"),
    StrokesEntry("惠", 12, 12, "心", "水"),
    StrokesEntry("浩", 10, 11, "水", "水"),
    StrokesEntry("豪", 14, 14, "豕", "水"),
    StrokesEntry("好", 6, 6, "女", "水"),
    StrokesEntry("和", 8, 8, "口", "水"),
    StrokesEntry("華", 12, 14, "艸", "水"),       # 艹 → 艸
    StrokesEntry("花", 7, 10, "艸", "木"),         # 보고서 §2 예시 — 정확히 10획
    StrokesEntry("煥", 13, 13, "火", "火"),
    StrokesEntry("黃", 12, 12, "黃", "土"),
    StrokesEntry("孝", 7, 7, "子", "水"),
    StrokesEntry("熙", 13, 13, "火", "火"),
    StrokesEntry("禧", 17, 17, "示", "土"),
    StrokesEntry("姬", 9, 9, "女", "土"),
)


# 빠른 조회 dict — 중복 정의 시 마지막 값 우선
_BY_CHAR: dict[str, StrokesEntry] = {e.char: e for e in _ENTRIES}


# ─────────────────────────── Public API ───────────────────────────
#
# 조회 우선순위 (보고서 §2 변형 부수 보정 정확도 우선):
#   1. 수동 큐레이트 표(_BY_CHAR, 250자) — 변형 부수 보정 정확
#   2. Unihan 자동 추출(name_unihan, 8525자) — fallback
#
# 변형 부수 보정이 필요한 한자(花·江·萬 등)는 수동 표가 정답. Unihan은 단순
# 필획만 제공하므로 변형 부수 보정 없음.


def kangxi_strokes(char: str) -> int | None:
    """단일 한자의 강희자전 원획수. 수동 표 우선, Unihan fallback."""
    e = _BY_CHAR.get(char)
    if e is not None:
        return e.kangxi_strokes
    # Fallback — Unihan (변형 부수 보정 없는 단순 필획)
    try:
        from engine.divination.name.unihan import kangxi_strokes as _unihan_strokes
        return _unihan_strokes(char)
    except Exception:
        return None


def writing_strokes(char: str) -> int | None:
    """단일 한자의 일반 필획수. 수동 표 우선, Unihan fallback."""
    e = _BY_CHAR.get(char)
    if e is not None:
        return e.writing_strokes
    try:
        from engine.divination.name.unihan import kangxi_strokes as _unihan_strokes
        # Unihan은 단순 필획 = 일반 필획과 일치
        return _unihan_strokes(char)
    except Exception:
        return None


def resource_ohaeng(char: str) -> str | None:
    """자원오행. 수동 표 우선, Unihan 부수 매핑 fallback."""
    e = _BY_CHAR.get(char)
    if e is not None and e.resource_ohaeng:
        return e.resource_ohaeng
    try:
        from engine.divination.name.unihan import resource_ohaeng as _unihan_ohaeng
        return _unihan_ohaeng(char)
    except Exception:
        return None


def get_entry(char: str) -> StrokesEntry | None:
    return _BY_CHAR.get(char)


def total_strokes(name_hanja: str) -> dict[str, Any]:
    """이름(한자 문자열)의 글자별·합계 원획수 dict.

    Args:
        name_hanja: 한자 문자열 (예: "李珹旻")

    Returns:
        {
            "name": "李珹旻",
            "chars": ["李", "珹", "旻"],
            "kangxi": [7, 12, 8],         # 미수록은 None
            "writing": [7, 11, 8],
            "kangxi_total": 27,            # None 제외 합
            "missing": ["珹"]              # 미수록 char 목록 (실제로는 수록됨)
        }
    """
    chars = [c for c in (name_hanja or "") if c.strip()]
    kangxi = [kangxi_strokes(c) for c in chars]
    writing = [writing_strokes(c) for c in chars]
    missing = [c for c, k in zip(chars, kangxi) if k is None]
    total = sum(k for k in kangxi if k is not None)
    return {
        "name": name_hanja,
        "chars": chars,
        "kangxi": kangxi,
        "writing": writing,
        "kangxi_total": total,
        "missing": missing,
    }


def total_count() -> int:
    return len(_BY_CHAR)
