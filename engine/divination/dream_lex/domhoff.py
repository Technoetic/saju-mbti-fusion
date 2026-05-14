"""G.W. Domhoff 연속성 가설(Continuity Hypothesis).

꿈은 깨어 있는 삶의 관심·관계·근심의 연속 — 신비한 메시지가 아니라
일상적 인지 양식이 수면 중에도 지속되는 결과.

이 모듈의 역할:
  - 꿈 내용을 6대 생활 영역으로 분류
  - 어느 영역이 도드라지는지 집계해 깨어 있는 삶의 어떤 부분이
    꿈에 반영되었는지 정량화
"""

from __future__ import annotations
from typing import Any


DOMHOFF_LABEL = (
    "연속성 가설 — 꿈은 깨어 있는 삶의 관심·관계·근심의 연속. "
    "어느 생활 영역이 꿈에 반영되었는지가 핵심 단서."
)


LIFE_DOMAINS = {
    "work_school": "일·학업 — 직장·시험·과제·동료",
    "family": "가족 — 부모·형제·자녀·친지",
    "romance": "연애·결혼 — 연인·배우자·이성",
    "social": "사회관계 — 친구·이웃·낯선 사람",
    "health": "건강·신체 — 질병·신체변화·치료",
    "finance_property": "재정·소유 — 돈·집·물건·재산",
}


WORK_SCHOOL = [
    "회사", "사무실", "직장", "동료", "상사", "팀장", "부장", "과장", "사장",
    "직원", "출근", "퇴근", "회의", "프로젝트", "보고서", "발표",
    "학교", "학원", "교실", "선생님", "교수", "시험", "성적", "과제", "숙제",
    "졸업", "입학", "수업", "강의", "기말", "중간고사", "수능",
]

FAMILY = [
    "부모", "엄마", "어머니", "아빠", "아버지", "할머니", "할아버지",
    "형", "오빠", "누나", "언니", "동생", "남매", "자매", "형제",
    "아들", "딸", "자식", "자녀", "조카", "삼촌", "이모", "고모",
    "사촌", "친척", "가족", "집안", "친정", "시댁",
]

ROMANCE = [
    "연인", "남자친구", "여자친구", "애인", "남친", "여친",
    "남편", "아내", "와이프", "허즈번드", "배우자",
    "결혼", "프로포즈", "데이트", "키스", "포옹", "고백",
    "헤어짐", "이별", "이혼", "재회", "옛 연인", "전 연인",
    "썸", "소개팅", "맞선",
]

SOCIAL = [
    "친구", "동창", "단짝", "베프", "지인", "이웃", "동네 사람",
    "모임", "파티", "회식", "결혼식", "장례식",
    "낯선 사람", "처음 본 사람", "외국인", "행인",
    "유명인", "연예인", "스타",
]

HEALTH = [
    "병원", "의사", "간호사", "환자", "진료", "검사", "수술",
    "병", "병에 걸림", "암", "감기", "독감", "수술실",
    "약", "주사", "혈액", "치과", "이빨", "이빨 빠짐", "치통",
    "다침", "상처", "골절", "타박상", "출혈",
    "임신", "출산", "유산", "초음파",
]

FINANCE_PROPERTY = [
    "돈", "현금", "지폐", "동전", "수표", "통장", "계좌",
    "월급", "보너스", "돈 받음", "돈 잃음", "지갑",
    "집", "아파트", "전세", "월세", "매매", "이사",
    "차", "자동차", "신차", "중고차",
    "가게", "장사", "사업", "투자", "주식", "부동산",
    "복권", "당첨", "횡재",
]


_DOMAIN_KEYWORDS = {
    "work_school": WORK_SCHOOL,
    "family": FAMILY,
    "romance": ROMANCE,
    "social": SOCIAL,
    "health": HEALTH,
    "finance_property": FINANCE_PROPERTY,
}


def classify_domains(text: str) -> dict[str, Any]:
    """꿈 내용을 6대 생활 영역으로 분류·집계."""
    t = text or ""
    matches_by_domain: dict[str, list[str]] = {}
    counts: dict[str, int] = {}

    for domain, keywords in _DOMAIN_KEYWORDS.items():
        hits = [k for k in keywords if k in t]
        matches_by_domain[domain] = hits
        counts[domain] = len(hits)

    total = sum(counts.values()) or 1
    distribution = {k: round(v / total * 100, 1) for k, v in counts.items()}
    dominant = max(counts, key=lambda k: counts[k]) if total > 1 else None

    return {
        "by_domain": matches_by_domain,
        "counts": counts,
        "distribution_pct": distribution,
        "dominant_domain": dominant,
        "dominant_label": LIFE_DOMAINS.get(dominant) if dominant else None,
        "continuity_signal": (
            f"꿈이 깨어 있는 삶의 '{LIFE_DOMAINS.get(dominant)}' 영역과 연속됨."
            if dominant else "특정 생활 영역과 강한 연속성 없음."
        ),
    }


__all__ = [
    "DOMHOFF_LABEL",
    "LIFE_DOMAINS",
    "classify_domains",
]
