"""face_reading 모듈 단위 테스트 — LLM 호출 없는 순수 로직만 검증.

명세서 §5/§6 기준 메트릭 포맷팅 + 캐시 키 + 위기 감지를 회귀 방지.
LLM 응답이 필요한 흐름은 mock으로 처리.
"""

from __future__ import annotations

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path 에 추가 (engine 패키지 import 가능하도록)
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 캐시 키 ───────────────────────────

def test_hash_payload_determinism():
    """같은 입력 → 같은 해시 (캐시 hit 보장)."""
    from engine.divination.face_reading import _hash_payload
    h1 = _hash_payload("img-b64", 30, "남성", "새 일", {"three_thirds": [33, 34, 33]})
    h2 = _hash_payload("img-b64", 30, "남성", "새 일", {"three_thirds": [33, 34, 33]})
    assert h1 == h2
    assert len(h1) == 24


def test_hash_payload_metric_sensitivity():
    """다른 메트릭 → 다른 해시 (다른 풀이가 캐시되어야 함)."""
    from engine.divination.face_reading import _hash_payload
    h1 = _hash_payload("img", 30, "남성", "q", {"alar_ratio": 0.30})
    h2 = _hash_payload("img", 30, "남성", "q", {"alar_ratio": 0.40})
    assert h1 != h2


def test_hash_payload_none_metrics_compat():
    """metrics 없을 때도 정상 (하위 호환)."""
    from engine.divination.face_reading import _hash_payload
    h = _hash_payload("img", 30, "남성", "q", None)
    assert isinstance(h, str) and len(h) == 24


def test_hash_payload_metric_key_order_irrelevant():
    """딕셔너리 키 순서가 달라도 같은 해시 (json sort_keys 보장)."""
    from engine.divination.face_reading import _hash_payload
    h1 = _hash_payload("img", None, None, None, {"a": 1, "b": 2})
    h2 = _hash_payload("img", None, None, None, {"b": 2, "a": 1})
    assert h1 == h2


# ─────────────────────────── 메트릭 포맷팅 ───────────────────────────

def test_format_metrics_block_empty():
    """None 또는 빈 dict → 빈 출력."""
    from engine.divination.face_reading import _format_metrics_block
    assert _format_metrics_block(None) == []
    assert _format_metrics_block({}) == []


def test_format_metrics_block_three_thirds():
    from engine.divination.face_reading import _format_metrics_block
    out = _format_metrics_block({"three_thirds": [30.5, 34.2, 35.3]})
    joined = "\n".join(out)
    assert "삼정 비율" in joined
    assert "30% : 34% : 35%" in joined


def test_format_metrics_block_alar_ratio_classification():
    """콧방울 너비 임계값 분류 (도탑다 / 고르다 / 아담하다)."""
    from engine.divination.face_reading import _format_metrics_block
    big = _format_metrics_block({"alar_ratio": 0.40})
    mid = _format_metrics_block({"alar_ratio": 0.31})
    small = _format_metrics_block({"alar_ratio": 0.25})
    assert "도탑다" in "\n".join(big)
    assert "고르다" in "\n".join(mid)
    assert "아담하다" in "\n".join(small)


def test_format_metrics_block_mouth_corner_classification():
    """입꼬리 방향 분류 (올라간 / 단정한 / 처진)."""
    from engine.divination.face_reading import _format_metrics_block
    up = "\n".join(_format_metrics_block({"mouth_corner_lift": 0.10}))
    mid = "\n".join(_format_metrics_block({"mouth_corner_lift": 0.02}))
    down = "\n".join(_format_metrics_block({"mouth_corner_lift": -0.10}))
    assert "올라간 상" in up
    assert "단정한 상" in mid
    assert "처진 상" in down


def test_format_metrics_block_face_shape_translation():
    """얼굴형 영문 키 → 한국어 5체질."""
    from engine.divination.face_reading import _format_metrics_block
    for key, expected in [
        ("round", "영양질"),
        ("square", "근골질"),
        ("inverted_tri", "심성질"),
        ("oval", "계란형"),
        ("long", "지력질"),
    ]:
        out = "\n".join(_format_metrics_block({"face_shape": key}))
        assert expected in out, f"{key} → {expected} 실패"


