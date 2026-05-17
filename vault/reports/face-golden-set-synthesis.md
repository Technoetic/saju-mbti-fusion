---
type: external_report
status: received_partial_application
date: 2026-05-17
source: deepresearch
domain: face
applied_to:
  - C1 안면 해부학 매핑 + MediaPipe 478 → ADR-018 §2.1 + face_scoring.py 이미 일치
  - C3 G22~G36 합성 사양 15개 (설계만) → ADR-018 §2.2
  - C4 회귀 테스트 JSON 스키마 (설계만) → ADR-018 §2.3
  - C5 사실성 분리 정책 + 사용자 노출 금지 → ADR-018 §1 (영구 정책)
deferred:
  - C2 합성 도구 선택 (FLUX.1 vs SDXL) — 🔵 사업 단계
  - R2 실제 G22~G36 이미지 생성 — 보고서 §5.3 자체 "과적합 유도" 명시
permanently_rejected:
  - Gemini 1차 도구 — SynthID 워터마크 + RLHF 미화 편향
  - 사용자에게 흉상/길상 비교 노출 — ADR-006 위반
neo4j_synced: false
factuality: verified_with_self_deferral
related:
  - decisions/ADR-004-face-keypoint-scoring
  - decisions/ADR-005-claude-opus-vision
  - decisions/ADR-006-legaltech-rejected
  - decisions/ADR-010-name-sibling-factuality
  - decisions/ADR-018-face-golden-set-policy
  - reports/face-image-generation.md (이전 거부 사례 — 본 보고서가 그 정책 강화 응답)
original_file: ../../관상 분석 SaaS 백엔드 회귀 테스트용 골든셋 합성 이미지 사양 및 통합 설계 보고서.md
verified_against:
  - https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker (MediaPipe 478 공식)
  - Gemini 3.1 Flash Image 가격 ($0.067/1K 또는 $0.039/장)
  - FLUX.1 schnell Apache 2.0 라이선스 (GitHub 공식)
processed_by: "/squeeze-report 슬래시 명령어 (ADR-017) — 분석/판정 분리 패턴 + Haiku"
---

# 관상 분석 SaaS 백엔드 회귀 테스트용 골든셋 합성 이미지 사양 — 사실성 분리 검토

## 본 보고서의 등급

ADR-010 사실성 분리 + 분석/판정 분리 (ADR-017) 적용 결과 **혼합 등급**:

본 보고서는 본 프로젝트의 이전 [[face-image-generation]] (관상 길상/흉상
합성 보고서, ADR-010 거부)에 대한 정책 강화 응답. 본 보고서는 그 거부 정책을
충실히 준수하며 작성됨:
- "흉상/길상" 직접 표현 0건 (모두 객관 해부학)
- 사용자 노출 금지 정책 자체 명시 (§5.2)
- "현 시점 즉시 생성 X" 자체 권고 (§5.3)

## 🟢 팩트 (검증 완료)

| 영역 | 검증 |
|---|---|
| MediaPipe Face Landmarker 478 인덱스 매핑 | ✅ Google AI Edge 공식 문서 |
| 안면 해부학 객관 기준점 (Menton·Glabella·Pronasale 등) | ✅ 표준 의학 용어 |
| Gemini 3.1 Flash Image 가격 $0.067/1K | ✅ Vertex AI 공식 가격표 |
| FLUX.1 schnell Apache 2.0 라이선스 | ✅ Black Forest Labs GitHub |
| SDXL Stability AI 정책 ($1M 매출 분기점) | ✅ Stability AI 공식 (2026-05 시점) |

## 🟡 구조 (시스템 설계 명제)

- G22~G36 합성 사양 15개 (5 face_shape × 3 메트릭 변형)
- 회귀 테스트 JSON 스키마 (expected_metrics + expected_palace_scores_range)
- 사용자 노출 금지 정책 (격리 디렉토리)
- "FLUX.1 schnell 1차 + SDXL+ControlNet 보조" 권장

## 🔴 도그마 (거부)

