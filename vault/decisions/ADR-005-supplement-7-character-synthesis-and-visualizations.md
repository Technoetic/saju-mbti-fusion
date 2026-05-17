---
type: adr_supplement
parent_adr: ADR-005
status: accepted
date: 2026-05-17
domain: [face]
related: [ADR-004, ADR-005, ADR-010, ADR-022]
---

# ADR-005 Supplement 7 — Phase 22 종합 인상 캐릭터화 단락 + 객관 분석 시각화 6종

## 상태

Accepted (2026-05-17). Supplement 1·2·3·4·5·6 위에 사용자 체감 개선 2가지 추가.

## 맥락

Phase 21까지 운명 매핑·학파 통설·사전학습 잔재를 모두 차단했으나 사용자 피드백:

1. **풀이가 형태 나열에 그침** — "이마는 넓고 평평하며·눈은 또렷하며" 식 부위 묘사. 사용자가 "결국 어떤 인상의 사람인지" 못 얻음.
2. **마무리가 사진 메타 정보** — "정면·조명 양호한 사진으로 잘 살펴보았네"는 풀이가 아닌 photo_quality_note 그대로 노출.
3. **UI에 시각화 부재** — 응답 dict에 palace_scores·face_shape·anatomical_description 풍부하나 UI는 text 본문만 노출.

## 결정

### Phase 22b — Stage 2 프롬프트 캐릭터화 + 마무리 수정

**작성 형식**에 신규 6번 단락 추가:

```
6) 종합 인상(캐릭터화) — 윤곽·부위·기색의 시각적 종합이 주는 일반적
   첫인상을 한 단락으로 풀어낸다. 예: "단정한·온화한·또렷한·따뜻한·
   차분한·강단 있어 보이는·부드러운·서글서글한·기품 있어 보이는".
   필수 단락 — 생략 X.
```

**종합 인상 어조 규칙** 신규 절:

- 시각 형태가 주는 **일반적 첫인상**만 묘사 (사회 통념)
- 단정 어조 금지: "~한 사람이다·~할 것이다·~의 운이 있다" X
- 인상 어조 사용: "~한 인상이 느껴지는구먼·~한 분위기를 풍기는다·~한 결이 비치는구먼"
- 학파 운명·성격 단정 X

**마무리 한 줄** 재정의:

- 운학 도사의 종합 소감 (캐릭터 한마디)
- photo_quality_note 그대로 옮기지 말 것 — "정면·조명 양호한 사진" 등 메타 잔재 노출 금지
- 면책 문구 노출 금지 (시스템이 자동 부착)
- 예 ✓: "이 늙은이의 한 마디 — 단정하고 따뜻한 결이 그대 안에 머무는구먼."
- 예 ✗: "이 늙은이의 한 마디 — 정면·조명 양호한 사진으로 잘 살펴보았네."

### Phase 22a — front 객관 분석 시각화 6종

응답 dict의 결정론 데이터를 사극 톤 UI로 시각화. 백엔드 변경 0, front만:

| ID | 시각화 | 데이터 출처 | 구현 |
|---|---|---|---|
| A | 12궁 가로 막대 차트 (top/weak 강조) | `palace_scores.palaces` | CSS 막대 |
| B | 삼정 도넛 (상정·중정·하정 비율) | `palace_scores.samjeong` | CSS conic-gradient |
| C | 오관 5각 레이더 | `palace_scores.ogwan` | SVG polygon |
| D | 오행 5형 배지 (목·화·토·금·수 한자) | `face_shape.shape_type` | CSS 배지 |
| E | 신(神)·기(氣) 게이지 | `palace_scores.shen_score·qi_score` | CSS 가로 막대 |
| F | 해부학 묘사 카드 표 | `anatomical_description` 9개 부위 | HTML table |

신규 헬퍼: `renderFaceShapeBadge`·`renderSamjeongDonut`·`renderOgwanRadar`·`renderShenQi`·`renderPalaceBars`·`renderAnatomicalTable`·`renderVisualizations`.

`renderResult` 함수 본문 위에 `${vizBlock}` 삽입 — 본문 위에 객관 시각화 노출 후 운학 도사 자연어 풀이.

## ADR-010 사실성 분리 정합

| 위험 | 본 Supplement 처리 |
|---|---|
| "단정·온화·강단" 같은 형용사가 인상학적 운명 단정? | ❌ 시각 형태 → 일반 첫인상 (사회 통념). 학파 운명 매핑 X. 단정 어조도 금지 |
| 시각화가 사용자에게 점수 단정으로 인식? | ⚠️ 점수 = 측정 결과 명시. 의미 해석은 운학 도사 본문에서만 |
| 5형 배지가 학파 운명 매핑 강조? | ⚪ 분류명 + 형태학적 명칭만 노출. 의미 매핑 X |

## 회귀

신규 2건 (PASS 2/2, 누적 Phase 19+20+21+22b 21건 PASS):

- `test_stage2_system_requires_character_synthesis_paragraph`
- `test_stage2_system_forbids_photo_meta_in_final_line`

## 실측 재테스트

길상·흉상 사진(`google/gemini-2.5-flash-image` 생성) 재통과:

| 항목 | 길상 | 흉상 |
|---|---|---|
| 종합 인상 단락 출현 | ✅ "단정하면서도 온화한 분위기" | ✅ "단정하면서도 온화한 기품, 서글서글하면서도 믿음직한 인상" |
| 마무리 캐릭터화 | ⚠️ 부분 ("정면·조명 양호" 부분 잔재) | ✅ "단정하고 온화한 결을 지녔으니 편안함을 느끼게 하는 인상" |
| 운명 어휘 부재 | ✅ | ✅ |

길상 마무리 잔재는 LLM 우회 표현 — 시스템 프롬프트로 100% 보장 X. 추후 출력 후처리 필터 또는 추가 강화로 보완 가능.

## 한계

- **시각화는 metrics 의존**: 클라이언트(브라우저) MediaPipe가 metrics를 전달해야 palace_scores·face_shape 산출. metrics 미주입 시 빈 시각화 (Phase 21에서 폴백 0.5 차단됨)
- **캐릭터화 어조 단정 우회**: "단정한 인상·따뜻한 분위기"는 인상학적 평가 잔재. 100% 중립 묘사가 아닌 일반 사회 통념의 첫인상. 사용자 결정 (Phase 22 결정) — UX 가치 우선
- **마무리 photo_meta 잔재**: 시스템 프롬프트로 명시 금지 + 잘못된 예시 명시했으나 LLM이 부분 우회 가능. 운영 모니터링 의무
- **SVG/CSS 폴리필 미고려**: 구 브라우저는 conic-gradient·SVG polygon 미지원 가능. 모바일 주력 사용자라 영향 작음
- 본 ADR은 **immutable**

## 관련

- ADR 본문: `vault/decisions/ADR-005-claude-opus-vision.md`
- Supplement 1·2·3·4·5·6: 동일 디렉토리
- 회귀: `engine/divination/test_face_reading.py:1804~1830`
- 변경 모듈:
  - `engine/divination/face_reading.py` (Stage 2 프롬프트 캐릭터화 + 마무리)
  - `front/index.html` (CSS 시각화 6종 + JS 헬퍼 + renderResult 확장)
