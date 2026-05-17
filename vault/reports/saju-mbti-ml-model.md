---
type: external_report
status: received_with_caveats
date: 2026-05-17
source: deepresearch
domain: saju
applied_to: []
neo4j_synced: false
factuality: high_risk
related:
  - reports/saju-mbti-correlation.md
  - decisions/ADR-002-saju-option-A.md
  - decisions/ADR-010-name-sibling-factuality.md
  - decisions/ADR-006-legaltech-rejected.md
original_file: ../../사주팔자와 성명학 데이터를 활용한 머신러닝 기반 MBTI 예측 모델 구축 및 구현 가이드.md
---

# 사주-성명학 → MBTI ML 예측 모델 — 사실성 검토 (거부)

## 보고서 요약

[[saju-mbti-correlation]] 보고서의 매핑을 ML 모델로 코드화. 억부 점수, 십성 → MBTI 4축 feature engineering, 트리 기반 분류기 학습.

## 본 보고서는 [[saju-mbti-correlation]]의 파생물

전제 보고서의 매핑(사주 십성 ↔ MBTI 4축)을 그대로 채택하여 ML 학습용 feature
공학으로 확장. **전제 보고서가 거부됐으므로 본 보고서도 같은 사유로 거부**.

## 추가 위험 (ML 특화)

### 1. ❌ "강력한 통계적 유의성" 단정

ML 모델 구축을 위해서는 학습 데이터셋 + 라벨이 필요한데, 본 보고서는:
- 데이터셋 출처 명시 없음
- 라벨(MBTI 정답) 수집 방법 없음
- 검증·테스트 분할 방법 없음
- 성능 지표(정확도·F1) 0건

### 2. ❌ "성명학 ↔ 후천적 페르소나" 가설

본 보고서의 핵심 가설 — 성명(사용자 이름)이 후천적 MBTI에 영향. 검증 불가능한 형이상학적 인과 주장. 본 프로젝트 ADR-010 도그마 분류.

### 3. ❌ 학술적·법적 위험

- 심리 검사(MBTI) 결과를 사주·성명으로 예측하는 모델은 한국 심리검사법 / 면허 문제 가능
- 사용자에게 "AI가 당신의 MBTI를 예측합니다" 같은 출력은 의료법 §27 (의료 자문) 회피 정신과 충돌 가능 ([[../decisions/ADR-006-legaltech-rejected]])

### 4. ❌ 본 프로젝트 사주 옵션 A와 정면 충돌

본 프로젝트는 [[../decisions/ADR-002-saju-option-A]]에서 **학파 분쟁 회피 → 단순 오행 카운팅** 채택. 본 보고서는 억부법 + 조후 + 조토/습토 예외 처리까지 학파 선택을 강요. ADR-002 위반.

## 본 시스템 반영

### ❌ 채택 거부

본 보고서 전면 거부. 사유:
1. 전제 보고서 [[saju-mbti-correlation]] 거부 사유 그대로 적용
2. ML 학습 데이터 부재
3. 학술적·법적 위험
4. ADR-002 사주 옵션 A 위반
5. ADR-006 자문 거절 정신과 충돌 가능

### 🟡 시사점 (학습용 보관만)

- 만세력 라이브러리 `sajupy` 언급 — 본 프로젝트는 자체 `engine/saju/pillars.py` 사용 중. 비교 검토 가치는 있음
- 억부법·조후·조토/습토 알고리즘 — 명리학 학파 채택 결정 시 참고 가능 ([[../roadmap/saju-option-B-school]])

### ❌ ML 모델 구축 결정

본 프로젝트에 MBTI **예측** ML 모델 도입 거부:
- 결정론 엔진 원칙 위반 (CLAUDE.md §0)
- 환각·오류 시 사용자 영향 큼
- 학습 데이터 미확보
- 사용자 입력 MBTI를 받아 결정론 매핑(현 [engine/saju/mbti_functions.py](../../engine/saju/mbti_functions.py))으로 충분

## 신뢰성 평가

| 항목 | 평가 |
|---|---|
| 만세력 알고리즘 설명 | ✅ 사실 |
| 억부법·조후 알고리즘 | ✅ 명리학 학설 (단, 학파 채택 필요) |
| MBTI ↔ 십성 매핑 | 🔴 [[saju-mbti-correlation]] 거부 사유 |
| ML 모델 구축 가능성 | 🔴 데이터·라벨 부재 |
| 본 프로젝트 적합성 | 🔴 ADR-002·006·010 모두 위반 |

## 다음 액션

- [ ] **결정**: 본 보고서 반영 거부
- [ ] (보류) 만세력 라이브러리 sajupy vs 자체 pillars.py 비교 — SaaS 운영 후 검토
- [ ] (보류) 억부·조후 알고리즘 — [[../roadmap/saju-option-B-school]] 학파 결정 시 참고

## 출처

- 본 보고서 원본: `사주/사주팔자와 성명학 데이터를 활용한 머신러닝 기반 MBTI 예측 모델 구축 및 구현 가이드.md`

## 메타

- 영속화: 2026-05-17 (ADR-010 사실성 분리, 거부)
- ADR-010 사례 7호 — 거부 사례 2호
- 본 노트 immutable
