---
type: external_report
status: rejected_mostly
date: 2026-05-17
source: 외부 작성 (사용자 제공 딥리서치)
domain: dream_agent
applied_to: []
permanently_rejected:
  - "§2 학파 (Jung·Fromm·Foulkes) — ISBN 9781032601144 중복 데이터 오류 (Jung·Fromm 동일 ISBN, 물리적 불가능) + ADR-002 옵션 A 학파 회피 위반"
  - "Foulkes 'Group Analytic' — ISBN 미명시, 일반 용어만 (검증 불가)"
  - "§3 시대별 클러스터 6개 — symbols 필드 6건 모두 공란 (라인 36·42·48·54·60·66) = 빈 약속"
  - "§4 cluster_social_unconscious 함수 — 'Placeholder for actual clustering logic' 라인 99 (구현 미완)"
  - "§5 KCI 논문 6건 — '예: ...' 일반화 인용 (구체 저자·연도 미명시)"
  - "§7 회귀 20쌍 — expected_cluster_candidates 필드 모두 공란 (테스트 스켈레톤만)"
  - "§2.3 소셜 미디어 가설 — 실증 사례 0"
deferred_pending_data:
  - "C2 6개 클러스터 symbols 데이터 (사용자/보고서 저자 보완 필요)"
  - "C3 clustering logic 구체 구현 (NLP keyword + 가중치 함수)"
  - "C1 Foulkes 저작 ISBN 라이브 검증 + KCI 논문 3~5건 구체 인용"
already_implemented:
  - "social_unconscious.py v2 (Lawrence 소셜 드리밍 매트릭스, 161줄)"
  - "min_users=30, min_entries=100 운영 데이터 임계값 (보고서 §6 ACCEPT 영역 이미 구현)"
  - "ADR-010 사실성 분리 면책 자동 (interpretive_note + principle 필드)"
  - "ADR-014 단정 회피 정신"
related_adr: [ADR-002, ADR-010, ADR-014, ADR-021, ADR-023]
adr_017_first_application: "2026-05-17 (squeeze-report 16회째 — ADR-017 두 번째 ZERO 사례 추정)"
original_file: ../../../사회적 무의식, 집단 무의식 및 한국 시대 문화 클러스터링 학술 근거 보고서.md
adopted_option: "거부 (대부분) — ISBN 중복 오류 + 빈 약속 다수 + ADR-002 위반"
---

# 사회적 무의식·집단 무의식 학술 근거 — 대부분 영구 거부

## 보고서 요약

357줄, 27KB. A13 social_unconscious v3 (engine/agents __init__ TODO 영역)
대상. Jung 집단 무의식 + Fromm 사회적 무의식 + Foulkes Group Analytic +
한국 시대별 클러스터 6개 (1910~2025).

**핵심 결함**:
1. **ISBN 데이터 오류**: 9781032601144가 Jung·Fromm 동일 ISBN으로 명시 (물리적 불가능)
2. **symbols 6건 모두 공란** (시대 클러스터 빈 약속)
3. **clustering logic placeholder** (라인 99)
4. **회귀 20쌍 expected 모두 공란** (테스트 스켈레톤만)
5. **KCI 논문 일반화 인용** ("예: ...")

## 🟢 팩트 (부분 검증)

- Jung 집단 무의식 (1934/1968) — 학문적 사실
- Fromm 사회적 무의식 (1956) — 학문적 사실
- 한국 시대 구분 (1910~2025) 6개 — 역사적 사실

## 🟡 구조 (조건부)

- cluster_social_unconscious 함수 명세 (placeholder만)
- 사용자 출력 면책 가이드라인 (C4 — 이미 부분 구현)
- 운영 데이터 의존성 (C5 — 이미 구현 min_users=30)

## 🔴 영구 거부

| 영역 | 사유 |
|---|---|
| ISBN 9781032601144 중복 | 데이터베이스 물리 오류 (Jung·Fromm 동일 ISBN 불가능) |
| Foulkes ISBN | 미명시 (Group Analytic 일반 용어만) |
| 시대 클러스터 symbols 공란 | 6건 모두 빈 약속 (라인 36·42·48·54·60·66) |
| clustering logic placeholder | 함수 명세만, 실 구현 0 (라인 99) |
| 회귀 20쌍 expected 공란 | 테스트 스켈레톤만, 검증 불가 |
| KCI 논문 일반화 | "예: ..." 구체 저자·연도 미명시 |
| 소셜 미디어 가설 | 실증 0 |
| ADR-002 학파 명시 | Jung·Fromm·Foulkes 학파 강요 (옵션 A 회피 위반) |

