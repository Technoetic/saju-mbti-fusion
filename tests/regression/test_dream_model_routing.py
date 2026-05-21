"""ADR-098 회귀 — dream char_key 모델 분리 라우팅.

A/B 테스트 인프라 — DREAM_MODEL 환경변수로 dream만 Flash 업그레이드 가능.
다른 char_key (saju·name·face·palm·star·hwapae)는 BIZROUTER_MODEL 유지.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SERVER_PY = ROOT / "web" / "server.py"


def _src() -> str:
    return SERVER_PY.read_text(encoding="utf-8")


def test_adr_098_marker_present():
    """ADR-098 주석 명시."""
    src = _src()
    assert "ADR-098" in src


def test_dream_model_env_var():
    """DREAM_MODEL 환경변수 사용."""
    src = _src()
    assert 'os.environ.get("DREAM_MODEL"' in src


def test_bizrouter_model_default_preserved():
    """BIZROUTER_MODEL 기본값 유지 (다른 char_key)."""
    src = _src()
    assert 'os.environ.get("BIZROUTER_MODEL", "google/gemini-2.5-flash-lite")' in src


def test_dream_routing_conditional():
    """char_key == 'dream' 조건부 분기."""
    src = _src()
    assert 'if char_key == "dream":' in src
    assert "model = os.environ.get(\"DREAM_MODEL\", default_model)" in src


def test_non_dream_uses_default():
    """dream 외 char_key는 default_model 사용."""
    src = _src()
    # else 분기 또는 default fallback
    assert "model = default_model" in src


def test_ai_generation_meta_uses_actual_model():
    """ai_generation 메타에 실제 사용된 모델 반영."""
    src = _src()
    assert "build_ai_generation_meta(model_label=model)" in src


def test_default_model_var_name():
    """변수명 default_model 사용 (혼동 방지)."""
    src = _src()
    assert "default_model = os.environ.get(\"BIZROUTER_MODEL\"" in src


def test_no_hardcoded_gemini_flash():
    """dream 분기에 하드코딩된 'gemini-2.5-flash' 부재 — 환경변수만."""
    src = _src()
    # 직접 'gemini-2.5-flash'를 char_key='dream' 분기에 하드코딩하지 않음
    # 환경변수만 사용
    lines = src.split("\n")
    for i, line in enumerate(lines):
        if 'if char_key == "dream":' in line:
            # 다음 5줄 검사
            for j in range(i+1, min(i+5, len(lines))):
                stripped = lines[j].strip()
                if not stripped or stripped in ("else:", "}", "{") or stripped.startswith("#"):
                    continue
                # 'gemini-2.5-flash' 하드코딩 차단 — 환경변수만 사용
                assert "google/gemini-2.5-flash" not in stripped or "environ" in stripped, f"line {j} hardcoded: {stripped}"
            break
