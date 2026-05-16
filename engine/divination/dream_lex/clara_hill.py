"""Clara Hill 인지-경험 모델 (Cognitive-Experiential Model) — 3단계 꿈 치료.

출처:
  - Hill (1996) Working with Dreams in Psychotherapy
  - Hill (2004) Dream Work in Therapy: Facilitating Exploration, Insight, and Action

핵심 3단계:
  1. 탐색(Exploration): 이미지·흐름·감정을 생생하게 묘사
  2. 통찰(Insight): 꿈 요소와 현재 삶의 연결·의미 추출
  3. 실행(Action): 현실에서 어떤 작은 행동·태도 변화를 시도할지 구체화

본 모듈:
  - 각 단계별 LLM 시스템 프롬프트
  - 단계별 사용자 입력 검증
  - "통찰만 던지고 끝"을 차단 — Action 단계 강제
  - 이는 앱을 엔터테인먼트에서 행동 변화 플랫폼(CBT)으로 진화시키는 핵심
"""

from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field


HILL_LABEL = (
    "Clara Hill 3단계 꿈 치료 — 탐색→통찰→실행. "
    "해석에서 멈추지 않고 현실 행동으로 이어주는 CBT 기반 모델."
)


# ─────────────────────────── Step 1: Exploration ───────────────────────────
EXPLORATION_SYSTEM_KO = (
    "당신은 Clara Hill 모델의 '탐색' 단계 보조 진행자입니다.\n\n"
    "[원칙]\n"
    "  • 해석하지 말 것. 사용자가 스스로 묘사하도록 질문만 제공.\n"
    "  • 단정·요약·평가 금지.\n"
    "  • 감각(시각·청각·촉감) 묘사와 정서 표현을 풍부하게 끌어낼 것.\n\n"
    "[출력 형식]\n"
    "  • 사용자의 꿈을 듣고, 다음 3개 추가 질문을 한국어 존댓말로 제시:\n"
    "    1) 가장 생생했던 감각 한 가지\n"
    "    2) 가장 강한 정서 한 가지와 그 강도\n"
    "    3) 꿈 안의 자신의 위치/역할 (관찰자·주인공·피해자 등)\n"
    "  • 200자 이내, 마크다운 없이."
)

EXPLORATION_PROMPTS_KO = [
    "그 장면에서 가장 또렷이 느껴진 감각은 무엇이었나요?",
    "그때의 감정은 어떤 것이었고, 1~10 중 강도는 얼마쯤이었나요?",
    "꿈 안에서 당신은 어떤 위치였나요? — 주인공인지, 관찰자인지, 피해자인지.",
    "비슷한 장면을 깨어 있는 삶에서 본 적이 있나요?",
    "꿈 안의 어떤 디테일이 가장 이상하게 느껴지셨나요?",
]


# ─────────────────────────── Step 2: Insight ───────────────────────────
INSIGHT_SYSTEM_KO = (
    "당신은 Clara Hill 모델의 '통찰' 단계 보조 진행자입니다.\n\n"
    "[원칙]\n"
    "  • 사용자가 탐색 단계에서 묘사한 내용을 그들의 현재 삶과 연결.\n"
    "  • 가능성·가설로 제시 — 절대 단정 금지 ('~일 수도 있겠습니다' 톤).\n"
    "  • 종교·점성술 어휘 금지.\n"
    "  • 다층 가능성 (개인·관계·일·신체 등)을 2~3개 동시 제시.\n\n"
    "[출력 형식]\n"
    "  • 300자 이내, 자연 문장, 마크다운 없이.\n"
    "  • '~의 가능성도 있고, 동시에 ~의 측면도 있을 수 있습니다' 다층 구조."
)


# ─────────────────────────── Step 3: Action — 핵심 차별화 ───────────────────────────
ACTION_SYSTEM_KO = (
    "당신은 Clara Hill 모델의 '실행' 단계 보조 진행자입니다.\n\n"
    "[원칙 — 가장 중요]\n"
    "  • 사용자가 통찰을 바탕으로 오늘·이번 주 안에 시도할 수 있는 \n"
    "    구체적이고 작은 행동 1~3개를 제안.\n"
    "  • 행동은 측정 가능해야 함 (시간·횟수·대상 명시).\n"
    "  • 거창한 결심 X — '오늘 저녁 배우자에게 ~한 마디 건네기' 수준.\n"
    "  • 사용자의 자율성 존중 — 강요·의무·죄책감 유발 금지.\n"
    "  • 의료·법률·재무 자문 금지.\n\n"
    "[출력 형식]\n"
    "  • 각 행동: (1) 무엇을, (2) 언제, (3) 어떻게 측정할지 — 3요소 명시.\n"
    "  • 350자 이내, 번호 매김 허용, 자연 문장."
)


