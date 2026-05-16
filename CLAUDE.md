# CLAUDE.md — 본 프로젝트 AI 작업 프로토콜

본 파일은 **AI 어시스턴트(Claude·Copilot 등)가 본 사주·작명·관상 SaaS
프로젝트에서 작업할 때 따라야 할 규칙**을 정의합니다.

> 글로벌 `~/.claude/CLAUDE.md`는 사용자 개인 규칙(파일 쓰기·.claude 보호 등)을
> 담당합니다. 본 파일은 그것과 **별개**로 본 프로젝트 도메인에 특화된 작업
> 프로토콜입니다. 충돌 시 글로벌 규칙 > 본 파일.

---

## 0. 프로젝트 정체성

- **목표**: 사주·작명·관상·궁합·해몽 SaaS
- **팀**: 2인 개발
- **배포**: Railway + GitHub Actions
- **운영 원칙**: 결정론 엔진 + LLM 작문 분리, 학파 분쟁 회피, 법률·의료 자문 거절
- **지식 저장소**: `vault/` (Obsidian Vault + Git)
- **코드 저장소**: `engine/` (도메인 모듈), `web/` (API), `front/` (UI)

---

## 1. 새 작업 시작 시 — 반드시 vault/ 점검

### 순서

1. **`vault/roadmap/INDEX.md`** — 다음 작업 후보, 우선순위 분류
2. **`vault/decisions/INDEX.md`** — 기존 ADR 확인, 정책 준수
3. **`vault/done/INDEX.md`** — 비슷한 작업 패턴 참고
4. **`vault/references/INDEX.md`** — 학파·문헌 출처

### 검색 패턴

```
Grep "검색어" vault/
Glob vault/**/*.md
Read vault/decisions/ADR-XXX-*.md
```

작업이 도메인(작명·관상·사주·안전)에 해당하면 해당 폴더 우선 탐색.

---

## 2. 의사결정 → 즉시 ADR 파일

답변에만 적지 말고 **파일로 영속화**한다.

### 새 ADR 작성 조건

- 학파·도구·라이브러리 선택
- 보고서 §X 항목 채택/거부/보류
- 운영 정책 (법적·윤리적 기준)
- 모델·라이브러리 의존성 추가

### ADR 작성 절차

1. `vault/decisions/ADR-NNN-짧은제목.md` 생성
2. `vault/templates/ADR_TEMPLATE.md` 기반
3. 다음 ADR 번호: `vault/decisions/INDEX.md` 확인
4. 작성 후 INDEX.md 표에 행 추가
5. 답변에서 ADR 번호로 인용 (예: "ADR-002에 따라 옵션 A 채택")

### 면책

ADR은 **immutable**. 변경 필요 시:
- 새 ADR 작성
- 이전 ADR의 frontmatter에 `superseded_by: ADR-NNN` 추가
- 이전 ADR 본문은 보존

---

## 3. 외부 보고서 받으면 — 즉시 reports/

사용자가 딥리서치·명리학자 자문·문헌 자료를 전달하면:

1. **`vault/reports/주제명.md`** 즉시 생성 (`templates/REPORT_TEMPLATE.md` 기반)
2. 본문은 원본 그대로 또는 정리
3. "본 시스템 반영" 섹션에 적용 계획 (✅ 즉시 / 🟡 부분 / ❌ 불가)
4. `vault/reports/INDEX.md` 표에 행 추가
5. 본문화 시작 시 done/ 노트 + ADR 동반 작성

---

## 4. 작업 완료 시 — done/ + roadmap 갱신

코드 변경 + 커밋·푸시·라이브 검증이 끝났을 때:

1. **`vault/done/주제-phase.md`** 작성 (`templates/DONE_TEMPLATE.md` 기반)
   - commit SHA, workflow ID, 회귀 테스트 수 명시
   - 관련 ADR 링크
