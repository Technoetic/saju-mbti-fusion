---
type: adr
status: accepted
date: 2026-05-17
domain: [face]
related:
  - ADR-005 (claude-opus-vision Stage 2 결정론 입력)
  - ADR-006 (자문 거절)
  - ADR-010 (사실성 분리)
  - ADR-022 (face_shape 5형 — 부위 단위 확장 패턴)
related_report: ../reports/facial-feature-classification-phase1
related_module: engine/divination/facial_feature_classifier.py
---

# ADR-034 — 부위별 형상 결정론 분류 Phase 1 (입꼬리: 앙월구·복주구·일자구)

## 상태

Accepted (2026-05-17). 외부 딥리서치 보고서 squeeze-report 결과 본문화.

## 맥락

PROMPT_facial-feature-classification 의뢰의 외부 딥리서치 결과 보고서를
정독한 결과 (1차 분석/판정 Haiku 서브에이전트):

- 보고서 7개 후보(C1~C7) 중 **C5(앙월구) 단독만 구체 임계값 명시**
- C5: 입꼬리 각도 > 0도 (구체적, 측정 가능, 출처 명시)
- 나머지 C1·C2·C4·C7: "평균 + 0.5*SD (예시)" 표기만, 구체 μ·σ 부재 → ADR-010 빈 약속
- C3(눈썹): 출처 "추가 발굴 필요" → ADR-010 팩트 미충족
- C6(귀): MediaPipe Face Landmarker 미지원 → 기술 결손

본 ADR은 C5 1건만 본문화. 나머지는 reports/facial-feature-classification-phase1.md
`deferred_pending_research`·`permanently_rejected`에 영속화.

## 결정

### 부위 단위 결정론 분류 모듈 신규 도입

`engine/divination/facial_feature_classifier.py` 신규. ADR-022(5형 윤곽)와
직교(orthogonal) — 입꼬리 키포인트만 사용, face_width_height_ratio 등
윤곽 메트릭 무관.

### 분류 3종 (앙월구·복주구·일자구)

| 분류명 | 한자 | 측정 |
|---|---|---|
| 앙월구 | 仰月口 | 입꼬리 각도 ≥ +2도 (수평 대비) |
| 일자구 | 一字口 | -2도 < 각도 < +2도 (잡음 마진) |
| 복주구 | 覆舟口 | 입꼬리 각도 ≤ -2도 |

임계값 ±2도 = 측정 잡음(MediaPipe 478 키포인트 정밀도) + 자연 비대칭 마진.

### 측정 알고리즘

MediaPipe Face Landmarker 478 키포인트:
- KP_61: 좌측 입꼬리 (사용자 기준)
- KP_291: 우측 입꼬리
- KP_13: 윗입술 중앙 (baseline 계산용)
- KP_14: 아랫입술 중앙 (baseline 계산용)

baseline_y = (KP_13.y + KP_14.y) / 2 — 입 가로 중심선

좌우 입꼬리 각각의 baseline 대비 각도 측정:
- +값 = 입꼬리가 baseline보다 위 (앙월구 방향)
- -값 = 입꼬리가 baseline보다 아래 (복주구 방향)

평균 각도로 최종 분류.

### 입력 경로 3종

| 경로 | metrics 형식 | 신뢰도 |
|---|---|---|
| 1 | `{"mouth_corner_lift_angle": <float>}` — 사전 계산 | HIGH |
| 2 | `{"landmarks": {61, 291, 13, 14: [x, y]}}` — 풀 키포인트 | HIGH |
| 3 | `{"mouth_corner_left": [x,y], "mouth_corner_right": [x,y]}` — 직접 | 일자구 폴백 (baseline 부재) |

클라이언트(브라우저 MediaPipe)는 경로 2 권장. 경로 1은 클라이언트가
사전 계산한 각도를 보낼 때.

### Stage 2 통합

`_build_deterministic_scores_summary`에 신규 인자 `facial_features` 추가:
- 분류 결과를 한국어 라벨로 Stage 2(Gemini)에 전달
- "facial_features": {"mouth_corner": {"shape": "앙월구"}}
- Stage 2가 본 결정론 출처 라벨을 사극 어조로 인용 가능
- Gemini 사전학습 인입 X (ADR-005 Supplement 5 정신)

