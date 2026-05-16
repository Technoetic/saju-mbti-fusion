"""자각몽(Lucid Dreaming) — LaBerge·Voss 메타인지 훈련 모듈.

출처:
  - LaBerge (1980) "Lucid dreaming as a learnable skill", Perceptual and Motor Skills 51
  - Voss et al. (2009) "Lucid dreaming: A state of consciousness with features of
    both waking and non-lucid dreaming", Sleep 32(9) — 전두 감마 40Hz 입증

핵심:
  - 꿈속에서 자신이 꿈꾸고 있음을 자각 (배외측 전전두피질 활성)
  - 학습 가능한 기술 — MILD / WBTB / reality check 3대 기법
  - 악몽 환자에게는 IRT(#24)와 시너지 — 자각 후 결말 변경 가능

본 모듈의 역할:
  - 자각몽 훈련 7일 프로그램 안내
  - reality check 일일 알림 항목
  - 자각 진입 신호(비행·왜곡·반복) 탐지
"""

from __future__ import annotations
from typing import Any


LUCID_LABEL = (
    "자각몽 — 꿈속에서 꿈인 줄 자각하는 메타인지 상태 (DLPFC 활성, 전두 감마 40Hz). "
    "MILD·WBTB·reality check로 학습 가능."
)


# Reality Check (RC) 12개 — 일상에서 의식적으로 수행
REALITY_CHECKS_KO = [
    {"name": "손 점검", "instruction": "손가락 개수를 두 번 세어보고 모양이 일관된지 확인하세요. 꿈에서는 손이 일그러집니다."},
    {"name": "숨막힘 점검", "instruction": "코를 막고 숨을 들이쉬어 보세요. 숨이 쉬어진다면 꿈입니다."},
    {"name": "글자 점검", "instruction": "근처의 글자를 읽고, 시선을 돌렸다가 다시 읽으세요. 꿈에서는 글자가 바뀝니다."},
    {"name": "시계 점검", "instruction": "시계를 보고, 잠시 시선을 돌린 뒤 다시 보세요. 꿈에서는 시간이 일치하지 않습니다."},
    {"name": "전등 스위치", "instruction": "전등 스위치를 켜보세요. 꿈에서는 작동이 일관되지 않습니다."},
    {"name": "거울 점검", "instruction": "거울 속 자신을 보세요. 꿈에서는 얼굴이 왜곡됩니다."},
    {"name": "점프", "instruction": "가볍게 점프해 보세요. 꿈에서는 중력이 다르게 느껴집니다."},
    {"name": "벽 만지기", "instruction": "손가락을 벽에 대보세요. 꿈에서는 손이 통과하기도 합니다."},
    {"name": "기억 점검", "instruction": "지금까지의 1시간을 순서대로 떠올려 보세요. 꿈에서는 기억이 비어 있습니다."},
    {"name": "휴대폰 점검", "instruction": "화면을 보고 시선을 돌렸다가 다시 보세요. 꿈에서는 텍스트가 바뀝니다."},
    {"name": "코·입 점검", "instruction": "코나 입의 위치를 의식적으로 확인하세요. 꿈에서는 신체 인식이 흐릿합니다."},
    {"name": "지금 어떻게 여기 있는가?", "instruction": "'직전에 무엇을 하다 여기 왔는가?'를 물어보세요. 답이 안 나오면 꿈입니다."},
]


# MILD (Mnemonic Induction of Lucid Dreams) — LaBerge 1980
MILD_PROTOCOL_KO = """[MILD — 기억 유도 자각몽 기법]

준비: 자다가 자연스럽게 깬 직후(REM 직후가 이상적) 시도하면 효과가 최대.

  1. 직전 꿈을 한 단어로 기억하세요 (예: '쫓김', '비행').
  2. 다음 의도 문장을 천천히 5번 반복: '나는 다시 잠들면, 내가 꿈꾸고 있음을 알아챌 것이다.'
  3. 다시 잠드는 동안, 직전 꿈으로 돌아가는 상상을 하되 그 안에서 '아, 이건 꿈이다'를 깨닫는 장면을 함께 상상.
  4. 자연스럽게 잠들도록 두세요.

LaBerge 연구: MILD 4주 훈련 시 평균 자각몽 빈도 주 0.5회 → 주 2.5회로 증가."""


# WBTB (Wake Back To Bed) — 새벽 REM 활용
WBTB_PROTOCOL_KO = """[WBTB — 다시 자기 기법]

REM 수면은 새벽 4~6시에 집중. 이 구간을 의도적으로 활용.

  1. 평소 기상 시간보다 4.5~6시간 일찍 알람.
  2. 깨어나서 20~30분 가량 약하게 활동 (꿈 일기 쓰기·자각몽 책 읽기).
  3. 그 후 MILD 의도 문장을 외우며 다시 잠들기.
  4. 다시 든 잠에서 REM 비율이 매우 높아 자각몽 진입 가능성 증가.

주의: 매일 하지 마세요. 주 2회 정도로 수면 위생 보호."""


