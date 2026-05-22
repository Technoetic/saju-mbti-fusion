"""ADR-143 회귀 — palm·face Vision 디폴트 모델 Opus 4.7 영속 보장.

본 시스템 정책 (사용자 결단 2026-05-22):
  palm·face Vision 진단은 Claude Opus 4.7 모델 사용 (최고 정확도).

회귀 의무:
  - 환경변수 BIZROUTER_VISION_MODEL 미설정 시 디폴트 = "anthropic/claude-opus-4.7"
  - Anthropic SDK fallback 디폴트 = "claude-opus-4-7"
  - 코드 상수 직접 검증 (런타임 호출 X — 외부 API 키 의존 회피)

/domain-priorities #7 후속 강화.
"""
from __future__ import annotations

import inspect

from engine.divination.palm import reading as palm_reading
from engine.divination.face import reading as face_reading


# 디폴트 모델 라벨 — palm·face 공통
BIZROUTER_DEFAULT_MODEL = "anthropic/claude-opus-4.7"
ANTHROPIC_SDK_MODEL = "claude-opus-4-7"


class TestPalmVisionOpusDefault:
    """palm Vision 디폴트 모델 Opus 4.7."""

    def test_palm_bizrouter_default_is_opus47(self):
        """palm _call_vision 소스에 BizRouter 디폴트 Opus 4.7 명시."""
        src = inspect.getsource(palm_reading._call_vision)
        assert BIZROUTER_DEFAULT_MODEL in src, (
            f"palm _call_vision BizRouter 디폴트 {BIZROUTER_DEFAULT_MODEL} 누락 — "
            "ADR-143 정책 위반"
        )

    def test_palm_anthropic_sdk_uses_opus47(self):
        """palm Anthropic SDK fallback이 Opus 4.7 (claude-opus-4-7)."""
        src = inspect.getsource(palm_reading._call_vision)
        assert ANTHROPIC_SDK_MODEL in src, (
            f"palm Anthropic SDK fallback {ANTHROPIC_SDK_MODEL} 누락"
        )

    def test_palm_no_inferior_model_default(self):
        """palm 디폴트에 열등 모델 (Haiku·Sonnet) 명시 없음."""
        src = inspect.getsource(palm_reading._call_vision)
        # 디폴트 fallback 라인에 inferior 모델이 명시되어 있으면 위반
        # 단 코드 주석·문서 안에서 다른 모델 언급은 허용 (정책 비교 용도)
        # 실 디폴트 fallback 표현만 검증
        assert 'or "anthropic/claude-opus-4.7"' in src or "or 'anthropic/claude-opus-4.7'" in src


class TestFaceVisionOpusDefault:
    """face Vision 디폴트 모델 Opus 4.7."""

    def test_face_bizrouter_default_is_opus47(self):
        """face _call_vision 소스에 BizRouter 디폴트 Opus 4.7 명시."""
        src = inspect.getsource(face_reading._call_vision)
        assert BIZROUTER_DEFAULT_MODEL in src, (
            f"face _call_vision BizRouter 디폴트 {BIZROUTER_DEFAULT_MODEL} 누락"
        )

    def test_face_anthropic_sdk_uses_opus47(self):
        """face Anthropic SDK fallback이 Opus 4.7."""
        src = inspect.getsource(face_reading._call_vision)
        assert ANTHROPIC_SDK_MODEL in src


class TestModelConsistencyAcrossModules:
    """palm·face 두 Vision 모듈이 동일 모델 정책 사용."""

    def test_both_use_same_bizrouter_default(self):
        """palm·face BizRouter 디폴트 일치 (Opus 4.7)."""
        palm_src = inspect.getsource(palm_reading._call_vision)
        face_src = inspect.getsource(face_reading._call_vision)
        # 두 모듈 모두 동일 디폴트 명시
        assert BIZROUTER_DEFAULT_MODEL in palm_src
        assert BIZROUTER_DEFAULT_MODEL in face_src

    def test_both_use_same_anthropic_fallback(self):
        """palm·face Anthropic SDK fallback 일치 (Opus 4.7)."""
        palm_src = inspect.getsource(palm_reading._call_vision)
        face_src = inspect.getsource(face_reading._call_vision)
        assert ANTHROPIC_SDK_MODEL in palm_src
        assert ANTHROPIC_SDK_MODEL in face_src


class TestADR143PolicyDocumentation:
    """ADR-143 정책 문서화 의무 — palm·face 모듈에 정책 마커 명시 권장."""

    def test_palm_module_documents_vision_policy(self):
        """palm/reading.py 모듈 또는 _call_vision 함수에 Opus 4.7 정책 언급."""
        # _call_vision 또는 모듈 docstring 어디든 OPUS·Claude 언급 권장
        # 본 회귀는 약한 검증 — 코드 상수 일치만 강제
        src = inspect.getsource(palm_reading)
        # palm은 model 라인에 "anthropic/claude-opus-4.7" 명시 있음
        assert BIZROUTER_DEFAULT_MODEL in src

    def test_face_module_documents_vision_policy(self):
        """face/reading.py 모듈에 Opus 4.7 정책 docstring 명시."""
        src = inspect.getsource(face_reading._call_vision)
        # face는 _call_vision docstring에 "claude-opus-4.7" 명시 (line 587)
        assert "opus-4.7" in src.lower() or "opus-4-7" in src.lower()
