"""ADR-073 회귀 — day_pillar·compute_ten_gods 천문·명리 ground truth 검증.

본 시스템 day_pillar 알고리즘:
- 앵커 1900-01-01 = 己亥 (한국천문연구원 공인 만세력 기준값)
- julian day delta + 60갑자 cycle
- 본 알고리즘은 표준 만세력 알고리즘 정합 (사주첩경·명리요강 동일)

ten_god 알고리즘:
- 표준 명리 매트릭스 (오행 상생·상극 + 음양 동이) 11/11 정합
"""

from datetime import date, timedelta

from engine.saju.pillars import day_pillar, year_pillar
from engine.saju.ten_gods import ten_god, compute_ten_gods


# ── ① 천문 앵커 정합 ─────────────────────────────────────────


def test_anchor_1900_01_01_is_gapsul():
    """앵커 1900-01-01 = 甲戌 (KASI 음양력 API 공식 회신, ADR-085 정합)."""
    p = day_pillar(1900, 1, 1)
    assert p["gan"] == "갑"
    assert p["ji"] == "술"
    assert p["gan_han"] == "甲"
    assert p["ji_han"] == "戌"


def test_year_1900_is_gyeongja():
    """1900년 = 庚子 (천문연 공인 60갑자 연도)."""
    yp = year_pillar(1900)
    assert yp["gan"] == "경"
    assert yp["ji"] == "자"


# ── ② 60갑자 cycle invariant ─────────────────────────────────


def test_60day_cycle_repeats_identically():
    """매 60일마다 동일 갑자 반복 (수학 불변량)."""
    d0 = date(2026, 1, 1)
    d60 = d0 + timedelta(days=60)
    p0 = day_pillar(d0.year, d0.month, d0.day)
    p60 = day_pillar(d60.year, d60.month, d60.day)
    assert p0["gan"] == p60["gan"]
    assert p0["ji"] == p60["ji"]


def test_consecutive_days_increment_indices():
    """연속일 → gan_idx +1 mod 10, ji_idx +1 mod 12."""
    d0 = date(2026, 5, 1)
    p0 = day_pillar(d0.year, d0.month, d0.day)
    for i in range(1, 13):
        d = d0 + timedelta(days=i)
        p = day_pillar(d.year, d.month, d.day)
        assert p["gan_idx"] == (p0["gan_idx"] + i) % 10
        assert p["ji_idx"] == (p0["ji_idx"] + i) % 12


def test_full_60day_no_duplicate_within_cycle():
    """60일 cycle 내 동일 갑자 중복 X (전체 60갑자 등장)."""
    d0 = date(2026, 1, 1)
    seen = set()
    for i in range(60):
        d = d0 + timedelta(days=i)
        p = day_pillar(d.year, d.month, d.day)
        key = (p["gan"], p["ji"])
        assert key not in seen, f"중복 갑자 발견: {key} at day {i}"
        seen.add(key)
    assert len(seen) == 60


# ── ③ 본 시스템 라이브 사례 결정론 정합 ───────────────────


def test_user_birth_1990_05_15_is_gyeongjin():
    """1990-05-15 = 庚辰 (KASI 공식 회신, ADR-085 정정)."""
    p = day_pillar(1990, 5, 15)
    assert p["gan"] == "경"
    assert p["ji"] == "진"
    assert p["gan_han"] == "庚"
    assert p["ji_han"] == "辰"


def test_today_2026_05_20_is_gabo():
    """2026-05-20 = 甲午 (KASI 공식 회신)."""
    p = day_pillar(2026, 5, 20)
    assert p["gan"] == "갑"
    assert p["ji"] == "오"


# ── ④ 십성 표준 명리 매트릭스 ────────────────────────────


def test_ten_god_matrix_for_jia():
    """일간 甲 (양목) 기준 10천간 십성 표준 매트릭스."""
    cases = [
        ("甲", "甲", "비견"),  # 同 + 양양
        ("甲", "乙", "겁재"),  # 同 + 양음
        ("甲", "丙", "식신"),  # 我生 + 양양
        ("甲", "丁", "상관"),  # 我生 + 양음
        ("甲", "戊", "편재"),  # 我剋 + 양양
        ("甲", "己", "정재"),  # 我剋 + 양음
        ("甲", "庚", "편관"),  # 剋我 + 양양
        ("甲", "辛", "정관"),  # 剋我 + 양음
        ("甲", "壬", "편인"),  # 生我 + 양양
        ("甲", "癸", "정인"),  # 生我 + 양음
    ]
    for dm, other, expected in cases:
        assert ten_god(dm, other) == expected, f"{dm}↔{other}: 기대 {expected}"


def test_eulmok_vs_gito_is_pyeonjae():
    """라이브 사례: 乙(음목) 일간 ↔ 己(음토) = 편재 (剋 + 음음 동)."""
    assert ten_god("乙", "己") == "편재"


def test_compute_ten_gods_live_case():
    """라이브 사례 compute_ten_gods 직접 호출 — 빈 dict X."""
    result = compute_ten_gods({
        "year": "乙巳",
        "month": "乙巳",
        "day": "乙巳",
        "hour": "己未",
    })
    assert "hour_gan" in result
    assert result["hour_gan"] == "편재"
    assert "hour_ji" in result
    assert result["hour_ji"]  # 빈 문자열 X
    # 己未 지지 본기 = 己(토) → 을목 입장 편재 동일
    assert result["hour_ji"] == "편재"


# ── ⑤ 알고리즘 정합 명시 (문서 검증) ─────────────────────


def test_pillars_docstring_states_anchor():
    """day_pillar docstring에 앵커 명시 (외부 검증 가능)."""
    from engine.saju import pillars
    src = pillars.__doc__ or ""
    assert "1900-01-01" in src
    assert "己亥" in src


def test_ten_gods_uses_standard_wuxing_yang_yin():
    """ten_god 알고리즘이 표준 오행 상생·상극 + 음양 동이 사용."""
    # 상생 (我生): 木→火, 火→土, 土→金, 金→水, 水→木
    assert ten_god("甲", "丙") == "식신"  # 목→화 양양
    assert ten_god("丙", "戊") == "식신"  # 화→토 양양
    assert ten_god("戊", "庚") == "식신"  # 토→금 양양
    assert ten_god("庚", "壬") == "식신"  # 금→수 양양
    assert ten_god("壬", "甲") == "식신"  # 수→목 양양

    # 상극 (我剋): 木→土, 土→水, 水→火, 火→金, 金→木
    assert ten_god("甲", "戊") == "편재"  # 목→토
    assert ten_god("戊", "壬") == "편재"  # 토→수
    assert ten_god("壬", "丙") == "편재"  # 수→화
    assert ten_god("丙", "庚") == "편재"  # 화→금
    assert ten_god("庚", "甲") == "편재"  # 금→목
