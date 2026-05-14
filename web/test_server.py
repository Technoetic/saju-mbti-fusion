"""웹 백엔드 단위 테스트 (FastAPI TestClient + 비동기 직접 호출)."""

import sys
from pathlib import Path

import pytest

# 프로젝트 루트를 sys.path 에 추가
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


@pytest.fixture
def client():
    from server import app
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
def server_instance():
    """클래스 직접 인스턴스 (정적 마운트 없이)."""
    from server import PersonalityAPIServer
    return PersonalityAPIServer(mount_static=False)


# === 동기 endpoint (TestClient) ===

def test_saju_endpoint(client):
    r = client.post("/api/saju", json={
        "dt_local": "1990-05-15T14:30",
        "tz": "Asia/Seoul",
        "longitude": 126.978,
        "latitude": 37.5665,
        "gender": "M",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["year"] == "庚午"
    assert data["day"] == "庚辰"


def test_tarot_endpoint(client):
    r = client.post("/api/tarot", json={
        "question": "test",
        "spread": "three",
        "seed": 42,
    })
    assert r.status_code == 200
    data = r.json()
    assert len(data["cards"]) == 3


def test_iching_endpoint(client):
    r = client.post("/api/iching", json={
        "question": "test",
        "seed": 42,
    })
    assert r.status_code == 200
    data = r.json()
    assert "primary" in data["result"]


def test_health_endpoint(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_profile_endpoint(client):
    r = client.get("/api/profile/ESTJ")
    assert r.status_code == 200
    data = r.json()
    assert "strengths" in data


def test_profile_unknown_type(client):
    r = client.get("/api/profile/XXXX")
    assert r.status_code == 404


def test_assess_all_endpoint_saju_oracle(client):
    """9 시스템 통합 — saju + tarot + iching (LLM 없이)."""
    r = client.post("/api/assess_all", json={
        "saju": {
            "dt_local": "1990-05-15T14:30",
            "gender": "M",
        },
        "oracle_question": "today",
        "oracle_seed": 42,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["saju"] is not None
    assert data["tarot"] is not None
    assert data["iching"] is not None
    assert data["saju"]["year"] == "庚午"


# === 비동기 직접 호출 (Engine 우회 검증) ===

@pytest.mark.asyncio
async def test_post_saju_async_direct(server_instance):
    from server import SajuRequest
    result = await server_instance.post_saju(SajuRequest(
        dt_local="1990-05-15T14:30",
        gender="M",
    ))
    assert result["year"] == "庚午"


@pytest.mark.asyncio
async def test_post_tarot_async_direct(server_instance):
    from server import TarotRequest
    result = await server_instance.post_tarot(TarotRequest(
        question="t",
        seed=42,
    ))
    assert len(result["cards"]) == 3


@pytest.mark.asyncio
async def test_post_iching_async_direct(server_instance):
    from server import IChingRequest
    result = await server_instance.post_iching(IChingRequest(
        question="t",
        seed=42,
    ))
    assert "primary" in result["result"]


@pytest.mark.asyncio
async def test_get_health_async_direct(server_instance):
    result = await server_instance.get_health()
    assert result["status"] == "ok"


def test_server_instance_has_engine(server_instance):
    from engine import PersonalityEngine
    assert isinstance(server_instance.engine, PersonalityEngine)
