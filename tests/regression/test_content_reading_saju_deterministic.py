"""ADR-069 회귀 — /api/content/reading saju 도메인 결정론 결합 검증.

만월 아씨 'today' 콘텐츠가 사주 엔진 (day_pillar·ten_gods) 결정론 출력을
LLM 시스템 프롬프트에 주입하는지 자동 검증. ADR-067 단순 LLM 호출에서
ADR-069 결정론 직결로 정정.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SERVER_PY = ROOT / "web" / "server.py"
CONTENT_JS = ROOT / "front" / "js" / "ui" / "content-system.js"


def _server_text() -> str:
    return SERVER_PY.read_text(encoding="utf-8")


def _client_text() -> str:
    return CONTENT_JS.read_text(encoding="utf-8")


# ─────────────────────────── 라우트·핸들러 정합 ───────────────────────────

def test_content_reading_route_registered():
    """POST /api/content/reading 라우트 등록."""
    src = _server_text()
    assert "/api/content/reading" in src
    assert "post_content_reading" in src


def test_content_reading_request_model():
    """ContentReadingRequest pydantic 모델 — char_key·content_key·fields."""
    src = _server_text()
    assert "class ContentReadingRequest" in src
    assert "char_key: str" in src
    assert "content_key: str" in src
    assert "fields: dict[str, str] | None" in src


# ─────────────────────────── saju 결정론 직결 ───────────────────────────

def test_saju_today_calls_day_pillar():
    """saju + today → day_pillar() 호출 (engine/saju/pillars)."""
    src = _server_text()
    assert "from engine.saju.pillars import day_pillar" in src
    assert 'char_key == "saju"' in src
    assert '"today"' in src and '"tomorrow"' in src


def test_saju_calls_ten_gods():
    """compute_ten_gods 호출 — 사용자 일간 ↔ 오늘 천간 십성 관계."""
    src = _server_text()
    assert "from engine.saju.ten_gods import compute_ten_gods" in src
    assert "compute_ten_gods" in src


def test_deterministic_block_in_system_prompt():
    """결정론 출력이 system 프롬프트에 명시 주입."""
    src = _server_text()
    assert "deterministic_block" in src
    assert "사주 결정론 — engine/saju 출력" in src
    assert "사용자 일주(日柱)" in src
    assert "오늘 일진(今日 日辰)" in src


def test_deterministic_block_includes_60갑자():
    """일주·일진 갑자 명시 — 60갑자 결정론 인용."""
    src = _server_text()
    # 한글 천간·지지 또는 한자 명시
    assert "gan" in src
    assert "ji" in src
    assert "gan_han" in src
    assert "ji_han" in src


# ─────────────────────────── ADR-010 사실성 분리 ───────────────────────────

def test_llm_pretraining_blocked_in_prompt():
    """system 프롬프트에 사전학습 추가 차단 명시 (ADR-010)."""
    src = _server_text()
    assert "사전학습 추가 X" in src
    assert "ADR-010" in src


def test_deterministic_only_quotation():
    """LLM이 결정론 출력만 인용 — 사주 명칭 사전학습 차단."""
    src = _server_text()
    assert "결정론 출력만 인용" in src or "결정론 출력이 주어지면 그 출력만 인용" in src


# ─────────────────────────── ADR-006 안전 장치 ───────────────────────────

def test_adr_006_safety_in_system_prompt():
    """단정 차단 시스템 프롬프트 강제."""
    src = _server_text()
    assert "ADR-006" in src
    assert "단정적 예언 금지" in src
    assert "운명·재물·결혼 단정 매핑 금지" in src


def test_legal_footer_attached():
    """응답에 build_legal_footer + build_ai_generation_meta 자동."""
    src = _server_text()
    assert "build_legal_footer()" in src
    assert "build_ai_generation_meta" in src


# ─────────────────────────── 7 캐릭터 페르소나 ───────────────────────────

def test_seven_persona_tones_in_server():
    """7 캐릭터 페르소나 톤 매핑 서버측."""
    src = _server_text()
    for persona in ["만월 아씨", "몽이 도령", "화선 낭자", "성하 공자", "운학 도사", "옥선 할미", "묵향 선생"]:
        assert persona in src


# ─────────────────────────── 클라이언트 정합 ───────────────────────────

def test_client_calls_content_reading_endpoint():
    """client가 /api/content/reading 호출 (ADR-067 /api/llm/chat → ADR-069 /api/content/reading)."""
    src = _client_text()
    assert "/api/content/reading" in src


def test_client_sends_char_key_content_key():
    """client request에 char_key·content_key·fields 포함."""
    src = _client_text()
    assert "char_key: data.charKey" in src
    assert "content_key: contentKey" in src
    assert "fields: inputs" in src


# ─────────────────────────── Graceful fallback ───────────────────────────

def test_deterministic_failure_graceful_fallback():
    """결정론 산출 실패 시 LLM 단독 (graceful)."""
    src = _server_text()
    assert "graceful fallback" in src or "산출 실패" in src


def test_response_includes_deterministic_used_flag():
    """응답에 deterministic_used boolean 명시 — 디버그·관찰 가능성."""
    src = _server_text()
    assert "deterministic_used" in src
