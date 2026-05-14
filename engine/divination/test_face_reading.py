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


# ─────────────────────────── 엣지 케이스 — graceful degradation ───────────────────────────

def test_format_metrics_block_partial_metrics():
    """메트릭이 부분적으로만 있어도 정상 (한 항목만 있는 경우)."""
    from engine.divination.face_reading import _format_metrics_block
    out = _format_metrics_block({"alar_ratio": 0.35})
    joined = "\n".join(out)
    assert "콧방울" in joined
    # 다른 항목은 노출 X
    assert "삼정 비율" not in joined
    assert "입꼬리" not in joined


def test_format_metrics_block_invalid_types_ignored():
    """잘못된 타입(str/None)이 들어와도 KeyError/TypeError 없이 무시."""
    from engine.divination.face_reading import _format_metrics_block
    out = _format_metrics_block({
        "three_thirds": "not a list",
        "alar_ratio": None,
        "mouth_corner_lift": "+0.1",  # str
        "face_shape": 123,  # int
        "blendshapes": "not a dict",
    })
    joined = "\n".join(out)
    # 헤더는 있지만 잘못된 라인은 모두 생략
    assert "측정된 자취" in joined or out == [] or len([l for l in out if "•" in l]) == 0


def test_format_metrics_block_threshold_boundary_alar():
    """콧방울 너비 임계값 경계 — 0.28 / 0.34."""
    from engine.divination.face_reading import _format_metrics_block
    # exact thresholds
    assert "아담하다" in "\n".join(_format_metrics_block({"alar_ratio": 0.28}))
    # 0.28 보다 살짝 위 → 고르다
    assert "고르다" in "\n".join(_format_metrics_block({"alar_ratio": 0.281}))
    # 0.34 정확히 → 도탑다
    assert "도탑다" in "\n".join(_format_metrics_block({"alar_ratio": 0.34}))
    # 0.34 미만 → 고르다
    assert "고르다" in "\n".join(_format_metrics_block({"alar_ratio": 0.339}))


def test_format_metrics_block_quality_thresholds_independent():
    """신뢰도 단서 — 각각 독립 노출."""
    from engine.divination.face_reading import _format_metrics_block
    # 틸트만
    o1 = "\n".join(_format_metrics_block({"head_tilt_deg": 11.0}))
    assert "기울어졌" in o1
    assert "광각 왜곡" not in o1
    # 광각만
    o2 = "\n".join(_format_metrics_block({"face_center_offset": 0.20}))
    assert "광각 왜곡" in o2
    assert "기울어졌" not in o2
    # 안전 범위
    o3 = "\n".join(_format_metrics_block({"head_tilt_deg": 5.0, "face_center_offset": 0.10}))
    assert "측정 신뢰도 단서" not in o3


def test_format_metrics_block_brightness_notes():
    """조도 기반 신뢰도 단서 — 낮음/과강/안전."""
    from engine.divination.face_reading import _format_metrics_block
    dark = "\n".join(_format_metrics_block({"brightness": 0.15}))
    bright = "\n".join(_format_metrics_block({"brightness": 0.90}))
    safe = "\n".join(_format_metrics_block({"brightness": 0.50}))
    assert "조도가 낮음" in dark
    assert "기색 판단 보수적" in dark
    assert "과강" in bright
    assert "역광/하이라이트" in bright
    assert "조도" not in safe


def test_format_metrics_block_asymmetry_classification():
    """좌우 비대칭 3단계 — 0.010 / 0.020 임계."""
    from engine.divination.face_reading import _format_metrics_block
    low = "\n".join(_format_metrics_block({"asymmetry": 0.005}))
    mid = "\n".join(_format_metrics_block({"asymmetry": 0.015}))
    high = "\n".join(_format_metrics_block({"asymmetry": 0.030}))
    assert "거의 대칭" in low
    assert "은은한 비대칭" in mid
    assert "또렷한 비대칭" in high
    # 경계
    assert "거의 대칭" in "\n".join(_format_metrics_block({"asymmetry": 0.009}))
    assert "은은한 비대칭" in "\n".join(_format_metrics_block({"asymmetry": 0.019}))


