"""Dormio TDI (Targeted Dream Incubation) — MIT MediaLab 입면환각 표적 부화.

출처: Horowitz, Cunningham, Maes, Stickgold (MIT MediaLab, 2018~)
"Dormio: A Targeted Dream Incubation Device"

핵심:
  - N1 수면 단계(입면환각/hypnagogia) — 깨어있음과 얕은 수면의 경계
  - 이 단계 진입 시 음성 큐(예: '나무에 대해 생각하세요') 주입
  - 살짝 깨움 → 미세꿈(microdream) 보고 → 다시 재움 반복
  - → 표적 주제로 발산적 창의성 폭증 (실험적으로 입증)

기존 #1 incubation(취침 전 의식적 안내)의 다음 단계:
  - incubation: 의식 상태에서의 의도 형성 (수면 진입 전)
  - dormio:    N1 단계 자체를 능동 활용 (수면 진입 중)

본 모듈:
  - N1 진입 추정 가이드 (시간·체동 단서)
  - 표적 주제별 큐 문구 생성
  - 미세꿈 보고 수집 양식
"""

from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field


DORMIO_LABEL = (
    "Dormio TDI — MIT MediaLab의 N1 입면환각 단계 표적 부화. "
    "수면 진입 중 음성 큐 + 미세꿈 보고 반복으로 창의성 발산."
)


# Dormio 권장 표적 주제 카테고리
DORMIO_TARGET_CATEGORIES = {
    "creative_problem": {
        "korean": "창의적 문제 해결",
        "example_targets": ["디자인 문제", "코드 구조", "기획 아이디어"],
        "expected_outcome": "기존 사고 틀을 벗어난 발산적 연상",
    },
    "memory_recall": {
        "korean": "기억 회상 보조",
        "example_targets": ["잊어버린 약속", "어릴 적 장소", "지난 대화"],
        "expected_outcome": "장기 기억의 비선형적 재활성화",
    },
    "emotional_processing": {
        "korean": "정서 처리",
        "example_targets": ["복잡한 관계", "결정의 갈등", "미해결 감정"],
        "expected_outcome": "감정적 무게의 은유적 재배치",
    },
    "skill_consolidation": {
        "korean": "기술 통합 (절차 기억)",
        "example_targets": ["악기 연습 패턴", "운동 동작", "외국어 표현"],
        "expected_outcome": "Stickgold 효과 — 절차 기억의 야간 통합 가속",
    },
}


# N1 진입 추정 가이드 — 웨어러블 없이도 사용 가능한 보수적 기준
N1_ENTRY_GUIDE_KO = """[N1 진입 추정 가이드 — 웨어러블 없는 경우]

다음 신호가 보이면 N1 단계 진입 가능성 높음:

  1. 침대에 누운 후 5~15분 경과
  2. 의식이 흐릿해지지만 완전히 잠들지 않은 상태
  3. 머릿속에 자유연상·이미지 단편이 떠오르기 시작
  4. 갑작스러운 근경련(hypnic jerk) 직전·직후
  5. 손에 쥔 가벼운 물건(열쇠·숟가락)을 놓치면 깨어남
     → MIT Dormio는 이 '손 물체 떨어뜨리기' 고전 기법을 활용

[알람 권장]
  • 침대 누운 후 8분 후 첫 알람 (큐 주입)
  • 살짝 깨우는 진동·소리로 미세꿈 보고
  • 1~2회 반복 후 본격 수면 진입 허용
"""


# N1 큐 시스템 프롬프트 — 짧고 평이한 한국어
def build_cue_audio_text(
    target_topic: str,
    category: str | None = None,
) -> str:
    """N1 단계에 주입할 음성 큐 문구 생성."""
    topic = target_topic.strip() or "오늘 마음에 떠오르는 것"
    return (
        f"이제 '{topic}'에 대해 생각해 보세요. "
        f"답을 찾으려 하지 말고, 떠오르는 이미지나 단어를 그저 받아들이세요. "
        f"'{topic}' — 생각의 흐름을 따라가세요."
    )


