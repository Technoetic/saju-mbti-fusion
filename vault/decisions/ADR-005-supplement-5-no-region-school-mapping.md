---
type: adr_supplement
parent_adr: ADR-005
status: accepted
date: 2026-05-17
domain: [face]
related: [ADR-004, ADR-005, ADR-010, ADR-022]
supersedes_partial: ADR-005-supplement-3-two-stage-pipeline (Stage 2 작성 형식 영역-학파명 매핑 예시 부분)
---

# ADR-005 Supplement 5 — Stage 2 프롬프트 영역-학파명 매핑 예시 제거

## 상태

Accepted (2026-05-17). Supplement 1·2·3·4 위에 마지막 잔재 한 줄 제거.

## 맥락

Supplement 4(Phase 19)로 Opus(Stage 1)에서 학파 용어를 완전 격리. 그러나 Gemini(Stage 2) 시스템 프롬프트 작성 형식 절에 잔재:

```
2) forehead — 이마 (결정론에 상정·관록궁 있으면 인용 가능)
3) eyebrow·eye·nose — 눈썹·눈·코 (결정론에 명궁·재백궁 등 있으면 인용 가능)
4) mouth·chin — 입·턱 (결정론에 하정·노복궁 등 있으면 인용 가능)
```

**문제**: 시스템 프롬프트가 Gemini에게 **"관록궁=이마, 명궁=눈썹/눈, 노복궁=턱" 학파 매핑을 직접 주입**. 엔진이 결정론으로 산출한 것이 아니라 코드 작성 시점에 추측으로 박힌 매핑. ADR-010 사실성 분리 정신 위반.

사용자 결정 (2026-05-17):

> "객관적 이미지 분석은 opus / 알고리즘, 엔진에 의한 결과에 대한 자연어 풀이는 gemini"

→ 학파 명칭의 영역 매핑은 **엔진 결정론 출력에서만** 흘러나와야 함. 시스템 프롬프트에 매핑 박힘 = 사용자 설계 위반.

## 결정

### Stage 2 시스템 프롬프트 작성 형식 절 단순화

**이전 (Supplement 3·4)**:
```
2) forehead — 이마 (결정론에 상정·관록궁 있으면 인용 가능)
3) eyebrow·eye·nose — 눈썹·눈·코 (결정론에 명궁·재백궁 등 있으면 인용 가능)
4) mouth·chin — 입·턱 (결정론에 하정·노복궁 등 있으면 인용 가능)
```

**이후 (Supplement 5)**:
```
2) forehead — 이마
3) eyebrow·eye·nose — 눈썹·눈·코
4) mouth·chin — 입·턱
```

+ 별도 규칙 줄 추가:
```
deterministic_scores에 있는 명칭·점수는 적절한 부위 단락에 자연스럽게 인용
(어느 부위에 어느 명칭이 해당하는지는 본 시스템이 명시하지 않음 — 입력 2의
라벨을 그대로 인용하되, 라벨 뒤에 새 매핑 추가 금지)
```

### 정보 흐름 (최종)

```
사진 ─→ Opus 4.7 Vision ─→ 해부학 JSON (학파 명칭 0%)
                            │
                            ▼
MediaPipe ─→ ADR-004/022 ─→ 결정론 점수 (학파 명칭 100% 코드 출처)
                            │
                            ▼
                       Gemini Flash Lite
                       (두 입력 받음, 사진 미열람,
                        영역-학파 매핑은 결정론 라벨 그대로만 인용)
                            │
                            ▼
                       운학 도사 자연어 풀이
```

→ **사용자 원하는 설계 100% 일치**: Opus = 사진 분석, 엔진 = 결정론, Gemini = 자연어 풀이.

## 회귀

`engine/divination/test_face_reading.py` 신규 2건:

- `test_stage2_system_omits_region_to_school_name_mapping` — 6개 영역-학파명 매핑 패턴 부재 검증
- `test_stage2_system_still_allows_deterministic_label_citation` — 결정론 라벨 인용 정책 유지 검증

회귀 13/13 PASS (Phase 19 11건 + Phase 20 2건).

## 한계

- **Gemini가 라벨을 부적절한 단락에 인용할 가능성**: 시스템 프롬프트가 매핑을 안 주니 Gemini가 자체 추정으로 매핑할 수 있음. 운영 모니터링 의무
- **Gemini 사전학습 자체 매핑 가능성**: 시스템 프롬프트가 가르치지 않아도 Gemini가 사전학습으로 "관록궁=이마" 매핑할 수 있음. 시스템 프롬프트의 "사전학습으로 끌어오지 말 것" 명시는 유지
- 본 ADR은 **immutable**

## 관련

- ADR 본문: `vault/decisions/ADR-005-claude-opus-vision.md`
- Supplement 1·2·3·4: 동일 디렉토리
- 회귀: `engine/divination/test_face_reading.py:1700~1760`
- 변경 모듈: `engine/divination/face_reading.py` (`_STAGE2_PERSONA_SYSTEM` 작성 형식 절)
