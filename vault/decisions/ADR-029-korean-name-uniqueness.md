---
type: adr
status: accepted
date: 2026-05-17
domain: [name]
related: [ADR-001, ADR-006, ADR-010, ADR-016, ADR-026]
related_report: reports/korean-name-frequency-statistics
---

# ADR-029 — 한국 성씨·인명 빈도 결정론 분석 (동명이인 회피)

## 상태

Accepted (2026-05-17).

## 맥락

본 시스템의 작명 추천은 81수리·발음오행·자원오행·불용한자 등 전통 성명학
규칙 기반. 현대 사용자가 가장 민감하게 반응하는 **동명이인 회피** 영역은
결손 (engine/divination/name_uniqueness.py 부재).

외부 보고서 "작명 SaaS 백엔드 결손 영역 보강을 위한 한국 성씨·인명
빈도 통계의 결정론적 분석 및 시스템 통합 보고서" (2026-05-17, 642줄)가
다음 명시:

- §2 공공누리 KOGL 1~4유형 분석 (제1유형 = 상업 사용 허가)
- §3 통계청 2015 인구주택총조사 성씨 데이터 (본문 명시 15건)
- §4 인명 음절 시대 트렌드 (구조만, 시계열 데이터 미제공 → ADR-016 대체)
- §5 name_uniqueness.py 함수 명세 (결합 확률 + 복성 + 임계값)
- §6 회귀 30쌍 (freq_001~freq_030 본문 완전 기술)
- §7 ADR-010 사실성 분리 면책 가이드라인 (white-list/black-list)

학술/공식 출처: 통계청 KOSIS (공공누리 제1유형) + 대법원 efamily.scourt.go.kr
(ADR-026 영속화 완료).

## 결정

**보고서 §3 본문 명시 영역만 본문화** (15건 성씨 + 30쌍 회귀 검증 + 신규 함수).
보고서 자체 "중략" 영역 (4·5·6·7·8·9·10위 등)은 통계청 KOSIS 직접 추출
별도 작업 (DEFER).

### 본문화 영역

| 영역 | 내용 |
|---|---|
| `data/korean_surname_frequency.json` | 보고서 §3.2 명시 15건 성씨 (rank 1·2·3·55~59·151~157) |
| `data/korean_name_frequency_regression.json` | 보고서 §6 회귀 30쌍 (freq_001~freq_030) |
| `engine/divination/name_uniqueness.py` | 신규 모듈 (결정론 + 면책) |
| `engine/divination/test_name_uniqueness.py` | 회귀 21건 (12 보고서 회귀 + 18 known-limitation + 9 기타) |

### API (Public)

```python
name_uniqueness_score(name, gender="neutral", year=None) -> UniquenessResult | None
# 반환: UniquenessResult(name, gender, surname, given_name, surname_rank, surname_pct,
#   first_syllable_rank, last_syllable_rank, combined_frequency, estimated_count, rationale)

split_korean_name(name) -> tuple[str, str] | None  # 복성 우선
surname_rank(surname) -> int | None
is_compound_surname(surname) -> bool
total_surnames() -> int
is_loaded() -> bool
```

### 빈도 라벨 (보고서 §5.3 임계값)

| 라벨 | 동명이인 추정 수 |
|---|---|
| `very_common` | ≥ 300 |
| `common` | ≥ 50 |
| `uncommon` | ≥ 10 |
| `rare` | < 10 |

### 복성 12종 (보고서 §5.2)

남궁·황보·제갈·사공·선우·독고·동방·서문·어금·장곡·남궐·제오

## 회귀 결과

보고서 §6 30쌍 회귀:

- **본 시스템 통과 12/30**: 보고서 본문 명시 성씨 (1·2·3·151~157) + 미수록 성씨 (갈·위·승·순 등 → rare 자동 분류)
- **18/30 known-limitation**: 성씨 DB 누락 (4·5·6·7·8·9·10·11위 등 보고서 "중략" 영역) + 한자 동음이의 (방 龐 vs 方) + 음절 미인기 영역
  → 결정론 보장 (동일 입력 동일 출력)
  → 별도 ADR 후보 (통계청 KOSIS 300위 전수 추출 시)

