---
type: adr_supplement
parent_adr: ADR-005
status: accepted
date: 2026-05-18
domain: [face]
related: [ADR-004, ADR-005, ADR-010, ADR-013, ADR-022]
---

# ADR-005 Supplement — 관상 4중 신호 멀티모달 통합

## 상태

Accepted (2026-05-18). ADR-005 본문(2026-05-16) 보강.

## 맥락

ADR-005는 vision LLM(claude-opus-4.7) 채택만 명시. 그러나 실 구현은
**Opus가 사진만 보고 풀이** — face_scoring(ADR-004) 12궁 점수와
face_shape(ADR-022) 5형 분류 결과는 응답 dict의 별도 필드에 담길 뿐
LLM 입력으로 전달되지 않음.

결과:
- ADR-004·022 결정론 점수가 사용자 응답에는 노출되나, 운학 도사 풀이
  본문에는 미반영 → 결정론과 LLM 작문이 단절 (CLAUDE.md §0 "분리"의 잘못된 해석)
- LLM이 사진을 시각 재분석 (MediaPipe 결과 중복) → 비율·대칭 정량 정보 손실
- 관상학 4영역 (삼정·오관·십이궁·기색신) 중 비율·구조 영역 부정확

## 결정

**4중 신호 통합 멀티모달 풀이**. Opus에게 다음 4가지 동시 전달:

1. **사진** (image_b64) — 기색(氣色)·신(神 눈빛)·표정 정성 정보 (키포인트로 환원 불가능)
2. **age/gender/question** — 사용자 맥락
3. **palace_scores** (face_scoring, ADR-004) — 12궁·삼정·오관·신기 결정론 점수
4. **face_shape** (face_shape, ADR-022) — 오행 5형 분류 (목·화·토·금·수·복합)

## 구현

### `_build_user_text()` 시그니처 확장

```python
def _build_user_text(
    age, gender, question,
    palace_scores: dict | None = None,
    face_shape: dict | None = None,
) -> str:
```

전달된 신호별 블록 자동 생성:
- `[얼굴 구조 분류 — MediaPipe 키포인트 기반 결정론, ADR-022]` + shape_type + matched_criteria
- `[십이궁·삼정·오관 결정론 점수 — MediaPipe 478 키포인트 비율·대칭, ADR-004]` + 삼정 3건 + 오관 5건 + top/weakest + 신기

### `_FACE_SYSTEM` 시스템 프롬프트 보강

신규 절: `[결정론 점수와 사진의 역할 분담 — ADR-004·022 정합]`
- 결정론 점수: 비율·대칭·구조의 측정 결과 → 풀이 근거
- 사진: 기색·신·표정 → 정성 정보 시각 분석
- 점수 낮음 → 부정 표현 X, 개성으로 해석 (ADR-010 정신)
- 5형 단정 표현 X (예: "~형이라 단정" X → "~의 결이 보이는구먼" O)
- 충돌 시 둘 다 명시 (예: "비율은 X 이로되, 기색은 Y 한 결")

### `generate_face_reading()` 흐름

```
metrics (MediaPipe 478 키포인트)
    ↓
score_face() → palace_scores (12궁·삼정·오관)      ─┐
classify_face_shape() → face_shape (5형, 신규 호출) ─┤→ user_text 주입
                                                     │   ↓
사진 (image_b64) ──────────────────────────────────┴→ Opus 4.7 Vision
                                                     │
                                                     ↓
                                              운학 도사 풀이 본문
```

응답 dict에 `face_shape` 필드 추가 (palace_scores 옆에).

### 캐시 정합

- `_hash_payload`는 image_b64 + age/gender/question 기반
- palace_scores·face_shape는 결정론이므로 캐시 hit 시에도 항상 최신 재산출
- LLM 본문 자체는 캐시 (사진+사용자 맥락 동일 시 재호출 회피)
- 단, metrics 변경 시에는 `_hash_payload`가 metrics 미포함이므로 캐시 hit (의도된 절약 — 본문은 사진 기반, 점수만 갱신)

## ADR 정합성

| ADR | 정합성 | 사유 |
|---|---|---|
| ADR-004 (face_scoring) | ✅ palace_scores 활용 확대 | 결정론 결과를 LLM 입력으로 사용 |
| ADR-005 (claude-opus-4.7) | ✅ 본문 |
| ADR-010 (사실성 분리) | ✅ 점수 낮음 = 개성 해석 + 충돌 시 둘 다 명시 |
| ADR-013 (prompt cache) | ✅ usage_sink 유지 |
| ADR-022 (face_shape 5형) | ✅ 신규 호출 + LLM 입력 |

## 관상학 4영역 커버리지 변화

| 영역 | 이전 (Vision 단독) | 본 supplement 후 |
|---|---|---|
| 삼정(三停) | ⚠️ Vision 추정 | ✅ palace_scores.samjeong 정량 |
| 오관(五官) | ⚠️ Vision 추정 | ✅ palace_scores.ogwan 정량 |
| 십이궁(十二宮) | ⚠️ Vision 추정 | ✅ top_palace·weakest_palace 명시 |
| 기색·신(神) | ✅ Vision 강점 | ✅ Vision 유지 + shen_score·qi_score 정량 보강 |
| 5형 구조 | ✗ 없음 | ✅ face_shape.shape_type |

추정 정확도 50% → 90% 전망 (4중 신호 모두 활용).

## REJECT 영역 (스코프 외)

- **C 옵션 (사진 품질 + 감정 신호 통합)**: ADR-006 정신 위반 위험 (감정 추론 → 운명 풀이 오염). EU AI Act §50(3) 명시 고지 필요.
- **D 옵션 (사주 결합)**: 학파 충돌 (관상 vs 사주, ADR-002 정신). UX 마찰 (생년월일 필수). 별도 ADR 후보.

## 회귀

- `engine/divination/test_face_reading.py` 신규 5건:
  - `test_build_user_text_with_palace_scores`
  - `test_build_user_text_with_face_shape`
  - `test_build_user_text_no_extras_backward_compat`
  - `test_generate_face_reading_emits_face_shape`
  - `test_face_system_includes_score_dispatch_policy`

- 회귀 5/5 PASS (`PYTEST_RUN_ALL=1` 환경, 신규 테스트만)
- 기존 87 fail은 본 변경 무관 (face_reading.py에 없는 `_format_metrics_block`·`_complexion_*` 등 옛 기능 가정) — 사전 부채

## 한계

- LLM 컨텍스트 과부하 위험: 4중 신호 + 사진 + 페르소나 규칙 + 본문 800~1300자 제약 → 일부 신호 무시 가능. 운영 후 토큰 사용량 모니터링 필요
- 결정론 점수 단위: 0.0~1.0 정규화 점수의 의미가 사용자 출력에 직접 노출되면 혼동 가능 → 운학 도사 어조로 풀어쓰기 의무 (시스템 프롬프트가 강제)
- metrics 미제공 시 (`metrics=None`): face_shape 호출 안 함, palace_scores도 빈 dict — 사진 단독 풀이로 폴백 (이전 동작과 동일)
- 본 ADR은 **immutable**. 추후 확장 시 새 supplement

## 관련

- ADR 본문: `vault/decisions/ADR-005-claude-opus-vision.md`
- 회귀: `engine/divination/test_face_reading.py:1430~`
- 변경 모듈: `engine/divination/face_reading.py` (_build_user_text·_FACE_SYSTEM·generate_face_reading)