def test_format_metrics_block_eye_distance_classification():
    """미간 폭 3단계 — 명궁 좁다/고르다/트였다."""
    from engine.divination.face_reading import _format_metrics_block
    narrow = "\n".join(_format_metrics_block({"eye_distance_ratio": 0.85}))
    mid = "\n".join(_format_metrics_block({"eye_distance_ratio": 1.00}))
    wide = "\n".join(_format_metrics_block({"eye_distance_ratio": 1.20}))
    assert "명궁이 좁다" in narrow
    assert "명궁이 고르다" in mid
    assert "명궁이 트였다" in wide
    # 경계 0.90 / 1.10
    assert "명궁이 고르다" in "\n".join(_format_metrics_block({"eye_distance_ratio": 0.90}))
    assert "명궁이 고르다" in "\n".join(_format_metrics_block({"eye_distance_ratio": 1.10}))
    assert "명궁이 좁다" in "\n".join(_format_metrics_block({"eye_distance_ratio": 0.89}))
    assert "명궁이 트였다" in "\n".join(_format_metrics_block({"eye_distance_ratio": 1.11}))


def test_format_metrics_block_cheo_cheop_classification():
    """처첩궁 폭 3단계."""
    from engine.divination.face_reading import _format_metrics_block
    assert "처첩궁이 좁다" in "\n".join(_format_metrics_block({"cheo_cheop_ratio": 0.20}))
    assert "처첩궁이 고르다" in "\n".join(_format_metrics_block({"cheo_cheop_ratio": 0.25}))
    assert "처첩궁이 넓다" in "\n".join(_format_metrics_block({"cheo_cheop_ratio": 0.35}))
    # 경계 0.22 / 0.30
    assert "처첩궁이 고르다" in "\n".join(_format_metrics_block({"cheo_cheop_ratio": 0.22}))
    assert "처첩궁이 넓다" in "\n".join(_format_metrics_block({"cheo_cheop_ratio": 0.30}))


# ─────────────────────────── §7.2.1 사진 불량 9종 에러코드 ───────────────────────────

def test_classify_metric_issue_normal_metrics_returns_none():
    """정상 메트릭은 None 반환 (불량 아님)."""
    from engine.divination.face_reading import classify_metric_issue
    assert classify_metric_issue(None) is None
    assert classify_metric_issue({}) is None
    assert classify_metric_issue({
        "three_thirds": [33, 34, 33],
        "head_tilt_deg": 5,
        "brightness": 0.5,
        "z_variance": 0.005,
        "blendshapes": {"jaw_open": 0.05, "mouth_smile": 0.10, "brow_inner_up": 0.05, "eye_blink": 0.20},
    }) is None


def test_classify_metric_issue_face_count():
    """face_count 0 / >=2 분류."""
    from engine.divination.face_reading import (
        classify_metric_issue, ERR_FACE_NOT_DETECTED, ERR_FACE_MULTIPLE,
    )
    assert classify_metric_issue({"face_count": 0}) == ERR_FACE_NOT_DETECTED
    assert classify_metric_issue({"face_count": 2}) == ERR_FACE_MULTIPLE
    assert classify_metric_issue({"face_count": 3}) == ERR_FACE_MULTIPLE


def test_classify_metric_issue_non_human():
    """blendshape 키는 있는데 모두 0 → 사람 아님."""
    from engine.divination.face_reading import classify_metric_issue, ERR_FACE_NON_HUMAN
    assert classify_metric_issue({
        "blendshapes": {"jaw_open": 0, "mouth_smile": 0, "brow_inner_up": 0, "eye_blink": 0}
    }) == ERR_FACE_NON_HUMAN


def test_classify_metric_issue_profile_view():
    """head_tilt_deg 절대값 40° 초과 → 강측면."""
    from engine.divination.face_reading import classify_metric_issue, ERR_FACE_PROFILE
    assert classify_metric_issue({"head_tilt_deg": 45}) == ERR_FACE_PROFILE
    assert classify_metric_issue({"head_tilt_deg": -50}) == ERR_FACE_PROFILE
    # 경계
    assert classify_metric_issue({"head_tilt_deg": 40}) != ERR_FACE_PROFILE  # 경계 미포함


def test_classify_metric_issue_backlit():
    """brightness < 0.10 → 강한 역광/저조도."""
    from engine.divination.face_reading import classify_metric_issue, ERR_FACE_BACKLIT
    assert classify_metric_issue({"brightness": 0.05}) == ERR_FACE_BACKLIT
    # 경계 0.10 (미만이라야 잡힘)
    assert classify_metric_issue({"brightness": 0.10}) != ERR_FACE_BACKLIT


