---
type: prompt_template
target: deepresearch
purpose: A13 social_unconscious v3 — 사회적 무의식 DB 클러스터링 (현재 TODO)
created: 2026-05-17
related_module: engine/agents/social_unconscious.py (v3 TODO)
related_adr:
  - ADR-006-legaltech-rejected (자문 거절)
  - ADR-010-name-sibling-factuality (사실성 분리)
  - ADR-014-saju-mbti-prediction-exception (단정 회피 정신)
priority: medium
status: draft
post_traffic: true  # 운영 데이터 누적 후 가치 평가 가능
---

# 딥리서치 프롬프트 — A13 Social Unconscious v3 (사회적 무의식 DB 클러스터링)

## 사용법

본 프롬프트는 본 시스템 꿈해석 멀티에이전트 오케스트레이터의 명시 TODO
영역 (`engine/agents/__init__.py` A13 v3 — DB 클러스터링)을 위한 학술
근거 조사. 운영 데이터 누적 전 사실성 분리 의무.

Erich Fromm "사회적 무의식" + Jung "집단무의식" + 현대 사회심리학
연구 학술 출처. 단정·예언 절대 금지 (ADR-014 정신).

---

## 프롬프트 본문

```
Erich Fromm "사회적 무의식(social unconscious)" 개념 + Jung "집단무의식
(collective unconscious)" + 현대 사회심리학(소셜 미디어 시대 공유 꿈
패턴 연구)을 결정론 클러스터링 학술 근거로 조사·정리해주세요.
본 자료는 꿈해석 SaaS의 사회적 무의식 에이전트(A13 v3) 보강용이며,
ADR-010 사실성 분리 + ADR-014 단정 회피 정신을 따라야 합니다.

### 요구사항

#### 1. 학술 출처 라이브 검증

- Erich Fromm 《인간의 마음》(1964) ISBN
- Jung 《원형과 집단무의식》 ISBN
- KCI 등재 한국 사회심리학·문화심리학 논문 (꿈·세대 무의식)
- 한국학중앙연구원 한국민족문화대백과사전 (한국 토속 집단 표상)

각 출처 라이브 검증 가능 URL/ISBN 의무.

#### 2. 사회적 무의식 ↔ 한국 시대 문화 클러스터 매핑

각 시대별 한국 집단 표상 (학술 검증):
- 일제강점기 (1910-1945)
- 한국전쟁기 (1950-1953)
- 산업화기 (1960-1980)
- 민주화기 (1987-2000)
- IMF·금융위기 (1997-2010)
- 디지털 전환기 (2010-2025)

각 시대 표상은:
- KCI 등재 한국 문화심리학·역사심리학 논문 출처
- 객관 라벨 (인과 단정 X)
- 사용자 출력 면책 의무

예시 형식:
```yaml
cluster: "IMF_collective_anxiety"
period: "1997-2010"
symbols: ["실직", "가족 해체", "전세 압박"]
academic_source: "<KCI URL: 한국심리학회지 IMF 관련 논문>"
disclaimer: "한국 IMF 시대 집단 표상 추정 — 개인 경험과 다를 수 있음"
```

#### 3. ADR-010 + ADR-014 정합

다음은 채택 불가:
- ❌ "당신의 꿈은 IMF 트라우마 때문입니다" (단정)
- ❌ "한국인은 모두 일제 트라우마를 가지고 있다" (집단 단정)
- ❌ "디지털 네이티브 세대는 OOO 꿈을 꾼다" (세대 단정)

채택 가능:
- ✅ "당신의 꿈에 등장하는 [실직] 모티프는 한국 IMF 시기 집단 표상에서
  자주 보고된 패턴입니다. 본 결과는 통계적 경향이며 개인 해석은
  다를 수 있습니다."
- ✅ "Fromm 사회적 무의식 학설에 따르면..." (학파 명시)
- ✅ 다중 해석 가능성 제시

#### 4. DB 클러스터링 알고리즘 명세

본 시스템 A13 v3 신규 모듈 후보:

```python
def cluster_social_unconscious(
    dream_text: str,
    user_birth_year: int,
    user_locale: str = "KR",
) -> dict:
    """
    꿈 텍스트의 사회적 무의식 클러스터 식별 (결정론).

    Returns:
        {
            "cluster_id": "IMF_collective_anxiety",
            "period": "1997-2010",
            "matched_symbols": ["실직", "전세"],
            "match_confidence": "low" | "medium" | "high",
            "alternative_clusters": [...],  # 다중 가능성
            "disclaimer": "한국 IMF 시대 집단 표상 추정",
            "academic_sources": [...]
        }
    """
```

#### 5. 운영 데이터 의존성

본 후보는 **운영 데이터 누적 후 가치 발현** 영역:
- 실제 한국 사용자 꿈 보고 → 클러스터 보정
- 시기별 분포 → 학술 근거 검증
- 운영 트래픽 누적 전 학습은 부정확 위험

본 프롬프트는 **학술 근거만 우선 영속화** + 운영 데이터 누적 후 실제
클러스터링 알고리즘 본문화 (ADR-014 단정 회피 정신).

#### 6. 회귀 테스트 데이터셋

본 시스템 회귀 검증용 20쌍 (학술 검증된 표상):

```json
[
  {
    "id": "soc_unc_001",
    "dream_text_kr": "회사에서 해고당하는 꿈",
    "user_birth_year": 1965,
    "expected_cluster_candidates": ["IMF_collective_anxiety", "1997_lay_off"],
    "expected_disclaimer": "한국 IMF 시대 집단 표상 추정"
  }
]
```

### 출력 형식

1. **학술 출처 표** (Fromm·Jung·KCI 라이브 검증)
2. **시대별 한국 집단 표상 클러스터 YAML** (학술 출처 명시)
3. **결정론 클러스터링 함수 명세**
4. **사용자 출력 면책 가이드라인**
5. **운영 데이터 의존성 명시**
6. **회귀 데이터셋 JSON** (20쌍)

### 검증 기준

- 모든 학술 인용 KCI/한국학중앙연구원 라이브 검증 가능
- 가짜 인용 0건
- 세대·집단 단정 표현 0건
- 다중 가능성 + 면책 의무
- 회귀 20쌍 이상

위 조건 미충족 시 ADR-010 + ADR-014에 따라 거부됩니다.
```

---

## 본 시스템 채택 절차

1. `/squeeze-report` 사실성 분리 + KCI/ISBN 라이브 검증
2. ACCEPT 후보:
   - 신규 ADR (A13 사회적 무의식 학파 명시 채택)
   - `engine/agents/social_unconscious.py` v3 보강
   - `data/korean_social_unconscious_clusters.json` 학술 검증
   - 회귀 20건
   - vault/references/ Fromm·Jung·KCI 출처 영속화
3. 운영 데이터 누적 후 실 클러스터링 보정 (별도 ADR)

## 면책

- 본 후보는 운영 데이터 누적 전까지 학술 근거 단계만
- 세대·집단 단정 절대 금지
- 다중 가능성 + 면책 의무
- 학파 명시 (Fromm ≠ Jung ≠ 현대 사회심리학)
