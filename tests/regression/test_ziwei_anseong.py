"""자미두수 안성법(安星法) 결정론 회귀 — engine/divination/ziwei.

영역:
  · 명궁·신궁 정위, 오호둔·납음 오행국, 자미성 정국표, 14주성 배치, 12궁 역행
  · 검증 예시 (1990-05-15 10시 남성) 고정값 회귀
  · 자미성 정국표 앵커 5개 (국수 2~6 생일1일)
  · 생년사화 유파 병기 (戊·庚·壬)
  · ADR-006 길흉 단정 필드 부재
  · 순수 안성 함수는 lunar-python 불요. compute_ziwei_chart만 lunar-python 필요(있으면 검증).

근거: vault/references/ziwei-doushu-anseong.md
"""

import pytest

from engine.divination.ziwei import an_xing
from engine.divination.ziwei.palace_data import (
    FOURTEEN_STARS,
    SIHUA_STAR_LABEL_KO,
    STAR_LABEL_KO,
    TWELVE_PALACES,
    zhi_ko,
)


# ─────────────────────────── 명궁·신궁 정위 ───────────────────────────

def test_ming_palace_example():
    """검증 예시: 음력 4월 사시(5) → 명궁 자궁(0)."""
    assert an_xing.ming_palace(4, 5) == 0


def test_body_palace_example():
    """검증 예시: 음력 4월 사시(5) → 신궁 술궁(10)."""
    assert an_xing.body_palace(4, 5) == 10


def test_ming_palace_range_validation():
    """월·시 범위 밖은 ValueError."""
    with pytest.raises(ValueError):
        an_xing.ming_palace(0, 5)
    with pytest.raises(ValueError):
        an_xing.ming_palace(4, 12)


def test_ming_palace_deterministic():
    """동일 입력 → 동일 명궁 (결정론)."""
    assert an_xing.ming_palace(7, 3) == an_xing.ming_palace(7, 3)


# ─────────────────────────── 오행국 (오호둔·납음) ───────────────────────────

def test_palace_stem_example():
    """검증 예시: 경(6)년 자궁(0) 천간 → 무(4)."""
    assert an_xing.palace_stem(6, 0) == 4


def test_wuxing_ju_example():
    """검증 예시: 경년 명궁 자궁 → 화6국."""
    ju = an_xing.wuxing_ju(6, 0)
    assert ju.num == 6
    assert ju.label_ko == "화육국"


# ─────────────────────────── 자미성 정국표 ───────────────────────────

def test_ziwei_star_example():
    """검증 예시: 화6국 생일21 → 인궁(2). (Export.md '진'은 오기, 표준표 채택)"""
    assert an_xing.ziwei_star(6, 21) == 2


def test_ziwei_star_anchors():
    """정국표 앵커 5개: 국수 2~6 생일1일 → 축·진·해·오·유."""
    expected = {2: "축", 3: "진", 4: "해", 5: "오", 6: "유"}
    for ju, zhi in expected.items():
        assert zhi_ko(an_xing.ziwei_star(ju, 1)) == zhi, f"{ju}국 1일"


def test_ziwei_star_range_validation():
    """국수·생일 범위 밖은 ValueError."""
    with pytest.raises(ValueError):
        an_xing.ziwei_star(7, 15)
    with pytest.raises(ValueError):
        an_xing.ziwei_star(6, 31)


# ─────────────────────────── 14주성 배치 ───────────────────────────

def test_fourteen_stars_count():
    """14주성 전부 영속."""
    assert len(FOURTEEN_STARS) == 14
    assert len(STAR_LABEL_KO) == 14


def test_tianfu_symmetry():
    """자미-천부 인-신 축 대칭: 자미 인(2)→천부 인(2, 동궁), 자미 진(4)→천부 자(0)."""
    assert an_xing.tianfu_star(2) == 2
    assert an_xing.tianfu_star(4) == 0
    assert an_xing.tianfu_star(0) == 4


def test_place_stars_example():
    """검증 예시: 자미 인(2) → 명궁 자궁(0)에 파군."""
    pos = an_xing.place_fourteen_stars(2)
    ming_stars = [STAR_LABEL_KO[k] for k, p in pos.items() if p == 0]
    assert ming_stars == ["파군"]


