---
type: adr
adr_number: 23
status: accepted
date: 2026-05-17
authors: [Technoetic]
domain: [dream]
related:
  - ADR-002-saju-option-A
  - ADR-006-legaltech-rejected
  - ADR-010-name-sibling-factuality
  - ADR-015-saju-option-B-eokbu
  - ADR-017-squeeze-report-command
  - ADR-021-dreamnet-b6-v4
related_module: ../../engine/agents/freud_v2.py
related_report: ../reports/freud-v2-research
related_reference: ../references/freud-korean-isbn
related_prompt: ../templates/PROMPT_freud-classical-v2
---

# ADR-023: A8 Freud v2 — 고전 정신분석 4기제 결정론 매핑

## 배경

`engine/agents/__init__.py` 명시 TODO `A8 freud (v2) — TODO` 해소.

PROMPT_freud-classical-v2.md 의뢰 → 보고서 수령 → /squeeze-report 절차:
- 분석 에이전트 (Haiku): 후보 5건 (C1·C2·C3·C4·C5)
- 판정 에이전트 (Haiku): ACCEPT 5건 (모두 통합)
- 오케스트레이터 (Opus): 본문화

본 ADR-023 = ADR-017 절차 **네 번째 본문화 사례**:
- ADR-020 L2 photo_quality (회귀 9 PASS)
- ADR-021 B6 DreamNet v4 (회귀 17 PASS)
- ADR-022 face_shape 5형 (회귀 18 PASS)
- **ADR-023 A8 Freud v2 (회귀 26 PASS) ← 본 ADR**

## 결정

`engine/agents/freud_v2.py` 신규 모듈 본문화 (v1 freud_persona.py와 별개).

### 4기제 결정론 매핑 (보고서 §4 YAML)

| 기제 | 영문 원어 | 키워드 예시 | 한국어 표준판 ISBN |
|---|---|---|---|
| 응축 | Verdichtung (Condensation) | "같은데 다른"·"여러 명이 하나로" | 9788932920528 |
| 전치 | Verschiebung (Displacement) | "사소한 것에"·"이상하게 신경 쓰여" | 9788932920528 |
| 상징화 | Symbolisierung (Symbolization) | "집"·"부모"·"왕"·"물"·"여행"·"의복" | 9788932920498 |
| 이차가공 | sekundäre Bearbeitung | "줄거리가 있는"·"마치 영화처럼" | 9788932920528 |

### 보편 상징 매핑 (보고서 §5 6건)

집·부모·왕족·물·여행·벌거벗음 + 한국어 표준판 ISBN 3건 + 가능성 다중 제시
포맷 (ADR-006 준수).

### v1 vs v2 분리

| 모듈 | 책임 | 상태 |
|---|---|---|
| `freud_persona.py` (v1) | LLM 페르소나 응답 생성 | 유지 (190줄) |
| `freud_v2.py` (본 ADR) | **결정론 4기제 + 보편 상징 검출** | 신규 |

v2는 LLM 호출 0건. CLAUDE.md §0 결정론 + LLM 분리 정신 완전 정합.

### ADR-006/010/014 정합 강제

`DEFAULT_DISCLAIMERS` 3건:
1. "본 결과는 Freud 정신분석 학파의 학설이며 임상 진단·미래 예언이 아닙니다."
2. "꿈 작업 기제(응축·전치·상징화·이차 가공)는 가능성 다중 해석으로 제시됩니다."
3. "다른 학파(Jung 분석심리학·Hobson 활성화종합·Solms SEEKING)는 다르게 해석할 수 있습니다."

`FORBIDDEN_OUTPUT_PATTERNS` (8건 차단):
- 의료 단정 ("당신은 [질병명]입니다")
- 미래 예언 ("확실히", "반드시", "운명")
- **성환원 단정** ("지팡이는 남근", "동굴은 자궁") — 보고서 §7 footnote 7 명시

`has_forbidden_output()` 함수로 LLM 페르소나 출력 사후 검증 가능.

### 학파 명시 의무 (ADR-002 + ADR-015 정합)

- `FreudV2Result.school = "Freud 정신분석"` 강제
- ADR-002 학파 회피 (옵션 A 디폴트) 무관 — Freud는 명시 학파 채택 (ADR-015 옵션 B 패턴 정합)
- 다른 학파(Jung·Hobson·Solms)는 별도 에이전트 분리 명시

## 회귀 26 PASS

`engine/agents/test_freud_v2.py`:

