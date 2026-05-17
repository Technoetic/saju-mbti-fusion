---
type: done
status: applied
date: 2026-05-17
domain: name
related:
  - decisions/ADR-016-name-aesthetic-partial.md
  - reports/name-aesthetic-survey.md
commit: TBD
---

# 어감·인기 음절 가점 — 보고서 부분 채택 (ADR-016)

## 무엇

[[../roadmap/name-aesthetic-survey]] (🟢 외부 입력 대기) **부분 완료**.
딥리서치 보고서 수신 + ADR-010 사실성 분리 검증 결과 혼합 등급 → 검증된
§2 부분만 본문화.

## ADR-010 검증 핵심 발견

### KCI 라이브 fetch로 가짜 인용 2건 발견

1. **김진욱·류선영 (2017)** "한국인 이름 음운 빈도" — **존재하지 않음**
   - 실제: 조성문(2025) "한국인 이름의 음운적 특성" (다른 저자·연도)
2. **정희원 (2009)** "한국어 사전 표제어 음절 빈도" — **존재하지 않음**
   - 실제: 신지영(2010) Communication Sciences and Disorders (저자·연도 모두 오류)

### 빈 약속 2건 발견

- §1 "음운 결합 자연스러움 규칙 JSON 형식 정리" → 본문에 JSON 없음
- §3 "회귀 테스트 데이터 50쌍 다음과 같다" → 본문에 데이터 없음

## 변경

### 신규 데이터
- [data/name_aesthetic_syllable_freq.json](../../data/name_aesthetic_syllable_freq.json)
  - 보고서 §2.1·§2.2 인기 이름 70건(10년 × 7위) 추출
  - 가중치 산출 (1위=7점 / ... / 7위=1점)
  - 남자 17 음절 (1위 '준' 170점)
  - 여자 17 음절 (1위 '서' 135점)
  - 중성 (남+여 합산)

### 신규 모듈
- [engine/divination/name_aesthetic.py](../../engine/divination/name_aesthetic.py)
  · `aesthetic_score(name_korean, gender)` — 음절 가점 산출
  · `AestheticResult` — score 0.0~1.0 + rationale (면책 내장)
  · `get_top_syllables(gender, n)` — 디버깅
  · `DISCLAIMER_KO` 상수

### 신규 테스트
- [engine/divination/test_name_aesthetic.py](../../engine/divination/test_name_aesthetic.py) — 14 PASS
  · 데이터 로드 3 (총 음절 수 + 보고서 정답 검증)
  · 점수 산출 5 (인기 이름·비인기·정규화·빈 입력·비한글)
  · ADR-016 출력 의무 3 (면책·인과 거부·단정 금지)
  · 결정론 + 성별 차별화 2

## 검증

```
python -m pytest engine/divination/test_name_aesthetic.py --no-skip-all
14 passed in 0.95s
```

### 라이브 시나리오
- "이준" (남자) → 점수 ~0.59 (1위 음절 '준' 170점 포함)
- "서아" (여자) → 점수 ~0.66 (1위 음절 '서' 135점 포함)
- "괴짜" → 0.0 (인기 통계 음절 없음)
- "준수" 남자 vs 여자 → 남자 점수가 높음 (성별 차별화 작동)

## 미채택 (재시도 필요)

| 영역 | 사유 | 향후 |
|---|---|---|
| ~~§1 음운 결합 규칙~~ | ~~빈 약속~~ | ✅ **추가 채택 완료** (보고서 본문 명시 4규칙) — 본 노트 하단 추가 본문화 절 참조 |
| §3 회귀 50쌍 | 빈 약속 | 본 모듈 회귀에 인기 이름 70건이 대체 |
| §4 학술 인용 | 가짜 인용 2건 | 인용 없이 통계 데이터만 사용 |

## 2026-05-17 추가 본문화 — §1 음운 결합 규칙

본 보고서 §1 JSON 표는 빈 약속이나, **본문에 명시된 4개 규칙**은 국립국어원
표준발음법 기반 한국어 음운론 표준 사실 → 추가 본문화.

### 추가 구현

[engine/divination/name_aesthetic.py](../../engine/divination/name_aesthetic.py):
- `phonetic_combination_score(name_korean)` — 음운 결합 자연스러움 점수
- `_decompose_jamo(syllable)` — 한글 음절 → (초성·중성·종성) 분해
- `_normalize_coda(coda)` — 표준발음법 제8항 7대 종성 정규화
- `_AWKWARD_BATCHIM_INITIAL` — 자음군 회피 위반 조합 (ㄱ+ㅍ 등)
- `_SMOOTH_BATCHIM_INITIAL` — 자연 결합 조합 (ㄴ+ㅇ 등)

### 보고서 §1 예시 검증

| 입력 | 점수 | 보고서 §1 분류 | 일치 |
|---|---|---|---|
| 선영 (ㄴ+ㅇ) | +1.00 | 자연 결합 | ✅ |
| 박파 (ㄱ+ㅍ) | -1.00 | 자음군 회피 위반 | ✅ |

### 추가 회귀 (23 PASS, 기존 14 + 신규 9)
- 자모 분해 1
- 자연/어색 결합 2
- 1음절 처리 1
- 정규화 1
- 면책/인과 거부 2
- 종성 정규화 1
- 결정론 1

### 보고서 §1 채택 근거

보고서 §1 JSON 표는 빈 약속이나, **본문 텍스트**에 다음 4규칙 명시:
1. 종성 7자음 (ㄱㄴㄷㄹㅁㅂㅇ) — 표준발음법 제8항
2. ㄴ 받침 + ㅇ/ㅎ = 자연 결합
3. ㄱ 받침 + ㅍ = 자음군 회피 위반 (어색)
4. 비음화·유음화·된소리되기 자음동화

→ 한국어 음운론 표준 사실. ADR-010 통과.

### 면책 의무

`phonetic_combination_score` 반환 dict의 `rationale`에 면책 메시지 자동 포함.

## ADR-010 의 정교한 적용

본 작업은 ADR-010의 가장 정교한 적용 사례:

1. **KCI 라이브 검증** — 인용 학술 출처 가짜 인용 발견
2. **출처 독립 검증** — baby-name.kr WebFetch로 인기 통계 사실성 확인
3. **부분 채택** — 검증된 §2만 채택, 가짜 인용·빈 약속 폐기
4. **면책 의무** — rationale 자동 포함

본 보고서가 거부된 saju-mbti 보고서들과 결정적 차이: **§2 데이터는 독립
검증 통과**. 가짜 인용은 부분이라 보고서 전체를 거부하지 않고 부분 채택.

## 면책

- 본 모듈은 추천 정렬 가점 — 길흉 절대 기준 X
- 음절 빈도는 추세 — 절대 평가 X
- 사용자 출력 rationale에 면책 자동 포함

## 결과

- roadmap [[../roadmap/name-aesthetic-survey]] **부분 완료**
- §1 (음운 규칙)·§3 (50쌍 회귀)은 향후 재시도 필요
- 보고서로부터 짜낼 가치 모두 추출
