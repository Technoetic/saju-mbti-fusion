"""Playwright 회귀 테스트 공통 fixture — local HTTP server + browser context."""
import http.server
import socketserver
import threading
import time
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRONT_DIR = REPO_ROOT / "front"
SERVER_PORT = 8790  # 회귀 테스트 전용 포트


class _Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(FRONT_DIR), **kw)

    def log_message(self, format, *args):  # noqa: A002
        pass  # silence


@pytest.fixture(scope="session")
def local_server():
    """세션 1회만 로컬 HTTP 서버 기동 (front/ root)."""
    httpd = socketserver.TCPServer(("127.0.0.1", SERVER_PORT), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)
    yield f"http://127.0.0.1:{SERVER_PORT}"
    httpd.shutdown()


@pytest.fixture
def page(local_server):
    """Playwright page — pageerror·console.error 자동 수집."""
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        pg = ctx.new_page()
        pg.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
        pg.on(
            "console",
            lambda msg: errors.append(f"console.{msg.type}: {msg.text}")
            if msg.type == "error"
            else None,
        )
        pg.goto(f"{local_server}/index.html", wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        pg.errors = errors  # type: ignore[attr-defined]
        yield pg
        browser.close()
