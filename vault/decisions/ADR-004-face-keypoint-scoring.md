---
type: adr
adr_number: 4
status: accepted
date: 2026-05-16
authors: [Technoetic]
domain: [face]
related: [done/face-phase1-keypoint-scoring]
---

# ADR-004: 관상은 키포인트 기반 결정론 점수표 + LLM 작문

## 배경

사용자 의견: "관상은 시스템 프롬프트가 아니라 키포인트로 분석해야 하는 것 아니냐"
- LLM 단독 풀이는 재현성 X
- 같은 사진 두 번 → 미세하게 다른 풀이
- 정량 데이터 없음 → 프론트 시각화 불가

## 검토한 옵션

### Phase 1 (채택)
- 키포인트 → 12궁 점수표 결정론 산출
- 응답 envelope에 palace_scores 노출
- LLM 자유도 보존 — 강제 X

### Phase 2 (운영 데이터 후)
- palace_scores를 LLM 시스템 프롬프트에 참고 주입

### Phase 3 (Phase 2 후)
- response_fact_check가 점수와 명백 모순 시 폴백

## 채택

**Phase 1만 우선**. 위험 최소화 + 재현성·시각화 우선 확보.

## 결과

- `face_scoring.py` 신규 — LLM 무관
- `face_reading.py`에 metrics 파라미터 + palace_scores envelope
- 합성 얼굴 5장 검증 (균형/비대칭/표정/길상/흉상)

## 면책

- AI 합성 얼굴은 실제 관상학 시각 특징을 완전 재현 못함
- palace_scores는 정량 데이터일 뿐 — "흉상" 평가 X
- Phase 2/3 진행은 운영 데이터 누적 후 ADR 별도 작성
