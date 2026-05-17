---
type: report
date: 2026-05-18
domain: [face, meta]
status: verification_complete
verified_by: validator_agent
related: [vault/roadmap/physiognomy-knowledge-db, vault/roadmap/facial-feature-classification]
---

# /propose-research Phase A 산출물 독립 검증 — 2026-05-18

## 검증 범위

- N1: `PROMPT_physiognomy-knowledge-db.md` + `.deepresearch.txt` 페어
- N2: `PROMPT_facial-feature-classification.md` + `.deepresearch.txt` 페어
- 정정 후보: 0건
- 삭제 후보: 0건

## 검증 결과 (YAML)

```yaml
verdicts:
  new_prompts:
    - id: "N1"
      file_pair:
        meta_md: "vault/templates/PROMPT_physiognomy-knowledge-db.md"
        deepresearch_txt: "vault/templates/PROMPT_physiognomy-knowledge-db.deepresearch.txt"
        both_exist: true
      module_directory_exists: true
      module_already_exists: false
      module_pool_actual_state: "engine/divination/: 947+532+324 = 1803 라인 (face_reading.py, face_scoring.py, face_shape.py 기존 모듈)"
      duplicate_of: null
      adr_compliance:
        ADR-002: OK
        ADR-004: N/A
        ADR-005: OK
        ADR-006: OK
        ADR-010: OK
        ADR-018: OK
        ADR-022: OK
      deepresearch_input_validation:
        no_project_identifier_leak: true
        leaked_patterns: []
        no_yaml_frontmatter: true
        self_contained: true
      verdict: "ACCEPT"
      rationale: "PROMPT.md 문서가 ADR 정합성 명확히 함 (ADR-005 Stage 2 Gemini입력, ADR-010 사실성 분리 강제, ADR-022 부위별 확장). deepresearch.txt는 자족적이고 출처 검증 명시 (KCI/DBpia/민족문화대백과 우선). 모듈 신규 및 결손 부재(부위별 형상) 확인. 페어 완전."
    - id: "N2"
      file_pair:
        meta_md: "vault/templates/PROMPT_facial-feature-classification.md"
        deepresearch_txt: "vault/templates/PROMPT_facial-feature-classification.deepresearch.txt"
        both_exist: true
      module_directory_exists: true
      module_already_exists: false
      module_pool_actual_state: "engine/divination/: 기존 face_reading.py(947줄)·face_scoring.py(532줄)·face_shape.py(324줄) 존재. face_shape.py는 5형(목·화·토·금·수) 윤곽분류만 수행, 부위별(코·눈썹·눈·입·귀) 형상 분류 함수 부재 확인 (grep -E classify_nose_shape|classify_eyebrow_shape|... → 0hit)."
      duplicate_of: null
      adr_compliance:
        ADR-004: OK
        ADR-005: OK
        ADR-006: OK
        ADR-010: OK
        ADR-018: OK
        ADR-022: OK
      deepresearch_input_validation:
        no_project_identifier_leak: true
        leaked_patterns: []
        no_yaml_frontmatter: true
        self_contained: true
      verdict: "ACCEPT"
      rationale: "PROMPT.md가 ADR-022 패턴 정합 명시 (5형 윤곽과 별개 부위 단위 확장). deepresearch.txt는 MediaPipe 478 키포인트·한국인 인체측정학 KCI 출처 기반 구체적 임계값 조사 의뢰로 자족적. 기존 korean-face-anthropometry.md (106줄, 이미 ADR-022 근거)와의 충돌 없음 (N2는 부위 단위 확장). 모듈 신규 확인. 페어 완전."
  corrections: []
  deletions: []

summary:
  new_accepted: 2
  new_rejected: 0
  should_proceed: true
  notes: "
  모든 검증 항목 통과. 정합성 요약:
  
  1. 모듈 실존 확인:
     - engine/divination/ 디렉토리 실존 ✓
     - 신규 모듈(physiognomy_knowledge.py, facial_feature_classifier.py) 부재 ✓
     - 중복 명칭 검사 → 0hit ✓
  
  2. 모듈 풀 결손 검증:
     - N1 결손: 부위별 형상(복코·매부리코·앙월구·삼백안 등) 분류 — 실제로 코드 내 검출 0hit ✓
     - N2 결손: face_shape.py가 5형만 수행, 부위 단위 분류 함수 부재 확인 ✓
  
  3. ADR 정합 점검:
     - ADR-002 (학파 회피): N1은 '옛 관상학에서 이르길~' 투명 어조 명시 ✓, N2는 객관 기하학만 ✓
     - ADR-005 (Opus Vision): N1·N2 모두 Stage 2 Gemini(자연어 LLM) + 코드 DB 인용 패턴 적합 ✓
     - ADR-006 (자문 거절): N1·N2 모두 '운명·길흉 무관' 면책 명시 ✓
     - ADR-010 (사실성 분리): N1 사실성 3등급 분리 강제(KCI 검증), N2 결정론 분류(객관)만 ✓
     - ADR-018 (골든셋): N2 5형 윤곽 vs 부위 형상 다른 영역 정합 ✓
     - ADR-022 (face_shape 5형): N2가 명시적으로 '5형 윤곽과 별개' 부위 단위 확장 의뢰 ✓
  
  4. 입력본 페어 의무:
     - 각 PROMPT .md + .deepresearch.txt 페어 존재 ✓
     - .deepresearch.txt 누설 검사:
       · step0\d\d|\.ps1|\.claude/|CLAUDE\.md|progress\.json 등 프로젝트 내부 식별자 → 0hit ✓
       · vault/|engine/divination|face_reading|face_scoring 같은 내부 경로 → 0hit ✓
       · YAML frontmatter (첫 줄 '---') → 없음 ✓
       · 자족성: 본 프로젝트 컨텍스트 없이 의뢰 가능 (배경·목표·요구사항·출력 형식 모두 명시) ✓
  
  5. 공개 기술 용어 허용 확인:
     - N1: MediaPipe, KCI, DBpia, 민족문화대백과, 학파 명칭(마의·유장·신상전편) 등 — 모두 공개 도메인 ✓
     - N2: MediaPipe Face Landmarker 478, 한국인 안면 인체측정학, KCI 출처 — 공개 도메인 ✓
  
  결론: 두 PROMPT 페어 모두 사실성 분리·ADR 정합·누설 없음·자족성 기준을 만족. 
  본문화 진행 권장 (Phase B Haiku 검증 → squeeze-report → 모듈화 절차 진행 가능)."
```

