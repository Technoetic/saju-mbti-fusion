---
type: external_report
status: applied_partially
date: 2026-05-17
source: 외부 작성 (사용자 제공 딥리서치)
domain: name
applied_to: [§대규모 매핑 데이터 94자 (옵션 C KCI 학설 매핑)]
rejected:
  - "참고 자료 URL 3개 (skymap·fiveluck·hanname.com) — ECONNREFUSED"
deferred_pending_data:
  - "§대규모 매핑 데이터 표제 vs 실제 94자 (5001자 대비 1.9%)"
  - "§6 disputed characters 처리 (primary+alternative 스키마 변경) — 별도 ADR 후보"
  - "신규 1,407자(ADR-026) KCI 매핑 (학술 출처 부재)"
already_implemented:
  - "본 시스템 부수 자동 매핑 (옵션 A) — name_unihan.py resource_ohaeng (3,524자, 35.5%)"
related_adr: [ADR-026, ADR-027]
adr_017_first_application: "2026-05-17 (squeeze-report 8회째)"
original_file: ../../../자원오행 5001자 매핑 조사.md
adopted_option: "C — 옵션 C 신규 필드 추가 (resource_ohaeng_kci) + 옵션 A 보존 + 충돌 6건 명시"
---

# 자원오행 5001자 매핑 조사 — 옵션 C 94자 본문화

## 보고서 요약

272줄, 51KB. 자원오행(字源五行) 매핑 3가지 옵션(A·B·C) 비교 후
옵션 C 채택 권장. 추상·복합 부수 매핑 논리(宀·亠·力·勹·又) + 오상
5문자(仁義禮智信) + 계절(春夏秋冬) + 방위(東南西北) + 빈출 회의/형성
문자 = 94자 JSON 형식 매핑 데이터 본문 명시.

학술 출처: 김기승·이재승·김만태 (KCI 검증 통과).

## 🟢 팩트 (검증 통과)

| 주장 | 검증 |
|---|---|
| 이재승·김만태 KCI 논문 (2018) | ✅ DOI 10.33645/cnc.2018.06.40.3.339 |
| 이재승 KCI 논문 (2024) — 214 부수 자원 배속 | ✅ shss.kr 확인 |
| 이재승 『명리·용신 성명학 원론』 ISBN 9791173182693 | ✅ 교보문고 |
| 김기승 『자원오행 성명학』 (다산글방) | ✅ 알라딘/교보 |
| 옵션 비교표 논리 | ✅ 옵션 B 비판 타당 |
| 94자 본문 JSON 데이터 (라인 160-256) | ✅ 실제 데이터 존재 |
| 본 시스템 결손 영역 매칭 | ✅ resource_ohaeng 35.5%만 보유 |

## 🟡 구조 (시스템 설계 명제)

- 옵션 C 학설 매핑 방법론 (자원·본의 형태론 추적)
- 부수별 배속 논리 (宀·亠·力·勹·又)
- 오상/계절/방위 한자 자동 매핑 가능

## 🔴 도그마 / 빈 약속 (영구 거부)

| 영역 | 사유 |
|---|---|
| 보고서 표제 "5001자 매핑 데이터" | 실 본문 94자 (1.9% 미충족) → 정직 명시 의무 |
| 강희자전·금문 본문 인용 | 보고서가 학파 KCI 참조만 명시, 자전 직접 인용 0 |
| 참고 자료 URL 3개 (skymap·fiveluck·hanname) | ECONNREFUSED 라이브 검증 실패 |
| §6 disputed 5자 본 보고서 본문화 | 스키마 변경 (string→dict) → 별도 ADR 후보 |

## 본 시스템 반영 (적용 완료)

### 채택 영역 (ADR-027)

- 94자 KCI 학설 매핑 → `data/korean_hanja_unihan.json` 신규 3 필드
  (`resource_ohaeng_kci`, `kci_reason`, `kci_school_source`) 주입
