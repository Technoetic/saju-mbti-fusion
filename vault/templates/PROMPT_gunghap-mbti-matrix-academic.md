---
type: prompt_template
target: deepresearch
purpose: 궁합 MBTI 16×16 호환 매트릭스 — 학술 출처 + 인지기능 이론 검증
created: 2026-05-17
related_module: engine/saju/compat.py (라인 8 "MBTI 16×16 호환 매트릭스 (간이)")
related_adr:
  - ADR-010-name-sibling-factuality (사실성 분리)
  - ADR-014-saju-mbti-prediction-exception (단정 회피 정신 — 16유형은 사용자 입력)
  - ADR-006-legaltech-rejected (자문 거절 — 연애·결혼 자문 회피)
priority: medium
status: draft
related_report: ../reports/saju-mbti-correlation.md (관련)
---

# 딥리서치 프롬프트 — 궁합 MBTI 16×16 호환 매트릭스 학술 검증

## 사용법

본 프롬프트는 [engine/saju/compat.py](../../engine/saju/compat.py) 라인 8
명시 "MBTI 16×16 호환 매트릭스 **(간이)** — 인지 기능 거울/짝 기준"의 학술
출처 부재 결손 보강용.

현 매트릭스는 융 인지기능(Jungian Cognitive Functions) 거울/짝 이론 기반
"간이" 추정이며 학술 검증 없음. 본 프롬프트는 학술 출처 라이브 검증 가능한
호환 모델만 채택하여 매트릭스 보강.

**ADR-014 정합 의무**: 사주→MBTI 단정 예측은 영구 금지이나, 사용자가
**명시 입력한 두 MBTI 16유형 간 호환 매트릭스**는 별개 (사용자 자기보고
입력 기반). 본 프롬프트는 이 경계를 엄격히 유지.

---

## 프롬프트 본문

```
MBTI 16유형 × 16유형 호환 매트릭스의 학술 근거 + 인지기능 이론 검증을
조사·정리해주세요. 본 자료는 운세 SaaS 백엔드의 궁합 결정론 분석
(engine/saju/compat.py) 보강용이며, ADR-006 자문 거절 + ADR-010 사실성
분리 + ADR-014 단정 회피 정신을 따라야 합니다.

### 요구사항

#### 1. 인지기능 이론 학술 출처

융 분석심리학 + Myers 인지기능 스택 이론:
- Carl Jung 《심리유형론》(Psychologische Typen, 1921) 한국어 ISBN
- Isabel Briggs Myers 《Gifts Differing》(1980) 한국어 번역본 ISBN
- David Keirsey 《Please Understand Me II》(1998) ISBN

각 출처의 라이브 검증 가능 URL/ISBN/DOI 의무.

#### 2. 8 인지기능 매핑 결정론

다음은 본 시스템 [engine/saju/mbti_functions.py](../../engine/saju/mbti_functions.py)에
이미 구현된 표준 매핑 (논쟁 적은 영역):

```yaml
INTJ: [Ni, Te, Fi, Se]
INTP: [Ti, Ne, Si, Fe]
ENTJ: [Te, Ni, Se, Fi]
...
```

본 매핑은 융 표준이므로 채택. 본 프롬프트는 다음 16×16 호환 점수 산출
로직만 학술 출처로 검증:

(a) **거울(Mirror) 관계**: 같은 인지기능 + 다른 외향/내향
   - 예: INTJ(Ni-Te-Fi-Se) ↔ ENFP(Ne-Fi-Te-Si)?
(b) **짝(Dual) 관계**: 인지기능 보완
(c) **그림자(Shadow) 관계**: 인지기능 정반대

각 관계가 **학술 출처에 명시되어 있는가** 검증.

#### 3. KCI/Pubmed 한국어 MBTI 호환 연구

- KCI 등재 한국 심리학회·교육학회 논문
- 부부·연인 MBTI 일치도 통계 (있다면 표본·p-value 명시)
- 직장 팀 MBTI 호환 연구

**경고**: MBTI는 학계에서 재현성·구성 타당도 논쟁 큼 (NEO-PI-R·Big5와 대비).
본 프롬프트는 MBTI를 "검증된 도구"로 전제하지 않음 — 한계 명시 의무.

#### 4. 본 시스템 결손 영역 매핑

현 [engine/saju/compat.py](../../engine/saju/compat.py):

```
4. MBTI 16×16 호환 매트릭스
# MBTI 16×16 호환 매트릭스 (간이 — 인지 기능 거울/짝 기준)
def mbti_compat_score(type_a: str, type_b: str) -> int:
    """MBTI 두 유형 호환 점수 (1~9). 매트릭스에 없으면 6 (보통)."""
