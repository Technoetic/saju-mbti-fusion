"""ancestor 도메인 — palm 8 카드 중 '조상님의 메시지' 결정론 산출 모듈.

학술 근거 (ADR-122·123·124):
  - 한국학중앙연구원 한국민족문화대백과사전 — 조상굿·진오기굿·새남굿 표제
  - 국립민속박물관 한국민속대백과사전 — 4 지역 위령 의례
  - 이능화 (1927) 조선무속고 ISBN 9788936471391 — 삼신/조상신 추상 형이상학
  - 임석재·김태곤·황루시 정통 민속학자 KCI 논문
  - 메트로신문 김상회 칼럼 — 십이신살 천살(天殺) 풍수 방위

본 모듈은 한국 무속 정통 학파 정합 결정론 산출만 제공.
INFEASIBLE 영역 (개인 망자 1인칭 메시지·접신·빙의)는 영구 미본문화.
"""
from .cheonsal import get_cheonsal_direction, CHEONSAL_DIRECTIONS_BY_YEAR_JI
from .vocabulary import ANCESTOR_FLOW_TONE_VOCAB, RECOMMENDED_FLOW_TONES, build_ancestor_prompt_injection
from .regional_rites import REGIONAL_RITES, get_regional_rite

__all__ = [
    "get_cheonsal_direction",
    "CHEONSAL_DIRECTIONS_BY_YEAR_JI",
    "ANCESTOR_FLOW_TONE_VOCAB",
    "RECOMMENDED_FLOW_TONES",
    "build_ancestor_prompt_injection",
    "REGIONAL_RITES",
    "get_regional_rite",
]
