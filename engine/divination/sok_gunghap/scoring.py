"""ADR-158 — 야선 아씨 속궁합 결정론 + sanitize.

본 모듈은 두 사주(본인·상대) 일주·지지 기반 궁합 결정론 + 단정 어휘 차단.
LLM 응답 시 결정론 메타만 system prompt 주입 — 운명 단정 X.

원칙 (ADR-002·006·010 정합):
  · 결정론 점수만 산출 (45~85점, 별자리 144 매트릭스 패턴 정합)
  · 결혼·이혼·이별·재혼 단정 X (sanitize 차단)
  · 일주 매칭 + 지지 합·충 결정론 + 도화·홍염 시너지 (ADR-153)
  · 학파 단정 X — 합·충 모두 점성술 element 패턴으로 메타 분류
  · 면책 자동 포함
"""
from __future__ import annotations

import re
from dataclasses import dataclass


# ─────────────────────────── 일주 60갑자 ohaeng 매핑 ───────────────────────────

# 천간 오행 (간단 매핑 — 본 시스템 pillars 정합)
_GAN_OHAENG = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}
_JI_OHAENG = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

# 지지 6합 (지지끼리 결합)
_YUKHAP = {
    frozenset(["子", "丑"]): "土",
    frozenset(["寅", "亥"]): "木",
    frozenset(["卯", "戌"]): "火",
    frozenset(["辰", "酉"]): "金",
    frozenset(["巳", "申"]): "水",
    frozenset(["午", "未"]): "火",
}
# 지지 6충
_YUKCHUNG = {
    frozenset(["子", "午"]), frozenset(["丑", "未"]),
    frozenset(["寅", "申"]), frozenset(["卯", "酉"]),
    frozenset(["辰", "戌"]), frozenset(["巳", "亥"]),
}
# 도화 (지지) — 子午卯酉
_DOHWA = frozenset(["子", "午", "卯", "酉"])
# 홍염살 매핑 (일간별)
_HONGYEOM = {
    "甲": "午", "乙": "申", "丙": "寅", "丁": "未", "戊": "辰",
    "己": "辰", "庚": "戌", "辛": "酉", "壬": "子", "癸": "申",
}

# 오행 상생·상극
_SANGSAENG = {  # A → B 상생
    "木": "火", "火": "土", "土": "金", "金": "水", "水": "木",
}
_SANGGEUK = {  # A → B 상극
    "木": "土", "土": "水", "水": "火", "火": "金", "金": "木",
}


@dataclass(frozen=True)
class SokGunghapResult:
    """야선 아씨 속궁합 결정론 결과.

    ★ 의도적 부재 필드 (ADR-006 단정 차단):
      - marriage_outcome, breakup_risk, sexual_compat_score
      - financial_outcome, fertility_outcome
    """
    self_day_gan: str           # 본인 일간
    self_day_ji: str            # 본인 일지
    partner_day_gan: str        # 상대 일간
    partner_day_ji: str         # 상대 일지
    self_day_element: str       # 본인 일간 오행
    partner_day_element: str    # 상대 일간 오행
    gan_relation: str           # "동기" | "상생" | "상극" | "보완"
    ji_relations: tuple[str, ...]  # ["六合(火)", "六冲"] 등
    dohwa_count: int            # 도화 일치 개수 (시너지 메타)
    hongyeom_match: bool        # 홍염살 매칭 여부
    element_score: int          # 45~85 (element 호환)
    relation_score: int         # 45~85 (지지 관계)
    overall_score: int          # 가중 평균 (45~85)
    relation_type: str          # "deep_resonance" | "complementary" | "frictional_learning"
    tone_ko: str                # 흐름 톤 (단정 X)
    disclaimer: str


_DISCLAIMER = (
    "본 속궁합은 두 사주의 일주(日柱)·지지 관계 결정론 분류로, "
    "결혼·이혼·이별·재혼·외도 단정 X. 흐름의 결만 풀이. "
    "참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다."
)


