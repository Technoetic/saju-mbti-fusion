---
type: done
status: applied
date: 2026-05-17
domain: [name]
adr: ADR-033-korean-surname-300-extension
related_report: reports/korean-surname-300-algorithm-extension
supersedes_done: korean-name-uniqueness (ADR-029)
---

# 한국 성씨 300위 확장 + 한자 분리 + γ 보정 (ADR-033)

## 작업 요약

ADR-029 (15 entries) 확장. 외부 보고서 537줄 §2~§6 본문화. 300 entries
전수 (보고서 §2 라인 23-323) + 한자 동음이의 분리 + γ 감마 보정. 회귀
15/30 PASS (이전 12 → 15, +3).

ADR-017 절차 **열다섯 번째 본문화 사례**.

## 변경 사항

### 데이터 (확장)

- [data/korean_surname_frequency.json](../../data/korean_surname_frequency.json):
  - 15 → **300 entries** (보고서 §2 라인 23-323 전수)
  - 통계청 KOSIS 2015 (공공누리 제1유형)
  - 동음이의 한자 80건 (방方/龐, 정鄭/丁/程, 강姜/康/江 등)

### 코드 (확장)

- [engine/divination/name_uniqueness.py](../../engine/divination/name_uniqueness.py): 3 신규 API
  - `split_korean_name_with_hanja(name_kr, hanja_name)` — 동음이의 정확 분리
  - `_apply_gamma_penalty(first_rank, last_rank)` — γ 0.1/1.0 보정
  - `_load_surname_db_by_hanja()` — 한자 인덱스
  - `GAMMA_BOTH_LOW_RANK = 0.1` / `GAMMA_DEFAULT = 1.0`

### 회귀 테스트

- [engine/divination/test_name_uniqueness.py](../../engine/divination/test_name_uniqueness.py) — **24/24 PASS**
  - 21 기존 + 3 신규 (top 10 ADR-033, split_with_hanja, gamma_penalty)
  - 30쌍 보고서 §6: **15 PASS** + 15 known-limitation

### 신규 ADR

- [vault/decisions/ADR-033-korean-surname-300-extension.md](../decisions/ADR-033-korean-surname-300-extension.md)

### 신규 보고서

- [vault/reports/korean-surname-300-algorithm-extension.md](../reports/korean-surname-300-algorithm-extension.md)

## 회귀 30쌍 PASS 변화

### ADR-029 (12 PASS) → ADR-033 (15 PASS), +3

신규 PASS:
- **freq_010 임도현** (10위 임 본문화) → common ✅
- **freq_019 방(龐)지훈** (한자 분리) → rare ✅
- **freq_030 임하늘** (10위 임 본문화) → common ✅

### 15 known-limitation

- freq_004~009: 임계값 분포 (got common, expected very_common) — 6건
- freq_011·012·013: 음절 미인기 + γ 추가 강화 필요 — 3건
- freq_024·025·026: γ 적용 후 still 임계값 초과 — 3건
- freq_027·028·029: 음절 미인기 결합 — 3건

→ 별도 ADR-034 후보 (임계값 분포 보정 + γ 강도 학파 결정)

## 라이브 검증 예시

```python
>>> from engine.divination.name_uniqueness import (
...     name_uniqueness_score, split_korean_name_with_hanja, surname_rank
... )
>>> surname_rank("최")  # ADR-029 None → ADR-033 4
4
>>> split_korean_name_with_hanja("방지훈", "龐志訓")
('방', '龐', '지훈')
>>> r = name_uniqueness_score("임도현", gender="male")
>>> r.combined_frequency
'common'
```

## ADR-010 사실성 분리

- ✅ 통계청 KOSIS 공공누리 제1유형 출처
- ✅ 신지영 (2014) γ 학설 근거
- ✅ 면책 자동 (rationale에 운명·인과 단어 0)
- ✅ 결정론 보장
- ✅ 한자 옵셔널 (한글 입력 시 최상위 우선 fallback)

## 향후 작업

- 잔여 15 known-limitation: 임계값 분포 보정 (별도 ADR)
- γ 강도 학파별 비교 (0.1 vs 0.3, 사업 결정)
- 시계열 음절 데이터 (ADR-034 후보)
- UX: 한자 입력 UI (사업 단계)

## 메타

- ADR-017 열다섯 번째 본문화
- ADR-029 supersede (15 → 300 entries, immutable 보존)
- 부분 본문화 + known-limitation 정직 명시 패턴 일관 (ADR-027·028·029·032)
- 본 노트 immutable
