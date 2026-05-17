---
type: prompt_template
target: deepresearch
purpose: 대법원 인명용 한자 9389자 — 1,070자 추가분 전수 JSON 데이터 추출 (빈 약속 차단 강화 버전)
created: 2026-05-17
related_module: data/korean_hanja_unihan.json (현 8,525자) + engine/divination/name_unihan.py
related_adr:
  - ADR-001-name-deterministic-engine
  - ADR-010-name-sibling-factuality
priority: high
status: draft
related_report: ../reports/hanja-9389-source-research (DEFER 사례 — 빈 약속 차단)
supersedes: PROMPT_korean-hanja-9389-source (의도적 삭제, 빈 약속 답습 문제)
---

# 딥리서치 프롬프트 — 대법원 9389자 1,070자 추가분 전수 JSON 데이터

## 사용법

본 프롬프트는 직전 보고서 (`vault/reports/hanja-9389-source-research.md`)
DEFER 사례 해소용. 이전 PROMPT (PROMPT_korean-hanja-9389-source.md)는
"공식 출처 라이브 확보"만 명시했으나 보고서가 샘플 15건만 제공하고 1,070자
전체 데이터 미제공으로 빈 약속 차단됨.

본 강화 버전은 **샘플 기각 + 전수 JSON 강제 + 회귀 30쌍 실 데이터 명시 의무**.

---

## 프롬프트 본문

```
대한민국 대법원 가족관계의 등록 등에 관한 규칙 제3151호 (2024-06-11 시행)
인명용 한자표 별표 1 신규 추가 1,070자의 **전수 JSON 데이터**를 추출·정리해주세요.

본 자료는 운세 SaaS 백엔드 결정론 엔진 데이터 보강용이며 ADR-010 사실성
분리 의무 + **빈 약속 절대 금지**.

### 절대 요구사항 (위반 시 보고서 전체 거부)

#### 1. 1,070자 전수 JSON (샘플 X, 부분 X, 전수 의무)

다음 형식으로 **1,070자 모두** 제공:

```json
[
  {
    "char": "鬰",
    "reading": "울",
    "meaning": "답답할 울",
    "radical": "鬯",
    "kangxi_strokes": 29,
    "is_scourt_approved": true,
    "added_in_2024": true
  },
  ...
  (1,070개 객체 전수)
]
```

**빈 약속 금지 패턴 (보고서 거부 사유)**:
- ❌ "샘플 15건은 다음과 같다 ... (나머지 1,055건은 별도 첨부)" — 거부
- ❌ "구조는 다음과 같다 ... 실제 데이터는 HWPX 파일 참조" — 거부
- ❌ "1,070자 목록은 부록 참조" — 거부 (부록 없으면 빈 약속)
- ❌ "본 보고서에는 핵심 케이스만 ..." — 거부

**보고서 본문에 1,070개 JSON 객체 완전 명시 의무**.

#### 2. 회귀 테스트 30쌍 실 데이터

다음 형식으로 **30쌍 모두** 본문 명시:

```json
[
  {
    "id": "hanja_test_001",
    "char": "鬰",
    "expected_reading": "울",
    "expected_kangxi_strokes": 29,
    "expected_radical": "鬯",
    "expected_in_scourt_2024_addition": true
  },
  ...
  (30개 전수)
]
```

빈 약속 금지 (위 동일).

#### 3. 학술·법적 출처 라이브 검증

- 대법원규칙 제3151호 (2024-06-11) — law.go.kr URL 의무
- 별표 1 첨부 HWPX 또는 PDF 다운로드 가능 URL
- 추출 방법 명시 (HWPX 파싱 도구·OCR 등)

#### 4. 라이선스 검증

- 저작권법 제7조 (국가 법령 저작권 배제) 인용
- 상업 SaaS 재배포 가능 명시
- data.go.kr 공공데이터 라이선스 (있다면)

#### 5. 시스템 무결성 안전성 명시

본 데이터로 다음 시스템 작동 보장:
- 현재 8,525자 + 신규 864자 (set difference) = 9,389자
- `engine/divination/name_unihan.py _verify_scourt_compliance()` 통과
- 기존 entries 8,525자 정합성 유지 (덮어쓰기 금지)

#### 6. 본 시스템 결손 영역 정밀 매핑

현 상태 (직접 검증):
- `data/korean_hanja_unihan.json` 8,525건 (list 형식)
- `engine/divination/name_unihan.py` 라인 266-276: expected_count=9389
- 결손: 864자 (9,389 - 8,525)

본 보고서가 제공해야 할 것:
- 1,070자 전체 JSON → set difference 후 본 시스템 추가 864자 추출 가능
- 1,070자 중 8,525자에 이미 포함된 206자 (1070 - 864 = 206)는 검증용

### 출력 형식

1. **1,070자 전수 JSON 배열** (각 객체 최소 6필드)
2. **회귀 30쌍 JSON 배열** (각 객체 최소 5필드)
3. **출처 표** (law.go.kr URL·HWPX·법령 인용)
4. **라이선스·재배포 보고**
5. **시스템 통합 명세** (set difference + 기존 entries 보존)

### 검증 기준

- 1,070자 정확 개수 (오차 0)
- 30쌍 정확 개수
- 모든 char가 유효한 한자 (Unicode 유효)
- kangxi_strokes 1~50 범위
- 외부 URL 라이브 검증 가능

**위 기준 미충족 시 ADR-010에 따라 보고서 전체 거부**.

### 본 프롬프트 차별점 (이전 PROMPT 빈 약속 차단)

| 영역 | 이전 PROMPT | 본 강화 버전 |
|---|---|---|
| §5 1,070자 | "샘플 + 출처 명시" 허용 | **전수 본문 명시 의무** |
| §7 회귀 | "30쌍 구축" 명시만 | **30쌍 실 데이터 본문** |
| 빈 약속 | 거부 조건 모호 | **명시 거부 패턴 5건** |

```

---

## 본 시스템 채택 절차 (보고서 수령 후)

1. `/squeeze-report` 사실성 분리:
   - 1,070자 전수 JSON 존재 여부 직접 카운트 검증
   - 회귀 30쌍 본문 데이터 존재 여부 직접 카운트 검증
   - 둘 다 충족 시 ACCEPT, 미충족 시 즉시 영구 거부
2. ACCEPT 후보:
   - `data/korean_hanja_unihan.json` set difference 864자 추가 → 9,389자
   - `engine/divination/name_unihan.py _verify_scourt_compliance()` 활성화
   - 회귀 30쌍 → `tests/data/regression_hanja_2024.json` 신규
   - 신규 ADR (대법원 9389자 완전 수록 정책)
   - vault/references/대법원-인명용-한자-2024.md 영속화

## 면책

- ADR-010 사실성 분리 의무
- 빈 약속 답습 절대 금지 (위반 시 보고서 전체 거부)
- 사용자 출력 인과 표현 절대 금지 (한자 풀 = 객관 데이터)
- 라이선스 위반 시 채택 거부

## 본 프롬프트의 결정적 차별점

이전 PROMPT_korean-hanja-9389-source.md는 의뢰 결과 보고서 §5에 샘플 15건만
제공하여 빈 약속 차단 → DEFER. 본 강화 버전은:

1. **전수 JSON 강제 + 거부 패턴 5건 명시** (보고서가 빈 약속 시 거부 사유 명확)
2. **회귀 30쌍 실 데이터 강제** (보고서 §7 "구축하였다" 답습 방지)
3. **시스템 무결성 안전성 검증 의무** (ValueError 차단)

→ 사용자 재의뢰 시 본 프롬프트로 빈 약속 차단 가능.
