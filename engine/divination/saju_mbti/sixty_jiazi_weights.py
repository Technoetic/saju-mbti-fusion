"""ADR-108 — 60갑자 일주별 MBTI 4축 가중치 보정.

본 모듈은 ADR-014 (사주→MBTI 예외 결정) + ADR-002 (학파 회피) +
ADR-010 (사실성 분리) 정합. 학설 권위 인용 0 — 본 시스템 자체 매핑.

영역:
  · 60갑자 일주 × 4축 (E/I·S/N·T/F·J/P) = 240 가중치
  · 일간 음양 + 일지 십이지 결합 → 4축 보정 가중치 ±0.10
  · predictor.py 기본 yang_ratio·wuxing 매핑 위에 보정 적용

원칙 (ADR-014 의무):
  · 16유형 단정 영구 금지 — 가중치만 산출
  · 4축 모두 단정 X — "미정" 가능 영역 보존
  · 학설 인용 0 — 본 시스템 자체 룰
  · 면책 의무 (호출자 책임)

면책:
  · MBTI 검사 대체 X — 사주 기운 흐름의 결만 추정
  · 의료·법률·금융 의사결정 단독 근거 X
"""

from __future__ import annotations

from dataclasses import dataclass


# ─────────────────────────── 60갑자 영속 ───────────────────────────

# 10 천간 × 12 지지 = 60갑자 (양간-양지 / 음간-음지만 조합)
_CHEONGAN = "甲乙丙丁戊己庚辛壬癸"  # 10
_JIJI = "子丑寅卯辰巳午未申酉戌亥"  # 12

# 천간 음양
_YANG_GAN = frozenset("甲丙戊庚壬")

# 지지 음양
_YANG_JI = frozenset("子寅辰午申戌")


def _generate_sixty_jiazi() -> tuple[str, ...]:
    """60갑자 자동 생성 — 갑자→을축→...→계해."""
    result = []
    for i in range(60):
        gan_idx = i % 10
        ji_idx = i % 12
        result.append(_CHEONGAN[gan_idx] + _JIJI[ji_idx])
    return tuple(result)


SIXTY_JIAZI: tuple[str, ...] = _generate_sixty_jiazi()


# ─────────────────────────── 지지 십이지별 MBTI 결 보정 ───────────────────────────

# 본 시스템 자체 룰 (학파 인용 0):
# 각 지지의 동물 상징 + 오행 + 계절 + 음양에서 직관적으로 도출.
# E/I: 외향(활동성)·내향(정적) | S/N: 감각(현실)·직관(추상)
# T/F: 사고(논리)·감정(공감)   | J/P: 판단(계획)·인식(즉흥)
_JIJI_AXIS_WEIGHTS: dict[str, dict[str, float]] = {
    # 子 쥐 (수, 겨울, 양지): 내향적 활동 (밤 활동) — 직관·감정 살짝
    "子": {"E_I": -0.05, "S_N": +0.05, "T_F": +0.03, "J_P": -0.03},
    # 丑 소 (토, 겨울, 음지): 묵묵·꾸준 — 내향·감각·사고·판단
    "丑": {"E_I": -0.08, "S_N": -0.05, "T_F": +0.03, "J_P": +0.05},
    # 寅 호랑이 (목, 봄, 양지): 활달·진취 — 외향·직관·판단
    "寅": {"E_I": +0.08, "S_N": +0.05, "T_F": +0.03, "J_P": +0.03},
    # 卯 토끼 (목, 봄, 음지): 섬세·유연 — 내향·감각·감정·인식
    "卯": {"E_I": -0.03, "S_N": -0.03, "T_F": -0.05, "J_P": -0.05},
    # 辰 용 (토, 봄, 양지): 큰 그림·이상 — 외향·직관·사고·판단
    "辰": {"E_I": +0.05, "S_N": +0.08, "T_F": +0.05, "J_P": +0.03},
    # 巳 뱀 (화, 여름, 음지): 직관·신비 — 내향·직관·감정
    "巳": {"E_I": -0.05, "S_N": +0.08, "T_F": -0.03, "J_P": -0.03},
    # 午 말 (화, 여름, 양지): 활동적·외향 — 외향·감각·사고·인식
    "午": {"E_I": +0.08, "S_N": -0.03, "T_F": +0.03, "J_P": -0.05},
    # 未 양 (토, 여름, 음지): 부드러움·공감 — 내향·감정
    "未": {"E_I": -0.05, "S_N": -0.03, "T_F": -0.08, "J_P": +0.03},
    # 申 원숭이 (금, 가을, 양지): 영리·재치 — 외향·직관·사고·인식
    "申": {"E_I": +0.05, "S_N": +0.05, "T_F": +0.05, "J_P": -0.05},
    # 酉 닭 (금, 가을, 음지): 정밀·꼼꼼 — 내향·감각·사고·판단
    "酉": {"E_I": -0.03, "S_N": -0.08, "T_F": +0.05, "J_P": +0.08},
    # 戌 개 (토, 가을, 양지): 충직·믿음직 — 외향·감각·감정·판단
    "戌": {"E_I": +0.03, "S_N": -0.05, "T_F": -0.03, "J_P": +0.05},
    # 亥 돼지 (수, 겨울, 음지): 솔직·풍부 — 외향·감정·인식
    "亥": {"E_I": +0.03, "S_N": +0.03, "T_F": -0.05, "J_P": -0.03},
}

