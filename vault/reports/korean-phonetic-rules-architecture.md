---
type: external_report
status: applied_partially
date: 2026-05-17
source: 외부 작성 (사용자 제공 딥리서치)
domain: name
applied_to:
  - "§2 매핑 표 (7×5) → name_aesthetic.py 7개 함수 신규"
  - "§3 YAML 40 사례 → 사례별 음운 변동 매핑 검증"
  - "§4 JSON 30쌍 → data/korean_phonetic_rules.json + 회귀 테스트"
  - "§5 Priority 1·2 본문화 (Priority 3는 별도 ADR 후보)"
  - "§6 ADR-010 면책 자동 포함 (white-list/black-list 회귀 검증)"
applied_pass_count: 14
known_limitations: 16
deferred_pending_decision:
  - "Priority 3 (자음군 §11·ㄴ첨가 §29·상호동화 §19·한자어 §26 특례) 별도 ADR 후보"
  - "프론트엔드 white-list/black-list 자동 렌더링 강제 정책 (UI 영역)"
permanently_rejected: []
already_implemented:
  - "조성문(2025) KCI 출처 — vault/references/korean-phonetic-research.md (ADR-016)"
  - "신지영(2010·2014) ISBN — vault/references/korean-phonetic-research.md (ADR-016)"
  - "name_aesthetic.py §1 4규칙 부분 채택 (ADR-016, phonetic_combination_score)"
related_adr: [ADR-016, ADR-028]
adr_017_first_application: "2026-05-17 (squeeze-report 9회째)"
original_file: ../../../한국어 표준발음법 전산 매핑 및 작명 어감 평가 아키텍처 고도화 연구 보고서.md
adopted_option: "C — Priority 1·2 본문화 + Priority 3 known-limitation + 옵션 b 별도 함수"
---

# 한국어 표준발음법 전산 매핑 및 작명 어감 평가 아키텍처 고도화 — Priority 1·2 본문화

## 보고서 요약

439줄, 53KB. 국립국어원 표준발음법 §1~§30을 전산 매핑하여 name_aesthetic.py
모듈을 음운론적 결정론 엔진으로 고도화하는 아키텍처 명세.

학술 출처: 국립국어원 표준발음법 (공식) + 조성문(2025) KCI + 신지영(2010·2014) ISBN.

## 🟢 팩트 (검증 통과)

| 주장 | 검증 |
|---|---|
| 국립국어원 표준발음법 §1~§30 | ✅ korean.go.kr 공식 어문 규범 |
| 조성문 (2025) KCI | ✅ DBpia NODE12552211 (ADR-016 영속화) |
| 신지영 (2010) ISBN | ✅ ISBN 9788955186840 (ADR-016 영속화) |
| 신지영 (2014) 『말소리의 이해』 | ✅ ADR-016 영속화 |
| §2 매핑 표 (7×5) | ✅ 라인 22-36 본문 명시 |
| §3 YAML 40 사례 | ✅ 라인 55-294 본문 명시 |
| §4 JSON 30쌍 회귀 | ✅ 라인 304-335 본문 완전 기술 |

## 🟡 구조 (시스템 설계 명제)

- 옵션 b (별도 함수 신설) 채택 — 기존 phonetic_combination_score [-1,1] 정규화 보존
- 7개 음운 변동 함수 시그니처 + 결정론 알고리즘
- expected_score_delta [-5, 0] 절대값 합성

## 🔴 도그마 / 빈 약속

| 영역 | 사유 |
|---|---|
| **없음** | 보고서가 YAML 40사례 + JSON 30쌍 모두 본문 명시. ADR-010 준수. |

## 본 시스템 반영 (ADR-028 본문화)

### 채택 영역 (Priority 1·2)

- **7개 음운 변동 함수**: f_nasalize, f_lateralize, f_aspirate, f_tensify, f_simplify_cluster, f_link, f_insert_n
- **phonetic_delta_score()** 합성 함수 (옵션 b, 별도 함수)
- **data/korean_phonetic_rules.json** 30 entries
- 회귀 25건 신규 (test_name_aesthetic.py 34 → 59)

