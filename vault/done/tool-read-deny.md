---
type: done
status: applied
date: 2026-05-17
domain: [meta, infra]
related:
  - decisions/ADR-012-tool-read-deny.md
  - reports/saas-claude-obsidian-methodology.md
commit: TBD
---

# Claude Code Read 거부 패턴 적용

## 무엇

[[../reports/saas-claude-obsidian-methodology]] 권장 `.claudeignore` 방식을
ADR-010 사실성 검토 후 거부 → 공식 `permissions.deny` 패턴으로 채택.
data/unihan/ (49MB) · step_archive/ (9.9MB) · __pycache__/ 거부.

## 변경

`.claude/settings.json` `permissions.deny`에 5개 Read 패턴 추가:
- `Read(./data/unihan/**)`
- `Read(./data/unihan/*.txt)`
- `Read(./data/unihan/*.zip)`
- `Read(./step_archive/**)`
- `Read(./**/__pycache__/**)`

## vault 동반

- ADR-012 신규
- reports/saas-claude-obsidian-methodology.md `applied_to` 갱신
- INDEX 갱신

## 검증

- JSON 유효성 — `python -m json.tool` 통과
- data/ 디렉토리 무결성 — ls 정상
- 차단 대상 확인: Unihan 원본 zip/txt, 캐시, pycache

## 결과

- 본 세션에서 실제 발생한 토큰 낭비 사례 (Unihan 원본 읽기 시도 등) 차단
- 보고서 §3.2 권장은 거부 — `.claudeignore` 공식 미지원 (ADR-010 사실성 분리 적용)
- 공식 `permissions.deny` 패턴으로 동등 효과

## 면책

- `.claude/`는 `.gitignore` 대상이라 settings.json 자체는 git 추적 안 됨
- 본 done 노트 + ADR-012가 결정의 영속화 매개
- 다른 컴퓨터에서 동일 설정 필요 시 ADR-012 참조하여 재구성
