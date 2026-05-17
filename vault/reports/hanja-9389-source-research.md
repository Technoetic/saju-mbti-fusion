---
type: external_report
status: applied_via_alternative
date: 2026-05-17
source: deepresearch
domain: name
factuality: mixed_with_empty_promise
applied_to:
  - "9389자 부족 해소 → AI 자율 진행 (사용자 지시) → efamily.scourt.go.kr API 직접 추출 → 9932자 본문화"
  - "data/korean_hanja_unihan.json 9932자 (보고서 1070자 대신 1407자 신규 + 변형자 439자 보존)"
  - "ADR-026 본문화 (법원 API 직접 추출 방법론 영속화)"
  - "saju-app-spec C1 DEFER 해소"
resolution_method: "보고서 빈 약속 차단 후 사용자 명시 'AI 직접 조사' 지시로 efamily.scourt.go.kr API 호출로 우회 해소"
related:
  - decisions/ADR-010-name-sibling-factuality
  - decisions/ADR-017-squeeze-report-command
  - reports/saju-app-spec
  - templates/PROMPT_korean-hanja-9389-source
original_file: ../../대법원 인명용 한자 9389자 확보.md
adr_017_first_application: "2026-05-17 (ADR-017 7회째, DEFER 처리)"
critical_finding: |
  보고서가 1,070자 실 데이터 미제공 — 핵심 15건 샘플만 본문 명시.
  본 시스템 8,525자에 샘플 15건 추가해도 8,540자 (여전히 9,389 미만).
  name_unihan.py _verify_scourt_compliance() expected_count=9389은 미충족.
  → 빈 약속 확정. 코드 변경 시 ValueError로 시스템 기동 불가.
permanently_rejected:
  - "샘플 15건만 추가 (864자 정합성 미충족, 시스템 기동 불가)"
  - "name_unihan.py 9389 검증 활성화 (현재 8525이므로 ValueError, 시스템 망가뜨림)"
  - "회귀 테스트 30쌍 본문 데이터 0 (빈 약속)"
deferred_pending_data:
  - "1,070자 전체 JSON 데이터 (보고서 §5 샘플 15건만, 전수 미제공)"
  - "law.go.kr HWPX 파일 파싱 (바이너리 제약)"
  - "회귀 테스트 30쌍 실 데이터 (보고서 §7 명시 없음)"
already_factually_verified:
  - "9389 - 8525 = 864자 수학 검증 (정확)"
  - "대법원규칙 제3151호 (2024-06-11 시행) law.go.kr 라이브 검증 통과"
  - "저작권법 제7조 (국가 법령 저작권 배제) 인용 (법적 검증 가능)"
  - "engine/divination/name_unihan.py 라인 266-276 _verify_scourt_compliance() 9389 검증 준비됨"
adopted_option: "C — 보고서 부분 채택 + DEFER (1070자 실 데이터 확보 후 재호출)"
user_directive: "2026-05-17 사용자 명시 — 합리적이면 단독 진행, 불합리면 진행 X"
rationale_for_defer: |
  사용자 지시 정신 적용 — 불합리 영역 진행 X.
  본 보고서 채택은 다음 불합리 영역 포함:
  1. 시스템 기동 불가 위험 (expected_count=9389 vs 현재 8525)
  2. 864자 정밀 식별 불가능 (1070자 전체 데이터 부재)
  3. 회귀 테스트 30쌍 빈 약속
  → 본 호출 본문화 진행 = destructive (ADR-010 빈 약속 답습)
---

# 대법원 인명용 한자 9,389자 확보 보고서 — 부분 채택 + DEFER

## 보고서 요약

PROMPT_korean-hanja-9389-source.md 의뢰 응답. 34KB 보고서.
대법원규칙 제3151호 (2024-06-11 시행) 인명용 한자 9,389자 (기존 8,319 + 신규 1,070) 출처
+ 저작권 검증 + 시스템 통합 명세 + 회귀 테스트 30쌍 명세.

## 🟢 팩트 (검증 통과)

| 주장 | 검증 |
|---|---|
| 대법원규칙 제3151호 9,389자 (2024-06-11 시행) | ✅ law.go.kr 라이브 검증 |
| 저작권법 제7조 (국가 법령 저작권 배제) | ✅ 법적 검증 가능 |
| 9,389 - 8,525 = 864자 (수학) | ✅ 정량 직접 검증 |
| 데이터 출처: law.go.kr·scourt.go.kr·법원포털 4종 URL | ✅ URL 접근 가능 |
| 신규 1,070자 핵심 샘플 15건 (㖀·疋·䬈·汩·鬰·屎·婡·乫·㐊·㐡·乯·㐤·㐨·㐲·㑁) | ✅ 보고서 본문 명시 |

## 🟡 구조 (시스템 설계 명제)

- JSON 스키마 명세 (char·reading·meaning·radical·kangxi_strokes·is_scourt_approved·added_in_2024)
- 마이그레이션 절차 (Set Difference 식별)
- _verify_scourt_compliance() 무결성 검증 (이미 준비됨)
- 프론트엔드 면책 문구 가이드 (ADR-010과 통합 가능)

## 🔴 도그마 + 빈 약속 (영구 거부)

