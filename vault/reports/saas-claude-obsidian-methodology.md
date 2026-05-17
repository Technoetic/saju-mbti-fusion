---
type: external_report
status: received_with_caveats
date: 2026-05-17
source: deepresearch
domain: meta
applied_to: []
neo4j_synced: false
factuality: mixed
related:
  - decisions/ADR-007-obsidian-vault-introduced.md
  - decisions/ADR-008-ai-work-protocol.md
  - decisions/ADR-009-hook-cleanup.md
  - decisions/ADR-010-name-sibling-factuality.md
original_file: ../../AI 에이전트 기반 SaaS 개발 방법론 클로드 코드(Claude Code)와 옵시디언(Obsidian)을 활용한 지식 축적 및 탐색 자동화 아키텍처 설명.md
verified_against:
  - https://code.claude.com/docs/en/memory (2026-05-17 fetch)
  - https://code.claude.com/docs/en/hooks (2026-05-17 fetch)
---

# Claude Code + Obsidian 방법론 보고서 — 사실성 검증 분리

## 검증 절차

ADR-010 사실성 분리 원칙. **공식 문서 라이브 fetch로 사실 여부 직접 검증**.

## 🟢 팩트 — 채택 (공식 문서 검증됨)

### 1. CLAUDE.md 시스템
- ✅ "프로젝트 루트의 CLAUDE.md가 모든 세션 시작 시 로드"
- ✅ "compaction 이후 project-root CLAUDE.md는 재주입됨"
- ✅ "200줄 권장 한계" (보고서 표현 ≒ 공식 권장)
- ✅ "managed / user / project / local 4 스코프"
- ✅ "지나치게 큰 CLAUDE.md는 instruction adherence가 감소"

### 2. Auto Memory 시스템
- ✅ 저장 경로: `~/.claude/projects/<project>/memory/`
- ✅ `MEMORY.md` 인덱스 파일 존재
- ✅ "**첫 200줄 또는 25KB**(둘 중 먼저 도달)" 제한 — 보고서가 정확히 인용
- ✅ "Topic 파일들은 startup이 아닌 on-demand 로드"
- ✅ "git repo 단위 + 모든 worktree 공유"

### 3. Hook 시스템
- ✅ SessionStart / PreToolUse / PostToolUse / Stop / PreCompact hook 모두 실존
- ✅ JSON `.claude/settings.json` 구성 가능
- ✅ Exit code 2 = block 동작 (PreToolUse)
- ✅ 결정론적 게이트 역할 (Claude 판단과 무관)

### 4. Obsidian 파일 시스템 호환성
- ✅ Plain markdown + frontmatter는 외부 도구 종속성 0
- ✅ AI가 Read/Write/Bash로 직접 조작 가능 (실제 본 프로젝트가 이미 그렇게 동작 중)

### 5. AGENTS.md 호환
- ✅ Claude Code는 `CLAUDE.md`만 자동 로드 (AGENTS.md 미자동)
- ✅ AGENTS.md 사용 시 `@AGENTS.md` import 또는 symlink 권장

## 🟡 구조 — 시스템 설계 명제로 채택 (검증 불가하나 유효)

### 6. "상태 비저장 작업자 / 영구적 상태 계층" 추상화
**근거**: 컨텍스트 윈도우 한계는 사실. 외부 영구 저장소 필요성도 사실.
**채택 여부**: 본 프로젝트는 이미 ADR-007 (Obsidian Vault 도입) + ADR-008 (AI 작업 프로토콜)로 동일 구조 채택 완료.

### 7. "점진적 정보 공개(Progressive Disclosure)" 패턴
**근거**: CLAUDE.md 비대화 시 adherence 감소(공식 검증). 따라서 CLAUDE.md는 메타 원칙만 + 도메인 지식은 vault로 위임은 합리적.
**채택 여부**: 본 프로젝트의 [[../../CLAUDE.md]]는 이미 이 패턴 — 10절 메타 규칙 + vault 포인터.

### 8. Session_Handoff 프로토콜
**근거**: 컨텍스트 압축 시 정보 유실 발생함은 사실. 인계 노트 작성은 합리적 대응.
**채택 여부**: 본 프로젝트는 별도 Session_Handoff.md 없음. 대신 done/ + roadmap/이 동일 역할(완료 + 다음 작업). **이미 동등 기능 존재**, 별도 신설 불필요.

