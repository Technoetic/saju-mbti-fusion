---
type: reference
status: accepted
date: 2026-05-17
domain: [face]
factuality: koreascience_verified
sources:
  - 한국인 입에 대한 생체계측학적 연구 (KoreaScience JAKO200810103458095)
verified_url:
  - https://koreascience.kr/article/JAKO200810103458095.pdf
verified_date: 2026-05-17
related:
  - decisions/ADR-034-facial-feature-mouth-corner
  - reports/facial-feature-classification-phase1
related_module: engine/divination/facial_feature_classifier.py
---

# 한국인 입 생체계측학 — KoreaScience 학술 출처

## 배경

본 시스템 ADR-034(입꼬리 분류 — 앙월구·복주구·일자구)에서 사용하는
임계값과 한국인 입 평균 통계의 학술 출처.

`engine/divination/facial_feature_classifier.py` `_SOURCE_URL` 영속화 근거.

## 출처

- **제목**: 한국인 입에 대한 생체계측학적 연구
- **KoreaScience URL**: https://koreascience.kr/article/JAKO200810103458095.pdf
- **JAKO ID**: JAKO200810103458095

## 활용 통계 (보고서 §3.4 인용)

| 항목 | 한국인 성인 |
|---|---|
| 입술 높이 | 10mm 이내 |
| 윗입술 vs 아랫입술 두께 | 아랫입술이 윗입술보다 약 1mm 더 두꺼움 |
| 남성 입 너비 평균 | 48mm |
| 여성 입 너비 평균 | 45mm |
| 입 너비 vs 인중 너비 비율 | 약 4.5배 |

## 본 시스템 활용

### ADR-034 본문화

`engine/divination/facial_feature_classifier.py`:
- 입꼬리 KP_61·291 + 입술 중앙 KP_13·14 baseline
- 분류 임계값: 입꼬리 각도 > 0도 (앙월구), < 0도 (복주구), ±2도 잡음 마진
- 출처 URL: 본 reference 노트 인용

### ADR-010 사실성 분리 정합

- ✅ KoreaScience JAKO 라이브 URL 검증 가능 (2026-05-17)
- ✅ 한국인 표본 통계 명시 (표본 크기는 원논문 fetch 필요)
- ✅ 본 시스템은 "입꼬리 각도 측정"으로만 사용 (운명·관운 매핑 X)
- ✅ 사상체질(태음인·소양인) 인용은 본 노트에서도 미본문화

### 한계 명시

- 표본 크기·연도·저자 본문 미발췌 (원논문 fetch 시 보강 가능)
- 입꼬리 각도 자체의 한국인 분포 통계는 본 출처에 부재 — 입 너비·입술 두께
  통계만 인용 가능. 입꼬리 각도 임계값(±2도)은 측정 잡음 휴리스틱
- 표정 변화 영향 (무표정 정면 사진 권장)

## 본 시스템 적용 면책

- 본 데이터는 객관 생체계측학적 분류 베이스라인이며 운명·인과·길흉 무관
- 사용자 출력 시 ADR-006·010 면책 자동 포함:
  - "객관 형태 측정"
  - "운명·관운 매핑이 아님"
  - "사상체질 분류 채택 X"

## 향후

- 원논문 fetch — 표본 크기·연도·저자 보강
- 운영 데이터 누적 후 입꼬리 각도 임계값 보정 (post_traffic, 별도 ADR)
- C1 코·C4 눈·C7 턱 분류 Phase 2 시 추가 KCI/KoreaScience 출처 발굴
