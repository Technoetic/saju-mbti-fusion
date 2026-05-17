---
type: index
section: decisions
last_updated: 2026-05-18
note: ADR-036 (Phase 5회차 LLM 출력 샘플러) 추가
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
| ADR-021 | [[ADR-021-dreamnet-b6-v4]] | accepted | 2026-05-17 |
| ADR-022 | [[ADR-022-face-shape-classifier]] | accepted | 2026-05-17 |
| ADR-023 | [[ADR-023-freud-v2-adoption]] | accepted | 2026-05-17 |
| ADR-024 | [[ADR-024-mbti-compat-v2-socionics]] | accepted | 2026-05-17 |
| ADR-025 | [[ADR-025-hwapae-korean-deterministic]] | accepted | 2026-05-17 |
| ADR-026 | [[ADR-026-hanja-9389-scourt-api]] | accepted | 2026-05-17 |
| ADR-027 | [[ADR-027-resource-ohaeng-kci-option-c]] | accepted | 2026-05-17 |
| ADR-028 | [[ADR-028-korean-phonetic-rules-priority-1-2]] | accepted | 2026-05-17 |
| ADR-029 | [[ADR-029-korean-name-uniqueness]] | accepted | 2026-05-17 |
| ADR-030 | [[ADR-030-palm-scoring-deterministic]] | accepted | 2026-05-17 |
| ADR-031 | [[ADR-031-saju-twelve-stages]] | accepted | 2026-05-17 |
| ADR-032 | [[ADR-032-korean-phonetic-priority-3]] | accepted | 2026-05-17 |
| ADR-033 | [[ADR-033-korean-surname-300-extension]] | accepted | 2026-05-17 |
| ADR-034 | [[ADR-034-facial-feature-mouth-corner]] | accepted | 2026-05-17 |
| ADR-035 | [[ADR-035-client-ux-image-size-guidance]] | accepted | 2026-05-18 |

## Supplement (parent ADR 본문은 immutable; 추가 결정만 supplement로 영속화)

| Parent | 제목 | 상태 | 일자 |
|---|---|---|---|
| ADR-005 | [[ADR-005-supplement-multimodal-4-signal]] — Phase 12 4중 신호 멀티모달 | accepted | 2026-05-18 |
| ADR-005 | [[ADR-005-supplement-2-objective-vision-only]] — Phase 17 Opus 시각 객관 묘사 한정 | accepted | 2026-05-17 |
| ADR-005 | [[ADR-005-supplement-3-two-stage-pipeline]] — Phase 18 2단계 (Opus JSON + Gemini 사극) | accepted | 2026-05-17 |
| ADR-005 | [[ADR-005-supplement-4-pure-anatomical-stage1]] — Phase 19 Stage 1 순수 해부학 명칭 | accepted | 2026-05-17 |
| ADR-005 | [[ADR-005-supplement-5-no-region-school-mapping]] — Phase 20 Stage 2 영역-학파명 매핑 예시 제거 | accepted | 2026-05-17 |
| ADR-005 | [[ADR-005-supplement-6-test-findings-fixes]] — Phase 21 실측 테스트 5문제 + PNG MIME 버그 해결 | accepted | 2026-05-17 |
| ADR-005 | [[ADR-005-supplement-7-character-synthesis-and-visualizations]] — Phase 22 캐릭터화 단락 + 시각화 6종 | accepted | 2026-05-17 |
| ADR-036 | [[ADR-036-llm-output-sampler]] — LLM 운영 출력 샘플러 (운명 어휘 모니터링 의무 이행, ADR-005 Sup 2~7) | accepted | 2026-05-18 |

## 원칙

1. **ADR은 immutable** — deprecated 표시는 가능, 삭제·재작성 X
2. 새 결정이 이전 결정을 무효화 → 새 ADR 작성하고 이전 것 `superseded_by` 표시
3. 코드 PR에 ADR 번호 참조
4. Parent ADR 본문 보존 + 추가 결정은 `ADR-NNN-supplement-주제.md` 형식으로 분리
