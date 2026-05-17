---
type: adr
adr_number: 12
status: accepted
date: 2026-05-17
authors: [Technoetic]
domain: [meta, infra]
related:
  - ADR-009-hook-cleanup
  - reports/saas-claude-obsidian-methodology.md
related_file: ../../.claude/settings.json
---

# ADR-012: Claude Code Read 권한 거부 패턴 — 토큰 낭비 방지

## 배경

[[../reports/saas-claude-obsidian-methodology]] (Claude Code + Obsidian 방법론
보고서) 검토 결과, 본 프로젝트가 보고서 권장 구조의 대부분을 이미 채택했으나
**Claude Code가 무거운 디렉토리(data/unihan/ 49MB, step_archive/ 9.9MB,
__pycache__)를 읽으려 시도할 때 토큰을 대량 낭비**할 가능성이 있음.

본 세션에서 실제 발생한 사례:
- 사용자 입력 보고서 .md를 매번 26K 토큰 분량으로 읽음
- data/korean_hanja_unihan.json 712KB 직접 읽기 가능

### 보고서가 제안한 방식의 함정

보고서 §3.2는 `.claudeignore` + PreToolUse hook (Exit code 2) 방식을 권장.
**공식 문서 fetch 검증 결과 `.claudeignore`는 공식 미지원**.

공식 문서 (https://code.claude.com/docs/en/settings) 확인 사항:
- `.claudeignore` — 공식 기능 아님 (GitHub 커뮤니티 wrapper만 존재)
- 공식 대안: `.claude/settings.json`의 `permissions.deny` 패턴
- 형식: `"Read(./경로/패턴)"`

→ ADR-010 사실성 분리 원칙에 따라 보고서 권장 방식 거부, 공식 대안 채택.

## 검토한 옵션

### A. 보고서 원안 — `.claudeignore` + PreToolUse hook
- 장점: 보고서 명세 그대로
- 단점: 공식 미지원, 커뮤니티 wrapper 의존, ADR-009의 hook 단순화 정신과 충돌

### B. `permissions.deny` 패턴 (채택)
- 장점: 공식 지원, 기존 settings.json 구조 확장만, hook 추가 없음
- 단점: `.claude/` 자체가 `.gitignore` 대상이라 git 추적 안 됨 → 다른 컴퓨터에서 동일 설정 필요 시 별도 동기화

### C. 미구현 유지
- 장점: 추가 작업 없음
- 단점: 본 세션에서 이미 발생한 토큰 낭비 방치

## 채택

**B 채택**. `.claude/settings.json` `permissions.deny`에 Read 패턴 추가:

```json
{
  "permissions": {
    "deny": [
      "Bash(rm -rf *)",
      "Bash(rm -rf /)",
      "Bash(git push --force*)",
      "Bash(git reset --hard*)",
      "Bash(git clean -f*)",
      "Read(./data/unihan/**)",
      "Read(./data/unihan/*.txt)",
      "Read(./data/unihan/*.zip)",
      "Read(./step_archive/**)",
      "Read(./**/__pycache__/**)"
    ]
  }
}
```

### 거부 대상 선정 기준

| 대상 | 크기 | 사유 |
|---|---|---|
| `data/unihan/Unihan.zip` | 49MB zip | Unicode 원본. 읽을 일 없음 |
| `data/unihan/*.txt` | 합 50MB+ | Unihan 원본 텍스트 9개. `build_korean_hanja.py`로 가공된 JSON만 사용 |
| `step_archive/**` | 9.9MB | 캐시·로그·이전 step harness 잔재 |
| `**/__pycache__/**` | 5개 디렉토리 | Python 바이트코드 캐시 |

### 거부 대상이 **아닌** 것

| 대상 | 사유 |
|---|---|
| `data/korean_hanja_unihan.json` (712KB) | 가공된 JSON, 코드에서 참조. 큰 편이나 작업 자료라 보존 |
| `data/name_sibling_preference.json` | ADR-011로 추가된 본 프로젝트 데이터 |
| 사용자 입력 보고서 `.md` (7개) | 검토 대상이라 ignore 불가. vault 영속화 후 사용자가 직접 삭제 가능 |
| `vault/.obsidian/workspace*.json` | `.gitignore`로 이미 처리. Claude Code도 굳이 안 읽음 |

## 결과

- `.claude/settings.json` 갱신 (로컬 머신만 적용)
- 본 ADR-012로 결정 영속화 (git tracked vault에 기록)
- 다른 컴퓨터에서 작업 시 본 ADR을 참조해 동일 패턴 적용 가능

## 면책

- `.claude/`는 `.gitignore` 대상이라 settings.json 자체는 git 추적 안 됨
- 본 ADR이 **결정의 영속화** — settings.json은 머신별 재구성
- `permissions.deny`는 Claude의 도구 호출만 차단. git/IDE/일반 도구에는 영향 0

## 향후

- 새 무거운 디렉토리 추가 시 본 ADR에 패턴 추가 (또는 새 ADR)
- 공식 `.claudeignore` 기능이 추가되면 마이그레이션 검토
