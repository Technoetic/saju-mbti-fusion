---
type: index
section: reports
last_updated: 2026-05-17
---

# 외부 보고서 누적

외부에서 받은 보고서 (딥리서치·명리학자 자문·문헌 정리). [[../templates/REPORT_TEMPLATE|템플릿]] 사용.

## 받은 보고서

| 일자 | 제목 | 출처 | 반영 상태 |
|---|---|---|---|
| 2026-05-15 | [[saju-app-spec]] (작명 보고서) | 외부 작성 | §1~§5 본문화 완료, §6 거부, §3 옵션 A 채택 |
| 2026-05-17 | [[name-sibling-bulyong]] (가족 서열 상대 불용한자) | 딥리서치 | ✅ 본문화 완료 (ADR-010 적용) → [[../done/name-phase3-sibling-preference]] |
| 2026-05-17 | [[saas-claude-obsidian-methodology]] (Claude Code + Obsidian 방법론) | 딥리서치 | ✅ 검증 — 본 프로젝트가 이미 권장 구조 채택 완료 (ADR-007~010) |
| 2026-05-17 | [[input-guardrails]] (입력 가드레일 7계층) | 딥리서치 | ✅ 검증 — 70% 이미 구현, L1 파일 무결성 + Laplacian blur 추가 가치 |
| 2026-05-17 | [[llm-token-caching]] (LLM 캐싱 전략) | 딥리서치 | ✅ 검증 — Anthropic prompt caching 이미 사용. 시맨틱 캐싱 ROI 낮음 |
| 2026-05-17 | [[knowledge-graph-non-rag]] (Neo4j + NL2GQL) | 딥리서치 | ⚪ Neo4j 도입 보류 유지 (ADR-007 재확인) — 본 프로젝트 RAG 미사용 |
| 2026-05-17 | [[saju-mbti-correlation]] (사주-MBTI 연관성) | 딥리서치 | 🔴 **거부** — 인용 검증 불가 + ADR-002·010 위반 위험 |
| 2026-05-17 | [[saju-mbti-ml-model]] (사주-MBTI ML 모델) | 딥리서치 | 🔴 **거부** — 위 보고서 거부 + 학습 데이터 부재 + ADR 다수 위반 |
| 2026-05-17 | [[face-image-generation]] (Gemini Flash Image 길흉상) | 딥리서치 | 🟡 내부 테스트 한정 — 사용자 노출 금지 |
| 2026-05-17 | [[palm-reading-app]] (손금 앱 도메인·아키텍처) | 딥리서치 | 🟡 palm_reading.py 이미 인과 표현 차단. 한의학 손톱 병리 거부 |
| 2026-05-17 | [[saju-option-B-school]] (사주 용신 학파 채택) | 딥리서치 | ✅ ADR-015 본문화 — KCI 검증 통과 (최상 정합도) |
| 2026-05-17 | [[name-aesthetic-data]] (어감·인기 음절) | 딥리서치 | 🟡 §2만 채택 (ADR-016) — 가짜 인용 2건 + 빈 약속 2건 발견 |
| 2026-05-17 | [[face-golden-set-synthesis]] (관상 골든셋 합성 사양) | 딥리서치 | 🟡 ADR-018 정책·사양만 (실제 생성은 DEFER, 보고서 자체 권고) — `/squeeze-report` 첫 사용 |
| 2026-05-17 | [[resource-ohaeng-kci-mapping]] (자원오행 5001자 매핑 조사) | 딥리서치 | 🟡 94자 본문화 (ADR-027) — 보고서 표제 5001자 vs 실 94자 정직 명시 + 옵션 A 보존 + 충돌 6건 |

## 대기 중인 보고서

→ [[../roadmap/INDEX]]의 🟢 외부 입력 대기 섹션 참조

| 항목 | 노트 |
|---|---|
| ~~§3 용신 학파 옵션 B~~ | ✅ 완료 [[saju-option-B-school]] → [[../done/saju-option-B-eokbu]] |
| ~~자원오행 5001자~~ | 🟡 부분 완료 [[resource-ohaeng-kci-mapping]] → 94자 본문화 (ADR-027). 잔여 ~4,900자 학파 자료 추가 의뢰 필요 |

✅ §1 가족 서열 상대 불용 — 완료 ([[name-sibling-bulyong]] 보고서 → ADR-010 사실성 분리 적용 → [[../done/name-phase3-sibling-preference]])

## 보고서 받는 절차

1. 외부에서 보고서 .md 형식으로 받음
2. `reports/` 폴더에 [[../templates/REPORT_TEMPLATE|템플릿]] 사용해 노트 작성
3. 본문은 보고서 그대로 (또는 정리)
4. "본 시스템 반영" 섹션에 적용 계획
5. 본문화 완료 시 done/ 노트 + ADR 작성
6. roadmap에서 이동
