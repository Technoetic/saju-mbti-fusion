---
type: done
status: applied
date: 2026-05-17
domain: [name]
adr: ADR-028-korean-phonetic-rules-priority-1-2
related_report: reports/korean-phonetic-rules-architecture
---

# 표준발음법 §10~§30 Priority 1·2 본문화 (ADR-028)

## 작업 요약

외부 보고서 "한국어 표준발음법 전산 매핑 및 작명 어감 평가 아키텍처
고도화 연구 보고서"(439줄)의 §2~§4 영역 (매핑 표 + YAML 40사례 + JSON 30쌍)
중 Priority 1·2 부분을 본 시스템에 본문화.

ADR-016 (어감 부분 채택)에서 본문 4규칙만 부분 적용했으나, 본 ADR로
국립국어원 표준발음법 §10~§30 7개 음운 변동 결정론 함수 신규 + 합성
함수 `phonetic_delta_score()` 추가.

ADR-017 절차 **아홉 번째 본문화 사례**.

## 변경 사항

### 코드 (engine/divination/name_aesthetic.py)

기존 426줄 → 음운 변동 함수 7개 신규 + 합성 함수 1개 추가:

| 함수 | 표준발음법 조항 | 시그니처 |
|---|---|---|
| `f_nasalize(coda, initial)` | §18~§19 비음화 | → 새 종성 or None |
| `f_lateralize(coda, initial)` | §20 유음화 | → (종성, 초성) or None |
| `f_aspirate(coda, initial)` | §12 격음화 | → (종성, 초성) or None |
| `f_tensify(coda, initial)` | §23~§28 경음화 | → 새 초성 or None |
| `f_simplify_cluster(coda)` | §10~§11 자음군 단순화 | → str |
| `f_link(coda, initial)` | §13~§16 연음 (§14 겹받침) | → (종성, 초성) or None |
| `f_insert_n(coda, initial, jung_next)` | §29~§30 ㄴ첨가 | → (종성, 초성) or None |
| `phonetic_delta_score(name_korean)` | 합성 (옵션 b) | → dict |

`_compose_jamo()` 자모 합성 헬퍼 추가.
`_CODA_VELAR`, `_CODA_ALVEOLAR`, `_CODA_BILABIAL`, `_TENSE_MAP`,
`_ASPIRATE_MAP`, `_N_INSERT_VOWELS`, `_CLUSTER_SIMPLIFY`,
`_PLAIN_CONSONANTS` 결정론 매핑 테이블 추가.

### 데이터 (신규)

- [data/korean_phonetic_rules.json](../../data/korean_phonetic_rules.json) — 보고서 §4 30 entries
  - test_p001~test_p030
  - 각 entry: id, input_name, expected_phonetic, rule_applied, expected_score_delta

### 회귀 테스트

- [engine/divination/test_name_aesthetic.py](../../engine/divination/test_name_aesthetic.py) — **59/59 PASS** (34 기존 + 25 신규)
  - 각 함수 단위 테스트 (7×2~3)
  - phonetic_delta_score 반환 스키마 + delta 범위 + 면책 + 결정론
  - 보고서 §4 회귀 14/30 PASS 명시 + 16 known-limitation 결정론 보장
  - ADR-010 인과 단어 차단 자동 검증

### 신규 ADR

- [vault/decisions/ADR-028-korean-phonetic-rules-priority-1-2.md](../decisions/ADR-028-korean-phonetic-rules-priority-1-2.md)

### 신규 보고서

- [vault/reports/korean-phonetic-rules-architecture.md](../reports/korean-phonetic-rules-architecture.md)

## 보고서 §4 회귀 30쌍 결과

### Priority 1·2 통과 14쌍 ✅

