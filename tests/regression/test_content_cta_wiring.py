"""ADR-067 회귀 — 60+ 메뉴 콘텐츠 CTA 백엔드 wire-up 검증.

본 시스템 content-system.js의 60+ 메뉴 콘텐츠 "풀이 받기" 버튼이
무동작 상태였음. ADR-067로 free 콘텐츠는 /api/llm/chat 호출,
premium/season은 결제 안내 유지, tab 위임은 기존 화면 이동.

ADR-006 정합: 운명·재물·결혼 단정 차단 시스템 프롬프트 강제.
ADR-058·059 정합: AI 생성 라벨 + 리터러시 면책 footer 자동 첨부.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CONTENT_SYSTEM_JS = ROOT / "front" / "js" / "ui" / "content-system.js"


def _read_js() -> str:
    return CONTENT_SYSTEM_JS.read_text(encoding="utf-8")


def test_cta_handler_wired():
    """contentCtaBtn 클릭 핸들러 wire-up 확인."""
    js = _read_js()
    assert "#contentCtaBtn" in js
    assert "callContentReading" in js


def test_cta_button_has_data_attributes():
    """CTA 버튼이 data-content-key·data-tier·data-tab 속성 보유."""
    js = _read_js()
    assert 'data-content-key="${item.key}"' in js
    assert 'data-tier="${item.tier' in js
    assert 'data-tab="${item.tab}"' in js


def test_tab_delegation_path():
    """tab 위임: 기존 정통 화면으로 이동 (만월·운학·옥선 등)."""
    js = _read_js()
    assert 'data-tab="${tab}"' in js
    assert "tabBtn.click()" in js


def test_premium_season_keep_payment_hint():
    """premium·season은 결제 안내 유지 (사업 결정 영역)."""
    js = _read_js()
    assert "tier === 'premium' || tier === 'season'" in js


def test_free_tier_calls_llm_chat():
    """free 콘텐츠는 /api/llm/chat 호출."""
    js = _read_js()
    assert "/api/llm/chat" in js
    assert "callContentReading" in js


def test_persona_tone_map_seven_characters():
    """7 캐릭터 페르소나 톤 매핑 (만월·몽이·화선·성하·운학·옥선·묵향)."""
    js = _read_js()
    for k in ["saju", "dream", "hwapae", "star", "face", "palm", "name"]:
        assert f"{k}:" in js
    for persona in ["만월 아씨", "몽이 도령", "화선 낭자", "성하 공자", "운학 도사", "옥선 할미", "묵향 선생"]:
        assert persona in js


def test_adr_006_safety_in_system_prompt():
    """★ ADR-006 단정 금지 시스템 프롬프트 강제."""
    js = _read_js()
    assert "단정적 예언 금지" in js
    assert "ADR-006" in js
    assert "운명·재물·결혼 단정 매핑 금지" in js


def test_adr_058_ai_generated_footer():
    """ADR-058 EU AI Act §50 AI 생성 라벨 결과 footer 자동."""
    js = _read_js()
    assert "EU AI Act §50" in js
    assert "AI 시스템에 의해 생성" in js


def test_adr_059_literacy_footer():
    """ADR-059 §52 의료·법률·금융 단독 근거 X 안내."""
    js = _read_js()
    assert "의료·법률·금융" in js
    assert "참고용" in js


def test_result_renders_with_error_handling():
    """LLM 호출 실패 시 사용자 친화 오류 메시지."""
    js = _read_js()
    assert "content-result-error" in js
    assert "잠시 후 다시 시도" in js


def test_loading_state_during_call():
    """LLM 호출 중 로딩 상태 명시."""
    js = _read_js()
    assert "풀이 중" in js
    assert "content-result-loading" in js


def test_button_disabled_during_call():
    """중복 호출 차단 — 버튼 disabled 처리."""
    js = _read_js()
    assert "ctaBtn.disabled = true" in js
    assert "ctaBtn.disabled = false" in js


def test_input_field_collection():
    """item.fields 입력 값 수집 → LLM prompt 결합."""
    js = _read_js()
    assert "(item.fields || [])" in js
    assert "inputs[f.key]" in js


def test_ymd_field_handling():
    """ymd 필드 (생년월일) year_month_day 결합 처리."""
    js = _read_js()
    assert "f.type === 'ymd'" in js
    assert "_year" in js and "_month" in js and "_day" in js