# 미세꿈(microdream) 보고 양식
MICRODREAM_REPORT_FIELDS_KO = [
    {
        "key": "first_image",
        "name": "첫 이미지",
        "instruction": "큐가 들린 직후 떠오른 첫 이미지·단어를 한 줄로.",
    },
    {
        "key": "associations",
        "name": "연상 단편",
        "instruction": "이어진 자유연상 (3~5개 단편).",
    },
    {
        "key": "emotional_tone",
        "name": "정서 톤",
        "instruction": "어떤 느낌이었나? (1단어: 평화/혼란/기쁨/불안 등)",
    },
    {
        "key": "surprise_factor",
        "name": "예상 밖 요소",
        "instruction": "낮에는 생각하지 못했던 의외의 연결이 있었나?",
    },
]


@dataclass
class DormioSession:
    """1회 Dormio TDI 세션 상태."""
    target_topic: str
    category: str = "creative_problem"
    cycles: int = 2  # 반복 횟수
    reports: list[dict[str, Any]] = field(default_factory=list)
    started_at_iso: str | None = None
    completed: bool = False

    def add_microdream_report(self, report: dict[str, Any]) -> None:
        self.reports.append(report)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_topic": self.target_topic,
            "category": self.category,
            "cycles": self.cycles,
            "report_count": len(self.reports),
            "reports": self.reports,
            "started_at_iso": self.started_at_iso,
            "completed": self.completed,
        }


def build_dormio_session(
    target_topic: str,
    category: str = "creative_problem",
    cycles: int = 2,
) -> dict[str, Any]:
    """Dormio TDI 세션 안내 + 큐 + 보고 양식 묶음."""
    cat_info = DORMIO_TARGET_CATEGORIES.get(category) or DORMIO_TARGET_CATEGORIES["creative_problem"]
    cue = build_cue_audio_text(target_topic, category)

    return {
        "target_topic": target_topic,
        "category": category,
        "category_label": cat_info["korean"],
        "expected_outcome": cat_info["expected_outcome"],
        "cycles": cycles,
        "n1_entry_guide": N1_ENTRY_GUIDE_KO,
        "audio_cue_text": cue,
        "cue_repeat_interval_min": 8,
        "microdream_fields": MICRODREAM_REPORT_FIELDS_KO,
        "disclaimer": (
            "Dormio TDI는 창의성 발산 보조 도구이며 의료 치료가 아닙니다. "
            "수면 부족이 누적되면 즉시 중단하세요. "
            "주 2회 이상은 권장되지 않습니다 — 정상 수면 사이클 보호."
        ),
    }


def synthesize_microdream_insights(
    reports: list[dict[str, Any]],
    target_topic: str,
) -> dict[str, Any]:
    """N회 반복 후 수집한 미세꿈 보고들에서 통찰 추출 (결정론·LLM 없이)."""
    if not reports:
        return {"insights": [], "note": "보고 없음."}

    # 반복 등장 이미지
    all_images = []
    for r in reports:
        if r.get("first_image"):
            all_images.append(r["first_image"])
        for a in r.get("associations") or []:
            all_images.append(a)

    # 빈도 카운트
    from collections import Counter
    counter = Counter(all_images)
    repeating = [(img, n) for img, n in counter.most_common(5) if n >= 2]

    # 정서 톤 분포
    tones = [r.get("emotional_tone") for r in reports if r.get("emotional_tone")]
    tone_dist = dict(Counter(tones))

    # 예상 밖 요소 수집
    surprises = [r.get("surprise_factor") for r in reports if r.get("surprise_factor")]

    return {
        "target_topic": target_topic,
        "cycle_count": len(reports),
        "repeating_images": repeating,
        "emotional_tone_distribution": tone_dist,
        "surprise_elements": surprises,
        "interpretive_note": (
            f"{len(reports)}회 미세꿈에서 반복 이미지 {len(repeating)}개, "
            f"예상 밖 요소 {len(surprises)}개. "
            f"낮 사고로는 접근하기 어려웠던 '{target_topic}'의 측면이 드러났을 수 있습니다."
        ),
    }


__all__ = [
    "DORMIO_LABEL",
    "DORMIO_TARGET_CATEGORIES",
    "N1_ENTRY_GUIDE_KO",
    "MICRODREAM_REPORT_FIELDS_KO",
    "DormioSession",
    "build_cue_audio_text",
    "build_dormio_session",
    "synthesize_microdream_insights",
]
