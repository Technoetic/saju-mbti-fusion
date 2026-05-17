---
type: prompt_template
target: deepresearch
purpose: 한국 성씨·인명 빈도 통계 — 작명 시 흔한 이름 회피 + 동명이인 회피 점수화
created: 2026-05-17
related_module: engine/divination/name_gaemyeong.py (보강)
related_adr:
  - ADR-010-name-sibling-factuality (사실성 분리)
  - ADR-002-saju-option-A (학파 회피)
priority: medium
status: draft
---

# 딥리서치 프롬프트 — 한국 성씨·인명 빈도 통계

## 사용법

본 프롬프트는 작명 모듈의 결손 영역 보강용. 현 시스템은 81수리·발음오행·
음양·자원오행·서열 등 풍부하나 **인명 빈도 데이터 부재** — 즉 "흔한 이름"
회피 조언 결정론 불가능.

통계청 인구주택총조사 + 행정안전부 인명용 한자 통계 기반 결정론 데이터
구축. 인과 길흉 X, 객관 빈도 라벨만 채택.

---

## 프롬프트 본문

```
한국 성씨·인명 빈도 통계 데이터를 작명 SaaS 백엔드에 결정론적으로
적용할 수 있도록 조사·정리해주세요.

### 요구사항

#### 1. 성씨 빈도 통계 (통계청 인구주택총조사)

- 2015년 인구주택총조사 (성씨 본관 포함, 마지막 전수조사)
- 2020년 또는 최신 보완 자료
- 출처: kostat.go.kr 또는 통계청 공식 데이터

데이터 구조 (예시):
```yaml
surnames_top_300:
  - rank: 1
    surname: "김"
    count: 10689959
    pct: 21.5
    source: "통계청 2015 인구주택총조사"
  - rank: 2
    surname: "이"
    ...
```

#### 2. 인명 음절 빈도 (행정안전부·대법원)

- 행정안전부 출생신고 인명 통계
- 대법원 가족관계등록부 인명 빈도
- 연도별 인기 음절 (예: 2010·2015·2020·2025)
- 성별별 인기 음절

데이터 구조 (예시):
```yaml
popular_syllables_by_year:
  - year: 2020
    gender: "M"
    top_50:
      - rank: 1
        syllable: "준"
        count: 12345
        pct: 5.2
        position: "끝"  # 첫음절·끝음절 빈도 구분
```

#### 3. 사용 라이선스·법규

- 통계청 데이터 상업 SaaS 사용 라이선스
- 행정안전부 공공데이터 포털 라이선스
- 개인정보 보호: 음절 통계는 익명·집계 데이터로 비식별

#### 4. 결정론 적용 함수 명세

본 시스템 채택 시 다음 결정론 함수 구현 가능해야 함:

```python
def name_uniqueness_score(name: str, year: int = 2025) -> dict:
    """
    이름의 동시대 흔함 지수 (객관 빈도 기반).

    Returns:
        {
            "surname_rank": 1,        # 김 1위
            "surname_pct": 21.5,
            "first_syllable_rank": 3,  # 이름 첫 음절 순위
            "last_syllable_rank": 1,
            "combined_frequency": "very_common" | "common" | "uncommon" | "rare",
            "alternative_count_estimate": 15000  # 추정 동명이인 수
        }
    """
```

#### 5. 사용자 출력 면책 가이드

다음 표현 금지:
- ❌ "흔한 이름은 운이 약합니다." (인과 도그마)
- ❌ "독특한 이름이 성공합니다." (예언)

채택할 표현:
- ✅ "통계청 2020 인구주택총조사 기준 김씨는 전체 21.5%, '준'은
  남자 이름 1위입니다. 동명이인 회피를 원하시면 참고하시기 바랍니다."
- ✅ "본 결과는 객관 빈도 통계이며 길흉과 무관합니다."

#### 6. 회귀 테스트 데이터셋

본 시스템 회귀 검증용 30쌍:

```json
[
  {
    "id": "freq_001",
    "name": "김준호",
    "year": 2020,
    "expected": {
      "surname_rank": 1,
      "first_syllable_rank": 1,
      "combined_frequency": "very_common"
    }
  }
]
```

#### 7. 본 시스템 결손 영역

현 `engine/divination/` 모듈 점검:
- ✅ 81수리·발음오행·음양·자원오행·서열 모두 구현
- ❌ 인명 빈도 데이터 부재
- ❌ 동명이인 회피 점수 불가

신규 모듈 후보:
- `data/korean_surname_frequency.json` (성씨 300+)
- `data/korean_syllable_frequency.json` (연도별 음절 빈도)
- `engine/divination/name_uniqueness.py` (결정론 함수)

### 출력 형식

1. **성씨 빈도 표 YAML** (300위까지)
2. **연도별 음절 빈도 표 YAML** (2010·2015·2020·2025 × 성별)
3. **라이선스·법규 점검 보고**
4. **결정론 함수 명세 + 임계값**
5. **사용자 출력 면책 가이드라인**
6. **회귀 데이터셋 JSON** (30쌍)

### 검증 기준

- 모든 통계 출처 통계청/행정안전부 공식 URL로 라이브 검증
- 가짜 인용 0건
- 라이선스 명확 (상업 SaaS 사용 가능)
- 인과 길흉 표현 0건

위 조건 미충족 시 ADR-010 사실성 분리에 따라 거부됩니다.
```

---

## 본 시스템 채택 절차

1. `/squeeze-report` 사실성 분리 + 통계청 라이브 검증
2. ACCEPT 후보:
   - 신규 ADR (인명 빈도 데이터 정책)
   - `engine/divination/name_uniqueness.py` 신규
   - `data/korean_surname_frequency.json` + `data/korean_syllable_frequency.json`
   - 회귀 30건
   - vault/references/ 통계청 공식 자료 영속화

## 면책

- ADR-010 사실성 분리 의무
- 빈도 = 객관 라벨, 인과 길흉 절대 금지
- 라이선스 위반 시 채택 거부
- 통계청 데이터 갱신 주기 (5년) 명시
