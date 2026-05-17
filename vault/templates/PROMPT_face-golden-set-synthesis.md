---
type: prompt_template
target: deepresearch
purpose: 관상 골든셋 합성 이미지 — 객관 묘사 한정 (보고서 원안 도그마 회피)
created: 2026-05-17
related_roadmap: null
related_reports: reports/face-image-generation.md
related_adr:
  - ADR-004-face-keypoint-scoring (face_scoring.py 결정론 12궁 점수)
  - ADR-005-claude-opus-vision (vision LLM 정책)
  - ADR-006-legaltech-rejected (자문 거절 — 외모 평가 금지)
  - ADR-010-name-sibling-factuality (사실성 분리 원칙)
---

# 딥리서치 프롬프트 — 관상 골든셋 합성 이미지

## 본 프롬프트의 방향 결정 (중요)

원본 보고서(`관상 앱 이미지 생성 AI 설계.md`)는 "길상·흉상" 합성을 권장.
**본 SaaS는 ADR-006/010에 따라 사용자에게 흉상/길상 직접 비교 금지**.

따라서 본 프롬프트는 보고서 권장을 그대로 채택하지 않고, 본 프로젝트의
실제 결핍 영역에 맞춰 **객관 묘사 한정 골든셋 합성**으로 방향 전환:

| 보고서 원안 | 본 프롬프트 방향 |
|---|---|
| 흉상·길상 합성 | face_shape·메트릭 분포 합성 |
| 사용자 노출용 | 내부 회귀 테스트만 |
| 인과 예언 ("재물 새는") | 해부학 객관 묘사 |

본 합성 이미지는 face_scoring.py 결정론 점수 회귀 테스트 + MediaPipe
메트릭 추출 정확도 검증에만 사용. 사용자 노출 영구 금지.

## 사용법

본 프롬프트를 그대로 ChatGPT Deep Research / Claude Research / Gemini
Deep Research에 입력. 결과 받으면 `vault/reports/` 영속화 + ADR-010
검증 후 ADR 작성 + 골든셋 통합.

---

## 프롬프트 본문

