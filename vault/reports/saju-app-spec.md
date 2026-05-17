---
type: external_report
status: applied
date: 2026-05-15
source: 외부 작성 (사용자 제공)
domain: name
applied_to: [§1, §2, §3 옵션 A, §4, §5-A, §5-B]
rejected: [§6 리걸테크]
boring: [§3 옵션 B (학파 채택)]
related_done: [done/name-phase1-bulyong-strokes-scoring, done/name-phase2-saju-unihan]
related_adr: [decisions/ADR-001, ADR-002, ADR-003, ADR-006, ADR-010, ADR-015, ADR-016]
file: "../../../작명 및 개명 특화 애플리케이션 개발을 위한 성명학 도메인 지식 및 시스템 설계 심층 분석 보고서.md"
permanently_rejected:
  - "§6 법원 신청서 자동 생성 — ADR-006 변호사법·책임 소재 영구 거부"
  - "§6 1개월 CRM 알림 — ADR-006 규제 준수 강제 범위 외 영구 거부"
  - "§2 月(고기육변) 6획 처리 — 의도된 설계 제약 (결정론 우선, 의미 구분 불가)"
already_implemented:
  - "§1 불용한자 진단 80자/13 카테고리 → engine/divination/name_bulyong.py"
  - "§2 강희자전 원획수 + 변형부수 7종 → engine/divination/name_strokes.py (月 의도적 제외)"
  - "§2 81수원도 4격 길수 필터링 → name_scoring.py + name_gaemyeong.py 라인 100-103 + name_gaeja.py 라인 107-109"
  - "§2 2자 성명·복성 가상 수 1 → name_scoring.py 라인 146-156 (외자/복성 명시 처리)"
  - "§3 만세력 + 자원오행 + 음양 + 발음오행 (해례본 다수설) → engine/divination/name_baleum.py + name_eumyang.py + name_saju_ohaeng.py"
  - "§4 두음법칙 + 역매핑 → engine/divination/name_dueum.py (35+6 음절, '유'→['유','류'] 지원)"
  - "§4 인명용 한자 풀 8525자 (90.8%) → data/korean_hanja_unihan.json"
  - "§5-A 개명 트랙 발음오행 상생 대량 생성 → engine/divination/name_gaemyeong.py (require_baleum_sangsaeng=True, max_combinations=50000)"
  - "§5-B 개자 트랙 3-step Constraint Satisfaction (자원오행 제약3 포함) → engine/divination/name_gaeja.py (target_ohaeng 파라미터)"
deferred_pending_source:
  - "§4 9389자 - 8525자 = 864자 추가 (2026-05-17 라이브 검증 실패, 출처 확보 후 재호출)"
adr_017_first_application: "2026-05-17 (본 보고서 ADR-017 분석/판정 분리 절차 첫 적용)"

# 작명·개명 특화 앱을 위한 성명학 도메인 지식·시스템 설계 보고서

## 원본 위치

프로젝트 루트의 `작명 및 개명 특화 애플리케이션 개발을 위한 성명학 도메인 지식 및 시스템 설계 심층 분석 보고서.md` (29KB, 167줄).

## 핵심 요약

작명·개명 앱을 "제약 조건 만족 알고리즘 엔진"으로 구현하기 위한 8장 보고서.
한국 정통 성명학 도메인 지식 + 대법원 행정 + 시스템 설계.

## 적용 상태 (2026-05-17 기준)

### ✅ 적용 완료
- §1 불용한자 진단 (80자/13 카테고리)
- §2 강희자전 원획수 + 변형 부수 8종 + 81수원도 + 4격
- §3 만세력 활용 + 자원오행 매칭 + 음양 + 발음오행
- §4 두음법칙 + 인명용 한자 풀 8525자 (90.8%)
- §5-A 개명 트랙
- §5-B 개자 트랙

→ 자세히: [[../done/name-phase1-bulyong-strokes-scoring]] / [[../done/name-phase2-saju-unihan]]

### 🟡 보류
- §3 용신 학파별 도출 → [[../decisions/ADR-002-saju-option-A]] (단순 분포 채택)
- §4 9389자 - 8525자 = 864자 부족
- §1 가족 서열 → 완료 (별도 딥리서치 보고서 + ADR-010 사실성 분리 적용) → [[../done/name-phase3-sibling-preference]]

### ⛔ 거부
- §6 법원 신청서 자동 생성 → [[../decisions/ADR-006-legaltech-rejected]]
- §6 1개월 CRM 알림 → 동 ADR

## 다음 액션

[[../roadmap/INDEX]] 참조.

## 2026-05-17 ADR-017 절차 첫 적용 결과

본 보고서는 1차 처리(2026-05-15)가 ADR-017 분석/판정 분리 패턴 도입 전이라
**ADR-017 절차 첫 적용 재호출** 수행. 분석/판정 에이전트 (Haiku) 2회 dispatch.

### 분석 결과
- 후보 추출 7건 (C1~C7) + 거부 2건 (R1·R2 §6) + 사용자 결정 3건 (U1~U3)
- 분석 에이전트가 "확인 필요"로 분류한 C3~C7은 실제로 모두 이미 구현됨

### 오케스트레이터 본 시스템 직접 점검 (메인 컨텍스트)

| 후보 | 보고서 | 본 시스템 실 구현 | 결정 |
|---|---|---|---|
| C1 | §4 9389자 | 8525자 (864자 미수록) | **DEFER** (출처 라이브 검증 실패) |
| C2 | §2 月 6획 | name_strokes.py 4획 통일 (의도적 제외) | **REJECT permanently** |
| C3 | §2 2자/복성 가상 1 | name_scoring.py 라인 146-156 | 이미 구현 |
| C4 | §4 두음 역매핑 | name_dueum.py docstring 라인 8 명시 | 이미 구현 |
| C5 | §5-A 발음오행 상생 | name_gaemyeong.py require_baleum_sangsaeng=True | 이미 구현 |
| C6 | §2 81수리 길수 | name_gaemyeong.py 라인 100-103 + name_gaeja.py 라인 107-109 | 이미 구현 |
| C7 | §5-B 자원오행 제약3 | name_gaeja.py target_ohaeng 파라미터 | 이미 구현 |
| R1·R2 | §6 법원/CRM | - | **영구 거부** (ADR-006) |

### 판정 결과
- **ACCEPT 0건** (모든 코드 결손 영역 이미 구현 또는 의도된 제약)
- **REJECT 10건**: C2~C7, R1·R2, U1·U3
- **DEFER 2건**: C1 + U2 (864자 추가, 출처 확보 후)

### 외부 검증 시도 (WebFetch)

대법원 인명용 한자 2024년 5월 9389자 라이브 검증:
- scourt.go.kr 공식 발표 페이지 직접 접근 실패
- Google 검색 차단으로 우회 출처 확인 불가
- 본 보고서 본문 라인 81-85 외 1차 출처 미확인
→ **C1 DEFER 정직 판정**

### 결론

본 호출도 코드 변경 0. 비용 (Haiku 2회 ≈ $0.02)으로 ADR-017 절차 정합화 +
permanently_rejected/already_implemented/deferred_pending_source 영속화로
향후 재호출 시 효율 ↑.

분석 에이전트 피드백: 보고서 텍스트만 읽고 실 코드 미확인으로 인한 오분류
다수 발견 — 향후 분석 에이전트 프롬프트에 "engine/divination/*.py 실 코드
교차 검증 의무" 추가 필요.
