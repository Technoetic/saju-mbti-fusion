---
type: index
section: decisions
last_updated: 2026-05-17
---

# 의사결정 (ADR) 인덱스

본 시스템의 모든 주요 의사결정 기록. ADR(Architecture Decision Record) 형식.

| 번호 | 제목 | 상태 | 일자 |
|---|---|---|---|
| ADR-001 | [[ADR-001-name-deterministic-engine]] | accepted | 2026-05-17 |
| ADR-002 | [[ADR-002-saju-option-A]] | accepted | 2026-05-17 |
| ADR-003 | [[ADR-003-unihan-fallback]] | accepted | 2026-05-17 |
| ADR-004 | [[ADR-004-face-keypoint-scoring]] | accepted | 2026-05-16 |
| ADR-005 | [[ADR-005-claude-opus-vision]] | accepted | 2026-05-16 |
| ADR-006 | [[ADR-006-legaltech-rejected]] | accepted | 2026-05-17 |
| ADR-007 | [[ADR-007-obsidian-vault-introduced]] | accepted | 2026-05-17 |
| ADR-008 | [[ADR-008-ai-work-protocol]] | accepted | 2026-05-17 |
| ADR-009 | [[ADR-009-hook-cleanup]] | accepted | 2026-05-17 |
| ADR-010 | [[ADR-010-name-sibling-factuality]] | accepted | 2026-05-17 |
| ADR-011 | [[ADR-011-l1-file-integrity]] | accepted | 2026-05-17 |
| ADR-012 | [[ADR-012-tool-read-deny]] | accepted | 2026-05-17 |
| ADR-013 | [[ADR-013-prompt-cache-telemetry]] | accepted | 2026-05-17 |
| ADR-014 | [[ADR-014-saju-mbti-prediction-exception]] | accepted | 2026-05-17 |
| ADR-015 | [[ADR-015-saju-option-B-eokbu]] | accepted | 2026-05-17 |
| ADR-016 | [[ADR-016-name-aesthetic-partial]] | accepted | 2026-05-17 |
| ADR-017 | [[ADR-017-squeeze-report-command]] | accepted | 2026-05-17 |
| ADR-018 | [[ADR-018-face-golden-set-policy]] | accepted | 2026-05-17 |
| ADR-019 | [[ADR-019-propose-research-command]] | accepted | 2026-05-17 |
| ADR-020 | [[ADR-020-l2-photo-quality-laplacian]] | accepted | 2026-05-17 |

## 원칙

1. **ADR은 immutable** — deprecated 표시는 가능, 삭제·재작성 X
2. 새 결정이 이전 결정을 무효화 → 새 ADR 작성하고 이전 것 `superseded_by` 표시
3. 코드 PR에 ADR 번호 참조
