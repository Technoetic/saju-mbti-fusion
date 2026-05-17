---
type: prompt_template
target: deepresearch
purpose: MediaPipe 478 keypoints 기반 5형(목·화·토·금·수) 관상 분류 결정론 규칙
created: 2026-05-17
related_module: engine/divination/face_reading.py (LLM Vision) + engine/divination/face_scoring.py
related_adr:
  - ADR-002-saju-option-A (학파 회피 정신)
  - ADR-006-legaltech-rejected (자문 거절)
  - ADR-010-name-sibling-factuality (사실성 분리)
  - ADR-018-face-goldenset-policy (관상 골든셋)
priority: high
status: draft
---

# 딥리서치 프롬프트 — 관상 5형 결정론 분류

## 사용법

본 프롬프트는 본 시스템 관상 결정론 엔진 결손 보강용. 현 구현은
[engine/divination/face_reading.py](../../engine/divination/face_reading.py)
LLM Vision(Gemini) 기반 — 학파 인과 해석 위험 차단은 페르소나 시스템
프롬프트로만 제어. **MediaPipe 결정론 엔진으로 LLM과 분리**해야 CLAUDE.md
§0 "결정론 엔진 + LLM 작문 분리" 정신 완성.

ADR-018(관상 골든셋 내부 한정)과 짝을 이루는 객관 형태 분류 엔진 구축이
목표. ADR-002 "학파 회피" 정신 유지.

마의상법·유장상법 같은 고전 학파의 인과 해석(예: "이마 넓으면 출세")은
**채택 불가**. 대신 한국인 안면 인체측정학(anthropometry)으로 검증 가능한
형태 비율 분류만 채택.

---

## 프롬프트 본문

```
MediaPipe Face Landmarker 478 keypoints 기반으로 한국인 얼굴을 5형
(목형·화형·토형·금형·수형) 또는 그에 준하는 객관 형태로 분류하는
결정론 규칙을 조사해주세요.

본 자료는 운세 SaaS 백엔드의 결정론 분류 엔진용이며, 관상 학파의
인과 해석(예: "이마 넓으면 출세")은 채택 대상이 아닙니다.
**형태 비율 + 학술 검증 가능 출처만 필요**합니다.

### 요구사항

#### 1. 한국인 안면 인체측정학 학술 출처

- KCI/RISS/DBpia 등재 한국인 안면 측정 논문
- 우선 분야: 의학(성형외과·치과교정학)·인류학·법의학
- 필수 데이터:
  - 표본 크기·연령·성별 분포
  - 측정 지표(얼굴 너비·길이·턱각도 등)의 한국인 평균·표준편차
  - DOI 또는 KCI URL (라이브 검증 가능해야 함)
- 가짜 인용 절대 금지 — 실제 검색·조회 가능한 출처만

#### 2. MediaPipe 478 keypoints 매핑

각 측정 지표를 478 keypoints의 어느 인덱스 조합으로 계산하는지 명시:

- 얼굴 너비(zygomatic width): keypoints[A] ↔ keypoints[B] 거리
- 얼굴 길이(face height): keypoints[C] ↔ keypoints[D] 거리
- 턱각도(mandibular angle): keypoints[E,F,G]로 형성되는 각도
- 이마 너비·턱 너비·코 길이·인중 등 추가 지표

각 keypoint 인덱스는 공식 MediaPipe 문서 또는 GitHub mediapipe/mediapipe
저장소의 face_landmarker 가이드 출처로 검증.

#### 3. 5형(또는 그에 준하는) 분류 규칙 — 결정론

각 형태의 분류 기준을 **수치 임계값**으로 제시:

예시 형식:
```yaml
shape_type: "토형"
criteria:
  - face_width_height_ratio: ">= 0.85"
  - jaw_angle_deg: ">= 115"
  - reference_paper: "<KCI URL>"
```

학파별 해석 차이가 큰 영역은 **객관 형태명**(예: "광대뼈 발달형")으로
대체. 운세 인과 해석(길흉)은 본 결과에 절대 포함 금지.

#### 4. 학파 회피 — 인과 해석 배제

다음은 본 조사 대상이 아닙니다:
- ❌ "이마 넓은 사람은 출세한다" 같은 인과 단정
- ❌ "관골 발달은 성격이 강하다" 같은 도그마
- ❌ 마의상법·유장상법 등 고전 학파 통설 그대로 옮기기
- ❌ 통계 미명시 인기 관상서 인용

다음만 채택:
- ✅ 학술 논문이 측정·통계한 한국인 평균·분포
- ✅ MediaPipe 공식 keypoint 매핑
- ✅ 의학·인류학·법의학 출처

#### 5. 회귀 테스트 데이터셋 제안

본 시스템 회귀 검증용 keypoint 더미 데이터 + 기대 분류 결과 10쌍 이상:

```json
[
  {
    "id": "case_001",
    "keypoints_subset": {...},
    "expected_shape": "토형",
    "expected_metrics": {
      "face_width_height_ratio": 0.91,
      "jaw_angle_deg": 121.5
    }
  }
]
```

#### 6. 라이선스·운영 검토

- 인용 학술 자료의 상업 SaaS 사용 가능 여부
- 한국 개인정보보호법상 안면 측정 데이터 처리 규정
- EU AI Act §50(3) 감정 추론 명시 고지 (관상 적용 검토)

### 출력 형식

1. **검증된 학술 출처 표** (저자·연도·KCI URL·DOI·표본·핵심 지표)
2. **MediaPipe keypoint 매핑 표** (지표·인덱스·계산식·출처)
3. **5형 분류 규칙 YAML** (형태별 임계값·근거 논문)
4. **회귀 데이터셋 JSON** (10쌍 이상)
5. **라이선스·법규 점검 보고**
6. **본 조사의 한계** (가짜 인용 의심 출처·표본 한정 등)

### 검증 기준

본 보고서가 받아들여지려면:
- 모든 학술 인용이 KCI/RISS/DBpia URL로 라이브 검증 가능
- 모든 keypoint 인덱스가 MediaPipe 공식 문서로 검증 가능
- 학파 인과 해석 0건
- 회귀 데이터셋 10쌍 이상

위 조건 미충족 시 ADR-010 사실성 분리에 따라 거부될 수 있습니다.
```

---

## 본 시스템 채택 절차 (보고서 수령 후)

1. `/squeeze-report` 명령어로 ADR-010 사실성 분리
2. 학술 인용 KCI/RISS 라이브 검증
3. ACCEPT 후보:
   - 신규 ADR (관상 5형 결정론 분류 정책)
   - `engine/face/shape_classifier.py` 모듈 + 회귀 N건
   - `data/face_anthropometry_korean.json` 학술 데이터
   - vault/references/ 학술 출처 영속화
4. REJECT 항목:
   - 학파 인과 해석 → `permanently_rejected` 명시
   - 가짜 인용 → 출처 폐기

## 면책

- 본 프롬프트로 받은 보고서도 ADR-010 사실성 분리 의무
- 인과 해석 채택 금지 (학파 회피)
- 사용자 출력에 면책 자동 포함 (관상 = 객관 형태 분류, 길흉 X)
- EU AI Act §50(3) 감정 추론 명시 고지 적용
