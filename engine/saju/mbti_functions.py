"""MBTI 16유형 → 8 인지 기능 스택 (주/부/3차/열등).

융(Jung) 의 8 인지 기능:
  Ti/Te (사고 내/외향), Fi/Fe (감정 내/외향),
  Ni/Ne (직관 내/외향), Si/Se (감각 내/외향)

스택 순서: [주기능(Dominant), 부기능(Auxiliary), 3차(Tertiary), 열등(Inferior)]
"""

from __future__ import annotations

_FUNCTION_STACK = {
    "INTJ": ["Ni", "Te", "Fi", "Se"],
    "INTP": ["Ti", "Ne", "Si", "Fe"],
    "ENTJ": ["Te", "Ni", "Se", "Fi"],
    "ENTP": ["Ne", "Ti", "Fe", "Si"],
    "INFJ": ["Ni", "Fe", "Ti", "Se"],
    "INFP": ["Fi", "Ne", "Si", "Te"],
    "ENFJ": ["Fe", "Ni", "Se", "Ti"],
    "ENFP": ["Ne", "Fi", "Te", "Si"],
    "ISTJ": ["Si", "Te", "Fi", "Ne"],
    "ISFJ": ["Si", "Fe", "Ti", "Ne"],
    "ESTJ": ["Te", "Si", "Ne", "Fi"],
    "ESFJ": ["Fe", "Si", "Ne", "Ti"],
    "ISTP": ["Ti", "Se", "Ni", "Fe"],
    "ISFP": ["Fi", "Se", "Ni", "Te"],
    "ESTP": ["Se", "Ti", "Fe", "Ni"],
    "ESFP": ["Se", "Fi", "Te", "Ni"],
}

_FUNCTION_KO = {
    "Ti": "내향 사고 (내면 논리 구축)",
    "Te": "외향 사고 (외부 시스템 조직화)",
    "Fi": "내향 감정 (개인 가치·신념)",
    "Fe": "외향 감정 (집단 조화·공감)",
    "Ni": "내향 직관 (통찰·미래 패턴)",
    "Ne": "외향 직관 (가능성 탐색·연결)",
    "Si": "내향 감각 (과거 경험·세부 기억)",
    "Se": "외향 감각 (현재 5감·즉시 반응)",
}


def function_stack(mbti: str) -> dict:
    """MBTI → 4 기능 스택 한국어 설명.

    Returns:
        {
          "dominant": "Ni (내향 직관)",
          "auxiliary": "Te (외향 사고)",
          "tertiary": "Fi (내향 감정)",
          "inferior": "Se (외향 감각)",
        }
    """
    mbti = (mbti or "").upper().strip()
    stack = _FUNCTION_STACK.get(mbti)
    if not stack:
        raise ValueError(f"unknown MBTI: {mbti}")
    labels = ["dominant", "auxiliary", "tertiary", "inferior"]
    return {
        label: f"{code} ({_FUNCTION_KO[code]})"
        for label, code in zip(labels, stack)
    }


def function_stack_lines(mbti: str) -> list[str]:
    """프롬프트 첨부용 한 줄 라인 리스트."""
    s = function_stack(mbti)
    return [
        f"- 주기능: {s['dominant']} — 무의식적 1순위 정보 처리",
        f"- 부기능: {s['auxiliary']} — 외부 상호작용 도구",
        f"- 3차 기능: {s['tertiary']} — 약하지만 성장 영역",
        f"- 열등 기능: {s['inferior']} — 스트레스 시 폭발 지점",
    ]


__all__ = ["function_stack", "function_stack_lines"]
