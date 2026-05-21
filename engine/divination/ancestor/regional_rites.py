"""4 지역 위령 의례 백과사전 메타.

학술 근거 (ADR-124):
  - 한국민속대백과사전 (folkency.nfm.go.kr) — 진오기굿·새남굿·오구굿·씻김굿·망묵이굿 표제
  - 한국학중앙연구원 한국민족문화대백과사전 (encykorea.aks.ac.kr) — 조상굿·대택굿 표제

본 모듈은 사용자 출신 지역 또는 정보 제공 목적으로 4 권역 위령 의례의
정통 학술 명칭·정의·출처를 결정론 매핑한다.
"""
from __future__ import annotations

from typing import Dict, List, Optional


REGIONAL_RITES: Dict[str, Dict[str, object]] = {
    "수도권": {
        "region_ko": "수도권 (서울·경기)",
        "rites": ["진오기굿", "새남굿"],
        "definition": (
            "서울 지역 본격 망자 천도(遷度)굿. 새남굿은 쌍계새남·수팔년꽃 장식·"
            "방망이떡 등 화려한 물질문화가 동반된 상류층 대상 대규모 천도 의례."
        ),
        "source_urls": [
            "https://folkency.nfm.go.kr/kr/topic/detail/2858",
            "https://folkency.nfm.go.kr/topic/detail/2323",
        ],
    },
    "경상도": {
        "region_ko": "경상도 (동해안·남해안)",
        "rites": ["오구굿", "동해안별신굿", "수륙새남굿"],
        "definition": (
            "동해안 세습무 특유의 천도 의례. 무당들 사이 은어 '밤쩌(夜祭)'. "
            "남해안 수륙새남굿은 사령제 계통 한을 풀고 부정을 가시게 함."
        ),
        "source_urls": [
            "https://folkency.nfm.go.kr/topic/%EB%8F%99%ED%95%B4%EC%95%88%EC%98%A4%EA%B5%AC%EA%B5%BF",
            "https://folkency.nfm.go.kr/topic/detail/1874",
        ],
    },
    "전라도": {
        "region_ko": "전라도",
        "rites": ["씻김굿"],
        "definition": (
            "죽은 자의 영혼에 묻은 부정을 깨끗이 씻어내어 극락으로 보내는 천도 의례. "
            "서울 진오기굿에 대응하는 남부 지방 대표 사령제."
        ),
        "source_urls": [
            "https://folkency.nfm.go.kr/topic/%EB%82%A8%ED%95%B4%EC%95%88%EC%98%A4%EA%B5%AC%EA%B5%BF",
        ],
    },
    "북부": {
        "region_ko": "북부 (함경도·평안도)",
        "rites": ["망묵이굿", "다리굿"],
        "definition": (
            "함경도 일대 망자 천도 의례. 임석재 조사 22 세부 굿거리(부정풀이 등) "
            "체계화. 평안도 '다리'는 이승-저승 상징성 극대화."
        ),
        "source_urls": [
            "https://folkency.nfm.go.kr/topic/%EB%A7%9D%EB%AC%B5%EC%9D%B4%EA%B5%BF",
        ],
    },
}


def get_regional_rite(region_key: str) -> Optional[Dict[str, object]]:
    """4 권역 키 → 위령 의례 메타.

    Args:
        region_key: '수도권'·'경상도'·'전라도'·'북부' 중 1.

    Returns:
        dict | None: 의례 메타 (region_ko·rites·definition·source_urls).
        키가 4 권역 외 시 None.
    """
    rite = REGIONAL_RITES.get(region_key)
    if rite is None:
        return None
    result = dict(rite)
    result["school"] = "한국학중앙연구원·국립민속박물관 정통"
    result["disclaimer"] = (
        "한국 전통 위령 의례 학술 정보 제공용 — 점술적 단정 X."
    )
    return result


def list_all_regions() -> List[str]:
    """4 권역 키 리스트."""
    return list(REGIONAL_RITES.keys())
