---
type: adr
adr_number: 9
status: accepted
date: 2026-05-17
authors: [Technoetic]
domain: [meta, infra]
related: [ADR-008-ai-work-protocol]
related_file: ../../.claude/settings.json
---

# ADR-009: Hook 정리 — 본 프로젝트 전용으로 단순화

## 배경

ADR-008에서 CLAUDE.md를 본 프로젝트 전용으로 분리. 그러나
`.claude/settings.json`에 등록된 hook 10여 개는 **다른 프로젝트의
step harness 시스템 잔재**.

사용자 지적:
> "hook도 해당 프로젝트 전용으로 수정하던지?"

### 기존 hook 목록 (settings.json 분석)

| Hook 파일 | 단계 | 목적 | 본 프로젝트 적합성 |
|---|---|---|---|
| `session-start.ps1` | SessionStart | 세션 로그 | step harness 잔재 |
| `step-progress-loader.ps1` | SessionStart | step001.md 강제 | ❌ 무관 |
| `destructive-guard.ps1` | PreToolUse | rm -rf / git reset 차단 | ✅ 유지 |
| `step-dependency-gate.ps1` | PreToolUse | step 의존성 검증 | ❌ 무관 |
| `mx-tag-validator.ps1` | PostToolUse | mx 태그 검증 | ❌ 무관 |
| `lsp-autofix.ps1` | PostToolUse | LSP 자동 수정 | 🟡 선택 |
| `step-progress-writer.ps1` | Stop | step001.md 업데이트 | ❌ 무관 |
| `spec-generator.ps1` | Stop | SPEC 생성 | ❌ 무관 |
| `trust5-validator.ps1` | Stop | trust5 검증 | ❌ 무관 |
| `task-metrics.ps1` | Stop | metric 기록 | ❌ 무관 |
| `step-auto-continue.ps1` | Stop | step 자동 진행 | ❌ 무관 |

본 사주·작명·관상 SaaS 프로젝트는 step harness를 사용하지 않음.
step harness가 매 답변 후 step001.md 부재로 무한 재가동 시도 → 컨텍스트 오염.

## 검토한 옵션

### A. settings.json 단순화 (채택)
- destructive-guard만 유지
- 다른 hook 모두 제거
- 장점: 명료함, 본 프로젝트 코드와 일치
- 단점: 다른 프로젝트에서 작업 시 재설정 필요

### B. settings.local.json 오버라이드
- settings.json은 그대로 두고 settings.local.json으로 비활성화
- 장점: 글로벌 hook 보존
- 단점: settings.local.json도 Git 추적 가능, 복잡도 ↑

### C. step harness 전체 정리
- .claude/hooks/ 폴더 자체를 정리
- step_archive/ 폴더도 정리 대상
- 장점: 깔끔
- 단점: 글로벌 CLAUDE.md "절대 규칙" — .claude/ 보호 (사용자 직접 작업 필요)

## 채택

**A 채택**. settings.json을 본 프로젝트 전용으로 단순화:

```json
{
  "permissions": {
    "deny": [
      "Bash(rm -rf *)",
      "Bash(rm -rf /)",
      "Bash(git push --force*)",
      "Bash(git reset --hard*)",
      "Bash(git clean -f*)"
    ],
    "allow": ["Read", "Glob", "Grep"]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "powershell.exe -NoProfile -ExecutionPolicy Bypass -File .claude/hooks/destructive-guard.ps1",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### 실행 주체

글로벌 `~/.claude/CLAUDE.md` **절대 규칙**:
> ".claude/ 루트 및 commands/ 외 서브디렉토리에 .md, .txt, .json, 기타 파일
>  직접 생성 금지"

→ AI가 settings.json을 직접 편집 못함 → **사용자가 직접 편집**.
단, settings.json 수정은 **허용 목록**에 명시:
> "settings.json, settings.local.json 수정"

확인 결과 settings.json은 **AI도 Edit 가능**. 본 ADR 채택 후 AI가 Edit 실행.

## 결과

- `.claude/settings.json`: hook 10개 → 1개 (destructive-guard)
- `.claude/hooks/` 폴더 자체는 보존 (다른 프로젝트 호환)
- step_archive/ 폴더도 보존 (별도 정리는 사용자 판단)

## 면책

- 본 ADR은 본 프로젝트 한정 — 다른 프로젝트에서 settings.json 사용 시 재검토
- 글로벌 `~/.claude/settings.json`은 본 ADR 영향 X (있다면 별도 관리)

## 향후

- destructive-guard 외 추가 hook 필요 시 새 ADR
- step harness 시스템이 정식 채택되면 본 ADR 재검토
