---
type: adr
status: accepted
date: 2026-05-17
domain: [name]
related: [ADR-001, ADR-010, ADR-026, ADR-029]
related_report: reports/korean-surname-300-algorithm-extension
supersedes: ADR-029 (15 → 300 entries 확장, 한자 분리 + γ 보정)
---

# ADR-033 — 한국 성씨 300위 전수 + 한자 분리 + γ 보정 (ADR-029 확장)

## 상태

Accepted (2026-05-17).

## 맥락

ADR-029 (2026-05-17) 한국 성씨·인명 빈도 결정론 분석 본문화. 그러나
보고서 본문 명시 15 entries만 채택 → 30쌍 회귀 12/30 PASS + 18 known-limitation.

외부 보고서 "작명 SaaS 백엔드 결손 영역 보강을 위한 한국 성씨·인명 빈도
통계 분석 및 알고리즘 고도화 보고서" (2026-05-17, 537줄) §2~§6 직접 응답:
- §2 라인 23-323: **300 entries 전수 본문 명시** (빈 약속 0)
- §3 한자 동음이의 분리 알고리즘 (split_korean_name_with_hanja)
- §4 γ 감마 보정 계수 (음절 미인기 결합 보수적 1/10)
- §5 회귀 18쌍 해소 기전
- §6 ADR-010 면책

학술/공식 출처: 통계청 KOSIS 2015 (공공누리 제1유형) + 신지영 (2014) γ 학설.

## 결정

**300 entries 전수 본문화 + split_korean_name_with_hanja 신규 + γ 보정**.
ADR-029 supersede (ADR-029 immutable 보존, 본 ADR이 확장).

### 본문화 영역

| 영역 | 내용 |
|---|---|
| `data/korean_surname_frequency.json` | 15 → **300 entries** (보고서 §2 라인 23-323 전수) |
| `engine/divination/name_uniqueness.py` | `split_korean_name_with_hanja` + `_apply_gamma_penalty` + 한자 인덱스 |
| `engine/divination/test_name_uniqueness.py` | 24/24 PASS (21 기존 + 3 신규) |

### 새 API (보고서 §3·§4)

```python
split_korean_name_with_hanja(name_kr, hanja_name=None) -> tuple[str, str|None, str] | None
# 동음이의 한자 정확 구분 (방方 vs 방龐)

_apply_gamma_penalty(first_rank, last_rank, rank_threshold=100) -> float
# 음절 둘 다 비인기 → γ=0.1 (보고서 §4 보수적)
GAMMA_BOTH_LOW_RANK = 0.1
GAMMA_DEFAULT = 1.0
```

### 데이터 분포 (보고서 §2)

| 영역 | entries |
|---|---|
| 보고서 §2 전수 | 300 |
| 한글 unique surname | 164 (동음이의 한자 80건 한글 충돌) |
| `total_surnames()` | 164 |
| 동음이의 한자 분리 가능 | 80건 (방方/龐, 정鄭/丁/程, 강姜/康/江, 조趙/曺 등) |

### 회귀 결과 (보고서 §6 30쌍)

- **15 PASS** (ADR-029 12 → ADR-033 15, +3건)
  - 신규 PASS: freq_010 임도현, freq_019 방(龐)지훈, freq_030 임하늘
- **15 known-limitation**:
  - freq_004~009: 임계값 분포 보정 영역 (got common, expected very_common)
  - freq_011·012·013: 음절 미인기 + γ 추가 강화 필요
  - freq_024·025·026: 음절 미수록 (γ 적용했으나 임계값 초과)
  - freq_027·028·029: 음절 미인기 결합

### 정합성

| ADR | 정합성 | 사유 |
|---|---|---|
| ADR-001 (결정론) | OK | lru_cache + JSON |
| ADR-002 (학파 회피) | N/A | 통계 매핑 |
| ADR-006 (자문 거절) | OK | 의료·법률 인과 0 |
| ADR-010 (사실성 분리) | OK | rationale 면책 + 출처 명시 + γ 학술 근거 (신지영 2014) |
| ADR-026 (efamily.scourt.go.kr 한자) | OK | 한자 데이터 동일 출처 |
| ADR-029 (성씨 15 entries) | OK (extension) | immutable 보존, 본 ADR로 확장 |

## REJECT 영역

- **C5 시계열 음절 데이터**: 보고서 구조 제안만, 실 데이터 0 → DEFER (별도 ADR)
- **C4 30/30 PASS**: 부분 달성 (15/30 + 15 known-limitation) — ADR-027·028·029·032 패턴 정합

## DEFER 영역

- 잔여 15 known-limitation (임계값 분포 보정 + γ 추가 강화)
- 시계열 음절 데이터 (향후 ADR-034 후보)

## 사용자 결정 영역 (참고)

- UX: 한자 입력 UI 제공 여부 (사업 단계, U2)
- γ 강도: 0.1 보수적 vs 0.3 (학파 견해, U3 — 본 ADR 0.1 채택)

## 학술/공식 출처

- **통계청 KOSIS 2015 인구주택총조사**: 공공누리 제1유형 (영리 + 출처표시)
- **신지영 (2014)** 『말소리의 이해』: γ 감마 학설 근거
- **조성문 KCI**: 한국어 자음 음운 현상 (vault/references/korean-phonetic-research.md)

## 면책 (ADR-010 자동)

- "공공 통계 기반 객관 빈도 라벨"
- "운명·길흉·사주와 인과관계 없음"
- 출처 명시 "통계청 2015"
- γ 학술 근거 명시

## 한계 (영구 기록)

- 15/30 PASS. 15 known-limitation (임계값 미세 조정 영역)
- γ=0.1은 보고서 §4 보수적 안 — 학파별 견해 (0.3 등) 채택 시 별도 ADR
- 한자 명시 입력 의무 X (옵셔널) — 한글만 입력 시 동음이의 최상위 우선
- 본 ADR은 **immutable**. ADR-029 supersede (확장 패턴)

## 관련

- 외부 보고서: [[../reports/korean-surname-300-algorithm-extension]]
- 본 작업 영속화: [[../done/korean-surname-300-extension]]
- 회귀: `engine/divination/test_name_uniqueness.py` (24/24 PASS)
- 데이터: `data/korean_surname_frequency.json` (300 entries)
- 직전 ADR: ADR-029 (15 entries, supersede)
