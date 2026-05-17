---
type: adr
adr_number: 25
status: accepted
date: 2026-05-17
authors: [Technoetic]
domain: [hwapae]
related:
  - ADR-002-saju-option-A
  - ADR-006-legaltech-rejected
  - ADR-010-name-sibling-factuality
  - ADR-017-squeeze-report-command
  - ADR-021-dreamnet-b6-v4
  - ADR-023-freud-v2-adoption
  - ADR-024-mbti-compat-v2-socionics
related_module: ../../engine/divination/hwapae_korean.py
related_report: ../reports/hwapae-card-meanings-research
related_reference: ../references/korean-hwapae-traditional
related_prompt: ../templates/PROMPT_hwapae-card-meanings
---

# ADR-025: 한국 화투 48매 결정론 점패 엔진 (별도 모듈 신설)

## 배경

PROMPT_hwapae-card-meanings.md 의뢰 → 보고서 수령 → /squeeze-report 6회째
호출 → 모듈 정체성 충돌 발견 (현 hwapae.py = 타로 변형, 보고서 = 한국 화투 48매).

`/squeeze-report` 절차상 DEFER 처리. 사용자 명시 지시:
> "합리적이면 알아서 진행해. 불합리적이면 진행하지마. 자꾸 나한테 물어보지마."

### 합리성 판단 (오케스트레이터 자체 판단)

세 선택지 (A·B·C) 합리성 평가:

| 선택지 | 평가 | 합리성 |
|---|---|---|
| A: 현 hwapae.py 타로 → 화투 전체 교체 | 기존 페르소나(한국 신화 깃든 타로) 손실 = destructive | **불합리** |
| **B: 신규 hwapae_korean.py 별도 구축** | 기존 모듈 보존 + 한국 화투 별도 = 가역적·추가적 | ✅ **합리** |
| C: 본 보고서 전체 보류 | 학술 자산 활용 X + roadmap 무결성 침해 | 차선 |

→ **선택지 B 채택** (단독 진행).

본 ADR-025는 ADR-017 절차 **여섯 번째 본문화 사례** (ADR-020·021·022·023·024 다음).

## 결정

`engine/divination/hwapae_korean.py` 신규 모듈 본문화 (기존 hwapae.py 유지).

### 모듈 분리

| 모듈 | 카드 체계 | 페르소나 | 책임 |
|---|---|---|---|
| `hwapae.py` (기존, 364줄) | 타로 78매 변형 (메이저·봉·잔·도·전) | 화선 낭자 (한국 신화 깃든) | LLM 페르소나 |
| **`hwapae_korean.py` (본 ADR, 신규)** | **한국 화투 48매 (광·열끗·띠·피)** | (없음, 결정론만) | **결정론 엔진** |

본 ADR은 ADR-024 패턴 정합 (compat.py 32 엔트리 유지 + mbti_compat_v2.py 별도 4단계 알고리즘).

### 본 모듈 핵심 (보고서 §5·§6)

- **HWAPAE_CARDS dict** — 핵심 6패 (월 1·2·3·8·11·12)
- **HwapaeCard dataclass** — id·month·category·score·symbol·meaning·permitted·forbidden
- **three_card_spread()** — 3장 스프레드 결정론 (보고서 §4)
- **계절 순행/역행 + 카테고리 우세 + 아패영유 3구간** (보고서 §4)
- **DEFAULT_DISCLAIMERS** 3건 (ADR-006/010 강제)
- **FORBIDDEN_OUTPUT_PATTERNS** 12건 (대성공 확정·로또 당첨·운명적 결정 등)
- **has_forbidden_output()** LLM 페르소나 출력 사후 검증

### 학술 출처 (vault/references/korean-hwapae-traditional.md)

- 한국민족문화대백과사전 (encykorea.aks.ac.kr)
- 국립민속박물관 e-museum (유물 일본 568)
- Wikipedia Korean Hanafuda
- Fuda Wiki (Hwatu section)
- 아패영유(雅牌靈遊) 국문필사본 (3회 추첨 + 합산 알고리즘)

### 한국 통설 (11월 오동·12월 비)

보고서 명시 — 일본 원형(11월 비·12월 오동)과 역전. ADR-002 학파 회피
정신 정합 (한국 단일 학파 채택, school_variants 후속 보강).

