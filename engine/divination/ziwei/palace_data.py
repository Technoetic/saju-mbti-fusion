"""자미두수(紫微斗數) 결정론 명반 데이터 — 12궁·14주성·오행국·납음·생년사화 메타.

본 모듈은 ADR-002·010·015 정합 — 결정론 분류/배치 데이터만, LLM 작문 분리.

근거 (vault/references/ziwei-doushu-anseong.md):
  · 《자미두수전서(紫微斗數全書)》 안성법(安星法) 원전
  · 《삼명통회(三命通會)》 오호둔법(五虎遁法)·납음오행(納音五行)
  · 딥리서치 27건 종합 (자미/Export.md, 2차 자료)

원칙 (ADR-002·006·010·015):
  · 배치는 결정론 (생년월일시 → 동일 명반), 길흉 단정 X
  · 묘왕리함(廟旺利陷) 밝기 판정 유파 차 → 미산출
  · 생년사화 유파 쟁점(庚년) → school 태그 병기 (ADR-002·015)
"""

from __future__ import annotations

from dataclasses import dataclass


# ─────────────────────────── 지지·천간 (자미두수 인덱스) ───────────────────────────
# 자미두수 지지 인덱스: 자=0 축=1 인=2 ... 해=11 (사주 관례와 동일)

ZHI_KO: tuple[str, ...] = ("자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해")
ZHI_HANJA: tuple[str, ...] = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")
GAN_KO: tuple[str, ...] = ("갑", "을", "병", "정", "무", "기", "경", "신", "임", "계")
GAN_HANJA: tuple[str, ...] = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")


def zhi_ko(idx: int) -> str:
    return ZHI_KO[idx % 12]


def zhi_hanja(idx: int) -> str:
    return ZHI_HANJA[idx % 12]


def gan_ko(idx: int) -> str:
    return GAN_KO[idx % 10]


# ─────────────────────────── 12궁(十二宮) 메타 ───────────────────────────

@dataclass(frozen=True)
class PalaceMeta:
    """12 사항궁 메타 (명궁 기점 배열 순서)."""
    seq: int          # 0=명궁 기점, 역행 순서 인덱스
    key: str          # 영문 키
    label_ko: str     # 한국어 명칭
    label_hanja: str  # 한자
    alias_ko: str     # 별칭 (노복=교우, 관록=사업 등, 없으면 "")


# 명궁 기점 역행(반시계) 배열 — 《자미두수전서》 안성역기법
TWELVE_PALACES: tuple[PalaceMeta, ...] = (
    PalaceMeta(0,  "ming",    "명궁",   "命宮",   ""),
    PalaceMeta(1,  "xiong_di", "형제궁", "兄弟宮", ""),
    PalaceMeta(2,  "fu_qi",   "부처궁", "夫妻宮", "배우자궁"),
    PalaceMeta(3,  "zi_nu",   "자녀궁", "子女宮", ""),
    PalaceMeta(4,  "cai_bo",  "재백궁", "財帛宮", ""),
    PalaceMeta(5,  "ji_e",    "질액궁", "疾厄宮", ""),
    PalaceMeta(6,  "qian_yi", "천이궁", "遷移宮", ""),
    PalaceMeta(7,  "nu_pu",   "노복궁", "奴僕宮", "교우궁"),
    PalaceMeta(8,  "guan_lu", "관록궁", "官祿宮", "사업궁"),
    PalaceMeta(9,  "tian_zhai", "전택궁", "田宅宮", ""),
    PalaceMeta(10, "fu_de",   "복덕궁", "福德宮", ""),
    PalaceMeta(11, "fu_mu",   "부모궁", "父母宮", ""),
)


def palace_meta_by_seq(seq: int) -> PalaceMeta:
    return TWELVE_PALACES[seq % 12]


# ─────────────────────────── 14주성(十四主星) 메타 ───────────────────────────

@dataclass(frozen=True)
class MainStar:
    """14 주성 메타."""
    key: str
    label_ko: str
    label_hanja: str
    series: str       # "ziwei"(자미성계) | "tianfu"(천부성계)
    offset: int       # 자미/천부 위치로부터의 궁 오프셋 (배치 계산용)


