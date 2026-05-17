---
type: done
status: applied
date: 2026-05-17
domain: [meta, infra]
related: [ADR-009-hook-cleanup, ADR-008-ai-work-protocol]
commit: TBD
---

# Hook 정리 — 본 프로젝트 전용

## 배경

ADR-008로 CLAUDE.md를 본 프로젝트 전용 분리 후, hook도 동일하게 본 프로젝트
도메인에 맞춰 정리. step harness 시스템(다른 프로젝트 잔재)이 매 답변마다
무한 재가동 시도 → 컨텍스트 오염 해소가 목표.

## 변경 사항

### `.claude/settings.json`

**Before**: 10개 hook (SessionStart×2 + PreToolUse×2 + PostToolUse×2 + Stop×5)

**After**: 1개 hook (PreToolUse Bash matcher → destructive-guard.ps1)

```json
{
  "permissions": { ... },
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "powershell.exe ... destructive-guard.ps1",
        "timeout": 5
      }]
    }]
  }
}
```

### `.claude/hooks/` 폴더

- 파일 자체는 보존 (다른 프로젝트에서 복원 가능)
- 본 프로젝트 settings.json은 destructive-guard만 참조

### vault 동반 변경

- `vault/decisions/ADR-009-hook-cleanup.md` 신규
- `vault/decisions/INDEX.md` ADR-009 행 추가
- `vault/runbook/INDEX.md` "Claude Code Hook 정책" 절 추가

## 검증

- settings.json 유효 JSON 확인
- destructive-guard.ps1 파일 존재 (PreToolUse Bash 단계에서 실행됨)
- 다른 hook 등록 해제 → step001.md 부재로 인한 무한 재가동 해소

## 결과

- 본 프로젝트에서 Claude Code 세션 시 hook 1개만 작동
- step harness 무관 (사주·작명·관상 SaaS 도메인 코드와 일치)
- 다른 프로젝트로 이동 시 본 프로젝트 settings.json 영향 0

## 관련

- ADR-009: Hook 정리 결정
- ADR-008: AI 작업 프로토콜 (CLAUDE.md 분리)
- CLAUDE.md: 본 프로젝트 AI 작업 규칙
- runbook/INDEX.md: Hook 정책 절