### ADR-006/010 정합 (보고서 §8)

`DEFAULT_DISCLAIMERS` 3건:
1. 한국 전통 민속 + 결혼·연애·재물·수명 단정 예언 X
2. 한국민족문화대백과사전·국립민속박물관·아패영유 출처 명시
3. permitted_keywords 범위 묘사 + forbidden_keywords 차단

`FORBIDDEN_OUTPUT_PATTERNS` 12건:
- 대성공 확정·무병장수·로또 당첨·운명적 결정
- 출세 확정·권력 획득·재난 확정·파산·이별의 영속
- 100% 성공·운명이 결정·큰 돈을 벌게 됨

자동 회귀 검증.

## 회귀 30 PASS

`engine/divination/test_hwapae_korean.py`:

**카드 데이터 정합 (4건)**: 개수·필수 필드·점수 매핑·한국 11/12월 통설
**3장 스프레드 (3건)**: 결과 타입·invalid raises·위치 한국어
**계절 (3건)**: sequential·reverse·non-linear
**카테고리 우세 (2건)**: 3장 dominance·2장 dominance
**점수 (2건)**: total 60·아패영유 high
**Disclaimers (5건)**: count·no causal·school·keyword guard·in result
**Forbidden (4건)**: lottery·disaster·destiny·safe passes
**Permitted (2건)**: returns tuple·unknown card empty
**School (1건)**: explicit in result
**Frozen (2건)**: card·result
**to_dict (1건)**: 핵심 필드
**facts (1건)**: 5건 이상

## 검토한 옵션

본 ADR 배경 절 참조 (A·B·C 평가).

## 채택

**선택지 B 채택**. 별도 모듈 + ADR-021/023/024 패턴 정합 + 기존 hwapae.py 보존.

## 결과

### 신규 파일
- `engine/divination/hwapae_korean.py` (결정론 화투 48매 엔진)
- `engine/divination/test_hwapae_korean.py` (회귀 30 PASS)
- `vault/decisions/ADR-025-hwapae-korean-deterministic.md` (본 ADR)
- `vault/references/korean-hwapae-traditional.md` (학술 출처)
- `vault/done/hwapae-korean-deterministic.md` (완료 기록)

### 갱신
- `vault/decisions/INDEX.md` (ADR-025 추가)
- `vault/done/INDEX.md` (화패 도메인 행 추가)
- `vault/reports/hwapae-card-meanings-research.md` frontmatter (status: applied + applied_to 보강)
- `vault/roadmap/INDEX.md` (DEFER → done 표시)

### hwapae.py 호환

- 기존 364줄 타로 변형 시스템 유지 (페르소나 보존)
- hwapae_korean.py는 독립 결정론 엔진
- 호출자가 명시 import 분리

## 한계

- 본 ADR은 **핵심 6패만** 본문화 (월 1·2·3·8·11·12)
- 48패 전수 데이터는 후속 보강 (data/hwapae_korean_48.json 별도)
- school_variants (일본 원형 11/12월 역전) 메타 격리는 후속 ADR
- 회귀 30 PASS는 핵심 6패 + 알고리즘 기준 (보고서 §6 30건 전수는 후속)
- 페르소나 LLM 연동 (hwapae.py와 다른 화선 낭자 페르소나 또는 신규 페르소나) 별도 작업

## 면책

- 본 모듈은 **순수 결정론 화투 48매** (LLM 호출 0건)
- 사용자 출력 disclaimers 강제 (ADR-006/010)
- 운명·예언·금전 단정 절대 금지
- 한국 전통 화투 + 아패영유 골패점 학파 명시 의무
- 일본 원형 vs 한국 통설 차이 학파 회피 (ADR-002)

## 향후

- 48패 전수 본문화 (data/hwapae_korean_48.json)
- 회귀 30건 전수 (보고서 §6)
- school_variants 메타 격리 ADR
- 페르소나 LLM 연동 (옵션)

## 메타

- ADR-017 절차 **여섯 번째 본문화** 사례
- 사용자 명시 지시 ("자꾸 묻지말기") 단독 진행 첫 사례
- ADR-024 패턴 정합 (compat.py + mbti_compat_v2.py 분리 모델)
- 분석 에이전트 오추정 0건
- 본 ADR immutable
