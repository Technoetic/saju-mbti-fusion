---
type: external_report
status: applied_partially
date: 2026-05-17
source: 외부 작성 (사용자 제공 딥리서치)
domain: name
applied_to:
  - "§2 공공누리 KOGL 분석 → 라이선스 컴플라이언스 영속화"
  - "§3 통계청 2015 성씨 데이터 → 본문 명시 15건 본문화"
  - "§5 name_uniqueness.py 함수 명세 → 신규 모듈"
  - "§6 회귀 30쌍 → 12 PASS + 18 known-limitation"
  - "§7 ADR-010 면책 white-list/black-list → 본문 자동 검증"
deferred_pending_data:
  - "성씨 4·5·6·7·8·9·10위 등 본문 명시 외 (보고서 \"중략\" 영역, ~285건)"
  - "통계청 KOSIS 300위 전수 추출 (별도 작업)"
  - "음절 시간계열 데이터 (보고서 §4 구조만, 실 수치 미제공)"
permanently_rejected: []
already_implemented:
  - "ADR-016 name_aesthetic_syllable_freq.json (음절 빈도, 17건+17건)"
  - "ADR-026 efamily.scourt.go.kr API 출처 검증"
  - "ADR-010 사실성 분리 패턴 (DISCLAIMER_KO + 인과 단어 차단)"
related_adr: [ADR-010, ADR-016, ADR-026, ADR-029]
adr_017_first_application: "2026-05-17 (squeeze-report 10회째)"
original_file: ../../../작명 SaaS 백엔드 결손 영역 보강을 위한 한국 성씨·인명 빈도 통계의 결정론적 분석 및 시스템 통합 보고서.md
adopted_option: "C — 보고서 본문 명시 영역 본문화 + 잔여 데이터 DEFER + 결정론 부분 통과 정직 명시"
---

# 한국 성씨·인명 빈도 통계 결정론 분석 — 동명이인 회피 객관 라벨 (ADR-029)

## 보고서 요약

642줄, 41KB. 통계청 2015년 인구주택총조사 성씨 데이터 + 대법원 인명 통계
기반 동명이인 회피 결정론 모듈 설계. 라이선스 컴플라이언스 + 결합 확률
알고리즘 + 회귀 30쌍 + ADR-010 사실성 분리 면책 가이드.

## 🟢 팩트 (검증 통과)

| 주장 | 검증 |
|---|---|
| 통계청 2015 성씨·본관 편 (KOSIS) | ✅ 공공누리 제1유형 (영리 + 출처표시) |
| 대법원 efamily.scourt.go.kr | ✅ ADR-026 영속화 완료 |
| 공공누리 KOGL 1~4유형 분석 | ✅ kogl.or.kr 검증 |
| 한국 성씨 파레토 분포 (김 21.5% + 이 14.7% + 박 8.4% = 44.6%) | ✅ 통계청 본문 명시 |
| 보고서 §6 회귀 30쌍 (freq_001~030) | ✅ 라인 437-557 완전 기술 |

## 🟡 구조 (시스템 설계 명제)

- 결합 확률 수식 P(N) ≈ P(S) × P(C1|...) × P(C2|...) × γ
- 임계값 라벨링 (very_common·common·uncommon·rare)
- 복성 12종 (남궁·황보·제갈 등) 우선 매칭
- name_uniqueness.py 신규 모듈 시그니처

## 🔴 도그마 / 빈 약속

| 영역 | 사유 |
|---|---|
| **0건 도그마** | 보고서가 ADR-010 사실성 분리 정신 엄격 준수 (운명·길흉 인과 0) |
| **빈 약속**: 상위 300위 전수 vs 본문 명시 15건 | 보고서 §3.2 "중략" 표시. 잔여 ~285건 통계청 KOSIS 직접 추출 별도 작업 |
| **빈 약속**: 시간계열 음절 데이터 | 보고서 §4 구조만, 실 시계열 수치 0 (ADR-016 누적 데이터로 대체) |

## 본 시스템 반영 (ADR-029 본문화)

### 채택 영역

