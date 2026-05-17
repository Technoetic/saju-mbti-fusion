---
type: adr_supplement
parent_adr: ADR-005
status: accepted
date: 2026-05-17
domain: [face]
related: [ADR-005, ADR-010, ADR-013, ADR-022]
supersedes_partial: ADR-005-supplement-2-objective-vision-only (Opus가 페르소나 어조 직접 수행하던 부분)
---

# ADR-005 Supplement 3 — 2단계 파이프라인 (Opus 객관 JSON + Gemini 사극 어조)

## 상태

Accepted (2026-05-17). ADR-005 본문(2026-05-16) + Supplement 1(Phase 12 4중 신호) + Supplement 2(Phase 17 시각 객관 묘사 한정) 위에 **모델 책임 분리**를 추가.

## 맥락

Supplement 2(Phase 17)는 시스템 프롬프트에 "시각 객관 묘사만" 강제. 그러나 정직 검증 결과:

- Opus가 사극 어조와 객관 묘사를 **동일 호출에서 동시 수행** → 어조 변환 중 사전학습 운명 매핑 잔재가 자연어에 섞일 가능성
- "또렷한·맑은·개성·결" 같은 평가 형용사가 시스템 프롬프트 자체에 잔재
- 운학 도사 캐릭터 = 연기 행위 → 순수 객관 묘사가 아닌 페르소나 출력
- 출력이 자연어 본문이라 골든셋 검증·재현·중간 산출물 감사 불가

사용자 결정 (2026-05-17):

> "Opus가 객관 묘사만 전달하고 운학 도사 대사는 gemini 2.5 flash lite가 하면?"

**역할 분리**: Opus = 객관 측정 전문가, Gemini = 어조 변환기.

## 결정

**2단계 직렬 파이프라인**:

```
사진 + age/gender/question + palace_scores + face_shape
       ↓
┌─────────────────────────────────────────────┐
│ Stage 1 — Opus 4.7 Vision                   │
│ 모델: anthropic/claude-opus-4.7 (Bizrouter) │
│ 출력: 구조화 JSON (객관 묘사만)             │
│ 페르소나 X · 사극 어조 X · 운명 매핑 X     │
│ 시스템 프롬프트: 영문, 엄격 JSON 스키마     │
└─────────────────────────────────────────────┘
       ↓ (objective_json)
┌─────────────────────────────────────────────┐
│ Stage 2 — Gemini 2.5 Flash Lite             │
│ 모델: google/gemini-2.5-flash-lite (Bizrouter)│
│ 사진 미열람 (JSON만 입력)                   │
│ 출력: 운학 도사 사극 어조 자연어 본문       │
│ 새 시각 사실 추가 X · 운명 매핑 X          │
└─────────────────────────────────────────────┘
       ↓
사용자 응답: {text: 본문, objective_json: 중간 JSON, ...}
```

### Stage 1 JSON 스키마

```json
{
  "overall_impression": {"shape": "...", "balance": "...", "complexion": "..."},
  "sangjeong_forehead": {"width": "...", "shape": "...", "wrinkles": "..."},
  "jungjeong_eyebrow_eye_nose": {"eyebrow": "...", "eye": "...", "nose": "..."},
  "hajeong_mouth_chin": {"mouth": "...", "chin": "..."},
  "distinctive_feature": "...",
  "deterministic_scores_cited": {
    "top_palace": "...", "weakest_palace": "...",
    "face_shape": "...", "shen_qi": "..."
  },
  "photo_quality_note": "..."
}
```

**핵심 설계 원리**: 운명 매핑할 필드가 구조적으로 존재하지 않음 → 표면 키워드 회피로도 운명 매핑 출력 불가.

### Stage 2 핵심 제약

- **사진 미열람**: image_b64 미전달. JSON만 입력 → Gemini가 자체 시각 묘사 추가 불가
- "JSON에 없는 새 시각 사실 절대 추가 금지" 시스템 프롬프트 명시
- 운명 매핑 어휘 7개 카테고리 금지 (Supplement 2와 동일)
- 운학 도사 페르소나 어조는 Stage 2에서만 수행

### 폴백 사슬

| 실패 단계 | 동작 |
|---|---|
| Stage 1 (Bizrouter Opus) | Anthropic SDK 직접 Opus 호출 (기존 `_call_vision` 폴백 유지) |
| Stage 1 모두 실패 | 결정론 점수만으로 최소 JSON 합성 + `photo_quality_note: "Stage 1 실패"` |
| Stage 2 (Bizrouter Gemini) | Anthropic SDK Opus가 페르소나 변환 (사진 없이 텍스트만) |
| Stage 2 모두 실패 | `_render_persona_template` 결정론 한국어 템플릿 (JSON 사실만 인용) |

→ 어떤 단계 실패에도 사용자에게 응답 보장. JSON 사실 외 운명 매핑은 어떤 폴백 경로에서도 미주입.

## 구현

### 신규 모듈 (`engine/divination/face_reading.py`)

- `_STAGE1_OBJECTIVE_SYSTEM` — Opus용 영문 JSON 스키마 시스템 프롬프트 (운명 어휘 + 페르소나 어휘 모두 금지)
- `_STAGE2_PERSONA_SYSTEM` — Gemini용 한국어 사극 어조 변환 시스템 프롬프트 (새 시각 사실 추가 금지)
- `_build_stage1_user_text` — Stage 1 사용자 메시지 (영문, 결정론 점수 인용)
- `_call_stage1_objective` — Stage 1 호출 + JSON 파싱 + 코드 펜스 제거
- `_call_stage2_persona` — Stage 2 호출 (Gemini 우선 → Opus 폴백 → 템플릿 폴백)
- `_render_persona_template` — LLM 두 단계 모두 실패 시 결정론 한국어 폴백

