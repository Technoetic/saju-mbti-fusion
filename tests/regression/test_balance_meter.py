"""ADR-093 회귀 — 궁합 양면 해석 균형도 객관 측정 모듈."""

from engine.saju.balance_meter import (
    BalanceResult,
    measure_balance,
    measure_batch,
)


def test_measure_balance_returns_dataclass():
    """measure_balance 반환이 BalanceResult."""
    r = measure_balance("강점이 있을 수 있고 약점도 있을 수 있습니다.")
    assert isinstance(r, BalanceResult)
    assert hasattr(r, "positive_count")
    assert hasattr(r, "negative_count")
    assert hasattr(r, "balance_pct")
    assert hasattr(r, "verdict")


def test_perfect_balance():
    """긍정·부정 같은 횟수 → balance 100%."""
    text = "조화 갈등 조화 갈등 조화 갈등"
    r = measure_balance(text)
    assert r.positive_count == 3
    assert r.negative_count == 3
    assert r.balance_pct == 100.0
    assert r.verdict == "GOOD"


def test_pure_positive_warn():
    """긍정만 있음 → WARN_IMPLICIT_BIAS."""
    text = "조화 보완 강점 활력 성장 기회 발전"
    r = measure_balance(text)
    assert r.positive_count > 0
    assert r.negative_count == 0
    assert r.balance_pct == 0.0
    assert r.verdict == "WARN_IMPLICIT_BIAS"


def test_pure_negative_warn():
    """부정만 있음 → WARN_IMPLICIT_BIAS."""
    text = "갈등 마찰 약점 어려움 충돌 단점"
    r = measure_balance(text)
    assert r.negative_count > 0
    assert r.positive_count == 0
    assert r.balance_pct == 0.0
    assert r.verdict == "WARN_IMPLICIT_BIAS"


def test_empty_text():
    """빈 텍스트 → EMPTY."""
    r = measure_balance("")
    assert r.total_signal == 0
    assert r.verdict == "EMPTY"


def test_40_pass_threshold():
    """40% 이상 → PASS verdict."""
    # 긍정 5 + 부정 2 → 2/5 = 40%
    text = "조화 조화 보완 강점 활력 갈등 약점"
    r = measure_balance(text)
    assert r.balance_pct >= 40.0
    assert r.verdict in ("PASS", "GOOD")


def test_below_40_warn():
    """40% 미만 → WARN_IMPLICIT_BIAS."""
    # 긍정 10 + 부정 2 → 2/10 = 20%
    text = "조화 조화 보완 강점 활력 성장 기회 발전 안정 신뢰 갈등 약점"
    r = measure_balance(text)
    assert r.balance_pct < 40.0
    assert r.verdict == "WARN_IMPLICIT_BIAS"


def test_60_good_threshold():
    """60% 이상 → GOOD."""
    # 긍정 5 + 부정 3 → 3/5 = 60%
    text = "조화 보완 강점 활력 성장 갈등 약점 어려움"
    r = measure_balance(text)
    assert r.balance_pct >= 60.0
    assert r.verdict == "GOOD"


def test_measure_batch_average():
    """다회 응답 평균."""
    texts = [
        "조화 갈등",  # 100%
        "조화 조화 갈등",  # 50%
        "조화 갈등 갈등",  # 50%
    ]
    batch = measure_batch(texts)
    assert batch["count"] == 3
    assert batch["avg_balance_pct"] == round((100+50+50)/3, 1)
    assert batch["verdict"] in ("PASS", "GOOD")


def test_measure_batch_empty():
    """빈 리스트 → EMPTY verdict."""
    batch = measure_batch([])
    assert batch["count"] == 0
    assert batch["verdict"] == "EMPTY"


def test_measure_batch_warn_when_avg_below_40():
    """평균 40% 미만 → WARN."""
    texts = [
        "조화 조화 조화 조화 조화 갈등",  # 20%
        "보완 보완 보완 보완 약점",  # 25%
    ]
    batch = measure_batch(texts)
    assert batch["avg_balance_pct"] < 40.0
    assert batch["verdict"] == "WARN_IMPLICIT_BIAS"


def test_real_couple_response_pattern():
    """라이브 사례 (직전 평가 ADR-092 후) Couple mode."""
    # 직전 평가에서 측정된 패턴 시뮬레이션 (긍정 21, 부정 6 → 29%)
    text = (
        "조화 보완 강점 활력 성장 기회 발전 안정 신뢰 지지 도움 원활 긍정 긍정적 "
        "수 있 수 있 수 있 수 있 수 있 수 있 "
        "갈등 약점 어려움 주의 신중 마찰"
    )
    r = measure_balance(text)
    # 본 회귀는 측정 알고리즘만 검증 — 실 라이브 응답이 PASS인지는 라이브 회귀
    assert r.positive_count > r.negative_count
    assert r.verdict in ("PASS", "WARN_IMPLICIT_BIAS")


def test_min_max_in_batch():
    """배치 min·max balance 정합."""
    texts = ["조화 갈등", "조화 조화 갈등"]  # 100%, 50%
    batch = measure_batch(texts)
    assert batch["min_balance_pct"] == 50.0
    assert batch["max_balance_pct"] == 100.0