## 본 시스템 반영 (코드 변경 0건)

### REJECT 영역 (1건)

- **C1 학파 (Jung·Fromm·Foulkes)**: ISBN 중복 오류 + ADR-002 위반

### DEFER 영역 (2건)

- **C2 시대 클러스터**: symbols 보완 + KCI 구체 인용 후 재검토
- **C3 clustering logic**: NLP 구현 후 재검토 (운영 데이터 의존)

### ACCEPT 영역 (2건, 신규 작업 미세)

- **C4 사용자 출력 면책**: 이미 부분 구현 (social_unconscious.py interpretive_note)
  - 추가 작업: validate_social_unconscious_output() 함수만 추가 가능 (작은 작업)
- **C5 운영 데이터 의존성**: 이미 완전 구현 (min_users=30, min_entries=100)
  - 추가 작업: 0건

## 본 호출 본문화 결정: 0건 (현 상태 유지)

ACCEPT 2건 모두 이미 부분 또는 완전 구현됨. 신규 본문화 가치 매우 제한적:
- C4 validate 함수: 단독 ADR 가치 0 (기존 패턴 보강)
- C5: 이미 완료

DEFER 2건 (C2·C3)이 본 보고서의 핵심이나, 모두 빈 약속 (symbols 공란 +
placeholder logic). 보고서 본문 명시 영역 없이 본문화 불가.

## ADR-017 절차 16회째 — 두 번째 ZERO 사례

| 순 | 영역 | 결과 |
|---|---|---|
| 14 | 사주-MBTI 가상 데이터 | **첫 ZERO** (가상 데이터 영구 거부) |
| 15 | 한국 성씨 300위 | 24 PASS (ADR-033) |
| **16** | **사회적 무의식 (본 보고서)** | **두 번째 ZERO** (빈 약속·ISBN 오류 영구 거부) |

### 분석/판정 vs 오케스트레이터

- 분석 (Haiku): 5 후보 + 거부 4건 + 빈 약속 4건 + ISBN 데이터 오류 식별
- 판정 (Haiku): ACCEPT 2 (C4·C5) + REJECT 1 (C1) + DEFER 2 (C2·C3)
- **오케스트레이터**: 보고서 본문 직접 검증 — ISBN 중복·symbols 공란·placeholder·expected 공란 모두 확인. C4·C5 이미 구현됨 → 신규 본문화 작업 0건. 판정 결과 그대로 채택.

## ADR-014 정신 적용

본 시스템 ADR-014 saju→MBTI 예외 패턴: 단정 회피 + 면책 강제. 본 보고서가
요구하는 "집단 무의식 + 시대 클러스터" 매칭은 동일 위험 (개인 운명 인과
단정 가능성). ADR-014 정신 정합 영구 거부.

## 신뢰성 평가

| 항목 | 평가 |
|---|---|
| Jung·Fromm 학문적 존재 | ✅ (단 ISBN 데이터 오류) |
| Foulkes ISBN | ❌ 미명시 |
| 시대 클러스터 symbols | ❌ 6건 공란 |
| clustering logic | ❌ placeholder |
| 회귀 expected | ❌ 20건 공란 |
| KCI 구체 인용 | ❌ 일반화 |
| 본 프로젝트 적합성 | ❌ 본문화 가치 0 |

## 향후 작업 (사용자 결정 후 재시도)

- Foulkes ISBN 라이브 검증 + references/ 영속화
- 6개 클러스터별 symbols 10~15개 보완
- KCI 논문 3~5건 구체 인용
- clustering logic NLP 구현
- 회귀 20쌍 expected 채우기
- user_birth_year 가중치 함수 설계 (사업 결정)

위 모든 영역 보완 후 재호출 시에만 본문화 가치 발생.

## 메타

- 영속화: 2026-05-17 (ADR-017 16회째)
- **두 번째 본문화 가치 0 사례** (첫: 사주-MBTI 가상 데이터)
- 보고서 ISBN 데이터 오류 + 빈 약속 다수로 영구 거부
- A13 social_unconscious.py v2 유지 (Lawrence 소셜 드리밍 매트릭스)
- engine/agents __init__ TODO 라인 18 (v3 DB 클러스터링) 유지 (보강 후 재호출)
- 사용자 자율 정신 정합 — 합리적 거부, 영속화로 재발 차단
- 본 노트 immutable
