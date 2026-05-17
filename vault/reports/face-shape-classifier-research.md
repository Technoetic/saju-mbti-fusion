---
type: external_report
status: applied
date: 2026-05-17
source: deepresearch
domain: face
factuality: kci_verified
applied_to:
  - "§2.1 MediaPipe 478 키포인트 매핑 → face_scoring.py 이미 사용 중 + face_shape.py jaw_angle_from_points (보고서 정합)"
  - "§2.2 메트릭 산출 (FWHR + jaw_angle + bz/bg) → face_shape.py compute_face_metrics (보고서 §2.2 본문화)"
  - "§3 5형 YAML 임계값 → face_shape.py classify_face_shape (5형 + 복합형 fallback)"
  - "§4 회귀 10건 (case_001~010) → test_face_shape.py (18 tests PASS)"
  - "§5 법적 컴플라이언스 → DEFAULT_DISCLAIMERS (ADR-006/010 정합) — UI 고지문은 별도 ADR"
  - "§1.1 학술 출처 4건 → vault/references/korean-face-anthropometry.md (KCI 검증)"
related:
  - decisions/ADR-022-face-shape-classifier
  - decisions/ADR-018-face-golden-set-policy
  - decisions/ADR-010-name-sibling-factuality
  - references/korean-face-anthropometry
  - templates/PROMPT_face-shape-classifier
original_file: ../../MediaPipe 478 키포인트 기반 한국인 안면 형태 결정론적 분류 엔진 설계 및 법적 컴플라이언스 심층 연구 보고서.md
adr_017_first_application: "2026-05-17 (분석/판정 분리 절차 첫 적용 + ADR-017 세 번째 본문화 사례)"
permanently_rejected:
  - "마의상법·유장상법 등 전통 관상학 인과 해석 — 보고서 §0 명시적 배제 + ADR-006/010 정합"
  - "통계적 권위 수사 ('단정적', '완벽한' 등) — 보고서에 부재 (학술 어조 유지)"
deferred_pending_decision:
  - "face_reading.py LLM 페르소나 통합 호출 — 옵션 작업"
  - "§5 EU AI Act + 한국 PIPEA UI 고지문 — 별도 ADR + 프론트엔드 작업"
  - "한국인 표본 보정 (운영 데이터 누적 후 임계값 동적 스케일링) — post_traffic"
already_implemented:
  - "MediaPipe 478 키포인트 → face_scoring.py 12궁 점수 (532줄, 이미 사용)"
  - "face_shape 영문 5종 (round/square/oval/long/inverted_tri) → face_scoring.py 소비"
  - "ADR-018 골든셋 정책 (face_shape 분류 설계 ACCEPT, 구현 DEFER) — 본 ADR-022로 DEFER 해소"
---

# MediaPipe 478 키포인트 기반 5형 결정론 분류 — 사실성 분리 + ADR-022 본문화

## 보고서 요약

PROMPT_face-shape-classifier.md 의뢰 결과 수령. 56KB 대형 보고서.
한국인 안면 인체측정학 KCI 학술 + MediaPipe 478 키포인트 매핑 + 5형
YAML 분류 + 회귀 10건 + 법적 컴플라이언스 (EU AI Act + 한국 PIPEA).

## 🟢 팩트 (검증 통과)

| 주장 | 검증 |
|---|---|
| 송우철 외 (2017) DBpia NODE07133895 | ✅ DBpia 라이브 검증 |
| 최윤경·이경희 (2009) DBpia NODE09916734 | ✅ DBpia 라이브 검증 |
| 노상훈 외 (1998) JKAOMS | ✅ JKAOMS PDF 검증 |
| POSTECH HFES (2012) | ✅ POSTECH 공개 PDF |
| MediaPipe 478 키포인트 인덱스 (10·152·234·454·58·288) | ✅ 공식 문서 일치, face_scoring.py 이미 사용 |
| 5형 임계값 + 회귀 10건 JSON | ✅ 빈 약속 아님 (보고서 §3·§4 실 데이터) |