# 자미성계 (역행 배치) — 자미 기준 오프셋 (음수=역행)
# 자미(0) 천기(-1) [공] 태양(-3) 무곡(-4) 천동(-5) [공][공] 염정(-8)
# 천부성계 (순행 배치) — 천부 기준 오프셋
# 천부(0) 태음(+1) 탐랑(+2) 거문(+3) 천상(+4) 천량(+5) 칠살(+6) [공][공][공] 파군(+10)
FOURTEEN_STARS: tuple[MainStar, ...] = (
    # 자미성계 (紫微系)
    MainStar("ziwei",    "자미", "紫微", "ziwei",  0),
    MainStar("tianji",   "천기", "天機", "ziwei",  -1),
    MainStar("taiyang",  "태양", "太陽", "ziwei",  -3),
    MainStar("wuqu",     "무곡", "武曲", "ziwei",  -4),
    MainStar("tiantong", "천동", "天同", "ziwei",  -5),
    MainStar("lianzhen", "염정", "廉貞", "ziwei",  -8),
    # 천부성계 (天府系)
    MainStar("tianfu",   "천부", "天府", "tianfu", 0),
    MainStar("taiyin",   "태음", "太陰", "tianfu", 1),
    MainStar("tanlang",  "탐랑", "貪狼", "tianfu", 2),
    MainStar("jumen",    "거문", "巨門", "tianfu", 3),
    MainStar("tianxiang", "천상", "天相", "tianfu", 4),
    MainStar("tianliang", "천량", "天梁", "tianfu", 5),
    MainStar("qisha",    "칠살", "七殺", "tianfu", 6),
    MainStar("pojun",    "파군", "破軍", "tianfu", 10),
)

# 주성 키 → 한국어 라벨 (사화 배속 참조용)
STAR_LABEL_KO: dict[str, str] = {s.key: s.label_ko for s in FOURTEEN_STARS}
STAR_KEY_BY_KO: dict[str, str] = {s.label_ko: s.key for s in FOURTEEN_STARS}


# ─────────────────────────── 사화 전용 보조성(輔星) ───────────────────────────
# 생년사화 화과·화기가 14주성이 아닌 보조성(문창·문곡·좌보·우필)에 붙는 년간(丙戊己辛壬) 대응.
# 본 시스템은 보조성 위치는 산출하지 않고 사화 배속 명칭에만 사용 (핵심 명반 범위).
AUX_STAR_LABEL_KO: dict[str, str] = {
    "wenchang": "문창",   # 文昌
    "wenqu": "문곡",      # 文曲
    "zuofu": "좌보",      # 左輔
    "youbi": "우필",      # 右弼
}

# 사화 배속에 등장 가능한 모든 성요(주성 + 보조성) 한국어 라벨
SIHUA_STAR_LABEL_KO: dict[str, str] = {**STAR_LABEL_KO, **AUX_STAR_LABEL_KO}


# ─────────────────────────── 오행국(五行局) 메타 ───────────────────────────

@dataclass(frozen=True)
class WuxingJu:
    """오행국 (국수 2~6)."""
    num: int          # 국수 2~6
    label_ko: str     # "수이국" 등
    label_hanja: str  # "水二局" 등
    element_ko: str   # 오행


WUXING_JU: dict[int, WuxingJu] = {
    2: WuxingJu(2, "수이국", "水二局", "수"),
    3: WuxingJu(3, "목삼국", "木三局", "목"),
    4: WuxingJu(4, "금사국", "金四局", "금"),
    5: WuxingJu(5, "토오국", "土五局", "토"),
    6: WuxingJu(6, "화육국", "火六局", "화"),
}


# ─────────────────────────── 오호둔(五虎遁) — 년간 → 인월(寅) 천간 ───────────────────────────
# 오호둔가: 갑기지년 병인두, 을경지년 무인두, 병신지년 경인두, 정임지년 임인두, 무계지년 갑인두
# 년간 index(0~9) → 인궁(寅=2) 천간 index

