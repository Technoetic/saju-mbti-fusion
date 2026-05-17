---
type: external_report
status: received_partial_application
date: 2026-05-17
source: deepresearch
domain: name
applied_to:
  - §2 인기 이름 통계 → ADR-016 + data/name_aesthetic_syllable_freq.json + engine/divination/name_aesthetic.py
  - §1 음운 결합 규칙 — 미적용 (보고서 빈 약속)
  - §3 회귀 50쌍 — 미적용 (보고서 빈 약속)
  - §4 학술 인용 — 미인용 (KCI 검증 실패, 가짜 인용 2건)
neo4j_synced: false
factuality: mixed
related:
  - decisions/ADR-010-name-sibling-factuality
  - decisions/ADR-016-name-aesthetic-partial
  - done/name-aesthetic-partial.md
original_file: ../../한국어 작명 SaaS 어감·발음 선호도 데이터 분석 보고서.md
verified_against:
  - https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003283283 (가짜 인용 확인)
  - https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART001432925 (가짜 인용 확인)
  - https://baby-name.kr/ (인기 이름 출처 확인)
---

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

## 메타

- 영속화: 2026-05-17 (사실성 분리 부분 적용)
- ADR-010 사례 — 가장 정교한 적용
- 본 노트 immutable
