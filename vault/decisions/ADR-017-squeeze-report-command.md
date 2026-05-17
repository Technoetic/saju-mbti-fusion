---
type: adr
adr_number: 17
status: accepted
date: 2026-05-17
authors: [Technoetic]
domain: [meta]
related:
  - ADR-008-ai-work-protocol
  - ADR-010-name-sibling-factuality
related_file: ../../.claude/commands/squeeze-report.md
---

# ADR-017: /squeeze-report 슬래시 명령어 — 보고서 가치 추출 자동화

## 배경

본 프로젝트 외부 보고서 처리 패턴 (ADR-010 사실성 분리)을 5번 적용한 결과,
동일 보고서를 정독할 때마다 새 가치가 발견되는 패턴 확인:

- name-aesthetic 보고서: 5번에 걸쳐 +5 PR 추가 적용
- 매 정독마다 본문 명시 부분이 점진 발견됨

사용자 지적 (2026-05-17):
> "더 적용할 것 없어?" 이런식으로 반복질문하면 적용할 게 나오잖아?
>  루프돌리는 커맨드 만들면?

본 패턴을 단일 슬래시 명령어로 추상화하여:
1. 사용자 반복 질문 부담 ↓
2. AI가 정독 1회에 모든 합리적 후보 발견하도록 강제
3. 결정론 절차로 짜낼 가치 0 판정 명확화

## 결정

`.claude/commands/squeeze-report.md` 슬래시 명령어 신설. 본 ADR로 결정 영속화.

### 명령어 행동 7단계

1. 이전 적용 이력 확인 (reports/INDEX 검색)
2. 본문 정독 + ADR-010 3등급 분리
3. 외부 출처 검증 (WebFetch — KCI·통계청·서지)
4. 본 프로젝트 ADR 정합성 검토 (ADR-002·006·010·014·015)
5. 결손 영역 매칭 → 채택 항목 본문화
   - 신규 ADR + 모듈 + 회귀 테스트 + vault 영속화
6. 커밋 + 푸시 + 라이브 검증
7. "짜낼 가치 0" 정직 판정

### 안전장치

- 1회 호출당 모든 합리적 후보 한 번에 처리 (반복 호출 불필요)
- 거부 영역 frontmatter 영구 기록 (`permanently_rejected`)
- 사용자 결정 영역(🔵 사업 단계) 자동 정지
- 비합리 작업 자동 거부 (학설 도그마·UI·가짜 인용)

## 위치

- 명령어 파일: `.claude/commands/squeeze-report.md`
- `.claude/`는 `.gitignore` 대상이라 git tracked X
- 결정 영속화는 본 ADR-017로 vault에 기록
- 다른 컴퓨터에서 작업 시 본 ADR을 참조하여 명령어 재생성 가능

## 검토한 옵션

### A. 슬래시 명령어 신설 (채택)
- 장점: 사용자 명시 호출, 자동화 가치, ADR-010 패턴 영속화
- 단점: `.claude/`는 git tracked X — ADR-017로 우회

### B. 미작성 (반복 질문 유지)
- 장점: 무한 루프 위험 0
- 단점: 사용자 반복 부담 + 매 정독 가치 발견 패턴 비효율

### C. AI 자동 호출 (사용자 명시 X)
- 장점: 부담 0
- 단점: ADR-008 (AI 작업 프로토콜) 정신 — 사용자 통제권 약화

## 채택

**A 채택**. 슬래시 명령어 + ADR-017 영속화.

## 결과

- `.claude/commands/squeeze-report.md` 신규
- vault/decisions/ADR-017-squeeze-report-command.md 신규
- 향후 외부 보고서 수신 시: `/squeeze-report <경로>` 1회 호출로 모든
  합리적 가치 추출

## 면책

- 본 명령어는 비합리 작업 자동 거부 — ADR 위반·도그마·가짜 인용·UI 결정·운영 데이터 영역
- 사용자가 명시 호출 시만 실행
- 결과는 항상 사용자에게 명시 보고

## 향후

- 명령어 사용 누적 후 패턴 보강 (예: 보고서 유형별 분기·자동 보고서 인덱싱)
- ADR-017이 절차 정합 문제 발생 시 새 ADR로 superseded