def test_format_metrics_block_quality_notes():
    """신뢰도 단서 — 헤드 틸트/광각/평면 사진."""
    from engine.divination.face_reading import _format_metrics_block
    out = "\n".join(_format_metrics_block({
        "head_tilt_deg": 15.5,
        "face_center_offset": 0.25,
        "z_variance": 0.00005,
    }))
    assert "측정 신뢰도 단서" in out
    assert "기울어졌으나" in out
    assert "광각 왜곡" in out
    assert "평면 사진" in out


def test_format_metrics_block_blendshape_flags():
    """Blendshape 임계값 이상 시 표정 단서 노출."""
    from engine.divination.face_reading import _format_metrics_block
    out = "\n".join(_format_metrics_block({
        "blendshapes": {"jaw_open": 0.20, "mouth_smile": 0.25, "brow_inner_up": 0.20}
    }))
    assert "표정 단서" in out
    assert "입이 살짝" in out
    assert "미소 띤" in out


# ─────────────────────────── _build_user_text ───────────────────────────

def test_build_user_text_no_metrics_backward_compat():
    """메트릭 없을 때도 정상 — 풀이 흐름 안내 포함."""
    from engine.divination.face_reading import _build_user_text
    t = _build_user_text(30, "남성", "새 일을 시작해도 좋을지")
    assert "약 30세" in t
    assert "남성" in t
    assert "새 일을" in t
    assert "운학 도사의 어조" in t
    # 메트릭 블록은 없어야 함
    assert "측정된 자취" not in t


def test_build_user_text_with_metrics():
    """메트릭 있을 때 안내 블록 포함."""
    from engine.divination.face_reading import _build_user_text
    t = _build_user_text(30, "여성", None, {
        "three_thirds": [33, 34, 33],
        "alar_ratio": 0.35,
    })
    assert "측정된 자취" in t
    assert "삼정 비율" in t
    assert "객관적 측정치" in t


# ─────────────────────────── 위기 신호 우선 처리 ───────────────────────────

def test_generate_face_reading_crisis_bypass(monkeypatch):
    """화두에 위기 신호 감지 시 LLM 호출 없이 핫라인 응답 반환."""
    from engine.divination import face_reading

    # _call_vision이 호출되면 안 됨 — 호출되면 RuntimeError
    def boom(*a, **k):
        raise RuntimeError("crisis 케이스에서 LLM 호출 X")
    monkeypatch.setattr(face_reading, "_call_vision", boom)

    # 명백한 위기 키워드 (engine.safety 가 잡는 것)
    result = face_reading.generate_face_reading(
        image_b64="dummy",
        question="죽고 싶다",
    )
    assert result["crisis_alert"] is not None
    assert "1393" in result["text"] or "1577" in result["text"]


# ─────────────────────────── 시스템 프롬프트 어휘집 회귀 ───────────────────────────

def test_face_system_prompt_contains_terminology():
    """운학 도사 페르소나 + 12궁/오관/오형 어휘집 회귀 방지."""
    from engine.divination.face_reading import _FACE_SYSTEM
    # 페르소나
    assert "雲鶴道士" in _FACE_SYSTEM or "운학 도사" in _FACE_SYSTEM
    # 12궁 핵심 명칭
    for term in ["명궁", "관록궁", "재백궁", "전택궁", "처첩궁", "자녀궁", "복덕궁"]:
        assert term in _FACE_SYSTEM, f"{term} 누락"
    # 오관 한자명
    for term in ["채청관", "보수관", "감찰관", "심변관", "출납관"]:
        assert term in _FACE_SYSTEM, f"{term} 누락"
    # 오형
    for term in ["영양질", "근골질", "심성질", "지력질", "체력질"]:
        assert term in _FACE_SYSTEM, f"{term} 누락"
