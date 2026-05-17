---
type: reference
status: accepted
date: 2026-05-17
domain: name
factuality: kci_verified
sources:
  - 조성문 (2025). 한국인 이름의 음운적 특성에 대한 연구.
  - 신지영 (2010). 한국어 사전 표제어 발음의 음소 및 음절 빈도.
verified_url:
  - https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003283283
  - https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART001432925
verified_date: 2026-05-17 (WebFetch 라이브 검증)
related:
  - decisions/ADR-010-name-sibling-factuality
  - decisions/ADR-016-name-aesthetic-partial
  - reports/name-aesthetic-data
---

# 한국어 음운·이름 음운론 KCI 논문 — 검증된 출처

## 배경

ADR-016 적용 시 [[../reports/name-aesthetic-data]] (어감 보고서) 학술 인용
가짜 발견:
- 보고서 명시: 김진욱·류선영(2017) / 정희원(2009)
- KCI 라이브 fetch 결과: 둘 다 존재하지 않음

본 노트는 보고서가 인용하려던 **진짜 출처**를 영속화. 향후 음운 결합
규칙 보강이나 학술 인용 필요 시 참조용.

## 1. 조성문 (2025) — 한국인 이름 음운적 특성

- **저자**: 조성문 (Sungmoon Cho)
- **소속**: 한양대학교
- **학회지**: 국제언어문학 (International Language and Literature) Vol.62
- **페이지**: 219-233
- **발간**: 2025
- **KCI**: ART003283283 (라이브 검증 통과)

### 핵심 기여
- 대법원 통계 2008-2025 상위 출생신고 이름 92개 음절 구조 분석
- 초성·중성·종성 단위 빈도 산출
- **결과**: 음절 '진'이 가장 대표적, 초성 ㅈ / 중성 ㅣ / 종성 ㄴ 최다

### 본 시스템 활용 가능성
- 본 시스템 [data/name_aesthetic_syllable_freq.json](../../data/name_aesthetic_syllable_freq.json)
  은 70건(10년 × 7위) 가중 빈도
- 본 논문은 92개 출생신고 데이터 — 본 시스템과 다른 표본
- 향후 본 시스템 데이터 확장 시 비교 검증 자료로 활용 가능

## 2. 신지영 (2010) — 한국어 사전 표제어 음소·음절 빈도

- **저자**: 신지영 (Shin Jiyoung)
- **학회지**: Communication Sciences and Disorders Vol.15, No.1
- **페이지**: 94-106
- **발간**: 2010
- **KCI**: ART001432925 (라이브 검증 통과)

### 핵심 기여
- 47,401개 사전 표제어 분석
- 한국어 음소·음절 빈도 통계 산출
- 음운론 표준 통계 자료

### 본 시스템 활용 가능성
- 사전 표제어 ≠ 이름 (도메인 다름)
- 한국어 일반 음운 통계로 가중 보정 시 활용 가능
- 본 시스템 음절 빈도와 일반 한국어 빈도 비교 시 "이름 특화 음절" 식별 가능

## ADR-016 적용 정신

본 references 노트는 보고서가 **잘못 인용**한 학술 출처를 진짜 출처로
교체. ADR-010 사실성 분리의 부분 사례 — 가짜 인용은 폐기, 진짜 출처는
영속화.

본 두 논문은 현 시점 **활용 안 함** (코드 변경 0). 향후 음운 보강 시
재참조 가능.

## 면책

- 본 노트는 학술 사실 영속화만 — 시스템 적용은 별도 ADR 필요
- 본 두 논문 인용 시 ADR-010 사실성 분리 원칙 준수 (단정·과장 금지)
