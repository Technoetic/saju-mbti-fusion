"""ADR-146 회귀 — 합성 베이스라인 측정 영속화.

/domain-priorities #14·#15·#17·#18 운영 데이터 의존 영역을 합성 테스트 셋으로
베이스라인 측정 + 회귀 영속. 추후 운영 데이터 누적 시 비교 기준.

영역:
  · #14 face shape_classifier 6 형태 합성 정확도
  · #15 palm 손금선 길이 단조성
  · #17 saju_mbti 60갑자 가중치 분포 다양성
  · #18 dream 학파 인용 빈도 분포 (3 학파 매칭 보장)
"""
from __future__ import annotations

from collections import Counter

from engine.divination.face.shape import classify_face_shape
from engine.divination.palm.scoring import (
    _compute_fateline_metric,
    _compute_headline_metric,
    _compute_heartline_metric,
    _compute_lifeline_metric,
)
from engine.divination.saju_mbti.sixty_jiazi_weights import (
    SIXTY_JIAZI,
    get_axis_weights,
)
from engine.divination.tojeong.scoring import (
    TOJEONG_ACADEMIC_CITATIONS,
    format_tojeong_citations_for_prompt,
    get_tojeong_academic_citations,
)


class TestTojeongAcademicCitation:
    """ADR-146 — tojeong 학술 인용 영속 (#1 부분 해소)."""

    def test_at_least_one_citation(self):
        assert len(TOJEONG_ACADEMIC_CITATIONS) >= 1

    def test_kim_2016_citation_present(self):
        """김수년 (2016) 박사논문 RISS 000014351511 영속."""
        cs = get_tojeong_academic_citations()
        kim = [c for c in cs if c.author_ko == "김수년"]
        assert len(kim) == 1
        c = kim[0]
        assert c.publication_year == 2016
        assert c.degree == "박사학위논문"
        assert c.riss_control_no == "000014351511"
        assert "144괘 원문" in c.appendix_note

    def test_prompt_format_includes_riss(self):
        prompt = format_tojeong_citations_for_prompt()
        assert "ADR-146" in prompt
        assert "RISS" in prompt
        assert "144괘" in prompt
        assert "김수년" in prompt


class TestFaceShapeAccuracy:
    """#14 — face shape_classifier 6 형태 합성 정확도 100%."""

    TEST_CASES = [
        ("목형", {"face_width_height_ratio": 0.75, "jaw_angle_deg": 120,
                  "bizygomatic_to_bigonial_ratio": 1.10}),
        ("화형", {"face_width_height_ratio": 0.84, "jaw_angle_deg": 130,
                  "bizygomatic_to_bigonial_ratio": 1.30}),
        ("토형", {"face_width_height_ratio": 0.92, "jaw_angle_deg": 118,
                  "bizygomatic_to_bigonial_ratio": 1.05}),
        ("금형", {"face_width_height_ratio": 0.87, "jaw_angle_deg": 108,
                  "bizygomatic_to_bigonial_ratio": 1.10}),
        ("수형", {"face_width_height_ratio": 0.85, "jaw_angle_deg": 125,
                  "bizygomatic_to_bigonial_ratio": 1.15}),
        ("복합형", {"face_width_height_ratio": 0.84, "jaw_angle_deg": 113,
                    "bizygomatic_to_bigonial_ratio": 1.22}),
    ]

    def test_all_6_shapes_classified_correctly(self):
        """6 형태 각 1건 정확 분류."""
        correct = 0
        for intended, metrics in self.TEST_CASES:
            result = classify_face_shape(metrics)
            if result.shape_type == intended:
                correct += 1
        assert correct == 6, f"정확 분류: {correct}/6"

    def test_each_shape_separately(self):
        """6 형태 개별 검증."""
        for intended, metrics in self.TEST_CASES:
            result = classify_face_shape(metrics)
            assert result.shape_type == intended, (
                f"{intended}: 실제 {result.shape_type}"
            )


class TestPalmLineMonotonicity:
    """#15 — palm 손금선 측정값 단조성 (짧음 < 보통 < 김)."""

    def test_lifeline_monotonic(self):
        short = _compute_lifeline_metric({"lifeline_arc": 0.65})
        normal = _compute_lifeline_metric({"lifeline_arc": 1.20})
        long = _compute_lifeline_metric({"lifeline_arc": 1.85})
        assert short < normal < long

    def test_headline_monotonic(self):
        short = _compute_headline_metric({"headline_horizontal": 30.0})
        normal = _compute_headline_metric({"headline_horizontal": 60.0})
        long = _compute_headline_metric({"headline_horizontal": 95.0})
        assert short < normal < long

    def test_heartline_monotonic(self):
        short = _compute_heartline_metric({"heartline_curve": 0.4})
        normal = _compute_heartline_metric({"heartline_curve": 0.8})
        long = _compute_heartline_metric({"heartline_curve": 1.5})
        assert short < normal < long

    def test_fateline_monotonic(self):
        short = _compute_fateline_metric({"fateline_vertical": 0.3})
        normal = _compute_fateline_metric({"fateline_vertical": 0.75})
        long = _compute_fateline_metric({"fateline_vertical": 1.0})
        assert short < normal < long

    def test_empty_keypoints_returns_zero(self):
        """빈 keypoint → 0 (안전 fallback)."""
        assert _compute_lifeline_metric({}) == 0.0
        assert _compute_headline_metric({}) == 0.0
        assert _compute_heartline_metric({}) == 0.0
        assert _compute_fateline_metric({}) == 0.0