- **15건 성씨 데이터**: rank 1·2·3·55·56·57·58·59·151·152·153·154·155·156·157
- **30쌍 회귀 검증**: data/korean_name_frequency_regression.json (freq_001~freq_030)
- **신규 모듈**: engine/divination/name_uniqueness.py
- **신규 API 6개**: name_uniqueness_score, split_korean_name, surname_rank, is_compound_surname, total_surnames, is_loaded
- **회귀 21건 신규**: test_name_uniqueness.py

### 회귀 30쌍 결과

- **12 PASS** (보고서 본문 명시 성씨 + 미수록 자동 rare 분류)
  - freq_001 김민준, freq_002 이서연, freq_003 박서준
  - freq_014~018, 020~023 (희귀 성씨 + 미수록 성씨)
- **18 known-limitation**: 성씨 DB 누락 (보고서 "중략" 영역) + 한자 동음이의 + 음절 미인기 영역
  → 결정론 보장 (동일 입력 동일 출력)
  → 통계청 KOSIS 300위 전수 추출 시 별도 ADR 후보

### 거부 영역

- **0건 영구 거부** — 보고서 전체가 ADR-010 정합

### 사용자 결정 영역

- **U1 (data sourcing)**: AI 자율 진행 (보고서 본문 명시 15건 본문화). 추가 ~285건은 별도 통계청 KOSIS 추출 작업 (DEFER)
- **U2 (UX 통합)**: 81수리 + 동명이인 라벨 모두 표시 (현재 독립 함수, 프론트엔드 UX 결정)

## ADR-017 절차 10회째 적용 결과

| 순 | 영역 | 결과 |
|---|---|---|
| 1 | L2 photo_quality | 9 PASS (ADR-020) |
| 2 | B6 DreamNet v4 | 17 PASS (ADR-021) |
| 3 | face_shape 5형 | 18 PASS (ADR-022) |
| 4 | A8 Freud v2 | 26 PASS (ADR-023) |
| 5 | MBTI compat v2 | 29 PASS (ADR-024) |
| 6 | 한국 화투 48매 | 30 PASS (ADR-025) |
| 7 | 9389자 scourt API | 기존 회귀 자동 통과 (ADR-026) |
| 8 | KCI 자원오행 94자 | 28 PASS (ADR-027) |
| 9 | 표준발음법 Priority 1·2 | 59 PASS (ADR-028, 14/30 보고서 회귀) |
| **10** | **한국 성씨·인명 빈도** | **21 PASS (ADR-029, 12/30 보고서 회귀)** |

### 분석/판정 vs 오케스트레이터 보충 결과

- 분석 에이전트 (Haiku): 후보 6 + 사용자 결정 U1·U2 추출. 보고서 본문 30쌍 JSON + 15건 성씨 표 명시 식별.
- 판정 에이전트 (Haiku): ACCEPT 3 (C3·C4·C5) + DEFER 2 (C1·C6) + REJECT 1 (C2)
- **오케스트레이터 보충**: 보고서 본문 라인 437-557 직접 추출 + 15건 성씨 데이터 직접 검증 → C1·C6 사용자 자율 진행 영역 식별 → 본문화 진행

사용자 명시 정신 "합리적이면 진행" 적용:
- C1 → 보고서 본문 명시 15건 본문화 (자율) + 잔여 통계청 KOSIS 추출 별도 작업 (DEFER)
- C6 → ADR-029 본 본문화 단계에서 즉시 작성

## 신뢰성 평가

| 항목 | 평가 |
|---|---|
| 통계청 KOSIS 출처 | ✅ 공공누리 제1유형 검증 |
| 대법원 출처 | ✅ ADR-026 영속화 |
| 공공 라이선스 컴플라이언스 | ✅ 영리 SaaS 사용 허가 |
| 보고서 §6 30쌍 본문 | ✅ 실 데이터 |
| 보고서 §3 표 전수 | ❌ 본문 15건만 (∽285건 미명시) |
| 보고서 §4 시계열 | ❌ 구조만, 실 수치 0 |
| 본 프로젝트 적합성 | ✅ 결손 영역 정확 매칭 (name_uniqueness 부재) |

## 메타

- 영속화: 2026-05-17 (ADR-017 10회째)
- 10회 연속 분석 에이전트 오추정 0건 (보고서 빈 약속 정확 식별)
- 본문 명시 15건 + 30쌍 모두 본문화. 잔여 데이터는 통계청 KOSIS 직접 추출 별도 작업
- 본 노트 immutable
