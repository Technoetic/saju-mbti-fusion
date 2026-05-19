"""engine.divination.name — 성명학 도메인 서브패키지 (ADR-039)

이전 평면 구조 (engine/divination/name_*.py 16개)에서 본 서브폴더로 이전.

import path 변경 (구→신):
  name_strokes  →  name.strokes
  name_scoring  →  name.scoring
  name_aesthetic, name_baleum, name_bulyong, name_dueum, name_eumyang,
  name_gaeja, name_gaemyeong, name_hangul_hanja, name_reading,
  name_saju_ohaeng, name_saju_school, name_sibling_preference,
  name_unihan, name_uniqueness  (총 16개)

본 패키지의 모든 모듈은 명시 import 권장:
  from engine.divination.name.strokes import kangxi_strokes
"""
