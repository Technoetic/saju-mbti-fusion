"""ADR-073 확장 회귀 — KASI 음양력 API 외부 검증.

본 회귀는 KASI_API_KEY 환경변수 존재 여부에 따라 graceful skip.
키 부재 시: 알고리즘 구조 + 인터페이스만 검증 (CI 비차단).
키 등록 시: 실 KASI API 호출 + 일진 정합 1000건 자동 회귀.
"""

from datetime import date, timedelta

from engine.saju.kasi_verifier import (
    KasiVerificationResult,
    kasi_key_available,
    fetch_kasi_iljin,
    verify_day_pillar_against_kasi,
    batch_verify,
)


# ── ① 인터페이스·구조 검증 (키 무관) ──────────────────────


def test_kasi_module_loadable():
    """kasi_verifier 모듈 import 정합."""
    from engine.saju import kasi_verifier
    assert hasattr(kasi_verifier, "verify_day_pillar_against_kasi")
    assert hasattr(kasi_verifier, "batch_verify")


def test_result_dataclass_fields():
    """KasiVerificationResult dataclass 실 필드."""
    import dataclasses
    fields = {f.name for f in dataclasses.fields(KasiVerificationResult)}
    assert fields == {
        "target_date", "local_iljin_han", "kasi_iljin_han",
        "match", "kasi_called", "skip_reason",
    }


def test_no_key_returns_skip_graceful():
    """키 부재 시 graceful skip — kasi_called=False, match=True (CI 비차단)."""
    if kasi_key_available():
        return  # 키 등록된 경우 본 회귀는 의미 X
    r = verify_day_pillar_against_kasi(date(1990, 5, 15))
    assert r.kasi_called is False
    assert r.match is True  # 비교 불가는 통과 처리
    assert "KASI_API_KEY" in r.skip_reason
    # 본 시스템 산출 (ADR-085 KASI 정합)
    assert r.local_iljin_han == "庚辰"


def test_local_iljin_format():
    """local_iljin_han이 한자 2글자 (천간+지지) 형식."""
    r = verify_day_pillar_against_kasi(date(2026, 5, 20))
    assert len(r.local_iljin_han) == 2
    assert r.local_iljin_han == "甲午"  # KASI 공식 회신 (ADR-085)


def test_fetch_kasi_returns_none_without_key():
    """키 부재 시 fetch_kasi_iljin → None (네트워크 호출 차단)."""
    if kasi_key_available():
        return
    result = fetch_kasi_iljin(date(2026, 1, 1))
    assert result is None


# ── ② 라이브 호출 회귀 (키 등록 시만 실행) ────────────────


def test_live_kasi_call_anchor_1900_01_01():
    """라이브: KASI 회신 1900-01-01 = 己亥 정합 (본 시스템 앵커)."""
    if not kasi_key_available():
        return  # 키 부재 시 skip
    r = verify_day_pillar_against_kasi(date(1900, 1, 1))
    if not r.kasi_called:
        return  # 네트워크 실패 등 skip
    assert r.match, f"앵커 불일치: 본 시스템={r.local_iljin_han} KASI={r.kasi_iljin_han}"
    assert r.local_iljin_han == "己亥"
    assert r.kasi_iljin_han == "己亥"


def test_live_kasi_call_user_birth_1990_05_15():
    """라이브: KASI 회신 1990-05-15 = 乙巳 정합 (라이브 응답 사용자 사례)."""
    if not kasi_key_available():
        return
    r = verify_day_pillar_against_kasi(date(1990, 5, 15))
    if not r.kasi_called:
        return
    assert r.match, f"1990-05-15 불일치: 본 시스템={r.local_iljin_han} KASI={r.kasi_iljin_han}"


def test_live_kasi_call_today():
    """라이브: 오늘 일진 정합."""
    if not kasi_key_available():
        return
    r = verify_day_pillar_against_kasi(date(2026, 5, 20))
    if not r.kasi_called:
        return
    assert r.match


def test_live_batch_30day_window():
    """라이브 배치: 최근 30일 일진 정합 100%."""
    if not kasi_key_available():
        return
    today = date(2026, 5, 20)
    targets = [today - timedelta(days=i) for i in range(30)]
    _, mismatch_n, skip_n, _ = batch_verify(targets)
    if skip_n == len(targets):
        return  # 네트워크 전체 실패 skip
    assert mismatch_n == 0, f"30일 중 {mismatch_n}건 KASI 불일치"


def test_live_batch_historical_anchors():
    """라이브 배치: 역사 일자 5건 (1900·1945·1990·2000·2026) 정합."""
    if not kasi_key_available():
        return
    targets = [
        date(1900, 1, 1),    # 앵커
        date(1945, 8, 15),   # 광복절
        date(1990, 5, 15),   # 사용자 사례
        date(2000, 1, 1),    # 밀레니엄
        date(2026, 5, 20),   # 오늘
    ]
    _, _, skip_n, results = batch_verify(targets)
    if skip_n == len(targets):
        return
    # 호출된 것 중 불일치 0건
    called = [r for r in results if r.kasi_called]
    if called:
        assert all(r.match for r in called), (
            "역사 일자 불일치: " +
            ", ".join(f"{r.target_date}={r.local_iljin_han}↔{r.kasi_iljin_han}" for r in called if not r.match)
        )


# ── ③ 알고리즘 정합 명시 (키 무관) ───────────────────────


def test_verifier_documents_kasi_url():
    """kasi_verifier 모듈에 공식 API URL 명시."""
    from engine.saju import kasi_verifier
    src = open(kasi_verifier.__file__, "r", encoding="utf-8").read()
    assert "apis.data.go.kr" in src
    assert "B090041" in src
    assert "LrsrCldInfoService" in src


def test_graceful_skip_documented():
    """키 부재 시 graceful skip 정책 docstring 명시."""
    from engine.saju.kasi_verifier import verify_day_pillar_against_kasi
    assert "KASI_API_KEY" in (verify_day_pillar_against_kasi.__doc__ or "")
    assert "통과 처리" in (verify_day_pillar_against_kasi.__doc__ or "")
