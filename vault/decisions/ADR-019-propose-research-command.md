---
type: adr
adr_number: 19
status: accepted
date: 2026-05-17
authors: [Technoetic]
domain: [meta]
related:
  - ADR-008-ai-work-protocol
  - ADR-010-name-sibling-factuality
  - ADR-017-squeeze-report-command
related_file: ../../.claude/commands/propose-research.md
---

# ADR-019: /propose-research 슬래시 명령어 — 딥리서치 프롬프트 제안 자동화

## 배경

ADR-017로 도입한 `/squeeze-report` 명령어 사용 후 다음 사용자 패턴이
**4회 반복** 관찰됨 (2026-05-17 세션 내):

> "딥리서치로 조사할 것 프롬프트 제안해 후
>
> md도 정리해"

본 패턴은 항상 `/squeeze-report` 직후 호출. 동작:
1. 본 시스템 결손 영역 점검 (engine/ 모듈 풀 + 명시 TODO + DEFER 영역)
2. 신규 딥리서치 프롬프트 후보 추출
3. 기존 PROMPT 풀과 중복 검사
4. `vault/templates/PROMPT_<주제>.md` 신규 작성 또는 정정
5. `vault/roadmap/INDEX.md` 갱신
6. 커밋 + 푸시

사용자 지적 (2026-05-17):

> 이 패턴 내가 반복하잖아?
> 커스텀 슬래시 커맨드로 만들면?

본 패턴을 단일 슬래시 명령어로 추상화하여:
1. 사용자 반복 부담 ↓
2. AI가 1회 호출에 결손 영역 + 중복 검사 + 영속화 일관 처리
3. 절차 영속화 (ADR-019)

## 결정

`.claude/commands/propose-research.md` 슬래시 명령어 신설. 본 ADR로
결정 영속화.

### 명령어 행동 (단일 컨텍스트 패턴)

`/squeeze-report`의 분석/판정 분리와 다른 점:
- **단일 컨텍스트 (메인 Opus 4.7)**
- 분석/판정 분리 미적용

**이유**:
- 결손 영역 발굴은 **시스템 전체 구조 이해 + 창의적 추론** 필요
- Haiku는 결정론 작업(매칭·YAML)에 적합하나 결손 영역 발굴은 부적합
- 검증은 후속 `/squeeze-report` 호출에서 자동 (보고서 받을 때)

### 행동 단계

1. 본 시스템 결손 영역 자동 점검 (TODO 검색 + DEFER 영역 + 모듈 풀 비교)
2. 기존 PROMPT 풀 중복 검사 (frontmatter `purpose` + `related_module`)
3. 신규 PROMPT 작성 또는 기존 정정
4. roadmap INDEX 갱신
5. 잘못 추정된 PROMPT 제거 (필요 시)
6. 커밋 + 푸시
7. 사용자 보고 (표 형식)

### 입력

인자 없음. 시스템 자동 점검.

## 검토한 옵션

### A. 슬래시 명령어 신설 (채택)

- 장점: 사용자 명시 호출, 패턴 추상화 + ADR 영속화
- 장점: 결손 영역 자동 발굴 일관성 ↑
- 단점: `.claude/`는 git tracked X → ADR-019로 우회

### B. 미작성 (반복 유지)

- 장점: 추가 복잡도 0
- 단점: 사용자 매 호출 동일 명령어 입력 부담

### C. `/squeeze-report` 내부 통합

- 장점: 1회 호출에 squeeze + propose 동시
- 단점:
  - `/squeeze-report`는 분석/판정 분리(Haiku) — propose는 단일 Opus 필요
  - 명령어 책임 단일화 정신 위반
  - 사용자가 squeeze만 원할 때 propose 강제 X

## 채택

**A 채택**. 슬래시 명령어 + ADR-019 영속화.

## 결과

### 신규 파일
- `.claude/commands/propose-research.md` (slash command 정의)
- `vault/decisions/ADR-019-propose-research-command.md` (본 ADR)

### 행동 패턴 매트릭스

| 사용자 입력 | 결과 |
|---|---|
| `/propose-research` | 본 시스템 결손 점검 + 프롬프트 신설/정정 + roadmap + commit |
| `/squeeze-report <보고서>` + `/propose-research` | 보고서 처리 후 결손 영역 신규 발견 시 후속 프롬프트 작성 |

### 안전장치 (실제 발생 오류 패턴 반영)

이전 호출에서 발견된 결손 영역 오추론 패턴 (본 명령어가 차단해야 함):

1. **경로 오추정**: engine/face/ 추정 (실제 engine/divination/face_reading.py)
   → 본 명령어: 모든 `related_module` 경로 실존 검증 의무

2. **결손 오추정**: dream 모듈 결손 추정 (실제 dream_lex/ 30+ 학파 모듈)
   → 본 명령어: Glob + wc 명령으로 실제 모듈 풀 직접 확인 의무

3. **이미 구현된 영역 신규 추정**: hwapae.py 결손 추정 (실제 364줄 구현)
   → 본 명령어: 모든 후보의 실제 구현 여부 wc -l 확인 의무

## 면책

- 본 명령어는 비합리 작업 자동 차단:
  - 기존 PROMPT 중복 작성 금지
  - 본 시스템 결손이 아닌 영역 PROMPT 작성 금지
  - 사용자 결정 영역(🔵 사업 단계)은 PROMPT 작성 X, roadmap만
- 사용자 명시 호출 시만 실행
- 결과는 항상 사용자에게 명시 보고 (표 + 파일 경로)

## 위치

- 명령어 파일: `.claude/commands/propose-research.md`
- `.claude/`는 `.gitignore` 대상이라 git tracked X
- 결정 영속화는 본 ADR-019로 vault에 기록
- 다른 컴퓨터에서 작업 시 본 ADR을 참조하여 명령어 재생성 가능

## 향후

- 명령어 사용 누적 후 결손 발굴 패턴 보강
- `/squeeze-report` + `/propose-research` 묶음 호출 패턴 발견 시 또 다른
  추상화 ADR 후보 (예: `/process-report` = squeeze + propose 1회)
- 단, 본 시점에는 단일 명령어 책임 원칙 유지

## 메타

- 본 ADR은 ADR-017과 동일 패턴 (커맨드 영속화 ADR)
- ADR-017 `/squeeze-report` + ADR-019 `/propose-research` = 외부 보고서
  파이프라인 완성
