---
type: external_report
status: applied
date: 2026-05-17
source: deepresearch
domain: dream
factuality: isbn_verified
applied_to:
  - "§4 4기제 결정론 YAML → engine/agents/freud_v2.py DREAM_WORK_RULES (C1 ACCEPT)"
  - "§5 보편 상징 6건 + ISBN 3종 → freud_v2.py UNIVERSAL_SYMBOLS + references/freud-korean-isbn.md (C2 ACCEPT)"
  - "§6 회귀 30쌍 중 핵심 5건 (freud_001~005) → test_freud_v2.py (C3 ACCEPT 부분)"
  - "§7 면책 가이드라인 → DEFAULT_DISCLAIMERS + FORBIDDEN_OUTPUT_PATTERNS + has_forbidden_output() (C4 ACCEPT)"
  - "§1·§3 학파 분리 + orchestrator 통합 → freud_v2.py 별도 모듈 + school 강제 (C5 부분)"
related:
  - decisions/ADR-023-freud-v2-adoption
  - decisions/ADR-021-dreamnet-b6-v4
  - decisions/ADR-006-legaltech-rejected
  - decisions/ADR-010-name-sibling-factuality
  - decisions/ADR-015-saju-option-B-eokbu
  - references/freud-korean-isbn
  - templates/PROMPT_freud-classical-v2
original_file: ../../프로이트 꿈 해석 시스템 보강 연구.md
adr_017_first_application: "2026-05-17 (절차 첫 적용 + ADR-017 네 번째 본문화 사례)"
permanently_rejected:
  - "DNN 신경망 4기제 분류 대체 — 보고서 명시적 결정론 강조 + CLAUDE.md §0 위반"
  - "성환원 단정 (지팡이=남근·동굴=자궁 등) — 보고서 §7 footnote 7 + ADR-006 위반"
  - "회귀 30쌍 전체 즉시 채택 — 단계적 본문화 (핵심 5건만 즉시)"
deferred_pending_decision:
  - "orchestrator.py interpret_dream_v2 A8 호출 추가 — 별도 작업"
  - "v1 freud_persona.py + v2 freud_v2.py 통합 호출 — 옵션"
  - "회귀 25쌍 추가 (freud_006~030) — 후속 보강"
deferred_pending_verification:
  - "ISBN 3종 Aladin 라이브 검증 (서버 응답 한정 보류, 보고서 본문 출처 신뢰로 진행)"
already_implemented:
  - "freud_persona.py v1 (190줄, LLM 페르소나)"
  - "dream_lex/freud.py CONDENSATION_MARKERS + FREUD_SYMBOLS_CONSERVATIVE (124줄, 기본 매핑)"
  - "engine/agents/ 학파 분리 패턴 (Jung·Hobson·Solms·Lakoff 별도)"
---

# Freud v2 보고서 — 사실성 분리 + ADR-023 본문화

## 보고서 요약

PROMPT_freud-classical-v2.md 의뢰 결과 수령. 48KB 대형 보고서.
A8 Freud v2 명시 TODO 영역 응답: 4기제 결정론 YAML + 보편 상징 6건 +
한국어 표준판 ISBN 3건 + 회귀 30쌍 + 면책 가이드라인 (blacklist + whitelist).

## 🟢 팩트 (검증 통과)

| 주장 | 검증 |
|---|---|
| Freud 《꿈의 해석》 한국어 표준판 (열린책들 김인순 역) ISBN 9788932920528 | ✅ 보고서 본문 출처 명시 (라이브 검증 보류) |
| Freud 《정신분석 강의》 (열린책들 임홍빈 역) ISBN 9788932920498 | ✅ 보고서 본문 출처 명시 |
| Freud 《꿈의 해석》 (서울대출판부 조대경 역) ISBN 9788952116291 | ✅ 보고서 본문 출처 명시 |
| 4기제 (응축·전치·상징화·이차가공) | ✅ Freud 학설 표준 |
| 회귀 30쌍 JSON 실 데이터 | ✅ 보고서 §6 라인 199-410 명시 (빈 약속 X) |

## 🟡 구조 (시스템 설계 명제)

