"""응답 PII 누출 감지 — 운영표준 §7.2.18 본문화.

LLM이 응답에 PII(개인식별정보) 패턴을 포함시키는 경우를 결정론 후처리로 감지.
PII는 일반적으로 시스템 프롬프트에 없으므로 응답에 등장하면 다음을 의심:
  · LLM이 학습 데이터의 PII를 재생성 (hallucination)
  · 시스템/사용자 프롬프트에 포함된 PII가 누출
  · 다른 사용자 세션의 PII가 혼입 (cross-session leak)

§7.2.18 검출 패턴:
  · 전화번호 (KR 010-/+82, US (xxx)/xxx-xxx-xxxx, intl +XX)
  · 이메일 (RFC 5322 단순화)
  · 한국 주민등록번호 (xxxxxx-xxxxxxx)
  · 신용카드 (4그룹 4자리)
  · IP 주소 (IPv4)
  · API 키 패턴 (sk-..., AKIA..., ghp_..., AIza...)

본 모듈은 검출만 — 응답 수정은 호출자(혹은 engine.safety.gdpr.pii.mask_pii) 책임.
검출 시 폴백 트리거 권장 (의심 응답 사용 금지).

§7.2.18 false positive 회피:
  · 한국 위기 핫라인(1393/1577-0199/119/112)은 PII 아님 — 화이트리스트
  · 운영표준 §7.2.10 model_card의 contact_method도 면제
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# §7.2.18 검출 코드
PII_PHONE_KR = "phone_kr"
PII_PHONE_INTL = "phone_intl"
PII_EMAIL = "email"
PII_KOR_SSN = "kor_ssn"
PII_CREDIT_CARD = "credit_card"
PII_IPV4 = "ipv4"
PII_API_KEY = "api_key"


# 한국 휴대전화: 010-XXXX-XXXX, 010 XXXX XXXX, 01012345678
_PHONE_KR_RE = re.compile(
    r"\b01[016789][-\s]?\d{3,4}[-\s]?\d{4}\b"
)

# 국제 전화 (+82-10-..., +1-555-..., +44-..) — 최소 6자리
_PHONE_INTL_RE = re.compile(
    r"\+\d{1,3}[-\s]?\d{2,4}[-\s]?\d{3,4}[-\s]?\d{3,4}"
)

# 이메일 — RFC 5322 단순화
_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

# 한국 주민번호 — YYMMDD-NNNNNNN
_KOR_SSN_RE = re.compile(
    r"\b\d{6}[-\s]?[1-4]\d{6}\b"
)

# 신용카드 — 4그룹 4자리 (Luhn 미검증, 패턴만)
_CREDIT_RE = re.compile(
    r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
)

# IPv4
_IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)

# API 키 패턴 (Anthropic sk-ant-, OpenAI sk-, AWS AKIA, GitHub ghp_, Google AIza)
# AIza 등의 끝에 추가 영숫자가 더 붙어 있어도 매칭되도록 {n,} 로 처리.
_API_KEY_RE = re.compile(
    r"\b(?:sk-ant-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16,}|ghp_[A-Za-z0-9]{36,}|AIza[A-Za-z0-9_-]{35,})\b"
)

# §7.2.18 — false positive 화이트리스트 (PII가 아닌 공익 번호)
_WHITELIST_NUMBERS = (
    "1393",        # 자살예방상담
    "1577-0199",   # 정신건강위기상담
    "129",         # 보건복지콜센터
    "112",         # 경찰
    "119",         # 소방·응급
    "988",         # US 라이프라인
)


@dataclass(frozen=True)
class PIILeakResult:
    leaks: list[str] = field(default_factory=list)
    matched_samples: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.leaks


# ─────────────────────────── 헬퍼 ───────────────────────────

def _is_whitelisted(match: str) -> bool:
    """위기 핫라인 등 공익 번호는 PII 아님."""
    m = match.strip().replace(" ", "")
    return any(w.replace("-", "").replace(" ", "") in m for w in _WHITELIST_NUMBERS)


def _find_with_filter(
    text: str,
    pattern: re.Pattern,
    *,
    skip_whitelist: bool = False,
) -> list[str]:
    matches: list[str] = []
    for m in pattern.finditer(text):
        val = m.group(0)
        if skip_whitelist and _is_whitelisted(val):
            continue
        matches.append(val)
    return matches


# ─────────────────────────── 개별 검출 ───────────────────────────

def find_phone_kr(text: str) -> list[str]:
    if not text:
        return []
    return _find_with_filter(text, _PHONE_KR_RE, skip_whitelist=True)


def find_phone_intl(text: str) -> list[str]:
    if not text:
        return []
    return _find_with_filter(text, _PHONE_INTL_RE)


def find_email(text: str) -> list[str]:
    if not text:
        return []
    return [m.group(0) for m in _EMAIL_RE.finditer(text)]


def find_kor_ssn(text: str) -> list[str]:
    if not text:
        return []
    return [m.group(0) for m in _KOR_SSN_RE.finditer(text)]


def find_credit_card(text: str) -> list[str]:
    if not text:
        return []
    return [m.group(0) for m in _CREDIT_RE.finditer(text)]


def find_ipv4(text: str) -> list[str]:
    if not text:
        return []
    matches = [m.group(0) for m in _IPV4_RE.finditer(text)]
    # 0.0.0.0 / 127.0.0.1 / 255.255.255.255 는 PII 아님
    benign = {"0.0.0.0", "127.0.0.1", "255.255.255.255", "1.1.1.1", "8.8.8.8"}
    return [m for m in matches if m not in benign]


def find_api_key(text: str) -> list[str]:
    if not text:
        return []
    return [m.group(0) for m in _API_KEY_RE.finditer(text)]


# ─────────────────────────── 통합 진입점 ───────────────────────────

def scan(text: str | None) -> PIILeakResult:
    """모든 PII 패턴 일괄 검출. 위반 코드 + 매칭 샘플 반환."""
    if not text or not isinstance(text, str):
        return PIILeakResult()

    leaks: list[str] = []
    samples: list[str] = []

    p_kr = find_phone_kr(text)
    if p_kr:
        leaks.append(PII_PHONE_KR)
        samples.extend(p_kr)

    p_intl = find_phone_intl(text)
    if p_intl:
        leaks.append(PII_PHONE_INTL)
        samples.extend(p_intl)

    em = find_email(text)
    if em:
        leaks.append(PII_EMAIL)
        samples.extend(em)

    ssn = find_kor_ssn(text)
    if ssn:
        leaks.append(PII_KOR_SSN)
        samples.extend(ssn)

    cc = find_credit_card(text)
    if cc:
        leaks.append(PII_CREDIT_CARD)
        samples.extend(cc)

    ip = find_ipv4(text)
    if ip:
        leaks.append(PII_IPV4)
        samples.extend(ip)

    ak = find_api_key(text)
    if ak:
        leaks.append(PII_API_KEY)
        samples.extend(ak)

    return PIILeakResult(leaks=leaks, matched_samples=samples)


def has_leak(text: str | None) -> bool:
    """빠른 게이트."""
    return bool(scan(text).leaks)


def to_fallback_trigger(result: PIILeakResult) -> str:
    """llm_fallback_router 호환 — PII 검출 시 persona_failed로 폴백."""
    return "persona_failed" if result.leaks else ""


# 외부 API에서 명확한 이름으로 노출 (모듈 내부에서는 scan/has_leak 사용)
scan_response_pii = scan
has_pii_leak = has_leak
