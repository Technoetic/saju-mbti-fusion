---
type: prompt_template
target: deepresearch
purpose: 한국어 표준발음법 완전 매핑 — 작명 음운 규칙 정밀화
created: 2026-05-17
related_module: engine/divination/name_aesthetic.py
related_adr:
  - ADR-010-name-sibling-factuality (사실성 분리)
  - ADR-016-name-aesthetic-partial (어감 §2만 채택, §1 음운 결손)
priority: medium
status: draft
---

# 딥리서치 프롬프트 — 한국어 표준발음법 작명 적용

## 사용법

본 프롬프트는 `engine/divination/name_aesthetic.py`의 음운 규칙 결손 보강용.
현 구현은 연음(linking) 일부만 처리. 비음화·격음화·경음화·ㄴ첨가 등
한국어 표준발음법 §1~§30 전체를 작명에 적용하는 결정론 규칙 필요.

조성문(2025)·신지영(2010) 외 추가 학술 출처 + KCI 검증 의무.

---

## 프롬프트 본문

```
한국어 표준발음법 §1~§30 전체를 한국 인명 작명에 적용하는 결정론
음운 규칙을 조사·정리해주세요. 본 자료는 운세 SaaS 백엔드의
작명 어감 점수 계산용이며, 사용자 출력 면책 의무를 동반합니다.

### 요구사항

#### 1. 표준발음법 §1~§30 완전 매핑

각 조항별로:
- 조항 번호 + 원문
- 적용 조건 (자모 결합·위치·환경)
- 결정론 규칙 (입력→출력 함수)
- 작명 시 발생 빈도 (인명용 한자 9,389자 + 한글 음절 11,172자 기준)

대상 음운 현상:
- 연음(linking) — §13~§16
- 비음화(nasalization) — §18~§19
- 유음화(lateralization) — §20
- 격음화(aspiration) — §12
- 경음화(tensification) — §23~§28
- ㄴ첨가(n-insertion) — §29~§30
- 자음군 단순화(cluster simplification) — §10~§11
- 두음법칙 — §5 (이미 본 시스템 반영)

#### 2. KCI/RISS 학술 출처 라이브 검증

각 규칙별 학술 근거:
- 조성문(2025) 외 KCI 등재 한국어 음운론 논문
- 신지영(2010) 한국어 음운론 표준 교재
- 한국어교육학회·국어학회 등재 논문

가짜 인용 절대 금지. 모든 인용은 KCI URL 또는 ISBN으로 라이브 검증
가능해야 함.

#### 3. 작명 적용 사례

각 음운 규칙별 작명 적용 사례 5건 이상:

```yaml
rule: "비음화 §18"
condition: "받침 ㄱ/ㄷ/ㅂ + 첫소리 ㄴ/ㅁ"
input_example: "박나리"
phonetic_output: "방나리"
naming_impact:
  - aesthetic_score_delta: "-2"  # 어색함 페널티
  - reason: "표기와 발음 괴리"
references:
  - "조성문(2025) KCI URL"
```

#### 4. 회귀 테스트 데이터셋

본 시스템 회귀 검증용 입력→출력 30쌍:

```json
[
  {
    "id": "phonetic_001",
    "input_name": "박나리",
    "expected_phonetic": "방나리",
    "rule_applied": "표준발음법 §18 비음화",
    "expected_score_delta": -2
  }
]
```

#### 5. 본 시스템 결손 영역 점검

현 `name_aesthetic.py` (34 tests)의 처리 현황:
- ✅ 연음 일부
- ❌ 비음화·격음화·경음화 미처리
- ❌ ㄴ첨가 미처리
- ❌ 자음군 단순화 미처리

각 미처리 영역의 작명 영향도 평가 + 우선순위 추천.

#### 6. 사용자 출력 면책

작명 결과에 음운 규칙 적용 시 사용자 출력 표현 가이드:
- ✅ "박나리는 표준발음법상 '방나리'로 발음됩니다."
- ❌ "박나리는 발음이 어색해서 운이 나쁩니다." (인과 도그마)
- ❌ "방나리로 발음되니 길합니다." (학파 도그마)

### 출력 형식

1. **표준발음법 §1~§30 완전 매핑 표**
2. **학술 출처 표** (KCI URL·DOI 라이브 검증)
3. **작명 적용 사례 YAML** (규칙별 5건)
4. **회귀 데이터셋 JSON** (30쌍)
5. **결손 영역 우선순위 추천**
6. **사용자 출력 면책 가이드라인**

### 검증 기준

- 모든 학술 인용 KCI/RISS 라이브 검증 가능
- 가짜 인용 0건
- 회귀 데이터셋 30쌍 이상
- 인과 도그마 표현 0건

위 조건 미충족 시 ADR-010 사실성 분리에 따라 거부됩니다.
```

---

## 본 시스템 채택 절차

1. `/squeeze-report` 사실성 분리
2. 학술 인용 KCI 라이브 검증
3. ACCEPT 후보:
   - `engine/divination/name_aesthetic.py` 보강 (§18·§20·§23 등 추가)
   - 회귀 +30건
   - `data/korean_phonetic_rules.json` 신규
   - vault/references/ 학술 출처 영속화

## 면책

- ADR-010 사실성 분리 의무
- 음운 어색함 → 인과 길흉 표현 금지
- 사용자 출력 면책 자동 포함