### `generate_face_reading` 흐름 재설계

```python
# Stage 1: 객관 JSON
objective_json = _call_stage1_objective(stage1_user, image_b64)

# Stage 2: 사극 어조 (사진 미전달)
reading_text = _call_stage2_persona(objective_json, age, gender, question)

# 응답
out = {
    "text": reading_text + legal,
    "objective_json": objective_json,  # Phase 18 — 검증 가능성
    "palace_scores": ..., "face_shape": ...,
}
```

### 응답 dict 변경

신규 필드: `objective_json` — Stage 1 출력 JSON 그대로. 사용자가 운학 도사 본문과 객관 묘사를 분리해서 검증 가능 (ADR-010 검증 가능성 정신).

### 환경 변수

- `BIZROUTER_VISION_MODEL` (기본 `anthropic/claude-opus-4.7`) — Stage 1
- `BIZROUTER_PERSONA_MODEL` (기본 `google/gemini-2.5-flash-lite`) — Stage 2 (신규)

## ADR-010 사실성 분리 정밀 적용

| 등급 | Stage 1 (Opus) | Stage 2 (Gemini) |
|---|---|---|
| 🟢 팩트 | 형태·색상·비율·대칭 시각 측정 | Stage 1 JSON 사실 인용만 |
| 🟡 구조 | 5형·12궁·삼정 영역 명칭 | 영역명을 사극 어조로 풀어 전달 |
| 🔴 도그마 | 운명 매핑 필드 부재 (구조적 차단) | 운명 어휘 금지 + 새 사실 금지 (이중 차단) |

## Supplement 2 (Phase 17)와의 관계

- Supplement 2의 `_FACE_SYSTEM`·`_build_user_text`는 **사용처가 사라짐** (deprecated, 코드에는 유지하되 호출 없음)
- 두 함수의 회귀(`test_face_system_*`·`test_build_user_text_*` Phase 17 4건)는 **유지** — 함수 자체가 사라진 것이 아니라 호출 경로만 우회된 것
- Supplement 2의 정책(시각 객관 묘사 한정·운명 매핑 금지)은 **Stage 1·2 모두에 분산 적용** — Stage 1은 구조적 차단, Stage 2는 어휘 금지

## 비용·지연

| 항목 | 이전 | 본 Supplement 후 |
|---|---|---|
| LLM 호출 횟수 | 1 (Opus vision) | 2 (Opus vision + Gemini text) |
| 사진 전송 | 1회 | 1회 (Stage 1만) |
| 토큰 비용 | Opus 입력+출력 1세트 | Opus 1세트 + Gemini 1세트 (Flash Lite 저렴) |
| 예상 지연 증가 | — | ~500ms~1s (Gemini Flash Lite는 빠름) |

→ 비용·지연 소폭 증가 vs 객관성 강제 + 검증 가능성 + 사전학습 잔재 차단의 가치.

## 회귀

`engine/divination/test_face_reading.py` 신규 9건 (Phase 18):

- `test_stage1_system_forbids_persona_and_fate_words`
- `test_stage1_system_defines_json_schema_fields`
- `test_stage2_persona_system_enforces_no_new_facts`
- `test_build_stage1_user_text_omits_persona`
- `test_stage1_call_parses_json_response`
- `test_stage1_call_strips_code_fence`
- `test_stage2_render_template_fallback_uses_only_json_facts`
- `test_generate_face_reading_emits_objective_json`
- `test_stage2_persona_fallback_to_template_when_both_llm_fail`

회귀 9/9 PASS (`PYTEST_RUN_ALL=1`, 2026-05-17).

기존 89 pre-existing fail(`_format_metrics_block`·`classify_metric_issue` 부재 함수 + Phase 17이 일부 12궁 명칭을 제거)은 본 변경 무관 — 사전 부채.

## 한계

- **Gemini도 사전학습 운명 매핑 보유 가능**: 마의상법 등을 학습했을 가능성. 시스템 프롬프트로 명시 금지하나 100% 차단 보장 X → 운영 모니터링 의무
- **JSON 스키마 위반 위험**: Opus가 가끔 형식을 어김 → `json.JSONDecodeError` 시 결정론 점수 단독 폴백
- **Stage 1·2 직렬 호출**: 지연 증가. 병렬 호출 불가 (Stage 2가 Stage 1 결과 의존)
- **Stage 1 영문 시스템 프롬프트**: Korean 시각 형용사를 영문 지시로 강제하는 위험. 운영 시 출력 샘플로 한국어 일관성 점검
- **objective_json 노출의 UX 부담**: 응답 dict가 커짐. UI는 무시 가능하나 API 응답 크기 증가
- 본 ADR은 **immutable**. 추후 정책 변경 시 새 supplement

## 관련

- ADR 본문: `vault/decisions/ADR-005-claude-opus-vision.md`
- Supplement 1: `vault/decisions/ADR-005-supplement-multimodal-4-signal.md` (4중 신호)
- Supplement 2: `vault/decisions/ADR-005-supplement-2-objective-vision-only.md` (시각 객관 한정)
- 회귀: `engine/divination/test_face_reading.py:1497~1700`
- 변경 모듈: `engine/divination/face_reading.py`
- 정합 ADR: ADR-010 (사실성 분리), ADR-013 (prompt cache telemetry), ADR-022 (face_shape)
