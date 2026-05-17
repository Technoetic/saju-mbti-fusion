---
type: external_report
status: received_with_caveats
date: 2026-05-17
source: deepresearch
domain: name
applied_to:
  - "engine/divination/name_sibling_preference.py (125자, 20 tests PASS)"
  - "data/name_sibling_preference.json (entries 125, gender 분포 neutral 101/male 20/female 4, policy 분포 hard_block_always 5/only_child_pass 12/only_child_warning 3)"
  - "vault/references/baekjungsukgye.md (백중숙계 원전 노트)"
neo4j_synced: false
factuality: mixed
related:
  - decisions/ADR-001-name-deterministic-engine.md
  - decisions/ADR-006-legaltech-rejected.md
  - decisions/ADR-010-name-sibling-factuality.md
  - done/name-phase3-sibling-preference.md
  - reports/saju-app-spec.md
original_file: ../../한국 정통 성명학의 서열별 상대적 불용한자 판정 알고리즘 및 데이터베이스 구축 심층 보고.md
adr_017_first_application: "2026-05-17 (분석/판정 분리 절차 첫 적용)"
permanently_rejected:
  - "흉화 물리 발현 (혈관·뇌신경·관절·단명·요절·관재구설·이별수·과부살) — ADR-006/010 1차 확정"
  - "통계적 유의성 권위 수사 (p-value·표본 0) — 1차 확정"
  - "학파별 흉화 빈도 정량 비교 (출처 0) — 1차 확정"
  - "우주적 기운·파동·역행 (형이상학 인과) — 1차 확정"
  - "마스킹된 ISBN 출처 인용 — ADR-010 검증 불가 1차 확정"
  - "§4 학파별 차이 조율 — ADR-002 학파 회피 위반 (본 호출 추가 확정)"
already_implemented:
  - "§1 4 카테고리 분류 → name_sibling_preference.py CATEGORY_*"
  - "§1-D 외동 정책 (hard_block_always/only_child_pass/only_child_warning) → JSON policy 필드 5/12/3"
  - "§2 Gender 변수 (male/female/neutral) → JSON gender 필드 + gender_mismatch 처리"
  - "§3 Severity 재정의 (ABSOLUTE/ADVISORY → STRONG/WEAK/CONDITIONAL, 호칭 직접성으로 재명명)"
  - "§5 현대 가정 5 예외 (큰누나 → 입양 → 재혼 → 쌍둥이 순서) → _apply_modern_exceptions()"
  - "출처 일괄 표기 ('전통 관습') → sources 필드"
deferred_pending_decision:
  - "C4 — §6 충돌 우선순위 규칙 (81수리 대길수·용신 오행 상쇄·추천 vs 진단 모드 분기): name_sibling_preference.py 존재하나 name_scoring.py에서 호출 0. ADR-002 옵션 A 디폴트 + ADR-015 옵션 B 정합성 사전 검증 필요 + 추천/진단 UX 결정 사업부 협의 의무"
  - "C5 — 복합 예외 우선순위 (입양+쌍둥이 동시 등) 명리학적 정당성 명시 및 회귀 보강"
analyst_misclassifications_in_this_call:
  - "C1: 분석 에이전트 142자 추정 오류 (실제 entries 125자, 메타 키 5개 포함 추정)"
  - "C2/U3: conflict_resolution 필드 vs policy 필드 중복 추출 (C4로 흡수되어야 함)"
  - "C6: hard_block 5/pass 12/warning 3 정량 (분석 에이전트 2/13/3 오추론)"

# 가족 서열별 상대적 불용한자 — 사실성 검토 분리

## 사실성 분리 원칙

본 보고서는 **검증 없이 영속화하지 않는다** (사용자 지적 2026-05-17).
보고서 내용을 다음 3 등급으로 분리한다:

| 등급 | 의미 | 시스템 반영 |
|---|---|---|
| 🟢 **팩트** | 문헌·자전·관습으로 검증 가능 | 본문화 가능 |
| 🟡 **구조** | 검증 불가하나 시스템 설계 명제로 채택 | 객관 라벨로 본문화 |
| 🔴 **도그마** | 검증 불가 + 위해 가능성 (의료·법률 인과 주장) | **폐기** |