## 상세 검증 로그

### 1. 파일 실존 검증

```
✓ vault/templates/PROMPT_physiognomy-knowledge-db.md 실존
✓ vault/templates/PROMPT_physiognomy-knowledge-db.deepresearch.txt 실존
✓ vault/templates/PROMPT_facial-feature-classification.md 실존
✓ vault/templates/PROMPT_facial-feature-classification.deepresearch.txt 실존
✓ engine/divination/ 디렉토리 실존
```

### 2. 모듈 중복 검사

```
✗ engine/divination/physiognomy_knowledge.py — 미존재 (신규 OK)
✗ engine/divination/facial_feature_classifier.py — 미존재 (신규 OK)
```

### 3. 모듈 풀 상태

```
engine/divination/ 기존 모듈 (라인):
  · face_reading.py: 947줄
  · face_scoring.py: 532줄
  · face_shape.py: 324줄
  · 합계: 1,803줄

N1 결손 검증 (부위별 형상):
  grep -rE "복코|매부리코|앙월구|삼백안" → 0hit ✓
  grep -rE "physiognomy_knowledge|PHYSIOGNOMY_KNOWLEDGE" → 0hit ✓

N2 결손 검증 (부위 형상분류 함수):
  grep -E "classify_nose_shape|classify_eyebrow_shape|classify_eye_shape|classify_mouth_corner|classify_ear_shape" → 0hit ✓
  face_shape.py 내용: 5형(목·화·토·금·수) 윤곽분류만, 부위 단위 분류 함수 없음 ✓
```

