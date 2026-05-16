"""§7.3 골든 셋 회귀 — 운영 표준 §6.5 + §6.7 케이스를 N≥20건으로 확장.

이 회귀는 두 층:
  (A) 입력 → user_text 조립의 정합성 (LLM 호출 없이 100% 결정적)
       - 메트릭 사극풍 라벨이 정확히 들어갔는가
       - 신뢰도 노트가 임계 조건과 일치하는가
       - 우선순위 ⑤단락 자리 후보가 정확히 식별되는가
  (B) LLM 응답(모킹)의 페르소나 톤 검증
       - 6.4 권장 어휘 ≥3회 출현
       - 6.4 금지 어휘 0건
       - 7.1 의료·법률·금융 단정 0건

LLM 응답 자체는 mock으로 대체 — 실 호출 없이 골든 셋 회귀가 CI에서 빠르게 통과한다.
실 LLM 응답 품질 평가(LLM-as-Judge)는 별도 운영 작업으로 분리(§7.3.1).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 페르소나 톤 검증 헬퍼 ───────────────────────────

PERSONA_ENCOURAGED = [
    "그대", "자네", "허허", "이 늙은이",
    "~시게", "~하시게", "~구먼", "~이로세", "~인고", "~하이",
]
PERSONA_FORBIDDEN = [
    "회원님", "고객님", "당신", "분명",
    "대박", "대운", "금전수", "재물수",
    "AI", "모델", "시스템",
]
MEDICAL_LEGAL_FORBIDDEN = [
    "암이 보입니", "치매", "단명", "수술해야",
    "고소", "패소", "이혼한다", "헤어진다",
    "주식이 오를", "비트코인", "부동산을 사",
]


def assert_persona_tone(text: str, min_encouraged_hits: int = 3) -> None:
    """페르소나 어휘 ≥3회 출현 + 금지 0건."""
    # 권장 어휘 매칭 (어미 '~시게' 같은 패턴은 부분 문자열로 충분)
    encouraged_hits = sum(1 for w in PERSONA_ENCOURAGED if w.replace("~", "") in text)
    assert encouraged_hits >= min_encouraged_hits, (
        f"권장 어휘 {encouraged_hits}회 < {min_encouraged_hits} — 페르소나 톤 부족"
    )
    for fw in PERSONA_FORBIDDEN:
        assert fw not in text, f"금지 어휘 '{fw}' 검출"
    for fw in MEDICAL_LEGAL_FORBIDDEN:
        assert fw not in text, f"7.1 단정 표현 '{fw}' 검출"


# ─────────────────────────── 골든 셋 케이스 정의 ───────────────────────────

GOLDEN_SET = [
    # ===== 운영표준 §6.5.A 양형 — 청년 근골 강함 =====
    {
        "id": "G01_yang_young_square",
        "age": 38, "gender": "남", "question": "올해 직업 운이 궁금합니다",
        "metrics": {
            "three_thirds": [33, 36, 31], "alar_ratio": 0.35,
            "mouth_corner_lift": 0.07, "eye_distance_ratio": 1.02,
            "face_shape": "square", "asymmetry": 0.012,
            "blendshapes": {"jaw_open": 0.05, "mouth_smile": 0.18, "brow_inner_up": 0.04, "eye_blink": 0.21},
            "face_count": 1,
        },
        "expect": {
            "metric_labels": ["도탑다", "올라간 상", "각진형"],
            "priority_focus": "face_shape",  # face_shape ≠ oval
        },
    },
    # ===== 운영표준 §6.5.B 음형 — 노년 지력질 =====
    {
        "id": "G02_yin_elder_long",
        "age": 72, "gender": "여", "question": "건강과 자녀가 걱정입니다",
        "metrics": {
            "three_thirds": [42, 38, 20], "alar_ratio": 0.27,
            "mouth_corner_lift": -0.06, "eye_distance_ratio": 0.96,
            "face_shape": "long", "asymmetry": 0.028,
            "blendshapes": {"jaw_open": 0.02, "mouth_smile": 0.04, "brow_inner_up": 0.12, "eye_blink": 0.35},
            "face_count": 1,
        },
        "expect": {
            "metric_labels": ["아담하다", "처진 상", "긴 얼굴", "또렷한 비대칭"],
            "priority_focus": "face_shape",
        },
    },
    # ===== 영양질 원형 (중년) =====
    {
        "id": "G03_round_middle",
        "age": 45, "gender": "여", "question": None,
        "metrics": {
            "three_thirds": [30, 36, 34], "alar_ratio": 0.31,
            "mouth_corner_lift": 0.04, "eye_distance_ratio": 1.05,
            "face_shape": "round", "asymmetry": 0.008,
            "face_count": 1,
        },
        "expect": {
            "metric_labels": ["고르다", "단정한 상", "원형"],
        },
    },
    # ===== 심성질 역삼각 (청년, 명궁 좁음) =====
    {
        "id": "G04_inverted_tri_young",
        "age": 24, "gender": "남", "question": "공부에 집중이 안 됩니다",
        "metrics": {
            "three_thirds": [38, 34, 28], "alar_ratio": 0.29,
            "mouth_corner_lift": 0.03, "eye_distance_ratio": 0.85,
            "face_shape": "inverted_tri", "asymmetry": 0.011,
            "face_count": 1,
        },
        "expect": {
            "metric_labels": ["역삼각", "명궁이 좁다"],
        },
    },
    # ===== 계란형 균형 + 미소 =====
    {
        "id": "G05_oval_balanced_smile",
        "age": 32, "gender": "여", "question": "인연이 있을까요",
        "metrics": {
            "three_thirds": [33, 34, 33], "alar_ratio": 0.32,
            "mouth_corner_lift": 0.12, "eye_distance_ratio": 1.00,
            "face_shape": "oval", "asymmetry": 0.006,
            "cheo_cheop_ratio": 0.32, "wajam_ratio": 0.20,
            "face_count": 1,
        },
        "expect": {
            "metric_labels": ["올라간 상", "계란형", "처첩궁이 넓다", "와잠이 도톰하다"],
        },
    },
    # ===== 비대칭 두드러진 케이스 =====
    {
        "id": "G06_high_asymmetry",
        "age": 41, "gender": "남", "question": None,
        "metrics": {
            "three_thirds": [33, 34, 33], "alar_ratio": 0.33,
            "mouth_corner_lift": 0.01, "eye_distance_ratio": 1.03,
            "face_shape": "oval", "asymmetry": 0.035,
            "face_count": 1,
        },
        "expect": {
            "metric_labels": ["또렷한 비대칭"],
        },
    },
    # ===== 명궁 트인 케이스 =====
    {
        "id": "G07_wide_eye_distance",
        "age": 28, "gender": "여", "question": None,
        "metrics": {
            "three_thirds": [33, 34, 33], "alar_ratio": 0.31,
            "mouth_corner_lift": 0.06, "eye_distance_ratio": 1.18,
            "face_shape": "oval", "asymmetry": 0.010,
            "face_count": 1,
        },
        "expect": {
            "metric_labels": ["명궁이 트였다"],
        },
    },
    # ===== 와잠 옅음 케이스 =====
    {
        "id": "G08_thin_wajam",
        "age": 55, "gender": "남", "question": None,
        "metrics": {
            "three_thirds": [33, 34, 33], "alar_ratio": 0.30,
            "mouth_corner_lift": 0.02, "eye_distance_ratio": 1.02,
            "face_shape": "oval", "asymmetry": 0.012,
            "cheo_cheop_ratio": 0.20, "wajam_ratio": 0.10,
            "face_count": 1,
        },
        "expect": {
            "metric_labels": ["와잠이 옅다", "처첩궁이 좁다"],
        },
    },
    # ===== 헤드 틸트 큰 케이스 (신뢰도 노트) =====
    {
        "id": "G09_tilted_head",
        "age": 35, "gender": "남", "question": None,
        "metrics": {
            "three_thirds": [33, 34, 33], "alar_ratio": 0.33,
            "mouth_corner_lift": 0.03, "eye_distance_ratio": 1.00,
            "face_shape": "oval", "asymmetry": 0.012,
            "head_tilt_deg": 14.5, "face_count": 1,
        },
        "expect": {
            "metric_labels": ["기울어졌으나"],
        },
    },
    # ===== 광각 왜곡 의심 =====
    {
        "id": "G10_lens_distortion",
        "age": 30, "gender": "여", "question": None,
        "metrics": {
            "three_thirds": [33, 34, 33], "alar_ratio": 0.31,
            "mouth_corner_lift": 0.04, "eye_distance_ratio": 1.02,
            "face_shape": "oval", "asymmetry": 0.013,
            "face_center_offset": 0.22, "face_count": 1,
        },
        "expect": {
            "metric_labels": ["광각 왜곡"],
        },
    },
    # ===== 저조도 =====
    {
        "id": "G11_low_brightness",
        "age": 40, "gender": "남", "question": None,
        "metrics": {
            "three_thirds": [33, 34, 33], "alar_ratio": 0.31,
            "mouth_corner_lift": 0.02, "eye_distance_ratio": 1.00,
            "face_shape": "oval", "asymmetry": 0.012,
            "brightness": 0.15, "face_count": 1,
        },
        "expect": {
            "metric_labels": ["조도가 낮음"],
        },
    },
    # ===== 과조도 =====
    {
        "id": "G12_high_brightness",
        "age": 36, "gender": "여", "question": None,
        "metrics": {
            "three_thirds": [33, 34, 33], "alar_ratio": 0.32,
            "mouth_corner_lift": 0.05, "eye_distance_ratio": 1.01,
            "face_shape": "oval", "asymmetry": 0.011,
            "brightness": 0.90, "face_count": 1,
        },
        "expect": {
            "metric_labels": ["과강"],
        },
    },
    # ===== 입꼬리 처진 + 의료 화두 → 의료 우회 어휘 강제 =====
    {
        "id": "G13_health_question_medical_dodge",
        "age": 60, "gender": "여", "question": "요즘 몸이 자주 아픕니다",
        "metrics": {
            "three_thirds": [32, 35, 33], "alar_ratio": 0.30,
            "mouth_corner_lift": -0.05, "eye_distance_ratio": 1.00,
            "face_shape": "oval", "asymmetry": 0.014,
            "face_count": 1,
        },
        "expect": {
            "metric_labels": ["처진 상"],
            "must_avoid": MEDICAL_LEGAL_FORBIDDEN,
        },
    },
    # ===== 미성년 — 격려 톤 강제 =====
    {
        "id": "G14_minor_encouragement",
        "age": 16, "gender": "남", "question": "진로가 고민입니다",
        "metrics": {
            "three_thirds": [36, 33, 31], "alar_ratio": 0.29,
            "mouth_corner_lift": 0.06, "eye_distance_ratio": 1.05,
            "face_shape": "oval", "asymmetry": 0.010,
            "face_count": 1,
        },
        "expect": {
            "metric_labels": ["올라간 상"],
        },
    },
    # ===== 메트릭 부분 결손 (graceful) =====
    {
        "id": "G15_partial_metrics",
        "age": 33, "gender": None, "question": None,
        "metrics": {
            "alar_ratio": 0.32,
            "face_count": 1,
        },
        "expect": {
            "metric_labels": ["고르다"],
        },
    },
    # ===== 메트릭 None (LLM 사진만으로 풀이) =====
    {
        "id": "G16_no_metrics",
        "age": 40, "gender": "남", "question": "올해는 어떨까요",
        "metrics": None,
        "expect": {
            "no_metrics_block": True,
        },
    },
    # ===== §7.2.1 ERR_FACE_NOT_DETECTED =====
    {
        "id": "G17_err_face_not_detected",
        "age": 30, "gender": "남", "question": "올해 운이 궁금합니다",
        "metrics": {"face_count": 0},
        "expect_response": {
            "error_code": "ERR_FACE_NOT_DETECTED",
            "no_llm_call": True,
        },
    },
    # ===== §7.2.1 ERR_FACE_MULTIPLE =====
    {
        "id": "G18_err_face_multiple",
        "age": 30, "gender": "여", "question": None,
        "metrics": {"face_count": 3},
        "expect_response": {
            "error_code": "ERR_FACE_MULTIPLE",
            "no_llm_call": True,
        },
    },
    # ===== §7.2.1 ERR_FACE_PROFILE (강한 측면) =====
    {
        "id": "G19_err_face_profile",
        "age": 35, "gender": "남", "question": None,
        "metrics": {"head_tilt_deg": 50, "face_count": 1},
        "expect_response": {
            "error_code": "ERR_FACE_PROFILE",
            "no_llm_call": True,
        },
    },
    # ===== §7.2.1 WARN_FACE_FLAT (평면 사진) — 풀이 정상 =====
    {
        "id": "G20_warn_face_flat",
        "age": 40, "gender": "남", "question": None,
        "metrics": {
            "three_thirds": [33, 34, 33], "alar_ratio": 0.32,
            "mouth_corner_lift": 0.03, "eye_distance_ratio": 1.00,
            "face_shape": "oval", "asymmetry": 0.012,
            "z_variance": 0.00005, "face_count": 1,
        },
        "expect_response": {
            "warn_code": "WARN_FACE_FLAT",
        },
    },
    # ===== 위기 화두 — LLM 호출 없이 1393 응답 =====
    {
        "id": "G21_crisis_question",
        "age": 28, "gender": "여", "question": "죽고 싶다",
        "metrics": {
            "three_thirds": [33, 34, 33], "alar_ratio": 0.32,
            "face_count": 1,
        },
        "expect_response": {
            "crisis_alert": True,
            "hotline_in_text": "1393",
            "no_llm_call": True,
        },
    },
]


# ─────────────────────────── (A) user_text 조립 정합성 회귀 ───────────────────────────

@pytest.mark.parametrize("case", [c for c in GOLDEN_SET if "expect" in c],
                         ids=lambda c: c["id"])
def test_golden_user_text_assembly(case):
    """user_text에 기대 사극풍 라벨이 모두 포함되는가."""
    from engine.divination.face_reading import _build_user_text
    t = _build_user_text(
        age=case["age"], gender=case["gender"],
        question=case["question"], metrics=case["metrics"],
    )
    exp = case.get("expect", {})
    if exp.get("no_metrics_block"):
        assert "측정된 자취" not in t
        return
    for label in exp.get("metric_labels", []):
        assert label in t, f"[{case['id']}] '{label}' 누락 in user_text"
    # 화두가 있으면 user_text에 그대로 포함되어야
    if case["question"]:
        assert case["question"][:8] in t, f"[{case['id']}] 화두 누락"


# ─────────────────────────── (B) generate_face_reading 응답 회귀 ───────────────────────────

@pytest.mark.parametrize("case", [c for c in GOLDEN_SET if "expect_response" in c],
                         ids=lambda c: c["id"])
def test_golden_response_envelope(case, monkeypatch, tmp_path):
    """전체 거부·경고·위기 케이스의 응답 봉투(error_code/crisis_alert/text) 정합."""
    from engine.divination import face_reading

    monkeypatch.setattr(face_reading, "_CACHE_DIR", tmp_path)

    call_count = {"n": 0}
    def fake_vision(*a, **k):
        call_count["n"] += 1
        return "허허, 그대의 상이 잘 잡혔구먼. 이 늙은이가 살펴보았네."
    monkeypatch.setattr(face_reading, "_call_vision", fake_vision)

    r = face_reading.generate_face_reading(
        image_b64="dummy-img",
        age=case["age"], gender=case["gender"],
        question=case["question"], metrics=case["metrics"],
    )

    exp = case["expect_response"]
    if "error_code" in exp:
        assert r.get("error_code") == exp["error_code"], f"[{case['id']}] error_code 불일치"
    if "warn_code" in exp:
        assert r.get("error_code") == exp["warn_code"], f"[{case['id']}] warn_code 불일치"
        # 경고는 풀이 정상 진행
        assert "허허" in r["text"], f"[{case['id']}] 경고인데 풀이 미생성"
    if exp.get("crisis_alert"):
        assert r["crisis_alert"] is not None, f"[{case['id']}] crisis_alert 누락"
        assert exp["hotline_in_text"] in r["text"], f"[{case['id']}] 핫라인 누락"
    if exp.get("no_llm_call"):
        assert call_count["n"] == 0, f"[{case['id']}] LLM 호출 발생 (should be 0)"


# ─────────────────────────── (C) 페르소나 톤 회귀 — mock 응답 검증 ───────────────────────────

# 정답 풀이 견본 (운영표준 6.5.A 양형 기대 골격을 풀어쓴 모범 응답)
GOLDEN_MOCK_REPLIES = {
    "G01_yang_young_square": (
        "허허, 그대의 상이 잘 잡혀 있구먼. 이 늙은이가 살펴보니, "
        "광대와 턱의 결이 든든하여 근골(筋骨)의 결이 또렷하고 기색이 환하이. "
        "이마는 평이하나 큰 굴곡 없이 무던한 초년이었으리라. "
        "콧방울이 도타워 재백의 자리가 든든하고, 그대의 직업 자리와 호응하는구먼. "
        "입꼬리도 단정히 올라가 인덕의 결이 보이는구먼. "
        "그대만의 한 가지를 짚자면, 근골의 뚝심이라 하겠네. "
        "이 늙은이의 한 마디 — 콧대의 곧음을 믿고 한 해를 도모하시게나."
    ),
    "G02_yin_elder_long": (
        "허허, 그대의 상에 오랜 세월의 결이 곱게 흐르는구먼. "
        "신(神)이 또렷하고 기색이 단정하이. 음의 결이 깊되 어둡지 않으니 평안의 자리라네. "
        "이마가 넉넉하여 학문과 사색의 자리가 든든하시구먼. "
        "콧대가 곧으니 자존이 단정하고, 명궁의 결이 평안하이. "
        "하정이 다소 아담하고 입꼬리가 가라앉아 있으니 인덕은 안에서 살피시게. "
        "자녀의 결은 의원과 함께 짚어보시게나. "
        "이 늙은이의 한 마디 — 몸을 보전하시며 평안을 도모하시게나."
    ),
}


@pytest.mark.parametrize("case_id, mock_reply", GOLDEN_MOCK_REPLIES.items())
def test_golden_persona_tone(case_id, mock_reply):
    """모범 응답이 페르소나 톤 규약을 만족하는가."""
    assert_persona_tone(mock_reply, min_encouraged_hits=4)
    # 추가: "이 늙은이의 한 마디" 마무리 결구 존재
    assert "이 늙은이의 한 마디" in mock_reply, f"[{case_id}] 마무리 결구 누락"
    # 분량 800자 미만이라도 톤은 만족해야 함 (실 LLM은 800~1300자 강제)
    assert len(mock_reply) >= 200, f"[{case_id}] mock 응답이 너무 짧음"


def test_golden_set_size():
    """N≥20 케이스 유지 회귀 — 운영표준 §7.3 골든 셋 규약."""
    assert len(GOLDEN_SET) >= 20, f"골든 셋 {len(GOLDEN_SET)}건 < 20"


def test_golden_set_id_uniqueness():
    """case_id 중복 방지."""
    ids = [c["id"] for c in GOLDEN_SET]
    assert len(ids) == len(set(ids)), "골든 셋 case_id 중복"


def test_golden_set_covers_all_face_shapes():
    """5종 얼굴형이 모두 골든 셋에 1번 이상 등장."""
    shapes_seen = set()
    for c in GOLDEN_SET:
        m = c.get("metrics") or {}
        fs = m.get("face_shape")
        if fs:
            shapes_seen.add(fs)
    expected = {"round", "square", "inverted_tri", "oval", "long"}
    assert expected.issubset(shapes_seen), f"누락된 face_shape: {expected - shapes_seen}"


def test_golden_set_covers_error_codes():
    """ERR_*/WARN_* 핵심 코드가 골든 셋에 1번 이상 등장."""
    codes_seen = set()
    for c in GOLDEN_SET:
        er = c.get("expect_response") or {}
        if er.get("error_code"):
            codes_seen.add(er["error_code"])
        if er.get("warn_code"):
            codes_seen.add(er["warn_code"])
    expected_min = {"ERR_FACE_NOT_DETECTED", "ERR_FACE_MULTIPLE", "ERR_FACE_PROFILE", "WARN_FACE_FLAT"}
    assert expected_min.issubset(codes_seen), f"누락된 코드: {expected_min - codes_seen}"