**핵심 빈 약속**:
- §5 보고서가 "신규 1,070자 완전 목록"이라 칭하나 본문에는 **샘플 15건만** 명시
- §7 회귀 테스트 30쌍 "구축하였다" 명시하나 본문 데이터 0건
- 864자 정밀 식별 불가능 (8,525 기존자 vs 9,389 대법원 set difference 데이터 부재)

## 본 시스템 반영 (DEFER 처리)

### 분석 에이전트 (Haiku) 결과
후보 6건 (C1~C6) + 거부 2건 (R1·R2) + 사용자 결정 2건 (U1·U2)

### 오케스트레이터 합리성 판단 (사용자 지시 자율 적용)

본 보고서 본문화 = **불합리** 영역 포함:

1. **시스템 기동 불가 위험**:
   - name_unihan.py 라인 266-276 `_verify_scourt_compliance()` expected_count=9389
   - 현재 JSON 8,525자 → 9,389 미만 → ValueError로 시스템 기동 차단
   - 샘플 15건만 추가해도 8,540자 → 여전히 미충족

2. **864자 정밀 식별 불가능**:
   - 보고서가 1,070자 전체 데이터 미제공
   - 기존 8,525 vs 대법원 9,389 차집합(set difference) 계산 불가
   - 어느 864자가 부족한지 식별 불가능

3. **회귀 테스트 빈 약속**:
   - §7 30쌍 "구축하였다" 명시
   - 본문 데이터 0건 (라인 292-298 명세만)

→ **사용자 지시 정신 ("불합리면 진행 X") 적용 → DEFER**.

### 채택 가능 영역 (사용자 1070자 실 데이터 제공 후)

| 후보 | 본문화 조건 |
|---|---|
| C1 864자 병합 | 1,070자 전체 JSON 필요 |
| C2 라이선스 면책 | C1 동반 (저작권 주석 추가) |
| C3 _verify_scourt_compliance 활성화 | C1 완료 후 |
| C4 JSON 스키마 통합 | C1 동반 |
| C5 회귀 테스트 30쌍 | 30쌍 실 데이터 필요 |
| C6 프론트엔드 면책 가이드 | C1 완료 후 (ADR-010 통합) |

## 사용자 명시 데이터 필요 (DEFER 해소 조건)

**1. 1,070자 전체 JSON** (보고서 저자 재의뢰 또는 직접 추출):
- law.go.kr 첨부 HWPX 파일 파싱
- 또는 보고서 §5 샘플 15건 외 1,055건 추가

**2. 회귀 테스트 30쌍 실 데이터**:
- 보고서 §7 명시되었으나 본문 누락
- 보고서 저자 재의뢰 또는 신규 1,070자 중 자체 추출

## 신뢰성 평가

| 항목 | 평가 |
|---|---|
| 대법원규칙 제3151호 출처 | ✅ |
| 저작권법 제7조 인용 | ✅ |
| 9389 수학 검증 | ✅ |
| **1,070자 실 데이터** | ❌ **빈 약속 (샘플 15건만)** |
| **회귀 30쌍 실 데이터** | ❌ **빈 약속 (본문 0)** |
| 시스템 기동 안전성 | ❌ **9389 검증 활성화 시 ValueError** |
| 본 프로젝트 적합성 | ⚠️ **DEFER (실 데이터 제공 후 재호출)** |

## 본 보고서 처리 결과

| 영역 | 상태 |
|---|---|
| 대법원 출처 라이브 검증 | ✅ 4개 URL 접근 통과 |
| 저작권 면책 (퍼블릭 도메인) | ✅ 법적 검증 통과 |
| 8,525 → 9,389 마이그레이션 명세 | ⏸️ DEFER (1070자 실 데이터 필요) |
| 864자 정밀 식별 | ⏸️ DEFER (set difference 데이터 부재) |
| 회귀 30쌍 | ❌ 영구 거부 (빈 약속) |
| 프론트엔드 면책 가이드 | ⏸️ DEFER (C1 후) |
| 반기 자동 모니터링 | ⏸️ 별도 로드맵 |

**본 보고서로부터 본 호출 본문화 0건**. 사용자가 1,070자 실 데이터 확보 후 재호출 시 본문화 가능.

## ADR-017 7회째 누적 결과

| 순 | ADR | 영역 | 결과 |
|---|---|---|---|
| 1 | ADR-020 | L2 photo_quality | 9 PASS |
| 2 | ADR-021 | B6 DreamNet v4 | 17 PASS |
| 3 | ADR-022 | face_shape 5형 | 18 PASS |
| 4 | ADR-023 | A8 Freud v2 | 26 PASS |
| 5 | ADR-024 | MBTI compat v2 | 29 PASS |
| 6 | ADR-025 | 한국 화투 48매 | 30 PASS |
| **7** | **본 호출** | **9389자 + 1070자 빈 약속** | **DEFER** |

분석 에이전트 오추정 0건 (7회 연속) — 보고서 빈 약속 정확 식별.

## 후속 작업 (사용자 결정 후)

1. 사용자가 1,070자 전체 JSON 제공 (또는 보고서 저자 재의뢰)
2. /squeeze-report 재호출 → C1~C6 ACCEPT → ADR-026 본문화 가능

## 메타

- 영속화: 2026-05-17 (ADR-010 사실성 분리 + DEFER)
- ADR-017 7회째 — 빈 약속 차단 첫 사례 (이전 6회는 ACCEPT 본문화)
- 사용자 지시 "불합리면 진행 X" 정신 적용 첫 거부 사례
- 본 노트 immutable
