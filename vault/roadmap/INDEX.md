---
type: index
section: roadmap
last_updated: 2026-05-17
---

# 로드맵 — 앞으로 할 작업

분류:
- 🟢 외부 입력 대기 (보고서·자료 받으면 즉시 본문화) — **Human Input 필요**
- 🟡 정책 결정 필요 (학파 채택·법적 검토) — **Human Review 필요**
- 🔵 사업 단계 (SaaS 운영·마케팅·결제) — **Human Decision 필요**
- ⚪ 기술 부채 (CI 안정화·테스트 정리) — **AI 단독 진행 가능**

## AI vs Human 분담

본 vault는 보고서 [[../reports/saas-claude-obsidian-methodology]] §2.2의
Session Handoff 정신 — "Needs Human Review" 명시 — 을 분류 라벨에 반영한다.

| 분류 | AI 단독 진행 | Human 필요 사유 |
|---|---|---|
| 🟢 외부 입력 대기 | ❌ | 사용자가 자료·보고서 전달 시점 결정 |
| 🟡 정책 결정 필요 | ❌ | 법무·학파 채택 = 도메인 외부 권위 결정 |
| 🔵 사업 단계 | ❌ | 가격·마케팅·결제사 선택 = 비즈니스 결정 |
| ⚪ 기술 부채 | ✅ | 코드 정리·테스트 = 결정론 작업 |

→ 새 세션에서 AI가 작업 시작 시 ⚪부터 검토하면 사용자 개입 없이 진행 가능.

## 🟢 외부 입력 대기 (본문화 완료 10건 포함: ADR-020~029)

### 작명·관상·사주·손금 도메인

| 항목 | 노트 | 우선도 | 딥리서치 프롬프트 |
|---|---|---|---|
| ✅ 관상 5형 결정론 분류 완료 (ADR-022, 회귀 18 PASS) | [[../done/face-shape-5형-classifier]] | done | (사용자 의도 삭제) |
| ✅ 손금 4대 선 + 금성대 결정론 점수 완료 (ADR-030, 회귀 21 PASS / 120/120 라벨 100%) | [[../done/palm-scoring-deterministic]] | done | — |
| 십이운성 옵션 C (engine/saju/ 신살 5종 외 결손) | (새 항목) | 중 | (사용자 의도 삭제) |
| 🟡 한국 성씨·인명 빈도 — **부분 완료** (ADR-029 본문화, 15 성씨 + 30쌍 회귀 12 PASS) | [[../reports/korean-name-frequency-statistics]] | done (부분) | — |
| 통계청 KOSIS 300위 전수 추출 + 한자 동음이의 + 음절 미인기 결합 보정 (ADR-029 18 known-limitation 해소) | [[../reports/korean-name-frequency-statistics]] | 중 | [[../templates/PROMPT_korean-surname-kosis-300]] |
| ✅ 한국 화투 48매 결정론 점패 엔진 완료 (ADR-025, 회귀 30 PASS, 핵심 6패) | [[../done/hwapae-korean-deterministic]] | done | (사용자 의도 삭제) |
| ✅ §4 인명용 한자 9389자 → 9932자 본문화 완료 (ADR-026, scourt API 직접 추출) | [[../done/hanja-9389-scourt-api]] | done | (사용자 의도 삭제) |
| ✅ 궁합 MBTI 16×16 매트릭스 v2 완료 (ADR-024, 회귀 29 PASS) | [[../done/saju-mbti-compat-v2]] | done | (사용자 의도 삭제) |
| 🟡 §4 자원오행 5001자 — **부분 완료** (ADR-027, KCI 94자 본문화) | [[../reports/resource-ohaeng-kci-mapping]] | 중 | (사용자 의도 삭제, 신규 학파 자료 의뢰 시 PROMPT 재작성) |
| 🟡 §5 음운 결합 규칙 — **부분 완료** (ADR-028 Priority 1·2 본문화, 회귀 14/30 PASS) | [[../reports/korean-phonetic-rules-architecture]] | done (P1·2) | — |
| Priority 3 음운 변동 (자음군 §11+§23 연쇄·ㄴ첨가 §29·상호동화 §19·한자어 §26 특례·다중 연쇄) | [[../reports/korean-phonetic-rules-architecture]] | 중 | [[../templates/PROMPT_korean-phonetic-priority-3]] |