```

**갭**:
- "간이" 명시 — 학술 출처 0
- 1~9 점수 임계값 학술 검증 없음
- 거울/짝 관계 명시 부재
- 16×16 = 256 칸 전수 점검 미실시

#### 5. 결정론 호환 점수 명세 (1~9)

각 16×16 = 256 조합에 대해:

```yaml
type_a: "INTJ"
type_b: "ENFP"
score: 8  # 거울 관계 — Jung 인지기능 보완
relationship_type: "mirror" | "dual" | "shadow" | "similar" | "neutral"
academic_source:
  - "<Jung Psychologische Typen p.XX>"
  - "<Keirsey Please Understand Me II p.YY>"
disclaimer: "MBTI 학설 기반. 실제 관계는 다중 요인 영향. 자기보고식 검사 한계."
```

전수 점검 의무 또는 알고리즘 명시:
- (a) 전수 256 조합 점수표 제공
- (b) 또는 거울/짝/그림자 패턴 알고리즘으로 산출 + 학술 정당화

#### 6. ADR 정합 + 사용자 출력 면책

다음 표현 절대 금지:
- ❌ "당신은 OOO와 운명적 짝입니다" (운명론)
- ❌ "OOO와 결혼하면 행복합니다" (예언)
- ❌ "INTJ × ENFP = 95% 매칭" (정확도 표시 — ADR-014 정신 위반)
- ❌ "당신의 부부 관계 문제는 MBTI 때문입니다" (인과 단정)

채택 가능:
- ✅ "융 인지기능 이론상 INTJ와 ENFP는 거울 관계입니다. 본 결과는 학설이며
  실제 관계는 다중 요인 영향을 받습니다."
- ✅ 학파 명시 ("Jung·Myers·Keirsey 이론에 따르면")
- ✅ MBTI 한계 명시 ("자기보고식 검사이며 학계 재현성 논쟁이 있습니다")

#### 7. 회귀 테스트 데이터셋

본 시스템 회귀 검증용 30쌍:

```json
[
  {
    "id": "compat_001",
    "type_a": "INTJ",
    "type_b": "ENFP",
    "expected_score": 8,
    "expected_relationship": "mirror",
    "academic_source_required": "Jung 또는 Keirsey 인용",
    "expected_disclaimer": "융 인지기능 이론, 다중 요인 영향"
  }
]
```

#### 8. ADR-014 경계 명확화

본 시스템은 ADR-014로 "사주→MBTI 단정 예측 영구 금지"하나, 본 매트릭스는:
- 입력: 사용자 명시 자기보고 두 MBTI 16유형
- 출력: 16×16 호환 점수
- 사주와 무관 — 별개 모듈

본 경계가 명확히 유지되는지 매트릭스 설계상 점검 의무.

### 출력 형식

1. **학술 출처 표** (Jung·Myers·Keirsey·KCI 라이브 검증)
2. **8 인지기능 매핑 검증 결과**
3. **16×16 호환 매트릭스 YAML** (전수 256 조합 또는 알고리즘 명시)
4. **거울/짝/그림자 관계 학술 정당화**
5. **사용자 출력 면책 가이드라인**
6. **회귀 데이터셋 JSON** (30쌍)
7. **ADR-014 경계 명확화 보고**

### 검증 기준

- 모든 학술 인용 ISBN·페이지·DOI 라이브 검증 가능
- 가짜 인용 0건
- 운명론·정확도·인과 단정 표현 0건
- MBTI 한계 명시 의무
- 회귀 30쌍 이상
- ADR-014 경계 명확

위 조건 미충족 시 ADR-010·006·014에 따라 거부됩니다.
```

---

## 본 시스템 채택 절차

1. `/squeeze-report` 사실성 분리 + ISBN/KCI 라이브 검증
2. ACCEPT 후보:
   - 신규 ADR (궁합 MBTI 매트릭스 정책 — 융 표준 명시 채택)
   - `engine/saju/compat.py` 매트릭스 보강 + "간이" 표기 정정
   - 회귀 30건 추가
   - vault/references/ Jung·Myers·Keirsey 출처 영속화

## 면책

- ADR-006 자문 거절 + ADR-010 사실성 분리 + ADR-014 단정 회피 동시 적용
- 운명론·정확도·인과 단정 절대 금지
- 사용자 명시 두 MBTI 입력 기반만 (사주→MBTI 예측 X)
- MBTI 학계 한계 명시 의무
- 본 매트릭스는 "참고 학설"이며 결혼·연애·이직 결정 자문 아님
