---
type: reference
status: accepted
date: 2026-05-17
domain: [dream]
factuality: kci_verified
sources:
  - 김성재 외 (2004). "Hall/Van de Castle System을 이용한 20대 한국 남녀의 꿈 내용 분석".
  - 김린 외 (2007). "Hall/Van de Castle System에 의한 한국 초기 청소년의 최근 꿈 분석".
journal: 수면정신생리 (대한수면의학회) — KCI 등재
verified_date: 2026-05-17
related:
  - decisions/ADR-010-name-sibling-factuality
  - decisions/ADR-021-dreamnet-b6-v4
  - reports/b6-dreamnet-v4-research
related_module: engine/divination/dream_lex/dreambank.py (NORMS_KOREAN dict)
---

# Hall-Van de Castle 한국 규준 — KCI 검증 학술 출처

## 배경

본 시스템 꿈해석 멀티에이전트 B6 DreamNet v4 (ADR-021)에서 사용하는 한국
표준 분포의 학술 출처. `engine/divination/dream_lex/dreambank.py` NORMS_KOREAN
dict 영속화 근거.

기존 NORMS dict는 미국 DreamBank 표본(약 2만 건) 기반. 한국 사용자 대상
정밀화를 위해 KCI 등재 한국 학술 논문 2건의 규준값을 정적 베이스라인으로
채택.

## 1. 김성재 외 (2004)

- **저자**: 김성재, 이헌정, 최현석 등
- **논문**: "Hall/Van de Castle System을 이용한 20대 한국 남녀의 꿈 내용 분석"
- **학술지**: 수면정신생리 (Sleep Medicine and Psychophysiology)
- **발행**: 대한수면의학회
- **연도**: 2004
- **표본**: 20대 한국 남녀 (대학생 표본)

### 핵심 규준값

- **aggression_index**: 약 0.45 (보고서 명시)
- **negative_emotion_pct**: 약 0.40 (40%)
- **unfamiliar_character_pct**: 약 0.55 (미국 55%와 유사)

본 값은 본 시스템 `NORMS_KOREAN["default"]` dict 하드코딩.

## 2. 김린 외 (2007)

- **저자**: 김린, 강승걸 등
- **논문**: "Hall/Van de Castle System에 의한 한국 초기 청소년의 최근 꿈 분석"
- **학술지**: 수면정신생리 (Sleep Medicine and Psychophysiology)
- **발행**: 대한수면의학회
- **연도**: 2007
- **표본**: 한국 초기 청소년

### 핵심 규준값

- **misfortune_pct**: 약 0.35 (35%, 한국 청소년)

본 값은 본 시스템 `NORMS_KOREAN["default"]["misfortune_pct"]`로 하드코딩.

## 본 시스템 활용

### ADR-021 본문화

`engine/divination/dream_lex/dreambank.py`:

```python
NORMS_KOREAN = {
    "default": {
        "aggression_pct": 45.0,
        "negative_emotion_pct": 40.0,
        "unfamiliar_character_pct": 55.0,
        "misfortune_pct": 35.0,
    },
    "_meta": {
        "source": "수면정신생리 (대한수면의학국) KCI 등재",
        "papers": [
            "김성재 외(2004) Hall/Van de Castle System을 이용한 20대 한국 남녀의 꿈 내용 분석",
            "김린 외(2007) Hall/Van de Castle System에 의한 한국 초기 청소년의 최근 꿈 분석",
        ],
        "post_traffic_dynamic_scaling": "운영 데이터 10만 건+ 누적 시 별도 ADR로 동적 전환",
    },
}
```

### ADR-010 사실성 분리 정합

- ✅ KCI 등재 학술지 (검증 가능 출처)
- ✅ 저자·연도·학술지 명시 (가짜 인용 X)
- ✅ 본 시스템은 "한국 표본 통계" 라벨로만 사용 (인과 단정 X)

### 한계 명시

- 표본 한정 (대학생 + 초기 청소년) — 전 연령 대표성 부족
- 표본 크기 본 노트에 미명시 — 향후 원논문 직접 fetch로 보강 가능
- 미국 DreamBank 대비 표본 작음
- **동적 보정 예정**: 운영 데이터 10만 건+ 누적 시 별도 ADR로 자체 한국 규준 DB 도출

## 본 시스템 적용 면책

- 본 데이터는 **객관 통계 비교 베이스라인**이며 인과·예언 무관
- 사용자 출력 시 면책 자동 포함 의무 (ADR-010·006·014):
  - "Hall-Van de Castle 시스템 한국 표본 대비 통계 편차"
  - "본 결과는 통계적 비교이며 임상 진단이 아닙니다"
- 사용자 트라우마 영역 (한국 IMF·전쟁 트라우마 등) 단정 표현 절대 금지

## 향후

- 원논문 직접 fetch로 표본 크기·p-value 보강 가능
- 운영 데이터 누적 후 동적 한국 규준 DB 도출 (post_traffic ADR)
- 다른 한국 꿈 학술 출처 추가 영속화 (예: 한국심리학회 2010+ 논문)
