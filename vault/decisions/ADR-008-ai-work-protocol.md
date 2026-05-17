---
type: adr
adr_number: 8
status: accepted
date: 2026-05-17
authors: [Technoetic]
domain: [meta, ai]
related: [ADR-007-obsidian-vault-introduced]
supplemented_by:
  - done/roadmap-human-review-labels.md (2026-05-17, roadmap에 AI vs Human 분담 명시)
related_file: ../../CLAUDE.md
---

# ADR-008: AI 어시스턴트 작업 프로토콜 — CLAUDE.md 프로젝트 전용

## 배경

ADR-007에서 vault/ 도입. 그러나 사용자 지적:
> "AI인 네가 vault/를 보는 게 아니라, 네가 축적하고 탐색하면서 개발해야지"

즉 vault/는 인간 문서가 아니라 **AI가 능동적으로 읽고 쓰는 작업 환경**.

기존 글로벌 `~/.claude/CLAUDE.md`는 사용자 개인 규칙(파일 쓰기·.claude 보호)
담당이라 본 프로젝트 도메인 규칙을 담을 수 없음.

## 검토한 옵션

### A. 글로벌 CLAUDE.md 수정
- 모든 프로젝트에 영향
- 본 프로젝트만의 규칙 적용 어려움

### B. 프로젝트 루트에 별도 CLAUDE.md (채택)
- 본 프로젝트만 적용
- 글로벌과 충돌 시 글로벌 우선 명시
- AI가 자동 인식 (Claude Code·Copilot 모두 프로젝트 루트 CLAUDE.md 우선)

## 채택

**B 채택**. 프로젝트 루트 `CLAUDE.md` 신규.

## 핵심 규칙 (10개 절)

1. 새 작업 시작 시 vault/ 점검 (roadmap → decisions → done)
2. 의사결정 → 즉시 ADR 파일 (immutable)
3. 외부 보고서 받으면 즉시 reports/
4. 작업 완료 시 done/ + roadmap 갱신
5. 학파·문헌 인용 시 references/
6. Vault 파일 형식 (frontmatter YAML 필수)
7. AI 환각 한계 인정 — 파일이 진실 소스
8. 코드와 vault/ 동시 관리 (PR 단위)
9. 매 답변 self-check
10. 본 파일 위치 명시

## 결과

- 프로젝트 루트 `CLAUDE.md` 생성
- 본 ADR-008로 변경 가능성 추적
- 글로벌 CLAUDE.md와 충돌 시 글로벌 > 본 파일 명시

## 면책

- 본 프로토콜은 AI 자기 검증용 — 사용자가 위반 발견 시 지적
- AI 환각으로 ADR 없이 "결정했다" 답변 시 실제로 파일 작성 안 됨
- 사용자 검증 기준: 새 결정 → ADR 파일 / 작업 완료 → done/

## 향후 변경

- 본 파일은 immutable
- 본 ADR도 immutable
- 큰 변경 시 새 ADR + `superseded_by` 표시