2. **`vault/done/INDEX.md`** 표에 행 추가
3. **`vault/roadmap/INDEX.md`** 에서 해당 항목 제거 또는 다음 단계로 이동
4. 답변 끝에 "작업 완료" 한 문장으로 마무리

---

## 5. 학파·문헌 인용 시 — references/

운영표준이나 학파 통설을 인용할 때:

- `vault/references/문헌명.md` 있으면 인용
- 없으면 새 노트 생성 후 출처·저자·시대 명시
- 답변에서 `[[references/마의상법]]` 형식으로 링크

---

## 6. Vault 파일 형식 규칙

### Frontmatter (YAML 헤더) 필수

```yaml
---
type: adr | done | roadmap | report | reference | index
status: proposed | accepted | applied | rejected | superseded
date: YYYY-MM-DD
domain: [name | face | saju | safety | infra]
related: [경로/노트]
---
```

### 마크다운 평문 원칙

- Obsidian 백링크 `[[...]]`는 가능 (Git에서도 평문으로 보임)
- 일반 링크 `[제목](경로)`도 호환
- 백링크 우선, 일반 링크는 외부 자료에만
- 이미지·첨부는 가능하면 외부 링크

### 한글 파일명

- 영문이 안전하나 한글도 허용
- 공백 대신 `-` (예: `name-phase1-bulyong.md`)

---

## 7. AI 자체 한계 인정

### 환각 위험

- 제가 "기억하는" 결정은 신뢰 X
- **파일이 진실 소스** — 답변 전 vault/ Read
- "ADR-002에 따라"라고 말하기 전에 실제로 Read

### 컨텍스트 윈도 한계

- 매 답변마다 vault/ 전체 안 읽음
- 관련 폴더·키워드 Targeted Read
- 새 세션 시작 시 최소: `README.md` + `roadmap/INDEX.md` + 최근 `done/`

### 사용자가 검증할 수 있는 기준

1. 새 결정인데 ADR 파일 없으면 → 사용자가 지적
2. roadmap 항목 작업했는데 done/ 누락 → 사용자가 지적
3. 외부 보고서 받았는데 reports/ 없음 → 사용자가 지적

---

## 8. 코드와 vault/ 동시 관리

### PR 단위

코드 변경 + vault 변경을 **같은 커밋·PR**에 묶는다:

```
feat(name): 가족 서열 진단 모듈 (§1)

- engine/divination/name_hierarchy.py 신규
- 회귀 테스트 X건
- vault/decisions/ADR-008-family-hierarchy.md
- vault/done/name-hierarchy.md
- vault/roadmap/family-hierarchy-bulyong.md 제거 (done으로 이동)
```

### Git 메시지

- 코드 변경만이면 `feat`/`fix`/`docs` prefix
- vault 변경만이면 `docs(vault):`
- 둘 다이면 코드 prefix + 본문에 vault 변경 명시

---

## 9. 신뢰성 점검 — 매 답변 self-check

답변 마무리 전 다음 체크:

- [ ] 결정했으면 ADR 파일 있나
- [ ] 작업 완료면 done/ 있나
- [ ] roadmap 갱신했나
- [ ] 인용한 출처 references/ 있나
- [ ] 코드 변경했으면 회귀 통과·라이브 검증했나

---

## 10. 본 파일의 위치

- 본 파일: `사주/CLAUDE.md` (프로젝트 루트)
- 글로벌: `~/.claude/CLAUDE.md` (사용자 개인 — 본 파일과 별개)
- 우선순위: 글로벌(파일 쓰기 규칙·.claude 보호 등) > 본 파일

---

## 메타

- 작성: 2026-05-17
- 작성자: Technoetic (AI 협업)
- 관련 ADR: [[vault/decisions/ADR-007-obsidian-vault-introduced]]
- 변경 시: 본 파일도 immutable 원칙 적용 (큰 변경은 ADR + 새 절 추가)