## 🟢 팩트 — 채택 가능

### 1. 한자 어휘 의미

보고서 본문의 한자별 "뜻" 컬럼(예: `長`=길다/어른, `季`=막내, `仲`=버금)은
한국어 한자 자전 (네이버 한자사전·다음 한자사전·교학사 신옥편)으로 **개별
검증 가능**. 약 128자 → references/ 노트로 자전 출처 명시 후 채택.

### 2. 백중숙계(伯仲叔季) 호칭 체계

- 출전: 『의례(儀禮)』, 『예기(禮記)』
- 의미: 형제 출생 순서를 칭하는 고전 호칭 (伯=장자, 仲=차자, 叔=셋째, 季=막내)
- 검증: 한국·중국 고전 문헌 다수 일관 확인
- → references/baekjungsukgye.md 별도 노트로 정리

### 3. 학파 명칭의 실존

- 마의상법(麻衣相法): 진(陳)나라 마의도자 전승, 송대 정리. 관상학 고전.
- 유장상법(柳莊相法): 명대 원충철 저. 관상학 고전.
- 신상전편(神相全編): 명대 진단(陳摶) 등 편찬. 상법 종합서.

**검증된 사실**: 위 3종 모두 **관상학(觀相學)** 문헌이며 **성명학·작명학
전문서가 아님**. 보고서가 이들을 작명 학파로 호명한 것은 부정확한 라벨.
한국 현대 작명원이 관상학 문구를 차용하는 관습은 별개로 존재.

### 4. 현대 가정 형태의 사실

- 외동/형제/재혼/입양/쌍둥이는 호적·생물학상 명확히 구분되는 **사실**
- 큰누나 + 위 오빠 1명의 호칭 패턴 역시 한국어 관습 사실

## 🟡 구조 — 시스템 설계 명제로 채택

### 5. 4 카테고리 분류

`firstborn_only / lastborn_only / middleborn_only / only_child_only`

**근거**: 백중숙계 호칭 체계의 직접 매핑. 인과적 흉화 입증은 없음.
**시스템 표현**: "전통 관념상 ○○ 서열에 더 자주 사용되는 글자" 라벨.

### 6. 3단계 Severity

`ABSOLUTE / ADVISORY / CONDITIONAL`

**근거**: 시스템 내부 처리 정밀도 분류용. 흉화 강도가 아니라 **부적합도
강도**(서열 호칭 의미와의 직접성).
**시스템 표현**: "강한 부적합 / 약한 부적합 / 사주 보완 가능"으로 변환.

### 7. Gender 변수 (male/female/neutral)

**근거**: `兄·伯·甲`은 전통 남성 호칭, `姉·媛`은 전통 여성 호칭이라는 **언어
관습**. 음양 부조화로 인한 "과부살" 인과 주장은 도그마(🔴).
**시스템 표현**: 성별 선호 매칭 (사용자 입력 성별과 한자 호칭 성별 일치 여부).

### 8. 5 현대 가정 예외 처리

| 예외 | 시스템 표현 |
|---|---|
| 외동 | 형제 서열 부적합 검사 전체 skip (기준 부재) |
| 재혼 | 사용자 입력 "생모 출산 순서"를 신뢰 (의문 시 사용자에게 묻기) |
| 입양 | 사용자 입력 "법적 서열"을 신뢰 |
| 쌍둥이 | 출산 순서 적용 + 부적합도 1단계 완화 (시스템 설계 선택) |
| 큰누나(위 오빠) | firstborn → middleborn으로 변환 (호칭 사실 반영) |

### 9. 충돌 우선순위 규칙

```
IF 81수리 대길수 AND 서열 ABSOLUTE: 서열 표시 우선
IF 자원오행 옵션 A 추천 일치 AND 서열 ADVISORY: 권고 등급 1단계 완화
IF 추천 모드: ABSOLUTE/ADVISORY 한자 제외
IF 진단 모드: 상쇄 로직 적용
```

→ 시스템 설계 명제로 채택. **인과 주장 아님**.

## 🔴 도그마 — 폐기

다음은 검증 불가 + 위해 가능 → **시스템 반영·사용자 노출 금지**:

### 10. 흉화의 물리적 발현 주장

