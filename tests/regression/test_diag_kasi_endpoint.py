"""ADR-084 회귀 — /api/diag/kasi-verify endpoint.

라이브 KASI 1000건 호출 가능 endpoint. 키 부재 시 graceful skip + 통계만 반환.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SERVER_PY = ROOT / "web" / "server.py"


def _src() -> str:
    return SERVER_PY.read_text(encoding="utf-8")


def test_endpoint_registered():
    """라우터 등록 정합."""
    src = _src()
    assert 'self.app.get("/api/diag/kasi-verify")' in src
    assert "get_diag_kasi_verify" in src


def test_method_signature():
    """count + start 파라미터."""
    src = _src()
    assert "async def get_diag_kasi_verify" in src
    assert "count: int = 100" in src
    assert "start: str | None" in src


def test_returns_statistics_only():
    """반환 dict가 통계만 (개별 키 노출 X)."""
    src = _src()
    assert '"kasi_key_available"' in src
    assert '"kasi_called"' in src
    assert '"match"' in src
    assert '"mismatch"' in src
    assert '"skip"' in src
    assert '"match_rate_pct"' in src
    # 키 텍스트 반환 차단
    assert "ServiceKey" not in src.split("get_diag_kasi_verify")[1].split("post_error_log")[0]


def test_count_clamped_to_1000():
    """count 최대 1000 제한 (DDoS 방지)."""
    src = _src()
    assert "min(int(count), 1000)" in src


def test_uses_batch_verify():
    """batch_verify 호출 (단건 호출 X)."""
    src = _src()
    assert "batch_verify(targets)" in src


def test_mismatched_samples_limited_to_10():
    """불일치 샘플 10건까지만 반환 (개별 키·일진 텍스트 노출 최소화)."""
    src = _src()
    assert "[:10]" in src.split("get_diag_kasi_verify")[1].split("post_error_log")[0]


def test_local_endpoint_returns_200():
    """로컬 호출 시 200 + graceful skip (키 부재)."""
    from web.server import app
    from starlette.testclient import TestClient
    client = TestClient(app)
    resp = client.get("/api/diag/kasi-verify?count=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count_requested"] == 5
    # 키 부재 시 모두 skip
    if not data["kasi_key_available"]:
        assert data["skip"] == 5
        assert data["match"] == 0
        assert data["mismatch"] == 0
        assert data["match_rate_pct"] is None


def test_endpoint_handles_invalid_start_date():
    """잘못된 start 일자 → 오늘로 fallback."""
    from web.server import app
    from starlette.testclient import TestClient
    client = TestClient(app)
    resp = client.get("/api/diag/kasi-verify?count=3&start=invalid-date")
    assert resp.status_code == 200


def test_endpoint_count_exceeds_1000_clamped():
    """count > 1000 입력 시 1000으로 clamp."""
    from web.server import app
    from starlette.testclient import TestClient
    client = TestClient(app)
    resp = client.get("/api/diag/kasi-verify?count=5000")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count_requested"] == 1000