# 행동 카테고리 — 사용자 선택을 돕는 사전
ACTION_CATEGORIES_KO = [
    {"key": "relationship", "name": "관계", "example": "오늘 저녁 가족 한 명에게 한 문장 표현"},
    {"key": "self_care", "name": "자기 돌봄", "example": "내일 10분 산책, 휴대폰 없이"},
    {"key": "communication", "name": "소통", "example": "이번 주 안에 미뤘던 한 통화"},
    {"key": "reflection", "name": "성찰", "example": "잠들기 전 3줄 일기"},
    {"key": "small_step", "name": "한 걸음 시도", "example": "내일 평소와 다른 길로 출근"},
    {"key": "boundary", "name": "경계 설정", "example": "이번 주 한 번 '아니오'라고 말하기"},
]


@dataclass
class HillSession:
    """Clara Hill 3단계 세션 상태."""
    dream_text: str
    exploration_responses: list[str] = field(default_factory=list)
    insight_text: str | None = None
    action_items: list[dict[str, str]] = field(default_factory=list)
    current_step: int = 1  # 1=Exploration, 2=Insight, 3=Action
    completed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "dream_text": self.dream_text,
            "exploration_count": len(self.exploration_responses),
            "exploration_responses": self.exploration_responses,
            "insight_text": self.insight_text,
            "action_items": self.action_items,
            "current_step": self.current_step,
            "completed": self.completed,
        }


def build_step_prompt(step: int, session_data: dict[str, Any]) -> dict[str, Any]:
    """단계별 LLM 호출용 system + user 프롬프트 생성."""
    dream = session_data.get("dream_text", "").strip()

    if step == 1:
        return {
            "system": EXPLORATION_SYSTEM_KO,
            "user_message": (
                f"[손님의 꿈]\n{dream[:1500]}\n\n"
                "위 꿈을 탐색하기 위한 3개 질문을 한국어 존댓말로 제시하십시오."
            ),
            "step_name": "Exploration",
            "suggested_prompts": EXPLORATION_PROMPTS_KO,
        }
    elif step == 2:
        exp = session_data.get("exploration_responses") or []
        exp_block = "\n".join(f"  · {r}" for r in exp) or "(탐색 응답 없음)"
        return {
            "system": INSIGHT_SYSTEM_KO,
            "user_message": (
                f"[손님의 꿈]\n{dream[:1200]}\n\n"
                f"[탐색 단계에서 떠올린 것]\n{exp_block}\n\n"
                "위 자료를 바탕으로 통찰 단계를 진행하십시오. 단정 금지, 다층 가능성 제시."
            ),
            "step_name": "Insight",
        }
    elif step == 3:
        insight = session_data.get("insight_text") or "(통찰 단계 미완료)"
        return {
            "system": ACTION_SYSTEM_KO,
            "user_message": (
                f"[손님의 꿈]\n{dream[:800]}\n\n"
                f"[통찰]\n{insight[:1000]}\n\n"
                "위 통찰을 바탕으로 오늘·이번 주 안에 시도할 수 있는 구체적 행동 1~3개를 제시하십시오. "
                f"행동 카테고리 참고: {', '.join(c['name'] for c in ACTION_CATEGORIES_KO)}."
            ),
            "step_name": "Action",
            "categories": ACTION_CATEGORIES_KO,
        }
    else:
        raise ValueError(f"step은 1~3 (받음: {step})")


def validate_session_completion(session: HillSession) -> dict[str, Any]:
    """세션 완성도 검증 — Action까지 도달했는지 확인."""
    issues: list[str] = []
    if not session.exploration_responses:
        issues.append("탐색 단계 응답 없음")
    if not session.insight_text:
        issues.append("통찰 단계 미완료")
    if not session.action_items:
        issues.append("실행 단계 미완료 — 가장 중요한 단계")

    is_complete = len(issues) == 0
    return {
        "complete": is_complete,
        "issues": issues,
        "note": (
            "3단계 완주 — Clara Hill 모델의 진가는 Action까지 도달했을 때 발휘됩니다."
            if is_complete
            else f"남은 작업: {', '.join(issues)}"
        ),
    }


__all__ = [
    "HILL_LABEL",
    "EXPLORATION_SYSTEM_KO",
    "INSIGHT_SYSTEM_KO",
    "ACTION_SYSTEM_KO",
    "EXPLORATION_PROMPTS_KO",
    "ACTION_CATEGORIES_KO",
    "HillSession",
    "build_step_prompt",
    "validate_session_completion",
]
