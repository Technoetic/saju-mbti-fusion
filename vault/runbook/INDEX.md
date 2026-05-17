---
type: index
section: runbook
last_updated: 2026-05-17
---

# 운영 가이드

배포·롤백·라이브 점검·일상 운영.

## 배포

- 자동 배포: GitHub Actions (`.github/workflows/deploy.yml`)
- 트리거: `main` 브랜치 push
- 워크플로 상태: `gh run list --limit 3`

## 라이브 점검

```bash
# Railway SSH
railway ssh "python3 -c 'from engine.divination.name_unihan import total_chars; print(total_chars())'"
# 정상: 8525
```

## 한자 풀 데이터 갱신

```bash
# Unihan 원본 zip 갱신 (드물게)
cd data/unihan && python -c "
import urllib.request
urllib.request.urlretrieve('https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip', 'Unihan.zip')
"
# JSON 재생성
python data/unihan/build_korean_hanja.py
# Docker 재배포 — Dockerfile이 COPY data 자동 포함
git add data/korean_hanja_unihan.json && git commit && git push
```

## 운영표준 점검 (관상 영역)

`engine/safety/quick_check` 모듈 + 라이브 호출.

## 알람 채널

(TODO: 운영 시작 시 작성)
- Slack 채널·PagerDuty·이메일 등

## 사고 대응

(TODO: 운영표준 §14.7 incident_playbook 모듈 매핑)

## 백업·복구

- DB: 현재 없음 (stateless API)
- 캐시: `step_archive/face_reading_cache/` — Railway volume
- 한자 풀: Docker image에 내장 (재배포로 복원)

## Obsidian CLI (1.12+)

본 vault는 Obsidian CLI로 자동 탐색·갱신. 앱이 실행 중일 때만 동작.

### 설치
- Obsidian 1.12.7 설치 (`D:\Program Files\Obsidian\`)
- Settings → General → 고급 → "명령줄 인터페이스" 토글 ON
- "Register CLI" 클릭 → PATH 등록 (미클릭 시 alias 사용)

### 기본 사용
```bash
# 명령은 모두 vault=vault 로 본 프로젝트 vault 지정
OBS="D:/Program Files/Obsidian/Obsidian.com"

# 또는 alias (bashrc 등록됨)
alias obsidian='"D:/Program Files/Obsidian/Obsidian.com"'
alias ob-vault='"D:/Program Files/Obsidian/Obsidian.com" vault=vault'
```

### AI 자동화 명령 (개발 중 사용)

| 명령 | 용도 |
|---|---|
| `ob-vault files sort=modified limit=10` | 최근 수정된 노트 10개 |
| `ob-vault search query="키워드"` | 키워드 검색 (전체 vault) |
| `ob-vault read path="decisions/ADR-009-hook-cleanup.md"` | 노트 본문 읽기 |
| `ob-vault backlinks file=ADR-007 counts` | 백링크 + 카운트 |
| `ob-vault unresolved` | 깨진 백링크 목록 |
| `ob-vault tags counts` | 태그 통계 |
| `ob-vault append file=INDEX content="내용"` | 노트 끝 추가 |

### 새 작업 시 AI 점검 워크플로 (CLAUDE.md §1 보강)

```bash
ob-vault read path="roadmap/INDEX.md"      # 1. 다음 작업 후보
ob-vault search query="해당 주제 키워드"     # 2. 기존 결정·작업 검색
ob-vault unresolved                         # 3. 누락 노트 확인
```

## Claude Code Hook 정책 (ADR-009)

본 프로젝트는 step harness 시스템을 사용하지 않음. `.claude/settings.json`은
`destructive-guard.ps1`만 유지 (PreToolUse / Bash).

### 활성 hook
- `destructive-guard.ps1`: rm -rf, git reset --hard, git push --force 차단

### 비활성화된 hook (.claude/hooks/ 폴더에 파일은 존재, settings.json에서 등록 해제)
- step-progress-loader / writer / auto-continue
- session-start
- step-dependency-gate
- mx-tag-validator
- spec-generator
- trust5-validator
- task-metrics
- lsp-autofix

### 새 hook 추가 시
1. 새 ADR 작성 (ADR-009 superseded_by 또는 추가 ADR)
2. settings.json 수정
3. 본 runbook 갱신
