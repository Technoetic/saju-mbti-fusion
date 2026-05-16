"""IRT (Imagery Rehearsal Therapy) — 악몽 재각본 6단계 워크플로.

출처:
  - Krakow & Zadra (2010) Behavioral Sleep Medicine 8(4)
  - AASM Position Paper (2018) Journal of Clinical Sleep Medicine 14(6)

만성 악몽(주 1회+ × 6개월+) 사용자에 자동 트리거.
앱의 핵심 임상 차별화 모듈.

6단계:
  1. 심리교육 (Psychoeducation)
  2. 악몽 기록 (Nightmare Recording, 7일)
  3. 표적 악몽 선택 (Target Selection)
  4. 재각본 생성 (Rescripting, AI 보조)
  5. 낮 시간 리허설 (Daytime Rehearsal, 2주)
  6. 효과 측정·재조정 (8주차 평가)
"""

from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field


IRT_LABEL = (
    "IRT (Imagery Rehearsal Therapy) — 악몽을 의식 상태에서 긍정적 결말로 "
    "재각본화하고 낮에 리허설하면 악몽 빈도가 통계적으로 감소 (AASM 2018 권고)."
)


# 만성 악몽 기준 — IRT 트리거
CHRONIC_NIGHTMARE_WEEKS_THRESHOLD = 26  # 6개월
CHRONIC_NIGHTMARE_FREQ_PER_WEEK = 1


# ─────────────────────────── Step 1: 심리교육 ───────────────────────────
PSYCHOEDUCATION_CONTENT_KO = """[심리교육 — IRT를 시작하기 전]

악몽은 운명도 신호도 아닙니다. 학습된 행동에 가깝습니다.
같은 결말로 반복된 꿈은 그 결말을 더 잘 학습하게 되고, 결국 자주 떠오릅니다.

좋은 소식: 같은 학습 원리로 결말을 의식적으로 다시 짤 수 있습니다.

본 워크플로는 다음 6단계를 안내합니다.
  1. 지금 이 안내 (당신은 여기에 있습니다)
  2. 7일간 악몽 기록 — 베이스라인 측정
  3. 가장 자주·강하게 나타나는 악몽 1개 선택
  4. 그 악몽의 결말을 긍정적으로 다시 쓰기 (AI 도움)
  5. 매일 낮 5~20분, 새 결말 시각화 (2주)
  6. 8주차 효과 측정

본 워크플로는 의료 치료가 아니며, 자가 도움 도구입니다.
자살·자해 생각이 있다면 즉시 1393(자살예방상담)으로 연락하십시오.

준비되셨다면 다음 단계로 진행할 수 있습니다."""


# ─────────────────────────── Step 4: 재각본 생성용 LLM 프롬프트 ───────────────────────────
RESCRIPTING_SYSTEM_KO = (
    "당신은 IRT(Imagery Rehearsal Therapy)의 재각본 보조 역할입니다.\n\n"
    "[필수 원칙 — Krakow & Zadra 매뉴얼 기반]\n"
    "  1. 결말을 긍정적으로 변경 (위협의 해소·구조·평화)\n"
    "  2. 사용자 통제력 회복 장면 삽입 (피해자 → 행위자)\n"
    "  3. 갑작스러운 반전 금지 — 사용자가 자연스럽게 받아들일 흐름\n"
    "  4. 폭력으로 폭력을 해소하지 말 것 (트라우마 재활성화 위험)\n"
    "  5. 의료 자문·진단 절대 금지\n"
    "  6. 사용자가 한국어로 시각화할 수 있는 구체적 감각 묘사 (시각·청각·촉감)\n\n"
    "[출력 형식]\n"
    "  • 3개 안 (안1·안2·안3), 각 200~350자\n"
    "  • 마크다운 없이 자연 문장\n"
    "  • 각 안 끝에 '— 통제 회복 포인트: ~~' 한 줄 명시\n\n"
    "[안전 규칙]\n"
    "  • 사용자가 묘사한 가해자·위협을 인격적으로 비하하지 않을 것\n"
    "  • 자살·자해·약물 키워드가 입력에 있으면 재각본 생성을 거부하고 1393 안내"
)