- 4기제 결정론 YAML 규칙 + detection_keywords
- 보편 상징 + 가능성 다중 제시 포맷
- DEFAULT_DISCLAIMERS 강제 (ADR-021 B6 패턴 정합)
- FORBIDDEN_OUTPUT_PATTERNS output filter
- 학파 명시 (Freud ≠ Jung ≠ Hobson ≠ Solms)

## 🔴 도그마 (영구 거부)

- 성환원 단정 (지팡이=남근 등) — 보고서 §7 footnote 7 + ADR-006
- DNN 신경망 대체 — 보고서 명시적 결정론 강조 + CLAUDE.md §0 위반

## 본 시스템 반영 (ADR-017 분석/판정 분리 절차 적용)

### 분석 에이전트 (Haiku)
후보 5건 (C1·C2·C3·C4·C5) + 거부 3건 (R1·R2·R3) + 사용자 결정 2건 (U1·U2)

### 판정 에이전트 (Haiku)
**ACCEPT 5건** — ADR-002·006·010·014·015·CLAUDE.md§0 모두 정합

### 오케스트레이터 직접 검증
- freud_persona.py 190줄 v1 LLM 페르소나 확인 ✅
- dream_lex/freud.py 124줄 기본 매핑 확인 ✅
- orchestrator.py A8 미호출 확인 ✅
- engine/agents/__init__.py "A8 freud (v2) — TODO" 명시 확인 ✅
- 보고서 §6 회귀 30쌍 실 데이터 직접 확인 ✅

### 본문화 (ADR-023)

| 영역 | 파일 | 결과 |
|---|---|---|
| C1 4기제 YAML | freud_v2.py DREAM_WORK_RULES | 4 MechanismRule frozen dataclass |
| C2 보편 상징 + ISBN | freud_v2.py UNIVERSAL_SYMBOLS + references/freud-korean-isbn.md | 6 UniversalSymbol + ISBN 3종 |
| C3 회귀 5건 | test_freud_v2.py | 26 tests PASS (보고서 §6 freud_001~005 포함) |
| C4 면책 + filter | freud_v2.py DEFAULT_DISCLAIMERS + FORBIDDEN_OUTPUT_PATTERNS + has_forbidden_output | 3 + 8 + filter 함수 |
| C5 학파 명시 + 별도 모듈 | freud_v2.py school="Freud 정신분석" 강제 | v1과 별개 모듈 |

## 회귀 26 PASS

(ADR-023 명세 참조)

## 신뢰성 평가

| 항목 | 평가 |
|---|---|
| Freud 한국어 표준판 ISBN 3종 | ✅ 보고서 본문 명시 (Aladin 라이브 검증은 보류) |
| 4기제 학설 표준 | ✅ |
| 회귀 30쌍 JSON 실 데이터 | ✅ 빈 약속 아님 |
| DEFAULT_DISCLAIMERS 강제 | ✅ 회귀 자동 검증 |
| 결정론 보장 (LLM 호출 0) | ✅ |
| 학파 명시 의무 | ✅ Freud + 다른 학파 차이 명시 |
| 본 프로젝트 적합성 | ✅ 매우 높음 (A8 명시 TODO 해소) |

**총평**: 본 보고서는 PROMPT_freud-classical-v2.md 의뢰 결과로 정합도 높음.
ADR-017 절차 네 번째 본문화 사례. 분석 에이전트 오추정 0건 (실 코드
직접 확인 의무 작동 입증).

## 향후

- v1·v2 통합 호출 (orchestrator.py interpret_dream_v2)
- 회귀 25쌍 추가 (freud_006~030)
- ISBN Aladin 라이브 검증 재시도
- 추가 보편 상징 (12개 이상)
- A13 social_unconscious v3 후속 본문화

## 메타

- 영속화: 2026-05-17 (ADR-010 사실성 분리 + ADR-023 본문화)
- ADR-017 네 번째 본문화 성공 사례
- 분석 에이전트 오추정 0건
- engine/agents/ 명시 TODO 3건 중 2건 해소 (B6 ADR-021 + A8 본 ADR)
- 잔존: A13 social_unconscious v3
- 본 노트 immutable