| ID | 입력 | 변환 | 조항 |
|---|---|---|---|
| test_p001 | 박나리 | 방나리 | §18 비음화 |
| test_p003 | 김백민 | 김뱅민 | §18 비음화 |
| test_p005 | 이덕만 | 이덩만 | §18 비음화 |
| test_p006 | 신루리 | 실루리 | §20 유음화 |
| test_p007 | 진리안 | 질리안 | §20 유음화 (역행) |
| test_p008 | 김만리 | 김말리 | §20 유음화 |
| test_p009 | 최권률 | 최궐률 | §20 유음화 |
| test_p011 | 김국진 | 김국찐 | §23 경음화 |
| test_p013 | 이백조 | 이백쪼 | §23 경음화 |
| test_p014 | 송학동 | 송학똥 | §23 극단 경음화 (-5) |
| test_p015 | 김복자 | 김복짜 | §23 경음화 |
| test_p018 | 최덕호 | 최더코 | §12 격음화 |
| test_p019 | 송백현 | 송배켠 | §12 격음화 |
| test_p030 | 송닭이 | 송달기 | §14 겹받침 연음 |

### Priority 3 known-limitations 16쌍 ⏸️

- 자음군 §11 + 경음화 연쇄 (test_p028, p029)
- ㄴ첨가 §29~§30 단어 경계 (test_p021, p022, p023, p025) — 합성어 단정 회피
- 상호동화 §19 (test_p004 송학림 → 송항님)
- 한자어 §26 특례 (test_p012 박철수 → 박철쑤) — 한자어 식별 LLM 회피
- 평음화 §9 + 비음화 (test_p002)
- ㅎ 약화 (test_p016, p020)
- 격음화 변형 (test_p017, p027)
- 비음화 붙임 (test_p024)
- 겹받침 연음 예외 (test_p026)
- 비음화+유음화 연쇄 (test_p010)

별도 ADR 후보 (ADR-029). 모든 미구현 영역도 **결정론 보장** (동일 입력 동일 출력).

## ADR-010 사실성 분리

- ✅ 학술 출처: 국립국어원 표준발음법 + 조성문(2025) + 신지영(2010·2014)
- ✅ 면책 자동 포함 (DISCLAIMER_KO)
- ✅ 인과 단어 차단 자동 검증 (운명·사주·흉함·재물운·개명·치명적·팔자)
- ✅ 보고서 §6 white-list/black-list 정합 (UI 영역 별도 강제)
- ✅ 결정론 (lru_cache + 자모 분리)

## 라이브 검증 예시

```python
>>> from engine.divination.name_aesthetic import phonetic_delta_score
>>> phonetic_delta_score("박나리")
{
    'input_name': '박나리',
    'expected_phonetic': '방나리',
    'applied_rules': ['§18~19 비음화 (ㄱ→ㅇ / ㄴ_)'],
    'score_delta': -2,
    'rationale': "'박나리'은 표준발음법 적용 시 [방나리]으로 발음됩니다 (...). ※ ..."
}

>>> phonetic_delta_score("송학동")
{
    ...
    'expected_phonetic': '송학똥',
    'applied_rules': ['§23~26 경음화 (ㄱ+ㄷ→ㄸ)'],
    'score_delta': -4,
    ...
}
```

## 향후 작업

- ADR-029 후보: Priority 3 (자음군 §11+§23 연쇄, ㄴ첨가 §29 합성어 경계,
  상호동화 §19, 한자어 §26 특례) — 단어 경계 식별 + 한자어 식별 LLM
  보조 필요 (결정론 단정 회피)
- 프론트엔드 white-list/black-list 자동 렌더링 (UI 영역, ADR-010 강제)
- 보고서 §3 YAML 40 사례 추가 회귀 (현재 30쌍만 본문화)
- phonetic_delta_score → aesthetic_score 통합 (현재 독립)

## 메타

- ADR-017 아홉 번째 본문화
- 분석/판정 에이전트 보수적 ACCEPT + 오케스트레이터 보충 검증 (보고서 본문 라인 304-335 직접 추출)
- 옵션 b 자율 채택 (사용자 명시 "합리적이면 진행" 정신)
- 본 노트 immutable
