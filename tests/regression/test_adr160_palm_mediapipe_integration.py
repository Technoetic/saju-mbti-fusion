"""ADR-160 회귀 — 손금 MediaPipe Hand Landmarker 프론트 통합 (Phase 1.5).

ADR-159 face MediaPipe 패턴 정합. ADR-030 score_palm 인터페이스 활용 + 프론트
21 keypoint 추출 통합. LLM Vision 단독 → 결정론 점수 + LLM Vision 융합.

대상:
  · front/js/readers/palm-metrics.js (신규 MediaPipe Hand Landmarker)
  · front/js/readers/palm-reader.js (Phase 1.5 metrics 산출 통합)
  · front/index.html (palm-metrics.js 로드)
  · web/server.py PalmReadingRequest.metrics 필드 + endpoint 결정론 score_palm 호출
"""
from __future__ import annotations

from pathlib import Path


def _server_source() -> str:
    """server.py + web/handlers/*.py + web/schemas.py 합본 텍스트.

    구조 리팩터링(2026-06-21)으로 핸들러 본문이 web/handlers/*.py Mixin 으로,
    요청 모델이 web/schemas.py 로 물리 분리됨. grep 검사가 위치 무관하게
    통과하도록 합쳐서 반환한다.
    """
    root = Path(__file__).resolve().parent.parent.parent
    parts = [(root / "web" / "server.py").read_text(encoding="utf-8")]
    hdir = root / "web" / "handlers"
    if hdir.is_dir():
        for p in sorted(hdir.glob("*.py")):
            parts.append(p.read_text(encoding="utf-8"))
    schemas = root / "web" / "schemas.py"
    if schemas.is_file():
        parts.append(schemas.read_text(encoding="utf-8"))
    return "\n".join(parts)


# ─────────────────────────── front/js/readers/palm-metrics.js ───────────────────────────


class TestPalmMetricsModule:
    """palm-metrics.js 모듈 영속."""

    def test_module_exists(self):
        assert Path("front/js/readers/palm-metrics.js").exists()

    def test_mediapipe_hand_landmarker_imported(self):
        src = Path("front/js/readers/palm-metrics.js").read_text(encoding="utf-8")
        assert "HandLandmarker" in src
        assert "hand_landmarker.task" in src
        assert "@mediapipe/tasks-vision" in src

    def test_21_keypoint_mapping(self):
        src = Path("front/js/readers/palm-metrics.js").read_text(encoding="utf-8")
        # 21 keypoint 모두 (0~20) 명시
        for kp in (0, 1, 4, 5, 8, 12, 16, 20):
            assert f"{kp}:" in src or f"'{kp}'" in src or f"kp{kp}" in src

    def test_thumb_index_middle_ring_pinky(self):
        src = Path("front/js/readers/palm-metrics.js").read_text(encoding="utf-8")
        for finger in ("THUMB", "INDEX", "MIDDLE", "RING", "PINKY"):
            assert finger in src, f"손가락 '{finger}' 누락"

    def test_compute_metrics_function_exported(self):
        src = Path("front/js/readers/palm-metrics.js").read_text(encoding="utf-8")
        assert "computeMetrics" in src
        assert "window.PalmMetrics" in src

    def test_keypoints_dict_format(self):
        """score_palm 인터페이스 정합 — {'kp0': [x,y,z], ...} 형식."""
        src = Path("front/js/readers/palm-metrics.js").read_text(encoding="utf-8")
        assert "_toKeypointsDict" in src
        assert "`kp${i}`" in src


# ─────────────────────────── front/js/readers/palm-reader.js Phase 1.5 ───────────────────────────


class TestPalmReaderPhase15:
    """palm-reader.js Phase 1.5 — MediaPipe metrics 산출 통합 영속."""

    def test_palm_metrics_invocation(self):
        src = Path("front/js/readers/palm-reader.js").read_text(encoding="utf-8")
        assert "window.PalmMetrics" in src
        assert "window.PalmMetrics.computeMetrics" in src

    def test_adr_160_marker(self):
        src = Path("front/js/readers/palm-reader.js").read_text(encoding="utf-8")
        assert "ADR-160" in src

    def test_metrics_in_payload(self):
        src = Path("front/js/readers/palm-reader.js").read_text(encoding="utf-8")
        # payload 객체에 metrics 필드 포함
        assert "metrics," in src or "metrics:" in src

    def test_fallback_on_failure(self):
        """MediaPipe 실패 시 LLM Vision 단독 폴백 (try/catch)."""
        src = Path("front/js/readers/palm-reader.js").read_text(encoding="utf-8")
        assert "건너뜀" in src or "폴백" in src or "catch" in src


