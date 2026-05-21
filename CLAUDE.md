# 사주·MBTI 융합 SaaS — Claude Code Behavioral Contract

본 디렉토리는 **사주·작명·관상·궁합·해몽·손금·화패·점성술·윷점 9 도메인 운세 SaaS** (https://saju-mbti-fusion.fly.dev/) 백엔드 + 프론트엔드 + Obsidian Vault 통합 작업 공간이다.

너(Claude Code)는 **결정론 엔진 본문화 + 사실성 분리(ADR-010) + 자문 거절(ADR-006) 의무**를 따른다. 상세 결정은 `vault/decisions/ADR-*.md` 참조 (파일 포인터 패턴 — 필요 시 `cat`).

---

## 1. 아키텍처 맵

| 디렉토리 | 역할 | 권한 |
|---|---|---|
| `engine/divination/` | 도메인별 결정론 (star·name·face·palm·hwapae·dream_lex·saju_mbti·yutjeom) | RW |
| `engine/saju/` | 만세력·신살·십성·운성 (6133줄) | RW |
| `engine/safety/` | 50+ 안전 가드레일 | RW |
| `engine/agents/` | 꿈해석 멀티에이전트 (14+6) | RW |
| `web/` | FastAPI + BizRouter | RW |
| `front/` | 정적 프론트엔드 | RW |
| `tests/regression/` `tests/smoke/` | 회귀·스모크 (700+ PASS) | RW |
| `vault/` | **Obsidian Sync 전용 — git 무시** (decisions·done·reports·references·templates·roadmap) | RW (ADR 정정 X) |
| `.claude/` | **PROHIBITED — `.claude/commands/` 외 어떤 파일도 생성 금지** (전역 규칙) | RO |
| `data/` | 만세력·KASI 캐시 | RO (스크립트 재생성만) |

---

## 2. Hard Rules — 결정론 vs LLM 분리 (★ ADR-010)

- **NEVER**: LLM이 사주 일주·별자리·28수·신살·64괘 등을 **자체 산출**하게 두지 마라. 항상 `engine/` 결정론 → 시스템 프롬프트 주입.
- **NEVER**: 학술 출처 부재 영역을 본문화 마라. `/squeeze-report` Phase 2 판정 ACCEPT만.
- **NEVER**: 의료·법률·금융·결혼·이혼·정신질환 인과 예언 코드 작성 마라 (ADR-006).

상세 ADR: `cat vault/decisions/ADR-010-name-sibling-factuality.md` 등.

---

## 3. Hard Rules — ADR 정합 (포인터)

본 시스템 모든 본문화는 다음 ADR 정합 의무. 상세는 vault/decisions/ 직접 열람:

| ADR | 주제 | 열람 |
|---|---|---|
| ADR-002 | 사주 학파 회피 | `cat vault/decisions/ADR-002-saju-option-A.md` |
| ADR-006 | 자문 거절 | `cat vault/decisions/ADR-006-legaltech-rejected.md` |
| ADR-010 | 사실성 분리 ★ | `cat vault/decisions/ADR-010-name-sibling-factuality.md` |
| ADR-014 | MBTI 단정 회피 | `cat vault/decisions/ADR-014-saju-mbti-prediction-exception.md` |
| ADR-015 | 옵션 병행 | `cat vault/decisions/ADR-015-saju-option-B-eokbu.md` |

신규 결정은 immutable `vault/decisions/ADR-NNN-주제.md`. 정정은 `ADR-NNN-supplement-*.md`. 인덱스: `cat vault/decisions/INDEX.md` (112건).

---

## 4. 슬래시 명령어 풀 (본 시스템 운영)

| 명령어 | 역할 |
|---|---|
| `/squeeze-report <경로>` | 외부 보고서 가치 추출 (분석/판정 Haiku 분리) |
| `/propose-research` | 결손 영역 PROMPT 페어 작성 (Phase A Opus + Phase B Haiku) |
| `/domain-priorities` | 9 도메인 5차원 우선순위 매트릭스 |
| `/bizrouter` `/flyio deploy` `/verify` | 운영 도구 |

`/squeeze-report` 후 결손 발견 시 `/propose-research` 자동 dispatch (단계 8 트리거).

---

## 5. 개발 검증 명령어 (Workflow Commands)

코드 변경 후 반드시 실행:

```bash
# 1단계: 결정론 회귀 (700+ PASS 의무)
pytest tests/regression/ -q

# 2단계: 스모크 (CI Lint & Import Check 정합)
pytest tests/smoke/ -q

# 3단계: 로컬 서버 (UI 검증)
uvicorn web.server:app --reload --port 8000

# 4단계: 배포 (paths-filter engine/·web/·front/ 트리거)
git push origin main
gh run watch <run_id> --exit-status
curl -sf https://saju-mbti-fusion.fly.dev/api/health
```

---

## 6. vault/ Obsidian Sync 영속화 (★)

- **NEVER**: `vault/` 하위 파일 `git add` 마라 (`.gitignore` 등재).
- **NEVER**: ADR 본문 정정 마라 (immutable). supplement 분리.
- **INDEX 4종** (decisions·done·reports·references) 갱신 의무.

---

## 7. Cross-Project Access

본 디렉토리: `C:\Users\Admin\Desktop\사주`

외부 세션 접근 시:
1. `engine/divination/<도메인>/` 모듈 풀 우선 점검 (Glob+wc+grep)
2. `vault/decisions/ADR-*.md` 정체성 확인 (112건 immutable)
3. ADR-002·006·010·014·015 정합 의무 위반 차단

---

## 8. /plan·/diff·/rewind·/compact 운용

- `/plan <목표>`: 코드 작성 전 실행 계획 초안 명시 (탐색→계획→구현→커밋 분리)
- `/diff`: 변경 직후 차이점 점검 (결정론 엔진 임의 수정 발견 시 `/rewind`)
- `/rewind`: 세션 롤백 (결정론 순수성 훼손 시)
- `/compact`: 장기 세션 (~30분) 후 컨텍스트 압축 + CLAUDE.md 재로드
- `/memory`: 글로벌·프로젝트·로컬 CLAUDE.md 로드 상태 진단

---

## 9. 면책 (사용자 출력 의무)

모든 사용자 출력에 자동 포함:
- "참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다."
- 결정론 산출 영역 + 학술 출처 명시 (인용 시)
- ADR-006 단정·예언 어휘 차단 (sanitize 함수)

회귀 테스트로 자동 검증.
