---
type: prompt_template
target: deepresearch
purpose: A8 Freud v2 — 고전 정신분석 꿈해석 결정론 매핑 (현재 TODO)
created: 2026-05-17
related_module: engine/agents/freud_persona.py (v1 존재) + engine/agents/__init__.py (A8 v2 TODO)
related_adr:
  - ADR-002-saju-option-A (학파 회피 정신 — 학파 명시 채택 패턴 ADR-015 적용)
  - ADR-006-legaltech-rejected (자문 거절)
  - ADR-010-name-sibling-factuality (사실성 분리)
priority: medium
status: draft
---

# 딥리서치 프롬프트 — A8 Freud v2 (고전 정신분석 꿈해석 보강)

## 사용법

본 프롬프트는 본 시스템 꿈해석 멀티에이전트 오케스트레이터의 명시 TODO
영역 보강용. `engine/agents/__init__.py` 라인 명시:

```
A8 freud (v2)              (TODO)
```

v1 (`engine/agents/freud_persona.py`)은 단순 페르소나 응답 수준. v2는
고전 정신분석 (응축·전치·상징화·이차 가공) 결정론 매핑 + LLM 풀이
분리 패턴으로 보강 필요.

ADR-015 패턴 적용: 단일 학파(Freud) 명시 채택 + 다른 학파(Jung·Hobson 등)는
별도 에이전트 분리.

---

## 프롬프트 본문

```
지그문트 프로이트 《꿈의 해석》(Die Traumdeutung, 1900) 고전 정신분석
꿈해석 체계를 결정론 매핑 데이터로 조사·정리해주세요. 본 자료는 꿈해석
SaaS 백엔드의 학파 분리 에이전트(A8 Freud v2) 보강용이며, ADR-015
옵션 B 병행 패턴을 따라야 합니다.

### 요구사항

#### 1. 꿈 작업(Dream-Work) 4기제 결정론 매핑

Freud 명시 4기제:
- 응축(Verdichtung, Condensation)
- 전치(Verschiebung, Displacement)
- 상징화(Symbolisierung, Symbolization)
- 이차 가공(sekundäre Bearbeitung, Secondary Revision)

각 기제별 결정론 식별 규칙 + 한국어 꿈 보고 텍스트 적용 사례:

```yaml
mechanism: "응축"
detection_rules:
  - text_pattern: "복수 인물 혼합"
  - text_pattern: "한 장면 여러 시공간 결합"
detection_keywords: ["같은데 다른", "여러 명이 하나로"]
freud_source: "꿈의 해석 §6장 A절"
```

#### 2. 보편 상징(Universal Symbols) 매핑

Freud 명시 상징 (《꿈의 해석》 + 《정신분석 입문강의》):
- 집 → 신체
- 부모 → 권위
- 왕족 → 부모
- 물 → 출생
- 여행 → 죽음
- 의복 벗기 → 노출

본 시스템 KCI/RISS 검증 의무 — 한국어 번역본 표준판(열린책들·서울대 출판부 등)
ISBN 인용 + 페이지 명시.

#### 3. 한계 + ADR-006 정합

다음은 채택 불가:
- ❌ "꿈으로 정신질환 진단" (의료법 §27 + ADR-006)
- ❌ "성적 상징 인과 단정" (사용자 출력 부적합)
- ❌ "어머니/아버지 관계 단정 해석" (가족 갈등 유발 위험)

채택 가능:
- ✅ 객관 기제 라벨 ("이 꿈은 응축 기제로 보입니다")
- ✅ 상징 가능성 다중 제시 ("물은 출생·정화·무의식 등 다양한 해석 가능")
- ✅ Freud 학파 명시 ("Freud 정신분석 관점에서")
- ✅ 학파 차이 명시 ("Jung·Hobson 등 다른 학파는 다르게 해석")

#### 4. 회귀 테스트 데이터셋

본 시스템 회귀 검증용 30쌍:

```json
[
  {
    "id": "freud_001",
    "dream_text": "어머니와 선생님이 같은 사람이었어요.",
    "expected_mechanism": "응축",
    "expected_interpretation_keywords": ["권위 인물 통합"],
    "expected_disclaimer": "Freud 정신분석 학설"
  }
]
```

#### 5. 본 시스템 결손 영역

현 `engine/agents/freud_persona.py` v1:
- 단순 페르소나 응답 (학파 명시 부족)
- 4기제 결정론 검출 없음
- 상징 매핑 분산 (체계적 데이터 X)

신규 v2 모듈 후보:
- `engine/agents/freud_v2.py` 또는 freud_persona.py 보강
- `data/freud_universal_symbols.json` (검증된 상징 매핑)
- `data/freud_dream_work_rules.json` (4기제 검출 규칙)
- 회귀 30건

#### 6. 다른 학파와의 분리 명세

본 시스템 학파 분리 정책:
- A8 Freud (고전 정신분석)
- A5 Jung (분석심리학) — 별도 에이전트
- A9 Lakoff (인지언어학) — 별도 에이전트
- Hobson (활성화-종합) — dream_lex/hobson.py
- Solms (SEEKING) — dream_lex/solms_seeking.py

A8 v2는 **Freud 단독 채택** + 학파 명시 의무.

### 출력 형식

1. **4기제 결정론 검출 규칙 YAML**
2. **보편 상징 매핑 표** (한국어 표준판 ISBN·페이지 인용)
3. **학파 분리 명세** (Freud ≠ Jung ≠ Hobson 명확화)
4. **사용자 출력 면책 가이드라인**
5. **회귀 데이터셋 JSON** (30쌍)
6. **본 시스템 결손 영역 매핑** (freud_persona.py v1 → v2 갭)

### 검증 기준

- 모든 인용 ISBN·페이지 명시 (라이브 검증 가능)
- 가짜 인용 0건
- 의료법 §27 인과 단정 표현 0건
- 학파 차이 명시 의무
- 회귀 30쌍 이상

위 조건 미충족 시 ADR-010 사실성 분리 + ADR-006 자문 거절에 따라 거부.
```

---

## 본 시스템 채택 절차

1. `/squeeze-report` 사실성 분리 + ISBN 라이브 검증
2. ACCEPT 후보:
   - 신규 ADR (A8 Freud v2 정책)
   - `engine/agents/freud_v2.py` 또는 freud_persona.py 보강
   - `data/freud_universal_symbols.json` + `data/freud_dream_work_rules.json`
   - 회귀 30건
   - vault/references/ Freud 한국어 표준판 출처 영속화

## 면책

- ADR-006 자문 거절 + ADR-010 사실성 분리 동시 적용
- 학파 명시 의무 (Freud ≠ 절대 진리)
- 의료법 §27 인과 단정 절대 금지
- 다른 학파(Jung·Hobson 등) 차이 명시 의무
