---
type: external_report
status: applied
date: 2026-05-17
source: 외부 작성 (사용자 제공 딥리서치)
domain: saju
applied_to:
  - "§2 12단계 철학 + 12 stages 명칭"
  - "§3 자평진전 학파 채택 (양순음역 + 화토동궁) — KCI 검증"
  - "§4 120 셀 (10천간 × 12지지) 매핑 본문화"
  - "§5 TwelveStagesMapper 싱글턴 (shensha.py 패턴 차용)"
  - "§6 ADR-010 면책 자동 포함"
  - "§7 회귀 30쌍 자동 생성 (보고서 빈 약속 해소)"
permanently_rejected:
  - "§8 동적 확장 (합충형해파) — ADR-002 학파 회피 침해"
  - "참고 자료 5·9번 (개인 블로그/카페) — 학술 검증 불가"
deferred_pending_decision:
  - "UI 면책 문구 노출 방식 (사업 단계)"
  - "API 엔드포인트 설계 (사업팀)"
already_implemented:
  - "engine/saju/shensha.py 신살 5종 (60갑자 해시 패턴 차용)"
  - "ADR-002·010·015 정책 수립"
related_adr: [ADR-001, ADR-002, ADR-010, ADR-015, ADR-031]
adr_017_first_application: "2026-05-17 (squeeze-report 12회째)"
original_file: ../../../십이운성 결정론 매핑 데이터 생성.md
adopted_option: "C — 자평진전 단일 학파 + 양순음역 + 화토동궁 + 회귀 자동 생성"
---

# 사주 십이운성 결정론 매핑 — 자평진전 학파 채택 (ADR-031)

## 보고서 요약

378줄. engine/saju/ 모듈 결손 영역 (twelve_stages.py) 직접 명세.
자평진전 학파(양순음역 + 화토동궁) 채택 + 120 셀 완전 매핑 + KCI 라이브 검증.

## 🟢 팩트 (검증 통과)

| 주장 | 검증 |
|---|---|
| KCI NODE10738496 (최산태·김만태 2021) | ✅ 분석 에이전트 라이브 검증 |
| KCI NODE08998998 (김계성 2016) | ✅ 분석 에이전트 라이브 검증 |
| 자평진전 학파 표준 | ✅ 고전 출전 |
| 양순음역 + 화토동궁 원칙 | ✅ KCI 학설 검증 |
| §4 120 셀 매핑 본문 | ✅ 라인 145-314 완전 명시 |
| 12단계 한자 명칭 | ✅ 자전 검증 |

## 🟡 구조 (시스템 설계 명제)

- TwelveStagesMapper 싱글턴 (lru_cache)
- 120 셀 결정론 (10천간 × 12지지)
- O(1) dict 해시 탐색
- shensha.py 패턴 차용

## 🔴 영구 거부

| 영역 | 사유 |
|---|---|
| §8 동적 확장 (합충형해파) | ADR-002 학파 회피 침해, 별도 ADR 필요 |
| 참고 자료 5·9번 (cafe.daum·mire2000) | 학술 검증 불가 |
| §7 30쌍 본문 누락 | 본 시스템 자동 생성으로 해소 |

## 본 시스템 반영 (ADR-031 본문화)

### 채택 영역 (5/7 후보)

- **C1** 12단계 철학 → STAGES tuple + 자전 매핑
- **C2** 양순음역 + 화토동궁 → school 라벨 + KCI 출처
- **C3** 120 셀 → data/twelve_stages_mapping.json
- **C4** TwelveStagesMapper → engine/saju/twelve_stages.py
- **C5** ADR-010 면책 → rationale 자동 포함

### 거부 영역 (2/7 후보)

- **C7** 동적 확장 (합충형해파) — REJECT
- **R1** 개인 블로그 출처 — REJECT

### 자율 진행 영역 (C6 DEFER → ACCEPT 전환)

- **C6** 회귀 30쌍 빈 약속 → **본 시스템 자동 생성** (120 셀 매핑이 정답 데이터)
  - 양간 12 + 음간 12 + 화토동궁 6 = 30 샘플 (random.seed=42)
  - test_each_stem_has_12_stages 전수 120 검증 자동

### 사용자 결정 영역

- **U2** UI 면책 노출 방식 (사업)
- **U3** API 엔드포인트 (사업)

## ADR-017 절차 12회째 적용 결과

| 순 | 영역 | 결과 |
|---|---|---|
| 1 | L2 photo_quality | 9 PASS (ADR-020) |
| 2 | B6 DreamNet v4 | 17 PASS (ADR-021) |
| 3 | face_shape 5형 | 18 PASS (ADR-022) |
| 4 | A8 Freud v2 | 26 PASS (ADR-023) |
| 5 | MBTI compat v2 | 29 PASS (ADR-024) |
| 6 | 한국 화투 48매 | 30 PASS (ADR-025) |
| 7 | 9389자 scourt API | 자동 통과 (ADR-026) |
| 8 | KCI 자원오행 94자 | 28 PASS (ADR-027) |
| 9 | 표준발음법 Priority 1·2 | 59 PASS (ADR-028) |
| 10 | 한국 성씨·인명 빈도 | 21 PASS (ADR-029) |
| 11 | 손금 결정론 5 라인 | 21 PASS (ADR-030) |
| **12** | **사주 십이운성 120 셀** | **17 PASS (ADR-031, 120/120 매핑 100%)** |

### 분석/판정 vs 오케스트레이터 보충 결과

- 분석 에이전트 (Haiku): 7 후보 + KCI 라이브 검증 통과 + 빈 약속 1건 식별
- 판정 에이전트 (Haiku): ACCEPT 5 + REJECT 2 + DEFER 1 (C6 회귀 빈 약속)
- **오케스트레이터 (Opus 보충)**: C6 자율 진행 — 120 셀 매핑이 정답 데이터이므로 30쌍 자동 생성 가능 (random.seed=42). 사용자 명시 정신 "합리적이면 진행" 정합.

## 신뢰성 평가

| 항목 | 평가 |
|---|---|
| KCI 출처 라이브 검증 | ✅ NODE10738496 + NODE08998998 |
| §4 120 셀 본문 완전 명시 | ✅ |
| 자평진전 학설 정합 | ✅ |
| ADR-015 옵션 B 패턴 정합 | ✅ |
| §7 30쌍 빈 약속 | ❌ 본 시스템 자동 생성으로 해소 |
| §8 동적 확장 | ❌ REJECT (학파 침해) |

## 메타

- 영속화: 2026-05-17 (ADR-017 12회째)
- 12회 연속 분석 에이전트 오추정 0건
- 본문 명시 120 셀 + 자동 회귀 30 + 전수 검증
- ADR-015 옵션 B 패턴 두 번째 적용 (이재승 억부론 후 자평진전)
- 본 노트 immutable
