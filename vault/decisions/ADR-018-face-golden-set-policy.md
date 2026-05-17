---
type: adr
adr_number: 18
status: accepted
date: 2026-05-17
authors: [Technoetic]
domain: [face, meta]
related:
  - ADR-004-face-keypoint-scoring (12궁 결정론 점수)
  - ADR-005-claude-opus-vision (face_reading.py 비전 호출)
  - ADR-006-legaltech-rejected (자문·외모 평가 거절)
  - ADR-010-name-sibling-factuality (사실성 분리)
  - reports/face-image-generation.md (이전 거부 사례)
  - reports/face-golden-set-synthesis.md (본 보고서)
---

# ADR-018: 관상 골든셋 합성 이미지 정책 — 내부 한정, 사용자 노출 금지

## 배경

[[../reports/face-golden-set-synthesis]] (관상 분석 SaaS 백엔드 회귀 테스트용
골든셋 합성 이미지 사양 및 통합 설계 보고서, 2026-05-17) 수신. ADR-010
사실성 분리 + 분석/판정 분리(`/squeeze-report` ADR-017) 적용 결과:

| 후보 | 판정 |
|---|---|
| C1 안면 해부학 매핑 + 478 인덱스 | ACCEPT (사양 설계만) |
| C2 생성 AI 모델 비교 | DEFER (vault/reports 영속화만, 도구 선택은 🔵) |
| C3 G22~G36 합성 사양 15개 | ACCEPT (설계만, 실제 생성은 DEFER) |
| C4 회귀 테스트 JSON 스키마 | ACCEPT (스키마 설계만) |
| C5 사실성 분리 정책 + 사용자 노출 금지 | ACCEPT (본 ADR로 정책 영속화) |
| R1 Gemini 1차 도구 | REJECT (보고서 자체가 SynthID + RLHF 미화 편향 위험 명시) |
| R2 즉시 합성 이미지 생성 | DEFER (보고서 §5.3 "과적합 유도 위험" 자체 권고) |

본 ADR은 ACCEPT 항목을 **정책으로만 영속화**. 실제 합성 이미지 생성·도구
도입은 운영 데이터 누적 후 별도 ADR 검토.

## 결정

관상 골든셋 합성 이미지는 **내부 회귀 테스트 한정 자산**. 사용자 출력에
어떠한 형태로도 노출 금지. 본 ADR은 사용 범위·정책·사양·DEFER 항목을 정의.

### 1. 영구 정책 (사용자 노출 절대 금지)

- ❌ 합성 이미지 사용자 응답 경로 노출 금지 (face_reading.py 응답·web/server.py 출력 등)
- ❌ "흉상/길상" 직접 비교·외모 평가 표현 절대 금지 (ADR-006 인용)
- ❌ 합성 이미지 메타데이터에 운명론적 표현 금지
- ❌ 변수명·주석·로그에 "길상/흉상/재물/수명/인덕" 등 도그마 표현 금지

### 2. 채택 사양 (설계 자산만)

#### 2.1 안면 해부학 객관 메트릭 (보고서 §1)

MediaPipe Face Landmarker 478 인덱스 매핑 — 본 시스템 [engine/divination/face_scoring.py](../../engine/divination/face_scoring.py)
가 이미 사용 중인 패턴과 일치:

- 이마 상단 = 인덱스 10
- 턱끝(Menton) = 인덱스 152
- 좌측 광대 = 인덱스 234 / 우측 광대 = 인덱스 454
- 코끝(Pronasale) = 인덱스 1 / 미간(Glabella) = 인덱스 9
- 입술 좌측 구각 = 인덱스 61 / 우측 = 인덱스 291
- 좌측 눈 안쪽·바깥쪽 = 인덱스 133, 33 / 우측 눈 = 362, 263

주요 메트릭:
- `R_face`: 얼굴 가로세로 비율 = D(234, 454) / D(10, 152)
- `Three_thirds`: 상정·중정·하정 = D(10,9), D(9,1), D(1,152)
- `S_asy`: 비대칭 지수 = 중심축(10→1→152) 좌우 동형 기관 거리 차

#### 2.2 골든셋 합성 사양 G22~G36 (보고서 §3) — 설계만

5 face_shape × 3 메트릭 변형 = 15 케이스:

face_shape 5종: round / square / oval / long / inverted_tri
메트릭 변형 3종: balanced / asymmetric / expressive

