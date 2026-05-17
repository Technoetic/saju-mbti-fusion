---
type: adr
adr_number: 24
status: accepted
date: 2026-05-17
authors: [Technoetic]
domain: [saju, mbti]
related:
  - ADR-002-saju-option-A
  - ADR-006-legaltech-rejected
  - ADR-010-name-sibling-factuality
  - ADR-014-saju-mbti-prediction-exception
  - ADR-015-saju-option-B-eokbu
  - ADR-017-squeeze-report-command
  - ADR-021-dreamnet-b6-v4
  - ADR-023-freud-v2-adoption
related_module: ../../engine/saju/mbti_compat_v2.py
related_report: ../reports/mbti-gunghap-academic-validation
related_reference: ../references/jung-myers-keirsey-socionics
related_prompt: ../templates/PROMPT_gunghap-mbti-matrix-academic
---

# ADR-024: MBTI 16×16 호환 매트릭스 v2 — 결정론 4단계 알고리즘 + Socionics

## 배경

`engine/saju/compat.py` 라인 8 명시 "MBTI 16×16 호환 매트릭스 (간이 —
인지 기능 거울/짝 기준)" 의 학술 출처 부재 결손.

PROMPT_gunghap-mbti-matrix-academic.md 의뢰 → 보고서 수령 → /squeeze-report:
- 분석 에이전트 (Haiku): 후보 7건
- 판정 에이전트 (Haiku): ACCEPT 6건 + DEFER 1건 (회귀 빈 약속)
- 오케스트레이터 (Opus): 본문화

본 ADR-024 = ADR-017 절차 **다섯 번째 본문화 사례**:
- ADR-020 L2 photo_quality (회귀 9 PASS)
- ADR-021 B6 DreamNet v4 (회귀 17 PASS)
- ADR-022 face_shape 5형 (회귀 18 PASS)
- ADR-023 A8 Freud v2 (회귀 26 PASS)
- **ADR-024 MBTI compat v2 (회귀 29 PASS) ← 본 ADR**

## 결정

`engine/saju/mbti_compat_v2.py` 신규 모듈 본문화. 기존 `compat.py` 라인
87-108 `_MBTI_PAIR_SCORE` 32 엔트리는 유지 (호환성). 본 v2는 별도 모듈로
256 전수 + 학파 명시 결정론 알고리즘 제공.

### 4단계 알고리즘 (보고서 §5.1)

```
score = max(1, min(9, base + sn_bonus + socionics_bonus + keirsey_bonus))
```

| 단계 | 가중치 | 학술 근거 |
|---|---|---|
| 1. base | 5 | 중립 시작점 |
| 2. S/N 동기화 | +2 (공유) 또는 -1 (다름) | 윤호균·이선희 (2000) KCI |
| 3. Socionics 관계 | dual+4 / activation+3 / mirror+2 / identity+1 / super_ego-2 / conflict-4 | Aushra Augusta 14 Intertype |
| 4. Keirsey 보너스 | N 공유 + T/F 역전 + J/P 역전 → +1 | Please Understand Me II |

### 관계 분류 (보고서 §3.3)

- **Dual** (짝, +4): 주기능 ↔ 열등기능 매핑, E/I 다르되 J/P 공유 (예: INTJ-ESFP)
- **Activation** (활동, +3): Dual과 기능 공유 + E/I만 동일
- **Mirror** (거울, +2): 동일 쿼드라 (4 인지기능 공유 + 주/부 역전, 예: INTP-ENTP)
- **Identity** (동일, +1): 같은 16 유형
- **Super-Ego** (초자아, -2): 인지기능 역방향
- **Conflict** (갈등, -4): 인지기능 스택 완전 불일치 (예: INTP-ESFP)
- **Neutral** (0): 위 분류 외

### 256 매트릭스 사전 연산 (선택)

`precompute_matrix()` — 16×16 = 256 엔트리 메모리 캐싱. O(1) 조회.

### ADR-014 경계 명확화

본 모듈 입력 시그니처: `compute_mbti_compat(a: str, b: str)` — 사용자
명시 두 MBTI 유형만. 사주 입력 0건. 따라서 **사주→MBTI 단정 예측과
무관** (ADR-014 영구 금지 영역 외).

`saju → mbti_compat_v2` 호출 경로는 사주_mbti_predictor(ADR-014) → 4축
경향성 → 사용자 확인 → 본 모듈 별개. 구조적 단정 차단.

### ADR-006/010/014 정합 (DEFAULT_DISCLAIMERS 3건)

1. "본 호환 점수는 융(Jung)의 인지기능 스택 이론 및 Socionics 관계론에
   기반한 학술적 추정치이며 결혼·연애 결정 자문이 아닙니다."
2. "MBTI는 자기보고식 검사로 학계 재현성·구성 타당도 논쟁이 있습니다
   (NEO-PI-R·Big5 대비)."
3. "실제 대인 관계는 자아존중감·의사소통 노력·환경 변수 등 다중 요인의
   영향을 받으며 본 지표를 맹신해서는 안 됩니다."