def _gan_relation(g1: str, g2: str) -> str:
    """천간 오행 관계 분류."""
    e1, e2 = _GAN_OHAENG.get(g1, ""), _GAN_OHAENG.get(g2, "")
    if not e1 or not e2:
        return "unknown"
    if e1 == e2:
        return "동기 (同氣)"
    if _SANGSAENG.get(e1) == e2 or _SANGSAENG.get(e2) == e1:
        return "상생 (相生)"
    if _SANGGEUK.get(e1) == e2 or _SANGGEUK.get(e2) == e1:
        return "상극 (相剋)"
    return "보완 (補完)"


def _ji_relations(j1: str, j2: str) -> tuple[str, ...]:
    """지지 관계 (합·충) 추출."""
    out: list[str] = []
    pair = frozenset([j1, j2])
    if pair in _YUKHAP:
        out.append(f"六合({_YUKHAP[pair]})")
    if pair in _YUKCHUNG:
        out.append("六冲")
    return tuple(out)


def _element_score(rel: str) -> int:
    """천간 관계 → element 점수 (45~85)."""
    return {
        "동기 (同氣)": 80,
        "상생 (相生)": 78,
        "보완 (補完)": 65,
        "상극 (相剋)": 50,
    }.get(rel, 60)


def _relation_score(ji_rels: tuple[str, ...]) -> int:
    """지지 관계 점수 (45~85)."""
    if not ji_rels:
        return 60
    score = 60
    for r in ji_rels:
        if "六合" in r:
            score += 15
        elif "六冲" in r:
            score -= 5  # 충은 긴장이나 끌어당김 — 감점 최소
    return max(45, min(85, score))


def _relation_type(overall: int) -> str:
    if overall >= 75:
        return "deep_resonance"
    if overall >= 60:
        return "complementary"
    return "frictional_learning"


_TONES = {
    "deep_resonance": "깊은 공명 — 두 흐름이 같은 결로 흐르는 자리",
    "complementary": "보완의 결 — 다른 결이 서로를 채우는 흐름",
    "frictional_learning": "마찰의 결 — 차이가 학습이 되는 만남",
}


def compute_sok_gunghap(
    self_day: str,
    partner_day: str,
    self_branches: tuple[str, ...] | None = None,
    partner_branches: tuple[str, ...] | None = None,
) -> SokGunghapResult | None:
    """두 사주 일주 → 속궁합 결정론.

    Args:
        self_day: 본인 일주 ('庚午' 등 2자 한자)
        partner_day: 상대 일주
        self_branches: 본인 4지지 (도화·홍염 검출용, 선택)
        partner_branches: 상대 4지지

    Returns:
        SokGunghapResult 또는 None (입력 부정합)
    """
    if not (isinstance(self_day, str) and len(self_day) == 2):
        return None
    if not (isinstance(partner_day, str) and len(partner_day) == 2):
        return None

    g1, j1 = self_day[0], self_day[1]
    g2, j2 = partner_day[0], partner_day[1]

    if g1 not in _GAN_OHAENG or g2 not in _GAN_OHAENG:
        return None
    if j1 not in _JI_OHAENG or j2 not in _JI_OHAENG:
        return None

    gan_rel = _gan_relation(g1, g2)
    ji_rels = _ji_relations(j1, j2)
    elem_score = _element_score(gan_rel)
    rel_score = _relation_score(ji_rels)

    # 도화·홍염 시너지 메타 (지지 입력 시)
    dohwa_count = 0
    hongyeom_match = False
    if self_branches and partner_branches:
        all_jis = set(self_branches) | set(partner_branches)
        dohwa_count = sum(1 for j in all_jis if j in _DOHWA)
        target = _HONGYEOM.get(g1)
        if target and target in (partner_branches or ()):
            hongyeom_match = True
        else:
            target2 = _HONGYEOM.get(g2)
            if target2 and target2 in (self_branches or ()):
                hongyeom_match = True

    overall = round(elem_score * 0.6 + rel_score * 0.4)
    if hongyeom_match:
        overall = min(85, overall + 2)
    rt = _relation_type(overall)

    return SokGunghapResult(
        self_day_gan=g1,
        self_day_ji=j1,
        partner_day_gan=g2,
        partner_day_ji=j2,
        self_day_element=_GAN_OHAENG[g1],
        partner_day_element=_GAN_OHAENG[g2],
        gan_relation=gan_rel,
        ji_relations=ji_rels,
        dohwa_count=dohwa_count,
        hongyeom_match=hongyeom_match,
        element_score=elem_score,
        relation_score=rel_score,
        overall_score=overall,
        relation_type=rt,
        tone_ko=_TONES[rt],
        disclaimer=_DISCLAIMER,
    )


