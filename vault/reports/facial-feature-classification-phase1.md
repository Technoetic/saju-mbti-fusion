---
type: report
status: applied
date: 2026-05-17
domain: [face]
applied_to:
  - ADR-034 (Phase 1 — 입꼬리 분류만)
  - engine/divination/facial_feature_classifier.py
factuality_separation:
  facts: ["입꼬리 각도 측정 (KP_61·291·13·14)", "임계값 > 0도 (구체)", "KoreaScience JAKO200810103458095 학술 출처"]
  structures: ["앙월구·복주구·일자구 분류명 (학파 통설 명칭)", "마진 ±2도 (측정 잡음 휴리스틱)"]
  dogmas_rejected: ["사상체질 인용 (태음인·소양인 비교, ADR-006/010 위반)", "MediaPipe Attention Mesh 용어 오류"]
permanently_rejected:
  - C3 (눈썹 — 출처 미명시, ADR-010 팩트 미충족)
  - C6 (귀 — MediaPipe Face Landmarker 미지원, Holistic 별도 모델 필요)
  - 사상체질 기반 분류 (한의학 도메인, ADR-006 자문 거절 위반)
deferred_pending_research:
  - C1 (코 — 복코·매부리코·들창코, 구체 임계값 부재)
  - C2 (코 — 매부리코·들창코 추가 분류, 구체 임계값 부재)
  - C4 (눈 — 삼백안, 구체 임계값 부재 + 사상체질 제거 필요)
  - C7 (턱 — 이중턱·딤플·사각턱, 구체 임계값 부재)
verified_urls:
  - https://koreascience.kr/article/JAKO200810103458095.pdf (한국인 입 생체계측, C5 출처)
  - https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE07133895 (송우철 2017, C1 후속)
  - https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE09916734 (최윤경·이경희 2009, C4 후속)
  - https://www.jkaoms.org/journal/download_pdf.php?spage=129&volume=32&number=2 (노상훈 1998, C7 후속)
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC11431719/ (한국 코 형태 cone-beam CT 2024, C1·C2 후속)
  - https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker (MediaPipe 공식)
---

# 한국인 얼굴 부위별 형상 분류 보고서 — 사실성 분리 + Phase 1 적용 결과

## 보고서 원문

`한국인 얼굴 부위별 형상 분류를 위한 MediaPipe Face Landmarker 478 키포인트 임계값 및 학술·인체측정학 출처 분석 보고서.md` (182줄, 프로젝트 루트)

PROMPT_facial-feature-classification 의뢰의 외부 딥리서치 결과 응답.
6부위(코·눈썹·눈·입·귀·턱) × 분류 24+ 항목 의뢰 → 보고서 응답 7개 후보 + 출처 38개.

## ADR-010 사실성 분리 결과

### 🟢 팩트 1건 (ACCEPT)

**C5. 입꼬리 — 앙월구·복주구·일자구**
- 임계값: 입꼬리 각도 > 0도 (구체 명시)
- 출처: 한국인 입 생체계측학적 연구 (JAKO200810103458095, KoreaScience)
- MediaPipe KP: 61, 291 (공식 문서 검증)
- 신뢰도: HIGH
- → ADR-034 본문화 완료

### 🟡 구조 4건 (DEFER — 임계값 추가 조사 필요)

**C1. 코 — 복코**
- 학파 통설 명칭 + KP_115·344·234·454 (콧방울 너비)
- 출처: 송우철 2017 (KCI 검증, vault/references/korean-face-anthropometry.md 기존)
- 차단 사유: 임계값 "평균 + 0.5*SD (예시)" 표기만, 구체 μ·σ 부재
- Phase 2 후속: 송우철 논문 본문 직접 fetch로 μ·σ 추출 필요

**C2. 코 — 매부리코·들창코·마늘코 등**
- 지표: bridge_curvature, nose_length
- 차단: 임계값 명시 부재 (스켈레톤만)
- Phase 2 후속: PMC11431719 (한국 비강 cone-beam CT 2024) fetch + 임계값 추출

**C4. 눈 — 삼백안**
- 홍채 KP 468~477 (MediaPipe 정밀 측정 가능)
- 출처: 최윤경·이경희 2009 (KCI 검증)
- 차단 사유: 임계값 "흰자위 노출 비율 > 임계값 (예시)" 구체 부재
- 추가 차단: 보고서가 사상체질(태음인 여성 눈 길이) 인용 — 본문화 시 완전 제거 의무

**C7. 턱 — 이중턱·딤플·사각턱**
- KP_152·148·176·149·150 / 377·400·378·379·365
- 출처: 노상훈 1998 (KCI 검증)
- 차단: 구체 임계값 부재 + 3D 깊이 의존성
- Phase 2 후속: 사각턱은 jaw_squareness 단독 가능 (이중턱·딤플은 3D 한계)

