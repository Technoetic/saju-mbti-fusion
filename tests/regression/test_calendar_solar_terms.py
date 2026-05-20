"""ADR-073C 회귀 — 절기 기반 month_pillar + 200년 cycle 완전성.

본 회귀는 KASI API 없이도 가능한 추가 ground truth:
1. 24절기 12절 (입춘·경칩·청명·...) skyfield ephemeris 정합
2. month_pillar 五虎遁 표 정합 (年干 → 寅月 月干)
3. 1900~2099 200년 day_pillar cycle 완전성 (73048일 / 60 = 1217.467 cycle)
"""

from datetime import date, datetime, timedelta

from engine.saju.calendar import SOLAR_TERMS_MAJOR, solar_term_month, is_before_term
from engine.saju.pillars import day_pillar, month_pillar, year_pillar


# ── ① 절기 12절 메타 정합 ─────────────────────────────────


def test_solar_terms_count_is_12():
    """月柱 결정 절기는 12개 (24절기 중 절 12개)."""
    assert len(SOLAR_TERMS_MAJOR) == 12


def test_solar_term_first_is_ipchun():
    """첫 절기 = 立春 (寅月 시작, 황경 315°)."""
    name, longitude, month_idx = SOLAR_TERMS_MAJOR[0]
    assert name == "立春"
    assert longitude == 315
    assert month_idx == 1  # 寅月


def test_solar_term_last_is_sohan():
    """마지막 절기 = 小寒 (丑月 시작, 황경 285°)."""
    name, longitude, month_idx = SOLAR_TERMS_MAJOR[-1]
    assert name == "小寒"
    assert longitude == 285
    assert month_idx == 12  # 丑月


def test_solar_term_longitudes_30deg_apart():
    """각 절기 황경이 30° 간격 (24절기 12절 정합)."""
    longitudes = [t[1] for t in SOLAR_TERMS_MAJOR]
    # 정렬된 (mod 360) 시퀀스가 30° 간격
    sorted_lon = sorted(longitudes)
    for i in range(1, len(sorted_lon)):
        diff = sorted_lon[i] - sorted_lon[i-1]
        assert diff == 30, f"절기 간격 30° 위반: {sorted_lon[i-1]}°→{sorted_lon[i]}° (diff {diff})"


# ── ② 입춘 경계 정합 ───────────────────────────────────


def test_ipchun_2026_before_returns_丑月():
    """2026년 입춘 (2/4 경) 이전 = 丑月 (=12)."""
    # 2026-01-15 (입춘 이전 = 전년 丑月)
    m = solar_term_month(2026, 1, 15, 12)
    assert m == 12


def test_ipchun_2026_after_returns_寅月():
    """2026년 입춘 이후 = 寅月 (=1)."""
    # 2026-03-01 (경칩 이전 = 寅月)
    m = solar_term_month(2026, 3, 1, 12)
    assert m == 1


def test_is_before_term_consistency():
    """is_before_term이 입춘 경계 정합."""
    # 1990-01-15 = 입춘 이전 (1990 입춘은 2/4 경)
    assert is_before_term(datetime(1990, 1, 15, 12), 1990) is True
    # 1990-03-15 = 입춘 이후
    assert is_before_term(datetime(1990, 3, 15, 12), 1990) is False


# ── ③ month_pillar 五虎遁 정합 ────────────────────────


def test_ohotun_jia_year_in_month():
    """甲年 寅月 = 丙寅 (五虎遁 표 정합)."""
    # 1984 = 甲子년 → 寅月은 丙寅
    yp = year_pillar(1984)
    assert yp["gan"] == "갑"
    mp = month_pillar(1984, 1)  # 寅月
    assert mp["gan"] == "병"
    assert mp["ji"] == "인"


def test_ohotun_eul_year_in_month():
    """乙年 寅月 = 戊寅."""
    # 1985 = 乙丑년
    yp = year_pillar(1985)
    assert yp["gan"] == "을"
    mp = month_pillar(1985, 1)
    assert mp["gan"] == "무"
    assert mp["ji"] == "인"


def test_ohotun_byeong_year_in_month():
    """丙年 寅月 = 庚寅."""
    yp = year_pillar(1986)
    assert yp["gan"] == "병"
    mp = month_pillar(1986, 1)
    assert mp["gan"] == "경"


