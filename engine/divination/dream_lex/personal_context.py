"""개인 맥락 변수 — 사주·MBTI·인구통계 통합 어셈블러.

해몽은 보편 사전만으로 완성되지 않는다. 같은 '뱀'이라도 임신부에겐 태몽,
사업가에겐 재물 시그널이 된다. 이 모듈은 사주/연령/성별/직업/현재 고민 등을
하나의 맥락 객체로 묶어 dream.py 통합 에이전트의 user 메시지에 주입한다.
"""

from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field


@dataclass
class PersonalContext:
    """해몽 시 함께 주입되는 개인 맥락."""
    name: str | None = None
    gender: str | None = None  # 'M' or 'F'
    age: int | None = None
    occupation: str | None = None  # '직장인', '학생', '주부', '사업가' 등
    marital_status: str | None = None  # '미혼', '기혼', '이혼', '사별'
    has_children: bool | None = None
    is_pregnant: bool | None = None
    current_concerns: list[str] = field(default_factory=list)  # ['이직', '시험', '연애']

    # 사주 통합 필드
    day_master: str | None = None  # 일간 (甲乙丙丁戊己庚辛壬癸)
    day_master_element: str | None = None  # 木火土金水
    yongsin: str | None = None  # 용신
    current_daewoon_element: str | None = None  # 현재 대운 오행
    saju_summary: str | None = None  # 한 줄 요약

    # MBTI
    mbti: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "gender": self.gender,
            "age": self.age,
            "occupation": self.occupation,
            "marital_status": self.marital_status,
            "has_children": self.has_children,
            "is_pregnant": self.is_pregnant,
            "current_concerns": self.current_concerns,
            "day_master": self.day_master,
            "day_master_element": self.day_master_element,
            "yongsin": self.yongsin,
            "current_daewoon_element": self.current_daewoon_element,
            "saju_summary": self.saju_summary,
            "mbti": self.mbti,
        }

    def to_prompt_block(self) -> str:
        """LLM user 메시지에 주입할 '사실 블록' 텍스트 생성."""
        lines = ["[개인 맥락 사실]"]
        if self.name:
            lines.append(f"- 이름: {self.name}")
        if self.gender:
            lines.append(f"- 성별: {'남성' if self.gender == 'M' else '여성'}")
        if self.age:
            lines.append(f"- 나이: {self.age}세")
        if self.occupation:
            lines.append(f"- 직업: {self.occupation}")
        if self.marital_status:
            lines.append(f"- 혼인 상태: {self.marital_status}")
        if self.has_children is not None:
            lines.append(f"- 자녀 유무: {'있음' if self.has_children else '없음'}")
        if self.is_pregnant:
            lines.append("- 임신 중: 예 — 태몽 가능성 가중")
        if self.current_concerns:
            lines.append(f"- 현재 고민: {', '.join(self.current_concerns)}")

        if any([self.day_master, self.yongsin, self.current_daewoon_element]):
            lines.append("")
            lines.append("[사주 맥락]")
            if self.day_master:
                lines.append(f"- 일간: {self.day_master} ({self.day_master_element or '?'})")
            if self.yongsin:
                lines.append(f"- 용신: {self.yongsin}")
            if self.current_daewoon_element:
                lines.append(f"- 현 대운 오행: {self.current_daewoon_element}")
            if self.saju_summary:
                lines.append(f"- 사주 요약: {self.saju_summary}")

        if self.mbti:
            lines.append("")
            lines.append(f"[MBTI] {self.mbti}")

        return "\n".join(lines) if len(lines) > 1 else ""


def build_context_from_dict(data: dict[str, Any]) -> PersonalContext:
    """사용자 입력 dict에서 PersonalContext 생성."""
    return PersonalContext(
        name=data.get("name"),
        gender=data.get("gender"),
        age=data.get("age"),
        occupation=data.get("occupation"),
        marital_status=data.get("marital_status"),
        has_children=data.get("has_children"),
        is_pregnant=data.get("is_pregnant"),
        current_concerns=data.get("current_concerns") or [],
        day_master=data.get("day_master"),
        day_master_element=data.get("day_master_element"),
        yongsin=data.get("yongsin"),
        current_daewoon_element=data.get("current_daewoon_element"),
        saju_summary=data.get("saju_summary"),
        mbti=data.get("mbti"),
    )


# 맥락 기반 가중치 규칙 — critic이 참조
CONTEXT_WEIGHTING_RULES = [
    {
        "condition": "is_pregnant == True",
        "boost": "korean_folk:태몽 가중치 2배. 태몽 모티프 우선 해석.",
    },
    {
        "condition": "occupation in ['사업가', '자영업', '투자자']",
        "boost": "korean_folk:재물몽 가중치 1.5배. 재물 모티프 우선.",
    },
    {
        "condition": "occupation in ['학생', '수험생'] OR '시험' in current_concerns",
        "boost": "korean_folk:합격몽 가중치 1.5배.",
    },
    {
        "condition": "marital_status == '미혼' AND age < 35",
        "boost": "이별몽/연애 모티프 가중. 단 태몽 신호 강하면 그쪽 우선.",
    },
    {
        "condition": "age >= 60",
        "boost": "장수·건강·조상 모티프 가중. 가족 통합·뿌리 우선.",
    },
]


__all__ = [
    "PersonalContext",
    "build_context_from_dict",
    "CONTEXT_WEIGHTING_RULES",
]