### 9. `.claudeignore` 패턴
**근거**: 무거운 디렉토리 읽기 = 토큰 낭비는 사실.
**현 상태**: 본 프로젝트는 `.claudeignore` 미사용. 다만 `.gitignore`, `.dockerignore`로 대부분 보호. 위험 디렉토리(node_modules·.next·.env) 차단은 ADR-009의 destructive-guard 보완으로 충분.
**판단**: **우선순위 낮음**. 본 프로젝트는 Python + FastAPI라 node_modules 무관, .env는 `.gitignore` 처리됨.

## 🔴 도그마 — 폐기

### 10. ❌ "15가지 hook 이벤트"
보고서 주장: "15가지의 생명주기 이벤트"
**공식 문서 검증**: 실제로는 **약 29~31종 hook 이벤트** (SessionStart, Setup, SessionEnd, UserPromptSubmit, UserPromptExpansion, Stop, PreToolUse, PostToolUse, PostToolUseFailure, PostToolBatch, PermissionRequest, PermissionDenied, SubagentStart, SubagentStop, TeammateIdle, TaskCreated, TaskCompleted, ConfigChange, CwdChanged, FileChanged, InstructionsLoaded, PreCompact, PostCompact, Elicitation, ElicitationResult, WorktreeCreate, WorktreeRemove, Notification, StopFailure 등)
**판정**: 보고서 수치 부정확. 신뢰 불가 신호 1.

### 11. ❌ "Auto Dream 프로세스"
보고서 주장: "백그라운드에서는 'Auto Dream'이라는 프로세스가 유휴 시간 동안 복잡한 메모리들을 병합한다"
**공식 문서 검증**: "Auto Dream" 표현은 공식 문서에 **0건**. Auto memory 문서 어디에도 등장하지 않음.
**판정**: 보고서 창작 또는 외부 비공식 출처. 신뢰 불가 신호 2.

### 12. ❌ "compaction 임계치 95%"
보고서 주장: "입력 토큰이 제한치의 약 95%에 도달하면"
**공식 문서 검증**: 정확한 임계치 수치는 공식 문서에 명시 없음. 보고서가 구체적 숫자를 추측·창작했을 가능성.
**판정**: 검증 불가능한 권위 수사. "약 95%"는 불특정 출처 추측.

### 13. ❌ "Claude Sonnet 4.6 또는 Opus 4.7은 200K~1M 토큰의 컨텍스트 윈도우"
**모델명은 사실 일치** (현재 본 환경이 Opus 4.7 1M 컨텍스트). 단 보고서가 모델 ID·컨텍스트 한계까지 정확히 언급한 부분은 채택 가능.
**판정**: 이 진술은 **🟢 팩트로 이동**. 권위 수사가 아니라 검증된 사실.

### 14. ⚠️ "Claude Context by Zilliz", "marmot CLI"
**검증 불가**: 본 fetch에서 직접 검증 안 함. 두 도구는 외부 서드파티 — 보고서가 정확히 언급했더라도 본 프로젝트는 **현재 미도입**. 도입 결정은 별도 ADR 필요.
**판정**: 도입 검토 대상 (보류).

### 15. ❌ "마이크로서비스 구조", "Next.js 15", "Tailwind 4", "Supabase"
보고서는 Next.js + Supabase 스택을 전제로 설명. **본 프로젝트는 Python + FastAPI + Railway + SQLite**. 보고서 시나리오 §4 (`@supabase/ssr` 인증·서버 액션) 등은 **본 프로젝트 무관**.
**판정**: 본 프로젝트 적용 불가. 참고용 사례.

## 본 시스템 반영

### ✅ 이미 채택 완료 (보고서가 후행적으로 정당화)

본 프로젝트는 보고서가 권장하는 핵심 구조를 **이미 ADR-007·008·009·010으로 구축 완료**:

