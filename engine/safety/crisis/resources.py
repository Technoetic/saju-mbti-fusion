"""국가별 위기 응답 자원 라우터 — 운영표준 §7.2.12 본문화.

사용자 지역에 따라 자살예방·정신건강 위기 핫라인을 라우팅한다.
한국(1393/1577-0199) 외에도 EU·미국·일본·중국·영국 등 주요 시장의
공식 핫라인을 단일 진실 원천으로 정리.

§7.2.11 위기 응답 페이로드와 함께 사용:
  - detect_crisis가 위기 감지
  - get_crisis_resources(region)로 지역별 핫라인 반환
  - 응답 본문 + crisis_alert.hotlines 에 동봉

출처: 각국 보건복지부·NGO 공식 자료 (운영표준 §7.2.12 표).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CrisisHotline:
    """단일 위기 핫라인 정보."""
    name_ko: str          # 한국어 이름
    name_local: str       # 현지 공식 이름
    phone: str            # 전화번호 (국제 표기)
    available_24h: bool   # 24시간 운영 여부
    language: str         # 주 사용 언어 ('ko', 'en', 'ja', 'zh', 'multi')


# 지역별 핫라인 매핑 — 운영표준 §7.2.12 본문화
_CRISIS_HOTLINES: dict[str, list[CrisisHotline]] = {
    "KR": [
        CrisisHotline(
            name_ko="자살예방상담전화",
            name_local="자살예방상담전화",
            phone="1393",
            available_24h=True,
            language="ko",
        ),
        CrisisHotline(
            name_ko="정신건강위기상담전화",
            name_local="정신건강위기상담전화",
            phone="1577-0199",
            available_24h=True,
            language="ko",
        ),
        CrisisHotline(
            name_ko="청소년전화",
            name_local="청소년전화",
            phone="1388",
            available_24h=True,
            language="ko",
        ),
    ],
    "EU": [
        CrisisHotline(
            name_ko="유럽 자살예방 표준 번호",
            name_local="European Emergency Number",
            phone="112",
            available_24h=True,
            language="multi",
        ),
        CrisisHotline(
            name_ko="텔레폰 사마리탄즈 (다국어)",
            name_local="Telefonseelsorge / Samaritans Network",
            phone="116 123",
            available_24h=True,
            language="multi",
        ),
    ],
    "UK": [
        CrisisHotline(
            name_ko="사마리탄즈 (영국)",
            name_local="Samaritans UK",
            phone="116 123",
            available_24h=True,
            language="en",
        ),
        CrisisHotline(
            name_ko="NHS 정신건강 위기",
            name_local="NHS 111 (option 2)",
            phone="111",
            available_24h=True,
            language="en",
        ),
    ],
    "US-CA": [
        CrisisHotline(
            name_ko="988 자살·위기 라이프라인",
            name_local="988 Suicide & Crisis Lifeline",
            phone="988",
            available_24h=True,
            language="en",
        ),
        CrisisHotline(
            name_ko="위기 텍스트 라인",
            name_local="Crisis Text Line",
            phone="Text HOME to 741741",
            available_24h=True,
            language="en",
        ),
    ],
    "US-IL": [
        CrisisHotline(
            name_ko="988 자살·위기 라이프라인",
            name_local="988 Suicide & Crisis Lifeline",
            phone="988",
            available_24h=True,
            language="en",
        ),
    ],
    "JP": [
        CrisisHotline(
            name_ko="요리소이 핫라인",
            name_local="よりそいホットライン",
            phone="0120-279-338",
            available_24h=True,
            language="ja",
        ),
        CrisisHotline(
            name_ko="이노치노 덴와",
            name_local="いのちの電話",
            phone="0570-783-556",
            available_24h=False,
            language="ja",
        ),
    ],
    "CN": [
        CrisisHotline(
            name_ko="베이징 자살예방연구센터",
            name_local="北京心理危机研究与干预中心",
            phone="010-82951332",
            available_24h=True,
            language="zh",
        ),
        CrisisHotline(
            name_ko="국가심리지원 핫라인",
            name_local="全国心理援助热线",
            phone="400-161-9995",
            available_24h=True,
            language="zh",
        ),
    ],
}


def get_crisis_resources(region: str | None) -> list[CrisisHotline]:
    """지역 → 위기 핫라인 목록. 미지 지역은 한국(KR) fallback.

    Args:
        region: 'KR' / 'EU' / 'UK' / 'US-CA' / 'US-IL' / 'JP' / 'CN' / 로케일

    Returns:
        해당 지역 핫라인 목록. 빈 목록은 절대 반환하지 않음 (KR 최소 보장).
    """
    if not region:
        return _CRISIS_HOTLINES["KR"]
    key = region.upper().strip()
    # BCP-47 로케일 매핑
    if key.startswith("KO"):
        key = "KR"
    elif key.startswith("JA"):
        key = "JP"
    elif key.startswith("ZH"):
        key = "CN"
    elif key.startswith("EN-GB"):
        key = "UK"
    elif key.startswith("EN-US"):
        key = "US-CA"
    return _CRISIS_HOTLINES.get(key, _CRISIS_HOTLINES["KR"])


def format_hotlines_text(hotlines: list[CrisisHotline]) -> str:
    """위기 응답 본문에 부착할 핫라인 텍스트 — 사극풍 어조와 호환."""
    if not hotlines:
        return ""
    lines = []
    for h in hotlines:
        avail = "24시간" if h.available_24h else "주간"
        lines.append(f"  • {h.name_ko} ({h.name_local}) — {h.phone} ({avail})")
    return "\n".join(lines)


def list_supported_crisis_regions() -> list[str]:
    """위기 자원 매핑된 시장 코드 목록."""
    return sorted(_CRISIS_HOTLINES.keys())
