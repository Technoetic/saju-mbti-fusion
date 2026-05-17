---
type: prompt_template
target: deepresearch
purpose: 부위별 형상 분류 Phase 2 — 코·눈·턱 원논문 μ·σ·N 추출 의뢰 (Phase 1 DEFER 4건 잠금 해제)
created: 2026-05-17
related_module: engine/divination/facial_feature_classifier.py (확장)
related_adr:
  - ADR-034 (Phase 1 — 입꼬리 단독 완료)
  - ADR-022 (face_shape 5형 — 부위 단위 확장)
  - ADR-010 (사실성 분리)
  - ADR-006 (자문 거절)
priority: high
status: draft
related_report: ../reports/facial-feature-classification-phase1
deepresearch_input: PROMPT_facial-feature-classification-phase2.deepresearch.txt
post_traffic: false
---

# 부위별 형상 분류 Phase 2 — 원논문 μ·σ 추출 의뢰

## 사용법

Phase 1(ADR-034)으로 입꼬리 분류(앙월구·복주구·일자구) 본문화 완료.
보고서 7개 후보 중 C5 단독만 구체 임계값 명시되어 즉시 채택됐고
C1·C2·C4·C7 4건은 임계값 구체 μ·σ 부재로 DEFER.

본 PROMPT는 Phase 2 잠금 해제:
- C1 코 — 송우철 2017 (한국 안면 형태) 본문에서 콧방울 너비 평균·SD·표본 추출
- C2 코 — PMC11431719 (한국 비강 cone-beam CT 2024) 매부리·들창 비율 추출
- C4 눈 — 최윤경·이경희 2009 (한국 여성 안면) 흰자위 노출 분포 추출
- C7 턱 — 노상훈 1998 (한국인 하악각) 사각턱 임계값 추출

페어 입력본은 `PROMPT_facial-feature-classification-phase2.deepresearch.txt` 참조.

## 결손 영역 표

| 후보 | 분류 | KCI 출처 (이미 검증) | 결손 (Phase 2 채울 영역) |
|---|---|---|---|
| C1 | 복코·매부리코·들창코 (콧방울 너비) | 송우철 2017 NODE07133895 | 콧방울 너비 비율 μ·σ·N |
| C2 | 매부리코·들창코 형태 (비강 비율) | PMC11431719 (2024 신규) | bridge_curvature·nose_length 임계값 |
| C4 | 삼백안 (흰자위 노출 비율) | 최윤경·이경희 2009 NODE09916734 | 홍채 위/아래 흰자 노출 % 분포 |
| C7 | 사각턱·이중턱 (하악각·턱 살집) | 노상훈 1998 (JKAOMS) | jaw_squareness 각도 분포 + 사각턱 임계 |

## 본 시스템 채택 절차

1. 딥리서치 결과를 `vault/reports/facial-feature-classification-phase2.md` 저장
2. `/squeeze-report` 호출 — ADR-010 사실성 분리 3등급
3. Phase B Haiku 검증 — μ·σ·N 구체 숫자 명시 여부 + 가짜 통계 차단
4. ACCEPT 항목만 `engine/divination/facial_feature_classifier.py` 확장:
   - `classify_nose_shape(landmarks) -> NoseShapeResult` 신규
   - `classify_eye_shape(landmarks) -> EyeShapeResult` 신규 (삼백안 단독 시작)
   - `classify_jaw_shape(landmarks) -> JawShapeResult` 신규 (사각턱 단독 시작)
5. 회귀 N건 + ADR-034 supplement 또는 ADR-035 본문화

## 사상체질 인용 차단 의무

직전 Phase 1 보고서가 사상체질(태음인·소양인) 비교를 반복 인용했다.
Phase 2 의뢰는 다음 강제:
- 사상체질 비교 통계는 본 PROMPT 채택 범위 외 (ADR-006 자문 거절)
- "한국 성인 전체 평균값" 또는 "성별 분리 평균"만 사용
- 사상체질 기반 임계값이 보고서에 포함돼도 본문화 X (squeeze-report에서 거부)

## 면책

- ADR-010 사실성 분리 — μ·σ·N 구체 숫자 부재 시 ACCEPT 불가
- ADR-006 자문 거절 — 운명·관운·재물복 매핑 금지, 분류 라벨 한정
- ADR-022 정합 — 5형 윤곽과 부위 단위 분류는 직교
- ADR-034 정합 — 본 모듈은 입꼬리 분류와 같은 facial_feature_classifier.py 확장
