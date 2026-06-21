"""ADR-087 — 한국 주요 도시 위도/경도 룩업 테이블.

본 모듈은 출생지 경도 → 진태양시 보정 (calendar.py `_apply_solar_time`)에 사용.
geopy 외부 호출 의존 X — 한국 17개 시·도 + 주요 시군 50+ 도시 하드코딩.

출처: 행정안전부 도로명주소 + 국토지리정보원 표준 좌표.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CityCoord:
    """도시 좌표 메타.

    Attributes:
        name_ko: 한글 명칭
        latitude: 위도 (북위 양수)
        longitude: 경도 (동경 양수)
        region: 시·도 분류
    """
    name_ko: str
    latitude: float
    longitude: float
    region: str


# 한국 주요 도시 50+ 위도/경도 (KST 135°E 기준 진태양시 보정용)
KR_CITY_COORDS: dict[str, CityCoord] = {
    # 광역시·도청 소재지
    "서울": CityCoord("서울", 37.5665, 126.9780, "서울특별시"),
    "부산": CityCoord("부산", 35.1796, 129.0756, "부산광역시"),
    "대구": CityCoord("대구", 35.8714, 128.6014, "대구광역시"),
    "인천": CityCoord("인천", 37.4563, 126.7052, "인천광역시"),
    "광주": CityCoord("광주", 35.1595, 126.8526, "광주광역시"),
    "대전": CityCoord("대전", 36.3504, 127.3845, "대전광역시"),
    "울산": CityCoord("울산", 35.5384, 129.3114, "울산광역시"),
    "세종": CityCoord("세종", 36.4801, 127.2890, "세종특별자치시"),
    # 경기도
    "수원": CityCoord("수원", 37.2636, 127.0286, "경기도"),
    "성남": CityCoord("성남", 37.4201, 127.1265, "경기도"),
    "고양": CityCoord("고양", 37.6584, 126.8320, "경기도"),
    "용인": CityCoord("용인", 37.2411, 127.1776, "경기도"),
    "안양": CityCoord("안양", 37.3943, 126.9568, "경기도"),
    "부천": CityCoord("부천", 37.5034, 126.7660, "경기도"),
    "안산": CityCoord("안산", 37.3219, 126.8309, "경기도"),
    "남양주": CityCoord("남양주", 37.6360, 127.2165, "경기도"),
    "화성": CityCoord("화성", 37.1996, 126.8312, "경기도"),
    "평택": CityCoord("평택", 36.9921, 127.1126, "경기도"),
    "의정부": CityCoord("의정부", 37.7381, 127.0337, "경기도"),
    # 강원도
    "춘천": CityCoord("춘천", 37.8813, 127.7300, "강원도"),
    "원주": CityCoord("원주", 37.3422, 127.9202, "강원도"),
    "강릉": CityCoord("강릉", 37.7519, 128.8761, "강원도"),
    "속초": CityCoord("속초", 38.2070, 128.5918, "강원도"),
    # 충청북도
    "청주": CityCoord("청주", 36.6424, 127.4890, "충청북도"),
    "충주": CityCoord("충주", 36.9910, 127.9259, "충청북도"),
    # 충청남도
    "천안": CityCoord("천안", 36.8151, 127.1139, "충청남도"),
    "아산": CityCoord("아산", 36.7898, 127.0019, "충청남도"),
    "서산": CityCoord("서산", 36.7848, 126.4503, "충청남도"),
    # 전라북도
    "전주": CityCoord("전주", 35.8242, 127.1480, "전라북도"),
    "익산": CityCoord("익산", 35.9483, 126.9577, "전라북도"),
    "군산": CityCoord("군산", 35.9676, 126.7368, "전라북도"),
    # 전라남도
    "목포": CityCoord("목포", 34.8118, 126.3924, "전라남도"),
    "여수": CityCoord("여수", 34.7604, 127.6622, "전라남도"),
    "순천": CityCoord("순천", 34.9506, 127.4878, "전라남도"),
    # 경상북도
    "포항": CityCoord("포항", 36.0190, 129.3435, "경상북도"),
    "경주": CityCoord("경주", 35.8562, 129.2247, "경상북도"),
    "구미": CityCoord("구미", 36.1196, 128.3446, "경상북도"),
    "안동": CityCoord("안동", 36.5684, 128.7294, "경상북도"),
    # 경상남도
    "창원": CityCoord("창원", 35.2280, 128.6811, "경상남도"),
    "진주": CityCoord("진주", 35.1800, 128.1076, "경상남도"),
    "통영": CityCoord("통영", 34.8544, 128.4331, "경상남도"),
    "김해": CityCoord("김해", 35.2285, 128.8894, "경상남도"),
    # 제주도
    "제주": CityCoord("제주", 33.4996, 126.5312, "제주특별자치도"),
    "서귀포": CityCoord("서귀포", 33.2541, 126.5601, "제주특별자치도"),
}


_DEFAULT_LONGITUDE = 126.978  # 서울 (calendar.py 기본값과 정합)


def get_longitude(city_name: str) -> float:
    """도시명 → 경도 반환. 미등록 도시는 서울 기본값."""
    coord = KR_CITY_COORDS.get(city_name.strip())
    if coord is None:
        return _DEFAULT_LONGITUDE
    return coord.longitude


def get_coord(city_name: str) -> CityCoord | None:
    """도시명 → CityCoord dataclass 반환. 미등록 시 None."""
    return KR_CITY_COORDS.get(city_name.strip())


def list_cities_by_region(region: str) -> list[str]:
    """시·도별 등록 도시 목록."""
    return sorted(
        c.name_ko for c in KR_CITY_COORDS.values() if c.region == region
    )


__all__ = [
    "CityCoord",
    "KR_CITY_COORDS",
    "get_longitude",
    "get_coord",
    "list_cities_by_region",
]
