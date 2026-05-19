"""PII 마스킹 — 운영표준 §7.3.4.1 코드 골격 본문화.

자유 기술 피드백·로그 본문에서 이메일·전화·주민등록번호를 자동 마스킹.
SHA256 기반 식별자 해싱 함수도 함께 제공.

적용 위치 (운영표준 §7.3.4.1):
  - §7.2.7 자유 기술 피드백 저장 직전: mask_pii(feedback_text)
  - §7.3.4 uid 필드: hash_uid(uid) — 원본 uid는 어디에도 저장 금지
  - §7.3.4 question_hash 필드: hash_question(question) — 본문 미저장
  - §7.2.11 위기 응답 trigger_keywords: 매칭 키워드 앞 4자만 + [...]

본 모듈은 외부 의존성 0 (Python 표준 라이브러리만 사용).
"""

from __future__ import annotations

import hashlib
import re

# 이메일 — 일반 RFC 5322 단순 패턴 (오버매칭 최소화)
_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

# 한국 휴대전화 (010~019) + 일반 유선 (02, 031~064 등)
# (?<!\d)와 (?!\d)로 다른 숫자열에 묻힌 경우 과탐 방지.
_PHONE_RE = re.compile(
    r"(?<!\d)(01[016789]-?\d{3,4}-?\d{4}|\d{2,3}-\d{3,4}-\d{4})(?!\d)"
)

# 주민등록번호 (YYMMDD-N… 형식). 1~4는 내국인 성별 코드.
_RRN_RE = re.compile(r"(?<!\d)\d{6}-[1-4]\d{6}(?!\d)")


def mask_pii(text: str) -> str:
    """자유 기술 피드백·로그 본문에서 이메일·전화·주민번호를 마스킹.

    Args:
        text: 마스킹할 원본 문자열.

    Returns:
        이메일은 [EMAIL], 전화는 [PHONE], 주민번호는 [RRN]으로 치환된 문자열.
        None/빈 문자열은 빈 문자열로 정규화.

    예시:
        >>> mask_pii("문의 hello@example.com 또는 010-1234-5678")
        '문의 [EMAIL] 또는 [PHONE]'
        >>> mask_pii("주민 900101-1234567 확인")
        '주민 [RRN] 확인'
    """
    if not text:
        return ""
    text = _EMAIL_RE.sub("[EMAIL]", text)
    text = _PHONE_RE.sub("[PHONE]", text)
    text = _RRN_RE.sub("[RRN]", text)
    return text


def hash_uid(uid: str, length: int = 8) -> str:
    """§7.3.4 `uid_hash` 필드용 — SHA256 앞 N자만 보존.

    원본 uid는 어디에도 저장 금지. 로그·집계 키로만 사용.
    length=8 → 충돌 확률 무시 가능 수준이면서 PII 식별 불가.
    """
    if not uid:
        return ""
    return hashlib.sha256(uid.encode("utf-8")).hexdigest()[:length]


def hash_question(question: str, length: int = 8) -> str:
    """§7.3.4 `question_hash` 필드용 — 화두 본문 미저장, 식별만 가능.

    동일 화두 재호출 추적 용도. 본문은 로그에 남지 않음.
    """
    if not question:
        return ""
    return hashlib.sha256(question.encode("utf-8")).hexdigest()[:length]


def mask_crisis_keyword(keyword: str, prefix_len: int = 4) -> str:
    """§7.2.11 위기 응답 trigger_keywords 마스킹.

    매칭 키워드 앞 N자만 보존하고 나머지는 [...]로 가린다.
    위기 키워드 자체를 로그에 그대로 남기지 않기 위한 안전장치.

    예시:
        >>> mask_crisis_keyword("죽고싶다")
        '죽고싶다[...]'  # 4자 이하면 그대로 + [...]
        >>> mask_crisis_keyword("자살하고싶어")
        '자살하고[...]'  # 4자 + [...]
    """
    if not keyword:
        return ""
    if len(keyword) <= prefix_len:
        return f"{keyword}[...]"
    return f"{keyword[:prefix_len]}[...]"