WUHUDUN_YIN_STEM: dict[int, int] = {
    0: 2, 5: 2,   # 갑·기 → 병(2)
    1: 4, 6: 4,   # 을·경 → 무(4)
    2: 6, 7: 6,   # 병·신 → 경(6)
    3: 8, 8: 8,   # 정·임 → 임(8)
    4: 0, 9: 0,   # 무·계 → 갑(0)
}


# ─────────────────────────── 납음오행(納音五行) → 국수 ───────────────────────────
# 60갑자 index(0=갑자 ... 59=계해) → 오행국 국수 (2~6). 30쌍.
# 표준 납음: 金4 火6 木3 土5 순환 (자미두수 전 계열 공통)

NAYIN_JU: tuple[int, ...] = (
    4, 4, 6, 6, 3, 3, 5, 5, 4, 4,  # 갑자~계유
    6, 6, 2, 2, 5, 5, 4, 4, 3, 3,  # 갑술~계미
    2, 2, 5, 5, 6, 6, 3, 3, 2, 2,  # 갑신~계사
    4, 4, 6, 6, 3, 3, 5, 5, 4, 4,  # 갑오~계묘
    6, 6, 2, 2, 5, 5, 4, 4, 3, 3,  # 갑진~계축
    2, 2, 5, 5, 6, 6, 3, 3, 2, 2,  # 갑인~계해
)


# ─────────────────────────── 생년사화(生年四化) — 년간별 주성 배속 ───────────────────────────
# ★ 유파 쟁점 (ADR-002·015): 庚년 등 일부 년간은 유파 차. school 태그 병기.
# 배속: (화록, 화권, 화과, 화기) = 주성 key.
# 아래는 대만 현대 표준(중주파 우세) 기준. 딥리서치 교차검증으로 확정 예정.
# 유파 병기가 필요한 년간은 SIHUA_VARIANTS 참조.

@dataclass(frozen=True)
class SiHuaSet:
    """년간별 사화 배속."""
    year_gan_idx: int
    lu_star: str       # 화록(化祿) 주성 key
    quan_star: str     # 화권(化權)
    ke_star: str       # 화과(化科)
    ji_star: str       # 화기(化忌)


# 년간별 사화 기본 배속 — 원전 《자미두수전서》 卷二 〈安祿權科忌四星變化訣〉 + 남파 표준.
# ★ 2차 원전 축자 딥리서치(자미/2차-원전축자-딥리서치.json, vote 3-0) 확정:
#   원전 결(訣): "甲廉破武陽伴, 乙機梁紫月, 丙同機昌廉, 丁月同機巨,
#                戊貪月弼機為主(우필화과), 己武貪梁曲, 庚日武陰同為首(태음화과),
#                辛巨陽曲昌, 壬梁紫府武, 癸破巨陰貪" (록권과기 순).
#   → 戊 화과=우필, 庚 화과=태음이 원전(全書) 확정. 본 SIHUA_DEFAULT와 일치.
#   iztro 남파 구현(戊=우필·庚=태음·壬=좌보)과도 일치.
#   戊·庚·壬 3년간은 중주파(왕정지)·북파 이설 실재 → SIHUA_VARIANTS 병기.
# 보조성(문창wenchang·문곡wenqu·좌보zuofu·우필youbi)은 사화 배속에만 사용.
SIHUA_DEFAULT: dict[int, SiHuaSet] = {
    0: SiHuaSet(0, "lianzhen",  "pojun",     "wuqu",      "taiyang"),   # 甲: 염정·파군·무곡·태양 (합의)
    1: SiHuaSet(1, "tianji",    "tianliang", "ziwei",     "taiyin"),    # 乙: 천기·천량·자미·태음 (합의)
    2: SiHuaSet(2, "tiantong",  "tianji",    "wenchang",  "lianzhen"),  # 丙: 천동·천기·문창·염정
    3: SiHuaSet(3, "taiyin",    "tiantong",  "tianji",    "jumen"),     # 丁: 태음·천동·천기·거문 (합의)
    4: SiHuaSet(4, "tanlang",   "taiyin",    "youbi",     "tianji"),    # 戊 ★쟁점: 탐랑·태음·우필·천기 (중주파)
    5: SiHuaSet(5, "wuqu",      "tanlang",   "tianliang", "wenqu"),     # 己: 무곡·탐랑·천량·문곡
    6: SiHuaSet(6, "taiyang",   "wuqu",      "taiyin",    "tiantong"),  # 庚 ★쟁점: 태양·무곡·태음·천동 (중주파)
    7: SiHuaSet(7, "jumen",     "taiyang",   "wenqu",     "wenchang"),  # 辛: 거문·태양·문곡·문창
    8: SiHuaSet(8, "tianliang", "ziwei",     "zuofu",     "wuqu"),      # 壬 ★쟁점: 천량·자미·좌보·무곡 (중주파)
    9: SiHuaSet(9, "pojun",     "jumen",     "taiyin",    "tanlang"),   # 癸: 파군·거문·태음·탐랑 (합의)
}

