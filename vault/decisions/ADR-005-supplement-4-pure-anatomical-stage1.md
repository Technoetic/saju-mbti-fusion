---
type: adr_supplement
parent_adr: ADR-005
status: accepted
date: 2026-05-17
domain: [face]
related: [ADR-004, ADR-005, ADR-010, ADR-022]
supersedes_partial: ADR-005-supplement-3-two-stage-pipeline (Stage 1이 학파 용어 명칭/결정론 점수 수신하던 부분)
---

# ADR-005 Supplement 4 — Stage 1 순수 해부학 명칭 (학파 용어·결정론 점수 격리)

## 상태

Accepted (2026-05-17). ADR-005 본문 + Supplement 1·2·3 위에 **Stage 1 Opus를 순수 해부학 묘사 전문가로 격리**.

## 맥락

Supplement 3(Phase 18)의 2단계 파이프라인은 **Stage 1 JSON 스키마 자체에 학파 용어가 잔재**:

- `sangjeong_forehead`, `jungjeong_eyebrow_eye_nose`, `hajeong_mouth_chin` — 삼정(三停) 학파 영역 명칭
- `deterministic_scores_cited` 필드에 12궁·5형 명칭 수신
- Stage 1 user_text에 결정론 점수("관록궁 0.82·토형") 명시 주입

→ Opus가 "관록궁이 어느 영역인지·토형이 무엇인지"를 **사전학습 마의상법 통설로 알게 됨**. Opus 출력이 자연어가 아닌 JSON이라도 사전학습 매핑이 영역 정의에 이미 묻어있음.

사용자 검증 후 결정 (2026-05-17):

> "Opus는 객관적인 형태만 파악하는 것이다."

→ Opus는 **해부학 명칭(이마·눈·코·턱·뺨·광대뼈)으로만** JSON 묘사. 학파 명칭은 본 시스템 결정론 코드(MediaPipe + ADR-004/022)에서만 흘러나옴.

## 결정

### Stage 1 JSON 스키마 재설계 — 순수 해부학

```json
{
  "face_outline": {"shape", "width_height_balance", "left_right_symmetry"},
  "forehead": {"width", "shape", "wrinkles"},
  "eyebrow": {"thickness", "length", "shape"},
  "eye": {"size", "shape", "gaze_intensity", "clarity"},
  "nose": {"bridge", "nostril_wing", "tip"},
  "mouth": {"thickness", "corner"},
  "chin": {"shape", "fullness"},
  "cheek_zygomatic": {"prominence", "fullness"},
  "complexion": {"tone", "color_cast"},
  "distinctive_feature": "...",
  "photo_quality_note": "..."
}
```

→ **11개 영역 모두 해부학 명칭**. 삼정·12궁·5형 필드 전면 제거.

### Stage 1 입력에서 결정론 점수 제거

`_build_stage1_user_text` 시그니처:

| 이전 | 이후 |
|---|---|
| `(age, gender, question, palace_scores, face_shape)` | `(age, gender, question)` |
| 결정론 점수 영문 라벨로 주입 | 결정론 점수 미주입 |
| 학파 명칭("관록궁·토형") 전달 | 학파 명칭 미전달 |

→ Opus는 **사진 + 최소 사용자 컨텍스트(나이·성별·질문)만 받음**.

### Stage 1 시스템 프롬프트 학파 금지 명시

신규 금지 절(line 128 부근):

```
Forbidden physiognomy school vocabulary (do NOT use anywhere):
삼정, 상정, 중정, 하정, 12궁, 십이궁, 명궁, 관록궁, 재백궁, 전택궁,
처첩궁, 자녀궁, 복덕궁, 형제궁, 부모궁, 노복궁, 천이궁, 질액궁,
인당, 준두, 5형, 오행 (in face context), 목형, 화형, 토형, 금형, 수형,
마의상법, 신상전편, 달마상법, 운학.
```

→ **30+ 학파 용어 직접 명시 금지**.

### Stage 2가 결정론 점수 수신

신규 함수 `_build_deterministic_scores_summary(palace_scores, face_shape)` — 12궁·5형·삼정·오관·신기 점수를 한국어 라벨로 요약. Stage 2 사용자 메시지에 **입력 1(해부학 JSON) + 입력 2(결정론 점수)** 두 가지 명시 분리.

Stage 2 시스템 프롬프트 신규 절:

```
[12궁·5형·삼정 명칭 사용 규칙 — 결정론 출처만]
• 12궁/삼정/5형 명칭은 deterministic_scores에 있는 라벨만 사용.
  JSON에 없는 명칭은 절대 새로 만들거나 사전학습으로 끌어오지 말 것.
```

→ Gemini도 마의상법 사전학습이 있으나, **본 시스템에서 흘러나오는 결정론 출처에서만 명칭 사용 가능**. 사전학습 인입 명시 차단.

### 응답 dict 신규 필드

| 필드 | 출처 | 의미 |
|---|---|---|
| `anatomical_description` | Opus Stage 1 | 순수 해부학 묘사 JSON |
| `deterministic_scores_summary` | 본 시스템 결정론 코드 | Stage 2가 받은 학파 명칭+점수 |
| `palace_scores`·`face_shape` | ADR-004/022 (기존) | 결정론 전체 산출물 |

→ 사용자가 "어디서 어느 명칭이 왔는지" 응답 dict에서 직접 추적 가능 (ADR-010 검증 가능성 정밀 적용).

## 정보 흐름 다이어그램