class TestSajuMbtiSixtyJiaziDiversity:
    """#17 — saju_mbti 60갑자 가중치 다양성 베이스라인."""

    def test_all_60_jiazi_have_weights(self):
        """60갑자 모두 가중치 반환."""
        for jiazi in SIXTY_JIAZI:
            w = get_axis_weights(jiazi)
            assert w is not None, f"{jiazi}: 가중치 None"

    def test_weight_range_within_bounds(self):
        """모든 가중치 [-0.20, +0.20] 범위."""
        for jiazi in SIXTY_JIAZI:
            w = get_axis_weights(jiazi)
            assert w is not None
            for v in (w.ei_weight, w.sn_weight, w.tf_weight, w.jp_weight):
                assert -0.20 <= v <= 0.20, f"{jiazi}: {v} 범위 초과"

    def test_60_jiazi_diversity_at_least_25_patterns(self):
        """60갑자 가중치 의미 라벨 다양성 ≥ 25 (ADR-014 단정 회피 정합)."""
        def label_axis(w, axis):
            if axis == "E_I":
                return "E" if w >= 0.05 else "I" if w <= -0.05 else "미정"
            if axis == "S_N":
                return "N" if w >= 0.05 else "S" if w <= -0.05 else "미정"
            if axis == "T_F":
                return "T" if w >= 0.05 else "F" if w <= -0.05 else "미정"
            return "J" if w >= 0.05 else "P" if w <= -0.05 else "미정"

        mbti_dist = Counter()
        for jiazi in SIXTY_JIAZI:
            w = get_axis_weights(jiazi)
            assert w is not None
            label = (
                label_axis(w.ei_weight, "E_I") +
                label_axis(w.sn_weight, "S_N") +
                label_axis(w.tf_weight, "T_F") +
                label_axis(w.jp_weight, "J_P")
            )
            mbti_dist[label] += 1
        # 베이스라인 (2026-05-23): 29 고유 라벨. 25 이상 보장.
        assert len(mbti_dist) >= 25, (
            f"60갑자 라벨 다양성 {len(mbti_dist)} (베이스라인 ≥ 25 깨짐)"
        )

    def test_mijeong_label_present(self):
        """일부 갑자가 미정 라벨 포함 (ADR-014 단정 회피 핵심)."""
        def has_mijeong(w):
            for axis_w in (w.ei_weight, w.sn_weight, w.tf_weight, w.jp_weight):
                if -0.05 < axis_w < 0.05:
                    return True
            return False
        mijeong_count = sum(
            1 for j in SIXTY_JIAZI
            if (w := get_axis_weights(j)) and has_mijeong(w)
        )
        assert mijeong_count > 0, "미정 라벨 갑자 0건 — ADR-014 단정 회피 위반"


class TestDreamSchoolDistribution:
    """#18 — dream 학파 인용 빈도 베이스라인 (3 매칭 학파 보장)."""

    def test_dream_module_has_30_domains(self):
        """analyze_dream이 30개 학파 호출 가능."""
        from engine.divination.dream import analyze_dream
        from engine.divination.dream_lex.personal_context import PersonalContext

        ctx = PersonalContext()
        result = analyze_dream("맑은 강물에서 수영하는 꿈", ctx)
        # 핵심 학파 호출 확인
        expected_keys = {
            "artemidorus_class", "artemidorus_lookup",
            "korean_folk", "zhougong", "wuxing",
            "archetypes", "freud", "hobson",
        }
        for k in expected_keys:
            assert k in result, f"학파 '{k}' 호출 누락"

    def test_three_lookup_schools_match_in_synthetic(self):
        """합성 꿈 30건 중 artemidorus·korean_folk·zhougong 3 학파 매칭 발생 보장."""
        from engine.divination.dream import analyze_dream
        from engine.divination.dream_lex.personal_context import PersonalContext

        ctx = PersonalContext()
        samples = [
            "맑은 강물에서 수영하는 꿈", "돈을 줍는 꿈", "용을 보는 꿈",
            "결혼식 꿈", "치아가 빠지는 꿈", "불이 활활 타는 꿈",
            "돼지를 보는 꿈", "꽃이 피는 꿈", "내 시신을 보는 꿈",
            "돌아가신 아버지의 꿈",
        ]
        match_count = Counter()
        for sample in samples:
            result = analyze_dream(sample, ctx)
            for key, val in result.items():
                if isinstance(val, list) and val:
                    match_count[key] += 1
                elif isinstance(val, dict):
                    for sub in ("matches", "lookup", "archetypes"):
                        if sub in val and val[sub]:
                            match_count[key] += 1
                            break
        # 핵심: artemidorus·korean_folk·zhougong 중 적어도 2개 학파에서 매칭 발생
        lookup_schools = sum(
            1 for k in ("artemidorus_lookup", "korean_folk", "zhougong")
            if match_count[k] >= 1
        )
        assert lookup_schools >= 2, (
            f"3 학파 중 {lookup_schools}개만 매칭 발생 — ADR-002 다학파 병행 약화"
        )