- "혈관계·뇌신경계 쇠약" / "관절 질환" / "단명" / "요절" / "신체 훼손"
- "관재구설" / "감금" / "법적 분쟁" / "가산 탕진"
- "이별수" / "과부살" / "부부 파경" / "이혼"

**폐기 사유**: 의료·법률 인과 주장. [[../decisions/ADR-006-legaltech-rejected]]
원칙(법률·의료 자문 거절)과 정면 충돌. 사용자 출력 노출 절대 금지.

### 11. "통계적 유의성"이라는 수사

보고서가 반복 사용한 표현이나 **p-value, 표본 크기, 연구 설계, 데이터셋
어느 것도 명시되지 않음**. 권위 가장 문구로 판정 → 시스템 reason 필드에서
삭제.

### 12. 학파별 "흉화 인정 빈도" 정량 비교

"유장상법 ABSOLUTE 채택 빈도 압도적" 등 — 출처 0, 정량 데이터 0.
→ 사용자 노출·시스템 가중치 모두 불가.

### 13. 우주적 기운·파동·역행

형이상학 명제. 반증 불가. 본 시스템은 **결정론 코드**이며 형이상학적 인과
주장을 채택하지 않음. → 시스템 내부 표현에서 삭제.

### 14. 출처 마스킹

보고서가 `ISBN: 97889xxxxxxx`로 출판 정보를 마스킹한 것은 **실제 검증
불가능한 출처를 권위로 가장한 흔적**. 한자 데이터를 채택하더라도 본 학파
출전은 **"전승 관습"**으로만 라벨링, 학술 서지로 인용 금지.

## 본 시스템 반영 (사실성 분리 후)

### ✅ 채택 (🟢 + 🟡)

1. **모듈명 변경**: `name_sibling_bulyong` → `name_sibling_preference`
   - "불용(不用)"은 인과 주장 라벨 → "선호(preference)"로 객관화
2. **JSON 데이터** (`data/name_sibling_preference.json`): 보고서 128자 채택, 단
   - `severity`: `STRONG / WEAK / CONDITIONAL` (인과 강도 X, 호칭 직접성)
   - `reason`: 어휘 의미 + 호칭 사실만 (인과 주장 삭제)
   - `sources`: "전통 관습 (학파별 상세 미검증)"으로 일괄 표기
3. **5 현대 가정 예외 로직**: 위 8번 표 그대로 채택
4. **충돌 우선순위 규칙**: 9번 그대로
5. **사용자 출력 표현**:
   - "○○ 서열에 더 자주 사용되는 글자입니다."
   - "○○ 서열에서는 사용 빈도가 낮은 글자입니다."
   - "전통 관념상 부적합 표시이며, 의료·법률 자문이 아닙니다."

### ❌ 폐기 (🔴)

- 흉화 물리 발현 모든 표현
- "통계적 유의성" 표현
- 학파별 빈도 비교
- 우주적 기운·파동·역행
- 출판 서지 인용 (마스킹된 ISBN)

## 다음 액션

- [ ] **ADR-010**: "가족 서열 한자 선호 모듈 — 사실성 분리 원칙 채택"
  - 명시: 본 모듈은 인과적 흉화 예언이 아님
  - 명시: 의료·법률 자문 아님 (ADR-006 준수)
  - 명시: "전통 관습 참고용" 라벨
- [ ] `references/baekjungsukgye.md`: 백중숙계 호칭 체계 원전 노트
- [ ] `data/name_sibling_preference.json`: 128자 적재 (reason 객관화 작업 동반)
- [ ] `engine/divination/name_sibling_preference.py`: 모듈 구현
- [ ] 회귀 테스트: 카테고리 매칭 + 5 예외 + 충돌 우선순위
- [ ] `name_scoring.py` 통합 (`sibling_order` 파라미터 추가)
- [ ] vault/done/ + roadmap 이동

## 출처

- 본 보고서 원본: `사주/한국 정통 성명학의 서열별 상대적 불용한자 판정 알고리즘 및 데이터베이스 구축 심층 보고.md`
- 한자 어휘: 한국어 한자 자전 (개별 검증 필요)
- 백중숙계: 『의례』·『예기』 (references 노트 작성 예정)
- 본 보고서 자체의 학파 출전 인용: **검증 보류** (마스킹된 ISBN, 정량 데이터 부재)

