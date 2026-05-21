# 사주·MBTI 융합 SaaS — Claude Code Behavioral Contract

본 디렉토리는 **사주·작명·관상·궁합·해몽·손금·화패·점성술 9 도메인 운세 SaaS** (https://saju-mbti-fusion.fly.dev/) 백엔드 + 프론트엔드 + Obsidian Vault (지식 영속화) 통합 작업 공간이다.

너(Claude Code)는 본 시스템에서 **결정론 엔진 본문화 + 학파 사실성 분리(ADR-010) + 자문 거절(ADR-006) 안전 가드 의무**를 따른다.

---

## 1. 본 시스템 아키텍처 맵

| 디렉토리 | 역할 | 접근 권한 |
|---|---|---|
| `engine/` | 결정론 엔진 (사주·작명·관상·손금·화패 등 9 도메인) | Read/Write |
| `engine/divination/` | 도메인별 결정론 모듈 (`star/`·`name/`·`face/`·`palm/`·`hwapae/`·`dream_lex/`·`saju_mbti/`) | Read/Write |
| `engine/saju/` | 만세력·신살·십성·운성 (6133줄, 21 파일) | Read/Write |
| `engine/safety/` | 50+ 안전 가드레일 (GDPR·DSR·인시던트·SLO) | Read/Write |
| `engine/agents/` | 꿈해석 멀티에이전트 (14 핵심 + 6 보조) | Read/Write |
| `web/` | FastAPI + uvicorn + BizRouter 백엔드 | Read/Write |
| `front/` | 정적 프론트엔드 (HTML·CSS·JS) | Read/Write |
| `tests/regression/` | 회귀 테스트 (700+ PASS 의무) | Read/Write |
| `tests/smoke/` | 스모크 테스트 (CI Lint & Import Check) | Read/Write |
| `vault/` | **Obsidian Sync 전용 지식 영속화 — git 무시** | Read/Write |
| `vault/decisions/` | ADR (109건+, immutable) | Read/Write (신규만, 기존 정정 X) |
| `vault/done/` | 완료 항목 영구 기록 | Read/Write |
| `vault/reports/` | 외부 보고서 사실성 분리 결과 | Read/Write |
| `vault/references/` | 검증된 학술 출처 (KCI·PMID·ISBN) | Read/Write |
| `vault/templates/` | 딥리서치 PROMPT 페어 (메타 + .deepresearch.txt) | Read/Write |
| `scripts/` | Playwright 자동화·평가 스크립트 | Read/Write |
| `.claude/` | **PROHIBITED — 어떤 파일도 직접 생성 금지** (전역 규칙) | `.claude/commands/` 외 Write 금지 |
| `.git/` | git 메타 | Read only |
| `data/` | 만세력·KASI 캐시 | Read only (재생성은 스크립트로만) |

---

## 2. Hard Rules — 결정론 vs LLM 분리 (★ 핵심)

본 시스템 정체성은 **사실성 분리** (ADR-010):

- **결정론 엔진** (`engine/divination/<도메인>/`): 동일 입력 → 동일 출력 보장. 학술 출처 명시 의무 (KCI·PMID·ISBN).
- **LLM 작문** (`web/server.py` BizRouter Stage 2): 결정론 출력을 시스템 프롬프트에 주입받아 사극체 풀이.

**NEVER**: LLM이 사주 일주·별자리·28수·신살 등을 **자체 산출**하게 두지 마라 — 사전학습 환각 위험. 항상 engine/ 결정론 산출 → 시스템 프롬프트 주입 패턴.

**NEVER**: 학술 출처 부재 영역을 본 시스템에 본문화하지 마라 — `/squeeze-report` Phase 2 판정 통과 ACCEPT 항목만 본문화.

---

## 3. Hard Rules — ADR 정합 (의무)

본 시스템 모든 본문화는 다음 ADR 정합 의무:

| ADR | 의무 |
|---|---|
| ADR-002 | 사주 학파 회피 — 단일 학파 매핑 강요 금지 (옵션 A 디폴트 + 옵션 B 명시 채택) |
| ADR-006 | 자문 거절 — 의료·법률·금융·결혼·이혼·정신질환 인과 예언 금지 |
| ADR-010 | 사실성 분리 — 가짜 인용·빈 약속·검증 불가 단정 금지 |
| ADR-014 | 사주→MBTI 예외 — 16유형 단정 영구 금지 + 4축 경향성만 |
| ADR-015 | 옵션 병행 — 옵션 A 디폴트 침해 금지 (다학파 인정) |

신규 결정 시 `vault/decisions/ADR-NNN-주제.md` 신설 (immutable). 이전 ADR 정정 시 `ADR-NNN-supplement-*.md` 분리 작성.

ADR-094 (dream 단정 어휘 차단): 길몽·흉몽·반드시·확실히 등 단정 어휘는 `_sanitize_dream_assertion_words` + `_sanitize_common_assertion_words` 자동 차단.

---

## 4. Hard Rules — 슬래시 명령어 (본 시스템 운영 풀)

본 시스템 명시 슬래시 명령어 (메타 도구):

| 명령어 | 역할 |
|---|---|
| `/squeeze-report <경로>` | 외부 보고서 가치 추출 (분석 + 판정 Haiku Subagent 분리 + 본문화) |
| `/propose-research` | 본 시스템 결손 영역 점검 + 딥리서치 PROMPT 페어 작성 (Phase A 창의 Opus + Phase B 검증 Haiku 분리) |
| `/domain-priorities` | 9 도메인 결손 영역 우선순위 매트릭스 산출 (5차원 점수화) |
| `/bizrouter` | BizRouter API 연결 확인 |
| `/flyio deploy` | Fly.io 배포 실행 |
| `/verify` | 범용 시각 검증 + 자동 수정 루프 |

`/squeeze-report` 후속에 `/propose-research` 자동 dispatch (단계 8 트리거). 본 시스템 워크플로우 자동화 패턴.

---

## 5. Hard Rules — vault/ 영속화 (Obsidian Sync 전용)

`vault/` 디렉토리는 **`.gitignore` 등재 — git 추적 X**. Obsidian Sync로만 동기화. 다음 의무:

- **NEVER**: `vault/` 하위 파일을 git에 add·commit 시도 마라.
- **NEVER**: ADR 본문 정정 마라 (immutable). supplement 분리.
- **INDEX 4종** (decisions·done·reports·references) 갱신 의무 (신규 ADR·보고서 신설 시).
- **로드맵**: `vault/roadmap/INDEX.md`에 🟢/🟡/🔵 라벨로 진행 단계 명시.

---

## 6. Hard Rules — 회귀 테스트 (★ 의무)

코드 변경 시 회귀 테스트 동반 의무 (ADR-018 정합):

- 결정론 검증 — 동일 입력 → 동일 출력
- ADR-010 사용자 출력 의무 자동 검증 — 인과 표현·면책 자동 포함 확인
- 학파 출처 검증 (학술 인용 시) — KCI·PMID·ISBN 실존 확인 자동화

회귀 테스트 부재 시 본문화 차단. CI Lint & Import Check 단계 통과 의무.

---

## 7. Cross-Project Access (교차 프로젝트 접근 통제)

본 작업 디렉토리 절대 경로: `C:\Users\Admin\Desktop\사주`

다른 디렉토리에서 시작된 Claude Code 세션이 본 시스템에 참조 접근 시:

1. **결정론 도메인**은 `engine/divination/<도메인>/` 모듈 풀 우선 확인 (Glob + wc + grep)
2. **본 시스템 정체성**은 `vault/decisions/ADR-*.md` 확인 (109건+ immutable 결정)
3. 본 시스템에 코드 변경 시 ADR-002·006·010·014·015 정합 의무
4. 본 시스템 vault/는 Obsidian Sync 전용 — 외부 세션에서 git commit 금지

---

## 8. /compact·/memory 진단 (Context Compression Syndrome 대응)

장기 세션에서 본 CLAUDE.md 행동 계약이 백그라운드로 밀려나면:

- `/compact` 입력 → CLAUDE.md 재로드 → 행동 계약 재각인
- `/memory` 입력 → 글로벌·프로젝트·로컬 CLAUDE.md 로드 상태 진단

본 시스템 본문화 규칙 (결정론/LLM 분리·학술 출처 검증·ADR 정합) 이탈 시 명시 사용.

---

## 9. 면책 (사용자 출력 의무)

본 시스템 모든 사용자 출력은 다음 면책 자동 포함 의무:

- "참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다."
- 결정론 산출 영역 명시 (학술 출처 인용 시 출처 명시)
- ADR-006 정신상 "단정·예언·결혼·이혼·정신질환" 어휘 차단

회귀 테스트로 면책 누락 자동 검증.

---

## 10. 본 CLAUDE.md 갱신 정책

본 파일은 본 시스템 **행동 계약서** — 신규 슬래시 명령어 추가·ADR 정합 의무 변경·교차 프로젝트 접근 정책 변경 시 갱신.

상세 ADR은 `vault/decisions/INDEX.md` 참조. 외부 보고서 영속화 결과는 `vault/reports/` 참조. 본 행동 계약은 도메인별 ADR이 덮어쓴다 (ADR 우선).
