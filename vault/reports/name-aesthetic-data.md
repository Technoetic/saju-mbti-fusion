---
type: external_report
status: received_partial_application
date: 2026-05-17
source: deepresearch
domain: name
applied_to:
  - §2 인기 이름 통계 → ADR-016 + data/name_aesthetic_syllable_freq.json + engine/divination/name_aesthetic.py
  - §1 음운 결합 규칙 — 부분 적용 (종성 7자음 + 연음 + 자음군 회피 구현, 보고서 JSON 빈 약속이라 비음화·유음화·경음화·ㄴ첨가 별도 PROMPT 경로)
  - §3 회귀 50쌍 — 보고서 빈 약속, 본 시스템 34 tests로 자체 회귀 보강
  - §4 학술 인용 — 가짜 인용 폐기 + 실제 출처 영속화 (vault/references/korean-phonetic-research.md)
neo4j_synced: false
factuality: mixed
related:
  - decisions/ADR-010-name-sibling-factuality
  - decisions/ADR-016-name-aesthetic-partial
  - done/name-aesthetic-partial.md
  - references/korean-phonetic-research.md
  - templates/PROMPT_korean-phonetic-rules.md
original_file: ../../한국어 작명 SaaS 어감·발음 선호도 데이터 분석 보고서.md
verified_against:
  - https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003283283 (가짜 인용 확인 → 실제는 조성문 2025)
  - https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART001432925 (가짜 인용 확인 → 실제는 신지영 2010)
  - https://baby-name.kr/ (인기 이름 출처 확인)
adr_017_first_application: "2026-05-17 (분석/판정 분리 절차 첫 적용)"
permanently_rejected:
  - "§1 음운 결합 JSON 규칙표 — 빈 약속 (보고서 본문 데이터 0)"
  - "§3 회귀 테스트 50쌍 — 빈 약속 (보고서 본문 데이터 0)"
  - "김진욱·류선영(2017) 인용 — KCI 검증 실패 (실제 URL은 조성문 2025)"
  - "정희원(2009) 인용 — KCI 검증 실패 (실제 URL은 신지영 2010)"
already_implemented:
  - "§2 인기 이름 통계 (남 17/여 17 음절 빈도) → data/name_aesthetic_syllable_freq.json"
  - "§2 위치별 가중치 (start/end) → name_aesthetic.py position_match_score (line 194-245)"
  - "§1 종성 7자음 + 연음 + 자음군 회피 → name_aesthetic.py (line 269-411)"
  - "§4 실제 학술 출처 → vault/references/korean-phonetic-research.md (조성문 2025 + 신지영 2010 KCI 검증)"
deferred_pending_research:
  - "§1 음운 확장 (비음화 §18-19·유음화 §20·격음화 §12·경음화 §23-28·ㄴ첨가 §29-30·자음군 단순화 §10-11) → PROMPT_korean-phonetic-rules.md 별도 딥리서치 영역 (보고서 §1 본문 빈 약속이라 학술 출처 직접 의뢰 필요)"
analyst_misclassifications_in_this_call:
  - "C3: vault/references/korean-phonetic-research.md 미존재 추정 (실제 영속화 완료, KCI 검증 통과 인용)"

# 한국어 작명 SaaS 어감·발음 선호도 데이터 분석 — 사실성 검증 및 부분 본문화

## 본 보고서의 등급

ADR-010 사실성 분리 검증 결과 **혼합 등급** (saju-option-B-school과 다름):

| 영역 | 등급 |
|---|---|
| 인기 이름 통계 (전자가족관계) | 🟢 사실 |
| 국립국어원 음운 법칙 (자음 7개·연음·비음화·유음화·자음군 회피) | 🟢 사실 |
| §1 음운 결합 JSON 규칙표 | 🔴 빈 약속 |
| §3 회귀 테스트 50쌍 | 🔴 빈 약속 |
| 김진욱·류선영 (2017) 인용 | 🔴 **가짜 인용** (실제: 조성문 2025) |
| 정희원 (2009) 인용 | 🔴 **가짜 인용** (실제: 신지영 2010) |

## 🟢 팩트 (검증 완료)

### 인기 이름 통계
- 출처: 전자가족관계등록시스템 공식
- baby-name.kr WebFetch로 사실 확인 (2026-05-17)
- 2015-2024 70건 (10년 × 7위) 추출 가능
- 가중치 산출 → 음절 빈도 데이터

### 국립국어원 음운 법칙
- 음절 종성 7개 자음 (ㄱㄴㄷㄹㅁㅂㅇ)
- 연음·비음화·유음화 자음동화
- 자음군 회피·된소리되기 (표준발음법 §29)

## 🔴 도그마/오류 (가짜 인용 2건)

### 1. 김진욱·류선영 (2017) "한국인 이름 음운 빈도"

**KCI 라이브 fetch 결과**:
- 동일 URL의 실제 논문: **조성문 (2025)** "한국인 이름의 음운적 특성에 대한 연구"
- 저자·연도 모두 다름
- 92건 분석 주장 자체는 실제 논문 내용과 일치

→ 보고서가 실제 KCI 논문을 발견했으나 저자·연도를 잘못 인용.

### 2. 정희원 (2009) "한국어 사전 표제어 음절 빈도"