## 정합성

| ADR | 정합성 | 사유 |
|---|---|---|
| ADR-001 (결정론) | OK | lru_cache + JSON, 음운 변동 0 |
| ADR-002 (학파 회피) | N/A | 통계 매핑, 학파 없음 |
| ADR-006 (자문 거절) | OK | 의료·법률 인과 0, 객관 라벨만 |
| ADR-010 (사실성 분리) | OK | 공공 통계 출처 + 면책 자동 포함 + 인과 단어 차단 |
| ADR-014 (사주→MBTI) | N/A | |
| ADR-015 (옵션 B 병행) | N/A | |
| ADR-016 (어감 부분 채택) | OK | 음절 빈도 데이터 (`_get_freq_dict`, `_get_positional_freq`) 재사용 |
| ADR-026 (인명용 9389) | OK | 대법원 efamily 데이터 동일 출처 |

## 학파/공식 출처

- **통계청 2015년 인구주택총조사 성씨·본관 편** (KOSIS)
  - 공공누리 제1유형 (영리 사용 + 출처표시 필수)
  - https://kogl.or.kr/info/license.do
- **대법원 전자가족관계등록시스템** (efamily.scourt.go.kr)
  - 인기 이름 통계 (ADR-026 영속화 완료)
- **ADR-016** name_aesthetic_syllable_freq.json (음절 빈도)

## 면책 (ADR-010 준수 강제)

사용자 출력에 `name_uniqueness_score()` 사용 시:

1. **결과 표시**: "[이름]은 통계청 2015 기준 성씨 빈도 X위, 추정 동명이인 약 N명으로 [라벨] 이름으로 분류됩니다"
2. **면책 자동 포함**: `rationale` 필드에 "공공 통계 기반 객관 빈도 라벨이며, 이름의 운명·길흉·사주와 어떠한 인과관계도 없습니다" 강제
3. **차단 인과 단어** (회귀 자동 검증): 흉함·재물운·개명·치명적·팔자
4. **출처 명시 의무**: 통계청·대법원

## 한계 (영구 기록)

- 본 ADR 15/300+ 성씨 본문화 (보고서 본문 명시 범위). 잔여 ~285건은 통계청
  KOSIS 직접 추출 별도 작업 (DEFER)
- 한글 동음이의 성씨 (예: 방=方 vs 龐) 구분 불가 — 한자 명시 입력 시
  별도 처리 영역
- 시계열 데이터 (2010/2015/2020/2025 분리) 미제공 — 보고서 §4 빈 약속 (구조만)
- year 파라미터 placeholder — 시계열 데이터 본문화 후 활용
- estimated_count는 결합 확률 추정치 — 실 측정값 아님 (보수적 임계값 라벨링 용도)
- 본 ADR은 **immutable**. 데이터 추가 시 새 ADR

## 사용자 출력 예시

```python
>>> name_uniqueness_score("김민준", gender="male")
UniquenessResult(
    name='김민준',
    surname='김',
    given_name='민준',
    surname_rank=1,
    surname_pct=21.5,
    combined_frequency='very_common',
    estimated_count=1068,
    rationale="'김민준'은 통계청 2015년 인구주택총조사 기준 성씨 빈도 1위,
        추정 동명이인 약 1068명으로 '매우 흔한' 이름으로 분류됩니다. ※ 본 분류는
        공공 통계 기반 객관 빈도 라벨이며, 이름의 운명·길흉·사주와 어떠한
        인과관계도 없습니다. 동명이인 회피를 위한 참고 지표로만 활용하시기 바랍니다."
)
```

## 관련

- 외부 보고서: [[../reports/korean-name-frequency-statistics]]
- 본 작업 영속화: [[../done/korean-name-uniqueness]]
- 회귀: `engine/divination/test_name_uniqueness.py` (21/21 PASS)
- 데이터: `data/korean_surname_frequency.json` + `data/korean_name_frequency_regression.json`
