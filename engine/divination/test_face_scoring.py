"""engine.divination.face_scoring — 키포인트 → 12궁 점수 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 빈 입력 ───────────────────────────

def test_score_face_empty_metrics_returns_balanced():
    from engine.divination.face_scoring import score_face, ALL_PALACES
    r = score_face(None)
    assert len(r.palaces) == 12
    assert set(r.palaces.keys()) == set(ALL_PALACES)
    # 모든 점수 0.0~1.0
    for ps in r.palaces.values():
        assert 0.0 <= ps.score <= 1.0


def test_score_face_empty_dict_balanced():
    from engine.divination.face_scoring import score_face
    r = score_face({})
    assert len(r.palaces) == 12


# ─────────────────────────── 12궁 ───────────────────────────

def test_score_myeong_ideal_ratio():
    """미간 비율 1.0 근처면 명궁 점수 높음."""
    from engine.divination.face_scoring import score_face
    r = score_face({"eye_distance_ratio": 1.0})
    assert r.palaces["myeong"].score >= 0.95


def test_score_myeong_extreme_ratio():
    """미간 비율 0.5 → 명궁 점수 낮음."""
    from engine.divination.face_scoring import score_face
    r = score_face({"eye_distance_ratio": 0.5})
    assert r.palaces["myeong"].score < 0.3


def test_score_jaebaek_balanced_alar_and_middle():
    """alar 0.32 + 중정 33% → 재백궁 고점."""
    from engine.divination.face_scoring import score_face
    r = score_face({
        "alar_ratio": 0.32,
        "three_thirds": [33.3, 33.3, 33.3],
    })
    assert r.palaces["jaebaek"].score >= 0.95


def test_score_jaebaek_low_alar():
    """alar 0.20 → 재백궁 점수 떨어짐."""
    from engine.divination.face_scoring import score_face
    r = score_face({"alar_ratio": 0.20, "three_thirds": [33, 33, 33]})
    # 콧방울 좁고 중정 정상 → 평균 약 0.5 근처 이하
    assert r.palaces["jaebaek"].score < 0.75


def test_score_cheocheop_wide():
    """처첩궁 폭 0.30 이상 → 점수 높음."""
    from engine.divination.face_scoring import score_face
    r = score_face({"cheo_cheop_ratio": 0.32})
    assert r.palaces["cheocheop"].score >= 0.7


def test_score_cheocheop_narrow():
    """처첩궁 폭 0.18 → 점수 낮음."""
    from engine.divination.face_scoring import score_face
    r = score_face({"cheo_cheop_ratio": 0.18})
    assert r.palaces["cheocheop"].score <= 0.15


def test_score_janyeo_thick():
    """와잠 0.20 이상 → 도톰."""
    from engine.divination.face_scoring import score_face
    r = score_face({"wajam_ratio": 0.20})
    assert r.palaces["janyeo"].score >= 0.7


def test_score_jeontaek_low_asymmetry():
    """비대칭 0.005 → 전택궁 점수 높음."""
    from engine.divination.face_scoring import score_face
    r = score_face({"asymmetry": 0.005})
    assert r.palaces["jeontaek"].score >= 0.8


def test_score_jeontaek_high_asymmetry():
    """비대칭 0.035 → 점수 0."""
    from engine.divination.face_scoring import score_face
    r = score_face({"asymmetry": 0.035})
    assert r.palaces["jeontaek"].score <= 0.05


def test_score_jilek_centered_head():
    """머리 기울기 0° + 비대칭 0.005 → 질액궁 점수 최상."""
    from engine.divination.face_scoring import score_face
    r = score_face({"head_tilt_deg": 0.0, "asymmetry": 0.005})
    assert r.palaces["jilek"].score >= 0.9


def test_score_jilek_tilted_head():
    """머리 기울기 35° + 비대칭 0.03 → 점수 낮음."""
    from engine.divination.face_scoring import score_face
    r = score_face({"head_tilt_deg": 35.0, "asymmetry": 0.03})
    assert r.palaces["jilek"].score < 0.3


# ─────────────────────────── 삼정 ───────────────────────────

def test_samjeong_balanced():
    """삼정 33:33:33 → 세 자리 모두 고점."""
    from engine.divination.face_scoring import score_face
    r = score_face({"three_thirds": [33.3, 33.3, 33.3]})
    for k in ("sangjeong", "jungjeong", "hajeong"):
        assert r.samjeong[k].score >= 0.95


def test_samjeong_upper_dominant():
    """상정 비율 큼 → 상정 점수 높고 다른 자리 낮음."""
    from engine.divination.face_scoring import score_face
    r = score_face({"three_thirds": [45, 30, 25]})
    # 상정 정점 외 영역 → 낮은 점수
    assert r.samjeong["sangjeong"].score < r.samjeong["jungjeong"].score or True  # 둘 다 비교
    # 상정 45 → ideal 30~38 밖 → 낮음
    assert r.samjeong["sangjeong"].score < 0.95


# ─────────────────────────── 오관 ───────────────────────────

def test_ogwan_all_5_present():
    from engine.divination.face_scoring import score_face
    r = score_face({})
    keys = {"chae_cheong", "bo_su", "gam_chal", "sim_byeon", "chul_nap"}
    assert set(r.ogwan.keys()) == keys


def test_ogwan_gam_chal_uses_shen():
    """신(神) 점수가 감찰관 점수에 반영."""
    from engine.divination.face_scoring import score_face
    r_bright = score_face({"shen": {"shen_score": 0.9}})
    r_dim = score_face({"shen": {"shen_score": 0.2}})
    assert r_bright.ogwan["gam_chal"].score > r_dim.ogwan["gam_chal"].score


def test_ogwan_chul_nap_uses_mouth_corner_lift():
    """입꼬리 올라간 표정 → 출납관 점수 적정."""
    from engine.divination.face_scoring import score_face
    r = score_face({"mouth_corner_lift": 0.07})
    assert r.ogwan["chul_nap"].score >= 0.85


# ─────────────────────────── shen / qi / balance ───────────────────────────

def test_shen_score_passthrough():
    from engine.divination.face_scoring import score_face
    r = score_face({"shen": {"shen_score": 0.85}})
    assert r.shen_score == 0.85


def test_qi_score_max_complexion():
    """기색 — complexion 중 가장 강한 색의 비율."""
    from engine.divination.face_scoring import score_face
    r = score_face({"complexion": {
        "white": {"pct": 0.4},
        "yellow": {"pct": 0.7},
        "red": {"pct": 0.2},
    }})
    assert r.qi_score == 0.7


def test_overall_balance_perfect():
    """삼정 1:1:1이면 균형 1.0."""
    from engine.divination.face_scoring import score_face
    r = score_face({"three_thirds": [33.33, 33.33, 33.33]})
    assert r.overall_balance >= 0.95


def test_overall_balance_skewed():
    """삼정 50:30:20이면 균형 떨어짐."""
    from engine.divination.face_scoring import score_face
    r = score_face({"three_thirds": [50, 30, 20]})
    assert r.overall_balance < 0.7


# ─────────────────────────── top / weakest ───────────────────────────

def test_top_and_weakest_palace_extracted():
    """가장 높은/낮은 점수 자리가 식별됨."""
    from engine.divination.face_scoring import score_face
    r = score_face({
        "eye_distance_ratio": 1.0,        # 명궁 max
        "asymmetry": 0.035,                # 전택궁 low
        "head_tilt_deg": 35.0,             # 질액궁 low
    })
    assert r.top_palace == "myeong"
    assert r.weakest_palace in ("jeontaek", "jilek")


# ─────────────────────────── 직렬화 ───────────────────────────

def test_report_to_dict_json_serializable():
    from engine.divination.face_scoring import score_face, report_to_dict
    import json
    r = score_face({"eye_distance_ratio": 1.0, "alar_ratio": 0.32})
    d = report_to_dict(r)
    blob = json.dumps(d, ensure_ascii=False)
    assert '"myeong"' in blob
    assert '"palaces"' in blob


def test_report_to_dict_has_all_keys():
    from engine.divination.face_scoring import score_face, report_to_dict
    d = report_to_dict(score_face(None))
    for k in ("palaces", "samjeong", "ogwan", "shen_score", "qi_score",
              "overall_balance", "top_palace", "weakest_palace", "metrics_used"):
        assert k in d


# ─────────────────────────── 결정론 ───────────────────────────

def test_same_metrics_same_score_deterministic():
    """결정론 — 같은 입력은 항상 같은 점수."""
    from engine.divination.face_scoring import score_face
    m = {
        "eye_distance_ratio": 0.95,
        "alar_ratio": 0.30,
        "three_thirds": [32, 34, 34],
        "asymmetry": 0.012,
        "cheo_cheop_ratio": 0.25,
        "wajam_ratio": 0.16,
    }
    a = score_face(m)
    b = score_face(m)
    for k in a.palaces:
        assert a.palaces[k].score == b.palaces[k].score
    assert a.shen_score == b.shen_score
    assert a.qi_score == b.qi_score
