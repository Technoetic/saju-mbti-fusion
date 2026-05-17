---
type: prompt_template
target: deepresearch
purpose: 부위별 형상(복코·매부리코·초승달 눈썹·앙월구·삼백안·칼귀 등) MediaPipe 키포인트 기반 결정론 분류 임계값 학술 출처 조사
created: 2026-05-17
related_module: engine/divination/facial_feature_classifier.py (신규, face_shape.py 확장 패턴)
related_adr:
  - ADR-004 (face_scoring 결정론)
  - ADR-010 (사실성 분리)
  - ADR-022 (face_shape 5형 분류 — 본 PROMPT는 부위 단위 확장)
priority: high
status: draft
related_report: ../reports/facial-feature-classification-research (예정)
deepresearch_input: PROMPT_facial-feature-classification.deepresearch.txt
post_traffic: false
---

# 부위별 형상 결정론 분류 — 키포인트 임계값 학술 출처 조사

## 사용법

ADR-022로 얼굴 윤곽 5형(목·화·토·금·수) 결정론 분류는 완료. 본 PROMPT는
**부위 단위 확장**:
- 코: 복코·매부리코·들창코·마늘코 등 → MediaPipe 478 키포인트 비율 임계값
- 눈썹: 초승달·일자·끊긴 눈썹 → 곡률·길이·짙기 임계값
- 눈: 단봉안·삼백안·도화안 등 → 흰자 비율·눈매 각도 임계값
- 입: 앙월구·복주구 → 입꼬리 각도 임계값
- 입술: 두께·색깔 분류 → 픽셀 분석 임계값
- 귀: 칼귀·후귀 → 귓볼 비율 임계값

결정론으로 산출한 부위별 형상 분류를 Stage 2(Gemini)가 코드 DB 인용
형태로 사용 (PROMPT_physiognomy-knowledge-db와 페어 정합).

딥리서치 입력본은 페어 `PROMPT_facial-feature-classification.deepresearch.txt` 참조.

## 결손 영역 표

| 부위 | 현재 상태 | 결손 |
|---|---|---|
| 코 형태 분류 | 부재 | 복코·매부리코·들창코·마늘코 5종+ |
| 눈썹 형태 분류 | 부재 | 초승달·일자·청수·끊김 5종+ |
| 눈 형태 분류 (13가지 안상 포함) | 부재 | 단봉안·삼백안·봉안·용안·도화안 등 |
| 입꼬리 분류 | 부재 | 앙월구·복주구·일자 3종+ |
| 입술 두께/색깔 분류 | 부재 | 두께·색감 임계값 |
| 귀 형태 분류 | 부재 | 칼귀·후귀·송곳귀 5종+ |

ADR-022 패턴 적용 (인체측정학 KCI 출처 + 결정론 임계값 + 형태 분류
결과만 사용, 운명 매핑 X — Stage 2 단계에서 코드 DB 인용으로 처리).

## 본 시스템 채택 절차

1. 딥리서치 결과를 `vault/reports/facial-feature-classification-research.md` 저장
2. `/squeeze-report` 호출 — KCI·DBpia 라이브 URL 검증 + 임계값 정량성 검증
3. Phase B Haiku 검증 — MediaPipe 478 키포인트 인덱스 정합 + 임계값 출처 검증
4. ACCEPT 항목만 `engine/divination/facial_feature_classifier.py` 신규 모듈로 영속화:
   - `classify_nose_shape(metrics) -> str` (복코 / 매부리코 / 들창코 / ...)
   - `classify_eyebrow_shape(metrics) -> str`
   - `classify_eye_shape(metrics) -> str`
   - `classify_mouth_corner(metrics) -> str`
   - `classify_ear_shape(metrics) -> str` (귀 키포인트 부재 시 LOW_CONFIDENCE)
5. 회귀 N건 + ADR-022 supplement 또는 ADR-005 Supplement 9 영속화

## 면책

- ADR-010 사실성 분리 — 분류는 객관 기하학, 운명 매핑은 별도 DB(PROMPT_physiognomy-knowledge-db) 인용
- ADR-022 정합 — 5형 윤곽 분류와 별개로 부위 단위 분류
- 임계값은 인체측정학 KCI 출처 우선, 학파 통설은 분류 명칭만 차용
- 사용자 출력 자동 면책 (운명·길흉 무관 명시)