### 꿈해석 멀티에이전트 (engine/agents/ TODO 명시 영역)

| 항목 | 노트 | 우선도 | 딥리서치 프롬프트 |
|---|---|---|---|
| ✅ A8 Freud v2 완료 (ADR-023, 회귀 26 PASS) | [[../done/dream-a8-freud-v2]] | done | (사용자 의도 삭제) |
| A13 사회적 무의식 v3 — DB 클러스터링 (운영 데이터 누적 후) | (새 항목) | 낮음 | [[../templates/PROMPT_social-unconscious-v3]] |
| ✅ B6 DreamNet v4 완료 (ADR-021, 회귀 17 PASS) | [[../done/dream-b6-dreamnet-v4]] | done | (사용자 의도 삭제) |

> ✅ §1 가족 서열 상대 불용한자 — **완료** (ADR-010 사실성 분리 적용) → [[../done/name-phase3-sibling-preference]]
> ✅ §3 용신 학파 옵션 B — **완료** (이재승 2019 계량화 억부론, KCI 검증) → [[../done/saju-option-B-eokbu]]
> 🟡 §5 어감 — **부분 완료** (§2 인기 음절만 채택, §1 음운 규칙은 미적용) → [[../done/name-aesthetic-partial]]
> 🟡 §4 자원오행 — **부분 완료** (ADR-027 94자, 잔여 1,407자 신규 + ~4,900자 학파 자료) → [[../done/resource-ohaeng-kci-94chars]]

## 🟡 정책 결정 필요 (2건)

| 항목 | 노트 | 비고 | 딥리서치 프롬프트 |
|---|---|---|---|
| §6 법원 절차 단순 안내 (법무 검토 후) | [[legaltech-info-only]] | ADR-006 후속 | [[../templates/PROMPT_saas-legal-compliance]] |
| 결제·SaaS 약관·면책 | [[saas-terms-disclaimer]] | 운영 시작 전 필수 | [[../templates/PROMPT_saas-legal-compliance]] |

## 🔵 사업 단계 (5건)

| 항목 | 노트 | 시점 | 딥리서치 프롬프트 |
|---|---|---|---|
| Stripe/Toss 결제 통합 | [[payment-integration]] | SaaS 본격 시작 | - |
| 사용자 인증·계정 시스템 | [[auth-system]] | 결제 전 | - |
| 가격·요금제 결정 | [[pricing-tiers]] | 결제 전 | - |
| 마케팅 페이지 | [[marketing-landing]] | 운영 시작 | - |
| 운영 모니터링·로그 강화 | [[ops-monitoring]] | 운영 시작 | [[../templates/PROMPT_incident-playbook]] |
| LLM 의존성 리스크 평가 | (운영 1-3개월 후) | 트래픽 누적 후 | [[../templates/PROMPT_llm-dependency-risk]] |

## ⚪ 기술 부채 (3건)

| 항목 | 노트 | 영향 |
|---|---|---|
| conftest.py 임시 skip 해제 | [[ci-conftest-cleanup]] | CI 신뢰성 |
| 다른 컴 PR과 safety 모듈 통합 | [[safety-modules-sync]] | 큰 작업 |
| pipeline-viz/ 정리 또는 정식 통합 | [[pipeline-viz-cleanup]] | 위생 |

## 도입 검토 대상

- Neo4j 그래프 DB (외부 보고서 누적 후)
- Obsidian Sync (모바일 필요 시)
- 명리학자·작명사 자문 파트너십
