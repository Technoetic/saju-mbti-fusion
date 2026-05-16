---
title: 사주 작명·관상 SaaS — 지식 베이스
type: vault_index
created: 2026-05-17
team_size: 2
maintainer: Technoetic
---

# 사주 작명·관상 SaaS 지식 베이스 (Vault)

본 폴더는 [Obsidian](https://obsidian.md) Vault입니다. 폴더를 그대로
Obsidian 앱에 열거나, VS Code·GitHub에서 평문 마크다운으로 읽을 수 있습니다.

## 목적

- **인간 가독 지식 저장소** — 운영 코드(`engine/`, `web/`)와 분리
- **의사결정 기록** — 왜 옵션 A 채택했나, 왜 §6 거부했나
- **외부 보고서 누적** — 딥리서치·명리학자 자문 결과
- **2인 협업 PR 리뷰** — 평문 마크다운 diff
- **Neo4j 정형 데이터 연동 다리** (frontmatter)

## 폴더 구조

| 폴더 | 용도 |
|---|---|
| `decisions/` | ADR(Architecture Decision Records) — 의사결정 기록 |
| `roadmap/` | 앞으로 할 작업 우선순위·계획 |
| `done/` | 완료된 작업 요약 (지금까지 한 작업) |
| `schools/` | 학파별 견해 정리 (조후·억부·격국·통관) |
| `reports/` | 외부 딥리서치 보고서 누적 (가족 서열 등) |
| `references/` | 출처·문헌 (마의상법·유장상법·자평진전 등) |
| `runbook/` | 운영 작업 가이드 (배포·롤백·라이브 점검) |
| `templates/` | 새 노트 작성 시 참고할 양식 |
| `daily/` | 작업 일지 (선택적) |

## 운영 원칙

1. **마크다운 평문 유지** — Obsidian 전용 문법 최소화 (백링크는 일반 링크로 표현)
2. **Frontmatter 필수** — 정형 메타데이터를 YAML 헤더로
3. **Git 커밋과 동시** — 코드 변경과 vault 변경을 같이 PR
4. **출처 명시** — 외부 자료 인용 시 references/에 별도 노트
5. **의사결정 immutable** — ADR은 deprecated 표시는 가능하나 삭제 X

## 연관 자원

- 코드: `engine/divination/name_*.py`, `engine/safety/`
- 데이터: `data/korean_hanja_unihan.json`, `engine/divination/name_*.py`
- 라이브: https://saju-mbti-fusion-production.up.railway.app/
- repo: https://github.com/Technoetic/saju-mbti-fusion

## Obsidian 앱 사용 시

1. Obsidian 다운로드: https://obsidian.md
2. "Open folder as vault" → `C:\Users\Admin\Desktop\사주\vault\`
3. 추천 plugin: Templater, Dataview, Git