```
한국 관상 분석 SaaS의 백엔드 회귀 테스트용 골든셋 합성 이미지 사양을
조사·정리해주세요. 본 작업은 사용자 노출용이 아닌 내부 테스트 한정입니다.

## 본 시스템 컨텍스트

본 SaaS는 다음을 이미 구현:
- MediaPipe Face Landmarker (클라이언트 측 478 키포인트 추출)
- engine/divination/face_scoring.py (12궁 결정론 점수)
- engine/divination/face_reading.py (claude-opus-4.7 vision 풀이)
- engine/divination/test_golden_set.py G01~G21 (메트릭 입력 회귀)

다음 영구 정책 (변경 불가):
- 사용자에게 "흉상/길상" 직접 비교·평가 금지
- 외모 평가·미추 비교 출력 금지
- "재물·수명·운명" 인과 예언 금지
- 페르소나(운학 도사) 출력은 "결" "기운" 같은 경향성 표현만

## 요구사항

### 1. 합성 이미지 사양 (해부학 객관 묘사만)

5가지 face_shape × 3가지 메트릭 변형 = 15개 합성 사양:

face_shape 5종:
- round (둥근 얼굴: 가로·세로 비율 ~1.0)
- square (각진 얼굴: 광대·턱선 강조)
- oval (계란형: 가로·세로 비율 ~0.75)
- long (긴 얼굴: 가로·세로 비율 ~0.6)
- inverted_tri (역삼각: 이마 광대 > 턱)

메트릭 변형 3종:
- balanced (대칭·표준 비율)
- asymmetric (좌우 비대칭 — MediaPipe 비대칭 메트릭 검증용)
- expressive (표정 변화 — 입꼬리·눈웃음 메트릭 검증용)

각 합성 이미지에 대해:
- 해부학 묘사 (이마 너비/광대 돌출/턱선 각도 등 측정 가능 수치)
- 합성 도구 + 프롬프트 텍스트 (Gemini Flash Image / FLUX.1 / SDXL 등)
- 기대되는 MediaPipe 메트릭 값 (face_landmarker 478 키포인트 중 핵심 5개)

### 2. 합성 도구 비교

다음 모델의 트레이드오프를 비교:
- Gemini 2.5 Flash Image (Google 공식, SynthID 워터마크)
- FLUX.1-dev / FLUX.1-schnell (오픈소스, 로컬 실행)
- SDXL (Stable Diffusion XL, 오픈소스)

비교 기준:
- 가격 (이미지당 USD)
- 정밀 제어 (해부학적 비율 제어 가능 여부)
- RLHF 미화 편향 정도 (사실적 비대칭 얼굴 생성 가능?)
- 워터마크·라이선스 (상용 사용 가능?)

### 3. 거부할 내용 (절대 미포함)

- "이 얼굴은 길상이다 / 흉상이다" 평가 표현
- "재물·수명·인덕" 같은 운명론 표현
- "이마가 좋으면 부귀하다" 같은 인과 주장
- 특정 인종·민족 일반화
- 미추 비교

본 합성은 **face_scoring.py 메트릭 분포 보강 + 비대칭 메트릭 검증**용
입니다. 외모 평가가 아닌 해부학 분포 확인용임을 보고서 본문에서 반복
명시하세요.

### 4. 회귀 테스트 통합 데이터

각 합성 이미지를 G22~G36 ID로 추가할 수 있는 형식:

```json
[
  {
    "id": "G22_synth_round_balanced",
    "image_b64": "<base64 encoded synthetic image>",
    "expected_metrics": {
      "face_shape": "round",
      "asymmetry_score": 0.05,
      "three_thirds": [33, 34, 33]
    },
    "expected_palace_scores_range": {
      "myeong": [0.4, 0.7]
    },
    "purpose": "round face + 대칭 메트릭 추출 정확도 검증"
  },
  ...
]
```

### 5. 사실성 분리 (ADR-010 의무)

- 모델 사양 출처 (Google 공식 docs URL · GitHub URL — 마스킹 금지)
- 가격 검증 시점 (가격 변동성 큼)
- "정밀 제어 가능" 같은 주장은 실측 예시 첨부

### 6. 출력 형식

마크다운 보고서 + JSON 데이터:
1. 합성 도구 비교 표 (마크다운)
2. 15개 합성 사양 (마크다운 + 해부학 묘사)
3. 회귀 테스트 통합 JSON (실제 base64 또는 생성 절차)
4. 본 시스템 적용 시 면책 요구 사항
5. 출처 (모두 검증 가능한 URL)

## 절대 조건

- 인과 예언·외모 평가 표현 0건
- "골든셋 회귀 테스트 한정" 라벨 보고서 본문에 명시
- 사용자 노출 금지 정책 (ADR-006 인용) 보고서 본문에 명시
```

---

## 결과물 처리 절차

1. 결과 .md를 `사주/[보고서 제목].md`로 저장
2. `vault/reports/[주제].md`에 ADR-010 사실성 분리 적용 영속화
3. ADR 신규 — "관상 골든셋 합성 이미지 도입 — 내부 테스트 한정"
4. `engine/divination/test_golden_set.py`에 G22~G36 추가
5. 합성 이미지는 `step_archive/golden_synth/` 또는 별도 디렉토리 (.gitignore 결정 필요)
6. 사용자 노출 경로(face_reading.py 응답)에 합성 이미지 절대 미노출 검증 회귀

## 우선순위 평가

본 프롬프트 실행은 **현 시점 미합리** 가능성 — 이유:

1. 현 골든셋 G01~G21 + face_shape 5종 모두 커버 → 결핍 사례 없음
2. 합성 이미지가 실제 사용자 사진 분포를 대표하는지 검증 불가
3. MediaPipe가 합성 이미지에서 메트릭 추출 정확도 별도 검증 필요

→ **SaaS 운영 후 실제 사용자 메트릭 분포 데이터로 골든셋 부족 사례
실측된 후** 본 프롬프트 실행 권장. 현 시점은 본 프롬프트를 영속화만
하고 즉시 실행은 보류.