## 2026-05-17 ADR-017 절차 첫 적용 결과

본 보고서는 1차 처리(2026-05-17)에서 ADR-010 사실성 분리 + 후속 본문화 완료
(done/name-phase3-sibling-preference)됐으나 ADR-017 분석/판정 분리 패턴은
미적용. 본 호출에서 절차 첫 적용 + 정밀 재정독.

### 분석 결과
- 후보 9건 (C1~C9) + 거부 2건 (R1·R2) + 사용자 결정 3건 (U1·U2·U3)

### 판정 결과
- **ACCEPT 0건** (실 본문화 작업 없음)
- **REJECT 7건**: C1·C2·C3·C6·C7·C8·C9 + R1·R2·U1·U3
- **DEFER 2건**: C4·C5

### 오케스트레이터 핵심 발견

| 후보 | 보고서 영역 | 본 시스템 실 구현 | 판정 |
|---|---|---|---|
| C1 | JSON 한자 개수 | 125자 entries (분석 142 오추론) | REJECT 정합 |
| C2 | conflict_resolution 필드 | policy 필드만 (§6과 혼동) | REJECT 중복 |
| C3 | Gender 변수 | neutral 101/male 20/female 4 + gender_mismatch | REJECT 이미 |
| C4 | **§6 충돌 우선순위** | **name_scoring.py 호출 0** | **DEFER 결손** |
| C5 | 복합 예외 우선순위 | 큰누나→입양→재혼→쌍둥이 (회귀 20 PASS) | DEFER 보강 |
| C6 | 외동 정책 분포 | 5/12/3 (분석 2/13/3 오추론) | REJECT 정합 |
| C7 | Severity 명명 | STRONG/WEAK/CONDITIONAL 재정의 완료 | REJECT 이미 |
| C8 | 마스킹 ISBN | sources "전통 관습" 일괄 | REJECT 이미 |
| C9 | §4 학파 조율 | ADR-002 학파 회피 정신 보존 | REJECT 위반 |

### 진짜 결손 영역 (C4)

본 시스템 결손 확인:
- name_sibling_preference.py 모듈 존재 + 125자 + 20 tests
- **name_scoring.py에서 sibling_preference 호출 0** (bulyong만 호출)
- §6 충돌 우선순위 4규칙 모두 미구현:
  - 81수리 대길수 + 서열 ABSOLUTE 우선
  - 자원오행 옵션 A 일치 + 서열 ADVISORY 1단계 완화
  - 추천 모드 / 진단 모드 분기

### DEFER 사유

- ADR-002 옵션 A 디폴트 무결성 검증 필요 (옵션 B 오행 상쇄가 침해 우려)
- ADR-015 옵션 B (이재승 억부론) 정합성 사전 검증 필요
- 추천 vs 진단 모드 분기 = UX 사업 결정 영역
- 사업부 협의 후 별도 ADR 작성 필수

### 분석 에이전트 오류 패턴

- C1: 142자 추정 (실제 125, 메타 키 5개 포함 추정)
- C6: 2/13/3 추정 (실제 5/12/3)
- C2/U3 중복 (C4로 흡수되어야 함)

→ 분석 에이전트 프롬프트 보강: "정량 후보 추출 시 실 JSON 파일을 직접 카운트 검증 의무" 추가 필요

### 결론

본 호출도 코드 변경 0. 비용 (Haiku 2회 ≈ $0.02)으로:
- ADR-017 절차 첫 적용
- frontmatter `permanently_rejected` 6건 + `already_implemented` 6건 + `deferred_pending_decision` 2건 영속화
- C4 결손 영역 명확화 — 별도 ADR + 사업부 협의 후 본문화 가능

## 메타

- 영속화: 2026-05-17 (사실성 분리 재작성)
- ADR-017 첫 적용: 2026-05-17 (코드 변경 0, 절차 정합화 + 결손 영역 명확화)
- 본 노트는 immutable. 본문화 시 새 done + ADR.
- 검토 원칙: **팩트가 아닌 것은 지식이 아님** (사용자 지적 2026-05-17)