# ─────────────────────────── front/index.html ───────────────────────────


class TestIndexHtmlScript:
    """index.html에 palm-metrics.js 로드 영속."""

    def test_palm_metrics_script_loaded(self):
        src = Path("front/index.html").read_text(encoding="utf-8")
        assert 'src="js/readers/palm-metrics.js"' in src


# ─────────────────────────── web/server.py PalmReadingRequest ───────────────────────────


class TestServerPalmRequest:
    """PalmReadingRequest.metrics 필드 + endpoint 결정론 score_palm 호출."""

    def test_request_has_metrics_field(self):
        # 요청 모델은 web/schemas.py 로 분리됨 (구조 리팩터링 2026-06-21)
        src = Path("web/schemas.py").read_text(encoding="utf-8")
        # PalmReadingRequest 본체에 metrics 필드 명시
        # 단순 grep으로 metrics: dict 검색
        assert "metrics: dict[str, Any] | None" in src

    def test_endpoint_imports_score_palm(self):
        src = _server_source()
        assert "from engine.divination.palm.scoring import score_palm" in src

    def test_endpoint_calls_score_palm_on_keypoints(self):
        src = _server_source()
        assert "score_palm" in src
        assert "ADR-160" in src
        # keypoints dict 검증 분기
        assert 'k.startswith("kp")' in src

    def test_deterministic_block_in_result(self):
        src = _server_source()
        assert "deterministic_block" in src

    def test_safety_disclaimer_in_block(self):
        src = _server_source()
        # 안전 장치 ADR-006/113 명시
        assert "ADR-006/113" in src

    def test_no_metric_fallback_no_regression(self):
        """metrics 부재 시 기존 LLM Vision 단독 동작 유지 (분기 가드)."""
        src = _server_source()
        # palm_deterministic_block = None 디폴트 + req.metrics 검증
        assert "palm_deterministic_block = None" in src
        assert "req.metrics" in src


# ─────────────────────────── ADR-030 score_palm 인터페이스 정합 ───────────────────────────


class TestScorePalmIntegration:
    """engine/divination/palm/scoring.score_palm이 keypoints dict 입력으로 동작."""

    def test_score_palm_accepts_kp_dict(self):
        """간단한 21 keypoint dict 입력 → PalmScoringReport 반환."""
        from engine.divination.palm.scoring import score_palm
        # 정규화 좌표 (0~1) 21 keypoint 더미 (손목 중심 + 손가락 끝 펼침)
        kps = {f"kp{i}": [0.5 + i * 0.01, 0.5 - i * 0.01, 0.0] for i in range(21)}
        report = score_palm(kps, hand_side="left")
        assert report is not None
        assert hasattr(report, "lines")
        assert hasattr(report, "disclaimer_ko")
        assert hasattr(report, "hand_side")
        assert report.hand_side == "left"

    def test_score_palm_returns_lines_dict(self):
        """4 손금선 + 금성대 메타 lines dict 정합."""
        from engine.divination.palm.scoring import score_palm
        kps = {f"kp{i}": [0.5, 0.5, 0.0] for i in range(21)}
        report = score_palm(kps, hand_side="right")
        # 4 손금선 + 금성대 영역 (lifeline·headline·heartline·fateline·girdle 중 일부)
        assert len(report.lines) >= 1

    def test_score_palm_disclaimer_includes_safety(self):
        from engine.divination.palm.scoring import score_palm
        kps = {f"kp{i}": [0.5, 0.5, 0.0] for i in range(21)}
        report = score_palm(kps)
        # ADR-006/113 정합 면책 어휘 (운명·수명·재물·진단·예언 단정 X)
        assert report.disclaimer_ko
        keywords = ("참고", "단정", "면책", "운명", "예언", "진단", "포함하지 않", "재물")
        assert any(k in report.disclaimer_ko for k in keywords), \
            f"면책 어휘 부재: {report.disclaimer_ko[:100]}"