각 케이스는 객관 해부학 묘사만 (예: "horizontal facial width exactly equal
to vertical facial height", "right eye positioned noticeably higher"). 어떤
케이스도 "길상/흉상/재물/수명" 같은 도그마 표현 0건.

본 사양은 [[../reports/face-golden-set-synthesis]] §3에 영속화. **실제
이미지 합성은 본 ADR 단독으로 진행 X** — 별도 ADR 필요.

#### 2.3 회귀 테스트 JSON 스키마 (보고서 §4) — 설계만

```json
{
  "id": "G22_synth_round_balanced",
  "image_b64": "<base64 if generated>",
  "expected_metrics": {
    "face_shape": "round",
    "asymmetry_score": 0.05,
    "three_thirds": [33, 34, 33]
  },
  "expected_palace_scores_range": {
    "myeong": [0.4, 0.7]
  },
  "purpose": "round face + 대칭 메트릭 추출 정확도 검증"
}
```

본 시스템 [engine/divination/test_golden_set.py](../../engine/divination/test_golden_set.py)
G01~G21 (메트릭 입력만) 확장 시 본 스키마 채택 가능.

### 3. DEFER 항목

다음은 본 ADR로 채택하지 않음. 운영 데이터 누적 후 별도 ADR로 검토:

| DEFER 항목 | 사유 |
|---|---|
| C2 합성 도구 선택 (FLUX.1 vs SDXL) | 🔵 사업 단계 — 사용자 결정 영역 + 라이선스 검토 |
| R2 실제 G22~G36 이미지 생성 | 보고서 §5.3 자체 "현 시점 즉시 생성 = 과적합 유도" 명시 |
| 격리 디렉토리 위치 (step_archive/golden_synth/ 또는 별도) | 실제 생성 시점에 결정 |
| MediaPipe 합성 이미지 메트릭 추출 검증 | 합성 이미지 1건 이상 생성 후 측정 가능 |

### 4. REJECT 항목 (영구)

| REJECT | 사유 |
|---|---|
| Gemini 3.1 Flash Image 1차 도구 | SynthID 워터마크 + RLHF 미화 편향 (보고서 §2.1 자체 명시) — 비대칭 회귀 데이터 합성 불가 |
| 사용자에게 흉상/길상 비교 노출 | ADR-006 자문 거절 정책 위반 |
| 합성 이미지 운명론 메타데이터 | ADR-010 사실성 분리 위반 |

## 검토한 옵션

### A. 본 ADR로 정책만 영속화 (채택)
- 장점: ADR-006/010 정신 강화, 실제 생성은 운영 후로 지연
- 단점: 즉시 회귀 테스트 G22~G36 미적용 — 단 G01~G21로 충분 (보고서 §5.3 인정)

### B. 즉시 합성 이미지 생성 + 회귀 통합
- 장점: 골든셋 풍부화
- 단점: 보고서 자체가 "과적합 유도 위험" 명시 → 본 옵션 거부

### C. 미적용 (정책 영속화 안 함)
- 장점: 추가 작업 0
- 단점: 합리적 정책 자산 폐기, 미래 도입 시 검토 비용 증가

## 채택

**A 채택**. 본 ADR로 정책 + 사양 영속화. 실제 합성 도구·이미지 생성은 별도 ADR.

## 결과

- 본 ADR로 ACCEPT 항목 5건(C1·C3·C4·C5) 정책 통합 영속화
- [[../reports/face-golden-set-synthesis]] (보고서 전체 사실성 분리)
- DEFER 항목 4건 + REJECT 항목 3건 명시
- 코드 변경 0 (사양만 영속화, 실제 합성 이미지 0)
- 회귀 테스트 추가 X (실제 합성 이미지 없음 = 테스트 불가)

## 면책

- 본 ADR은 정책·사양 영속화. 실제 합성 도구·이미지 도입은 별도 ADR 필요
- ADR-004·005·006·010 정신 모두 보존
- 보고서 §5.3 "현 시점 즉시 생성 X" 권고 준수

## 향후 (DEFER → 활성 조건)

다음 조건 충족 시 본 ADR이 가리키는 DEFER 항목 활성:

1. SaaS 운영 데이터 3~6개월 누적
2. MediaPipe 추출 실패·메트릭 결핍 사례 실측
3. 사용자가 합성 도구 선택 (FLUX.1 schnell / SDXL+ControlNet)
4. 격리 디렉토리 + .gitignore 정책 결정
5. 합성 이미지 메트릭 추출 정확도 검증 회귀 추가

위 조건 1개라도 미충족 시 본 ADR-018이 가리키는 정책 그대로 유지.