## 🟡 구조 (시스템 설계 명제)

- 5형 분류 + 복합형 fallback (보고서 §3)
- 3 핵심 메트릭 (FWHR + jaw_angle + bz/bg)
- LLM 페르소나 + 결정론 엔진 분리 (CLAUDE.md §0)
- DEFAULT_DISCLAIMERS 강제 (ADR-006/010)
- EU AI Act + 한국 PIPEA 준수 의무

## 🔴 도그마 (영구 거부)

- 마의상법·유장상법 인과 해석 — 보고서 §0 명시적 배제
- 통계 권위 수사 — 보고서 부재 (학술 어조 유지)

## 본 시스템 반영 (ADR-017 분석/판정 분리 절차 적용)

### 분석 에이전트 (Haiku)
후보 1건 (C1 = 5형 분류 엔진 통합) + 거부 0건 + 사용자 결정 1건 (U1 = 영문↔한글 매핑)

### 판정 에이전트 (Haiku)
**ACCEPT 1건** — ADR-002·006·010·018·CLAUDE.md§0 모두 정합

### 오케스트레이터 직접 검증
- face_scoring.py 라인 229·303·403 face_shape 소비만 확인 (산출 로직 0건) ✅
- 보고서 §4 case_001~010 JSON 실 데이터 직접 확인 ✅
- ADR-018 라인 35-36 DEFER 명시 확인 ✅

### 본문화 (ADR-022)

| 영역 | 파일 | 결과 |
|---|---|---|
| 5형 분류 함수 | face_shape.py | classify_face_shape + 5 임계값 + fallback |
| 메트릭 산출 | face_shape.py | compute_face_metrics + jaw_angle_from_points |
| 회귀 10건 | test_face_shape.py | 18 tests PASS |
| 영문↔한글 매핑 | face_shape.py | SHAPE_KOREAN_TO_LATIN dict (face_scoring 호환) |
| 학술 출처 | references/korean-face-anthropometry.md | KCI 4건 영속화 |
| 면책 | DEFAULT_DISCLAIMERS | 3건 강제 + 회귀 검증 |

## 회귀 18 PASS

(ADR-022 명세 참조)

## 신뢰성 평가

| 항목 | 평가 |
|---|---|
| 학술 출처 (KCI/DBpia/JKAOMS/POSTECH) | ✅ 모두 라이브 검증 |
| MediaPipe 478 키포인트 매핑 | ✅ 공식 문서 일치 |
| 5형 임계값 + 회귀 10건 | ✅ 빈 약속 아님 |
| ADR-018 정합 + DEFER 해소 | ✅ |
| 도그마 0건 | ✅ |
| 본 프로젝트 적합성 | ✅ 매우 높음 (관상 결정론 엔진 완성) |

**총평**: 본 보고서는 PROMPT_face-shape-classifier.md 의뢰 결과로 정합도 매우 높음.
ADR-017 절차 세 번째 본문화 사례 (ADR-020 L2 + ADR-021 B6 다음).
분석 에이전트 오추정 0건 (실 코드 직접 확인 의무 작동 입증).

## 향후

- face_reading.py LLM 페르소나 통합 호출 (옵션)
- EU AI Act + 한국 PIPEA UI 고지문 (별도 ADR + 프론트엔드)
- 임계값 운영 데이터 보정 (post_traffic)
- 노인·아동 표본 추가 (별도 ADR)

## 메타

- 영속화: 2026-05-17 (ADR-010 사실성 분리 + ADR-022 본문화)
- ADR-017 세 번째 본문화 성공 사례
- 분석 에이전트 오추정 0건 (보강된 프롬프트 작동 입증)
- ADR-018 DEFER 1건 해소 (5형 분류 구현)
- 본 노트 immutable
