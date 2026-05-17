---
type: adr_supplement
parent_adr: ADR-005
status: accepted
date: 2026-05-17
domain: [face]
related: [ADR-004, ADR-005, ADR-010, ADR-022]
---

# ADR-005 Supplement 6 — 길상·흉상 실측 테스트로 발견된 5개 문제 + 보너스 PNG MIME 버그 해결

## 상태

Accepted (2026-05-17). Supplement 1·2·3·4·5 위에 실측 테스트 결과 적용.

## 맥락

`google/gemini-2.5-flash-image`로 생성한 "길상" 통설 사진과 "흉상" 통설 사진 두 장을 Phase 19+20 적용 후 파이프라인 통과시킨 결과 4개 문제 + 보너스 버그 1개 발견:

1. **폴백 점수 인용**: `metrics=None`일 때 face_scoring이 모든 점수를 0.5로 폴백. Stage 2 본문에 "0.5라는 동일한 점수로 조화롭게" 인용됨.
2. **0.5 일색 긍정 해석**: "균형 잡힌·고른 기운" 같은 긍정 해석이 폴백 점수에서 유래.
3. **영문 key 노출**: 본문에 `top_palace`·`(myeong)`·`(bumo)`·`shen 0.5, qi 0.5` 그대로 노출.
4. **안전 거절구 오발동**: 정상 사진의 마무리에 "빛 좋은 곳에서 정면으로..." 거절구 삽입.
5. **라벨 변조**: face_scoring 라벨 `보수관(눈썹)`을 Stage 2가 `보수관(귀)`로 사전학습 매핑 변조.
6. **(보너스 버그)** **PNG MIME 오감지**: `_normalize_image_b64`가 raw base64일 때 무조건 `image/jpeg`로 처리 → PNG 이미지가 Anthropic Vision API에 400 BadRequest. Stage 1 전체 실패하고 폴백 빈 dict 사용.

## 결정

### 문제 1·6 해결 — 폴백 점수 차단 + MIME 자동 감지

`generate_face_reading`에서 `metrics=None`이면 `palace_scores=None` 처리. `score_face` 호출 자체를 건너뛰어 폴백 0.5 dict 생성 방지.

신규 함수 `_detect_image_mime(raw_b64)` — base64 매직 넘버로 PNG/JPEG/GIF/WebP 자동 식별. `_normalize_image_b64`가 raw base64일 때 자동 감지 사용.

### 문제 2 해결 — Stage 2 프롬프트 0.5 폴백 인용 금지 절 추가

```
[점수 의미론 — 0.5 폴백 인용 금지]
• 0.5 일색은 폴백 기본값 신호 — 실 측정이 아님. 입력 2에 점수가 모두
  0.5 또는 매우 균일한 경우, 점수 수치 자체를 본문에 인용하지 말 것.
  '점수가 균형 잡혔다'·'고른 기운'·'동일한 점수로 조화롭게' 같은 해석 X.
```

### 문제 3·5 해결 — Stage 2 프롬프트 라벨 변조·영문 key 노출 금지

```
[12궁·5형·삼정 명칭 사용 규칙 — 결정론 출처만 + 라벨 그대로 인용]
• 라벨 변조 절대 금지: deterministic_scores의 라벨 문자열을 토씨 하나
  바꾸지 말고 그대로 인용. 예: 라벨이 '보수관(눈썹)'이면 그대로 사용.
  '보수관(귀)'·'보수관'·'눈썹관' 같이 변조 X.
• 영문 key 노출 절대 금지: 본문에 'top_palace'·'weakest_palace'·'shen'·
  'qi'·'(myeong)'·'(bumo)' 같은 영문 식별자를 절대 노출 X.
```

`_build_deterministic_scores_summary`도 `palace_scores.palaces` 룩업으로 영문 key를 한국어 라벨로 변환해 Stage 2 입력에 영문 식별자 자체가 없게 처리.

### 문제 4 해결 — 일반 마무리 vs 안전 거절구 명확 분리

```
[마무리 형식 vs 안전 거절구 — 명확히 구분]
• 일반 마무리 (식별 불가 단어 없음): "이 늙은이의 한 마디 — " 뒤에
  photo_quality_note 내용 + 면책. 안전 거절구 사용 X.
• 안전 거절구 (식별 불가·재촬영·흉림 단어 포함 시에만): 거절구 한 줄.
• 혼동 금지: 일반 마무리에 거절구를 절대 섞지 말 것.
```

## 회귀

신규 6건 (PASS 6/6, 누적 Phase 19+20+21 19건 PASS):

- `test_generate_face_reading_returns_empty_summary_when_metrics_none`
- `test_stage2_system_forbids_fallback_score_citation`
- `test_stage2_system_forbids_english_key_exposure`
- `test_stage2_system_separates_normal_ending_from_safety_refusal`
- `test_build_deterministic_scores_summary_maps_english_keys_to_korean_labels`
- `test_detect_image_mime_distinguishes_png_jpeg`

## 실측 재테스트 결과

`google/gemini-2.5-flash-image`로 생성한 길상·흉상 두 사진을 Phase 21 적용 후 통과:

| 검증 항목 | 길상 | 흉상 |
|---|---|---|
| 운명 어휘 미주입 | ✅ | ✅ |
| 점수 인용 0건 (폴백 차단) | ✅ | ✅ |
| 영문 key 본문 0건 | ✅ | ✅ |
| 라벨 변조 0건 | ✅ | ✅ |
| 일반 마무리 정상 (거절구 부재) | ✅ | ✅ |
| Stage 1 Opus 정상 작동 (PNG MIME 자동 감지) | ✅ | ✅ |
| 객관 해부학 묘사 흐름 (윤곽·이마·눈썹·눈·코·입·턱·뺨·기색) | ✅ | ✅ |
| 글자 수 (가이드라인 800~1300) | 879 | 1057 |

## 한계

- **MIME 감지는 매직 넘버만**: 잘못된 확장자·손상된 헤더는 여전히 오감지 가능. L1 file_integrity의 magic 검증과 중복이나 안전망 역할
- **Stage 2 라벨 변조 차단은 프롬프트 의존**: Gemini 사전학습으로 우회할 가능성. 100% 보장 X
- **0.5 폴백 차단도 프롬프트 의존**: Gemini가 다른 우회 표현으로 0.5를 인용할 가능성 (예: "균등한 결"). 운영 모니터링 의무
- 본 ADR은 **immutable**

## 관련

- ADR 본문: `vault/decisions/ADR-005-claude-opus-vision.md`
- Supplement 1·2·3·4·5: 동일 디렉토리
- 회귀: `engine/divination/test_face_reading.py:1700~1850`
- 변경 모듈: `engine/divination/face_reading.py`
- 테스트 샘플: `step_archive/face_test_samples/`