- 본 시스템 API 5개 신규 (`resource_ohaeng_kci`, `kci_reason`,
  `kci_school_source`, `preferred_ohaeng`, `total_with_kci`)
- 회귀 테스트 13건 신규 (옵션 A·C 충돌 명시 + 학파 출처 검증 +
  결정론 + 면책 데이터)
- 옵션 A vs 옵션 C 충돌 6건 명시 보존 (덮어쓰기 X)

### 거부 영역 (영구)

- 보고서 표제 "5001자 매핑 데이터" → ADR-010 빈 약속
- 참고 자료 URL 3개 라이브 검증 실패
- §6 disputed 스키마 변경 → 본 보고서 범위 외

### 보류 영역

- 신규 1,407자 KCI 매핑 (학술 출처 부재)
- §6 disputed 5자 primary+alternative 구조 (별도 ADR 후보)
- 보고서 표제 5001자 잔여 4,907자 (학파 자료 추가 의뢰 필요)

## ADR-017 절차 8회째 적용 결과

| 순 | 영역 | 결과 |
|---|---|---|
| 1 | L2 photo_quality | 9 PASS (ADR-020) |
| 2 | B6 DreamNet v4 | 17 PASS (ADR-021) |
| 3 | face_shape 5형 | 18 PASS (ADR-022) |
| 4 | A8 Freud v2 | 26 PASS (ADR-023) |
| 5 | MBTI compat v2 | 29 PASS (ADR-024) |
| 6 | 한국 화투 48매 | 30 PASS (ADR-025) |
| 7 | 9389자 scourt API | 기존 회귀 자동 통과 (ADR-026) |
| **8** | **KCI 자원오행 94자** | **28 PASS (ADR-027)** |

### 분석/판정 에이전트 vs 오케스트레이터 보충 결과

- 분석 에이전트 (Haiku): 후보 6 + 거부 1 + 빈약속 3 + U1 추출
- 판정 에이전트 (Haiku): ACCEPT 0, DEFER 2(C1·C2·C3), REJECT 4
  → 판정 보수적 (보고서 JSON 실 내용 미확인 + 스키마 변경 우려)
- **오케스트레이터 보충 검증**: 보고서 라인 160-256 실 데이터 확인 +
  본 시스템 list 구조 확인 + 신규 필드 추가 방식으로 회피 가능 →
  **C2 ACCEPT 전환 (조건부)**
  · 신규 필드만 추가 (기존 필드 덮어쓰기 X)
  · 충돌 6건 명시 보존
  · 회귀 테스트 13건 신규

### 분석 에이전트 오추정 패턴 (재발 차단)

분석 에이전트가 "보고서 JSON 미확인"으로 DEFER 보고했으나 실제는
보고서 라인 160-256에 94자 데이터 명시. **판정 에이전트도 DEFER
유지**했으나 메인 오케스트레이터가 직접 Read로 검증 후 ACCEPT
전환.

→ 분석/판정 에이전트 모두 Read 도구 사용 가능했으나 보수적 회피.
향후 분석 프롬프트 보강: "보고서 표제 본문화 가능 영역에 명시된
JSON·표는 반드시 직접 Read 후 후보 보고" 추가 필요.

## 신뢰성 평가

| 항목 | 평가 |
|---|---|
| KCI 학술 출처 | ✅ 검증 통과 |
| ISBN 검증 | ✅ 통과 |
| 94자 JSON 본문 | ✅ 실 데이터 |
| 보고서 표제 5001자 | ❌ 미충족 (1.9%) |
| 참고 URL | ❌ 3개 실패 |
| 충돌 6건 처리 | ✅ 부수 매핑 보존 |
| 본 프로젝트 적합성 | ✅ 옵션 C 신규 필드 채택 |

## 메타

- 영속화: 2026-05-17 (ADR-017 8회째)
- ADR-017 첫 번째 "판정 에이전트 DEFER → 오케스트레이터 보충 ACCEPT" 사례
- 분석/판정 분리 패턴 한계 노출: 보수적 회피 시 메인 보충 필수
- 본 노트 immutable
