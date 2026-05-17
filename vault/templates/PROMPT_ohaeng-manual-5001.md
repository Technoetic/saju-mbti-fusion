---
type: prompt_template
target: deepresearch
purpose: §4 자원오행 5001자 매핑 입력
created: 2026-05-17
related_roadmap: roadmap/ohaeng-manual-5001.md
related_adr:
  - ADR-003-unihan-fallback (현 8525자 풀, 부수 자동 매핑 3524자 = 41%)
  - ADR-010-name-sibling-factuality (사실성 분리 원칙)
---

# 딥리서치 프롬프트 — §4 자원오행 5001자 매핑

## 사용법

본 프롬프트를 그대로 딥리서치 도구에 입력. 결과 받으면 `vault/reports/`
영속화 + ADR-010 검증 후 `data/korean_hanja_unihan.json`의
`resource_ohaeng` 필드 갱신.

---

## 프롬프트 본문

```
한국 작명 SaaS의 자원오행(字源五行) 매핑 데이터를 다음 요구사항에 맞춰
조사·정리해주세요.

## 컨텍스트

본 SaaS는 인명용 한자 8525자(Unicode Unihan 기반)를 풀로 보유.
이 중 부수(Radical) 기반 자동 매핑된 3524자(41%)는 자원오행이 채워졌으나,
추상 부수·복합 부수 한자 5001자는 미매핑.

데이터 형식:
```json
{
  "char": "樹",
  "kangxi_strokes": 16,
  "radical": "木",
  "resource_ohaeng": "木"
}
```

미매핑 한자 예: 仁(亻) / 知(矢) / 信(亻) / 美(羊) 등

## 요구사항

### 1. 매핑 원칙 (학파 단일 채택)
자원오행은 학파별 미세 차이 있음. 본 SaaS는 1개 학파만 채택:
- 옵션 A: 부수 기반 결정론 매핑 (亻=火/亠=水 등 기계적)
- 옵션 B: 자의(字義) 기반 매핑 (의미 → 오행)
- 옵션 C: 한자별 직접 매핑 (학파별 출처 추적)

각 옵션의 trade-off를 분석하고 1개 권장 + 사유 명시.

### 2. 매핑 데이터 (필수)
선택한 학파 기준으로 1000자 이상 한자에 대한 매핑 표:

```json
[
  {
    "char": "仁",
    "ohaeng": "木",
    "reason": "어진 마음·자라남의 의미 — 목의 인(仁)의 덕",
    "school_source": "○○○○"
  },
  ...
]
```

우선순위:
- 1순위: 한국 인명에 자주 쓰이는 한자 (인기 인명 1000자)
- 2순위: 추상 부수 한자 (亠·勹·宀·又·力 부속)
- 3순위: 복합 부수 한자

### 3. 학파 내 이견 명시
같은 한자가 학파별로 다른 오행으로 매핑되는 경우:

```json
{
  "char": "明",
  "primary_ohaeng": "火",
  "alternative_ohaeng": [
    {"ohaeng": "金", "school": "○○학파", "reason": "..."}
  ]
}
```

이견 있는 한자는 본 시스템에서 보수적 처리(primary만 사용 + 면책 명시).

### 4. 출처·반증 가능성 (ADR-010 사실성 분리 의무)
- 1차 문헌: 작명학 표준 교재 (저자·출판사·ISBN 명시 — 마스킹 금지)
- 2차 검증: 한국학술지 인용색인(KCI) 검색 가능한 논문
- 부수 → 오행 변환표는 학파별 출처 분리

### 5. 거부할 내용 (포함 금지)
- "이 오행이면 어떤 운이 좋다" 같은 인과 예언
- "통계적으로 유의미하다" 수사 (실제 데이터 없으면 거부)
- 검증 불가 작명원 주관 평가
- 학파 단정 ("이것이 정통이다" 같은 절대어)

## 출력 형식

마크다운 보고서 + 별도 JSON 파일:
1. 학파 비교 + 채택 권장 (마크다운)
2. 1000+자 매핑 표 (JSON — 본 SaaS data/ 폴더 직접 적용 가능 형식)
3. 학파 내 이견 한자 목록 (JSON)
4. 출처 + 반증 가능성 (마크다운)
5. 본 시스템 적용 시 면책 요구 사항
```

---

## 결과물 처리 절차

1. JSON 매핑을 `data/korean_hanja_unihan.json`에 병합
2. `vault/reports/[주제].md` 영속화
3. 코드 변경 0 (데이터만 업데이트, name_unihan 자동 반영)
4. 회귀: `python -c "from engine.divination.name_unihan import total_chars; print(total_chars())"` 확인
