"""ADR-047 E2E 라이브 테스트 — Railway 라이브 API 200 OK 검증.

@pytest.mark.live 마커: CI 외 수동 실행 권고 (외부 의존 + 라이브 사용량).
실행: pytest -m live -v
"""
import json
import urllib.error
import urllib.request

import pytest

LIVE_URL = "https://saju-mbti-fusion-production.up.railway.app"
TIMEOUT = 30


def _get(path):
    req = urllib.request.Request(f"{LIVE_URL}{path}", method="GET")
    return urllib.request.urlopen(req, timeout=TIMEOUT)


def _post_json(path, payload):
    req = urllib.request.Request(
        f"{LIVE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return urllib.request.urlopen(req, timeout=60)


@pytest.mark.live
def test_health():
    """헬스 체크 — /api/health 200."""
    resp = _get("/api/health")
    assert resp.status == 200


@pytest.mark.live
def test_root_html():
    """루트 index.html 200."""
    resp = _get("/")
    assert resp.status == 200
    body = resp.read().decode("utf-8", errors="replace")
    assert "月下夢" in body or "saju" in body.lower()


@pytest.mark.live
def test_static_js_modules():
    """ADR-038·043·044·045 외부 .js 모듈 200."""
    paths = [
        "/js/core/llm-utils.js",
        "/js/core/base-reader.js",
        "/js/core/html-utils.js",
        "/js/core/saju-engine.js",
        "/js/core/name-engine.js",
        "/js/core/saju-ui.js",
        "/js/readers/face-reader.js",
        "/js/readers/palm-reader.js",
        "/js/readers/name-reader.js",
        "/js/readers/dream-reader.js",
        "/js/readers/hwapae-reader.js",
        "/js/readers/face-visualizations.js",
        "/styles/main.css",
    ]
    for p in paths:
        resp = _get(p)
        assert resp.status == 200, f"{p} status: {resp.status}"


@pytest.mark.live
def test_media_paths():
    """ADR-040·041 front/media 경로 200 (한글 → 영문)."""
    paths = [
        "/media/characters/manweol_assi.mp4",
        "/media/characters/mongi_doryeong.mp4",
        "/media/characters/mukhyang_seonsaeng.mp4",
        "/media/characters/okseon_halmi.mp4",
        "/media/characters/unhak_dosa.mp4",
        "/media/characters/hwaseon_nangja.mp4",
        "/media/bg/Moon%20Over%20Han.wav",
        "/media/sounds/tap1.ogg",
    ]
    for p in paths:
        try:
            resp = _get(p)
            assert resp.status == 200, f"{p} status: {resp.status}"
        except urllib.error.HTTPError as e:
            pytest.fail(f"{p} HTTP error: {e.code}")


@pytest.mark.live
def test_name_reading_api():
    """묵향 선생 이름 풀이 — 홍길동 → 응답 200 + text 비어있지 않음."""
    resp = _post_json("/api/name/reading", {"fullname_ko": "홍길동"})
    assert resp.status == 200
    data = json.loads(resp.read().decode("utf-8"))
    assert "text" in data
    assert len(data["text"]) > 50  # 의미 있는 풀이 길이


@pytest.mark.live
def test_dream_interpret_v2_minimal():
    """몽이 도령 꿈해석 — 짧은 입력 응답 200.

    실제 LLM 14 에이전트 호출이라 30~60s 소요.
    """
    payload = {
        "dream_text": "어젯밤 꿈에서 하늘을 날았어요.",
        "user_id": None,
        "profile": {},
        "locale": "ko",
        "enable_llm_agents": False,  # 결정론 분석만 (빠른 응답)
    }
    try:
        resp = _post_json("/api/dream/interpret_v2", payload)
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "text" in data
    except urllib.error.HTTPError as e:
        # LLM rate limit 등 일시 오류는 skip
        if e.code in (429, 503):
            pytest.skip(f"transient LLM error: {e.code}")
        raise