@dataclass
class IRTSession:
    """IRT 6단계 세션 상태."""
    user_id: str
    started_at_iso: str | None = None
    current_step: int = 1

    # Step 2: 베이스라인 (7일)
    baseline_nightmares: list[dict[str, Any]] = field(default_factory=list)

    # Step 3: 표적 악몽
    target_nightmare_text: str | None = None
    target_chars: list[str] = field(default_factory=list)
    target_settings: list[str] = field(default_factory=list)
    target_activities: list[str] = field(default_factory=list)

    # Step 4: 재각본
    rescripted_options: list[str] = field(default_factory=list)
    chosen_rescript: str | None = None

    # Step 5: 리허설 로그
    rehearsal_log: list[dict[str, Any]] = field(default_factory=list)

    # Step 6: 결과
    outcome_report: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "started_at_iso": self.started_at_iso,
            "current_step": self.current_step,
            "baseline_nightmares": self.baseline_nightmares,
            "target_nightmare_text": self.target_nightmare_text,
            "rescripted_options": self.rescripted_options,
            "chosen_rescript": self.chosen_rescript,
            "rehearsal_log_count": len(self.rehearsal_log),
            "outcome_report": self.outcome_report,
        }


# ─────────────────────────── 함수형 API ───────────────────────────
def should_trigger_irt(
    nightmare_freq_per_week: int | None,
    weeks_duration: int | None,
) -> dict[str, Any]:
    """IRT 자동 트리거 판정."""
    if nightmare_freq_per_week is None or weeks_duration is None:
        return {"trigger": False, "reason": "악몽 빈도·기간 미입력"}
    if (
        nightmare_freq_per_week >= CHRONIC_NIGHTMARE_FREQ_PER_WEEK
        and weeks_duration >= CHRONIC_NIGHTMARE_WEEKS_THRESHOLD
    ):
        return {
            "trigger": True,
            "reason": (
                f"만성 악몽 기준 충족 — 주 {nightmare_freq_per_week}회 × "
                f"{weeks_duration}주 (AASM 2018: 주 1회+ × 6개월+)"
            ),
            "recommended_action": "IRT 6단계 워크플로 시작 권장",
        }
    return {
        "trigger": False,
        "reason": (
            f"주 {nightmare_freq_per_week}회 × {weeks_duration}주 — "
            "만성 악몽 기준 미달. 일반 해몽으로 진행."
        ),
    }


def generate_rescripted_endings(
    nightmare_text: str,
    *,
    safety_pre_check: bool = True,
) -> dict[str, Any]:
    """LLM에 재각본 3안 생성 요청.

    Args:
        nightmare_text: 사용자가 선택한 표적 악몽 narrative
        safety_pre_check: 자살/자해 키워드 사전 검사 (기본 True)
    """
    from engine.llm_sync import call_llm_sync
    from engine.safety import detect_crisis, CRISIS_RESPONSE_KO, build_legal_footer

    if safety_pre_check:
        crisis = detect_crisis(nightmare_text)
        if crisis["crisis_detected"]:
            return {
                "options": [],
                "crisis_alert": crisis,
                "text": CRISIS_RESPONSE_KO + build_legal_footer(is_crisis=True),
                "blocked": True,
            }

    user = (
        f"[표적 악몽 — 사용자가 재각본을 원하는 꿈]\n"
        f"{nightmare_text.strip()}\n\n"
        f"위 악몽의 결말을 IRT 원칙에 따라 다시 작성한 3안을 생성하십시오. "
        f"각 안은 사용자가 시각화할 수 있는 구체 묘사를 포함하고, "
        f"끝에 '— 통제 회복 포인트: ~~'를 명시하십시오."
    )
    try:
        text = call_llm_sync(user_text=user, system_prompt=RESCRIPTING_SYSTEM_KO)
    except Exception as e:
        return {
            "options": [],
            "text": f"(재각본 생성 실패: {e})",
            "blocked": False,
        }

    # 안1·안2·안3 분리 (단순 패턴)
    import re
    # "안1", "안2", "안3" 또는 "1.", "2.", "3." 기준 분할
    parts = re.split(r"(?:^|\n)(?:안\s*\d|\d+\.)\s*", text)
    options = [p.strip() for p in parts if p.strip() and len(p.strip()) > 20]
    if len(options) < 2:
        # 분할 실패 시 통째로
        options = [text.strip()]

    return {
        "options": options[:3],
        "raw_text": text,
        "blocked": False,
        "instruction": "위 3안 중 가장 자연스럽게 느껴지는 안을 선택하시고, 자유롭게 수정하셔도 됩니다.",
        "legal_notice": build_legal_footer(),
    }


