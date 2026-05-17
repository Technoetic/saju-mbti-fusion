---
type: adr
adr_number: 22
status: accepted
date: 2026-05-17
authors: [Technoetic]
domain: [face]
related:
  - ADR-002-saju-option-A
  - ADR-006-legaltech-rejected
  - ADR-010-name-sibling-factuality
  - ADR-017-squeeze-report-command
  - ADR-018-face-golden-set-policy
related_module: ../../engine/divination/face_shape.py
related_report: ../reports/face-shape-classifier-research
related_reference: ../references/korean-face-anthropometry
related_prompt: ../templates/PROMPT_face-shape-classifier
---

# ADR-022: 5형 결정론 안면 형태 분류 — 목·화·토·금·수 + 복합형

## 배경

`engine/divination/face_scoring.py` (532줄, MediaPipe 478 키포인트 12궁 점수)는
이미 결정론 엔진이나, **5형(五行) 형태 분류는 결손**. ADR-018
(face-golden-set-policy) 라인 35-36에서 "5형 분류 설계 ACCEPT, 구현 DEFER"
명시.

PROMPT_face-shape-classifier.md 딥리서치 의뢰 → 보고서 수령 →
/squeeze-report 절차:
- 분석 에이전트 (Haiku): 후보 1건 (C1)
- 판정 에이전트 (Haiku): ACCEPT 1건
- 오케스트레이터 (Opus): 본문화

본 ADR-022는 ADR-018 DEFER **해소** + ADR-017 절차 세 번째 본문화 사례
(ADR-020 L2 + ADR-021 B6 다음).

## 결정

`engine/divination/face_shape.py` 신규 모듈 본문화.

### 5형 매핑 (보고서 §3 YAML)

| 한글 오행 | 영문 (face_scoring.py 호환) | 형태명 | 임계값 |
|---|---|---|---|
| 목형 | long | 수직발달형 (긴 얼굴) | fwhr<0.82 + 115≤jaw≤130 |
| 화형 | inverted_tri | 상광하협형 (역삼각) | bz/bg>1.25 + jaw>125 |
| 토형 | oval | 수평발달형 (넓고 두꺼운) | fwhr≥0.88 + jaw≥115 |
| 금형 | square | 하악발달형 (각진) | fwhr≥0.85 + jaw<112 + bz/bg≤1.15 |
| 수형 | round | 곡선발달형 (둥근) | 0.83≤fwhr≤0.88 + jaw>120 + bz/bg≤1.20 |
| 복합형 | oval (fallback) | 표준형 (균형) | 임계값 교집합 외 |

### 메트릭 (보고서 §2.2)

- `face_width_height_ratio` (FWHR): Bizygomatic width / Trichion-Gnathion
- `jaw_angle_deg`: Go_L · Gnathion · Go_R 벡터 내적 각도
- `bizygomatic_to_bigonial_ratio`: 광대 / 하악 너비

### MediaPipe 478 키포인트 (보고서 §2.1)

- 10 (Trichion 머리털점)
- 9 (Glabella 미간)
- 152 (Gnathion 턱끝)
- 234·454 (좌·우 Zygion 광대)
- 58·288 (좌·우 Gonion 하악각)
- 13 (Stomion 입정중점)

face_scoring.py에 이미 사용 중 → 정합.

### 학파 회피 (ADR-002 정합)

- 보고서 §0·§3 명시: "길흉화복 내포 금지"
- 마의상법·유장상법 인과 해석 채택 X
- 객관 기하학 형태 분류만

### 사용자 출력 면책 (ADR-006/010 정합)

`DEFAULT_DISCLAIMERS` 3건 강제:
1. "본 결과는 객관 기하학적 형태 분류이며 길흉화복·운명·성격과 무관합니다."
2. "한국인 안면 인체측정학 KCI 학술 출처 기반의 통계 비교입니다."
3. "마의상법·유장상법 등 전통 관상학 인과 해석은 채택하지 않습니다."

회귀 자동 검증 (인과 표현 0건, 학파 회피 명시).

### 학술 출처 (KCI 검증 — references/korean-face-anthropometry.md)

- 송우철 외 (2017) DBpia NODE07133895
- 최윤경·이경희 (2009) DBpia NODE09916734
- 노상훈 외 (1998) JKAOMS
- POSTECH HFES (2012)

## 회귀 18 PASS

`engine/divination/test_face_shape.py`:

**메트릭 산출 (3건)**:
1-3. compute_face_metrics + jaw_angle_from_points 정합

