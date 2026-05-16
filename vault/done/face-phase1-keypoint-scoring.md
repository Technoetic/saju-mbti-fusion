---
type: done
date: 2026-05-16
phase: face
domain: [face]
related_adr: [decisions/ADR-004-face-keypoint-scoring, decisions/ADR-005-claude-opus-vision]
commits: [005e0f8, 94638a5]
tests_added: 26
loc_added: 450
---

# 관상 Phase 1 — 키포인트 기반 12궁 결정론 점수표

## 무엇

face_reading.py에 LLM 자유도 보존 + 결정론 점수표를 분리해 추가.
vision 모델을 claude-opus-4.7로 업그레이드.

## 왜

사용자 의견: "시스템 프롬프트가 아니라 키 포인트로 분석해야 하는 것 아니냐"
- 같은 사진 두 번 → 다른 풀이 (재현성 부족)
- LLM 환각으로 점수와 모순된 풀이 가능
- 정량 데이터 노출 X → 프론트 시각화 불가

## 어떻게

### `face_scoring.py` 신규 (LLM 무관)
- MediaPipe 메트릭 → 12궁·삼정·오관 정량 점수 (0.0~1.0)
- top_palace / weakest_palace / overall_balance / shen_score / qi_score
- `report_to_dict()` JSON 직렬화

### `face_reading.py` 수정
- `generate_face_reading(metrics=...)` 파라미터 추가
- envelope에 `palace_scores` 키 노출 (4 분기 모두)
- `_call_vision()` try/except fallback:
  - Primary: Bizrouter `anthropic/claude-opus-4.7`
  - Fallback: Anthropic SDK 직접 `claude-opus-4-7`

### vision 모델
- 이전: `google/gemini-2.5-flash-lite` (가성비 모델)
- 변경: `anthropic/claude-opus-4.7` via Bizrouter
- 환경변수 `BIZROUTER_VISION_MODEL` Railway에 설정

## 검증

### 합성 얼굴 테스트 (pipeline-viz/test-faces/)
- Gemini 2.5 Flash Image로 균형/비대칭/표정 3장 생성
- 관상학 문헌 어휘 기반 길상/흉상 2장 추가 생성
- claude-opus-4.7이 사진 차이를 미묘하게 인식 (운학 도사 페르소나 유지)
- palace_scores도 합리적으로 차이 (jeontaek Δ=0.82 등)

### 라이브
- 1×1 PNG → "Yellow." 응답 정상
- 응답 envelope에 palace_scores 키 정상 노출

## 면책·한계

- AI 합성 얼굴은 진짜 흉상의 시각 특징을 완전 재현 못함 (한계 인정)
- palace_scores는 정량 데이터, 길흉 평가어 X
- LLM은 점수표 받지만 강제 X — Phase 2에서 결정

## 다음 단계 (Phase 2/3)

- Phase 2: palace_scores를 LLM 시스템 프롬프트에 참고 주입 (운영 데이터 본 후)
- Phase 3: response_fact_check가 점수와 명백 모순 시 폴백