def evaluate_outcome(
    baseline_freq_per_week: float,
    week8_freq_per_week: float,
    baseline_psqi: int | None = None,
    week8_psqi: int | None = None,
    baseline_ces_d: int | None = None,
    week8_ces_d: int | None = None,
) -> dict[str, Any]:
    """Step 6 — 8주차 효과 측정.

    KPI:
        - 악몽 빈도 -50%↓
        - PSQI -1점
        - CES-D -3점
    """
    nightmare_reduction = (
        round((baseline_freq_per_week - week8_freq_per_week) / baseline_freq_per_week * 100, 1)
        if baseline_freq_per_week > 0
        else 0.0
    )
    met_nightmare_kpi = nightmare_reduction >= 50.0

    met_psqi_kpi = None
    psqi_delta = None
    if baseline_psqi is not None and week8_psqi is not None:
        psqi_delta = week8_psqi - baseline_psqi
        met_psqi_kpi = psqi_delta <= -1

    met_ces_d_kpi = None
    ces_d_delta = None
    if baseline_ces_d is not None and week8_ces_d is not None:
        ces_d_delta = week8_ces_d - baseline_ces_d
        met_ces_d_kpi = ces_d_delta <= -3

    success_count = sum(1 for v in [met_nightmare_kpi, met_psqi_kpi, met_ces_d_kpi] if v)
    total_measured = sum(1 for v in [met_nightmare_kpi, met_psqi_kpi, met_ces_d_kpi] if v is not None)

    if success_count == total_measured and total_measured > 0:
        verdict = "목표 달성"
        next_step = "유지 단계로 전환 — 월 1회 점검"
    elif success_count >= 1:
        verdict = "부분 달성"
        next_step = "표적 악몽을 재선정하여 Step 3부터 재시작 권장"
    else:
        verdict = "목표 미달"
        next_step = (
            "악몽 빈도 미감소 + CES-D ≥ 16점 동반 시 정신건강의학과 의뢰. "
            "1393(자살예방상담) 또는 1577-0199(정신건강위기상담) 활용."
        )

    return {
        "nightmare_reduction_pct": nightmare_reduction,
        "met_nightmare_kpi": met_nightmare_kpi,
        "psqi_delta": psqi_delta,
        "met_psqi_kpi": met_psqi_kpi,
        "ces_d_delta": ces_d_delta,
        "met_ces_d_kpi": met_ces_d_kpi,
        "success_count": success_count,
        "total_measured": total_measured,
        "verdict": verdict,
        "next_step": next_step,
    }


__all__ = [
    "IRT_LABEL",
    "CHRONIC_NIGHTMARE_WEEKS_THRESHOLD",
    "CHRONIC_NIGHTMARE_FREQ_PER_WEEK",
    "PSYCHOEDUCATION_CONTENT_KO",
    "RESCRIPTING_SYSTEM_KO",
    "IRTSession",
    "should_trigger_irt",
    "generate_rescripted_endings",
    "evaluate_outcome",
]
