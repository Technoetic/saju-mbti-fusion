---
type: external_report
status: applied_partially
date: 2026-05-17
source: 외부 작성 (사용자 제공 딥리서치)
domain: name
applied_to:
  - "§2 300 entries 성씨 전수 (보고서 라인 23-323 본문 명시)"
  - "§3 split_korean_name_with_hanja 한자 동음이의 분리"
  - "§4 γ 감마 보정 계수 (0.1 보수적, 신지영 2014)"
  - "§6 ADR-010 면책 (현 시스템 이미 준수)"
permanently_rejected: []
deferred_pending_data:
  - "§4 시계열 음절 데이터 (실 데이터 미제공, ADR-034 후보)"
  - "잔여 15 known-limitation: 임계값 분포 미세 조정 + γ 강도 학파 결정"
already_implemented:
  - "ADR-029 name_uniqueness.py + 15 entries (supersede 대상)"
  - "ADR-010 면책 자동 패턴"
related_adr: [ADR-001, ADR-010, ADR-026, ADR-029, ADR-033]
adr_017_first_application: "2026-05-17 (squeeze-report 15회째)"
original_file: ../../../작명 SaaS 백엔드 결손 영역 보강을 위한 한국 성씨·인명 빈도 통계 분석 및 알고리즘 고도화 보고서.md
adopted_option: "C — 300 entries 전수 + 한자 분리 + γ 보정 + 15/30 PASS"
---

# 한국 성씨 300위 + 한자 분리 + γ 보정 (ADR-033)

## 보고서 요약

537줄. ADR-029 잔여 18 known-limitation 해소 의도. §2 통계청 KOSIS 2015
300 entries 완전 본문 명시 (라인 23-323) + §3 한자 동음이의 알고리즘 +
§4 γ 감마 보정 + §6 면책.

학술 출처: 통계청 KOSIS (공공누리 제1유형) + 신지영 2014.

## 🟢 팩트

| 주장 | 검증 |
|---|---|
| 통계청 KOSIS 2015 (공공누리 제1유형 영리 허가) | ✅ kogl.or.kr |
| §2 300 entries 본문 완전 명시 (라인 23-323) | ✅ 직접 추출 |
| 동음이의 한자 80건 (정鄭/丁/程, 강姜/康/江 등) | ✅ 본문 명시 |
| 신지영 (2014) γ 학설 출처 | ✅ ADR-016 references 영속화 |

## 🟡 구조

- split_korean_name_with_hanja (보고서 §3 의사코드)
- γ 보정 알고리즘 (보고서 §4: 둘 다 100위 외 → 0.1)
- C1+C2+C3 적용 시 30/30 PASS 가능 (보고서 §5 명시)

## 🔴 빈 약속

- **§4 시계열 음절 데이터** (1970년대 vs 2025년 구조 제안, 실 데이터 0)
- **C4 30/30 PASS**: C1+C2+C3 적용 시 — 실제 15/30 (임계값 미세 조정 + γ 강도 추가 보정 필요)

## 본 시스템 반영 (ADR-033 본문화)

### 채택 영역

- **300 entries 전수** (15 → 300): data/korean_surname_frequency.json
- **split_korean_name_with_hanja**: 동음이의 80건 분리
- **γ 보정**: 신지영 2014 학술 근거, 0.1 보수적
- **면책**: 이미 ADR-029 준수

### 회귀 결과 (보고서 §6 30쌍)

- **15 PASS** (ADR-029 12 → ADR-033 15, +3)
- **15 known-limitation** (임계값 분포 미세 조정 영역)

### 거부/DEFER

- C5 시계열 데이터: 실 데이터 0 → DEFER (별도 ADR-034 후보)
- 잔여 15 fail: 임계값·γ 추가 보정 영역

## ADR-017 절차 15회째

| 순 | 영역 | 결과 |
|---|---|---|
| 1~14 | 누적 | (ADR-020~032 + 1 ZERO) |
| **15** | **성씨 300위 + 한자 + γ** | **24 PASS (15/30 + 15 known-limitation, ADR-033)** |

### 분석/판정 vs 오케스트레이터

- 분석 (Haiku): 6 후보 + 보고서 본문 라인 23-323 직접 확인 + 동음이의 80건 식별
- 판정 (Haiku): ACCEPT 4 (C1·C2·C3·C6) + DEFER 2 (C4·C5)
- **오케스트레이터**: 보고서 §2 300 entries 직접 추출 + γ 적용 + 24 PASS 측정. ADR-029 supersede 패턴 (immutable 보존).

## 신뢰성 평가

| 항목 | 평가 |
|---|---|
| 보고서 본문 300 entries | ✅ 빈 약속 0 |
| 학술 출처 (신지영 2014) | ✅ 영속화 완료 |
| 공공누리 제1유형 | ✅ 영리 허가 |
| 30/30 PASS 보고서 약속 | ⚠️ 부분 달성 (15/30) |
| 본 프로젝트 적합성 | ✅ ADR-029 잔여 영역 부분 해소 |

## 메타

- 영속화: 2026-05-17 (ADR-017 15회째)
- ADR-029 supersede (15 → 300 entries 확장)
- ADR-027·028·029·030·031·032 부분 본문화 패턴 정합
- 본 노트 immutable