**영문↔한글 매핑 (2건)**:
4-5. SHAPE_KOREAN_TO_LATIN + SHAPE_LATIN_TO_KOREAN 완전성

**면책 (3건)**:
6-8. DEFAULT_DISCLAIMERS 개수 + 인과 표현 0건 + 학파 회피 명시

**보고서 §4 회귀 10건**:
9. case_001 목형 standard
10. case_002 목형 extreme
11. case_003 화형 standard
12. case_004 화형 sharp_chin
13. case_005 토형 standard
14. case_006 토형 wide
15. case_007 금형 angular
16. case_008 금형 square
17. case_009 수형 round
18. case_010 복합형 fallback

**메타데이터 (5건)**:
- 학술 출처 URL 존재
- matched_criteria 비어있지 않음
- morphological_name 학파 용어 0건
- frozen dataclass
- latin face_scoring 호환

## 검토한 옵션

### A. 보고서 5형 명세 그대로 본문화 (채택)

- 장점:
  - 학술 출처 4건 라이브 검증 통과
  - 보고서 §3 YAML 임계값 + §4 회귀 10건 정합
  - ADR-018 DEFER 해소
  - face_scoring.py 영문 face_shape 호환 (latin 매핑)
- 단점:
  - 한국인 표본 일부 한정 (성인 + 여성 + 청소년)
  - 임계값은 학술 기반 추정 (실 분포 보정 미반영)

### B. face_scoring.py 직접 보강 (face_shape 산출 로직 추가)

- 장점: 1모듈 통합
- 단점:
  - face_scoring.py 532줄 거대화
  - 12궁 점수와 5형 분류 책임 분리 위반

### C. LLM 페르소나에서 5형 분류 처리

- 장점: 백엔드 단순
- 단점:
  - CLAUDE.md §0 결정론 + LLM 분리 정신 위반
  - 재현성 0

## 채택

**A 채택**. 별도 모듈 + face_scoring.py 호환 + ADR-018 정합.

## 결과

### 신규 파일
- `engine/divination/face_shape.py` (5형 결정론 분류 모듈)
- `engine/divination/test_face_shape.py` (회귀 18 PASS)
- `vault/decisions/ADR-022-face-shape-classifier.md` (본 ADR)
- `vault/references/korean-face-anthropometry.md` (KCI 학술 출처)
- `vault/reports/face-shape-classifier-research.md` (사실성 분리 결과)
- `vault/done/face-shape-5형-classifier.md` (완료 기록)

### vault 영속화
- `vault/decisions/INDEX.md` (ADR-022 추가)
- `vault/done/INDEX.md` (관상 도메인 행 추가)

### face_scoring.py 호환
- face_shape.py 결과의 `latin` 필드는 face_scoring.py가 소비하는
  영문 face_shape 5종(round·square·oval·long·inverted_tri)과 호환
- 통합 사용 시: `classify_face_shape(metrics).latin` → face_scoring.py metrics에 주입

## 한계

- 임계값은 학술 추정 (운영 데이터 누적 후 보정 별도 ADR)
- 한국인 표본 일부 한정 (성인·여성·청소년 → 노인 표본 미반영)
- 2D 프로젝션 기반 → 측면 각도 왜곡 가능
- face_reading.py LLM 페르소나 통합 호출은 별도 작업 (옵션)
- EU AI Act §50(3) UI 고지문 통합은 별도 ADR

## 면책

- 본 모듈은 **순수 기하학 결정론 분류** — LLM 호출 0건
- 사용자 출력 disclaimers 강제 (ADR-006/010/014)
- 마의·유장상법 인과 해석 절대 채택 X
- 임상·심리 진단 절대 X
- EU AI Act 감정 추론 명시 고지 적용 의무 (사용자 출력 시)

## 향후

- face_reading.py LLM 페르소나 통합 호출 (옵션 작업)
- EU AI Act + 한국 PIPEA UI 고지문 (별도 ADR)
- 임계값 운영 데이터 보정 (post_traffic)
- 노인·아동 표본 추가 (별도 ADR)

## 메타

- ADR-017 절차 세 번째 본문화 사례 (ADR-020 L2 photo_quality · ADR-021 B6 DreamNet 다음)
- ADR-018 DEFER (5형 분류 구현) 해소
- PROMPT_face-shape-classifier.md → 보고서 수령 → ADR-022 본문화 = 완전 파이프라인
- 본 ADR은 immutable