def test_place_stars_all_placed():
    """14주성 모두 12궁 안에 배치 (인덱스 0~11)."""
    pos = an_xing.place_fourteen_stars(2)
    assert len(pos) == 14
    assert all(0 <= p <= 11 for p in pos.values())


def test_ziwei_series_offsets():
    """자미성계 역행 오프셋: 천기=자미-1, 태양=자미-3, 무곡=자미-4, 천동=자미-5, 염정=자미-8."""
    zw = 2  # 자미 인
    pos = an_xing.place_fourteen_stars(zw)
    assert pos["tianji"] == (zw - 1) % 12
    assert pos["taiyang"] == (zw - 3) % 12
    assert pos["wuqu"] == (zw - 4) % 12
    assert pos["tiantong"] == (zw - 5) % 12
    assert pos["lianzhen"] == (zw - 8) % 12


# ─────────────────────────── 12궁 배열 ───────────────────────────

def test_twelve_palaces_count():
    """12궁 전부 영속."""
    assert len(TWELVE_PALACES) == 12
    assert TWELVE_PALACES[0].key == "ming"
    assert TWELVE_PALACES[11].key == "fu_mu"


def test_arrange_palaces_reverse():
    """12궁 역행: 명궁 자(0) → 형제 해(11) → 부처 술(10)."""
    layout = dict(an_xing.arrange_palaces(0))
    assert layout[0] == 0    # 명궁 자
    assert layout[1] == 11   # 형제궁 해
    assert layout[2] == 10   # 부처궁 술


def test_arrange_palaces_all_distinct():
    """12궁이 12지지에 1:1 배치."""
    branches = [br for _, br in an_xing.arrange_palaces(0)]
    assert sorted(branches) == list(range(12))


def test_palace_alias():
    """노복=교우, 관록=사업 별칭 영속."""
    aliases = {p.key: p.alias_ko for p in TWELVE_PALACES}
    assert aliases["nu_pu"] == "교우궁"
    assert aliases["guan_lu"] == "사업궁"


# ─────────────────────────── 생년사화 ───────────────────────────

def test_sihua_consensus_jia():
    """甲년 사화 전 유파 합의: 록염정·권파군·과무곡·기태양."""
    sh = an_xing.sihua(0)
    assert (sh.lu_star_ko, sh.quan_star_ko, sh.ke_star_ko, sh.ji_star_ko) == \
        ("염정", "파군", "무곡", "태양")


def test_sihua_original_text_confirmed():
    """원전 《자미두수전서》 卷二 확정 (2차 축자 딥리서치 vote 3-0):
    戊 화과=우필, 庚 화과=태음, 庚 화기=천동 (남파/원전 기본)."""
    assert an_xing.sihua(4).ke_star_ko == "우필"   # 戊貪月弼機 → 화과 우필
    assert an_xing.sihua(6).ke_star_ko == "태음"   # 庚日武陰同 → 화과 태음
    assert an_xing.sihua(6).ji_star_ko == "천동"   # 庚 화기 천동 (남파)


def test_sihua_geng_variants():
    """庚년 4유파 매트릭스 (원전 검증):
    남파 陽武陰同 / 민파 陽武同陰 / 중주파 陽武府同 / 북파 陽武同相."""
    napa = an_xing.sihua(6, "남파")
    assert (napa.ke_star_ko, napa.ji_star_ko) == ("태음", "천동")     # 陽武陰同
    minpa = an_xing.sihua(6, "민파")
    assert (minpa.ke_star_ko, minpa.ji_star_ko) == ("천동", "태음")   # 陽武同陰
    jungju = an_xing.sihua(6, "중주파")
    assert jungju.ke_star_ko == "천부"                              # 陽武府同
    bukpa = an_xing.sihua(6, "북파")
    assert (bukpa.ke_star_ko, bukpa.ji_star_ko) == ("천동", "천상")   # 陽武同相
    assert an_xing.sihua(6).has_variants is True


def test_sihua_disputed_stems_flagged():
    """戊·庚·壬 3년간은 유파 병기 대상 (딥리서치 확정)."""
    for gan in (4, 6, 8):
        assert an_xing.sihua(gan).has_variants is True


