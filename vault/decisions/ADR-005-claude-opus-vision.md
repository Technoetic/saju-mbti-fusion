---
type: adr
adr_number: 5
status: accepted
date: 2026-05-16
authors: [Technoetic]
domain: [face]
related: [done/face-phase1-keypoint-scoring]
---

# ADR-005: 관상 vision 모델은 claude-opus-4.7 (Bizrouter primary)

## 배경

관상은 vision-language 모델의 시각 분석 + 한국어 사극풍 작문 두 능력 필요.
이전 default `google/gemini-2.5-flash-lite`는 가성비 모델 — 미세 디테일 약함.

## 검토한 옵션

| 모델 | 시각 디테일 | 한국어·페르소나 | 비용 |
|---|---|---|---|
| gemini-2.5-flash-lite | ⚠️ | ✅ (프롬프트 강제) | 최저 |
| gemini-2.5-pro | ✅ | 🟡 | 중간 |
| claude-opus-4.7 (채택) | ✅ | ✅✅ | 최상위 |

## 채택

**claude-opus-4.7 + Bizrouter 경유**:
- Bizrouter dot notation: `anthropic/claude-opus-4.7`
- Anthropic SDK 직접: `claude-opus-4-7` (fallback)

## 구현

`_call_vision()` try/except 패턴:
1. Bizrouter primary 호출
2. timeout·5xx·권한 오류 시 Anthropic SDK 직접 fallback
3. 두 경로 모두 같은 모델 — 회복력 확보

## 결과

- 환경변수 `BIZROUTER_VISION_MODEL=anthropic/claude-opus-4.7` 라이브 설정
- 라이브 1×1 PNG → "Yellow." 응답 정상
- 합성 얼굴 5장 검증 통과

## 비용

- gemini-flash-lite 대비 약 50배 ~ 100배
- 단, response_fact_check / persona_self_eval 폴백률 감소로 일부 상쇄

## 면책

- 모델 가용성은 Bizrouter·Anthropic 정책에 종속
- 두 경로 모두 실패 시 → llm_fallback_router의 deterministic stub 응답
