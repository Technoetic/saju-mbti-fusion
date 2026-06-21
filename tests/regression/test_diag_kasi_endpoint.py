"""ADR-084 회귀 — /api/diag/kasi-verify endpoint.

라이브 KASI 1000건 호출 가능 endpoint. 키 부재 시 graceful skip + 통계만 반환.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SERVER_PY = ROOT / "web" / "server.py"


def _src() -> str:
    # 구조 리팩터링 후 핸들러 본문이 web/handlers/*.py Mixin 으로 이동,
    # 모델(class XxxRequest)이 web/schemas.py 로 이동 → 라우트(server.py)와 합쳐 grep.
    parts = [SERVER_PY.read_text(encoding="utf-8")]
    schemas = ROOT / "web" / "schemas.py"
    if schemas.is_file():
        parts.append(schemas.read_text(encoding="utf-8"))
    hdir = ROOT / "web" / "handlers"
    if hdir.is_dir():
        for p in sorted(hdir.glob("*.py")):
            parts.append(p.read_text(encoding="utf-8"))
    return "\n".join(parts)


def _handler_body_src() -> str:
    # split('get_diag_kasi_verify')[1].split('post_error_log')[0] 슬라이싱은
    # 핸들러 정의 순서(get_diag_kasi_verify → post_error_log)가 보존된 소스가 필요.
    # server.py 라우트 등록부는 두 이름의 등록 순서가 반대라 합친 소스로는 슬라이스가 깨짐.
    # 핸들러 본문은 web/handlers/*.py 에 있으므로 그것만 합쳐 본문 순서를 보존.
    hdir = ROOT / "web" / "handlers"
    parts: list[str] = []
    if hdir.is_dir():
        for p in sorted(hdir.glob("*.py")):
            parts.append(p.read_text(encoding="utf-8"))
    return "\n".join(parts)


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
    # 키 텍스트 반환 차단 — 핸들러 본문(handlers/*.py)에서 정의 순서 보존된 슬라이스로 검사
    body = _handler_body_src()
    assert "ServiceKey" not in body.split("get_diag_kasi_verify")[1].split("post_error_log")[0]


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
    body = _handler_body_src()
    assert "[:10]" in body.split("get_diag_kasi_verify")[1].split("post_error_log")[0]


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