# ★ 유파 병기 (ADR-002·015) — 딥리서치 확정: 戊·庚·壬 미합의 3년간.
#   각 유파의 완결 4화를 원전 축자로 확정하지 못해(딥리서치 openQuestion),
#   널리 통용되는 2대 관례(중주파 vs 전서/북파 계열)만 병기. 확정 시 보강.
SIHUA_VARIANTS: dict[int, dict[str, SiHuaSet]] = {
    4: {  # 戊
        "중주파": SiHuaSet(4, "tanlang", "taiyin", "youbi", "tianji"),
        "전서계열": SiHuaSet(4, "tanlang", "taiyin", "taiyang", "tianji"),  # 화과=태양 관례
    },
    6: {  # 庚 — '미궁의 경간(迷樣的庚干)' 최대 쟁점. 원전 검증 4갈래 (자미/자미두수 안성법 원전 검증.md):
        "남파": SiHuaSet(6, "taiyang", "wuqu", "taiyin", "tiantong"),        # 陽武陰同 (전집·전서영인·흠천, 화과=태음) — 기본
        "민파": SiHuaSet(6, "taiyang", "wuqu", "tiantong", "taiyin"),        # 陽武同陰 (민파, 화과=천동·화기=태음)
        "중주파": SiHuaSet(6, "taiyang", "wuqu", "tianfu", "tiantong"),      # 陽武府同 (왕정지, 화과=천부)
        "북파": SiHuaSet(6, "taiyang", "wuqu", "tiantong", "tianxiang"),     # 陽武同相 (비성파, 화과=천동·화기=천상)
    },
    8: {  # 壬
        "중주파": SiHuaSet(8, "tianliang", "ziwei", "zuofu", "wuqu"),
        "전서계열": SiHuaSet(8, "tianliang", "ziwei", "tianfu", "wuqu"),    # 화과=천부 관례
    },
}


# ─────────────────────────── 면책 ───────────────────────────

DISCLAIMER = (
    "본 자미두수 명반은 《자미두수전서》 안성법 결정론 배치이며, "
    "운명·연애·재물·직업 단정 X. 참고용이며 의료·법률·금융 의사결정의 "
    "단독 근거가 될 수 없습니다. 생년사화는 유파(중주파·흠천사법 등)에 따라 "
    "일부 배속이 다를 수 있어 채택 유파를 함께 표기합니다."
)


__all__ = [
    "ZHI_KO", "ZHI_HANJA", "GAN_KO", "GAN_HANJA",
    "zhi_ko", "zhi_hanja", "gan_ko",
    "PalaceMeta", "TWELVE_PALACES", "palace_meta_by_seq",
    "MainStar", "FOURTEEN_STARS", "STAR_LABEL_KO", "STAR_KEY_BY_KO",
    "WuxingJu", "WUXING_JU",
    "WUHUDUN_YIN_STEM", "NAYIN_JU",
    "SiHuaSet", "SIHUA_DEFAULT", "SIHUA_VARIANTS",
    "DISCLAIMER",
]