### 🔴 도그마 2건 (REJECT — 영구 거부)

**C3. 눈썹 — 초승달·일자·청수미·끊긴 눈썹**
- 차단: 출처 "추가 발굴 필요" 표기 — ADR-010 팩트 미충족
- 영구 거부: 보고서가 인용한 KCI 출처 0건. 신규 보고서 별도 수신 필요

**C6. 귀 — 칼귀·후귀·송곳귀·부처귀**
- 차단: MediaPipe Face Landmarker가 귀 키포인트 미포함 (보고서 본문 확인)
- 영구 거부: Holistic 모델 도입은 사업 결정 영역 (🔵). 본 시스템 관상
  파이프라인(Opus + face_scoring + face_shape)과 별개 인프라

**사상체질 기반 분류 (보고서 §2.1·§3.1·§3.3·§3.6 반복 인용)**
- "태음인 남성은 소양인 남성보다 콧방울 너비가 크다", "태음인 여성은
  소양인 여성보다 눈 길이가 길다", "태음인의 얼굴은 좌우 너비 > 상하 길이"
- 영구 거부: 한의학 체질 진단은 ADR-006(자문 거절) 정신 위반
- 대안: "한국인 성인 평균값" 기준만 사용 (개인 체질 분류 배제)

**MediaPipe "Attention Mesh" 용어 오류 (보고서 라인 11)**
- 실제: "Face Landmarker + refine_landmarks=True"
- 영향: 기술 신뢰성 약간 하락. 임계값 후보(C5)에는 무관

## 본 시스템 결손 영역 점검 결과

| 영역 | 현재 상태 | 보고서 후속 |
|---|---|---|
| 5형 얼굴 윤곽 분류 | ✅ ADR-022 완료 (face_shape.py 324줄) | 충돌 없음 (직교) |
| 입꼬리 분류 | ❌ 부재 → ✅ ADR-034 신규 (facial_feature_classifier.py) | Phase 1 완료 |
| 코 분류 | ❌ 부재 | DEFER (Phase 2) |
| 눈 분류 | ❌ 부재 | DEFER (Phase 2) |
| 눈썹 분류 | ❌ 부재 | REJECT (출처 0) |
| 귀 분류 | ❌ 부재 | REJECT (기술 결손) |
| 턱 분류 | ❌ 부재 (face_shape의 jaw_angle만) | DEFER (Phase 2 — 사각턱 단독) |

## 본 시스템 반영 — ADR-034 채택

신규 모듈: `engine/divination/facial_feature_classifier.py`

```python
def classify_mouth_corner(landmarks: dict[int, tuple[float, float]] | None) -> MouthCornerResult | None
def classify_from_metrics(metrics: dict[str, Any] | None) -> MouthCornerResult | None
```

face_reading.py 통합:
- `generate_face_reading` → metrics 제공 시 classify_from_metrics 호출
- `_build_deterministic_scores_summary` → facial_features 인자 추가
- 응답 dict에 `facial_features` 필드 노출

회귀 18건 PASS:
- 분류 정확도 (앙월구·복주구·일자구) 4건
- 입력 경로 3종 4건
- 비정상 입력 None 반환 4건
- ADR 정합 (면책·출처·사상체질 부재·5형 직교·좌우 각도·KP 정합) 6건

## Phase 2 후속 권고

| 우선도 | 항목 | 필요 조사 |
|---|---|---|
| 높음 | C1 복코 임계값 | 송우철 2017 본문 fetch → 콧방울 너비 μ·σ |
| 높음 | C4 삼백안 임계값 | 최윤경·이경희 2009 본문 fetch → 흰자위 노출 비율 분포 |
| 중 | C2 코 형태 추가 | PMC11431719 (한국 비강 cone-beam CT 2024) — 신규 |
| 중 | C7 사각턱 | 노상훈 1998 하악각 분포 |
| 낮음 | C3 눈썹 | 신규 출처 발굴 필요 |
| ⏸️ | C6 귀 | MediaPipe Holistic 도입 결정 (🔵 사업 단계) |

## 짜낼 가치 종합

| 영역 | 상태 |
|---|---|
| C5 앙월구·복주구·일자구 | ✅ 채택 (ADR-034) |
| C1·C2·C4·C7 코·눈·턱 분류 | ⏸️ DEFER (구체 임계값 추가 조사 후) |
| C3 눈썹 | ❌ 영구 거부 (출처 0) |
| C6 귀 | ❌ 영구 거부 (기술 결손) |
| 사상체질 인용 | ❌ 영구 거부 (ADR-006 위반) |
| 새 출처 PMC11431719 (한국 비강 CT) | ✅ vault/references 신규 영속화 |

본 보고서로부터 짜낼 가치 — Phase 1 C5 단독 본문화 완료. 잔여 6건은
구체 임계값 추가 조사 후 Phase 2로 분리.
