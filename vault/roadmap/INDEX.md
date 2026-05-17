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

## 🟢 외부 입력 대기 (12건 — 본문화 완료 5건 포함: ADR-020·021·022·023·024)

### 작명·관상·사주·손금 도메인

| 항목 | 노트 | 우선도 | 딥리서치 프롬프트 |
|---|---|---|---|
| ✅ 관상 5형 결정론 분류 완료 (ADR-022, 회귀 18 PASS) | [[../done/face-shape-5형-classifier]] | done | [[../templates/PROMPT_face-shape-classifier]] |
| 손금 4선 결정론 점수 (palm_scoring.py 신설, palm-reading-app C1·C2 DEFER) | [[../reports/palm-reading-app]] | **높음** | [[../templates/PROMPT_palm-scoring-deterministic]] |
| 십이운성 옵션 C (engine/saju/ 신살 5종 외 결손) | (새 항목) | 중 | [[../templates/PROMPT_saju-12-stages-jangsaeng]] |
| 한국 성씨·인명 빈도 (name_uniqueness.py 신설) | (새 항목) | 중 | [[../templates/PROMPT_korean-surname-frequency]] |
| ✅ 한국 화투 48매 결정론 점패 엔진 완료 (ADR-025, 회귀 30 PASS, 핵심 6패) | [[../done/hwapae-korean-deterministic]] | done | [[../templates/PROMPT_hwapae-card-meanings]] |
| 한국어 표준발음법 §1~§30 작명 적용 (name_aesthetic.py 보강) | (새 항목) | 중 | [[../templates/PROMPT_korean-phonetic-rules]] |
| §4 인명용 한자 9389자 추가 (saju-app-spec C1 DEFER) | [[../reports/saju-app-spec]] | **높음** | [[../templates/PROMPT_korean-hanja-9389-source]] |
| ✅ 궁합 MBTI 16×16 매트릭스 v2 완료 (ADR-024, 회귀 29 PASS) | [[../done/saju-mbti-compat-v2]] | done | [[../templates/PROMPT_gunghap-mbti-matrix-academic]] |
| §4 자원오행 5001자 수동 매핑 | [[ohaeng-manual-5001]] | 낮음 | [[../templates/PROMPT_ohaeng-manual-5001]] |
| §5 음운 결합 규칙 (어감 §1 영역) | [[name-aesthetic-survey]] | 낮음 | [[../templates/PROMPT_aesthetic-survey]] |

### 꿈해석 멀티에이전트 (engine/agents/ TODO 명시 영역)

| 항목 | 노트 | 우선도 | 딥리서치 프롬프트 |
|---|---|---|---|
| ✅ A8 Freud v2 완료 (ADR-023, 회귀 26 PASS) | [[../done/dream-a8-freud-v2]] | done | [[../templates/PROMPT_freud-classical-v2]] |
| A13 사회적 무의식 v3 — DB 클러스터링 (운영 데이터 누적 후) | (새 항목) | 낮음 | [[../templates/PROMPT_social-unconscious-v3]] |
| ✅ B6 DreamNet v4 완료 (ADR-021, 회귀 17 PASS) | [[../done/dream-b6-dreamnet-v4]] | done | [[../templates/PROMPT_dreamnet-multimodal-v4]] |

> ✅ §1 가족 서열 상대 불용한자 — **완료** (ADR-010 사실성 분리 적용) → [[../done/name-phase3-sibling-preference]]
> ✅ §3 용신 학파 옵션 B — **완료** (이재승 2019 계량화 억부론, KCI 검증) → [[../done/saju-option-B-eokbu]]
> 🟡 §5 어감 — **부분 완료** (§2 인기 음절만 채택, §1 음운 규칙은 미적용) → [[../done/name-aesthetic-partial]]

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