### 응답 dict 신규 필드

`facial_features` — 부위별 결정론 분류 결과 dict. 사용자 응답 노출
(검증 가능성, ADR-010).

## 출처 (KCI/KoreaScience 학술 검증)

| 출처 | URL | 검증 |
|---|---|---|
| 한국인 입에 대한 생체계측학적 연구 | https://koreascience.kr/article/JAKO200810103458095.pdf | 보고서 [20], 라이브 URL |

추가 잠재 출처 (DEFER, Phase 2 후속):
- 노상훈 외 (1998) 하악각 — 턱 분류
- 최윤경·이경희 (2009) — 눈 분류
- PMC11431719 한국 비강 코 형태 — 코 분류 (신규)

## ADR-010 사실성 분리 정합

| 등급 | 본 ADR 처리 |
|---|---|
| 🟢 팩트 | 입꼬리 각도 측정 (MediaPipe 478 키포인트, 결정론) + KoreaScience 학술 출처 |
| 🟡 구조 | 앙월구·복주구·일자구 분류명 (학파 통설 명칭, 결정론 출처에서만 흐름) |
| 🔴 도그마 | 사상체질(태음인·소양인) 인용 — **본문화 X** 명시 (ADR-006 정신) |

## ADR-006 자문 거절 정합

- ✅ 운명 매핑 X: "앙월구라 복을 부른다" 같은 학파 운명 매핑 코드/문서 0건
- ✅ 분류 명칭만 결정론 출처에서 흐름. Stage 2가 자연어로 풀어쓸 때
  ADR-005 Supplement 5 (학파 운명 매핑 금지) 정신 유지
- ✅ 면책 자동 부착: "본 분류는 입꼬리 각도 측정 결과로, 운명·길흉·관운 매핑이 아닙니다"

## 한계

- **표정 변화 민감**: 무표정 정면 사진 권장 (보고서 §3.4 한계 명시)
- **임계값 ±2도 = 휴리스틱**: 한국인 표본 통계(JAKO200810103458095) 구체 μ·σ
  부재 → 잡음 마진 ±2도는 향후 운영 데이터 보정 가능 (post_traffic)
- **사상체질 인용 미본문화**: 보고서가 인용한 태음인·소양인 비교는 본
  ADR에서 의도적 제외 (ADR-006 자문 거절 정신)
- **Phase 1 한정**: 코·눈썹·눈·귀·턱 5부위 분류는 보고서 구체 임계값 부재로
  DEFER (reports/facial-feature-classification-phase1.md)
- 본 ADR은 **immutable**. Phase 2 확장 시 새 ADR

## 회귀

`engine/divination/test_facial_feature_classifier.py` 신규 18건 (PASS 18/18):

분류 검증:
- test_angswolgu_detected_when_corners_lifted
- test_bokjugu_detected_when_corners_dropped
- test_iljagu_detected_when_corners_near_baseline
- test_iljagu_within_noise_margin

입력 경로 3종:
- test_classify_from_metrics_landmarks_dict
- test_classify_from_metrics_direct_corners_falls_back_to_iljagu
- test_classify_from_metrics_precomputed_angle
- test_classify_from_metrics_precomputed_negative_angle

비정상 입력 None 반환 4건

ADR 정합 검증 6건:
- test_disclaimer_explains_no_fate_mapping
- test_source_url_is_koreascience_paper
- test_no_saaschecheijl_dogma_in_module
- test_classification_orthogonal_to_face_shape
- test_result_has_left_and_right_angles
- test_kp_indices_match_official_mediapipe_doc

face_reading.py 통합 회귀 21건 유지 (Phase 19~22 누적, 신규 변경 무회귀).

## 관련

- 보고서 원문: `한국인 얼굴 부위별 형상 분류를 위한 MediaPipe Face Landmarker 478 키포인트 임계값 및 학술·인체측정학 출처 분석 보고서.md` (프로젝트 루트)
- squeeze 정독 결과: `vault/reports/facial-feature-classification-phase1.md`
- 신규 모듈: `engine/divination/facial_feature_classifier.py`
- 회귀: `engine/divination/test_facial_feature_classifier.py`
- 통합 위치: `engine/divination/face_reading.py` (generate_face_reading + _build_deterministic_scores_summary)
