"""국가별 규제 분류 — 운영표준 §7.2.5 본문화.

서비스가 다국가 배포될 때, 사용자의 로케일·IP·언어를 바탕으로 어느 법령
체계가 적용되는지 분류한다. 본 모듈은 결정론적 라우터일 뿐이며, 실제
시장 진입 시 현지 변호사·DPO 검토를 대체하지 않는다.

원본 출처: 운영표준 §7.2.5 국가별 규제·법령 매핑 표.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegulationProfile:
    """국가/지역별 규제 프로파일 — 운영표준 §7.2.5 표."""
    region_code: str       # ISO 3166-1 alpha-2 or special ('EU', 'UK')
    region_name_ko: str
    law_keys: tuple[str, ...]  # 법령 약어 ('GDPR', 'PIPA' 등)
    consent_required: bool      # 명시적 동의 의무
    biometric_sensitive: bool   # 얼굴 이미지가 민감정보로 분류
    delete_response_days: int   # 삭제 요청 응답 한도(일)
    notes_ko: str               # 운영 메모


# 운영표준 §7.2.5 표 본문화 (7개 시장).
# 데이터 출처: 각 법령 공식 문서 + FPF (EU AI Act 분석).
_PROFILES: dict[str, RegulationProfile] = {
    "KR": RegulationProfile(
        region_code="KR",
        region_name_ko="대한민국",
        law_keys=("PIPA", "정보통신망법", "생체정보 보호 가이드라인"),
        consent_required=True,
        biometric_sensitive=True,
        delete_response_days=30,
        notes_ko="얼굴 이미지 = 민감정보. 보호자 동의 미성년자 차단. 24h TTL.",
    ),
    "EU": RegulationProfile(
        region_code="EU",
        region_name_ko="유럽연합",
        law_keys=("GDPR Art.9", "EU AI Act §5(g)"),
        consent_required=True,
        biometric_sensitive=True,
        delete_response_days=30,
        notes_ko="민감 특성(인종·정치·종교·성지향) 생체 범주화 금지. "
                 "감정 추론 직장/교육 환경 금지. 명시적 동의 Art.9(2)(a).",
    ),
    "UK": RegulationProfile(
        region_code="UK",
        region_name_ko="영국",
        law_keys=("UK GDPR", "DPA 2018"),
        consent_required=True,
        biometric_sensitive=True,
        delete_response_days=30,
        notes_ko="EU GDPR 준용. AI Act는 미적용이나 ICO 가이드 따름.",
    ),
    "US-CA": RegulationProfile(
        region_code="US-CA",
        region_name_ko="미국 캘리포니아",
        law_keys=("CCPA", "CPRA"),
        consent_required=True,
        biometric_sensitive=True,
        delete_response_days=90,
        notes_ko="명시적 동의 화면 + 90일 내 삭제 요청 응답 SLO.",
    ),
    "US-IL": RegulationProfile(
        region_code="US-IL",
        region_name_ko="미국 일리노이",
        law_keys=("BIPA",),
        consent_required=True,
        biometric_sensitive=True,
        delete_response_days=30,
        notes_ko="생체정보 사전 서면 동의 의무. 위반 시 개인 소송권 발생.",
    ),
    "JP": RegulationProfile(
        region_code="JP",
        region_name_ko="일본",
        law_keys=("APPI",),
        consent_required=True,
        biometric_sensitive=True,
        delete_response_days=30,
        notes_ko="요배려 개인정보. 한국 PIPA 준용 권고 (보존 기간 단축).",
    ),
    "CN": RegulationProfile(
        region_code="CN",
        region_name_ko="중국",
        law_keys=("PIPL", "데이터안전법"),
        consent_required=True,
        biometric_sensitive=True,
        delete_response_days=15,
        notes_ko="데이터 현지화 필수. 현지 서버 미충족 시 시장 진입 차단.",
    ),
}


def get_regulation_profile(region: str | None) -> RegulationProfile:
    """로케일 코드 → 규제 프로파일. 미지 지역은 가장 엄격한 EU 프로파일 반환.

    Args:
        region: 'KR' / 'EU' / 'UK' / 'US-CA' / 'US-IL' / 'JP' / 'CN' / None

    Returns:
        해당 프로파일. None 또는 미지 지역은 EU (가장 엄격) fallback.
    """
    if not region:
        return _PROFILES["EU"]  # 알 수 없으면 가장 엄격한 기본값
    key = region.upper().strip()
    # 'EN-US' 같은 BCP-47 → 'US' 변환
    if key.startswith("EN-US"):
        key = "US-CA"
    elif key.startswith("KO"):
        key = "KR"
    elif key.startswith("JA"):
        key = "JP"
    elif key.startswith("ZH"):
        key = "CN"
    elif key.startswith("EN-GB"):
        key = "UK"
    return _PROFILES.get(key, _PROFILES["EU"])


def is_biometric_inference_restricted(region: str | None) -> bool:
    """EU AI Act §5(g) 위반 위험이 있는 추론 — 인종·정치·종교·성지향 분류 차단.

    본 앱은 그런 추론을 하지 않지만, 향후 메트릭이 확장될 때 차단해야 할
    지역인지 빠르게 판정.
    """
    profile = get_regulation_profile(region)
    # EU와 UK는 명시적으로 §5(g)/UK GDPR 적용
    return profile.region_code in ("EU", "UK")


def list_supported_regions() -> list[str]:
    """현재 모듈이 분류 가능한 시장 코드 목록."""
    return sorted(_PROFILES.keys())
