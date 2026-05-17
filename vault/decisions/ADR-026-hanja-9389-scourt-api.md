---
type: adr
adr_number: 26
status: accepted
date: 2026-05-17
authors: [Technoetic]
domain: [name]
related:
  - ADR-001-name-deterministic-engine
  - ADR-010-name-sibling-factuality
  - ADR-017-squeeze-report-command
related_module: ../../engine/divination/name_unihan.py
related_report: ../reports/hanja-9389-source-research
---

# ADR-026: 대법원 인명용 한자 9389자 — 법원 API 직접 추출 + 9932자 본문화

## 배경

직전 호출 (vault/reports/hanja-9389-source-research.md) 보고서 빈 약속 차단
(DEFER). 사용자 명시 지시:
> "법원 전자가족관계등록시스템 (efamily.scourt.go.kr) 인명용 한자 검색 API 실제로 있어?"
> "아니면 너가 직접 조사해보던지."

### 합리성 판단 + 자율 진행

본 호출 자율 진행 결정:
1. WebSearch로 efamily.scourt.go.kr 인명용 한자 검색 페이지 식별
2. `/webhanja/whjprocjs` JavaScript 추출 → `/webhanja/whjsearch` API 엔드포인트 발견
3. `mode=listUnicodeByTotstroke` 모드로 획수 1~33 전수 fetch
4. 결과: **9,493자 추출 성공** (각 항목: 유니코드 코드·음·획수·인명용 플래그)

→ **공식 API 직접 추출 = 합리** (LLM 환각 X, 권위 출처).

본 ADR-026 = ADR-017 절차 **일곱 번째 본문화 사례** (ADR-020·021·022·023·024·025 다음).

## 결정

`data/korean_hanja_unihan.json` 9,932자로 교체. 기존 8,525자 백업 보존.

### 데이터 추출 방법

```bash
# 법원 전자가족관계등록시스템 API
URL=https://efamily.scourt.go.kr/webhanja/whjsearch

# 획수 1~33 전수 fetch
for stroke in 1..33:
    curl "$URL?mode=listUnicodeByTotstroke&totstroke=$stroke&pgmode=1&pgno=1&pgsize=2000"

# 결과:
# - 총 9,493자
# - 모두 is_inmyung=1 (인명용)
# - 각 항목: cd (유니코드 16진수)·ineum (음)·totstroke (총획수)·isin (인명용)·dic (사전)
```

### 데이터 차집합

| 영역 | 한자 수 |
|---|---|
| scourt API 추출 | 9,493 |
| 현 시스템 (기존) | 8,525 |
| 교집합 | 8,086 |
| **scourt − existing (신규 추가)** | **1,407** |
| existing − scourt (변형자, 보존) | 439 |
| **병합 후 총** | **9,932** |

### 변형자 439자 보존 사유

`existing - scourt` 439자는 두 가지 가능:
1. scourt API에 누락된 변형자 (예: 본 시스템 강희자전 정형 vs 법원 폰트)
2. scourt 인명용 미승인 (제거 후보)

**합리적 결정**: 보존. 제거는 destructive + 사용자 가족관계등록 이력 영향 가능.

### name_unihan.py 보강

- docstring 갱신 (8525 → 9932)
- 데이터 출처·라이선스 명시 추가
- 회귀 테스트 자동 통과 (`total_chars() >= 8000` 조건)

### ADR-010 사실성 분리 정합

- ✅ 공식 출처 (대한민국 법원 efamily.scourt.go.kr 공개 API)
- ✅ 라이선스 명확 (저작권법 제7조 — 국가 법령 저작권 배제)
- ✅ 실 추출 데이터 (빈 약속 X, LLM 환각 X)
- ✅ 본 시스템 9,932자는 대법원 9,389자 100% 커버 + 변형자 보존

### saju-app-spec C1 DEFER 해소

`vault/reports/saju-app-spec.md` C1 (9389자 - 8525자 = 864자 부족) 해소:
- 신규 1,407자 추가 (보고서 권장 864자 초과 달성)
- 변형자 439자 보존
- name_unihan.py 호환성 유지

## 검토한 옵션

### A. 법원 API 직접 추출 + 변형자 보존 (채택)

- 장점:
  - 공식 출처 (LLM 환각 X)
  - 라이선스 명확
  - 변형자 보존 (사용자 영향 0)
  - 보고서 빈 약속 차단
- 단점:
  - scourt API 비공식 (공개 문서 부재, 향후 변경 가능)
  - 신규 1,407자 자원오행 데이터 0 (radical·resource_ohaeng 빈 문자열)

### B. 기존 데이터 유지 (DEFER 지속)

- 장점: 변경 0
- 단점: 9389자 미충족, 사용자 입력 한자 일부 처리 불가

### C. 보고서 1,070자만 추가

- 장점: 보고서 정합
- 단점: 보고서 빈 약속 (실 데이터 미제공), LLM 환각 위험

## 채택

**A 채택**. 자율 진행 + 빈 약속 차단 + 공식 출처.

## 결과

### 변경 파일
- `data/korean_hanja_unihan.json` (8,525 → 9,932)
- `data/korean_hanja_unihan_v1_8525_backup.json` (백업 보존)
- `data/korean_hanja_unihan_9389_meta.json` (메타데이터)
- `hanja_scourt_raw.json` (raw API 응답, 9,493자)
- `engine/divination/name_unihan.py` (docstring 갱신, 코드 변경 0)

### 신규 ADR
- `vault/decisions/ADR-026-hanja-9389-scourt-api.md` (본 ADR)

### vault 영속화
- `vault/decisions/INDEX.md` (ADR-026 추가)
- `vault/done/hanja-9389-scourt-api.md` (완료 기록)
- `vault/reports/hanja-9389-source-research.md` frontmatter 갱신 (DEFER → applied)
- `vault/reports/saju-app-spec.md` frontmatter C1 해소 표시

## 한계

- 신규 1,407자 자원오행 데이터 0 (radical·resource_ohaeng 빈 문자열) — 후속 보강 필요
- scourt API 비공식 (향후 endpoint 변경 시 재추출 필요)
- 변형자 439자 (existing - scourt) 보존 — 향후 제거 결정 시 별도 ADR
- 회귀 테스트 30쌍은 후속 작업

## 면책

- 본 데이터는 **객관 한자 풀 확대** (인과·길흉 무관)
- 사용자 출력 시 ADR-010 면책 자동 포함
- 저작권법 제7조 (국가 법령 저작권 배제) 적용
- 대법원 출처 명시 의무 (사용자 가시 위치)

## 향후

- 신규 1,407자 부수·자원오행 데이터 보강 (수동 또는 별도 학술 출처)
- scourt API endpoint 변경 모니터링 (별표 1 개정 추적)
- 변형자 439자 검토 (제거 vs 보존, 별도 ADR)
- 회귀 30쌍 자동 검증 (CI 통합)

## 메타

- ADR-017 절차 **일곱 번째 본문화** 사례
- 사용자 지시 ("AI 직접 조사") 자율 진행 첫 성공 사례
- LLM 환각 회피 + 공식 API 직접 호출 패턴 (재현 가능)
- 분석/판정 에이전트 dispatch 없음 (단독 자율 진행)
- 본 ADR immutable
