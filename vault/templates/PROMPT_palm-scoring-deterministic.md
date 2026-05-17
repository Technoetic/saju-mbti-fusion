---
type: prompt_template
target: deepresearch
purpose: 손금 4대 선 + 좌우 손 결정론 점수표 (MediaPipe Hand 21 키포인트 기반)
created: 2026-05-17
related_module: engine/divination/palm_reading.py (LLM Vision) + engine/divination/face_scoring.py (참조 패턴)
related_adr:
  - ADR-005-claude-opus-vision (Vision LLM)
  - ADR-006-legaltech-rejected (자문 거절)
  - ADR-010-name-sibling-factuality (사실성 분리)
  - CLAUDE.md §0 (결정론 엔진 + LLM 작문 분리)
priority: high
status: draft
related_report: ../reports/palm-reading-app.md (C1·C2 DEFER 영역 직격)
---

# 딥리서치 프롬프트 — 손금 결정론 점수 엔진

## 사용법

본 프롬프트는 본 시스템 결손 영역 정밀 직격용. palm-reading-app.md
ADR-017 첫 적용 결과 다음 DEFER 2건 도출:

- **C1**: 좌우 손 교차 분석 (선천=비우세수 / 후천=우세수)
- **C2**: 4대 선 + 보조선 결정론 점수표 (보고서 본문 임계값 미명시)

본 시스템 [engine/divination/face_scoring.py](../../engine/divination/face_scoring.py)
532줄은 MediaPipe Face Landmarker 478 키포인트 → 12궁 0.0~1.0 결정론 점수
산출 (LLM 없이) — **CLAUDE.md §0 분리 정책 완성 사례**.

손금 영역에 **동일 패턴**을 적용하려면 학술 임계값 + MediaPipe Hand 21
키포인트 매핑 명세가 필요한데, 기존 손금 보고서는 "호 넓이·곡률" 모호
표현만 제공하여 본문화 불가. 본 프롬프트는 이 결손을 정밀 직격.

---

## 프롬프트 본문

```
손금 4대 선(생명선·두뇌선·감정선·운명선) + 보조선 정량 분석을 MediaPipe
Hand Landmarker 21 키포인트 + 손금 선 세그멘테이션 기반 결정론 점수
엔진으로 구축하기 위한 학술 출처 + 알고리즘 명세를 조사·정리해주세요.

본 자료는 운세 SaaS 백엔드의 결정론 분류 엔진용이며, 손금 학파의 인과
해석(예: "생명선 짧으면 단명")은 채택 대상이 아닙니다. **형태 비율 +
학술 검증 가능 출처만 필요**합니다.

### 요구사항

#### 1. 학술 출처 라이브 검증

다음 영역 학술 출처:

(a) **손금 선 정량 측정 의학 논문**:
   - 손금(palmar crease) 형태와 발달 인류학 논문
   - 한국인 손금 인체측정학 KCI 등재 논문 (있다면)
   - Simian crease(다운증후군) 등 임상 의학 논문은 **인용하되 진단 용도 X**

(b) **MediaPipe Hand Landmarker 공식 출처**:
   - mediapipe.dev 또는 GitHub mediapipe/mediapipe 공식 문서
   - 21 키포인트 인덱스 매핑
   - 정확도·지연·재현성 데이터

(c) **손금 세그멘테이션 학술**:
   - U-Net·CFM·YOLO 손금 세그멘테이션 KCI/Pubmed 논문
   - 데이터셋 크기·라벨링 방법·mIoU 지표
   - **본 시스템 채택 X (결정론 정책 위반)** — 단 정량 측정 임계값 추출용

가짜 인용 절대 금지. 모든 출처는 라이브 검증 가능 URL/ISBN/DOI 의무.

#### 2. MediaPipe Hand Landmarker 21 키포인트 매핑

본 보고서는 다음 키포인트 매핑을 명시해야 함:

- 손목(0)·엄지(1-4)·검지(5-8)·중지(9-12)·약지(13-16)·소지(17-20)
- 각 키포인트의 3D 좌표 (x, y, z)
- 손금 4대 선이 통과하는 영역의 키포인트 조합

예시:
```yaml
palmar_lines:
  - line: "생명선"
    palmistry_traditional: "엄지 기저부에서 손목 방향 호"
    keypoint_region:
      bounded_by: [1, 2, 5, 0]  # 엄지·검지·손목 영역
      measurement: "arc_length / palm_width"
    
  - line: "두뇌선"
    palmistry_traditional: "검지 기저부에서 손바닥 가로 방향"
    keypoint_region:
      bounded_by: [5, 9, 13, 17]  # 손가락 기저 가로선
      measurement: "horizontal_extent / palm_width"
