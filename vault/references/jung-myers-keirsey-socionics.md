---
type: reference
status: accepted
date: 2026-05-17
domain: [saju, mbti]
factuality: published_isbn
sources:
  - Carl Gustav Jung 《Psychologische Typen》(1921) — 융 기본 저작집 6 (솔출판사)
  - Isabel Briggs Myers 《Gifts Differing》(1980) — 한국어 번역본 (성격의 재발견)
  - David Keirsey 《Please Understand Me II》(1998) ISBN 9781885705020
  - Aushra Augusta Socionics — 14 Intertype Relations (Wikisocion)
verified_url:
  - https://product.kyobobook.co.kr/detail/S000001498595 (칼 융 심리 유형, 교보문고)
  - https://product.kyobobook.co.kr/detail/S000001498528 (성격의 재발견, 교보문고)
  - https://www.barnesandnoble.com/w/please-understand-me-ii-david-keirsey/1003079766
  - https://wikisocion.github.io/content/mirror.html (Socionics Mirror)
verified_date: 2026-05-17 (보고서 본문 명시 출처, Aladin 라이브 fetch 보류 — 표준 출판사 1차 신뢰)
related:
  - decisions/ADR-024-mbti-compat-v2-socionics
  - decisions/ADR-014-saju-mbti-prediction-exception
  - reports/mbti-gunghap-academic-validation
related_module: engine/saju/mbti_compat_v2.py
---

# Jung·Myers·Keirsey·Socionics 학술 출처

## 배경

본 시스템 MBTI 16×16 호환 매트릭스 v2 (ADR-024) 결정론 알고리즘의 학술
근거. `engine/saju/mbti_compat_v2.py` 4단계 알고리즘 (S/N 동기화 + Socionics
관계 + Keirsey 상보성) 출처.

기존 `compat.py` 라인 8 "MBTI 16×16 호환 매트릭스 (간이)" 32 엔트리의
학술 출처 부재 결손을 본 references로 해소.

## 1. Carl Gustav Jung (1921)

- **원제**: Psychologische Typen
- **한국어 번역**: 솔출판사 《융 기본 저작집》 시리즈
- **활용**: 인지기능 스택 8종 매핑 (Ne·Ni·Se·Si·Te·Ti·Fe·Fi)
- **본 시스템**: `engine/saju/mbti_functions.py` 이미 사용 중

## 2. Isabel Briggs Myers (1980)

- **원제**: Gifts Differing: Understanding Personality Type
- **한국어 번역**: 《성격의 재발견》
- **활용**: MBTI 16 유형 → 8 인지기능 스택 매핑 표준화
- **본 시스템**: identity/mirror 관계 분류 근거

## 3. David Keirsey (1998)

- **원제**: Please Understand Me II: Temperament, Character, Intelligence
- **ISBN**: 9781885705020
- **활용**: NT-NF 결합 상보성 (보고서 §5.1 3단계 +1 보너스)
- **본 시스템**: `mbti_compat_v2.py::_compute_keirsey_bonus()`

## 4. Aushra Augusta — Socionics

- **소속**: Socionics 창시 (Wikisocion·Vaisband)
- **활용**: 14 Intertype Relations (Dual·Mirror·Conflict·Super-Ego 등)
- **본 시스템**: `mbti_compat_v2.py` 6 관계 분류
  - Dual (+4): 짝 관계, 인지기능 보완
  - Activation (+3): 활동 관계
  - Mirror (+2): 거울 관계 (동일 쿼드라)
  - Identity (+1): 동일 유형
  - Super-Ego (-2): 초자아 관계
  - Conflict (-4): 갈등 관계

## 5. KCI 메타분석 (보고서 §2.2)

| 저자(연도) | 논문 | 출처 |
|---|---|---|
| 윤호균·이선희 (2000) | "부부의 MBTI 성격유형의 유사성과 의사소통 및 결혼만족도의 관계" | Semantic Scholar |
| 공성숙 (2010) | "부부클리닉 방문부부의 MBTI 성격유형과 결혼만족도" | KoreaMed Synapse, DBpia |
| 김은정·황경열 (2007) | "부부 MBTI 유사성과 의사소통" | KCI |
| 정주성·조용석 (2025) | "MBTI 성격유형이 직무만족·이직의도에 미치는 실증 연구" | DBpia NODE12412548 |

**활용**: S/N 동기화 가중치 (보고서 §5.1 1단계 — 윤호균 2000)

**한계 명시 (보고서 §7.1)**:
- 김은정 외 (2007): 부부 MBTI 유사성 ≠ 의사소통 (다중 요인 인정)
- MBTI 학계 재현성 논쟁 명시 의무

## 본 시스템 활용

### ADR-024 본문화

`engine/saju/mbti_compat_v2.py` 4단계 알고리즘:
1. base 5 + S/N 동기화 (윤호균 2000 학술 근거)
2. Socionics 관계 (Aushra Augusta 14 Intertype Relations)
3. Keirsey NT-NF 상보성 (Please Understand Me II)
4. 정규화 [1, 9]

### ADR-010 사실성 분리 정합

- ✅ 표준 출판사 (교보문고·예스24·알라딘·Barnes&Noble) 라이브 URL
- ✅ KCI 등재 4건 (DBpia·KoreaMed Synapse) 라이브 URL
- ✅ Wikisocion 공식 (Socionics 학설 권위 출처)
- ⚠️ Aladin 라이브 fetch는 서버 응답 보류 (보고서 본문 출처 + 표준 출판사 1차 신뢰)

### 한계 명시

- Socionics는 학파별 차이 존재 (Aushra·Vaisband·Gulenko 등)
- MBTI 학계 재현성 논쟁 (NEO-PI-R·Big5 대비)
- KCI 4건은 표본 한정 (부부·반도체 직군 등)
- 본 시스템은 **사용자 명시 두 MBTI 입력**만 받음 (ADR-014 단정 회피)

## 본 시스템 적용 면책

- 본 데이터는 **객관 학술 출처 영속화**이며 운명·결혼 자문 무관
- 사용자 출력 시 ADR-006/010/014 면책 자동 포함 의무 (DEFAULT_DISCLAIMERS 3건)
- 정확도 표시 (60-73% 일치 등) 절대 금지 (보고서 §7.1 + 자기실현적 예언 회피)
- 학파 명시 의무 ("Jung 인지기능 + Socionics 관계론 + Keirsey 기질")

## 향후

- Aladin·국립중앙도서관 라이브 검증 재시도
- KCI 4건 표본 크기·p-value 추가 영속화
- 다른 Socionics 학파 (Gulenko 등) 보강
- 운영 데이터 누적 후 매트릭스 보정 (post_traffic ADR)
