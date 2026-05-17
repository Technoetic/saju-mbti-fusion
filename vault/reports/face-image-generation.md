---
type: external_report
status: received_with_caveats
date: 2026-05-17
source: deepresearch
domain: face
applied_to: []
neo4j_synced: false
factuality: mostly_verified
related:
  - decisions/ADR-005-claude-opus-vision.md
  - decisions/ADR-010-name-sibling-factuality.md
original_file: ../../관상 앱 이미지 생성 AI 설계.md
---

# 관상 앱 길상·흉상 이미지 생성 (Gemini 2.5 Flash Image) — 사실성 검토

## 보고서 요약

Gemini 2.5 Flash Image (코드명 Nano Banana)를 활용한 길상·흉상 얼굴 합성. LangGraph 다중 에이전트 오케스트레이션 + 관상학 삼정 매핑 + 해부학적 묘사 프롬프트 엔지니어링.

## 🟢 팩트

| 주장 | 검증 |
|---|---|
| Gemini 2.5 Flash Image 모델 실존 | ✅ Google 공식 (Nano Banana 코드명도 사실) |
| 32K 토큰 컨텍스트 / 7MB 입력 / 1024 해상도 | ✅ 공식 사양 |
| SynthID 워터마크 | ✅ Google 정책 |
| RLHF로 인한 미화 편향 | ✅ 알려진 현상 |
| LangGraph 프레임워크 | ✅ 실존 |
| 관상학 삼정(三停) 개념 | ✅ 전통 관상학 사실 |

## 🟡 구조

- "추상 명령 → 해부학 묘사 변환" 패턴은 합리적
- 다중 에이전트 (프롬프트 빌더 → 생성기 → 검증기) 분리
- Temperature 0.7 고정 권장은 일반적 가이드

## 🔴 도그마 / 부정확

| 항목 | 판정 |
|---|---|
| "흉상 = 재물이 새어나가는" 같은 인과 표현 | 🔴 관상 도그마 — 본 프로젝트 ADR-006·010 위반 가능 |
| "1000 토큰 초과 시 지시 순응도 급격 저하" 구체 수치 | 출처 없음 |
| "단일 이미지 1290 토큰 = $0.039" | 가격 직접 검증 필요 |

## 본 프로젝트 적용 가치

### 활용 시나리오

본 프로젝트 [engine/divination/face_reading.py](../../engine/divination/face_reading.py) + [engine/divination/test_golden_set.py](../../engine/divination/test_golden_set.py) — **골든셋 테스트 이미지 생성**에 활용 가능.

현재 `pipeline-viz/test-faces/` 디렉토리에 합성 얼굴 검증용 이미지 존재 ([[../done/face-phase1-keypoint-scoring]] 참조). Gemini Flash Image를 활용한 길상·흉상 합성은 다음 시나리오에서 가치:

1. **회귀 테스트 골든셋 확장** — 다양한 얼굴 유형 자동 생성
2. **face_scoring.py 임계값 보정** — 합성 흉상으로 메트릭 분포 측정

### 위험

- **사용자 노출 시 위험**: "이 얼굴이 흉상입니다" 같은 직접 비교는 외모 차별·EU AI Act §50(3) 감정 추론 명시 고지 위반 가능
- **내부 테스트만 허용**: 합성 이미지를 사용자에게 보여주는 기능은 도입 금지

## 본 시스템 반영

### 🟡 채택 가능 (내부 테스트 한정)

1. **Gemini Flash Image API 도입 평가** — 골든셋 합성 이미지 생성용
2. **새 ADR 필요**: "관상 테스트 골든셋 합성 — 내부 한정, 사용자 노출 금지" 정책
3. **비용 평가**: 골든셋 100장 × $0.039 = $3.9 (1회성 비용)

### ❌ 사용자 노출 미적용

- 사용자에게 "당신과 비교한 흉상" 같은 출력 금지
- "재물 새는 얼굴" 같은 도그마 표현 사용 금지

## 신뢰성 평가

| 항목 | 평가 |
|---|---|
| Gemini API 사양 | ✅ 정확 |
| 프롬프트 엔지니어링 권장 | ✅ 합리적 |
| 관상 도그마 표현 | 🔴 사용자 출력 금지 |
| 본 프로젝트 적합성 | 🟡 내부 테스트 한정 가치 있음 |

## 다음 액션

- [ ] (선택) ADR 후보: "관상 테스트 골든셋 합성 정책" — 도입 결정 시 작성
- [ ] (선택) Gemini Flash Image vs 기존 합성 방식 비용 비교
- [x] (확정) 사용자 노출 시 흉상/길상 직접 비교 금지 정책

## 딥리서치 프롬프트 (방향 전환됨)

본 보고서 원안(흉상/길상 합성)은 ADR-006·010 위반이라 거부.
대신 본 프로젝트 실제 결핍(face_shape×메트릭 분포 골든셋)에 맞춘 정밀 프롬프트:

→ [[../templates/PROMPT_face-golden-set-synthesis]]

본 프롬프트는 즉시 실행이 합리적이지 않음 — SaaS 운영 후 실제 사용자
메트릭 분포 데이터로 골든셋 부족이 실측된 후 실행 권장.

## 출처

- 본 보고서 원본: `사주/관상 앱 이미지 생성 AI 설계.md`

## 메타

- 영속화: 2026-05-17 (ADR-010 사실성 분리)
- ADR-010 사례 8호
- 본 노트 immutable