| 항목 | 판정 |
|---|---|
| Gemini 1차 도구 권장 | ❌ 보고서 §2.1 자체가 RLHF 미화 편향 + SynthID 워터마크 위험 명시 → 본 시스템 거부 |
| "RLHF 미화 편향 극복 가능성" 정성 평가 (FLUX 중간 / SDXL 우수) | 🟡 구체 근거 없음 — 구조적 추정으로만 수용 |
| 사용자에게 비대칭/대칭 비교 노출 | ❌ 본 보고서가 직접 금지함 (사용자 노출 금지 정책) |

## 본 시스템 반영 (ADR-018 부분 채택)

[[../decisions/ADR-018-face-golden-set-policy]] 본 ADR로 다음 통합:

### ✅ ACCEPT (정책·사양 영속화)

- C1 안면 해부학 매핑 — face_scoring.py가 이미 사용 중 패턴과 일치 (사후적 정당화)
- C3 G22~G36 사양 — 사양 설계만 영속화 (실제 생성은 DEFER)
- C4 회귀 JSON 스키마 — 설계만 (test_golden_set.py 확장 시 채택 가능)
- C5 사용자 노출 금지 정책 — ADR-018 §1로 영구 정책화

### ⏸️ DEFER (운영 데이터 후 별도 ADR)

- C2 합성 도구 선택 (FLUX.1 vs SDXL) — 🔵 사업 단계
- R2 실제 G22~G36 이미지 생성 — 보고서 §5.3 자체 "과적합 유도" 권고

### ❌ REJECT (영구)

- Gemini 1차 도구 선택 (SynthID + RLHF 미화 편향)
- 사용자에게 흉상/길상 노출
- 합성 이미지 운명론 메타데이터

## 본 보고서의 의미

본 보고서는 본 프로젝트의 **이전 거부 사례** ([[face-image-generation]],
2026-05-17 1차)에 대한 응답 보고서. 이전 거부 정책을 완벽히 준수하며 작성:

1. "흉상/길상" 직접 표현 0건
2. 사용자 노출 금지 정책 본문에 명시
3. 합성 이미지 = 회귀 테스트 한정 자산
4. "현 시점 즉시 생성 X" 자체 권고 (보고서 §5.3)

본 보고서가 ADR-010 정신을 외부 보고서가 자체적으로 준수한 첫 사례.

## /squeeze-report 처리 결과

본 보고서는 [/squeeze-report 슬래시 명령어](../decisions/ADR-017-squeeze-report-command.md)
의 첫 실전 적용 사례. 분석/판정 분리 + Haiku 모델로 처리:

- 분석 (Haiku Subagent 1): 5 후보 + 2 거부 + 2 사용자 결정 영역 추출
- 판정 (Haiku Subagent 2): 3 ACCEPT + 1 REJECT + 2 DEFER 판정
- 오케스트레이터 (Opus 메인): ADR-018 통합 본문화

## 다음 액션

- [x] ADR-018 작성 (정책 + 사양 영속화)
- [x] 본 reports 노트 영속화 (ADR-010 사실성 분리 결과)
- [ ] (DEFER) 합성 도구 선택 — 사용자 결정 후 별도 ADR
- [ ] (DEFER) 실제 G22~G36 이미지 생성 — 운영 데이터 누적 후
- [ ] (DEFER) test_golden_set.py G22~G36 스키마 확장 — 실제 합성 후

## 출처

- 본 보고서 원본: `사주/관상 분석 SaaS 백엔드 회귀 테스트용 골든셋 합성 이미지 사양 및 통합 설계 보고서.md`
- 본 보고서가 응답한 이전 거부 사례: [[face-image-generation]]
- 본 보고서 트리거 프롬프트: [[../templates/PROMPT_face-golden-set-synthesis]]

## 메타

- 영속화: 2026-05-17 (`/squeeze-report` 첫 실전 사용)
- 본 노트 immutable. 실제 합성 이미지 도입 시 별도 done 노트 + ADR.