def test_sihua_aux_star_resolved():
    """보조성(문창 등)이 사화에 붙어도 라벨 해결 (PLACEHOLDER 없음)."""
    sh = an_xing.sihua(2)  # 丙: 화과=문창
    assert sh.ke_star_ko == "문창"
    assert "PLACEHOLDER" not in sh.ke_star_ko
    assert "문창" in SIHUA_STAR_LABEL_KO.values()


# ─────────────────────────── compute_ziwei_chart (lunar-python 연동) ───────────────────────────

_LUNAR_AVAILABLE = True
try:
    import lunar_python  # noqa: F401
except ImportError:
    _LUNAR_AVAILABLE = False


@pytest.mark.skipif(not _LUNAR_AVAILABLE, reason="lunar-python 미설치")
def test_compute_chart_example():
    """검증 예시 end-to-end: 1990-05-15 10시 → 명궁 자·화6국·자미 인·명궁 파군."""
    from datetime import date
    from engine.divination.ziwei.scoring import compute_ziwei_chart

    chart = compute_ziwei_chart(date(1990, 5, 15), 10, "M")
    assert chart.lunar_month == 4
    assert chart.lunar_day == 21
    assert chart.ming_branch_ko == "자"
    assert chart.body_branch_ko == "술"
    assert chart.ming_stem_ko == "무"
    assert chart.wuxing_ju_num == 6
    assert chart.ziwei_branch_ko == "인"
    ming_cell = next(p for p in chart.palaces if p.key == "ming")
    assert ming_cell.main_stars_ko == ("파군",)


@pytest.mark.skipif(not _LUNAR_AVAILABLE, reason="lunar-python 미설치")
def test_compute_chart_deterministic():
    """동일 입력 → 동일 명반 (결정론)."""
    from datetime import date
    from engine.divination.ziwei.scoring import compute_ziwei_chart

    c1 = compute_ziwei_chart(date(1985, 3, 20), 14, "F")
    c2 = compute_ziwei_chart(date(1985, 3, 20), 14, "F")
    assert c1 == c2


@pytest.mark.skipif(not _LUNAR_AVAILABLE, reason="lunar-python 미설치")
def test_compute_chart_all_palaces_present():
    """명반에 12궁 모두 존재."""
    from datetime import date
    from engine.divination.ziwei.scoring import compute_ziwei_chart

    chart = compute_ziwei_chart(date(2000, 1, 1), 0, "M")
    assert len(chart.palaces) == 12
    keys = {p.key for p in chart.palaces}
    assert keys == {m.key for m in TWELVE_PALACES}


# ─────────────────────────── ADR-006 길흉 단정 필드 부재 ───────────────────────────

def test_adr006_no_fortune_fields():
    """ZiweiChart에 길흉·수명·럭키 단정 필드 부재 (ADR-006)."""
    from engine.divination.ziwei.scoring import ZiweiChart
    forbidden = {
        "fortune", "luck", "lucky_number", "lucky_color", "wealth_outcome",
        "career_outcome", "love_outcome", "marriage_outcome", "lifespan",
        "brightness", "miao_wang",  # 묘왕리함 밝기도 미산출
    }
    fields = set(ZiweiChart.__dataclass_fields__.keys())
    assert not (fields & forbidden), f"금지 필드 존재: {fields & forbidden}"


def test_disclaimer_present():
    """면책 문구에 단정 차단 명시."""
    from engine.divination.ziwei.palace_data import DISCLAIMER
    assert "단정" in DISCLAIMER
    assert "단독 근거" in DISCLAIMER


@pytest.mark.skipif(not _LUNAR_AVAILABLE, reason="lunar-python 미설치")
def test_prompt_format_safety_guard():
    """프롬프트 포맷에 ADR-006 안전 장치 문구 포함."""
    from datetime import date
    from engine.divination.ziwei.scoring import compute_ziwei_chart, format_ziwei_for_prompt

    chart = compute_ziwei_chart(date(1990, 5, 15), 10, "M")
    text = format_ziwei_for_prompt(chart)
    assert "단정 금지" in text
    assert "임의 변경 금지" in text
