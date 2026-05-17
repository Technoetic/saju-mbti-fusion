"""llm_output_sampler 단위 테스트.

ADR-005 Supplement 2~7 운영 모니터링 의무 이행 검증.
사용자 영향 0 (백그라운드 로깅) — sampling_rate 파라미터로 강제 제어.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_sampling_rate_1_0_creates_file(tmp_path, monkeypatch):
    """sampling_rate=1.0 (또는 _force=True) → 파일 반드시 생성."""
    from engine.safety import llm_output_sampler as m
    monkeypatch.setattr(m, "_SAMPLE_DIR", tmp_path)

    m.sample_llm_output("face_reading", "허허, 테스트 텍스트로세.", _force=True)

    from datetime import date
    today = str(date.today())
    out_file = tmp_path / f"{today}.jsonl"
    assert out_file.exists(), "강제 샘플링 시 JSONL 파일이 생성되어야 함"
    lines = out_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["domain"] == "face_reading"
    assert entry["text_len"] == len("허허, 테스트 텍스트로세.")
    assert "fate_vocab_hits" in entry


def test_sampling_rate_0_0_no_file(tmp_path, monkeypatch):
    """sampling_rate=0.0 → 파일 미생성."""
    from engine.safety import llm_output_sampler as m
    monkeypatch.setattr(m, "_SAMPLE_DIR", tmp_path)

    m.sample_llm_output("face_reading", "허허, 테스트.", sampling_rate=0.0)

    from datetime import date
    today = str(date.today())
    out_file = tmp_path / f"{today}.jsonl"
    assert not out_file.exists(), "sampling_rate=0.0 이면 파일이 생성되지 않아야 함"


def test_empty_text_no_file(tmp_path, monkeypatch):
    """빈 텍스트 → 파일 미생성 (예외 없음)."""
    from engine.safety import llm_output_sampler as m
    monkeypatch.setattr(m, "_SAMPLE_DIR", tmp_path)

    m.sample_llm_output("face_reading", "", _force=True)
    m.sample_llm_output("face_reading", None, _force=True)  # type: ignore

    from datetime import date
    today = str(date.today())
    out_file = tmp_path / f"{today}.jsonl"
    assert not out_file.exists(), "빈 텍스트는 저장 안 됨"


def test_fate_vocab_detected_increments_counter(tmp_path, monkeypatch):
    """운명 어휘 발견 시 fate_counter.json에 누적."""
    from engine.safety import llm_output_sampler as m
    monkeypatch.setattr(m, "_SAMPLE_DIR", tmp_path)

    fate_text = "말년의 재물복이 있겠도다. 직장운이 밝으신 분이로구먼."
    m.sample_llm_output("face_reading", fate_text, _force=True)

    counter_path = tmp_path / "fate_counter.json"
    assert counter_path.exists(), "운명 어휘 발견 시 fate_counter.json 생성"
    data = json.loads(counter_path.read_text(encoding="utf-8"))
    assert data["total_fate_hits"] > 0


def test_no_fate_vocab_no_counter(tmp_path, monkeypatch):
    """운명 어휘 없으면 fate_counter.json 미생성."""
    from engine.safety import llm_output_sampler as m
    monkeypatch.setattr(m, "_SAMPLE_DIR", tmp_path)

    clean_text = "허허, 그대의 이마가 넓고 눈빛이 또렷하구먼."
    m.sample_llm_output("face_reading", clean_text, _force=True)

    counter_path = tmp_path / "fate_counter.json"
    assert not counter_path.exists() or (
        json.loads(counter_path.read_text())["total_fate_hits"] == 0
    )


def test_multiple_samples_appended(tmp_path, monkeypatch):
    """여러 번 호출 → 같은 날짜 파일에 append."""
    from engine.safety import llm_output_sampler as m
    monkeypatch.setattr(m, "_SAMPLE_DIR", tmp_path)

    for i in range(3):
        m.sample_llm_output("face_reading", f"텍스트 {i}", _force=True)

    from datetime import date
    today = str(date.today())
    out_file = tmp_path / f"{today}.jsonl"
    lines = out_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3


def test_exception_silent(tmp_path, monkeypatch):
    """디렉토리 오류 시 예외 없음 (silent)."""
    from engine.safety import llm_output_sampler as m
    # 존재하지 않는 경로 + mkdir 실패 시뮬레이션
    monkeypatch.setattr(m, "_SAMPLE_DIR", Path("/nonexistent/path/that/cannot/exist"))

    # 예외가 발생하면 안 됨
    m.sample_llm_output("face_reading", "테스트", _force=True)