```

#### 3. 결정론 임계값 (face_scoring.py 패턴 적용)

face_scoring.py가 12궁 각 자리별로 0.0~1.0 점수 산출하듯,
손금 4대 선 + 보조선 각각에 대해:

- 측정 지표 (정량 함수)
- 한국인 평균·표준편차 (학술 출처 명시)
- 임계값 (0.0~0.3 / 0.3~0.6 / 0.6~1.0)
- **객관 라벨** ("두드러진 정도", "길이 비율" 등)
- 인과 해석 라벨링 절대 금지

예시:
```yaml
score_definition:
  line: "생명선"
  metric: "arc_length_normalized"
  formula: "lifeline_arc_length / palm_width"
  korean_baseline_mean: 0.X
  korean_baseline_std: 0.Y
  thresholds:
    low: "< mean - 1*std"      # 0.0~0.3
    medium: "mean ± 1*std"     # 0.3~0.6
    high: "> mean + 1*std"     # 0.6~1.0
  label: "생명선 호의 두드러짐 정도"
  forbidden_interpretation:
    - "생명선 짧음 = 단명 (인과 단정)"
    - "생명선 끊김 = 사고·질병 (예언)"
  academic_source: "<KCI URL: 한국인 손금 인체측정학 논문>"
```

#### 4. 좌우 손 교차 분석 (C1 직격)

본 보고서 §2.1 권장 "선천=비우세수 / 후천=우세수" 패러다임의:

(a) **학술 출처**: 좌우 손 형태 비대칭 학술 논문 (KCI/Pubmed)
   - 비우세수 vs 우세수 생물학적 차이 (있다면)
   - 손금 차이 정량 측정 표본

(b) **결정론 알고리즘**:
   - 좌우 손 키포인트 입력
   - 4대 선 점수 각각 산출
   - 좌우 차이(Δ) 계산
   - 객관 라벨 ("좌우 비대칭 정도")
   - **인과 해석 라벨링 절대 금지** ("선천 vs 후천" 단정 X)

(c) **본 시스템 학파 명시 정책**:
   - ADR-002 학파 회피 정신
   - "Samudrika Shastra 학설" 또는 "한국 전통 손금 관습" 객관 표시
   - 사용자 출력 면책 의무

#### 5. ADR-006 정합 + 사용자 출력 면책 가이드

다음 표현 절대 금지:
- ❌ "생명선이 짧아 수명 단축이 우려됩니다" (의료 단정 + 예언)
- ❌ "두뇌선 분기 = 지능 우수" (인과)
- ❌ "감정선 모양 = 연애운 X" (사적 영역 인과)
- ❌ "당신은 호르몬 노출이 많아 OOO한 성격입니다" (생물학 인과)

채택 가능:
- ✅ "본 측정 기준 생명선 호의 두드러짐 점수는 0.7입니다. 본 점수는
  한국인 평균 대비 상대 측정값이며, 수명·운명과 무관합니다."
- ✅ 학파 명시 ("Samudrika Shastra 학설")
- ✅ 면책 자동 포함 (palm_reading.py 페르소나 정합)

#### 6. 회귀 테스트 데이터셋

본 시스템 회귀 검증용 입력→출력 30쌍 이상:

```json
[
  {
    "id": "palm_001",
    "hand_side": "right",
    "keypoints_subset": {
      "kp0": [0.50, 0.95, 0.0],
      "kp1": [0.55, 0.85, 0.02],
      "...": "..."
    },
    "expected_scores": {
      "lifeline_arc": 0.72,
      "headline_horizontal": 0.55,
      "heartline_curve": 0.41,
      "fateline_vertical": 0.28
    },
    "expected_label": "생명선 두드러짐 / 운명선 흐릿",
    "forbidden_interpretation_check": true
  }
]
```

#### 7. 본 시스템 결손 영역 정밀 매핑

기존 모듈 정합 점검:
- ✅ engine/divination/palm_reading.py (351줄) — Gemini Vision LLM
- ❌ engine/divination/palm_scoring.py — 부재
- ✅ engine/divination/face_scoring.py (532줄) — 참조 패턴
- ❌ data/korean_palm_anthropometry.json — 부재

신규 모듈 후보:
- `engine/divination/palm_scoring.py` (face_scoring.py 패턴 차용)
- `data/korean_palm_anthropometry.json` (한국인 평균·표준편차)
- 회귀 30건
- palm_reading.py 통합 (LLM 페르소나가 결정론 점수 참조)

### 출력 형식

1. **학술 출처 표** (KCI/Pubmed/ISBN 라이브 검증)
2. **MediaPipe Hand 21 키포인트 매핑 표** (공식 인덱스·계산식·출처)
3. **결정론 점수 정의 YAML** (4대 선 + 보조선)
4. **좌우 손 교차 분석 알고리즘 명세**
5. **사용자 출력 면책 가이드라인**
6. **회귀 데이터셋 JSON** (30쌍 이상)
7. **본 시스템 모듈 명세** (palm_scoring.py 함수 시그니처)

### 검증 기준

본 보고서가 채택되려면:
- 모든 학술 인용 KCI/Pubmed/공식 출처 라이브 검증 가능
- MediaPipe Hand 21 키포인트 공식 문서 인용
- 가짜 인용 0건
- 인과 단정 표현 0건
- 회귀 30쌍 이상
- 한국인 평균·표준편차 학술 명시

위 조건 미충족 시 ADR-010 사실성 분리 + ADR-006 자문 거절에 따라
거부됩니다.
```