def format_sok_gunghap_for_prompt(r: SokGunghapResult) -> str:
    """Stage 2 시스템 프롬프트 주입용 결정론 메타."""
    ji_str = " · ".join(r.ji_relations) if r.ji_relations else "(중립)"
    return (
        f"[속궁합 결정론 — 두 사주 일주 매칭]\n"
        f"  · 본인 일주: {r.self_day_gan}{r.self_day_ji} ({r.self_day_element})\n"
        f"  · 상대 일주: {r.partner_day_gan}{r.partner_day_ji} ({r.partner_day_element})\n"
        f"  · 천간 관계: {r.gan_relation}\n"
        f"  · 지지 관계: {ji_str}\n"
        f"  · 도화 시너지: {r.dohwa_count}건 / 홍염 매칭: {'있음' if r.hongyeom_match else '없음'}\n"
        f"  · element 점수: {r.element_score} / relation 점수: {r.relation_score} / "
        f"종합: {r.overall_score}\n"
        f"  · 흐름 톤: {r.tone_ko}\n"
        f"[안전 장치 — ADR-006] 일주·합충·시너지 결정론만 사용. "
        f"결혼·이혼·이별·외도·재혼 단정 금지. 흐름 톤으로만 풀이.\n"
        f"{r.disclaimer}"
    )


# ─────────────────────────── ADR-158 sanitize — 속궁합 단정 어휘 차단 ───────────────────────────

# 결혼·이혼·이별·재혼·외도·궁합 점수 단정 어휘 차단.
_BANNED_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"반드시\s*결혼", "결혼은 두 분 선택의 결"),
    (r"확실히\s*결혼", "결혼은 흐름의 결로"),
    (r"이혼\s*할\s*것", "관계의 결은 두 분 선택에 달림"),
    (r"이혼\s*하게\s*된다", "관계의 결은 두 분 선택의 결"),
    (r"외도\s*할\s*것", "외도는 단정 X — 마음의 결만 묘사"),
    (r"바람\s*피울\s*것", "마음의 결은 두 분 선택의 결"),
    (r"바람\s*날\s*것", "흐름의 결은 두 분 선택"),
    (r"이별\s*할\s*것", "이별은 두 분 흐름의 결"),
    (r"헤어질\s*것", "관계 흐름은 두 분 선택"),
    (r"100%\s*궁합", "궁합은 흐름의 결로만"),
    (r"100점\s*궁합", "궁합 점수는 참고용"),
    (r"천생연분", "흐름이 닿는 결"),
    (r"운명\s*의\s*상대", "흐름이 닿는 분"),
    (r"불행\s*한\s*결혼", "결혼의 결은 두 분 선택"),
    (r"파탄", "흐름의 결"),
)


def sanitize_sok_gunghap_text(text: str) -> str:
    """ADR-158 — 속궁합 LLM 응답 단정 어휘 sanitize.

    결혼·이혼·외도·이별 단정 어휘를 흐름 톤 표현으로 치환.
    """
    if not isinstance(text, str) or not text:
        return text or ""
    out = text
    for pat, replacement in _BANNED_PATTERNS:
        out = re.sub(pat, replacement, out)
    return out


__all__ = [
    "SokGunghapResult",
    "compute_sok_gunghap",
    "format_sok_gunghap_for_prompt",
    "sanitize_sok_gunghap_text",
]