# 자각 진입 신호 (Dream Sign) — 흔한 꿈 특이성
LUCIDITY_TRIGGERS = [
    "날기", "공중 부양", "비행",
    "벽을 통과", "유리를 통과",
    "죽은 사람과 대화", "옛집 방문",
    "거울 속이 다름", "시계 숫자가 이상",
    "글자가 바뀜", "글자가 일그러",
    "반복되는 꿈", "데자뷔",
    "이상한 변형", "사물이 살아",
    "장소가 갑자기 바뀜",
]


def detect_lucidity_potential(dream_text: str) -> dict[str, Any]:
    """꿈 텍스트에서 자각 진입 가능 신호 탐지."""
    t = dream_text or ""
    triggers_found = [k for k in LUCIDITY_TRIGGERS if k in t]

    # 이미 자각한 흔적 (사용자가 보고서에 명시한 경우)
    self_awareness_markers = [
        "이건 꿈이다", "꿈인 줄", "꿈이라는 걸 알",
        "내가 통제", "내가 조종", "내가 바꿨",
    ]
    self_aware = [m for m in self_awareness_markers if m in t]

    if self_aware:
        level = "자각 발생"
        note = "이미 부분 자각몽을 경험하신 신호 — 다음에는 통제 시도를 늘려보세요."
    elif len(triggers_found) >= 3:
        level = "자각 잠재력 높음"
        note = "여러 자각 트리거가 등장 — 비행·왜곡·반복이 보일 때 reality check를 떠올리도록 훈련하세요."
    elif triggers_found:
        level = "자각 잠재력 보통"
        note = "일부 트리거 등장. 일주일간 같은 트리거가 반복되면 그것이 본인의 'dream sign'입니다."
    else:
        level = "자각 신호 미감지"
        note = "이 꿈에서는 명확한 자각 진입 신호가 없습니다."

    return {
        "lucidity_level": level,
        "triggers_found": triggers_found,
        "self_aware_markers": self_aware,
        "interpretive_note": note,
        "next_practice": _suggest_practice(level),
    }


def _suggest_practice(level: str) -> str:
    if level == "자각 발생":
        return "다음 자각 시 손 점검 → 코를 막고 호흡 → 통제 1동작 (예: 손가락 위로 가리키기)을 차례로."
    if "잠재력" in level:
        return "MILD 의도 문장을 매일 자기 전 5회 반복 + reality check 12개 중 3개를 일과 중 시도."
    return "꿈 일기를 1주일 누적해 본인의 dream sign을 찾으세요. 그것이 자각의 열쇠가 됩니다."


def build_7day_lucid_program() -> dict[str, Any]:
    """7일 자각몽 입문 프로그램."""
    return {
        "duration_days": 7,
        "daily_plan": [
            {"day": 1, "task": "Reality Check 12개를 읽고 마음에 드는 3개 선택"},
            {"day": 2, "task": "선택한 3개를 매시간 알림으로 일과 중 시도"},
            {"day": 3, "task": "꿈 일기 작성 시작 — 깨어난 즉시 한 줄이라도"},
            {"day": 4, "task": "자기 전 MILD 의도 문장 5회 반복 시작"},
            {"day": 5, "task": "꿈 일기에서 반복 모티프(dream sign) 찾기"},
            {"day": 6, "task": "WBTB 시도 — 평소보다 4.5시간 일찍 알람 + 30분 깨어 있기"},
            {"day": 7, "task": "주간 회고 — 자각 빈도·생생함 평가, 다음 주 계획"},
        ],
        "reality_checks": REALITY_CHECKS_KO[:3],  # 시작용 3개만
        "mild_protocol": MILD_PROTOCOL_KO,
        "wbtb_protocol": WBTB_PROTOCOL_KO,
        "disclaimer": (
            "자각몽 훈련은 자기관찰 도구입니다. 수면 부족·일과 방해가 느껴지면 즉시 중단하세요. "
            "악몽 환자는 IRT 워크플로와 병행하는 것이 안전합니다."
        ),
    }


__all__ = [
    "LUCID_LABEL",
    "REALITY_CHECKS_KO",
    "MILD_PROTOCOL_KO",
    "WBTB_PROTOCOL_KO",
    "LUCIDITY_TRIGGERS",
    "detect_lucidity_potential",
    "build_7day_lucid_program",
]