---

## 본 시스템 채택 절차 (보고서 수령 후)

1. `/squeeze-report` 사실성 분리 + KCI/Pubmed 라이브 검증
2. ACCEPT 후보:
   - 신규 ADR (손금 결정론 점수 정책, face_scoring.py 패턴 명시)
   - `engine/divination/palm_scoring.py` 신규 (palm_reading.py와 분리)
   - `data/korean_palm_anthropometry.json` 학술 데이터
   - 회귀 30건
   - vault/references/ 학술 출처 영속화

## 면책

- ADR-006 자문 거절 + ADR-010 사실성 분리 동시 적용
- 결정론 점수는 **객관 라벨**만 (인과·예언 절대 금지)
- palm_reading.py 옥선 할미 페르소나 정합 의무 (이미 차단된 표현 재진입 금지)
- 의료법 §27 (의료 자문 금지) 자동 회귀 검증
- MediaPipe Hand 한계 (조명·각도 영향) 면책 의무

## 본 프롬프트의 결정적 차별점

기존 손금 보고서가 "호 넓이·곡률" 모호 표현으로 본문화 불가했던 이유:
1. 결정론 임계값 학술 출처 부재
2. MediaPipe Hand 21 키포인트 매핑 명세 부재
3. 한국인 평균·표준편차 통계 부재
4. 회귀 검증 데이터셋 부재

본 프롬프트는 위 4가지를 **명시 요구사항**으로 채택 — 빈 약속 차단.

## 관련 참고

- 본 시스템 면책 패턴 참고: [face_scoring.py](../../engine/divination/face_scoring.py)
- 페르소나 정합 참고: [palm_reading.py](../../engine/divination/palm_reading.py)
- ADR-017 절차 적용 사례: [palm-reading-app.md](../reports/palm-reading-app.md)