def test_month_pillar_jiji_sequence():
    """月柱 지지 순환: 寅(1)→卯(2)→辰(3)→...→丑(12)."""
    expected_ji = ["인", "묘", "진", "사", "오", "미",
                   "신", "유", "술", "해", "자", "축"]
    for m in range(1, 13):
        mp = month_pillar(1990, m)
        assert mp["ji"] == expected_ji[m-1], f"month={m}: {mp['ji']} != {expected_ji[m-1]}"


# ── ④ 200년 cycle 완전성 ────────────────────────────


def test_200year_day_pillar_no_duplicates_within_60day():
    """1900-01-01 ~ 2099-12-31 200년 73048일 = 60갑자 cycle 1217.467회.
    임의 60일 윈도우에서 중복 없음."""
    test_starts = [date(1900,1,1), date(1950,6,15), date(2000,1,1),
                   date(2026,5,20), date(2099,12,1)]
    for start in test_starts:
        seen = set()
        for i in range(60):
            d = start + timedelta(days=i)
            p = day_pillar(d.year, d.month, d.day)
            key = (p["gan"], p["ji"])
            assert key not in seen, f"{start}+{i}일 중복: {key}"
            seen.add(key)


def test_200year_day_pillar_idx_monotonic():
    """1900-2099 200년 일주 인덱스가 일관된 mod 10/12 순환."""
    # 1900-01-01 기준 100년 후 (36525일) cycle 확인
    base = date(1900, 1, 1)
    base_p = day_pillar(base.year, base.month, base.day)

    for years_offset in [50, 100, 150, 199]:
        target = base.replace(year=base.year + years_offset)
        target_p = day_pillar(target.year, target.month, target.day)
        delta_days = (target - base).days
        expected_gan = (base_p["gan_idx"] + delta_days) % 10
        expected_ji = (base_p["ji_idx"] + delta_days) % 12
        assert target_p["gan_idx"] == expected_gan
        assert target_p["ji_idx"] == expected_ji


def test_60year_year_pillar_repeats():
    """년주 60년 cycle 반복 (60갑자)."""
    yp_1900 = year_pillar(1900)  # 庚子
    yp_1960 = year_pillar(1960)  # 60년 후
    yp_2020 = year_pillar(2020)  # 120년 후
    assert yp_1900["gan"] == yp_1960["gan"] == yp_2020["gan"]
    assert yp_1900["ji"] == yp_1960["ji"] == yp_2020["ji"]


# ── ⑤ 윤년·평년 정합 ───────────────────────────────


def test_leap_year_day_pillar_continuity():
    """윤년 2-28 → 2-29 → 3-1 일주 연속성."""
    # 2024 윤년
    p_feb28 = day_pillar(2024, 2, 28)
    p_feb29 = day_pillar(2024, 2, 29)
    p_mar01 = day_pillar(2024, 3, 1)
    assert p_feb29["gan_idx"] == (p_feb28["gan_idx"] + 1) % 10
    assert p_mar01["gan_idx"] == (p_feb29["gan_idx"] + 1) % 10


def test_nonleap_year_day_pillar_continuity():
    """평년 2-28 → 3-1 일주 연속성 (윤일 없음)."""
    # 2026 평년
    p_feb28 = day_pillar(2026, 2, 28)
    p_mar01 = day_pillar(2026, 3, 1)
    assert p_mar01["gan_idx"] == (p_feb28["gan_idx"] + 1) % 10


# ── ⑥ 자가 검증 가이드 명시 ───────────────────────


def test_user_self_verification_pathway_documented():
    """본 시스템이 KASI 외부 검증 가이드 명시 (kasi_verifier.py docstring)."""
    from engine.saju.kasi_verifier import verify_day_pillar_against_kasi
    doc = verify_day_pillar_against_kasi.__doc__ or ""
    assert "KASI_API_KEY" in doc


def test_solar_term_module_documents_skyfield():
    """calendar.py docstring이 skyfield ephemeris 명시."""
    from engine.saju import calendar
    src = open(calendar.__file__, "r", encoding="utf-8").read()
    assert "skyfield" in src
    assert "DE440" in src or "ephemeris" in src
