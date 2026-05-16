"""두음법칙(頭音法則) 매핑 — 보고서 §4 본문화.

전자가족관계등록시스템 실무 규정:
  · 한자의 첫소리(初聲)가 'ㄴ' 또는 'ㄹ'인 경우 두음법칙 적용 허용
  · 사용자가 '류(柳)' → '유' 또는 '라(羅)' → '나'로 검색해도 매칭

본 모듈은 결정론 매핑 사전 + 정규화 함수.
역(逆)매핑도 지원 — '유'로 입력 시 '류'·'유' 둘 다 후보로.
"""

from __future__ import annotations


# ─────────────────────────── 두음법칙 매핑 ───────────────────────────
# 원음 → 두음 변환 (한자 본래 음 → 한글 등록 시 실제 소리)
# 첫 글자에만 적용 (이름 둘째 글자는 본래 음 유지)

# ㄹ + 모음 → ㅇ + 모음 (ㄹ 탈락)
_R_TO_O: dict[str, str] = {
    "라": "나", "락": "낙", "란": "난", "랄": "날", "람": "남",
    "랍": "납", "랑": "낭", "래": "내", "랭": "냉", "량": "양",
    "려": "여", "력": "역", "련": "연", "렬": "열", "렴": "염",
    "렵": "엽", "령": "영", "례": "예", "로": "노", "록": "녹",
    "론": "논", "롱": "농", "뢰": "뇌", "료": "요", "룡": "용",
    "루": "누", "류": "유", "륙": "육", "륜": "윤", "률": "율",
    "륭": "융", "륵": "늑", "름": "늠", "릉": "능", "리": "이",
    "린": "인", "림": "임", "립": "입",
}

# ㄴ + 이/야 등 → ㅇ (역시 ㄴ 탈락)
_N_TO_O: dict[str, str] = {
    "냐": "야", "녀": "여", "뇨": "요", "뉴": "유", "니": "이",
    "녕": "영",
}


def apply_dueum(syllable: str) -> str:
    """단일 음절에 두음법칙 적용. 변환 대상 아니면 그대로 반환."""
    if not isinstance(syllable, str) or not syllable:
        return syllable or ""
    if syllable in _R_TO_O:
        return _R_TO_O[syllable]
    if syllable in _N_TO_O:
        return _N_TO_O[syllable]
    return syllable


def reverse_dueum(syllable: str) -> list[str]:
    """두음법칙 역(逆)매핑 — 두음 표기에서 가능한 원음 후보 목록.

    예: '유' → ['유', '류']  (원래 ㄹ 시작이었을 수 있음)
        '이' → ['이', '리', '니']
        '나' → ['나', '라']

    UI에서 사용자가 '유'로 검색 시 柳(류)·油(유)·有(유) 등 모두 후보로 노출.
    """
    if not isinstance(syllable, str) or not syllable:
        return []
    candidates = [syllable]
    # ㄹ → ㅇ 역방향: 두음 표기에서 원음 ㄹ 시작 음 찾기
    for orig, dueum in _R_TO_O.items():
        if dueum == syllable and orig not in candidates:
            candidates.append(orig)
    # ㄴ → ㅇ 역방향
    for orig, dueum in _N_TO_O.items():
        if dueum == syllable and orig not in candidates:
            candidates.append(orig)
    return candidates


def is_dueum_target(syllable: str) -> bool:
    """단일 음절이 두음법칙 적용 대상인지 (원음 ㄹ/ㄴ 시작 첫 글자)."""
    return syllable in _R_TO_O or syllable in _N_TO_O


def normalize_for_search(syllable: str) -> str:
    """검색용 정규화 — 항상 두음 표기로 변환.

    사용자가 '류' 또는 '유' 어느 쪽으로 입력해도 같은 키로 검색 가능.
    예: '류' → '유', '유' → '유'
    """
    return apply_dueum(syllable)


def expand_search_candidates(syllable: str) -> list[str]:
    """검색 시 매칭 후보 — 입력 + 두음·역두음 모두.

    예: '유' → ['유', '류']
        '류' → ['류', '유']  (apply_dueum으로 '유' 추가)
        '이' → ['이', '리', '니']
    """
    s = syllable or ""
    out = [s]
    # 1. 원음 → 두음
    d = apply_dueum(s)
    if d != s and d not in out:
        out.append(d)
    # 2. 두음 → 원음들 (역매핑)
    for c in reverse_dueum(s):
        if c not in out:
            out.append(c)
    return out


def total_mappings() -> int:
    """매핑된 음절 총 개수 (ㄹ + ㄴ)."""
    return len(_R_TO_O) + len(_N_TO_O)