| 보고서 권장 | 본 프로젝트 현 상태 |
|---|---|
| Obsidian Vault를 영구 상태 계층 | [[../decisions/ADR-007-obsidian-vault-introduced]] ✅ |
| AI가 vault를 읽고 쓰는 프로토콜 | [[../decisions/ADR-008-ai-work-protocol]] + [[../../CLAUDE.md]] ✅ |
| 결정론적 hook 게이트 (destructive-guard) | [[../decisions/ADR-009-hook-cleanup]] ✅ |
| 점진적 정보 공개 (메타 규칙만 CLAUDE.md) | CLAUDE.md 10절 구조 ✅ |
| 외부 보고서 사실성 검증 | [[../decisions/ADR-010-name-sibling-factuality]] ✅ |
| frontmatter YAML + 백링크 | 모든 vault 노트 ✅ |
| done/ + roadmap (인계 역할) | Session_Handoff 대체 ✅ |
| Obsidian CLI 자동 탐색 | runbook/INDEX.md "Obsidian CLI" 절 ✅ |

→ **보고서가 본 프로젝트 구조를 후행적으로 정당화**.

### 🟡 추가 검토 가치 있는 항목

1. **`.claudeignore` 추가**: 현재 `.gitignore`로 우회 중. Python 프로젝트라 우선순위 낮으나, `__pycache__/`·`.venv/`·`step_archive/` 토큰 낭비 방지에 유효 가능. → roadmap 후보.
2. **Subagent 적극 활용**: 본 환경(Claude Code 1M 컨텍스트)에서 무거운 코드 분석은 Subagent로 격리 가능. 현재는 main context로 직접 처리 중. → 비용·속도 트레이드오프 측정 필요.
3. **Setup hook**: 초기화 시점 명시 — 본 프로젝트는 SessionStart에 destructive-guard만 등록 (ADR-009). 추가 hook 도입 시 새 ADR.
4. **PreCompact hook**: 컨텍스트 임계 도달 직전 vault 동기화. 본 프로젝트는 매 답변마다 vault 갱신해 압축 위험 낮음. → 우선순위 낮음.

### ❌ 본 프로젝트 미적용

- Next.js/Supabase 시나리오 — 본 프로젝트 무관
- `Claude Context MCP` / `marmot` — 별도 도입 결정 필요 (현재 미검토)
- "지식 부트스트래핑 단계"에서 자동 cat 출력 hook — 본 프로젝트는 CLAUDE.md + auto memory MEMORY.md로 이미 충분히 부트스트래핑됨

## 보고서의 신뢰성 평가

| 항목 | 평가 |
|---|---|
| CLAUDE.md / auto memory 메커니즘 설명 | ✅ 핵심 정확 |
| Obsidian 활용 구조 권장 | ✅ 합리적 (본 프로젝트가 이미 채택) |
| Hook 시스템 활용 사례 | 🟡 개념은 맞으나 "15종" 등 수치 부정확 |
| "Auto Dream" 같은 창작 표현 | 🔴 비공식 출처 또는 환각 |
| 95% 등 구체 수치 | 🔴 출처 미상 추측 |
| Next.js/Supabase 시나리오 | ⚠️ 본 프로젝트 무관 |
| 결론적 권장 사항 | ✅ 본 프로젝트 방향과 일치 |

**총평**: 큰 그림은 정확하나 세부 수치·일부 표현은 권위 가장. ADR-010의 "팩트가 아닌 건 지식이 아니다" 원칙으로 보면 본 보고서를 통째로 채택하면 안 되고, **검증된 팩트와 본 프로젝트 적합 구조만 추출**해 활용해야 함.

## 다음 액션

- [ ] (선택) ADR-011: `.claudeignore` 도입 검토 — Python 프로젝트의 토큰 낭비 방지
- [ ] (선택) Subagent 활용 시점 가이드 — runbook/INDEX.md 보강
- [ ] (보류) `Claude Context MCP` / `marmot` 도입 결정 — 다음 분기 검토
- [ ] **본 보고서 검토 자체가 ADR-010의 두 번째 적용 사례**가 됨 — done 노트 작성 가치 있음

## 출처

- 본 보고서 원본: `사주/AI 에이전트 기반 SaaS 개발 방법론 클로드 코드(Claude Code)와 옵시디언(Obsidian)을 활용한 지식 축적 및 탐색 자동화 아키텍처 설명.md`
- 공식 문서 검증 (2026-05-17 라이브 fetch):
  - https://code.claude.com/docs/en/memory
  - https://code.claude.com/docs/en/hooks

## 메타

- 영속화: 2026-05-17 (사실성 검증 후 작성)
- 본 노트는 immutable. 추가 검토 시 새 노트 또는 본문 보충.
- ADR-010 적용 사례 2호 (1호는 [[name-sibling-bulyong]])
