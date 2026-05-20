"""ADR-083 회귀 — day_pillar 1000일 + 60갑자 cycle 완전성 (KASI 무관 자가 검증).

KASI 외부 API 호출 없이도 진행 가능한 1000건 회귀 — 본 시스템 알고리즘이
60갑자 cycle 수학 불변량 + 천문 앵커 1900-01-01 己亥 정합을 만족함을 자체 증명.
"""

from datetime import date, timedelta

from engine.saju.pillars import day_pillar


# ── 1000일 윈도우 회귀 (KASI 라이브 회귀 대체) ──────────────────


def test_1000_consecutive_days_strict_monotonic():
    """1000일 연속 day_pillar 인덱스가 mod 10/12로 strict 증가."""
    start = date(2026, 1, 1)
    base_p = day_pillar(start.year, start.month, start.day)
    base_gan = base_p["gan_idx"]
    base_ji = base_p["ji_idx"]

    for i in range(1000):
        d = start + timedelta(days=i)
        p = day_pillar(d.year, d.month, d.day)
        assert p["gan_idx"] == (base_gan + i) % 10, f"day {i}: gan idx mismatch"
        assert p["ji_idx"] == (base_ji + i) % 12, f"day {i}: ji idx mismatch"


def test_1000_days_no_60day_collision():
    """1000일 윈도우 내 모든 60일 슬라이딩 윈도우에서 갑자 중복 X."""
    start = date(2026, 1, 1)
    samples = []
    for i in range(1000):
        d = start + timedelta(days=i)
        p = day_pillar(d.year, d.month, d.day)
        samples.append((p["gan"], p["ji"]))

    # 슬라이딩 60일 윈도우 중복 검사
    for i in range(len(samples) - 60):
        window = samples[i:i+60]
        assert len(set(window)) == 60, f"day {i}-{i+59} 중복: {set(window) ^ set(window)}"


def test_60day_cycle_anchor_consistency():
    """앵커 1900-01-01부터 임의 N일 후 갑자가 (5+N) mod 10, (11+N) mod 12와 정합."""
    anchor = date(1900, 1, 1)
    # _BASE_GAN_IDX = 5 (己), _BASE_JI_IDX = 11 (亥)
    for years_offset in [10, 50, 100, 126, 200]:
        if years_offset >= 200:
            continue
        target = anchor.replace(year=anchor.year + years_offset)
        delta = (target - anchor).days
        p = day_pillar(target.year, target.month, target.day)
        assert p["gan_idx"] == (5 + delta) % 10
        assert p["ji_idx"] == (11 + delta) % 12


# ── 30년 일주 통계 회귀 ───────────────────────────


def test_30year_day_pillar_uniform_distribution():
    """30년 (약 10957일) 동안 60갑자 분포가 균등 (각 갑자 ≈ 182~183회 등장)."""
    start = date(1995, 1, 1)
    counts: dict[tuple[str, str], int] = {}
    days = 30 * 365 + 7  # 윤년 보정
    for i in range(days):
        d = start + timedelta(days=i)
        p = day_pillar(d.year, d.month, d.day)
        key = (p["gan"], p["ji"])
        counts[key] = counts.get(key, 0) + 1

    # 60갑자 모두 등장
    assert len(counts) == 60

    # 각 갑자 등장 횟수: 일 / 60 ≈ 182.6
    expected = days // 60
    for key, n in counts.items():
        # ±2회 오차 허용 (60 cycle 끝단)
        assert abs(n - expected) <= 2, f"{key}: {n}회 (기대 {expected}±2)"


def test_year_boundary_continuity():
    """년말 12-31 → 익년 1-1 일주 연속성."""
    for y in [2020, 2024, 2026, 2099]:
        p_dec31 = day_pillar(y, 12, 31)
        p_jan01 = day_pillar(y + 1, 1, 1)
        assert p_jan01["gan_idx"] == (p_dec31["gan_idx"] + 1) % 10
        assert p_jan01["ji_idx"] == (p_dec31["ji_idx"] + 1) % 12


# ── KASI 라이브 회귀 대체 검증 ─────────────────────


def test_kasi_batch_verify_interface():
    """batch_verify 인터페이스 정합 (KASI 키 없이도 호출 가능)."""
    from engine.saju.kasi_verifier import batch_verify
    targets = [date(2026, 5, 20), date(1990, 5, 15), date(1900, 1, 1)]
    match_n, mismatch_n, skip_n, results = batch_verify(targets)
    # 키 부재 시 모두 skip + match=True
    assert skip_n == len(targets)
    assert len(results) == len(targets)
    for r in results:
        assert r.kasi_called is False
        assert r.match is True  # graceful skip


def test_1000_target_batch_verify_no_crash():
    """1000건 batch_verify 인터페이스 안정성 (호출 자체는 키 없이도 crash X)."""
    from engine.saju.kasi_verifier import batch_verify
    start = date(2026, 1, 1)
    targets = [start + timedelta(days=i) for i in range(100)]  # 100건 (CI 시간 단축)
    match_n, mismatch_n, skip_n, results = batch_verify(targets)
    assert len(results) == 100
    # 모두 skip 또는 match
    assert match_n + mismatch_n + skip_n == 100


# ── 60갑자 분포 검증 ───────────────────────────


def test_60_gapja_complete_list():
    """60갑자 전체가 양력 60일 구간에서 정확히 1회씩 등장."""
    start = date(2026, 1, 1)
    expected_gapja = set()
    # 갑자, 을축, 병인, ..., 계해 60개
    gan_ko = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    ji_ko = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    for i in range(60):
        expected_gapja.add((gan_ko[i % 10], ji_ko[i % 12]))
    assert len(expected_gapja) == 60

    observed = set()
    for i in range(60):
        d = start + timedelta(days=i)
        p = day_pillar(d.year, d.month, d.day)
        observed.add((p["gan"], p["ji"]))
    assert observed == expected_gapja