```
사용자 사진 (image_b64)
       │
       ├─→ MediaPipe 키포인트 → ADR-004 face_scoring → palace_scores (12궁·삼정·오관)
       │                     → ADR-022 face_shape → face_shape_dict (5형)
       │                          │
       │                          ▼
       │                  _build_deterministic_scores_summary
       │                          │
       │                          ▼
       │                  deterministic_scores (학파 명칭 + 점수)
       │
       │                                          ┌─────────────────────┐
       └─→ Stage 1 Opus 4.7 Vision               │ Stage 2 Gemini 2.5   │
                ↓                                 │ Flash Lite           │
          (해부학 JSON만)                          │ (사진 미열람)         │
          anatomical_description ─────────────┬──→│ 입력 1: 해부학 JSON  │
                                              │   │ 입력 2: 학파 명칭+점수│
          deterministic_scores ───────────────┴──→│                      │
                                                  │ 출력: 운학 도사 풀이  │
                                                  └─────────────────────┘
                                                            │
                                                            ▼
                                                       사용자 응답
```

→ **학파 명칭은 결정론 코드 경로에서만 흐름**. Opus는 해부학 명칭만.

## ADR-010 사실성 분리 정밀 적용

| 등급 | 본 supplement 적용 |
|---|---|
| 🟢 팩트 | 해부학 부위·형태·색상 (Stage 1 Opus 측정) + 비율·대칭·5형 분류 (MediaPipe 결정론) |
| 🟡 구조 | 학파 명칭(12궁·5형·삼정)은 결정론 출처에서만 인용 — Opus는 미관여 |
| 🔴 도그마 | 학파 의미 매핑(관운·재물복·성격) — 모든 stage에서 어휘 금지 |

→ 의미 객관성은 본 시스템이 보장 X(사용자 자율 해석 영역)이나, **위치 객관성은 100% 결정론 출처**로 추적 가능.

## Supplement 3(Phase 18)과의 관계

- Supplement 3의 2단계 파이프라인 골격은 **유지**
- Supplement 3의 Stage 1 학파 명칭 JSON 스키마는 **본 supplement가 supersede**
- Supplement 3의 `objective_json` 응답 필드는 `anatomical_description`으로 명칭 변경 + `deterministic_scores_summary` 신규 분리

## 회귀

`engine/divination/test_face_reading.py` 신규 11건 (Phase 19, Supplement 3 9건 supersede):

- `test_stage1_system_forbids_physiognomy_school_terms` — 30+ 학파 용어 명시 금지 검증
- `test_stage1_system_defines_anatomical_schema_fields` — 11개 해부학 필드 검증
- `test_stage1_system_forbids_school_field_names` — 스키마에서 sangjeong·jungjeong·hajeong 필드 부재 검증
- `test_stage2_persona_system_enforces_school_term_from_deterministic_only` — 사전학습 인입 차단 검증
- `test_build_stage1_user_text_omits_persona_and_deterministic_scores` — Opus 입력에 학파 명칭·결정론 점수 미주입 검증
- `test_stage1_call_parses_anatomical_json` — 해부학 JSON 파싱
- `test_stage1_call_strips_code_fence` — 코드 펜스 제거
- `test_build_deterministic_scores_summary_collects_school_labels` — 결정론 점수 수집 함수
- `test_render_persona_template_uses_anatomical_schema` — 폴백 템플릿 해부학 스키마 사용 + 결정론 명칭 인용
- `test_generate_face_reading_emits_anatomical_description_and_scores` — 응답 dict 신규 필드 검증
- `test_stage2_persona_fallback_to_template_when_both_llm_fail` — LLM 실패 시 결정론 폴백

회귀 11/11 PASS (`PYTEST_RUN_ALL=1`, 2026-05-17).

## 한계

- **Opus 해부학 시각 어휘도 사전학습 의존**: "또렷한·맑은·짙은·곧은" 형용사 자체는 모델 사전학습 한국어 어휘. 정량 측정이 아님. 시스템 프롬프트가 어휘 풀을 명시했으나 형용사 선택은 모델 자율
- **Gemini 사전학습 학파 매핑 잔재 가능**: 시스템 프롬프트가 "결정론 출처만 사용" 명시하나 100% 보장 X. 운영 모니터링 의무
- **해부학 명칭 ↔ 학파 명칭 매핑은 Stage 2가 수행**: Stage 2가 "이마(상정)·코끝(준두)" 같이 매핑할 가능성. 결정론 점수 라벨 인용 외 매핑은 시스템 프롬프트로 금지
- **응답 dict 크기 증가**: `anatomical_description` + `deterministic_scores_summary` + `palace_scores` + `face_shape` 4개 구조화 필드 노출. UI는 무시 가능, API 응답 크기는 증가
- 본 ADR은 **immutable**. 추후 정책 변경 시 새 supplement

## 관련

- ADR 본문: `vault/decisions/ADR-005-claude-opus-vision.md`
- Supplement 1: `vault/decisions/ADR-005-supplement-multimodal-4-signal.md`
- Supplement 2: `vault/decisions/ADR-005-supplement-2-objective-vision-only.md`
- Supplement 3: `vault/decisions/ADR-005-supplement-3-two-stage-pipeline.md`
- 회귀: `engine/divination/test_face_reading.py:1497~1800`
- 변경 모듈: `engine/divination/face_reading.py`
- 정합 ADR: ADR-004 (face_scoring), ADR-010 (사실성 분리), ADR-022 (face_shape)
