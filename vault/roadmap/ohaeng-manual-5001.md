---
type: roadmap
status: partial_completed
priority: low
report_section: §4
created: 2026-05-17
updated: 2026-05-17
blocked_by: 학파 결정 + 자원오행 보고서
estimated_effort: 1-2 weeks (5001자 정리)
related_adr: [decisions/ADR-003-unihan-fallback, decisions/ADR-027-resource-ohaeng-kci-option-c]
partial_applied:
  - "94자 KCI 학설 매핑 본문화 (ADR-027, 2026-05-17)"
  - "옵션 C 신규 필드 `resource_ohaeng_kci` 추가"
  - "옵션 A 부수 매핑 보존 + 충돌 6건 명시"
remaining:
  - "~4,900자 잔여 (학파 자료 추가 의뢰 필요)"
  - "신규 1,407자(ADR-026) KCI 매핑 (학술 출처 부재)"
  - "§6 disputed 5자 primary+alternative 구조 (ADR-028 후보)"
---

# 자원오행 5001자 수동 매핑 (§4) — 부분 완료

## 진행 상황 (2026-05-17)

✅ **1차 부분 완료**: 외부 보고서 "자원오행 5001자 매핑 조사" §대규모 매핑
데이터 94자 KCI 학설 매핑 본문화 (ADR-027). 보고서 표제 5001자 대비
1.9% 달성, 잔여 ~4,900자.

→ [[../done/resource-ohaeng-kci-94chars]]
→ [[../reports/resource-ohaeng-kci-mapping]]
→ [[../references/name-resource-ohaeng-kci]]

## 잔여 작업

# 자원오행 5001자 수동 매핑 (§4)

## 무엇

현 8525자 중 부수 기반 자동 매핑 가능한 3524자 외에 추상 부수 5001자의
자원오행을 수동 정리.

## 왜

- 자원오행은 작명 추천(자원오행 매칭)의 핵심 점수
- 5001자 미정 = 추천 풀에서 가점 받지 못함

## 필요한 외부 입력

→ **정밀 프롬프트**: [[../templates/PROMPT_ohaeng-manual-5001]] (ADR-010 사실성 분리 요구사항 포함)

### 학파별 추상 부수 → 자원오행 매핑 합의

- 亠·勹·宀·力·土·又 같은 추상 부수
- 학파별 차이: 通義·人 부수는 木인가 火인가?
- 채택 학파의 매핑 규칙 명시

### 또는 한자별 직접 매핑 표

- 5001자 × 木火土金水 = JSON 표
- 출처 학파 + 사유

## 본문화 계획

### 데이터 추가만

`data/korean_hanja_unihan.json`의 `resource_ohaeng` 필드 채우기.
코드 변경 0. 데이터 갱신 후 `name_unihan` 자동 반영.

### 부분 수용 가능

5001자 한꺼번에 아닌 단계적:
- 1차: 자주 쓰이는 인명용 한자 우선 (1000자)
- 2차: 나머지 점진

## 우선순위 낮은 이유

- 작명 추천은 8525자 중 자원오행 매핑된 3524자만으로도 충분히 작동
- 5001자 정리는 정확도 ↑이지만 한계 효용 감소
- 비용 큰 작업 (1~2주)