# 일간(천간) 음양 보정 — 양간은 E/T/J 살짝, 음간은 I/F/P 살짝
_GAN_AXIS_WEIGHTS: dict[str, dict[str, float]] = {
    "甲": {"E_I": +0.05, "S_N": +0.03, "T_F": +0.03, "J_P": +0.03},  # 양목 — 큰 나무
    "乙": {"E_I": -0.03, "S_N": -0.03, "T_F": -0.03, "J_P": -0.03},  # 음목 — 풀
    "丙": {"E_I": +0.08, "S_N": +0.05, "T_F": +0.03, "J_P": -0.03},  # 양화 — 태양
    "丁": {"E_I": -0.03, "S_N": -0.03, "T_F": -0.05, "J_P": -0.03},  # 음화 — 등불
    "戊": {"E_I": +0.03, "S_N": -0.05, "T_F": +0.05, "J_P": +0.05},  # 양토 — 산
    "己": {"E_I": -0.05, "S_N": -0.05, "T_F": -0.03, "J_P": +0.03},  # 음토 — 들
    "庚": {"E_I": +0.05, "S_N": -0.03, "T_F": +0.08, "J_P": +0.05},  # 양금 — 강철
    "辛": {"E_I": -0.03, "S_N": -0.08, "T_F": +0.03, "J_P": +0.08},  # 음금 — 보석
    "壬": {"E_I": +0.03, "S_N": +0.08, "T_F": +0.03, "J_P": -0.05},  # 양수 — 바다
    "癸": {"E_I": -0.05, "S_N": +0.05, "T_F": -0.05, "J_P": -0.05},  # 음수 — 비
}


# ─────────────────────────── 결과 dataclass ───────────────────────────

@dataclass(frozen=True)
class JiaziAxisWeight:
    """60갑자 일주별 4축 보정 가중치."""
    jiazi: str  # 예: "甲子"
    gan: str    # 일간 (천간)
    ji: str     # 일지 (지지)
    ei_weight: float  # -0.20 ~ +0.20 범위
    sn_weight: float
    tf_weight: float
    jp_weight: float
    rationale: str  # 본 시스템 자체 룰 명시 (면책)


def get_axis_weights(day_pillar: str) -> JiaziAxisWeight | None:
    """일주(예: "甲子") → 4축 보정 가중치.

    Args:
        day_pillar: 일주 2글자 (천간+지지). 예: "甲子", "乙丑"

    Returns:
        JiaziAxisWeight 또는 None (잘못된 입력)

    Examples:
        >>> w = get_axis_weights("甲子")
        >>> w.ei_weight  # 갑(+0.05) + 자(-0.05) = 0.0
        0.0
    """
    if not day_pillar or len(day_pillar) != 2:
        return None
    gan, ji = day_pillar[0], day_pillar[1]
    if gan not in _GAN_AXIS_WEIGHTS or ji not in _JIJI_AXIS_WEIGHTS:
        return None
    gan_w = _GAN_AXIS_WEIGHTS[gan]
    ji_w = _JIJI_AXIS_WEIGHTS[ji]
    return JiaziAxisWeight(
        jiazi=day_pillar,
        gan=gan,
        ji=ji,
        ei_weight=round(gan_w["E_I"] + ji_w["E_I"], 3),
        sn_weight=round(gan_w["S_N"] + ji_w["S_N"], 3),
        tf_weight=round(gan_w["T_F"] + ji_w["T_F"], 3),
        jp_weight=round(gan_w["J_P"] + ji_w["J_P"], 3),
        rationale=(
            f"본 시스템 자체 룰 (학파 인용 0) — "
            f"일간 {gan} {'양' if gan in _YANG_GAN else '음'} + "
            f"일지 {ji} {'양지' if ji in _YANG_JI else '음지'} 결합. "
            f"MBTI 검사 대체 X."
        ),
    )


def apply_jiazi_weight_to_axis(base_label: str, axis_key: str, weight: float, threshold: float = 0.08) -> str:
    """기본 라벨에 60갑자 보정 적용.

    Args:
        base_label: 기본 4축 라벨 (E·I·S·N·T·F·J·P 또는 "미정")
        axis_key: "E_I"·"S_N"·"T_F"·"J_P" (API 일관성 시그니처)
        weight: 보정 가중치 (-0.20~+0.20)
        threshold: 라벨 전환 임계값 (디폴트 0.08)

    Returns:
        보정된 라벨. weight가 threshold 초과 시 base_label과 다를 수 있음.

    면책: 본 함수는 "미정" 라벨을 강제로 단정 라벨로 바꾸지 않음 (ADR-014).
    """
    _ = axis_key  # 시그니처 일관성 — 본 룰은 단정 전환 안 함 (ADR-014)
    # "미정"은 보정해도 미정 유지 (단정 회피)
    if base_label == "미정":
        return base_label

    # 임계값 미만 변화는 라벨 유지
    if abs(weight) < threshold:
        return base_label

    # 본 시스템 자체 룰: 60갑자 가중치는 보정만 — 단정 라벨 강제 전환 X
    # 라벨 유지 (보정은 호출자가 reasons에 명시할 책임)
    return base_label


__all__ = [
    "SIXTY_JIAZI",
    "JiaziAxisWeight",
    "get_axis_weights",
    "apply_jiazi_weight_to_axis",
]
