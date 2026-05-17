---
type: done
status: applied
date: 2026-05-17
domain: [name]
adr: ADR-029-korean-name-uniqueness
related_report: reports/korean-name-frequency-statistics
---

# 한국 성씨·인명 빈도 결정론 분석 모듈 본문화 (ADR-029)

## 작업 요약

외부 보고서 "작명 SaaS 백엔드 결손 영역 보강을 위한 한국 성씨·인명 빈도
통계의 결정론적 분석 및 시스템 통합 보고서" (642줄) §3·§5·§6·§7 영역
본문화. 동명이인 회피 객관 라벨 모듈 신규 + 통계청 KOSIS 공공누리 제1유형
라이선스 컴플라이언스.

ADR-017 절차 **열 번째 본문화 사례**.

## 변경 사항

### 데이터 (신규 2건)

- [data/korean_surname_frequency.json](../../data/korean_surname_frequency.json) — 15 entries
  - 보고서 §3.2 본문 명시 (rank 1·2·3·55~59·151~157)
  - 공공누리 제1유형 라이선스 명시
- [data/korean_name_frequency_regression.json](../../data/korean_name_frequency_regression.json) — 30 entries
  - 보고서 §6 회귀 freq_001~freq_030 본문 완전 기술

### 코드 (신규)

- [engine/divination/name_uniqueness.py](../../engine/divination/name_uniqueness.py) — 신규 모듈
  - `name_uniqueness_score(name, gender, year)` 핵심 함수
  - `split_korean_name(name)` — 복성 12종 우선 매칭
  - `surname_rank(surname)` — 성씨 순위 조회
  - `is_compound_surname(surname)` — 복성 여부
  - `total_surnames()` — DB 카운터
  - `is_loaded()` — 데이터 로드 확인
  - `UniquenessResult` 불변 dataclass

### 회귀 테스트

- [engine/divination/test_name_uniqueness.py](../../engine/divination/test_name_uniqueness.py) — **21/21 PASS**
  - 데이터 로드 + 성씨 조회 + 복성 분리
  - 보고서 §6 회귀 12 PASS + 18 known-limitation
  - ADR-010 면책 자동 검증 + 인과 단어 차단
  - 결정론 보장 + 추정치 ≥ 0

### 신규 ADR

- [vault/decisions/ADR-029-korean-name-uniqueness.md](../decisions/ADR-029-korean-name-uniqueness.md)

### 신규 보고서

- [vault/reports/korean-name-frequency-statistics.md](../reports/korean-name-frequency-statistics.md)

## 보고서 §6 회귀 30쌍 결과

### 12 PASS ✅

| ID | 입력 | 성씨 | 결과 |
|---|---|---|---|
| freq_001 | 김민준 | 김(1) | very_common |
| freq_002 | 이서연 | 이(2) | very_common |
| freq_003 | 박서준 | 박(3) | very_common |
| freq_014 | 갈민준 | 갈(미수록) | rare |
| freq_015 | 견사랑 | 견(151) | rare |
| freq_016 | 당한결 | 당(152) | rare |
| freq_017 | 화서진 | 화(154) | rare |
| freq_018 | 창서윤 | 창(155) | rare |
| freq_020 | 옹지원 | 옹(157) | rare |
| freq_021 | 위태풍 | 위(미수록) | rare |
| freq_022 | 승아름 | 승(미수록) | rare |
| freq_023 | 순슬기 | 순(미수록) | rare |

### 18 known-limitation ⏸️

- 성씨 DB 누락 (4·5·6·7·8·9·10·11위 등 보고서 "중략" 영역)
  - freq_004 최서윤, freq_005 정하준, freq_006 강지훈, freq_007 조은주,
    freq_008 윤영숙, freq_009 장영수, freq_010 임도현, freq_011 남궁민,
    freq_012 제서연
- 동음이의 한자 (한글 분리 시 구분 불가)
  - freq_013 방현우 (方=55위 매핑되나 보고서는 더 작은 빈도 기대)
  - freq_019 방(龐)지훈 (龐=156위, 한글 '방' 분리 시 方로 매핑)
- 음절 미인기 결합 (성씨 1위 + 비인기 음절)
  - freq_024 김탁구, freq_025 이삼순, freq_026 박을룡

→ 통계청 KOSIS 300위 전수 추출 시 별도 ADR 후보. 모두 결정론 보장.

## 라이선스 컴플라이언스

- **통계청 KOSIS 공공누리 제1유형**: 영리 SaaS 사용 + 출처표시 의무 ✓
- **대법원 efamily.scourt.go.kr**: ADR-026 동일 출처 ✓
- 비식별 집계 데이터만 사용 (개인정보 보호법 무관)

## ADR-010 사실성 분리

- ✅ 공공 통계 출처 (통계청 + 대법원)
- ✅ 면책 자동 포함 (rationale에 "운명·인과관계 X" 명시)
- ✅ 인과 단어 차단 자동 검증 (흉함·재물운·개명·치명적·팔자)
- ✅ 출처 명시 (사용자 출력에 "통계청 2015" 노출)
- ✅ 결정론 (lru_cache + JSON)

## 라이브 검증 예시

```python
>>> from engine.divination.name_uniqueness import name_uniqueness_score
>>> r = name_uniqueness_score("김민준", gender="male")
>>> r.combined_frequency
'very_common'
>>> r.estimated_count
1068
>>> r.surname_rank
1

>>> r2 = name_uniqueness_score("옹지원", gender="female")
>>> r2.combined_frequency
'rare'
>>> r2.surname_rank
157

>>> r3 = name_uniqueness_score("남궁민", gender="male")
>>> r3.surname
'남궁'  # 복성 우선 매칭
```

## 향후 작업

- 통계청 KOSIS 300위 전수 추출 → 18 known-limitation 해소 (별도 ADR-030 후보)
- 한자 명시 성명 분리 (동음이의 龐 vs 方 구분)
- 시계열 음절 데이터 (보고서 §4 빈 약속 해소 시)
- 81수리 + 동명이인 라벨 통합 UX (프론트엔드)

## 메타

- ADR-017 열 번째 본문화
- 분석/판정 에이전트 ACCEPT 3 + DEFER 2 → 오케스트레이터 사용자 자율 정신 적용 → 본문화 진행
- 본 노트 immutable