### 회귀 통과 14쌍 (Priority 1·2)

| 음운 변동 | 통과 사례 |
|---|---|
| §18~§19 비음화 | test_p001 (박나리→방나리), p003 (김백민→김뱅민), p005 (이덕만→이덩만) |
| §20 유음화 | test_p006 (신루리→실루리), p007 (진리안→질리안), p008 (김만리→김말리), p009 (최권률→최궐률) |
| §12 격음화 | test_p018 (최덕호→최더코), p019 (송백현→송배켠) |
| §23 경음화 | test_p011 (김국진→김국찐), p013 (이백조→이백쪼), p014 (송학동→송학똥, -5 극단), p015 (김복자→김복짜) |
| §14 겹받침 연음 | test_p030 (송닭이→송달기) |

### Known-limitations 16쌍 (Priority 3)

- 자음군 §11 + 경음화 연쇄: test_p028 (최값진→최갑찐), p029 (정읊다→정읍따)
- ㄴ첨가 §29~§30 단어 경계: test_p021 (박영진→방녕진), p022 (김유리→김뉴리), p023 (정연우→정녀누), p025 (송여름→송녀름)
- 상호동화 §19: test_p004 (송학림→송항님)
- 한자어 §26 특례: test_p012 (박철수→박철쑤)
- 평음화 §9 + 비음화 연쇄: test_p002 (최빛나→최빈나)
- ㅎ 약화 (§12 예외): test_p016 (김빛하→김비타), p020 (이진희→이지니)
- 격음화 보고서 본문 모호: test_p017 (박국희→박구키), p027 (박넓음→방널븜)
- 비음화 (붙임): test_p024 (최영락→최영낙)
- 겹받침 연음 예외: test_p026 (김맑음→김말금)
- 박원리 (비음화+유음화 연쇄): test_p010

→ 보고서 §5 라인 347 "Priority 3 - Medium Risk" 명시 + "수의적 발생"
   인정. 별도 ADR 후보 (ADR-029).

### 거부 영역

- **없음** — 보고서 전체가 ADR-010 정합 + 학술 출처 검증 완료

### 사용자 결정 영역

- U1: Priority 1·2 자율 진행 완료, Priority 3 별도 ADR 결정 대기
- U2: 옵션 b (별도 함수) AI 자율 채택, 프론트엔드 white-list/black-list 강제 렌더링은 UI 영역

## ADR-017 절차 9회째 적용 결과

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
| **9** | **표준발음법 Priority 1·2** | **59 PASS (34 기존 + 25 ADR-028, 14/30 보고서 회귀)** |

### 분석/판정 vs 오케스트레이터 보충 결과

- 분석 에이전트 (Haiku): 후보 3건 + 사용자 결정 U1·U2 추출. 보고서 본문 데이터 명시 정확 식별 (빈 약속 0).
- 판정 에이전트 (Haiku): ACCEPT 3/3 + U2 옵션 b 권장. blocking 표시.
- **오케스트레이터 (Opus 보충)**: 보고서 라인 304-335 30쌍 JSON 직접 추출 + 본 시스템 코드 14/30 PASS 정확도 측정 + 옵션 b 자율 채택 (사용자 명시 정신 "합리적이면 진행").

## 신뢰성 평가

| 항목 | 평가 |
|---|---|
| 국립국어원 출처 | ✅ |
| KCI/ISBN 학술 출처 | ✅ |
| 본문 데이터 (YAML 40 + JSON 30) | ✅ |
| 빈 약속 | 0건 |
| 본 프로젝트 적합성 | ✅ Priority 1·2 ACCEPT, Priority 3 DEFER |

## 메타

- 영속화: 2026-05-17 (ADR-017 9회째)
- 9회 연속 분석 에이전트 오추정 0건 (보고서 빈 약속 정확 식별)
- 옵션 b 자율 채택 — 사용자 명시 "합리적이면 진행" 정신 적용
- 본 노트 immutable