def test_classify_metric_issue_flat_photo_warn():
    """z_variance 매우 작음 → 평면 사진 의심 경고."""
    from engine.divination.face_reading import classify_metric_issue, WARN_FACE_FLAT
    assert classify_metric_issue({"z_variance": 0.00005}) == WARN_FACE_FLAT
    # z_variance 0은 측정 실패라 무시
    assert classify_metric_issue({"z_variance": 0}) is None


def test_generate_face_reading_returns_error_code_on_face_not_detected(monkeypatch, tmp_path):
    """face_count==0 케이스 — LLM 호출 없이 안내 + error_code 반환."""
    from engine.divination import face_reading
    monkeypatch.setattr(face_reading, "_CACHE_DIR", tmp_path)
    def boom(*a, **k):
        raise RuntimeError("불량 사진 거부 시 LLM 호출 X")
    monkeypatch.setattr(face_reading, "_call_vision", boom)

    r = face_reading.generate_face_reading(
        image_b64="dummy",
        metrics={"face_count": 0},
    )
    assert r["error_code"] == "ERR_FACE_NOT_DETECTED"
    assert "상이 잘 잡히지 않" in r["text"]
    assert r["crisis_alert"] is None


def test_generate_face_reading_returns_warn_code_on_flat_photo(monkeypatch, tmp_path):
    """z_variance 낮음 — 풀이는 정상, error_code: WARN_FACE_FLAT 노출."""
    from engine.divination import face_reading
    monkeypatch.setattr(face_reading, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(face_reading, "_call_vision",
                        lambda *a, **k: "허허, 그대의 상을 살피니…")

    r = face_reading.generate_face_reading(
        image_b64="dummy",
        metrics={"z_variance": 0.00005, "three_thirds": [33, 34, 33]},
    )
    assert r.get("error_code") == "WARN_FACE_FLAT"
    assert "허허" in r["text"]  # 풀이 본문은 정상 산출됨


# ─────────────────────────── §7.2.8 캐시 무효화 트리거 ───────────────────────────

def test_system_prompt_hash_is_8_chars():
    """_SYSTEM_PROMPT_HASH는 _FACE_SYSTEM SHA256 앞 8자."""
    import hashlib
    from engine.divination.face_reading import _FACE_SYSTEM, _SYSTEM_PROMPT_HASH
    expected = hashlib.sha256(_FACE_SYSTEM.encode("utf-8")).hexdigest()[:8]
    assert _SYSTEM_PROMPT_HASH == expected
    assert len(_SYSTEM_PROMPT_HASH) == 8


def test_hash_payload_includes_system_prompt_prefix():
    """캐시 키에 시스템 프롬프트 해시가 포함되어야 (§7.2.8)."""
    from engine.divination import face_reading
    key = face_reading._hash_payload("img", 30, "남", "q", None)
    # 키는 24자 SHA256 prefix이지만, 같은 입력 + 다른 시스템 프롬프트 해시면 달라져야 함
    # 우회 검증: monkeypatch로 _SYSTEM_PROMPT_HASH 임시 변경 시 키가 달라지는지
    orig_hash = face_reading._SYSTEM_PROMPT_HASH
    try:
        face_reading._SYSTEM_PROMPT_HASH = "deadbeef"
        key_changed = face_reading._hash_payload("img", 30, "남", "q", None)
        assert key != key_changed, "시스템 프롬프트 해시 변경 시 캐시 키도 달라져야 함"
    finally:
        face_reading._SYSTEM_PROMPT_HASH = orig_hash


def test_cache_invalidation_on_prompt_change(monkeypatch, tmp_path):
    """프롬프트 변경 시 기존 캐시 hit 안 되는지 시뮬레이션."""
    from engine.divination import face_reading
    monkeypatch.setattr(face_reading, "_CACHE_DIR", tmp_path)

    call_count = {"n": 0}
    def fake(*a, **k):
        call_count["n"] += 1
        return f"call {call_count['n']}"
    monkeypatch.setattr(face_reading, "_call_vision", fake)

    # 첫 호출 — 캐시 저장
    face_reading.generate_face_reading(
        image_b64="img", age=30, gender="남", question="화두"
    )
    assert call_count["n"] == 1

    # 시스템 프롬프트 해시 변경 (배포 시 _FACE_SYSTEM 수정한 효과 시뮬레이션)
    monkeypatch.setattr(face_reading, "_SYSTEM_PROMPT_HASH", "newhash1")

    face_reading.generate_face_reading(
        image_b64="img", age=30, gender="남", question="화두"
    )
    assert call_count["n"] == 2, "프롬프트 해시 변경 후 캐시 hit 발생 (§7.2.8 위반)"


# ─────────────────────────── §7.2.6 a11y 메타데이터 어댑터 ───────────────────────────

def test_a11y_metadata_extraction_full_reading():
    """전형적 풀이 → 인사·본문 단락·마무리 분리."""
    from engine.divination.face_reading import _extract_a11y_metadata
    body = (
        "허허, 그대의 상이 잘 잡혀 있구먼.\n\n"
        "광대의 결이 든든하니 근골의 자리가 또렷하구먼.\n\n"
        "콧방울이 도타워 재백의 결이 보이는구먼.\n\n"
        "이 늙은이의 한 마디 — 한 해를 도모하시게나."
    )
    a = _extract_a11y_metadata(body, "법적 고지 1단락")
    assert a["paragraph_count"] == 4
    assert a["has_greeting"] is True
    assert a["has_closing"] is True
    roles = [p["role"] for p in a["paragraphs"]]
    assert roles[0] == "greeting"
    assert roles[-1] == "closing"
    assert a["total_length"] == len(body)
    assert a["legal_footer_length"] == len("법적 고지 1단락")


def test_a11y_metadata_empty_text():
    """빈 풀이 → paragraph_count=0, has_* 모두 False."""
    from engine.divination.face_reading import _extract_a11y_metadata
    a = _extract_a11y_metadata("", "")
    assert a["paragraph_count"] == 0
    assert a["has_greeting"] is False
    assert a["has_closing"] is False
    assert a["paragraphs"] == []


def test_a11y_metadata_no_greeting_no_closing():
    """본문만 있을 때 has_greeting/has_closing 모두 False."""
    from engine.divination.face_reading import _extract_a11y_metadata
    body = "그대의 콧대가 곧으니 결이 또렷하구먼.\n\n광대의 결이 든든하이."
    a = _extract_a11y_metadata(body, "")
    assert a["paragraph_count"] == 2
    assert a["has_greeting"] is False
    assert a["has_closing"] is False


def test_a11y_metadata_paragraph_role_body():
    """인사·마무리 아닌 단락은 'body' 역할."""
    from engine.divination.face_reading import _extract_a11y_metadata
    body = "허허, 시작.\n\n중간 단락.\n\n이 늙은이의 한 마디 — 끝."
    a = _extract_a11y_metadata(body, "")
    roles = [p["role"] for p in a["paragraphs"]]
    assert roles == ["greeting", "body", "closing"]


def test_generate_face_reading_includes_a11y(monkeypatch, tmp_path):
    """generate_face_reading 응답에 a11y 필드 포함."""
    from engine.divination import face_reading
    monkeypatch.setattr(face_reading, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(
        face_reading, "_call_vision",
        lambda *a, **k: "허허, 시험이로세.\n\n이 늙은이의 한 마디 — 끝."
    )
    r = face_reading.generate_face_reading(
        image_b64="dummy-img", age=30, gender="남", question=None,
    )
    assert "a11y" in r
    assert r["a11y"]["paragraph_count"] >= 1
    assert r["a11y"]["has_greeting"] is True
    assert r["a11y"]["has_closing"] is True


def test_generate_face_reading_err_response_includes_a11y(monkeypatch, tmp_path):
    """ERR_FACE_* 거부 응답에도 a11y 필드 포함."""
    from engine.divination import face_reading
    monkeypatch.setattr(face_reading, "_CACHE_DIR", tmp_path)
    r = face_reading.generate_face_reading(
        image_b64="dummy-img", metrics={"face_count": 0},
    )
    assert r.get("error_code") == "ERR_FACE_NOT_DETECTED"
    assert "a11y" in r
    assert r["a11y"]["paragraph_count"] >= 1


def test_generate_face_reading_crisis_response_includes_a11y(monkeypatch, tmp_path):
    """위기 응답에도 a11y 필드 포함."""
    from engine.divination import face_reading
    monkeypatch.setattr(face_reading, "_CACHE_DIR", tmp_path)
    r = face_reading.generate_face_reading(
        image_b64="dummy-img", question="죽고 싶다",
    )
    assert r["crisis_alert"] is not None
    assert "a11y" in r
    assert r["a11y"]["paragraph_count"] >= 1


# ─────────────────────────── ④ 신(神) 엔진 (운영표준 §5.5) ───────────────────────────

def test_format_metrics_block_shen_bright():
    """신 bright → '맑고 또렷' 사극풍."""
    from engine.divination.face_reading import _format_metrics_block
    out = "\n".join(_format_metrics_block({
        "shen": {"kind": "bright", "shen_score": 0.82}
    }))
    assert "신(神)" in out
    assert "맑고 또렷" in out
    assert "0.82" in out


def test_format_metrics_block_shen_steady():
    from engine.divination.face_reading import _format_metrics_block
    out = "\n".join(_format_metrics_block({
        "shen": {"kind": "steady", "shen_score": 0.60}
    }))
    assert "단정하다" in out


def test_format_metrics_block_shen_dim():
    """신 dim → '안정·휴식이 필요'."""
    from engine.divination.face_reading import _format_metrics_block
    out = "\n".join(_format_metrics_block({
        "shen": {"kind": "dim", "shen_score": 0.22}
    }))
    assert "옅다" in out
    assert "안정·휴식" in out


def test_format_metrics_block_shen_missing_kind():
    """kind 또는 score 누락 시 graceful."""
    from engine.divination.face_reading import _format_metrics_block
    out1 = _format_metrics_block({"shen": {"kind": "bright"}})  # score 없음
    out2 = _format_metrics_block({"shen": {"shen_score": 0.5}})  # kind 없음
    out3 = _format_metrics_block({"shen": "not a dict"})
    # 모두 crash 없이 list 반환
    for o in [out1, out2, out3]:
        assert isinstance(o, list)


# ─────────────────────────── ③ 기색 엔진 (운영표준 §5.5) ───────────────────────────

def test_format_metrics_block_complexion_red():
    """이마 붉은 결 → '열의 기운' 사극풍 어휘."""
    from engine.divination.face_reading import _format_metrics_block
    out = "\n".join(_format_metrics_block({
        "complexion": {
            "forehead": {"kind": "red", "rgb": {"r": 200, "g": 130, "b": 130}},
        }
    }))
    assert "기색" in out
    assert "이마" in out
    assert "열의 기운" in out


def test_format_metrics_block_complexion_pale_cheek():
    """좌 뺨 흰 결 → 서늘한 기운."""
    from engine.divination.face_reading import _format_metrics_block
    out = "\n".join(_format_metrics_block({
        "complexion": {"cheek_l": {"kind": "pale"}},
    }))
    assert "좌 뺨" in out
    assert "서늘한 기운" in out


def test_format_metrics_block_complexion_all_neutral():
    """모든 부위 neutral → '단정한 결' 한 줄."""
    from engine.divination.face_reading import _format_metrics_block
    out = "\n".join(_format_metrics_block({
        "complexion": {
            "forehead": {"kind": "neutral"},
            "cheek_l": {"kind": "neutral"},
            "cheek_r": {"kind": "neutral"},
        }
    }))
    assert "전체적으로 단정한 결" in out
    # notable 라인은 없어야
    assert "열의 기운" not in out
    assert "서늘한 기운" not in out


def test_format_metrics_block_complexion_multiple_regions():
    """이마 붉음 + 턱 어두움 같이 노출."""
    from engine.divination.face_reading import _format_metrics_block
    out = "\n".join(_format_metrics_block({
        "complexion": {
            "forehead": {"kind": "red"},
            "chin": {"kind": "dark"},
            "nose": {"kind": "neutral"},
        }
    }))
    assert "이마" in out and "열의 기운" in out
    assert "턱" in out and "정체" in out


def test_format_metrics_block_complexion_invalid_type():
    """complexion 값이 dict가 아니면 graceful."""
    from engine.divination.face_reading import _format_metrics_block
    out = _format_metrics_block({"complexion": "not a dict"})
    # 다른 메트릭 없이는 헤더만 있거나 빈 출력 — assertion 단순
    assert isinstance(out, list)


def test_format_metrics_block_wajam_classification():
    """와잠(자녀궁) 3단계."""
    from engine.divination.face_reading import _format_metrics_block
    assert "와잠이 옅다" in "\n".join(_format_metrics_block({"wajam_ratio": 0.10}))
    assert "와잠이 고르다" in "\n".join(_format_metrics_block({"wajam_ratio": 0.15}))
    assert "와잠이 도톰하다" in "\n".join(_format_metrics_block({"wajam_ratio": 0.20}))
    # 경계 0.12 / 0.18
    assert "와잠이 고르다" in "\n".join(_format_metrics_block({"wajam_ratio": 0.12}))
    assert "와잠이 도톰하다" in "\n".join(_format_metrics_block({"wajam_ratio": 0.18}))


# ─────────────────────────── 캐시 라운드트립 ───────────────────────────

def test_cache_save_load_roundtrip(tmp_path, monkeypatch):
    """캐시 저장 → 로드 → 같은 내용 복원."""
    from engine.divination import face_reading

    # 임시 경로로 캐시 디렉토리 우회
    monkeypatch.setattr(face_reading, "_CACHE_DIR", tmp_path)
    key = "test-key-abc"
    data = {"text": "허허, 시험이로세", "cached": False, "crisis_alert": None}
    face_reading._save_cache(key, data)
    loaded = face_reading._load_cache(key)
    assert loaded is not None
    assert loaded["text"] == "허허, 시험이로세"
    assert loaded["cached"] is True  # _load_cache가 cached=True로 강제


def test_cache_expiry(tmp_path, monkeypatch):
    """TTL 초과 캐시는 무시되어 None 반환."""
    import time, json
    from engine.divination import face_reading

    monkeypatch.setattr(face_reading, "_CACHE_DIR", tmp_path)
    key = "expired-key"
    # 직접 만든 만료된 캐시 파일 (TTL 25시간 전)
    payload = {"text": "old", "_ts": time.time() - 25 * 3600}
    (tmp_path / f"{key}.json").write_text(json.dumps(payload), encoding="utf-8")
    assert face_reading._load_cache(key) is None


# ─────────────────────────── 전체 흐름 — LLM mock ───────────────────────────

def test_generate_face_reading_with_mocked_llm(tmp_path, monkeypatch):
    """LLM mock으로 전체 흐름 + 캐시 + 메트릭 키 작동 검증."""
    from engine.divination import face_reading

    monkeypatch.setattr(face_reading, "_CACHE_DIR", tmp_path)

    captured_user_text = {}
    def fake_vision(system, user_text, img_b64):
        captured_user_text["t"] = user_text
        return "허허, 그대의 상이 잘 잡혔구먼."
    monkeypatch.setattr(face_reading, "_call_vision", fake_vision)

    result = face_reading.generate_face_reading(
        image_b64="img-data",
        age=42,
        gender="여성",
        question="새 길을 떠나도 좋을지",
        metrics={"three_thirds": [33, 34, 33], "alar_ratio": 0.36},
    )
    assert "허허" in result["text"]
    assert result["cached"] is False
    assert result["crisis_alert"] is None
    # 메트릭 안내가 user_text에 들어갔는지
    assert "측정된 자취" in captured_user_text["t"]
    assert "삼정 비율" in captured_user_text["t"]

    # 같은 입력 → 캐시 hit (LLM 호출되면 안 됨)
    def boom(*a, **k):
        raise RuntimeError("캐시 hit 시 LLM 호출 X")
    monkeypatch.setattr(face_reading, "_call_vision", boom)
    result2 = face_reading.generate_face_reading(
        image_b64="img-data",
        age=42,
        gender="여성",
        question="새 길을 떠나도 좋을지",
        metrics={"three_thirds": [33, 34, 33], "alar_ratio": 0.36},
    )
    assert result2["cached"] is True
    assert "허허" in result2["text"]


def test_generate_face_reading_metric_change_invalidates_cache(tmp_path, monkeypatch):
    """메트릭이 바뀌면 캐시 hit 안 됨 (새 LLM 호출)."""
    from engine.divination import face_reading

    monkeypatch.setattr(face_reading, "_CACHE_DIR", tmp_path)

    call_count = {"n": 0}
    def fake_vision(*a, **k):
        call_count["n"] += 1
        return f"call #{call_count['n']}"
    monkeypatch.setattr(face_reading, "_call_vision", fake_vision)

    # 같은 사진, 다른 메트릭 → 두 번 호출되어야 함
    face_reading.generate_face_reading(
        image_b64="same", age=30, gender="M", question=None,
        metrics={"alar_ratio": 0.30},
    )
    face_reading.generate_face_reading(
        image_b64="same", age=30, gender="M", question=None,
        metrics={"alar_ratio": 0.40},
    )
    assert call_count["n"] == 2


def test_generate_face_reading_empty_image_raises():
    """빈 이미지 → ValueError (FastAPI에서 400으로 변환됨)."""
    import pytest as _pytest
    from engine.divination import face_reading
    with _pytest.raises(ValueError, match="image_b64 is required"):
        face_reading.generate_face_reading(image_b64="", age=30)
    with _pytest.raises(ValueError, match="image_b64 is required"):
        face_reading.generate_face_reading(image_b64="   ", age=30)