**4기제 정합 (3건)**:
1. mechanism count 4 (응축·전치·상징화·이차가공)
2. mechanism ISBN 포함
3. mechanism keywords >= 3건

**보편 상징 정합 (4건)**:
4. symbols 6건 (집·부모·왕족·물·여행·벌거벗음)
5. ISBN 13자리 + 978 prefix
6. output_format 가능성 다중 제시
7. 3종 ISBN (열린책들 2 + 서울대 1)

**DEFAULT_DISCLAIMERS (3건)**:
8. disclaimers count >= 3
9. school explicit (Freud + 다른 학파)
10. no medical diagnosis (임상·진단 + 예언 명시)

**analyze 통합 (3건)**:
11. analyze empty
12. analyze returns FreudV2Result
13. to_dict 모든 필드

**보고서 §6 회귀 5건**:
14. freud_001 응축
15. freud_002 전치
16. freud_003 물 분석 구조
17. freud_004 집
18. freud_005 이차가공

**Forbidden patterns (4건)**:
19. disease
20. sexual reduction
21. future prediction
22. safe output passes

**Frozen dataclass (3건)**:
23. FreudV2Result frozen
24. MechanismRule frozen
25. UniversalSymbol frozen

**기타 (1건)**:
26. (모든 검증 통합)

## 검토한 옵션

### A. 보고서 명세 본문화 + v1과 별개 모듈 (채택)

- 장점:
  - 책임 분리 (결정론 ≠ LLM 페르소나)
  - ADR-021 B6 패턴 정합
  - 회귀 자동 검증
  - 학파 명시 의무
- 단점: v1·v2 통합 호출 별도 작업

### B. v1 freud_persona.py 보강

- 장점: 1모듈 통합
- 단점:
  - 책임 분리 위반
  - LLM 호출 + 결정론 혼재

### C. dream_lex/freud.py 보강

- 장점: 기존 학파 모듈 활용
- 단점:
  - dream_lex는 학파별 단순 매핑 위주
  - ADR-023 명세 (DEFAULT_DISCLAIMERS·output filter·회귀)와 책임 다름

## 채택

**A 채택**. 별도 모듈 + B6 패턴 정합 + ADR-006/010/014 자동 검증.

## 결과

### 신규 파일
- `engine/agents/freud_v2.py` (결정론 모듈)
- `engine/agents/test_freud_v2.py` (회귀 26 PASS)
- `vault/decisions/ADR-023-freud-v2-adoption.md` (본 ADR)
- `vault/references/freud-korean-isbn.md` (한국어 표준판 ISBN 3건)
- `vault/reports/freud-v2-research.md` (사실성 분리 결과)
- `vault/done/dream-a8-freud-v2.md` (완료 기록)

### vault 영속화
- `vault/decisions/INDEX.md` (ADR-023 추가)
- `vault/done/INDEX.md` (꿈해석 도메인 행 추가)

## 한계

- v1 freud_persona.py + orchestrator interpret_dream_v2 통합 호출은 별도 작업 (옵션)
- 회귀 보고서 30쌍 중 핵심 5쌍만 채택 (나머지 25쌍 후속 보강)
- ISBN 라이브 검증은 보고서 본문 출처 신뢰 (Aladin 서버 응답 한정으로 보류)
- 추가 보편 상징 (12개 이상) 확장 별도 ADR

## 면책

- 본 모듈은 **순수 결정론 4기제 + 보편 상징 검출** — LLM 호출 0건
- 사용자 출력 disclaimers 강제 (ADR-006/010/014)
- 성환원 단정 절대 금지 (FORBIDDEN_OUTPUT_PATTERNS)
- 학파 명시 의무 (Freud ≠ Jung ≠ Hobson)
- 임상·심리 진단 절대 X

## 향후

- v1·v2 통합 (freud_persona가 freud_v2 결정론 결과 입력 받음)
- orchestrator interpret_dream_v2 A8 호출 추가 (별도 작업)
- 회귀 25쌍 추가 (freud_006~030)
- 추가 보편 상징 (12개 이상)
- ISBN 라이브 검증 (Aladin 복구 후)

## 메타

- ADR-017 절차 **네 번째 본문화** 사례 (ADR-020 + 021 + 022 다음)
- engine/agents/ 명시 TODO 3건 중 2건 해소 (B6 ADR-021 + A8 본 ADR)
- 잔존 TODO 1건: A13 social_unconscious v3 (post_traffic 영역)
- PROMPT_freud-classical-v2.md → 보고서 수령 → ADR-023 본문화 = 완전 파이프라인
- 본 ADR immutable