회귀 자동 검증:
- 학파 명시 (Jung·Socionics·Keirsey)
- MBTI 학계 한계 명시 (자기보고·재현성·논쟁)
- 다중 요인 명시 (환경·요인 키워드)
- 인과 단정 표현 0건 (당신은 [질병]·운명적으로·예언합니다)

## 회귀 29 PASS

`engine/saju/test_mbti_compat_v2.py`:

**입력 검증 (3건)**: 16 유형·잘못된 유형 거부·소문자 정규화
**관계 분류 (6건)**: identity·dual·mirror×2·conflict×2
**4단계 알고리즘 (3건)**: result type·score 1~9 (256 조합 전수)·invalid raises
**보고서 §5.1 예시 (4건)**: INTJ-ENFP Keirsey·INTJ-ESFP dual·INTP-ESFP conflict·INTJ-INTJ identity
**대칭 행렬 (1건)**: compute(a,b) == compute(b,a)
**256 매트릭스 (2건)**: size·all valid scores
**DEFAULT_DISCLAIMERS (6건)**: count·school·no causal·MBTI limit·multi factor·in result
**ADR-014 경계 (1건)**: no saju params
**학파 명시 (1건)**: school in result
**Frozen (1건)**: dataclass immutable
**to_dict (1건)**: components 분해

## 검토한 옵션

### A. 별도 모듈 mbti_compat_v2.py (채택)

- 장점:
  - 기존 compat.py 32 엔트리 호환 유지
  - 4단계 알고리즘 + 학파 명시 + DEFAULT_DISCLAIMERS
  - 256 전수 + 대칭 행렬 보장
  - ADR-021/023 패턴 정합
- 단점: 호출자가 v2 명시 import 필요

### B. compat.py 직접 보강

- 장점: 1모듈 통합
- 단점:
  - "간이" 라인 8 명시 제거 시 sajupy 호환성 변화
  - 32 엔트리 하드코딩과 4단계 알고리즘 책임 혼재
  - 별도 호출 경로 (saju + MBTI compat) vs 사용자 직접 입력 MBTI 모호

### C. compat.py 완전 교체

- 장점: 중복 제거
- 단점:
  - 기존 32 엔트리 사용 호출자 영향
  - 사주 계산 (5합·4충·오행 분포)와 MBTI 매트릭스 책임 분리 위반

## 채택

**A 채택**. 별도 모듈 + ADR-021/023 패턴 정합 + ADR-014 경계 명확화.

## 결과

### 신규 파일
- `engine/saju/mbti_compat_v2.py` (결정론 4단계 알고리즘)
- `engine/saju/test_mbti_compat_v2.py` (회귀 29 PASS)
- `vault/decisions/ADR-024-mbti-compat-v2-socionics.md` (본 ADR)
- `vault/references/jung-myers-keirsey-socionics.md` (학술 출처)
- `vault/reports/mbti-gunghap-academic-validation.md` (사실성 분리 결과)
- `vault/done/saju-mbti-compat-v2.md` (완료 기록)

### vault 영속화
- `vault/decisions/INDEX.md` (ADR-024 추가)
- `vault/done/INDEX.md` (사주 도메인 행 추가)

### compat.py 호환
- 라인 87-108 `_MBTI_PAIR_SCORE` 32 엔트리 유지 (호환성)
- 호출자가 v2 사용 원할 시: `from engine.saju.mbti_compat_v2 import compute_mbti_compat`
- v1 → v2 전환은 별도 작업 (옵션)

## 한계

- 보고서 §8 회귀 30쌍 JSON 빈 약속 → 본 모듈 자체 회귀 29건으로 대체
- Socionics 학파 차이 (Aushra·Vaisband·Gulenko) — 본 시스템은 Aushra 채택
- KCI 4건 라이브 검증 일부 보류 (보고서 본문 URL 명시 신뢰)
- compat.py v1과 v2 통합 호출은 별도 작업
- 운영 데이터 누적 후 매트릭스 보정 별도 ADR

## 면책

- 본 모듈은 **결정론 100%** (LLM 호출 0건)
- 사용자 출력 disclaimers 강제 (ADR-006/010/014)
- 정확도 표시 금지 (자기실현적 예언 회피, 보고서 §7.1)
- 학파 명시 의무 (Jung·Socionics·Keirsey)
- MBTI 학계 재현성 논쟁 명시 의무
- ADR-014 경계: 사용자 명시 두 MBTI 입력만 (사주→MBTI 단정 X)

## 향후

- compat.py v1 + v2 통합 호출 (옵션)
- 매트릭스 YAML 외부 영속화 (옵션, 현재는 코드 내장)
- 운영 데이터 누적 후 매트릭스 보정 (post_traffic ADR)
- KCI 4건 표본 크기·p-value 추가 영속화

## 메타

- ADR-017 절차 **다섯 번째 본문화** 사례
- 분석 에이전트 오추정 0건 (실 코드 직접 확인)
- ADR-021/023 패턴 정합 (DEFAULT_DISCLAIMERS + 학파 명시 + 회귀 자동 검증)
- 본 ADR immutable