**KCI 라이브 fetch 결과**:
- 실제: **신지영 (2010)** Communication Sciences and Disorders
- 47,401 표제어 분석은 사실 (신지영 논문)
- 저자·연도·학회지 모두 다름

→ 동일 패턴. 보고서가 인용을 정확히 못함.

## 🔴 빈 약속 2건

### §1 음운 결합 JSON 규칙표
"다음은 음운 결합 자연스러움에 대한 규칙을 JSON 형식으로 정리한 표이다." → 본문에 JSON 없음.

### §3 회귀 테스트 50쌍
"회귀 테스트 데이터 50쌍은 다음과 같다." → 본문에 데이터 없음.

## 본 시스템 반영 (부분 채택)

### ✅ 채택 (§2 인기 이름만)

[ADR-016](../decisions/ADR-016-name-aesthetic-partial.md) 본문화:
- data/name_aesthetic_syllable_freq.json (남 17 / 여 17 음절)
- engine/divination/name_aesthetic.py
- 14 회귀 PASS

### ❌ 미채택

- §1 음운 결합 규칙 — 데이터 미완
- §3 회귀 50쌍 — 데이터 미완
- §4 학술 인용 (김진욱·정희원) — KCI 검증 실패
- §1·§3 영역은 본 모듈 재시도 시 별도 보고서 또는 직접 수집 필요

## ADR-010 정교한 적용

본 작업은 본 프로젝트의 가장 정교한 ADR-010 적용 사례:
- KCI 라이브 fetch로 가짜 인용 직접 검증
- 부분 채택 (보고서 통째로 거부 X)
- 빈 약속 거부 (없는 데이터 채우지 않음)

## 신뢰성 평가

| 항목 | 평가 |
|---|---|
| 인기 이름 통계 | ✅ 검증 통과 |
| 음운 법칙 출처 | ✅ 국립국어원 공식 |
| 학술 인용 | 🔴 가짜 2건 |
| 빈 약속 | 🔴 2건 |
| 본 프로젝트 적합성 | 🟡 부분 (§2만) |

## 다음 액션

- [x] ADR-016 작성 (부분 채택)
- [x] data + engine + tests 본문화 (14 PASS)
- [x] vault/references는 가짜 인용이라 미작성 (정확한 출처 미확보)
- [ ] (선택) 음운 결합 규칙 별도 보고서 — 국립국어원 직접 수집
- [ ] (보류) §3 회귀 50쌍 — 본 모듈 회귀로 대체됨

## 출처

- 본 보고서 원본: `사주/한국어 작명 SaaS 어감·발음 선호도 데이터 분석 보고서.md`
- 검증 (2026-05-17 라이브 fetch):
  - https://baby-name.kr/ (인기 이름 출처 확인)
  - https://www.kci.go.kr/... ART003283283 (가짜 인용 확인)
  - https://www.kci.go.kr/... ART001432925 (가짜 인용 확인)

## 2026-05-17 ADR-017 절차 첫 적용 결과

본 보고서는 1차 처리(2026-05-17)가 ADR-017 분석/판정 분리 패턴 도입 전이라
재호출로 절차 정합화 + 결손 영역 명확화. 분석/판정 에이전트 Haiku 2회 dispatch.

### 분석 결과
- 후보 3건 (C1·C2·C3) + 영구 거부 3건 (R1·R2·R3) + 사용자 결정 2건 (U1·U2)

### 판정 결과
- **ACCEPT 0건** (모두 이미 처리 완료)
- **REJECT 3건**:
  - C1 음운 확장 → PROMPT_korean-phonetic-rules.md 이미 영속화
  - C2 위치별 패턴 → name_aesthetic.py 이미 구현 + 34 tests PASS
  - C3 조성문·신지영 영속화 → vault/references/korean-phonetic-research.md 이미 영속화

### 오케스트레이터 핵심 발견

분석 에이전트가 C3 "vault/references/korean-phonetic-research.md 미존재"로 추정했으나,
오케스트레이터 실 파일 확인 결과 **이미 영속화 완료** + KCI URL 라이브 검증 통과:
- 조성문(2025) "한국인 이름의 음운적 특성" (대법원 2008-2025 92개 음절)
- 신지영(2010) "한국어 사전 표제어 음소·음절 빈도" (47,401 표제어)

### 결론

본 호출도 코드 변경 0. 비용 (Haiku 2회 ≈ $0.02)으로:
- ADR-017 절차 첫 적용
- frontmatter `permanently_rejected` 4건 + `already_implemented` 4건 + `deferred_pending_research` 1건 영속화
- 본 보고서는 ADR-010 가장 정교한 적용 사례로 완결 상태 재확인

### 분석 에이전트 오류 패턴

- C3: vault/references/ 실 파일 미확인 오추정
→ ADR-017 프롬프트 보강 가치: "vault/references/ 파일 존재 여부 직접 확인 의무" (squeeze-report 절차 단계 0에 명시 추가 검토)

## 메타

- 영속화: 2026-05-17 (사실성 분리 부분 적용)
- ADR-017 첫 적용: 2026-05-17 (코드 변경 0, 절차 정합화 + 결손 영역 명확화)
- ADR-010 사례 — 가장 정교한 적용
- 본 노트 immutable
