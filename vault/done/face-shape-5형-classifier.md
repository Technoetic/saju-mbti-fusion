---
type: done
status: applied
date: 2026-05-17
domain: [face]
adr: ADR-022-face-shape-classifier
related_report: reports/face-shape-classifier-research
related_reference: references/korean-face-anthropometry
related_prompt: templates/PROMPT_face-shape-classifier
---

# 5형 결정론 안면 형태 분류 본문화 — 목·화·토·금·수 + 복합형

## 작업 요약

PROMPT_face-shape-classifier.md 의뢰 → 보고서 수령 → /squeeze-report
ADR-017 절차 적용 → ACCEPT 1건 → ADR-022 본문화.

ADR-018 (face-golden-set-policy) DEFER 1건 (5형 분류 구현) **해소**.
ADR-017 절차 세 번째 본문화 사례.

## 변경 사항

### 신규 파일
- [engine/divination/face_shape.py](../../engine/divination/face_shape.py) — 5형 결정론 분류 모듈
  - `classify_face_shape()` 함수
  - `compute_face_metrics()` 메트릭 산출
  - `jaw_angle_from_points()` 3D 벡터 내적 각도
  - `FaceShapeResult` frozen dataclass
  - `SHAPE_KOREAN_TO_LATIN` + `SHAPE_LATIN_TO_KOREAN` 매핑
  - `DEFAULT_DISCLAIMERS` (ADR-006/010 정합)
  - `_REFERENCE_PAPERS` (KCI 학술 출처 URL)
- [engine/divination/test_face_shape.py](../../engine/divination/test_face_shape.py) — 회귀 18 PASS
- [vault/decisions/ADR-022-face-shape-classifier.md](../decisions/ADR-022-face-shape-classifier.md)
- [vault/references/korean-face-anthropometry.md](../references/korean-face-anthropometry.md)
- [vault/reports/face-shape-classifier-research.md](../reports/face-shape-classifier-research.md)

### 갱신
- vault/decisions/INDEX.md — ADR-022 추가
- vault/done/INDEX.md — 관상 도메인 행 추가

## 회귀 테스트 (18 PASS)

**메트릭 산출 (3건)**: compute_face_metrics + jaw_angle_from_points
**영문↔한글 매핑 (2건)**: SHAPE_KOREAN_TO_LATIN + SHAPE_LATIN_TO_KOREAN
**면책 (3건)**: DEFAULT_DISCLAIMERS 개수 + 인과 표현 0건 + 학파 회피 명시
**보고서 §4 회귀 10건**: case_001 (목 standard) ~ case_010 (복합형 fallback)
**메타데이터 (5건)**: 학술 출처 + matched_criteria + morphological_name + frozen + latin compat

## 5형 임계값 (보고서 §3 YAML)

| 한글 | 영문 | 임계값 |
|---|---|---|
| 목형 | long | fwhr<0.82 + 115≤jaw≤130 |
| 화형 | inverted_tri | bz/bg>1.25 + jaw>125 |
| 토형 | oval | fwhr≥0.88 + jaw≥115 |
| 금형 | square | fwhr≥0.85 + jaw<112 + bz/bg≤1.15 |
| 수형 | round | 0.83≤fwhr≤0.88 + jaw>120 + bz/bg≤1.20 |
| 복합형 | oval | fallback (임계값 교집합 외) |

## 학술 출처 (KCI 검증)

- 송우철 외 (2017) DBpia NODE07133895 — 목형·토형 FWHR
- 최윤경·이경희 (2009) DBpia NODE09916734 — 화형 광대/하악 비율
- 노상훈 외 (1998) JKAOMS — 금형 하악각
- POSTECH HFES (2012) — 수형 한국인 평균

## ADR-006/010 자동 회귀

`DEFAULT_DISCLAIMERS` 3건:
1. "본 결과는 객관 기하학적 형태 분류이며 길흉화복·운명·성격과 무관합니다." (ADR-006)
2. "한국인 안면 인체측정학 KCI 학술 출처 기반의 통계 비교입니다." (ADR-010)
3. "마의상법·유장상법 등 전통 관상학 인과 해석은 채택하지 않습니다." (ADR-002 학파 회피)

자동 회귀 검증:
- 인과·예언 표현 0건 (당신은 운이·운명입니다·예언·단명·흉화·길흉)
- 학파 회피 명시 (마의상법·전통 관상학·학파 키워드)
- morphological_name에 학파 용어 0건

## face_scoring.py 호환

face_shape.py 결과의 `latin` 필드는 face_scoring.py가 소비하는
영문 face_shape 5종 (round·square·oval·long·inverted_tri)과 호환:

```python
m = compute_face_metrics(...)
result = classify_face_shape(m)
# face_scoring.py metrics에 주입 가능
metrics["face_shape"] = result.latin
```

## 후속 작업 (별도 ADR)

- face_reading.py LLM 페르소나 통합 호출 (옵션)
- EU AI Act + 한국 PIPEA UI 고지문 (별도 ADR + 프론트엔드)
- 임계값 운영 데이터 보정 (post_traffic 10만 건+ 누적 후)
- 노인·아동 표본 추가 (별도 ADR)

## 메타

- ADR-017 절차 세 번째 본문화 사례 (ADR-020 L2 + ADR-021 B6 다음)
- ADR-018 DEFER 해소 (5형 분류 구현)
- 분석 에이전트 오추정 0건 (보강된 프롬프트 작동 입증)
- 보고서 §4 회귀 10건 → 18 tests PASS
- 본 노트 immutable