### 4. ADR 정합성

#### ADR-002 (학파 회피)
- **N1**: PROMPT_physiognomy-knowledge-db.md §64 명시: "사용자 출력에 '옛 관상학에서 이르길~' 어조 명시 의무" → 단정 회피 설계 ✓
- **N2**: PROMPT_facial-feature-classification.md §65 명시: "분류는 객관 기하학, 운명 매핑은 별도" → 학파 해석 차단 ✓

#### ADR-005 (Claude Opus Vision + 2단계 파이프라인)
- **N1**: "Stage 2(Gemini 자연어 풀이) + 코드 DB 인용" 패턴 적합 ✓
- **N2**: "결정론 분류 + Stage 2 LLM 인용" 패턴 적합 ✓

#### ADR-006 (법률·의료 자문 거절)
- **N1**: "§58 면책: ADR-006 자문 거절 — 의료·법률·금융 운명 단정 금지" ✓
- **N2**: "§68 면책: ... 사용자 출력 자동 면책 (운명·길흉 무관 명시)" ✓

#### ADR-010 (사실성 분리)
- **N1**: "§49 본 PROMPT는 ADR-010 사실성 분리 정신 의무 — 가짜 인용·빈 약속 금지", "§69-130 검증 기준 명시 (출처 URL 라이브 검증, 가짜 인용 차단)" ✓
- **N2**: "§154-163 검증 기준: 임계값 한국인 인체측정학 학술 출처 검증, 가짜 통계 금지" ✓

#### ADR-018 (face-golden-set-policy)
- **N2**: "§47 ADR-022 정합 — N2는 부위 단위 확장 패턴" 명시, 5형 윤곽과 분리 ✓

#### ADR-022 (face_shape 5형)
- **N2**: "§10 ADR-022로 얼굴 윤곽 5형(목·화·토·금·수) 결정론 분류는 완료. 본 PROMPT는 **부위 단위 확장**" 명시 ✓

### 5. 입력본 누설 검사

#### N1 deepresearch.txt
```
grep -E "step0\d\d|\.ps1|\.claude/|CLAUDE\.md|mx-tag-validator|trust5-validator|progress\.json|step-progress-writer|vault/|engine/divination|face_reading|face_scoring|face_shape" → 0hit ✓
YAML frontmatter (첫 줄 '---'): 없음 ✓
자족성: 배경(라인1-16) → 목표(라인17-87) → 카테고리(라인29-66) → 요구사항(라인68-85) → 출력형식(라인87-113) → 검증기준(라인120-130) 모두 명시 ✓
```

#### N2 deepresearch.txt
```
grep -E "step0\d\d|\.ps1|\.claude/|CLAUDE\.md|mx-tag-validator|trust5-validator|progress\.json|step-progress-writer|vault/|engine/divination|face_reading|face_scoring" → 0hit ✓
YAML frontmatter: 없음 ✓
자족성: 배경(라인4-12) → 목표(라인14-23) → 부위6종(라인25-86) → 요구사항(라인88-104) → 참고 출처(라인105-119) → 출력형식(라인121-150) → 검증기준(라인154-163) 모두 명시 ✓
공개 라이브러리 참고(라인105-119): DBpia URL 4건, MediaPipe 공식 문서 언급 — 누설 아님 ✓
```

### 6. 기존 PROMPT 풀 확인

```
find vault/templates/ -name "PROMPT_*.md" → 2건 (본 N1·N2만, 기존 0건) ✓
```

## 최종 판정

**모두 ACCEPT.** 본문화 진행 가능.
